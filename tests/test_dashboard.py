"""Dashboard integration checks against the fixed SYNTHETIC demo data."""
from pathlib import Path
import shutil
from datetime import date

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def open_alert_page():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    app.radio[0].set_value("Risk Heatmap & Alerts").run()
    assert not app.exception
    return app


def consecutive_ids(app):
    assert not app.exception
    table = app.dataframe[-1].value
    return set(table.loc[table["Rule"].eq("CONSECUTIVE_FAILURES"),
                         "Control / Incident"])


def test_consecutive_alerts_render_from_source_history():
    app = open_alert_page()
    assert consecutive_ids(app) == {"CTRL-009", "CTRL-016"}
    assert "CTRL-014" not in consecutive_ids(app)

    # Event dates and heatmap drill-down must not hide snapshot alerts.
    app.date_input(key="event_start").set_value(date(2026, 10, 31))
    app.selectbox(key="heatmap_likelihood").set_value(4)
    app.selectbox(key="heatmap_impact").set_value(5)
    app.run()
    assert consecutive_ids(app) == {"CTRL-009", "CTRL-016"}
    assert "2026-10-31 to 2026-10-31" in " ".join(c.value for c in app.caption)
    cell = app.dataframe[0].value
    assert cell["likelihood"].eq(4).all()
    assert cell["impact"].eq(5).all()
    assert app.selectbox(key="heatmap_likelihood").value == 4
    assert app.selectbox(key="heatmap_impact").value == 5


@pytest.mark.parametrize("column,label", [
    ("owner", "Control owner"), ("csf_function", "NIST CSF function")
])
def test_consecutive_alerts_follow_control_filters(column, label):
    controls = pd.read_csv(ROOT / "data/SYNTHETIC_controls_DRAFT.csv")
    app = open_alert_page()
    selected = controls.loc[controls.control_id.eq("CTRL-009"), column].iloc[0]
    widget = next(w for w in (app.pills if label == "NIST CSF function" else app.multiselect) if w.label == label)
    widget.set_value([selected]).run()
    expected = set(controls.loc[
        controls[column].eq(selected) & controls.control_id.isin(["CTRL-009", "CTRL-016"]),
        "control_id"
    ])
    assert consecutive_ids(app) == expected
    widget = next(w for w in (app.pills if label == "NIST CSF function" else app.multiselect) if w.label == label)
    widget.set_value([]).run()
    assert consecutive_ids(app) == set()


def synthetic_copy(tmp_path):
    """Only public synthetic CSVs and the app; never the private answer key."""
    shutil.copy2(ROOT / "app.py", tmp_path / "app.py")
    shutil.copy2(ROOT / "dashboard.css", tmp_path / "dashboard.css")
    (tmp_path / "data").mkdir()
    for source in (ROOT / "data").glob("*.csv"):
        shutil.copy2(source, tmp_path / "data" / source.name)
    return tmp_path / "app.py"


def test_missing_owner_visible_even_with_control_owner(tmp_path):
    path = synthetic_copy(tmp_path)
    csv = tmp_path / "data/SYNTHETIC_risk_register.csv"
    risks = pd.read_csv(csv)
    risks.loc[risks.control_id.eq("CTRL-009"), "owner"] = None
    risks.to_csv(csv, index=False)
    app = AppTest.from_file(str(path), default_timeout=30).run()
    app.radio[0].set_value("Risk Heatmap & Alerts").run()
    assert not app.exception
    table = app.dataframe[-1].value
    missing = table.loc[table.Rule.eq("HIGH_CRITICAL_MISSING_OWNER")]
    assert missing["Control / Incident"].tolist() == ["CTRL-009"]
    assert "RISK-009" in missing.iloc[0].Details


def test_data_quality_failure_is_red_and_stops_calculations(tmp_path):
    path = synthetic_copy(tmp_path)
    csv = tmp_path / "data/SYNTHETIC_risk_register.csv"
    risks = pd.read_csv(csv)
    risks.loc[0, "risk_score"] = 999
    risks.to_csv(csv, index=False)
    app = AppTest.from_file(str(path), default_timeout=30).run()
    assert not app.exception
    assert any("Data quality failed" in error.value for error in app.error)
    assert len(app.metric) == 0


@pytest.mark.parametrize("start_date,end_date,expected", [
    ("2025-11-01", "2026-10-31", ["73.68%", "94.74%", "17", "41", "74.67%", "1", "60", "86.67%"]),
    ("2026-09-01", "2026-09-30", ["73.68%", "94.74%", "17", "30", "68.97%", "1", "7", "100.00%"]),
    ("2026-10-01", "2026-10-31", ["73.68%", "94.74%", "17", "5", "58.33%", "1", "8", "0.00%"]),
])
def test_screen_kpis_match_independent_source_counts(start_date, end_date, expected):
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    app.date_input(key="event_start").set_value(date.fromisoformat(start_date))
    app.date_input(key="event_end").set_value(date.fromisoformat(end_date)).run()
    assert not app.exception
    assert [m.value for m in app.metric] == expected


