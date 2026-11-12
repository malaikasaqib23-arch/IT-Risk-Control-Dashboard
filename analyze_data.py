"""Week 3: Eight IT Risk & Control Monitoring Dashboard KPIs.

Uses SYNTHETIC CSV data and the fixed reporting date from the generator.
Run: python analyze_data.py
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent / "data"
AS_OF = pd.Timestamp('2026-10-31')


def load_csv(*names):
    for name in names:
        path = ROOT / name
        if path.exists():
            return pd.read_csv(path, encoding='utf-8-sig')
    raise FileNotFoundError(
        f"Could not find {names} in {ROOT}. Keep the four SYNTHETIC CSV files "
        "beside analyze_data.py, or update ROOT."
    )


controls = load_csv('SYNTHETIC_controls_DRAFT.csv', 'SYNTHETIC_controls.csv')
tests = load_csv('SYNTHETIC_control_tests.csv')
incidents = load_csv('SYNTHETIC_incidents.csv')
risks = load_csv('SYNTHETIC_risk_register.csv')

for col in ('test_date', 'remediation_due_date', 'next_test_due'):
    tests[col] = pd.to_datetime(tests[col], errors='coerce')
for col in ('incident_date', 'resolved_date'):
    incidents[col] = pd.to_datetime(incidents[col], errors='coerce')
risks['review_date'] = pd.to_datetime(risks['review_date'], errors='coerce')

# Keep records dated on or before the reporting date.
tests = tests.loc[tests['test_date'].le(AS_OF)].copy()
incidents = incidents.loc[incidents['incident_date'].le(AS_OF)].copy()

# Normalize text only for comparison; don't modify the original CSV files.
for df, cols in (
    (tests, ['result', 'remediation_status']),
    (incidents, ['severity', 'status']),
    (risks, ['risk_level', 'status']),
):
    for col in cols:
        df[col] = df[col].astype('string').str.strip()


def percent(numerator, denominator):
    return numerator / denominator * 100 if denominator else float('nan')


def display_percent(value):
    return 'N/A' if pd.isna(value) else f'{value:.2f}%'


print(f'REPORTING DATE: {AS_OF.date()}')
print(f'DATASETS: {len(controls)} controls, {len(tests)} tests, '
      f'{len(incidents)} incidents, {len(risks)} risks')

# KPI 1 — Overall Control Health: most recent test per control.
latest = (
    tests.sort_values(['test_date', 'test_id'])
    .drop_duplicates('control_id', keep='last')
    .copy()
)
score_map = {'Pass': 100, 'Partial': 50, 'Fail': 0}
latest['health_score'] = latest['result'].map(score_map)
if latest['health_score'].isna().any():
    raise ValueError('Unexpected test result; cannot calculate health.')
health = latest['health_score'].mean()
coverage_count = latest['control_id'].nunique()
coverage = percent(coverage_count, len(controls))
print('\n--- KPI 1: Overall Control Health ---')
print('Overall Control Health:', display_percent(health))
print(f'Tested Controls: {coverage_count}/{len(controls)}')
print('Testing Coverage:', display_percent(coverage))

# KPI 2 — Pass rate across all historical tests.
result_counts = tests['result'].value_counts()
passed = int(result_counts.get('Pass', 0))
partial = int(result_counts.get('Partial', 0))
failed = int(result_counts.get('Fail', 0))
print('\n--- KPI 2: Control Test Pass Rate ---')
print(f'Total Tests: {len(tests)} | Pass: {passed} | Partial: {partial} | Fail: {failed}')
print('Control Test Pass Rate:', display_percent(percent(passed, len(tests))))

# KPI 3 — Overdue if elapsed days > 1.5 x scheduled interval.
# Handles the actual CSV spellings 'Annually' and 'Semi-annually'.
frequency_days = {
    'monthly': 30,
    'quarterly': 90,
    'semi-annual': 180,
    'semi-annually': 180,
    'semiannual': 180,
    'semiannually': 180,
    'annual': 365,
    'annually': 365,
    'yearly': 365,
}
last_dates = tests.groupby('control_id')['test_date'].max().rename('last_test_date')
overdue = controls.merge(last_dates, on='control_id', how='left')
overdue['frequency_days'] = (
    overdue['testing_frequency'].astype('string').str.strip().str.lower()
    .map(frequency_days)
)
if overdue['frequency_days'].isna().any():
    unknown = overdue.loc[overdue['frequency_days'].isna(), 'testing_frequency'].unique()
    raise ValueError(f'Unrecognized testing frequencies: {list(unknown)}')
overdue['days_since_test'] = (AS_OF - overdue['last_test_date']).dt.days
overdue['threshold_days'] = overdue['frequency_days'] * 1.5
overdue['never_tested'] = overdue['last_test_date'].isna()
overdue['is_overdue'] = (
    overdue['last_test_date'].notna()
    & overdue['days_since_test'].gt(overdue['threshold_days'])
)
print('\n--- KPI 3: Overdue Control Tests ---')
print('Overdue Controls:', int(overdue['is_overdue'].sum()))
print('Never Tested (reported separately):', int(overdue['never_tested'].sum()))
print('Overdue control details:')
cols = ['control_id', 'testing_frequency', 'last_test_date', 'days_since_test']
print(overdue.loc[overdue['is_overdue'], cols].to_string(index=False) if overdue['is_overdue'].any() else 'None')

# Open risks includes In Progress (not closed/resolved).
open_risks = risks[risks['status'].str.casefold().isin(['open', 'in progress'])].copy()
open_risks['risk_score'] = pd.to_numeric(open_risks['risk_score'], errors='coerce')
if open_risks['risk_score'].isna().any():
    raise ValueError('Open risk contains an invalid risk score.')

# KPI 4 — Number of open High/Critical risks (score >= 10).
high_critical = open_risks[open_risks['risk_score'].ge(10)]
print('\n--- KPI 4: High & Critical Risks ---')
print('Open High/Critical Risks:', len(high_critical))
print('High:', int(high_critical['risk_level'].eq('High').sum()),
      '| Critical:', int(high_critical['risk_level'].eq('Critical').sum()))

# KPI 5 — Critical risks / all open risks.
critical_count = int(open_risks['risk_level'].eq('Critical').sum())
print('\n--- KPI 5: Critical Risk Exposure ---')
print(f'Critical Open Risks: {critical_count}/{len(open_risks)}')
print('Critical Risk Exposure:', display_percent(percent(critical_count, len(open_risks))))

# KPI 6 — Monthly incident trend, split by severity.
# Reindex to include months with zero incidents.
start_month = (AS_OF - pd.DateOffset(months=11)).to_period('M')
months = pd.period_range(start_month, AS_OF.to_period('M'), freq='M')
trend_data = incidents[
    incidents['incident_date'].dt.to_period('M').isin(months)
].copy()
trend_data['month'] = trend_data['incident_date'].dt.to_period('M')
monthly = pd.crosstab(trend_data['month'], trend_data['severity'])
monthly = monthly.reindex(index=months, fill_value=0)
for severity in ['Low', 'Medium', 'High', 'Critical']:
    if severity not in monthly.columns:
        monthly[severity] = 0
monthly = monthly[['Low', 'Medium', 'High', 'Critical']]
monthly['Total'] = monthly.sum(axis=1)
monthly.index = monthly.index.astype(str)
monthly.index.name = 'Month'
print('\n--- KPI 6: Monthly Security Incidents ---')
print(monthly.to_string())
print('Incidents in 12-month chart:', int(monthly['Total'].sum()))

# KPI 7 — Prototype exception proxy: unresolved findings from tests.
# Count test records, not unique controls. Pass results are not findings.
open_remediation = tests[
    tests['remediation_status'].str.casefold().isin(['open', 'in progress'])
].copy()
open_exceptions = open_remediation[
    open_remediation['result'].isin(['Partial', 'Fail'])
    & open_remediation['findings'].notna()
    & open_remediation['findings'].astype(str).str.strip().ne('')
]
print('\n--- KPI 7: Open Control Exceptions ---')
print('Unresolved finding records:', len(open_exceptions))
print('Affected controls:', open_exceptions['control_id'].nunique())

# KPI 8 — Open remediations overdue as of reporting date.
# Missing due dates are excluded from overdue numerator and reported separately.
with_due = open_remediation['remediation_due_date'].notna()
overdue_remediation = (
    with_due & open_remediation['remediation_due_date'].lt(AS_OF)
)
print('\n--- KPI 8: Overdue Remediation Rate ---')
print('Open Remediations:', len(open_remediation))
print('Overdue Open Remediations:', int(overdue_remediation.sum()))
print('Open Remediations Missing Due Date:', int((~with_due).sum()))
print('Overdue Remediation Rate:',
      display_percent(percent(int(overdue_remediation.sum()), len(open_remediation))))

print('\nAll eight KPI calculations completed.')
