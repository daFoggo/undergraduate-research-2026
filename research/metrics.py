"""Budget and calibration diagnostics; independent of model fitting."""
import hashlib
import math

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score


def tie_key(issue_id, sprint_id):
    return hashlib.sha256(f'{int(issue_id)}:{int(sprint_id)}:20261008'.encode()).hexdigest()


def sprint_metrics(data, q=.2, rounding='ceil'):
    records = []
    for sprint_id,group in data.groupby('sprint_id'):
        group = group.copy()
        group['tie'] = [tie_key(i,sprint_id) for i in group.issue_id]
        k = int(math.ceil(q*len(group)) if rounding=='ceil' else math.floor(q*len(group)))
        alerts = group.sort_values(['p','tie'],ascending=[False,True]).head(k)
        positives, tp = int(group.y.sum()), int(alerts.y.sum())
        lead = (alerts.end-alerts.prediction_at).dt.total_seconds()/86400
        records.append({'project':group.project.iloc[0],'sprint_id':sprint_id,'n':len(group),'positives':positives,
                        'k':k,'realized_budget':k/len(group),'tp':tp,'false_alerts':k-tp,
                        'recall':tp/positives if positives else np.nan,
                        'precision':tp/k if k else np.nan,
                        'lead_days':float(lead[alerts.y==1].mean()) if tp else np.nan})
    return pd.DataFrame(records)


def probability_metrics(data):
    y,p = data.y.to_numpy(),np.clip(data.p.to_numpy(),1e-6,1-1e-6)
    result = {'n':len(y),'prevalence':float(y.mean()),'brier':float(brier_score_loss(y,p))}
    if len(np.unique(y))<2:
        result.update({'ap':None,'roc_auc':None,'calibration_intercept':None,'calibration_slope':None})
        return result
    result['ap'] = float(average_precision_score(y,p))
    result['roc_auc'] = float(roc_auc_score(y,p))
    diagnostic = LogisticRegression(C=1e6,max_iter=1000).fit(np.log(p/(1-p)).reshape(-1,1),y)
    result['calibration_intercept'] = float(diagnostic.intercept_[0])
    result['calibration_slope'] = float(diagnostic.coef_[0,0])
    return result


def paired_bootstrap(dynamic,static,unit='sprint_id',seed=20261008,replicates=2000):
    paired = dynamic[[unit,'recall']].merge(static[[unit,'recall']],on=unit,suffixes=('_dynamic','_static')).dropna()
    differences = (paired.recall_dynamic-paired.recall_static).to_numpy()
    if not len(differences):
        return {'n_units':0,'delta':None,'ci_low':None,'ci_high':None}
    rng = np.random.default_rng(seed)
    estimates = np.array([rng.choice(differences,len(differences),replace=True).mean() for _ in range(replicates)])
    return {'n_units':len(differences),'delta':float(differences.mean()),
            'ci_low':float(np.quantile(estimates,.025)),'ci_high':float(np.quantile(estimates,.975))}
