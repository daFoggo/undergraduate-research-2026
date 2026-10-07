"""Verify every completed prediction against the frozen dataset/split and saved model.

--partial checks available artifacts while training continues without reporting test metrics.
"""
import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from research.train import logit, prepare


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--partial',action='store_true')
    args=parser.parse_args()
    protocol=Path('artifacts/protocol')
    config=json.loads((protocol/'config.json').read_text())
    lock=json.loads((protocol/'lock.json').read_text())
    data=pd.read_parquet('data/processed/snapshots.parquet')
    temporal=pd.read_csv(protocol/'temporal_split_manifest.csv')
    cross=pd.read_csv(protocol/'cross_project_split_manifest.csv')
    dictionary=pd.read_csv('artifacts/validation/feature_dictionary.csv')
    allowed=set(dictionary[dictionary.allowed].feature)
    expected=[]
    for experiment in ['temporal','cross_project']:
        for project in lock['eligible_projects']:
            for landmark in config['landmarks']:
                for model in config['models']:
                    expected.append((experiment,project,landmark,model))
    records=[]
    for experiment,project,landmark,name in expected:
        key=f'{experiment}__{project}__{landmark:g}__{name}'
        paths=[Path('artifacts/predictions')/f'{key}.parquet',Path('artifacts/models')/f'{key}.joblib',Path('artifacts/runs')/experiment/f'{key}.json']
        if not all(path.exists() for path in paths):
            if args.partial: continue
            raise RuntimeError(f'Incomplete artifact triplet: {key}')
        prediction=pd.read_parquet(paths[0])
        artifact=joblib.load(paths[1])
        meta=json.loads(paths[2].read_text())
        assert meta['config_hash']==lock['config_sha256']
        assert meta['dataset_hash']==lock['dataset_sha256']
        assert artifact['run_hash']==meta['run_hash']
        assert set(meta['features'])<=allowed
        assert artifact['features']==meta['features']
        selected=data[(data.project==project)&(data.landmark==landmark)].copy()
        if experiment=='temporal':
            assignment=temporal[temporal.project==project][['sprint_id','partition']]
            selected=selected.merge(assignment,on='sprint_id',validate='many_to_one')
            test=selected[selected.partition=='test']
        else:
            test=selected
            assignment=cross[cross.fold==project]
            assert assignment[assignment.partition=='test'].project.tolist()==[project]
            assert project not in set(assignment[assignment.partition!='test'].project)
        indexes=['issue_id','sprint_id','landmark']
        assert not prediction.duplicated(indexes).any()
        assert len(prediction)==len(test)==meta['n_test']
        comparison=prediction.merge(test,on=indexes,suffixes=('_prediction','_dataset'),validate='one_to_one')
        assert len(comparison)==len(test)
        for column in ['y','project','start','end','prediction_at','dynamic_is_done','cohort_size','cancelled','removed']:
            assert (comparison[f'{column}_prediction']==comparison[f'{column}_dataset']).all(),(key,column)
        for score in ['p','p_raw']:
            assert prediction[score].notna().all() and prediction[score].between(0,1).all()
        sample=comparison.head(7)
        features=pd.DataFrame({column:sample[column] if column in sample else sample[column+'_dataset'] for column in artifact['features']})
        if artifact['model'] is not None:
            x,_=prepare(features,artifact['features'])
            raw=artifact['model'].predict_proba(x)[:,1]
        elif name=='frequency':
            raw=np.full(len(sample),artifact['constant'])
        else:
            raw=np.where(sample.dynamic_is_done_dataset==1,.01,
                         np.clip(.5+.02*sample.dynamic_inactive_days+.1*(sample.dynamic_status=='unknown'),.01,.99))
        np.testing.assert_allclose(raw,sample.p_raw,rtol=1e-8,atol=1e-10)
        calibrated=artifact['calibrator'].predict_proba(logit(raw))[:,1] if artifact['calibrator'] else raw
        np.testing.assert_allclose(calibrated,sample.p,rtol=1e-8,atol=1e-10)
        records.append({'key':key,'rows':len(prediction),'prediction_sha256':hashlib.sha256(paths[0].read_bytes()).hexdigest(),
                        'model_sha256':hashlib.sha256(paths[1].read_bytes()).hexdigest(),'run_hash':meta['run_hash'],
                        'calibrator_slope':float(artifact['calibrator'].coef_[0,0]) if artifact['calibrator'] else None,
                        'checks_passed':True})
    out=Path('artifacts/validation')
    pd.DataFrame(records).to_csv(out/('partial_prediction_audit.csv' if args.partial else 'prediction_audit.csv'),index=False)
    summary={'expected':len(expected),'checked':len(records),'complete':len(records)==len(expected),'checks_passed':True,
             'scope':'artifact triplets; exact test cohort/labels/timestamps; whitelist; sample model re-inference; calibrator application'}
    (out/('partial_prediction_validation.json' if args.partial else 'prediction_validation.json')).write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
