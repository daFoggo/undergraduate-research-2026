"""Chronological sprint splits with label-availability purging."""
import hashlib
import json
from pathlib import Path

import pandas as pd

OUT = Path('artifacts/protocol')
CONFIG = {
    'version':'1.0', 'seed':20261008, 'landmarks':[0.0,.25,.5,.75],
    'min_sprints':50,'min_instances':200,'min_class_instances':30,
    'min_test_sprints':10,'min_train_class':10,'min_validation_class':5,'min_test_class':5,
    'temporal_split':[.6,.2,.2], 'budget_rates':[.1,.2,.3],
    'budget_rounding':'ceil; report realized fraction; floor sensitivity',
    'models':['frequency','business_rule','static_lr','static_catboost','dynamic_catboost','dynamic_no_cohort'],
    'catboost':{'iterations':400,'depth':5,'learning_rate':.05,'l2_leaf_reg':5,'thread_count':4},
    'calibration':'sigmoid on validation only; identity fallback if insufficient validation classes',
    'cross_project':'leave-one-project-out; held-out validation projects deterministic by seed',
    'bootstrap_replicates':2000,
    'primary':'paired macro sprint Recall@20% at 50%, dynamic_catboost vs static_catboost',
    'sensitivity':['budget_floor','active_only','exclude_cancelled_removed','unseen_issue_ids','closed_only_label'],
}


def temporal_split(sprints):
    sprints = sprints.sort_values(['start','sprint_id']).copy()
    n = len(sprints)
    validation_start = sprints.iloc[int(.6*n)].start
    test_start = sprints.iloc[int(.8*n)].start
    sprints['partition'] = 'test'
    sprints.loc[sprints.start < test_start,'partition'] = 'validation'
    sprints.loc[sprints.start < validation_start,'partition'] = 'train'
    sprints.loc[(sprints.partition=='train') & (sprints.end>=validation_start),'partition'] = 'purged'
    sprints.loc[(sprints.partition=='validation') & (sprints.end>=test_start),'partition'] = 'purged'
    return sprints


def main():
    if Path('artifacts/predictions').exists() and any(Path('artifacts/predictions').glob('*.parquet')):
        raise RuntimeError('Predictions already exist: preserve the locked split and register a new run before any amendment.')
    OUT.mkdir(parents=True,exist_ok=True)
    data = pd.read_parquet('data/processed/snapshots.parquet')
    cohorts = data[data.landmark==0]
    eligibility, splits = [], []
    for project, group in cohorts.groupby('project'):
        counts = group.y.value_counts()
        sprints = group[['project','project_id','sprint_id','start','end']].drop_duplicates()
        reasons = []
        if len(sprints)<CONFIG['min_sprints']: reasons.append('fewer_than_50_sprints')
        if len(group)<CONFIG['min_instances']: reasons.append('fewer_than_200_instances')
        if min(counts.get(0,0),counts.get(1,0))<CONFIG['min_class_instances']: reasons.append('fewer_than_30_per_class')
        if not reasons:
            assigned = temporal_split(sprints)
            combined = group.merge(assigned[['sprint_id','partition']],on='sprint_id')
            for partition,minimum in [('train',10),('validation',5),('test',5)]:
                subset = combined[combined.partition==partition]
                cc = subset.y.value_counts()
                if min(cc.get(0,0),cc.get(1,0))<minimum: reasons.append(f'insufficient_{partition}_classes')
            if assigned[assigned.partition=='test'].sprint_id.nunique()<10: reasons.append('fewer_than_10_test_sprints')
            if not reasons: splits.append(assigned)
        eligibility.append({'project':project,'instances':len(group),'sprints':len(sprints),'positive':counts.get(1,0),
                            'negative':counts.get(0,0),'eligible':not reasons,'reasons':';'.join(reasons)})
    pd.DataFrame(eligibility).to_csv(OUT/'eligibility.csv',index=False)
    manifest = pd.concat(splits,ignore_index=True)
    manifest.to_csv(OUT/'temporal_split_manifest.csv',index=False)
    import numpy as np
    rng = np.random.default_rng(CONFIG['seed'])
    projects = sorted(manifest.project.unique())
    cross = []
    for test in projects:
        others = [p for p in projects if p!=test]
        validation = set(rng.choice(others,size=max(2,int(.2*len(others))),replace=False))
        for project in projects:
            cross.append({'fold':test,'project':project,'partition':'test' if project==test else 'validation' if project in validation else 'train'})
    pd.DataFrame(cross).to_csv(OUT/'cross_project_split_manifest.csv',index=False)
    (OUT/'config.json').write_text(json.dumps(CONFIG,indent=2),encoding='utf-8')
    lock = {'config_sha256':hashlib.sha256((OUT/'config.json').read_bytes()).hexdigest(),
            'dataset_sha256':hashlib.sha256(Path('data/processed/snapshots.parquet').read_bytes()).hexdigest(),
            'eligible_projects':projects,'test_metrics_viewed':False,
            'note':'Locked before any model fit or test prediction. Dataset outcome counts used for feasibility only.'}
    (OUT/'lock.json').write_text(json.dumps(lock,indent=2),encoding='utf-8')
    print(json.dumps(lock,indent=2))


if __name__ == '__main__': main()
