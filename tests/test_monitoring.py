"""Hand-worked SYNTHETIC examples for numeric rules and edge cases."""
from pathlib import Path

import pandas as pd
import pytest

from alerts import incident_spikes, missing_risk_owners
from monitoring import dashboard_kpis, event_risk_register, filter_incidents
from monitoring import selected_heatmap_cell, public_scenario_results
from quality import validate_data
from scoring import control_health_table, overdue_test

ROOT = Path(__file__).resolve().parents[1]
AS_OF = pd.Timestamp("2026-10-31")


@pytest.mark.parametrize("cell", [[1, 5], [3, 4], [5, 5]])
def test_heatmap_selection_reads_three_cells(cell):
    assert selected_heatmap_cell({"selection": {"points": [{"customdata": cell}]}}) == tuple(cell)


@pytest.mark.parametrize("event", [{}, {"points": []}, {"points": [{"customdata": [0, 5]}]},
                                    {"points": [{"customdata": [True, 4]}]},
                                    {"points": [{"customdata": [3.5, 4]}]}])
def test_heatmap_selection_ignores_invalid_payloads(event):
    assert selected_heatmap_cell(event) is None


def test_public_scenario_results_report_caught_missed_and_false_trigger():
    table = pd.DataFrame({"Control / Incident": ["CTRL-009", "CTRL-014"],
                          "Rule": ["CONSECUTIVE_FAILURES", "CONSECUTIVE_FAILURES"]})
    results = public_scenario_results(table)
    assert len(results) == 7
    assert results.iloc[0]["Result"] == "Pass"
    assert results.iloc[1]["Result"] == "Fail"  # Missing expected CTRL-016 alert.
    assert results.iloc[-1]["Result"] == "Fail"  # Unexpected CTRL-014 consecutive alert.


def load_tables():
    return [pd.read_csv(ROOT / "data" / name) for name in [
        "SYNTHETIC_controls_DRAFT.csv", "SYNTHETIC_control_tests.csv",
        "SYNTHETIC_incidents.csv", "SYNTHETIC_risk_register.csv"]]


@pytest.mark.parametrize("failures,incidents,impact,likelihood,score,band", [
    (0, 0, 3, 1, 3, "Low"),  # 0+0 events -> 1; 1*3=3
    (1, 1, 4, 3, 12, "High"),  # 1+1=2 -> 3; 3*4=12
    (3, 0, 5, 4, 20, "Critical"),  # guide example: 3 -> 4; 4*5=20
    (4, 2, 5, 5, 25, "Critical"),
])
def test_event_risk_worked_examples(failures, incidents, impact, likelihood, score, band):
    c = pd.DataFrame({"control_id": ["SYN-A"], "impact_score": [impact]})
    t = pd.DataFrame({"control_id": ["SYN-A"] * failures,
                      "test_date": ["2026-10-01"] * failures, "result": ["Fail"] * failures})
    i = pd.DataFrame({"control_id": ["SYN-A"] * incidents, "incident_date": ["2026-10-02"] * incidents})
    r = pd.DataFrame({"control_id": ["SYN-A"], "likelihood": [1], "impact": [impact], "risk_score": [impact], "risk_level": ["Low"]})
    before = r.copy(deep=True)
    out = event_risk_register(c, t, i, r, AS_OF).iloc[0]
    assert (out.likelihood, out.risk_score, out.risk_level) == (likelihood, score, band)
    pd.testing.assert_frame_equal(r, before)


def test_event_window_boundaries_partial_and_unlinked():
    c, t, i, r = load_tables()
    c, r = c.head(1), r.head(1)
    cid = c.control_id.iloc[0]
    t = pd.DataFrame({"control_id": [cid] * 5,
                      "test_date": ["2025-10-31", "2025-11-01", "2026-10-31", "2026-11-01", "2026-09-01"],
                      "result": ["Fail", "Fail", "Fail", "Fail", "Partial"]})
    i = pd.DataFrame({"control_id": [cid, cid, cid, None],
                      "incident_date": ["2025-10-31", "2026-10-31", "2026-11-01", "2026-10-01"]})
    out = event_risk_register(c, t, i, r, AS_OF).iloc[0]
    assert (out.failed_tests_365d, out.linked_incidents_365d, out.likelihood) == (2, 1, 4)


