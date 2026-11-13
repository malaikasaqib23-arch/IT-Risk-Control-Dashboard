
"""
IT Risk & Control Monitoring Dashboard
Guide-aligned prototype v2

SYNTHETIC DATA ONLY
All risk thresholds are project design choices.
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from alerts import consecutive_failures, missing_risk_owners, incident_spikes
from monitoring import (dashboard_kpis, event_risk_register, filter_incidents, unresolved_findings,
                        selected_heatmap_cell, public_scenario_results)
from quality import validate_data
from scoring import control_health_table, monthly_incidents, FREQUENCY_DAYS
from visuals import (style_chart, outcome_donut, incident_area, function_radar, risk_donut,
                     PALETTE, SEVERITY, CYAN, VIOLET, rounded_risk_heatmap)


# ============================================================
# 1. CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

AS_OF = pd.Timestamp("2026-10-31")
FIRST_DATE = pd.Timestamp("2025-11-01")

st.set_page_config(
    page_title="IT Risk & Control Monitoring | SYNTHETIC",
    page_icon="📊",
    layout="wide"
)


st.html(f"<style>{(ROOT / 'dashboard.css').read_text(encoding='utf-8')}</style>")

# ============================================================
# 2. LOAD SYNTHETIC DATA
# ============================================================

@st.cache_data(max_entries=4)
def load_data(signature):

    controls_path = DATA / "SYNTHETIC_controls_DRAFT.csv"

    if not controls_path.exists():
        controls_path = DATA / "SYNTHETIC_controls.csv"

    controls = pd.read_csv(controls_path)

    tests = pd.read_csv(
        DATA / "SYNTHETIC_control_tests.csv"
    )

    incidents = pd.read_csv(
        DATA / "SYNTHETIC_incidents.csv"
    )

    risks = pd.read_csv(
        DATA / "SYNTHETIC_risk_register.csv"
    )

    return controls, tests, incidents, risks


try:
    controls_file = DATA / "SYNTHETIC_controls_DRAFT.csv"
    if not controls_file.exists():
        controls_file = DATA / "SYNTHETIC_controls.csv"
    source_files = [controls_file] + [DATA / f"SYNTHETIC_{name}.csv"
                                    for name in ["control_tests", "incidents", "risk_register"]]
    signature = tuple((str(path), path.stat().st_mtime_ns, path.stat().st_size)
                      for path in source_files)
    controls, tests, incidents, risks = load_data(signature)
except (OSError, ValueError, pd.errors.ParserError) as error:
    st.error(f"Synthetic data could not be loaded: {error}")
    st.stop()

quality_results = validate_data(controls, tests, incidents, risks, AS_OF, FIRST_DATE)
quality_errors = quality_results.loc[~quality_results["Passed"] & quality_results["Severity"].eq("error")]
quality_warnings = quality_results.loc[~quality_results["Passed"] & quality_results["Severity"].eq("warning")]
if not quality_errors.empty:
    st.error("Data quality failed. Correct the listed source issues before using the dashboard.")
    st.table(quality_results)
    st.stop()


# Parse only after validation so malformed supplied dates cannot become silent blanks.
for column in [
    "test_date",
    "remediation_due_date",
    "next_test_due"
]:
    if column in tests.columns:
        tests[column] = pd.to_datetime(
            tests[column],
            errors="coerce"
        )

for column in [
    "incident_date",
    "resolved_date"
]:
    if column in incidents.columns:
        incidents[column] = pd.to_datetime(
            incidents[column],
            errors="coerce"
        )


# Reporting-date cutoff
tests = tests.loc[
    tests["test_date"].le(AS_OF)
].copy()

incidents = incidents.loc[
    incidents["incident_date"].le(AS_OF)
].copy()


# ============================================================
# 3. COMPUTE CURRENT HEALTH AND RISK DATA
# ============================================================

health = control_health_table(
    controls,
    tests,
    AS_OF
)

ALL_OWNERS = "All departments"


def normalize_owner_selection():
    values = list(st.session_state.get("filter_owner", []))
    previous = st.session_state.get("_previous_owner_selection", [ALL_OWNERS])
    if ALL_OWNERS in values and len(values) > 1:
        values = [ALL_OWNERS] if ALL_OWNERS not in previous else [v for v in values if v != ALL_OWNERS]
    st.session_state["filter_owner"] = values
    st.session_state["_previous_owner_selection"] = values


def reset_sidebar_filters():
    st.session_state["filter_csf"] = sorted(controls["csf_function"].dropna().unique().tolist())
    st.session_state["filter_owner"] = [ALL_OWNERS]
    st.session_state["_previous_owner_selection"] = [ALL_OWNERS]
    st.session_state["filter_band"] = ["Low", "Medium", "High", "Critical"]
    st.session_state["event_start"] = FIRST_DATE.date()
    st.session_state["event_end"] = AS_OF.date()


with st.sidebar:
    st.markdown('<div class="sidebar-eyebrow">CONTROL OBSERVATORY</div>', unsafe_allow_html=True)
    st.header("Refine your view")
    st.caption("Choose your scope. Results update instantly.")
    st.button("Reset filters", key="reset_sidebar", on_click=reset_sidebar_filters,
              icon=":material/restart_alt:", width="stretch")
    filter_panel = st.container()
    with st.expander("Scoring settings", icon=":material/tune:"):
        risk_basis = st.selectbox(
            "Risk scoring basis",
            ["Recomputed from events", "Stored register"],
            key="risk_basis",
            help="Recomputed scores use failed tests and linked incidents in the preceding 365 days. CSVs are never updated."
        )
        st.caption("Snapshot: 31 October 2026")

recomputed_risks = event_risk_register(controls, tests, incidents, risks, AS_OF)
active_risks = recomputed_risks if risk_basis == "Recomputed from events" else risks

risk_with_controls = active_risks.merge(
    controls[
        [
            "control_id",
            "iso_title",
            "csf_function",
            "owner",
            "iso_reference"
        ]
    ],
    on="control_id",
    how="left",
    suffixes=("", "_control")
)


# ============================================================
# 4. DASHBOARD TITLE
# ============================================================

st.markdown('<div class="observatory-kicker">CONTROL OBSERVATORY / SYNTHETIC DEMO</div>', unsafe_allow_html=True)
st.title("IT Risk & Control Monitoring Dashboard")

st.caption(
    "SYNTHETIC DATA ONLY | "
    "Reporting date: 31 October 2026 | "
    "Prototype v2 — project-defined risk rules"
)


passed_checks = int(quality_results["Passed"].sum())
if quality_warnings.empty:
    st.success(f"Data quality: {passed_checks}/{len(quality_results)} checks passed.")
else:
    st.error(f"Data quality: {passed_checks}/{len(quality_results)} checks passed; "
               f"Failed review checks requiring action: {len(quality_warnings)}.")
with st.expander("Data quality checks and data scope"):
    st.table(quality_results)
    unlinked = incidents.loc[incidents["control_id"].isna() | incidents["control_id"].astype(str).str.strip().eq("")].copy()
    if not unlinked.empty:
        st.caption("Incident records requiring control-link review")
        st.table(unlinked)
        st.download_button("Download unlinked incidents for review", data=unlinked.to_csv(index=False).encode("utf-8"),
                           file_name="SYNTHETIC_unlinked_incidents_review.csv", mime="text/csv", key="download_unlinked_review")

    st.caption("[Assumption] ISO references and CSF mappings are proposals pending source verification. "
               "[Design choice] Unlinked incidents appear only when every control is selected.")

# ============================================================
# 5. SIDEBAR FILTERS
# ============================================================

with filter_panel:

    # NIST CSF filter
    functions = sorted(
        controls["csf_function"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_functions = st.pills(
        "NIST CSF function", options=functions, default=functions,
        selection_mode="multi", key="filter_csf", wrap=True
    )
    st.divider()

    # Risk band filter
    risk_bands = [
        "Low",
        "Medium",
        "High",
        "Critical"
    ]

    selected_bands = st.pills(
        "Risk band", options=risk_bands, default=risk_bands,
        selection_mode="multi", key="filter_band", wrap=True
    )
    st.divider()

    owners = sorted(controls["owner"].fillna("Unassigned").unique().tolist())
    # Represent the unrestricted selection as one chip instead of every department.
    if "filter_owner" in st.session_state and set(st.session_state["filter_owner"]) == set(owners):
        st.session_state["filter_owner"] = [ALL_OWNERS]
        st.session_state["_previous_owner_selection"] = [ALL_OWNERS]
    owner_selection = st.multiselect(
        "Control owner", options=[ALL_OWNERS] + owners, default=[ALL_OWNERS],
        key="filter_owner", placeholder="Search departments...", on_change=normalize_owner_selection,
        select_all=False, help="Choose one or more departments. All departments restores the full owner scope."
    )
    selected_owners = owners if ALL_OWNERS in owner_selection else owner_selection
    st.divider()

    st.markdown("**Event date range**")
    st.caption("Pick a date from the calendar or type DD/MM/YYYY.")
    start_date = st.date_input(
        "Start date", value=FIRST_DATE.date(), min_value=FIRST_DATE.date(), max_value=AS_OF.date(),
        key="event_start", format="DD/MM/YYYY"
    )
    end_date = st.date_input(
        "End date", value=AS_OF.date(), min_value=FIRST_DATE.date(), max_value=AS_OF.date(),
        key="event_end", format="DD/MM/YYYY"
    )
    if start_date is None or end_date is None:
        st.info("Choose both a start date and an end date.")
        st.stop()
    start, end = pd.Timestamp(start_date), pd.Timestamp(end_date)
    st.caption(f"Selected range: {start:%Y-%m-%d} to {end:%Y-%m-%d}")
    if start > end:
        st.error("Start date cannot be after end date. Please adjust the calendar dates.")
        st.stop()

    st.caption("Current health and risk stay at the reporting date.")


# ============================================================
# 6. APPLY FILTERS
# ============================================================

eligible_ids = controls.loc[
    controls["csf_function"].isin(selected_functions)
    &
    controls["owner"].fillna("Unassigned").isin(selected_owners),
    "control_id"
]

# Risk-band selection defines the same control population on every page.
if set(selected_bands) != set(risk_bands):
    band_ids = active_risks.loc[active_risks["risk_level"].isin(selected_bands), "control_id"]
    eligible_ids = eligible_ids.loc[eligible_ids.isin(band_ids)]

health_f = health.loc[
    health["control_id"].isin(eligible_ids)
].copy()

with st.sidebar:
    st.markdown(f'<div class="sidebar-scope"><span>Current scope</span><strong>{len(health_f)} controls</strong></div>',
                unsafe_allow_html=True)


risks_f = risk_with_controls.loc[
    risk_with_controls["control_id"].isin(eligible_ids)
    &
    risk_with_controls["risk_level"].isin(selected_bands)
].copy()

open_risks = risks_f.loc[
    risks_f["status"]
    .astype(str)
    .str.strip()
    .str.casefold()
    .isin(["open", "in progress"])
].copy()

all_controls_selected = set(eligible_ids) == set(controls["control_id"])
incidents_f = filter_incidents(incidents, eligible_ids, all_controls_selected, start, end)
incident_history_f = filter_incidents(incidents, eligible_ids, all_controls_selected, FIRST_DATE, AS_OF)


tests_f = tests.loc[
    tests["control_id"].isin(eligible_ids)
    &
    tests["test_date"].between(start, end)
].copy()


# ============================================================
# 7. CALCULATE FOUR HEADLINE KPIs
# ============================================================

kpis = dashboard_kpis(health_f, risks_f, tests_f, incidents_f, AS_OF)
overall_health = kpis["health"]
coverage = kpis["coverage"]
on_time_percentage = kpis["on_time"]
high_critical_count = kpis["high_critical"]


# ============================================================
# 8. HELPER FUNCTIONS
# ============================================================

def fmt_pct(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:.2f}%"


def show_data(df, name):
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        alt=name.replace("_", " ")
    )

    st.download_button(
        label=f"Download {name} CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"SYNTHETIC_{name}.csv",
        mime="text/csv",
        key=f"download_{name}"
    )


def show_chart(figure, **kwargs):
    return st.plotly_chart(style_chart(figure), width="stretch", theme=None, **kwargs)


def select_heatmap_cell():
    cell = selected_heatmap_cell(st.session_state.get("risk_count_heatmap", {}))
    if cell is not None:
        st.session_state["heatmap_likelihood"], st.session_state["heatmap_impact"] = cell


def iso_theme(reference):
    key = (
        str(reference)
        .replace("A.", "")
        .split(".")[0]
    )

    return {
        "5": "Organizational",
        "6": "People",
        "7": "Physical",
        "8": "Technological"
    }.get(key, "Unknown")


# ============================================================
# 9. PAGE NAVIGATION
# ============================================================

page = st.radio(
    "View",
    options=[
        "Overview",
        "Control Health",
        "Risk Heatmap & Alerts"
    ],
    horizontal=True
)


# ============================================================
# 10. OVERVIEW PAGE
# ============================================================

if page == "Overview":

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Overall control health",
        fmt_pct(overall_health)
    )

    col2.metric(
        "Controls tested on time",
        fmt_pct(on_time_percentage)
    )

    col3.metric(
        "Open High/Critical risks",
        high_critical_count
    )

    col4.metric(
        "Incidents in last 90 days (selected range)",
        kpis["incidents90"]
    )

    support = st.columns(4)
    support[0].metric("Historical test pass rate", fmt_pct(kpis["pass_rate"]))
    support[1].metric("Overdue controls", kpis["overdue"])
    support[2].metric("Unresolved findings", kpis["exceptions"])
    support[3].metric("Overdue remediation", fmt_pct(kpis["overdue_remediation"]))
    st.caption(f"Testing coverage: {fmt_pct(coverage)} | "
               f"Open findings missing due dates: {kpis['missing_due_dates']}")

    with st.expander("Indicator formulas and suggested management actions"):
        st.table(pd.DataFrame([
            ["Control health", "Mean latest Pass=100 / Partial=50 / Fail=0; untested=0", "Controls and latest tests", "Review failed and untested controls"],
            ["Tested on time", "100 * controls neither overdue nor untested / selected controls", "Frequency and latest test date", "Schedule overdue testing"],
            ["Open High/Critical risks", "Count open/in-progress risks in High or Critical", "Selected scoring basis and risk status", "Assign remediation or escalation"],
            ["90-day incidents", "Count in [report date - 89 days, report date], intersect event filter", "Incident dates", "Review severity and recurring activity"],
            ["Historical pass rate", "100 * Pass tests / all tests in event range", "Test results and dates", "Investigate deterioration"],
            ["Overdue controls", "Count where elapsed days > 1.5 * interval; untested included", "Frequency and latest test date", "Resolve test coverage gaps"],
            ["Unresolved findings", "Count nonblank Partial/Fail findings with Open/In Progress remediation", "Filtered tests and remediation status", "Review outstanding actions"],
            ["Overdue remediation", "100 * unresolved findings due before report date / unresolved findings", "Findings and due dates; missing dates remain in denominator", "Prioritize late actions and complete missing dates"],
        ], columns=["Indicator", "Formula [Design choice]", "Data needed", "Suggested action [Design choice]"]))
        st.caption("[Design choice] Monthly/quarterly/semiannual/annual intervals = 30/90/180/365 days. "
                   "Never-tested health is 0; coverage is shown separately. Zero denominators display N/A.")

    st.info(
        "Control health, testing timeliness, and "
        "risk status are measured as of 31 October 2026. "
        "Incident activity and historical test results "
        "follow the selected event date range. Risk band selects controls and all their linked records across pages. "
        "Unlinked incidents are included only with all controls selected."
    )

    st.subheader(
        "Incidents by month and severity"
    )

    trend = monthly_incidents(
        incidents_f,
        AS_OF
    )

    long = trend.melt(
        id_vars="Month",
        value_vars=[
            "Low",
            "Medium",
            "High",
            "Critical"
        ],
        var_name="Severity",
        value_name="Incidents"
    )

    incident_fig = px.bar(
        long,
        x="Month",
        y="Incidents",
        color="Severity",
        barmode="stack",
        color_discrete_map=SEVERITY,
        category_orders={
            "Month": trend["Month"].tolist()
        },
        labels={
            "Month": "Month",
            "Incidents": "Incident count"
        }
    )

    incident_fig.update_layout(
        height=430,
        legend_title="Severity"
    )

    activity_col, results_col = st.columns([1.8, 1])
    with activity_col:
        show_chart(incident_fig, key="incident_severity_chart", alt="Monthly synthetic incidents split by severity")
    with results_col:
        st.caption("LATEST CONTROL TEST RESULTS")
        show_chart(outcome_donut(health_f), key="outcome_donut", alt="Latest test outcome counts for selected controls")
        st.caption("One latest result per control; separate from historical test pass rate.")

    st.subheader("Incident activity over time")
    show_chart(incident_area(trend), key="incident_area", alt="Total incident count by month")

    with st.expander(
        "Monthly numbers - reconcile with source records"
    ):
        show_data(
            trend,
            "monthly_incidents"
        )


# ============================================================
# 11. CONTROL HEALTH PAGE
# ============================================================

elif page == "Control Health":

    st.subheader(
        "Latest control health by NIST CSF function"
    )

    by_function = (
        health_f
        .groupby(
            "csf_function",
            dropna=False
        )["health_score"]
        .mean()
        .reset_index()
    )

    function_fig = px.bar(
        by_function,
        x="csf_function",
        y="health_score",
        color="csf_function",
        color_discrete_sequence=PALETTE,
        range_y=[0, 100],
        labels={
            "csf_function": "NIST CSF function",
            "health_score": "Mean control health (%)"
        }
    )

    function_fig.update_layout(showlegend=False)
    show_chart(function_fig, key="csf_health_bar", alt="Mean latest control health by proposed CSF grouping")

    st.subheader("Control health profile")
    st.caption("The same CSF averages on a common 0-100 scale; this is control health, not a maturity assessment.")
    show_chart(function_radar(by_function), key="csf_radar", alt="Radar profile of the same CSF control health averages")

    st.subheader(
        "Latest control health by ISO Annex A theme"
    )

    health_f["iso_theme"] = (
        health_f["iso_reference"]
        .apply(iso_theme)
    )

    by_theme = (
        health_f
        .groupby(
            "iso_theme",
            dropna=False
        )["health_score"]
        .mean()
        .reset_index()
    )

    theme_fig = px.bar(
        by_theme,
        x="health_score",
        y="iso_theme",
        orientation="h",
        color="iso_theme",
        color_discrete_sequence=[CYAN, VIOLET, "#F472B6", "#3B82F6"],
        range_x=[0, 100],
        labels={
            "iso_theme": "ISO Annex A theme",
            "health_score": "Mean control health (%)"
        }
    )

    theme_fig.update_layout(showlegend=False, height=330)
    show_chart(theme_fig, key="iso_health_bar", alt="Horizontal bars of latest control health by ISO theme")

    st.subheader(
        "Control register and current status"
    )

    control_columns = [
        "control_id",
        "iso_reference",
        "iso_title",
        "csf_function",
        "owner",
        "testing_frequency",
        "test_date",
        "result",
        "health_score",
        "is_overdue",
        "never_tested"
    ]

    show_data(
        health_f[control_columns],
        "control_health_filtered"
    )


# ============================================================
# 12. RISK HEATMAP & ALERTS PAGE
# ============================================================

else:

    st.subheader(
        "5 x 5 risk heatmap - likelihood x impact"
    )

    st.caption(
        "Each cell shows the number of open risks. "
        "Click a tile or use the likelihood and impact dropdowns "
        "below to inspect a specific cell. Blue, white and coral encode open-risk "
        "counts only; the colours do not represent risk severity or negative values."
    )

    st.info(f"[Design choice] Risk basis: {risk_basis}. Recomputed likelihood = min(1 + failed tests "
            "+ linked incidents, 5), over (2025-10-31, 2026-10-31]. Partial is not a Fail. "
            "Impact comes from the control register; source CSVs remain unchanged.")

    # Create the 5x5 count matrix
    risk_grid = (
        open_risks
        .groupby(["likelihood", "impact"])
        .size()
        .unstack(fill_value=0)
        .reindex(
            index=[5, 4, 3, 2, 1],
            columns=[1, 2, 3, 4, 5],
            fill_value=0
        )
    )

    # Rounded tiles keep the same underlying count matrix and hover values.
    heatmap_fig = rounded_risk_heatmap(risk_grid)

    # Native point selection updates the existing dropdowns before the rerun.
    matrix_col, mix_col = st.columns([1.65, 1])
    with matrix_col:
        show_chart(heatmap_fig, key="risk_count_heatmap", on_select=select_heatmap_cell,
                   selection_mode="points", alt="Five by five matrix of open risk counts; select a tile or use dropdowns")
    with mix_col:
        st.caption("OPEN RISK DISTRIBUTION")
        show_chart(risk_donut(open_risks), key="risk_mix_donut", alt="Open risks grouped by risk band")
        st.caption("Band colors describe risk level; heatmap intensity describes record count.")

    # ========================================================
    # FIXED HEATMAP DRILL-DOWN
    # ========================================================

    st.subheader("Inspect a risk heatmap cell")

    st.caption(
        "Choose the likelihood and impact values "
        "of the cell you want to investigate."
    )

    likelihood_col, impact_col = st.columns(2)

    with likelihood_col:
        selected_likelihood = st.selectbox(
            "Likelihood",
            options=[1, 2, 3, 4, 5],
            index=4,
            key="heatmap_likelihood"
        )

    with impact_col:
        selected_impact = st.selectbox(
            "Impact",
            options=[1, 2, 3, 4, 5],
            index=4,
            key="heatmap_impact"
        )

    # Select matching risk records
    selected_risks = open_risks.loc[
        open_risks["likelihood"].eq(
            selected_likelihood
        )
        &
        open_risks["impact"].eq(
            selected_impact
        )
    ].copy()

    selected_score = (
        selected_likelihood * selected_impact
    )

    # Classify selected risk cell
    if selected_score <= 4:
        selected_band_name = "Low"
    elif selected_score <= 9:
        selected_band_name = "Medium"
    elif selected_score <= 16:
        selected_band_name = "High"
    else:
        selected_band_name = "Critical"

    st.info(
        f"Selected cell: "
        f"Likelihood {selected_likelihood} x "
        f"Impact {selected_impact} | "
        f"Risk score: {selected_score} | "
        f"Risk band: {selected_band_name} | "
        f"Matching open risks: {len(selected_risks)}"
    )

    if selected_risks.empty:
        st.warning(
            "No open risks exist in this cell "
            "under the current filters."
        )

    st.subheader(
        "Risk records matching selected cell"
    )

    risk_columns = [
        "risk_id",
        "control_id",
        "iso_title",
        "likelihood",
        "impact",
        "risk_score",
        "risk_level",
        "status",
        "owner"
    ]

    show_data(
        selected_risks[risk_columns],
        "risk_heatmap_records"
    )

    with st.expander("Risk calculation evidence and full filtered register"):
        evidence = recomputed_risks.loc[recomputed_risks["risk_id"].isin(risks_f["risk_id"])].copy()
        show_data(evidence, "risk_calculation_evidence")
        st.caption("[Design choice] Comparison uses source events at the fixed report date, "
                   "independent of the historical event filter. Each row keeps the stored values for comparison.")

    # ========================================================
    # 13. RULE-BASED EXCEPTION ALERTS
    # ========================================================

    st.subheader(
        "Rule-based exception alerts (prototype)"
    )

    alerts = []

    # Latest test failure and overdue test
    for record in health_f.itertuples():

        if record.result == "Fail":
            alerts.append({
                "Control / Incident": record.control_id,
                "Rule": "LATEST_TEST_FAIL",
                "Details": f"Most recent test failed on {record.test_date:%Y-%m-%d}"
            })

        if record.is_overdue or record.never_tested:
            overdue_detail = "No test recorded by the report date"
            if not record.never_tested:
                threshold = 1.5 * FREQUENCY_DAYS[str(record.testing_frequency).strip().lower()]
                elapsed = (AS_OF - record.test_date).days
                overdue_detail = (f"Last test {record.test_date:%Y-%m-%d}; "
                                  f"{elapsed} days since test > {threshold:g}-day threshold")
            alerts.append({
                "Control / Incident": record.control_id,
                "Rule": "TEST_OVERDUE",
                "Details": overdue_detail
            })

    # Snapshot rule: use full history through AS_OF, like latest-test health.
    consecutive_ids = consecutive_failures(
        tests.loc[tests["control_id"].isin(eligible_ids)],
        AS_OF
    )

    for control_id in consecutive_ids:
        latest_two = tests.loc[tests["control_id"].eq(control_id)].sort_values(
            ["test_date", "test_id"]).tail(2)
        evidence_text = "; ".join(f"{r.test_id} ({r.test_date:%Y-%m-%d}): {r.result}"
                                  for r in latest_two.itertuples())
        alerts.append({
            "Control / Incident": control_id,
            "Rule": "CONSECUTIVE_FAILURES",
            "Details": evidence_text
        })

    # Unresolved test findings
    unresolved = unresolved_findings(tests_f)

    for _, record in unresolved.iterrows():

        alerts.append({
            "Control / Incident": record["control_id"],
            "Rule": "OPEN_EXCEPTION",
            "Details": (
                f"{record['test_id']}: "
                "unresolved control finding"
            )
        })

    # Critical open incidents
    critical_incidents = incidents_f.loc[
        incidents_f["severity"].eq("Critical")
        &
        incidents_f["status"]
        .astype(str)
        .str.strip()
        .str.casefold()
        .eq("open")
    ]

    for _, record in critical_incidents.iterrows():

        alerts.append({
            "Control / Incident": record["incident_id"],
            "Rule": "CRITICAL_OPEN_INCIDENT",
            "Details": "Critical incident remains open"
        })

    # Required risk-owner rule: never substitute the control department.
    for record in missing_risk_owners(open_risks).itertuples():
        alerts.append({
            "Control / Incident": record.control_id,
            "Rule": "HIGH_CRITICAL_MISSING_OWNER",
            "Details": f"{record.risk_id}: {record.risk_level} {record.status} risk has no assigned risk owner"
        })

    # Design choice: complete months with three complete preceding months.
    spikes = incident_spikes(incident_history_f, AS_OF, FIRST_DATE)
    for record in spikes.itertuples():
        period = pd.Period(record.month, freq="M")
        if period.end_time.normalize() < start or period.start_time > end:
            continue
        alerts.append({
            "Control / Incident": record.month,
            "Rule": "INCIDENT_SPIKE",
            "Details": (f"{record.count} incidents; previous 3 months total={record.previous_3_total}; "
                        f"mean={record.baseline:.2f}; threshold={record.threshold:.2f} "
                        "(>=10 and >=2 * mean; complete calendar months)")
        })

    # Convert alerts to table
    alert_table = pd.DataFrame(
        alerts,
        columns=[
            "Control / Incident",
            "Rule",
            "Details"
        ]
    )

    st.caption(
        "Alerts show recorded conditions, "
        "not proven causes. Historical exception "
        "alerts follow the selected date range. Snapshot alerts use all tests through the report date. "
        "[Design choice] Spike alerts use full months and their previous three-month mean; "
        "the event range selects which month alerts appear. Thresholds require supervisor approval."
    )

    show_data(
        alert_table,
        "exception_alerts"
    )

    with st.expander("Public synthetic scenario checks"):
        if all_controls_selected and start == FIRST_DATE and end == AS_OF and set(selected_bands) == set(risk_bands):
            scenario_checks = public_scenario_results(alert_table)
            st.table(scenario_checks)
            st.caption("Public set: six expected alerts and one expected non-alert. "
                       "These checks do not assess every possible false alert and do not replace the private answer-key review.")
        else:
            st.caption("Reset control, risk-band and event-date filters to run the public baseline checks.")



# ============================================================
# 14. DASHBOARD FOOTER
# ============================================================

st.divider()

st.caption(
    "SYNTHETIC DATA ONLY | Prototype for academic "
    "and internship demonstration. "
    "No production integrations or real client data. "
    "Risk and alert thresholds are project-specific "
    "design choices pending supervisor approval."
)
