"""Run: python test_data_quality.py (after generate_data.py)."""
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parent / "data"
c=pd.read_csv(ROOT/'SYNTHETIC_controls_DRAFT.csv')
t=pd.read_csv(ROOT/'SYNTHETIC_control_tests.csv')
i=pd.read_csv(ROOT/'SYNTHETIC_incidents.csv')
r=pd.read_csv(ROOT/'SYNTHETIC_risk_register.csv')
checks=[]
def check(name,condition):
    checks.append((name,bool(condition)))
    if not condition: raise AssertionError(name)
for label,df,key in [('controls',c,'control_id'),('tests',t,'test_id'),('incidents',i,'incident_id'),('risks',r,'risk_id')]:
    check(label+' unique, nonempty PK',df[key].notna().all() and df[key].is_unique)
for label,df in [('tests',t),('incidents',i),('risks',r)]:
    check(label+' valid control FK',df.control_id.dropna().isin(c.control_id).all())
check('test result allowed',t.result.isin(['Pass','Partial','Fail']).all())
check('remediation status allowed',t.remediation_status.isin(['Not Required','Open','In Progress','Closed']).all())
check('incident severity allowed',i.severity.isin(['Low','Medium','High','Critical']).all())
check('incident status allowed',i.status.isin(['Open','In Progress','Resolved','Closed']).all())
check('risk ratings in 1..5',r.likelihood.between(1,5).all() and r.impact.between(1,5).all())
check('risk scores match', (r.risk_score==r.likelihood*r.impact).all())
def band(x): return 'Low' if x<=4 else 'Medium' if x<=9 else 'High' if x<=16 else 'Critical'
check('risk bands match', (r.risk_level==r.risk_score.map(band)).all())
start=pd.Timestamp('2025-11-01'); end=pd.Timestamp('2026-10-31')
for label,df,datecol in [('tests',t,'test_date'),('incidents',i,'incident_date')]:
    dates=pd.to_datetime(df[datecol],errors='coerce')
    check(label+' valid historical dates',dates.notna().all() and dates.between(start,end).all())
check('resolved incidents have resolved date',i.loc[i.status.isin(['Resolved','Closed']),'resolved_date'].notna().all())
check('open incidents have no resolved date',i.loc[i.status.isin(['Open','In Progress']),'resolved_date'].isna().all())
check('required evidence present',t.evidence_reference.notna().all())
check('historical tests preserved',t.groupby('control_id').size().min()>1)
check('data volume',len(c)==19 and len(t)==300 and len(i)==110 and len(r)==19)
print('\n'.join('PASS | '+name for name,_ in checks))
print(f'\n{len(checks)} / {len(checks)} required checks passed')
(ROOT/'SYNTHETIC_data_quality_results.txt').write_text('\n'.join('PASS | '+name for name,_ in checks)+'\n',encoding='utf-8')
