"""Evaluate completed frozen predictions and export metrics, plots, alert replay."""
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from research.metrics import paired_bootstrap, probability_metrics as base_probability_metrics, sprint_metrics, tie_key

OUT = Path('artifacts/results')


def probability_metrics(data):
    result=base_probability_metrics(data)
    if data.p.max()-data.p.min()<1e-10:
        # Slope/intercept are not separately identifiable with constant scores.
        result['calibration_intercept']=None
        result['calibration_slope']=None
    return result


def aggregate_sprint(frame):
    return {'sprints':len(frame),'sprints_with_positive':int(frame.recall.notna().sum()),
            'recall_macro_sprint':float(frame.recall.mean()),'precision_macro_sprint':float(frame.precision.mean()),
            'false_alerts_per_sprint':float(frame.false_alerts.mean()),'realized_budget':float(frame.realized_budget.mean()),
            'recall_micro':float(frame.tp.sum()/frame.positives.sum()) if frame.positives.sum() else None,
            'precision_micro':float(frame.tp.sum()/frame.k.sum()) if frame.k.sum() else None,
            'lead_days_macro_sprint':float(frame.lead_days.mean()),
            'recall_macro_project':float(frame.groupby('project').recall.mean().mean()),
            'precision_macro_project':float(frame.groupby('project').precision.mean().mean())}


def sequential(data,q=.2):
    records,alert_records = [],[]
    groups=defaultdict(list)
    fields=['project','sprint_id','issue_id','landmark','y','p','dynamic_is_done','end','prediction_at']
    for row in data[fields].to_dict('records'):
        groups[row['sprint_id']].append(row)
    for sprint_id in sorted(groups):
        group=groups[sprint_id]
        cohort=[row for row in group if row['landmark']==.25]
        n = len(cohort)
        k = math.ceil(q*n)
        alerted,alerts = set(),[]
        ties={row['issue_id']:tie_key(row['issue_id'],sprint_id) for row in cohort}
        for step,landmark in enumerate((.25,.5,.75),start=1):
            candidates=[row for row in group if row['landmark']==landmark and row['dynamic_is_done']==0 and row['issue_id'] not in alerted]
            # Cumulative quota: reserve capacity for later observations in larger sprints.
            allowance = math.ceil(k*step/3)-len(alerted)
            selected=sorted(candidates,key=lambda row:(-row['p'],ties[row['issue_id']]))[:max(0,allowance)]
            for row in selected:
                alerted.add(row['issue_id'])
                record = {'project':row['project'],'sprint_id':sprint_id,'issue_id':row['issue_id'],'landmark':landmark,
                          'y':row['y'],'lead_days':(row['end']-row['prediction_at']).total_seconds()/86400}
                alerts.append(record)
                alert_records.append(record)
        assert len(alerted)<=k
        positives = int(sum(row['y'] for row in cohort))
        tp = sum(a['y'] for a in alerts)
        records.append({'project':cohort[0]['project'],'sprint_id':sprint_id,'n':n,'k':len(alerted),'budget_cap':k,
                        'positives':positives,'tp':tp,'false_alerts':len(alerted)-tp,
                        'recall':tp/positives if positives else np.nan,
                        'precision':tp/len(alerted) if alerted else np.nan,
                        'realized_budget':len(alerted)/n,
                        'lead_days':float(np.mean([a['lead_days'] for a in alerts if a['y']])) if tp else np.nan,
                        'positives_detected_by_half':sum(a['y'] for a in alerts if a['landmark']<=.5),
                        'recall_by_half':sum(a['y'] for a in alerts if a['landmark']<=.5)/positives if positives else np.nan})
    return pd.DataFrame(records),pd.DataFrame(alert_records)


