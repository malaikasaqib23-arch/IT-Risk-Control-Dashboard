"""Live checks for the four SYNTHETIC dashboard tables; never writes data."""
import pandas as pd

from monitoring import normalized, OPEN
from scoring import FREQUENCY_DAYS, risk_band

SCHEMAS = {
    "controls": {"control_id", "iso_reference", "iso_title", "csf_function", "owner",
                 "testing_frequency", "impact_score", "mapping_rationale", "impact_rationale"},
    "tests": {"test_id", "control_id", "test_date", "result", "evidence_reference",
              "findings", "remediation_status", "remediation_due_date"},
    "incidents": {"incident_id", "control_id", "incident_date", "severity", "status", "resolved_date"},
    "risks": {"risk_id", "control_id", "likelihood", "impact", "risk_score", "risk_level", "owner", "status"},
}


def validate_data(controls, tests, incidents, risks, report_date, first_date):
    tables = dict(controls=controls, tests=tests, incidents=incidents, risks=risks)
    rows = []

    def check(name, valid, detail="", severity="error"):
        rows.append({"Check": name, "Passed": bool(valid), "Severity": severity,
                     "Details": detail})

    for name, required in SCHEMAS.items():
        missing = sorted(required - set(tables[name].columns))
        check(f"{name}: required columns", not missing, ", ".join(missing))
    if not all(r["Passed"] for r in rows):
        return pd.DataFrame(rows)

    for name, key in [("controls", "control_id"), ("tests", "test_id"),
                      ("incidents", "incident_id"), ("risks", "risk_id")]:
        values = normalized(tables[name][key])
        check(f"{name}: unique nonempty keys", values.ne("").all() and values.is_unique)
    check("controls: register not empty", len(controls) > 0)
    for name in ["tests", "incidents", "risks"]:
        ids = tables[name]["control_id"]
        blank = normalized(ids).eq("")
        valid = ids.isin(controls["control_id"])
        check(f"{name}: valid control links", (valid | (blank if name == "incidents" else False)).all())
    unlinked = int(normalized(incidents["control_id"]).eq("").sum())
    check("incidents: all linked to controls", unlinked == 0,
          f"{unlinked} unlinked incidents; included only with all controls selected", "warning")

    allowed = [(tests, "result", {"Pass", "Partial", "Fail"}, "test results"),
               (tests, "remediation_status", {"Not Required", "Open", "In Progress", "Closed"}, "remediation status"),
               (incidents, "severity", {"Low", "Medium", "High", "Critical"}, "incident severity"),
               (incidents, "status", {"Open", "In Progress", "Resolved", "Closed"}, "incident status"),
               (risks, "status", {"Open", "In Progress", "Closed", "Accepted", "Resolved"}, "risk status"),
               (controls, "csf_function", {"Govern", "Identify", "Protect", "Detect", "Respond", "Recover"}, "CSF grouping")]
    for frame, col, choices, name in allowed:
        check(f"Allowed {name}", frame[col].isin(choices).all())
    check("Known testing frequencies", normalized(controls["testing_frequency"]).isin(FREQUENCY_DAYS).all())
    for frame, col, name in [(controls, "impact_score", "Control impact"),
                             (risks, "likelihood", "Stored likelihood"), (risks, "impact", "Stored impact")]:
        values = pd.to_numeric(frame[col], errors="coerce")
        check(name + " integers 1..5", (values.between(1, 5) & values.mod(1).eq(0)).all())
    score = pd.to_numeric(risks["risk_score"], errors="coerce")
    expected = pd.to_numeric(risks["likelihood"], errors="coerce") * pd.to_numeric(risks["impact"], errors="coerce")
    check("Stored risk scores match", score.eq(expected).all())
    bands = score.map(lambda x: risk_band(x) if pd.notna(x) and 1 <= x <= 25 else "INVALID")
    check("Stored risk bands match", risks["risk_level"].eq(bands).all())
    expected_impact = risks["control_id"].map(controls.set_index("control_id")["impact_score"]) if controls["control_id"].is_unique else pd.Series(index=risks.index, dtype=float)
    check("Risk impact matches control register", pd.to_numeric(risks["impact"], errors="coerce").eq(pd.to_numeric(expected_impact, errors="coerce")).all())

    for name, col in [("tests", "test_date"), ("incidents", "incident_date")]:
        dates = pd.to_datetime(tables[name][col], errors="coerce", format="ISO8601")
        check(f"{name}: valid historical dates", dates.notna().all()
              and dates.between(pd.Timestamp(first_date), pd.Timestamp(report_date)).all())
    for name, col in [("tests", "remediation_due_date"), ("incidents", "resolved_date")]:
        values = tables[name][col]
        dates = pd.to_datetime(values, errors="coerce", format="ISO8601")
        check(f"{col}: parseable when supplied", (normalized(values).eq("") | dates.notna()).all())
    for frame, column in [(tests, "next_test_due"), (risks, "review_date")]:
        if column in frame:
            supplied = normalized(frame[column]).ne("")
            dates = pd.to_datetime(frame[column], errors="coerce", format="ISO8601")
            check(f"{column}: parseable when supplied", (~supplied | dates.notna()).all())
    resolved = normalized(incidents["status"]).isin({"closed", "resolved"})
    resolved_dates = pd.to_datetime(incidents["resolved_date"], errors="coerce", format="ISO8601")
    incident_dates = pd.to_datetime(incidents["incident_date"], errors="coerce", format="ISO8601")
    check("Closed incidents have a valid resolution date", resolved_dates.loc[resolved].notna().all()
          and resolved_dates.loc[resolved].ge(incident_dates.loc[resolved]).all()
          and resolved_dates.loc[resolved].le(pd.Timestamp(report_date)).all())
    check("Open incidents have no resolution date", resolved_dates.loc[~resolved].isna().all())
    check("Test evidence references present", normalized(tests["evidence_reference"]).ne("").all())
    check("Mapping and impact reasons present", normalized(controls["mapping_rationale"]).ne("").all()
          and normalized(controls["impact_rationale"]).ne("").all(),
          "Reasons are student proposals; this check does not verify framework correctness")
    check("Control owners assigned", normalized(controls["owner"]).ne("").all(), severity="warning")
    unowned_risk = (normalized(risks["status"]).isin(OPEN)
                    & risks["risk_level"].isin(["High", "Critical"])
                    & normalized(risks["owner"]).eq(""))
    check("Open High/Critical stored risks have owners", not unowned_risk.any(),
          "Missing risk owners also trigger the named alert for the selected scoring basis", "warning")
    missing_due = normalized(tests["remediation_status"]).isin(OPEN) & normalized(tests["remediation_due_date"]).eq("")
    check("Open remediations have due dates", not missing_due.any(), severity="warning")
    return pd.DataFrame(rows)