def test_all_pages_empty_selection_and_stored_basis():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    app.selectbox(key="risk_basis").set_value("Stored register").run()
    for page in ["Overview", "Control Health", "Risk Heatmap & Alerts"]:
        app.radio[0].set_value(page).run()
        assert not app.exception
    table = app.dataframe[-1].value
    assert "2026-09" in table.loc[table.Rule.eq("INCIDENT_SPIKE"), "Control / Incident"].tolist()
    next(w for w in app.multiselect if w.label == "Control owner").set_value([]).run()
    assert app.dataframe[-1].value.empty
    app.radio[0].set_value("Overview").run()
    assert not app.exception
    assert app.metric[0].value == "N/A" and app.metric[3].value == "0"
    app.radio[0].set_value("Control Health").run()
    assert not app.exception


def test_seeded_scenarios_reach_the_displayed_table():
    app = open_alert_page()
    table = app.dataframe[-1].value
    actual = set(zip(table["Control / Incident"], table["Rule"]))
    expected = {
        ("CTRL-009", "CONSECUTIVE_FAILURES"),
        ("CTRL-016", "CONSECUTIVE_FAILURES"),
        ("CTRL-014", "TEST_OVERDUE"),
        ("2026-09", "INCIDENT_SPIKE"),
        ("CTRL-013", "OPEN_EXCEPTION"),
        ("INC-0001", "CRITICAL_OPEN_INCIDENT"),
    }
    assert expected <= actual
    assert ("CTRL-014", "CONSECUTIVE_FAILURES") not in actual


def test_calendar_invalid_range_stops():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    app.date_input(key="event_start").set_value(date(2026, 2, 28))
    app.date_input(key="event_end").set_value(date(2026, 1, 31)).run()
    assert not app.exception
    assert any("Start date cannot be after end date" in e.value for e in app.error)
    assert len(app.metric) == 0


def test_baseline_quality_checks_all_pass():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    assert not app.error
    assert any("39/39 checks passed" in item.value for item in app.success)
    assert len(app.metric) == 8


def test_risk_band_filters_control_population_and_linked_history_across_pages():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    risks = pd.read_csv(ROOT / "data/SYNTHETIC_risk_register.csv")
    expected_ids = set(risks.loc[risks.risk_level.eq("Critical"), "control_id"])
    next(w for w in app.pills if w.label == "Risk band").set_value(["Critical"]).run()
    assert not app.exception
    # Fifteen Critical records; all controls outside that band are excluded everywhere.
    assert app.metric[2].value == "15"
    app.radio[0].set_value("Control Health").run()
    assert set(app.dataframe[-1].value.control_id) == expected_ids
    app.radio[0].set_value("Overview").run()
    monthly = app.dataframe[0].value
    incidents = pd.read_csv(ROOT / "data/SYNTHETIC_incidents.csv")
    assert int(monthly.Total.sum()) == int(incidents.control_id.isin(expected_ids).sum())
    app.radio[0].set_value("Risk Heatmap & Alerts").run()
    assert not app.exception
    evidence = app.dataframe[1].value
    assert set(evidence.control_id) == expected_ids


def test_sidebar_reset_restores_scope_and_preserves_scoring_basis():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    app.selectbox(key="risk_basis").set_value("Stored register").run()
    app.pills(key="filter_csf").set_value(["Protect"]).run()
    app.pills(key="filter_band").set_value(["Critical"]).run()
    app.multiselect(key="filter_owner").set_value([]).run()
    assert app.metric[0].value == "N/A"
    app.date_input(key="event_start").set_value(date(2026, 10, 1)).run()
    app.button(key="reset_sidebar").click().run()
    assert not app.exception
    assert len(app.pills(key="filter_csf").value) == 6
    assert app.pills(key="filter_band").value == ["Low", "Medium", "High", "Critical"]
    assert app.date_input(key="event_start").value == date(2025, 11, 1)
    assert app.date_input(key="event_end").value == date(2026, 10, 31)
    assert app.selectbox(key="risk_basis").value == "Stored register"
    assert [m.value for m in app.metric[:4]] == ["73.68%", "94.74%", "17", "41"]


def test_owner_picker_switches_between_all_individual_and_multiple_departments():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert app.multiselect(key="filter_owner").value == ["All departments"]
    app.multiselect(key="filter_owner").set_value(["All departments", "IT Operations"]).run()
    assert not app.exception
    assert app.multiselect(key="filter_owner").value == ["IT Operations"]
    app.radio[0].set_value("Control Health").run()
    assert set(app.dataframe[-1].value.owner) == {"IT Operations"}
    app.multiselect(key="filter_owner").set_value(["IT Operations", "IT Infrastructure"]).run()
    assert set(app.dataframe[-1].value.owner) == {"IT Operations", "IT Infrastructure"}
    app.multiselect(key="filter_owner").set_value(["IT Operations", "IT Infrastructure", "All departments"]).run()
    assert app.multiselect(key="filter_owner").value == ["All departments"]
    assert len(app.dataframe[-1].value) == 19
