"""Generate reproducible, entirely fictional IT-risk dashboard data.
Run: python generate_data.py
Requires: pandas, numpy. Uses data/SYNTHETIC_controls_DRAFT.csv; --output-dir selects an isolated destination.
"""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from synthetic_links import complete_synthetic_links

parser = argparse.ArgumentParser(description="Generate SYNTHETIC demo tables; never use firm data.")
parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "data")
args = parser.parse_args()
ROOT = args.output_dir.resolve()
ROOT.mkdir(parents=True, exist_ok=True)
CONTROL_SOURCE = Path(__file__).resolve().parent / "data" / "SYNTHETIC_controls_DRAFT.csv"
SEED = 202611
AS_OF = pd.Timestamp('2026-10-31')
START = pd.Timestamp('2025-11-01')
rng = np.random.default_rng(SEED)
controls = pd.read_csv(CONTROL_SOURCE, encoding='utf-8-sig', dtype={'control_id': str})
assert len(controls) == 19 and controls.control_id.is_unique
ids = controls.control_id.tolist()
frequency_months = {'Monthly':1, 'Quarterly':3, 'Semi-annual':6, 'Semi-annually':6, 'Annually':12, 'Annual':12}
assert controls.testing_frequency.isin(frequency_months).all(), controls.testing_frequency.unique()

# Regular test events, plus follow-up verification tests for realistic testing volume.
records = []
for c in controls.itertuples(index=False):
    months = frequency_months[c.testing_frequency]
    dates = pd.date_range(START + pd.Timedelta(days=int(rng.integers(0, 20))), AS_OF, freq='MS')
    if len(dates) == 0:
        dates = pd.DatetimeIndex([START + pd.Timedelta(days=15)])
    for i, d in enumerate(dates):
        if i % months == 0:
            date = min(d + pd.Timedelta(days=int(rng.integers(0, 15))), AS_OF)
            records.append([c.control_id, date, 'Scheduled'])
# Force CTRL-014 to have no recent test: overdue alert while retaining earlier history.
records = [r for r in records if not (r[0]=='CTRL-014' and r[1] > pd.Timestamp('2026-06-15'))]
# Add follow-up checks without altering each control's scheduled testing frequency.
while len(records) < 300:
    cid = str(rng.choice(ids))
    day = START + pd.Timedelta(days=int(rng.integers(0, (AS_OF-START).days+1)))
    if cid == 'CTRL-014' and day > pd.Timestamp('2026-06-15'):
        continue
    records.append([cid, day, 'Follow-up verification'])
records = sorted(records, key=lambda r: (r[1], r[0], r[2]))

# The result generator uses control-specific failure tendencies and worsening trends.
rows=[]
for i,(cid, date, kind) in enumerate(records,1):
    idx = ids.index(cid)
    failure_prob = 0.07 + (idx % 5)*0.035
    if cid in ('CTRL-009','CTRL-012','CTRL-016') and date >= pd.Timestamp('2026-06-01'):
        failure_prob += 0.27
    result = str(rng.choice(['Pass','Partial','Fail'], p=[1-failure_prob-0.13,0.13,failure_prob]))
    finding = '' if result=='Pass' else ('Evidence incomplete' if result=='Partial' else 'Control requirement not met')
    rem_status = 'Not Required' if result=='Pass' else str(rng.choice(['Open','In Progress','Closed'],p=[0.40,0.40,0.20]))
    due = date + pd.Timedelta(days=30) if result!='Pass' else pd.NaT
    next_due = date + pd.DateOffset(months=frequency_months[controls.loc[controls.control_id==cid,'testing_frequency'].iloc[0]])
    rows.append(dict(test_id=f'TEST-{i:04d}',control_id=cid,test_date=date.date().isoformat(),result=result,
        tested_by='Synthetic Internal Audit Team',evidence_reference=f'SYN-EVID-{i:04d}',findings=finding,
        remediation_due_date=due.date().isoformat() if pd.notna(due) else '',remediation_status=rem_status,
        next_test_due=next_due.date().isoformat(),test_type=kind))
