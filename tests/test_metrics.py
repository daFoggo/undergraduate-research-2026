import pandas as pd

from research.metrics import paired_bootstrap, sprint_metrics


def test_budget_rounding_and_no_positive_sprints():
    data = pd.DataFrame({'project':['P']*3,'sprint_id':[1]*3,'issue_id':[1,2,3],
                         'y':[1,0,0],'p':[.9,.5,.1],
                         'end':pd.to_datetime(['2020-01-10']*3),'prediction_at':pd.to_datetime(['2020-01-05']*3)})
    assert sprint_metrics(data).iloc[0].recall==1
    assert sprint_metrics(data,rounding='floor').iloc[0].k==0
    data.y=0
    assert pd.isna(sprint_metrics(data).iloc[0].recall)
    assert sprint_metrics(data).iloc[0].false_alerts==1


def test_paired_bootstrap_keeps_sprint_pairing():
    dynamic = pd.DataFrame({'sprint_id':[1,2],'recall':[.8,.6]})
    static = pd.DataFrame({'sprint_id':[2,1],'recall':[.4,.6]})
    result = paired_bootstrap(dynamic,static,replicates=200)
    assert abs(result['delta']-.2)<1e-8