def main():
    config = json.loads(Path('artifacts/protocol/config.json').read_text())
    lock = json.loads(Path('artifacts/protocol/lock.json').read_text())
    expected = len(lock['eligible_projects'])*len(config['landmarks'])*len(config['models'])*2
    paths = list(Path('artifacts/predictions').glob('*.parquet'))
    if len(paths)!=expected: raise RuntimeError(f'Prediction matrix incomplete: {len(paths)}/{expected}')
    OUT.mkdir(parents=True,exist_ok=True)
    data = pd.concat([pd.read_parquet(path) for path in paths],ignore_index=True)
    probability,per_project,budget,per_sprint,sensitivity,comparisons,sequence,sequence_sprints,sequence_alerts = [],[],[],[],[],[],[],[],[]
    for (experiment,landmark,model),group in data.groupby(['experiment','landmark','model']):
        meta = {'experiment':experiment,'landmark':landmark,'model':model}
        for calibration in ['raw','sigmoid']:
            evaluated = group.copy()
            if calibration=='raw': evaluated['p']=evaluated.p_raw
            project_results = []
            for project,subgroup in evaluated.groupby('project'):
                result = probability_metrics(subgroup)
                project_results.append(result)
                per_project.append({**meta,'calibration':calibration,'project':project,**result})
            project_frame = pd.DataFrame(project_results)
            probability.append({**meta,'calibration':calibration,**probability_metrics(evaluated),
                                'ap_macro_project':float(project_frame.ap.mean()),'brier_macro_project':float(project_frame.brier.mean())})
        for q in config['budget_rates']:
            metrics = sprint_metrics(group,q)
            budget.append({**meta,'q':q,**aggregate_sprint(metrics)})
            metrics = metrics.assign(**meta,q=q)
            per_sprint.append(metrics)
        scenarios = {
            'raw_ranking':(group.assign(p=group.p_raw),'ceil'),
            'floor':(group,'floor'),
            'active_only':(group[group.dynamic_is_done==0],'ceil'),
            'exclude_cancelled_removed':(group[~(group.cancelled|group.removed)],'ceil'),
            'unseen_issue_ids':(group[~group.seen_training_issue],'ceil'),
            'closed_only_label':(group.assign(y=group.y_closed_only),'ceil'),
        }
        for scenario,(subset,rounding) in scenarios.items():
            if subset.empty: continue
            metrics = sprint_metrics(subset,.2,rounding)
            sensitivity.append({**meta,'scenario':scenario,**probability_metrics(subset),**aggregate_sprint(metrics)})
    sprint_table = pd.concat(per_sprint,ignore_index=True)
    for experiment in ['temporal','cross_project']:
        for landmark in config['landmarks']:
            for scenario in ['primary','raw_ranking','floor','active_only','exclude_cancelled_removed','unseen_issue_ids','closed_only_label']:
                group = data[(data.experiment==experiment)&(data.landmark==landmark)]
                rounding='ceil'
                if scenario=='raw_ranking': group=group.assign(p=group.p_raw)
                elif scenario=='floor': rounding='floor'
                elif scenario=='active_only': group=group[group.dynamic_is_done==0]
                elif scenario=='exclude_cancelled_removed': group=group[~(group.cancelled|group.removed)]
                elif scenario=='unseen_issue_ids': group=group[~group.seen_training_issue]
                elif scenario=='closed_only_label': group=group.assign(y=group.y_closed_only)
                dynamic = sprint_metrics(group[group.model=='dynamic_catboost'],.2,rounding)
                static = sprint_metrics(group[group.model=='static_catboost'],.2,rounding)
                if experiment=='cross_project':
                    dynamic = dynamic.groupby('project',as_index=False).recall.mean()
                    static = static.groupby('project',as_index=False).recall.mean()
                comparisons.append({'experiment':experiment,'landmark':landmark,'scenario':scenario,
                                    **paired_bootstrap(dynamic,static,unit='project' if experiment=='cross_project' else 'sprint_id',replicates=config['bootstrap_replicates'])})
            if experiment=='temporal':
                group=data[(data.experiment==experiment)&(data.landmark==landmark)]
                dynamic=sprint_metrics(group[group.model=='dynamic_catboost']).groupby('project',as_index=False).recall.mean()
                static=sprint_metrics(group[group.model=='static_catboost']).groupby('project',as_index=False).recall.mean()
                comparisons.append({'experiment':experiment,'landmark':landmark,'scenario':'project_weighted_exploratory',
                                    **paired_bootstrap(dynamic,static,unit='project',replicates=config['bootstrap_replicates'])})
        for model in config['models']:
            group = data[(data.experiment==experiment)&(data.model==model)&(data.landmark>0)]
            sm,alerts = sequential(group)
            sequence.append({'experiment':experiment,'model':model,**aggregate_sprint(sm),'recall_by_half_macro':float(sm.recall_by_half.mean())})
            sequence_sprints.append(sm.assign(experiment=experiment,model=model))
            sequence_alerts.append(alerts.assign(experiment=experiment,model=model))
    for name,records in [('probability_metrics',probability),('project_probability_metrics',per_project),('alert_budget_metrics',budget),
                         ('sensitivity_metrics',sensitivity),('paired_comparisons',comparisons),('sequential_alert_metrics',sequence)]:
        pd.DataFrame(records).to_csv(OUT/f'{name}.csv',index=False)
    sprint_table.to_csv(OUT/'sprint_alert_metrics.csv',index=False)
    sprint_table.groupby(['experiment','landmark','model','q','project']).agg(
        recall=('recall','mean'),precision=('precision','mean'),false_alerts=('false_alerts','mean'),
        realized_budget=('realized_budget','mean'),sprints=('sprint_id','size')).reset_index().to_csv(OUT/'project_alert_metrics.csv',index=False)
    pd.concat(sequence_sprints).to_csv(OUT/'sequential_sprint_metrics.csv',index=False)
    pd.concat(sequence_alerts).to_csv(OUT/'sequential_alert_log.csv',index=False)
    # Calibration plots at the pre-registered primary landmark.
    for experiment in ['temporal','cross_project']:
        figure,axes = plt.subplots(1,2,figsize=(10,4),sharex=True,sharey=True)
        for ax,score in zip(axes,['p_raw','p']):
            ax.plot([0,1],[0,1],'--',color='gray',linewidth=1)
            for model in ['static_catboost','dynamic_catboost','dynamic_no_cohort']:
                group = data[(data.experiment==experiment)&(data.landmark==.5)&(data.model==model)].copy()
                group['bin'] = pd.cut(group[score],bins=np.linspace(0,1,11),include_lowest=True)
                curve = group.groupby('bin',observed=True).agg(prediction=(score,'mean'),observed=('y','mean'),n=('y','size'))
                curve.to_csv(OUT/f'calibration_bins__{experiment}__{model}__{score}.csv',index=False)
                ax.plot(curve.prediction,curve.observed,'o-',label=model,markersize=4)
            ax.set_title('Raw' if score=='p_raw' else 'Validation sigmoid')
            ax.set_xlabel('Predicted risk')
            ax.set_ylabel('Observed non-completion')
            ax.legend(fontsize=7)
        figure.suptitle(f'{experiment}: 50% landmark; pooled reliability (10 fixed bins)')
        figure.tight_layout()
        figure.savefig(OUT/f'calibration_{experiment}.png',dpi=180)
        plt.close(figure)
    summary = {'evaluated_at':datetime.now(timezone.utc).isoformat(),'test_metrics_viewed':True,'prediction_files':len(paths),'rows':len(data),
               'config_sha256':lock['config_sha256'],'dataset_sha256':lock['dataset_sha256'],
               'primary_comparisons':[c for c in comparisons if c['landmark']==.5 and c['scenario']=='primary'],
               'note':'Test predictions now evaluated. No tuning or dataset rule changes permitted based on these results.'}
    (OUT/'manifest.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