tests=pd.DataFrame(rows)
# Known scenario: three consecutive failed results for a specific control.
indices = tests.index[tests.control_id=='CTRL-009'].tolist()[-3:]
for j in indices:
    tests.loc[j,['result','findings','remediation_status']] = ['Fail','Privileged access review failed','Open']
    tests.loc[j,'remediation_due_date']=(pd.Timestamp(tests.loc[j,'test_date'])+pd.Timedelta(days=30)).date().isoformat()
# Ensure one latest partial test for a separate rule scenario.
idx = tests.index[tests.control_id=='CTRL-013'].tolist()[-1]
tests.loc[idx,['result','findings','remediation_status']] = ['Partial','Configuration baseline evidence incomplete','Open']
tests.loc[idx,'remediation_due_date']=(pd.Timestamp(tests.loc[idx,'test_date'])+pd.Timedelta(days=30)).date().isoformat()

# Incidents: weighted toward controls with failed tests; September spike is deliberate.
failed_counts=tests.loc[tests.result=='Fail'].groupby('control_id').size().reindex(ids,fill_value=0).to_numpy()
weights=(1+failed_counts).astype(float); weights /= weights.sum()
incident_types=['Unauthorized Access','Malware','Service Disruption','Suspicious Activity','Data Exposure','Configuration Issue']
inc=[]
for i in range(1,111):
    if i<=24:
        date=pd.Timestamp('2026-09-01')+pd.Timedelta(days=int(rng.integers(0,30)))
    else:
        date=START+pd.Timedelta(days=int(rng.integers(0,(AS_OF-START).days+1)))
    cid = str(rng.choice(ids,p=weights)) if rng.random()<0.90 else ''
    sev=str(rng.choice(['Low','Medium','High','Critical'],p=[.30,.40,.23,.07]))
    status=str(rng.choice(['Open','In Progress','Resolved','Closed'],p=[.18,.17,.45,.20]))
    resolved=(date+pd.Timedelta(days=int(rng.integers(1,21)))) if status in ('Resolved','Closed') else pd.NaT
    if pd.notna(resolved) and resolved>AS_OF: status='In Progress'; resolved=pd.NaT
    inc.append(dict(incident_id=f'INC-{i:04d}',control_id=cid,incident_date=date.date().isoformat(),
        incident_type=str(rng.choice(incident_types)),severity=sev,
        description=f'SYNTHETIC {sev.lower()} security event for dashboard testing',assigned_team='Synthetic SOC',
        status=status,resolved_date=resolved.date().isoformat() if pd.notna(resolved) else ''))
incidents=complete_synthetic_links(pd.DataFrame(inc))
# Guaranteed critical open incident (high/critical incident alert).
incidents.loc[0,['severity','status','resolved_date']]=['Critical','Open','']

# One risk per control. Likelihood follows exactly the Week 2 12-month event-count rule.
risks=[]
for i,c in enumerate(controls.itertuples(index=False),1):
    failures=int(((tests.control_id==c.control_id)&(tests.result=='Fail')).sum())
    linked=int((incidents.control_id==c.control_id).sum())
    likelihood=min(5,1+failures+linked)
    impact=int(c.impact_score)
    score=likelihood*impact
    level='Low' if score<=4 else 'Medium' if score<=9 else 'High' if score<=16 else 'Critical'
    risks.append(dict(risk_id=f'RISK-{i:03d}',control_id=c.control_id,
        risk_description=f'SYNTHETIC risk associated with {c.iso_title}',category='IT Security',
        likelihood=likelihood,impact=impact,risk_score=score,risk_level=level,
        owner=c.owner,treatment_plan='Review control evidence and remediate weaknesses',
        status='Open' if i%4 else 'In Progress',review_date='2026-11-30'))
risk_register=pd.DataFrame(risks)

for name,df in [('control_tests',tests),('incidents',incidents),('risk_register',risk_register)]:
    df.to_csv(ROOT/f'SYNTHETIC_{name}.csv',index=False,encoding='utf-8-sig')
controls.to_csv(ROOT / 'SYNTHETIC_controls_DRAFT.csv', index=False, encoding='utf-8-sig')
print(f'Generated {len(controls)} controls, {len(tests)} tests, {len(incidents)} incidents, {len(risk_register)} risks.')
print('Fixed random seed:',SEED,'| Reference date:',AS_OF.date())
