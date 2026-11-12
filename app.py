
"""
IT Risk & Control Monitoring Dashboard
Week 4 Prototype v1

SYNTHETIC DATA ONLY
All risk thresholds are project design choices.
"""

from pathlib import Path
from calendar import monthrange

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from scoring import control_health_table, monthly_incidents


# ============================================================
# 1. CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

AS_OF = pd.Timestamp("2026-10-31")
FIRST_DATE = pd.Timestamp("2025-11-01")

MONTHS = pd.period_range(
    start=FIRST_DATE.to_period("M"),
    end=AS_OF.to_period("M"),
    freq="M"
)

MONTH_LABELS = [
    period.strftime("%B %Y")
    for period in MONTHS
]

st.set_page_config(
    page_title="IT Risk & Control Monitoring | SYNTHETIC",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# 2. LOAD SYNTHETIC DATA
# ============================================================

@st.cache_data
def load_data():

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

    return controls, tests, incidents, risks


controls, tests, incidents, risks = load_data()

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

risk_with_controls = risks.merge(
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

st.title("IT Risk & Control Monitoring Dashboard")

st.caption(
    "SYNTHETIC DATA ONLY | "
    "Reporting date: 31 October 2026 | "
    "Prototype v1 — project-defined risk rules"
)


# ============================================================
# 5. SIDEBAR FILTERS
# ============================================================

with st.sidebar:

    st.header("Dashboard filters")

    # NIST CSF filter
    functions = sorted(
        controls["csf_function"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_functions = st.multiselect(
        "NIST CSF function",
        options=functions,
        default=functions
    )

    # Owner filter
    owners = sorted(
        controls["owner"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_owners = st.multiselect(
        "Control owner",
        options=owners,
        default=owners
    )

    # Risk band filter
    risk_bands = [
        "Low",
        "Medium",
        "High",
        "Critical"
    ]

    selected_bands = st.multiselect(
        "Risk band",
        options=risk_bands,
        default=risk_bands
    )

    st.divider()

    # ========================================================
    # WORKING DATE FILTER - DROPDOWNS
    # ========================================================

    st.subheader("Event date range")

    st.caption("Select the month and day directly.")

    # Start month
    start_month_label = st.selectbox(
        "Start month",
        options=MONTH_LABELS,
        index=0,
        key="start_month"
    )

    start_period = MONTHS[
        MONTH_LABELS.index(start_month_label)
    ]

    # Start day
    start_days = list(
        range(
            1,
            monthrange(
                start_period.year,
                start_period.month
            )[1] + 1
        )
    )

    start_day = st.selectbox(
        "Start day",
        options=start_days,
        index=0,
        key="start_day"
    )

    # End month
    end_month_label = st.selectbox(
        "End month",
        options=MONTH_LABELS,
        index=len(MONTH_LABELS) - 1,
        key="end_month"
    )

    end_period = MONTHS[
        MONTH_LABELS.index(end_month_label)
    ]

    # End day
    end_days = list(
        range(
            1,
            monthrange(
                end_period.year,
                end_period.month
            )[1] + 1
        )
    )

    end_day = st.selectbox(
        "End day",
        options=end_days,
        index=len(end_days) - 1,
        key="end_day"
    )

    # Construct dates
    start = pd.Timestamp(
        year=start_period.year,
        month=start_period.month,
        day=start_day
    )

    end = pd.Timestamp(
        year=end_period.year,
        month=end_period.month,
        day=end_day
    )

    st.caption(
        f"Selected range: "
        f"{start:%Y-%m-%d} to {end:%Y-%m-%d}"
    )

    # Date validation
    if start > end:
        st.error(
            "Start date cannot be after end date. "
            "Please adjust the dropdowns."
        )
        st.stop()

    st.caption(
        "Date filters apply to historical incidents "
        "and tests. Current risk and control health "
        "are measured at the reporting date."
    )


# ============================================================
# 6. APPLY FILTERS
# ============================================================

eligible_ids = controls.loc[
    controls["csf_function"].isin(selected_functions)
    &
    controls["owner"].isin(selected_owners),
    "control_id"
]

health_f = health.loc[
    health["control_id"].isin(eligible_ids)
].copy()

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

incidents_f = incidents.loc[
    incidents["control_id"].isin(eligible_ids)
    &
    incidents["incident_date"].between(start, end)
].copy()

tests_f = tests.loc[
    tests["control_id"].isin(eligible_ids)
    &
    tests["test_date"].between(start, end)
].copy()


# ============================================================
# 7. CALCULATE FOUR HEADLINE KPIs
# ============================================================

# KPI 1: Overall control health
overall_health = health_f["health_score"].mean()

# Coverage
coverage = (
    100 * health_f["health_score"].notna().mean()
    if len(health_f)
    else float("nan")
)

# KPI 2: Controls tested on time
# Union avoids counting a never-tested, overdue control twice.
not_on_time = (
    health_f["is_overdue"].fillna(False)
    |
    health_f["never_tested"].fillna(False)
)

on_time_percentage = (
    100 * (~not_on_time).sum() / len(health_f)
    if len(health_f)
    else float("nan")
)

# KPI 3: Open High/Critical risks
high_critical_count = int(
    open_risks["risk_level"]
    .isin(["High", "Critical"])
    .sum()
)

# KPI 4: Last 90 days, intersected with event-date filter
last90_start = AS_OF - pd.Timedelta(days=89)

last90 = incidents_f.loc[
    incidents_f["incident_date"].between(
        last90_start,
        AS_OF
    )
]


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
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        label=f"Download {name} CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"SYNTHETIC_{name}.csv",
        mime="text/csv",
        key=f"download_{name}"
    )


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
        len(last90)
    )

    # Historical test pass rate
    pass_rate = (
        100 * tests_f["result"].eq("Pass").mean()
        if len(tests_f)
        else float("nan")
    )

    st.caption(
        f"Testing coverage: {fmt_pct(coverage)} | "
        f"Test pass rate: {fmt_pct(pass_rate)} | "
        f"Overdue controls: "
        f"{int(health_f['is_overdue'].sum())}"
    )

    st.info(
        "Control health, testing timeliness, and "
        "risk status are measured as of 31 October 2026. "
        "Incident activity and historical test results "
        "follow the selected event date range."
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

    st.plotly_chart(
        incident_fig,
        use_container_width=True
    )

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
        range_y=[0, 100],
        labels={
            "csf_function": "NIST CSF function",
            "health_score": "Mean control health (%)"
        }
    )

    st.plotly_chart(
        function_fig,
        use_container_width=True
    )

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
        x="iso_theme",
        y="health_score",
        range_y=[0, 100],
        labels={
            "iso_theme": "ISO Annex A theme",
            "health_score": "Mean control health (%)"
        }
    )

    st.plotly_chart(
        theme_fig,
        use_container_width=True
    )

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
        "Use the likelihood and impact dropdowns "
        "below to inspect a specific cell."
    )

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

    # Heatmap visualization
    heatmap_fig = go.Figure(
        data=go.Heatmap(
            z=risk_grid.values,
            x=[1, 2, 3, 4, 5],
            y=[5, 4, 3, 2, 1],
            colorscale="YlOrRd",
            showscale=True,
            text=risk_grid.values,
            texttemplate="%{text}",
            hovertemplate=(
                "Impact: %{x}"
                "<br>Likelihood: %{y}"
                "<br>Open risks: %{z}"
                "<extra></extra>"
            )
        )
    )

    heatmap_fig.update_layout(
        xaxis_title="Impact",
        yaxis_title="Likelihood",
        height=420
    )

    # Display chart without unreliable click selection
    st.plotly_chart(
        heatmap_fig,
        use_container_width=True
    )

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
                "Details": "Most recent test failed"
            })

        if record.is_overdue or record.never_tested:
            alerts.append({
                "Control / Incident": record.control_id,
                "Rule": "TEST_OVERDUE",
                "Details": (
                    "Control is overdue or "
                    "has never been tested"
                )
            })

    # Unresolved test findings
    unresolved = tests_f.loc[
        tests_f["result"].isin(["Partial", "Fail"])
        &
        tests_f["remediation_status"]
        .astype(str)
        .str.strip()
        .str.casefold()
        .isin(["open", "in progress"])
        &
        tests_f["findings"].notna()
    ]

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

    # Monthly incident spikes
    monthly = monthly_incidents(
        incidents_f,
        AS_OF
    )

    for _, record in monthly.iterrows():

        baseline = monthly.loc[
            monthly["Month"].ne(record["Month"]),
            "Total"
        ].median()

        count = int(record["Total"])

        # Existing prototype spike threshold
        if count >= 10 and count >= 2 * baseline:

            alerts.append({
                "Control / Incident": record["Month"],
                "Rule": "INCIDENT_SPIKE",
                "Details": (
                    f"{count} incidents versus "
                    f"{baseline:g} other-month median"
                )
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
        "alerts follow the selected date range."
    )

    show_data(
        alert_table,
        "exception_alerts"
    )


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