@pytest.mark.parametrize("days,expected", [(44, False), (45, False), (46, True)])
def test_overdue_hand_boundaries(days, expected):
    assert overdue_test(AS_OF - pd.Timedelta(days=days), "Monthly", AS_OF) == expected


def test_never_tested_zero_health_and_overdue():
    c = pd.DataFrame({"control_id": ["SYN-A"], "testing_frequency": ["Monthly"]})
    t = pd.DataFrame({"control_id": pd.Series(dtype=str), "test_date": pd.Series(dtype="datetime64[ns]"),
                      "test_id": pd.Series(dtype=str), "result": pd.Series(dtype=str)})
    h = control_health_table(c, t, AS_OF).iloc[0]
    assert h.health_score == 0 and h.never_tested and h.is_overdue


@pytest.mark.parametrize("owner", [None, "", "   "])
def test_missing_owner_positive_and_no_control_owner_fallback(owner):
    r = pd.DataFrame({"risk_id": ["SYN-R"], "owner": [owner], "owner_control": ["Synthetic SOC"],
                      "risk_level": ["Critical"], "status": [" In Progress "]})
    assert missing_risk_owners(r).risk_id.tolist() == ["SYN-R"]


@pytest.mark.parametrize("level,status,owner", [
    ("Medium", "Open", None), ("High", "Closed", None), ("Critical", "Open", "Synthetic SOC")])
def test_missing_owner_negative(level, status, owner):
    r = pd.DataFrame({"risk_id": ["SYN-R"], "owner": [owner], "risk_level": [level], "status": [status]})
    assert missing_risk_owners(r).empty


def incident_fixture(counts):
    return pd.DataFrame({"incident_date": [f"2026-{month:02d}-10"
                                           for month, count in enumerate(counts, 1) for _ in range(count)]})


@pytest.mark.parametrize("counts,mean,total,expected", [
    ([3, 6, 9, 12], 6, 18, True),  # (3+6+9)/3=6; 12 >= 2*6
    ([0, 0, 0, 10], 0, 0, True),  # zero baseline; absolute floor still applies
    ([10, 10, 10, 19], 10, 30, False),  # 19 < 20
    ([1, 1, 1, 9], 1, 3, False),  # 9 < absolute floor 10
])
def test_spike_hand_examples(counts, mean, total, expected):
    out = incident_spikes(incident_fixture(counts), "2026-04-30", "2026-01-01")
    assert (not out.empty) == expected
    if expected:
        assert out.iloc[0].baseline == mean and out.iloc[0].previous_3_total == total


def test_spike_needs_complete_months_and_excludes_future():
    i = incident_fixture([2, 2, 2, 20, 50])
    assert incident_spikes(i, "2026-04-29", "2026-01-01").empty
    assert incident_spikes(i, "2026-04-30", "2026-01-02").empty
    out = incident_spikes(i, "2026-04-30", "2026-01-01")
    assert out.month.tolist() == ["2026-04"] and out.iloc[0]["count"] == 20


