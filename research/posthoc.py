"""Explicitly exploratory diagnostics after the registered test evaluation.

No model fitting, protocol amendments, thresholds or test-based parameter selection.
"""
import json
from pathlib import Path

import pandas as pd

from research.metrics import paired_bootstrap


def main():
    out=Path('artifacts/results')
    sprint=pd.read_csv(out/'sprint_alert_metrics.csv')
    sequential=pd.read_csv(out/'sequential_sprint_metrics.csv')
    config=json.loads(Path('artifacts/protocol/config.json').read_text())
    comparisons=[]
    for experiment in ['temporal','cross_project']:
        selected=sprint[(sprint.experiment==experiment)&(sprint.landmark==.5)&(sprint.q==.2)]
        for left,right in [('dynamic_catboost','business_rule'),('dynamic_catboost','dynamic_no_cohort')]:
            a=selected[selected.model==left]
            b=selected[selected.model==right]
            unit='sprint_id'
            if experiment=='cross_project':
                a=a.groupby('project',as_index=False).recall.mean()
                b=b.groupby('project',as_index=False).recall.mean()
                unit='project'
            comparisons.append({'experiment':experiment,'policy':'single_50%','left':left,'right':right,
                                'analysis':'posthoc_exploratory',**paired_bootstrap(a,b,unit=unit,replicates=config['bootstrap_replicates'])})
        selected=sequential[sequential.experiment==experiment]
        a=selected[selected.model=='dynamic_catboost']
        b=selected[selected.model=='static_catboost']
        unit='sprint_id'
        if experiment=='cross_project':
            a=a.groupby('project',as_index=False).recall.mean()
            b=b.groupby('project',as_index=False).recall.mean()
            unit='project'
        comparisons.append({'experiment':experiment,'policy':'sequential','left':'dynamic_catboost','right':'static_catboost',
                            'analysis':'posthoc_exploratory',**paired_bootstrap(a,b,unit=unit,replicates=config['bootstrap_replicates'])})
    pd.DataFrame(comparisons).to_csv(out/'posthoc_comparisons.csv',index=False)
    budgets=[]
    for experiment in ['temporal','cross_project']:
        selected=sprint[(sprint.experiment==experiment)&(sprint.landmark==.5)&(sprint.q==.2)&(sprint.model=='dynamic_catboost')]
        budgets.append({'experiment':experiment,'n':int(selected.n.sum()),'positive':int(selected.positives.sum()),
                        'alerts':int(selected.k.sum()),'true_alerts':int(selected.tp.sum()),
                        'false_alerts':int(selected.false_alerts.sum()),'realized_budget_micro':float(selected.k.sum()/selected.n.sum()),
                        'realized_budget_macro_sprint':float(selected.realized_budget.mean()),
                        'sprints_fewer_than_5_instances':int((selected.n<5).sum()),'sprints':len(selected)})
    (out/'budget_population_diagnostics.json').write_text(json.dumps(budgets,indent=2),encoding='utf-8')
    print(json.dumps({'budget_population':budgets,'posthoc_comparisons':comparisons},indent=2))


if __name__=='__main__': main()
