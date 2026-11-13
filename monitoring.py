"""SYNTHETIC dashboard calculations; all numeric rules are design choices."""
import pandas as pd

from scoring import risk_band

OPEN = {"open", "in progress"}


def normalized(series):
    return series.astype("string").fillna("").str.strip().str.casefold()


def selected_heatmap_cell(event):
    """Read a Plotly cell selection without accepting malformed coordinates."""
    selection = event.get("selection", event)
    for point in reversed(selection.get("points", [])):
        cell = point.get("customdata")
        if not isinstance(cell, (list, tuple)) or len(cell) != 2:
            continue
        likelihood, impact = cell
        if (not isinstance(likelihood, bool) and not isinstance(impact, bool)
                and likelihood in [1, 2, 3, 4, 5] and impact in [1, 2, 3, 4, 5]):
            return int(likelihood), int(impact)
    return None


def public_scenario_results(alert_table):
    """Public regression checks only; this does not access a private answer key."""
    positives = [("CTRL-009", "CONSECUTIVE_FAILURES"), ("CTRL-016", "CONSECUTIVE_FAILURES"),
                 ("CTRL-014", "TEST_OVERDUE"), ("2026-09", "INCIDENT_SPIKE"),
                 ("CTRL-013", "OPEN_EXCEPTION"), ("INC-0001", "CRITICAL_OPEN_INCIDENT")]
    cases = [(entity, rule, True) for entity, rule in positives]
    cases.append(("CTRL-014", "CONSECUTIVE_FAILURES", False))
    actual = set(zip(alert_table["Control / Incident"], alert_table["Rule"]))
    return pd.DataFrame([{"Synthetic scenario": entity, "Rule": rule,
                          "Expected alert": expected, "Observed alert": (entity, rule) in actual,
                          "Result": "Pass" if ((entity, rule) in actual) == expected else "Fail"}
                         for entity, rule, expected in cases])


def event_risk_register(controls, tests, incidents, risks, report_date):
    """Recalculate in memory over (report date - 365 days, report date]."""
    report_date = pd.Timestamp(report_date)
    start = report_date - pd.Timedelta(days=365)
    test_dates = pd.to_datetime(tests["test_date"])
    incident_dates = pd.to_datetime(incidents["incident_date"])
    failures = tests.loc[test_dates.gt(start) & test_dates.le(report_date)
                         & tests["result"].eq("Fail")].groupby("control_id").size()
    linked = incidents.loc[incident_dates.gt(start) & incident_dates.le(report_date)
                           ].groupby("control_id").size()
    out = risks.copy()
    for column in ["likelihood", "impact", "risk_score", "risk_level"]:
        out[f"stored_{column}"] = out[column]
    out["failed_tests_365d"] = out["control_id"].map(failures).fillna(0).astype(int)
    out["linked_incidents_365d"] = out["control_id"].map(linked).fillna(0).astype(int)
    out["event_count_365d"] = out["failed_tests_365d"] + out["linked_incidents_365d"]
    out["likelihood"] = (out["event_count_365d"] + 1).clip(upper=5)
    out["impact"] = out["control_id"].map(controls.set_index("control_id")["impact_score"])
    out["risk_score"] = out["likelihood"] * out["impact"]
    out["risk_level"] = out["risk_score"].map(risk_band)
    return out


def filter_incidents(incidents, eligible_ids, all_controls_selected, start, end):
    """Include unlinked incidents only when the control selection is unrestricted."""
    linked = incidents["control_id"].isin(eligible_ids)
    if all_controls_selected:
        linked = linked | normalized(incidents["control_id"]).eq("")
    dates = pd.to_datetime(incidents["incident_date"])
    return incidents.loc[linked & dates.between(start, end)].copy()


def unresolved_findings(tests):
    return tests.loc[tests["result"].isin(["Partial", "Fail"])
                     & normalized(tests["remediation_status"]).isin(OPEN)
                     & normalized(tests["findings"]).ne("")].copy()


def dashboard_kpis(health, risks, tests, incidents, report_date):
    """Eight indicators; event inputs must already have the chosen UI filters."""
    report_date = pd.Timestamp(report_date)
    health = health.copy()
    open_risks = risks.loc[normalized(risks["status"]).isin(OPEN)]
    unresolved = unresolved_findings(tests)
    due = pd.to_datetime(unresolved["remediation_due_date"], errors="coerce")
    not_on_time = health["is_overdue"] | health["never_tested"]
    incident_dates = pd.to_datetime(incidents["incident_date"])
    pct = lambda numerator, denominator: 100 * numerator / denominator if denominator else float("nan")
    return {
        "health": health["health_score"].mean(),
        "on_time": pct((~not_on_time).sum(), len(health)),
        "high_critical": int(open_risks["risk_level"].isin(["High", "Critical"]).sum()),
        "incidents90": int(incident_dates.between(report_date - pd.Timedelta(days=89), report_date).sum()),
        "pass_rate": pct(tests["result"].eq("Pass").sum(), len(tests)),
        "overdue": int(not_on_time.sum()),
        "exceptions": len(unresolved),
        "overdue_remediation": pct(due.lt(report_date).sum(), len(unresolved)),
        "coverage": pct((~health["never_tested"]).sum(), len(health)),
        "missing_due_dates": int(due.isna().sum()),
    }