@pytest.mark.parametrize("case,expected", [
    (0, [50, 100/3, 2, 2, 100/3, 2, 2, 50, 200/3]),
    (1, [100, 100, 0, 0, 100, 0, 0, None, 100]),
    (2, [0, 0, 1, 1, 0, 2, 1, 100, 50]),
])
def test_eight_kpis_three_hand_worked_examples(case, expected):
    if case == 0:
        scores, overdue, never = [100, 50, 0], [False, True, True], [False, False, True]
        results, findings, statuses, due = ["Pass", "Partial", "Fail"], [None, "SYN finding", "SYN finding"], ["Not Required", "Open", "In Progress"], [None, "2026-10-30", "2026-10-31"]
        levels, risk_status = ["High", "Critical", "Low"], ["Open", "In Progress", "Open"]
        dates = ["2026-08-03", "2026-10-31", "2026-08-02"]
    elif case == 1:
        scores, overdue, never = [100, 100], [False, False], [False, False]
        results, findings, statuses, due = ["Pass", "Pass"], [None, None], ["Not Required"]*2, [None]*2
        levels, risk_status, dates = ["High"], ["Closed"], []
    else:
        scores, overdue, never = [0, 0], [True, True], [False, True]
        results, findings, statuses, due = ["Fail"], ["SYN finding"], ["Open"], ["2026-01-01"]
        levels, risk_status, dates = ["Critical"], ["Open"], ["2026-10-31"]
    h = pd.DataFrame({"health_score": scores, "is_overdue": overdue, "never_tested": never})
    t = pd.DataFrame({"result": results, "findings": findings, "remediation_status": statuses, "remediation_due_date": due})
    r = pd.DataFrame({"risk_level": levels, "status": risk_status})
    i = pd.DataFrame({"incident_date": dates})
    k = dashboard_kpis(h, r, t, i, AS_OF)
    keys = ["health", "on_time", "high_critical", "incidents90", "pass_rate", "overdue", "exceptions", "overdue_remediation", "coverage"]
    for key, value in zip(keys, expected):
        assert pd.isna(k[key]) if value is None else k[key] == pytest.approx(value)


def test_empty_kpis_are_explicit():
    c, t, i, r = load_tables()
    h = pd.DataFrame(columns=["health_score", "is_overdue", "never_tested"]).astype({"is_overdue": bool, "never_tested": bool})
    k = dashboard_kpis(h, r.iloc[:0], t.iloc[:0], i.iloc[:0], AS_OF)
    assert pd.isna(k["health"]) and pd.isna(k["on_time"]) and pd.isna(k["pass_rate"])
    assert k["incidents90"] == k["exceptions"] == k["overdue"] == 0


def test_unlinked_incident_filter_policy():
    i = pd.DataFrame({"control_id": ["A", "B", None], "incident_date": ["2026-10-01"]*3})
    assert len(filter_incidents(i, ["A", "B"], True, "2026-10-01", AS_OF)) == 3
    assert len(filter_incidents(i, ["A"], False, "2026-10-01", AS_OF)) == 1
    assert filter_incidents(i, [], False, "2026-10-01", AS_OF).empty


def test_quality_baseline_and_missing_columns():
    c, t, i, r = load_tables()
    out = validate_data(c, t, i, r, AS_OF, "2025-11-01")
    assert out.loc[out.Severity.eq("error"), "Passed"].all()
    assert out.loc[out.Check.eq("incidents: all linked to controls"), "Passed"].iloc[0]
    assert out.Passed.all()
    out = validate_data(c, t.drop(columns="result"), i, r, AS_OF, "2025-11-01")
    assert not out.Passed.all()


@pytest.mark.parametrize("table,column,value,check", [
    (1, "control_id", "BAD", "tests: valid control links"),
    (3, "risk_score", 999, "Stored risk scores match"),
    (2, "incident_date", "invalid", "incidents: valid historical dates"),
    (0, "impact_score", 2.5, "Control impact integers 1..5"),
    (1, "evidence_reference", " ", "Test evidence references present"),
])
def test_quality_rejects_corruption(table, column, value, check):
    tables = load_tables()
    tables[table][column] = tables[table][column].astype(object)
    tables[table].loc[0, column] = value
    out = validate_data(*tables, AS_OF, "2025-11-01")
    assert not out.loc[out.Check.eq(check), "Passed"].iloc[0]
