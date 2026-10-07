import math

import numpy as np
import pandas as pd

from research.metrics import sprint_metrics, tie_key


def test_vectorized_metrics_match_reference_for_ties_sparse_and_zero_positive_sprints():
    rng=np.random.default_rng(41)
    rows=[]
    for sprint,size in enumerate([1,2,3,4,5,13,21]):
        for issue in range(size):
            rows.append({'project':'P','sprint_id':sprint,'issue_id':sprint*100+issue,'y':0 if sprint==2 else int(rng.integers(2)),
                         'p':float(rng.choice([.1,.5,.9])),'end':pd.Timestamp('2020-01-20'),
                         'prediction_at':pd.Timestamp('2020-01-10')})
    data=pd.DataFrame(rows)
    for rounding in ['ceil','floor']:
        for q in [.1,.2,.3]:
            result=sprint_metrics(data,q,rounding).set_index('sprint_id')
            for sprint,group in data.groupby('sprint_id'):
                k=int(math.ceil(q*len(group)) if rounding=='ceil' else math.floor(q*len(group)))
                ordered=sorted(group.to_dict('records'),key=lambda row:(-row['p'],tie_key(row['issue_id'],sprint)))
                tp=sum(row['y'] for row in ordered[:k])
                assert result.loc[sprint,'k']==k
                assert result.loc[sprint,'tp']==tp
                assert result.loc[sprint,'false_alerts']==k-tp
                positives=group.y.sum()
                if positives: assert result.loc[sprint,'recall']==tp/positives
                else: assert pd.isna(result.loc[sprint,'recall'])
                if k: assert result.loc[sprint,'precision']==tp/k
                else: assert pd.isna(result.loc[sprint,'precision'])
