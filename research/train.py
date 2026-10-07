"""Train locked baselines and dynamic models; test labels never choose parameters.

python -m research.train --experiment temporal|cross_project
"""
import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from research.metrics import probability_metrics

MODELS = Path('artifacts/models')
PREDICTIONS = Path('artifacts/predictions')
PROTOCOL = Path('artifacts/protocol')


def feature_columns(data,model):
    static = [c for c in data if c.startswith('static_') and not c.endswith('timestamp')]
    if model.startswith('static_'):
        return static+['cohort_size']
    dynamic = [c for c in data if c.startswith('dynamic_') and not c.endswith('timestamp')]
    columns = static+dynamic+['cohort_size']
    if model=='dynamic_no_cohort':
        columns = [c for c in columns if 'cohort' not in c]
    return columns


def prepare(data,columns):
    x = data[columns].copy()
    categories = [c for c in columns if c.endswith(('_status','_priority','_issue_type'))]
    for c in categories:
        x[c] = x[c].fillna('unknown').astype(str)
    for c in set(columns)-set(categories):
        x[c] = pd.to_numeric(x[c],errors='coerce').astype(float)
    return x,categories


def make_model(name,columns,categories,config):
    if name=='static_lr':
        numeric = [c for c in columns if c not in categories]
        transform = ColumnTransformer([
            ('numeric',Pipeline([('impute',SimpleImputer(strategy='median',keep_empty_features=True)),('scale',StandardScaler())]),numeric),
            ('categorical',OneHotEncoder(handle_unknown='ignore'),categories)])
        return Pipeline([('preprocess',transform),('model',LogisticRegression(C=1,max_iter=2000,random_state=config['seed']))])
    return CatBoostClassifier(**config['catboost'],random_seed=config['seed'],loss_function='Logloss',
                              cat_features=categories,verbose=False,allow_writing_files=False)


def logit(p):
    p = np.clip(p,1e-6,1-1e-6)
    return np.log(p/(1-p)).reshape(-1,1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment',choices=['temporal','cross_project'],required=True)
    args = parser.parse_args()
    config = json.loads((PROTOCOL/'config.json').read_text())
    lock = json.loads((PROTOCOL/'lock.json').read_text())
    assert hashlib.sha256((PROTOCOL/'config.json').read_bytes()).hexdigest()==lock['config_sha256']
    assert hashlib.sha256(Path('data/processed/snapshots.parquet').read_bytes()).hexdigest()==lock['dataset_sha256']
    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    run_hash = hashlib.sha256((source_hash+lock['config_sha256']+lock['dataset_sha256']).encode()).hexdigest()
    data = pd.read_parquet('data/processed/snapshots.parquet')
    data = data[data.project.isin(lock['eligible_projects'])].copy()
    temporal = pd.read_csv(PROTOCOL/'temporal_split_manifest.csv')
    cross = pd.read_csv(PROTOCOL/'cross_project_split_manifest.csv')
    MODELS.mkdir(parents=True,exist_ok=True)
    PREDICTIONS.mkdir(parents=True,exist_ok=True)
    run_dir = Path('artifacts/runs')/args.experiment
    run_dir.mkdir(parents=True,exist_ok=True)
    for fold in lock['eligible_projects']:
        if args.experiment=='temporal':
            fold_data = data[data.project==fold].merge(temporal[['sprint_id','partition']],on='sprint_id',validate='many_to_one')
        else:
            assignment = cross[cross.fold==fold][['project','partition']]
            fold_data = data.merge(assignment,on='project',validate='many_to_one')
        for landmark in config['landmarks']:
            selected = fold_data[fold_data.landmark==landmark]
            train,val,test = [selected[selected.partition==p].copy() for p in ('train','validation','test')]
            assert not set(train.sprint_id)&set(test.sprint_id)
            assert not set(val.sprint_id)&set(test.sprint_id)
            if args.experiment=='cross_project':
                assert fold not in set(train.project)|set(val.project)
            for name in config['models']:
                key = f'{args.experiment}__{fold}__{landmark:g}__{name}'
                prediction_path = PREDICTIONS/f'{key}.parquet'
                meta_path = run_dir/f'{key}.json'
                if prediction_path.exists() and meta_path.exists():
                    meta = json.loads(meta_path.read_text())
                    if meta['run_hash']!=run_hash: raise RuntimeError(f'Stale artifact: {key}; preserve and choose new run id')
                    print(f'Resume: {key}',flush=True)
                    continue
                print(f'Fit {key}: {len(train)}/{len(val)}/{len(test)}',flush=True)
                model,columns = None,[]
                if name=='frequency':
                    pv,pt = np.full(len(val),train.y.mean()),np.full(len(test),train.y.mean())
                elif name=='business_rule':
                    def rule(frame):
                        return np.where(frame.dynamic_is_done==1,.01,
                                        np.clip(.5+.02*frame.dynamic_inactive_days+.1*(frame.dynamic_status=='unknown'),.01,.99))
                    pv,pt = rule(val),rule(test)
                else:
                    columns = feature_columns(train,name)
                    xt,categories = prepare(train,columns)
                    xv,_ = prepare(val,columns)
                    xe,_ = prepare(test,columns)
                    model = make_model(name,columns,categories,config)
                    model.fit(xt,train.y)
                    pv,pt = model.predict_proba(xv)[:,1],model.predict_proba(xe)[:,1]
                calibrator = None
                if val.y.nunique()==2 and min(val.y.value_counts())>=5:
                    calibrator = LogisticRegression(C=1e6,max_iter=1000).fit(logit(pv),val.y)
                    calibrated = calibrator.predict_proba(logit(pt))[:,1]
                else:
                    calibrated = pt
                keep = ['project','project_id','sprint_id','issue_id','landmark','start','end','prediction_at','y',
                        'y_closed_only','cancelled','removed','dynamic_is_done','cohort_size']
                prediction = test[keep].copy()
                prediction['model'],prediction['experiment'],prediction['fold'] = name,args.experiment,fold
                prediction['p_raw'],prediction['p'] = pt,calibrated
                prediction['seen_training_issue'] = prediction.issue_id.isin(set(train.issue_id))
                prediction.to_parquet(prediction_path,index=False)
                joblib.dump({'model':model,'calibrator':calibrator,'features':columns,'run_hash':run_hash,
                             'constant':float(train.y.mean()) if name=='frequency' else None},MODELS/f'{key}.joblib')
                validation = val[['y']].copy()
                validation['p'] = pv
                meta = {'run_hash':run_hash,'source_hash':source_hash,'config_hash':lock['config_sha256'],
                        'dataset_hash':lock['dataset_sha256'],'fold':fold,'landmark':landmark,'model':name,
                        'n_train':len(train),'n_validation':len(val),'n_test':len(test),'validation_raw':probability_metrics(validation),
                        'calibration': 'sigmoid' if calibrator else 'identity','features':columns,
                        'saved_at':datetime.now(timezone.utc).isoformat(),'python':platform.python_version()}
                meta_path.write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print(f'Completed training/predictions: {args.experiment}',flush=True)


if __name__ == '__main__': main()
