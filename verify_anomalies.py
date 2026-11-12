"""Verify the six seeded scenarios in the synthetic Week 3 data.
Run beside SYNTHETIC_control_tests.csv, SYNTHETIC_incidents.csv and the controls CSV.
This script does not modify source data.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent / "data"
REFERENCE_DATE = pd.Timestamp('2026-10-31')

def load(name):
    return pd.read_csv(ROOT / name)

tests = load('SYNTHETIC_control_tests.csv')
incidents = load('SYNTHETIC_incidents.csv')
control_file = next((ROOT / n for n in ('SYNTHETIC_controls.csv', 'SYNTHETIC_controls_DRAFT.csv') if (ROOT / n).exists()), None)
if control_file is None:
    raise FileNotFoundError('Controls CSV not found')
controls = pd.read_csv(control_file)
tests['test_date'] = pd.to_datetime(tests['test_date'])
incidents['incident_date'] = pd.to_datetime(incidents['incident_date'])
latest = tests.sort_values(['test_date', 'test_id']).drop_duplicates('control_id', keep='last')

results = []
def check(label, condition, detail):
    results.append(bool(condition))
    print(f"{'PASS' if condition else 'CHECK'} | {label} | {detail}")

print('SYNTHETIC ANOMALY VERIFICATION | as of', REFERENCE_DATE.date())
print('-' * 78)

# 1: latest test fails, and last 3 historical tests fail
history = tests.loc[tests.control_id.eq('CTRL-009')].sort_values(['test_date', 'test_id'])
last_three = history.tail(3)
check('1 CTRL-009 repeated failures', len(last_three) == 3 and last_three.result.eq('Fail').all(),
      f'last 3 results: {last_three.result.tolist()}')

# 2: overdue under project-defined 1.5x monthly cadence (30 days)
last_backup = tests.loc[tests.control_id.eq('CTRL-014'), 'test_date'].max()
days = (REFERENCE_DATE - last_backup).days if pd.notna(last_backup) else None
check('2 CTRL-014 overdue monthly test', days is not None and days > 45,
      f'last test: {last_backup.date() if pd.notna(last_backup) else "none"}; days: {days}; threshold: 45')

# 3: incident spike rule: >= 2x median of other months AND >= 10 incidents
monthly = incidents.groupby(incidents.incident_date.dt.to_period('M')).size()
sept = monthly.get(pd.Period('2026-09'), 0)
other_median = monthly.drop(pd.Period('2026-09'), errors='ignore').median()
spike = sept >= 10 and sept >= 2 * other_median
check('3 September 2026 incident spike', spike,
      f'September: {sept}; median other months: {other_median}; rule: >=10 and >=2x median')

# 4: latest Partial test has unresolved finding
c13 = latest.loc[latest.control_id.eq('CTRL-013')]
if not c13.empty:
    r = c13.iloc[0]
    finding = pd.notna(r['findings']) and bool(str(r['findings']).strip())
    unresolved = str(r['remediation_status']).strip().lower() not in ('closed', 'completed', 'resolved')
    condition = r['result'] == 'Partial' and finding and unresolved
    detail = f"result: {r['result']}; remediation status: {r['remediation_status']}; finding present: {finding}"
else:
    condition, detail = False, 'control not found'
check('4 CTRL-013 open exception', condition, detail)

# 5: critical open incident
inc = incidents.loc[incidents.incident_id.eq('INC-0001')]
condition = not inc.empty and inc.iloc[0]['severity'] == 'Critical' and inc.iloc[0]['status'] == 'Open'
check('5 INC-0001 critical open incident', condition,
      f"severity: {inc.iloc[0]['severity'] if not inc.empty else 'missing'}; status: {inc.iloc[0]['status'] if not inc.empty else 'missing'}")

# 6: descriptive trends only, not a guaranteed PASS/FAIL
print('\n6 | STATISTICAL TREND (not a deterministic acceptance test)')
for cid in ['CTRL-009', 'CTRL-012', 'CTRL-016']:
    subset = tests.loc[tests.control_id.eq(cid)].copy()
    before = subset.loc[subset.test_date < pd.Timestamp('2026-07-01')]
    after = subset.loc[subset.test_date >= pd.Timestamp('2026-07-01')]
    def failure_rate(df):
        return f"{100 * df.result.eq('Fail').mean():.1f}% ({df.result.eq('Fail').sum()}/{len(df)})" if len(df) else 'N/A (0 tests)'
    print(f'  {cid}: before July 2026 {failure_rate(before)} | July onward {failure_rate(after)}')

print(f'\nDeterministic scenarios verified: {sum(results)}/{len(results)}')
print('Note: detection of these patterns does not prove their cause or measure false-positive rates.')
