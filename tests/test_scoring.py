import pandas as pd
import pytest
from scoring import (health_score,risk_score,risk_band,overdue_test,
                     likelihood_from_events,latest_control_tests)

@pytest.mark.parametrize('result,score',[('Pass',100),('Partial',50),('Fail',0)])
def test_health(result,score): assert health_score(result)==score

def test_invalid_result():
    with pytest.raises(ValueError): health_score('Unknown')

def test_risk_example_from_guide():
    assert likelihood_from_events(3)==4
    assert risk_score(4,5)==20
    assert risk_band(20)=='Critical'

@pytest.mark.parametrize('score,expected',[(1,'Low'),(4,'Low'),(5,'Medium'),(9,'Medium'),(10,'High'),(16,'High'),(17,'Critical'),(25,'Critical')])
def test_bands(score,expected): assert risk_band(score)==expected

def test_monthly_overdue_boundary():
    assert not overdue_test('2026-09-16','Monthly','2026-10-31') # 45 days
    assert overdue_test('2026-09-15','Monthly','2026-10-31')

def test_never_tested_separately(): assert not overdue_test(pd.NaT,'Monthly','2026-10-31')

def test_frequency_spelling(): assert overdue_test('2025-01-01','Annually','2026-10-31')

def test_latest_test_only():
    x=pd.DataFrame({'control_id':['A','A'],'test_date':pd.to_datetime(['2026-01-01','2026-02-01']),'test_id':['T1','T2'],'result':['Fail','Pass']})
    assert latest_control_tests(x).iloc[0]['result']=='Pass'
