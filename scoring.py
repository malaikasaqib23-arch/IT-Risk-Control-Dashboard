"""Project-specific IT risk scoring rules (not official NIST/ISO scales)."""
import pandas as pd

RESULT_POINTS = {'Pass': 100, 'Partial': 50, 'Fail': 0}
FREQUENCY_DAYS = {'monthly':30, 'quarterly':90, 'semi-annual':180,
                  'semi-annually':180, 'semiannual':180, 'semiannually':180,
                  'annual':365, 'annually':365, 'yearly':365}


def health_score(result):
    if result not in RESULT_POINTS:
        raise ValueError(f'Unknown control test result: {result}')
    return RESULT_POINTS[result]


def risk_score(likelihood, impact):
    if not (1 <= likelihood <= 5 and 1 <= impact <= 5):
        raise ValueError('Likelihood and impact must each be 1..5')
    return int(likelihood * impact)


def risk_band(score):
    if not 1 <= score <= 25:
        raise ValueError('Risk score must be 1..25')
    if score <= 4: return 'Low'
    if score <= 9: return 'Medium'
    if score <= 16: return 'High'
    return 'Critical'


def overdue_test(last_test, frequency, as_of):
    """Never tested is separately flagged; does not silently count as overdue."""
    if pd.isna(last_test): return False
    days = FREQUENCY_DAYS.get(str(frequency).strip().lower())
    if days is None: raise ValueError(f'Unknown testing frequency: {frequency}')
    return (pd.Timestamp(as_of) - pd.Timestamp(last_test)).days > 1.5 * days


def likelihood_from_events(events):
    if events < 0: raise ValueError('Events cannot be negative')
    return min(int(events) + 1, 5)


def latest_control_tests(tests):
    return (tests.sort_values(['test_date', 'test_id'])
            .drop_duplicates('control_id', keep='last').copy())


def control_health_table(controls, tests, as_of):
    t = tests.loc[tests['test_date'].le(pd.Timestamp(as_of))]
    latest = latest_control_tests(t)
    out = controls.merge(latest[['control_id','test_date','result']], on='control_id', how='left')
    out['health_score'] = out['result'].map(RESULT_POINTS)
    invalid = out['result'].notna() & out['health_score'].isna()
    if invalid.any(): raise ValueError('Unknown results in test data')
    out['never_tested'] = out['test_date'].isna()
    out['is_overdue'] = out.apply(lambda r: overdue_test(r['test_date'],r['testing_frequency'],as_of),axis=1)
    return out


def monthly_incidents(incidents, as_of):
    periods = pd.period_range(pd.Timestamp(as_of).to_period('M')-11,
                              pd.Timestamp(as_of).to_period('M'),freq='M')
    inc=incidents.loc[incidents['incident_date'].le(pd.Timestamp(as_of))].copy()
    inc['month']=inc['incident_date'].dt.to_period('M')
    inc=inc[inc['month'].isin(periods)]
    pt=pd.crosstab(inc['month'],inc['severity']).reindex(periods,fill_value=0)
    for col in ['Low','Medium','High','Critical']:
        if col not in pt.columns:pt[col]=0
    pt=pt[['Low','Medium','High','Critical']]
    pt['Total']=pt.sum(axis=1)
    pt.index=pt.index.astype(str)
    pt.index.name='Month'
    return pt.reset_index()
