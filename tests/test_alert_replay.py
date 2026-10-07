import pandas as pd

from research.evaluate import sequential


def test_sequential_budget_is_total_not_per_landmark():
    records=[]
    for landmark in [.25,.5,.75]:
        for issue in range(10):
            records.append({'project':'P','sprint_id':1,'issue_id':issue,'landmark':landmark,'y':int(issue<3),
                            'p':1-issue/10,'dynamic_is_done':0,'end':pd.Timestamp('2020-01-11'),
                            'prediction_at':pd.Timestamp('2020-01-01')+pd.Timedelta(days=10*landmark)})
    metrics,alerts=sequential(pd.DataFrame(records))
    assert metrics.iloc[0].budget_cap==2
    assert len(alerts)==2
    assert alerts.issue_id.nunique()==2
