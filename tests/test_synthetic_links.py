"""Synthetic-link completeness, preservation and independent scoring examples."""
from pathlib import Path
import pandas as pd
import pytest
from synthetic_links import complete_synthetic_links
from monitoring import event_risk_register
from quality import validate_data

ROOT = Path(__file__).resolve().parents[1]


def test_link_completion_preserves_existing_links_and_other_fields():
    source = pd.DataFrame({"incident_id": ["A", "B", "C"],
        "incident_type": ["Malware", "Unauthorized Access", "Configuration Issue"],
        "control_id": [None, "CTRL-009", " "], "severity": ["Low", "High", "Medium"]})
    original = source.copy(deep=True)
    result = complete_synthetic_links(source)
    assert result.control_id.tolist() == ["CTRL-011", "CTRL-009", "CTRL-013"]
    pd.testing.assert_frame_equal(source, original)
    pd.testing.assert_frame_equal(result.drop(columns="control_id"), original.drop(columns="control_id"))


def test_unknown_unlinked_type_is_rejected():
    with pytest.raises(ValueError, match="Missing synthetic control mapping"):
        complete_synthetic_links(pd.DataFrame({"incident_type": ["Unknown"], "control_id": [None]}))


@pytest.mark.parametrize("control,incidents,failures,likelihood,impact,score", [
    ("CTRL-002", 3, 0, 4, 5, 20),  # 0 + 3 events -> 4; 4 * 5 = 20
    ("CTRL-006", 3, 0, 4, 5, 20),  # 0 + 3 events -> 4; 4 * 5 = 20
    ("CTRL-011", 8, 0, 5, 5, 25),  # 8 events -> capped at 5; 5 * 5 = 25
    ("CTRL-013", 5, 0, 5, 4, 20),  # 5 events -> capped at 5; 5 * 4 = 20
])
def test_repaired_register_matches_hand_counted_examples(control, incidents, failures, likelihood, impact, score):
    c, t, i, r = [pd.read_csv(ROOT / "data" / name) for name in [
        "SYNTHETIC_controls_DRAFT.csv", "SYNTHETIC_control_tests.csv", "SYNTHETIC_incidents.csv", "SYNTHETIC_risk_register.csv"]]
    assert not i.control_id.isna().any()
    assert i.control_id.isin(c.control_id).all()
    assert int(i.control_id.eq(control).sum()) == incidents
    assert int((t.control_id.eq(control) & t.result.eq("Fail")).sum()) == failures
    row = event_risk_register(c, t, i, r, "2026-10-31").set_index("control_id").loc[control]
    assert (row.likelihood, row.impact, row.risk_score, row.risk_level) == (likelihood, impact, score, "Critical")
    assert (row.stored_likelihood, row.stored_risk_score) == (likelihood, score)


def test_missing_link_still_triggers_quality_review():
    c, t, i, r = [pd.read_csv(ROOT / "data" / name) for name in [
        "SYNTHETIC_controls_DRAFT.csv", "SYNTHETIC_control_tests.csv", "SYNTHETIC_incidents.csv", "SYNTHETIC_risk_register.csv"]]
    i.loc[0, "control_id"] = None
    out = validate_data(c, t, i, r, "2026-10-31", "2025-11-01")
    assert not out.loc[out.Check.eq("incidents: all linked to controls"), "Passed"].iloc[0]
