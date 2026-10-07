"""Independent SQL sample checks and full artifact invariants before training."""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg

from research.replay import DONE, normalize, sprint_set


def main():
    out = Path('artifacts/validation')
    out.mkdir(parents=True,exist_ok=True)
    data = pd.read_parquet('data/processed/snapshots.parquet')
    lock = json.loads(Path('artifacts/protocol/lock.json').read_text())
    assert not data.duplicated(['issue_id','sprint_id','landmark']).any()
    assert data.groupby(['issue_id','sprint_id']).landmark.nunique().eq(4).all()
    for prefix in ['static','dynamic']:
        maximum = pd.to_datetime(data[f'{prefix}_feature_max_timestamp'],utc=True)
        cutoff = data.start if prefix=='static' else data.prediction_at
        assert (maximum<=cutoff).all()
    assert data.groupby(['issue_id','sprint_id']).y.nunique().eq(1).all()
    assert (data.status_gaps==0).all() and (data.membership_gaps==0).all()
    split = pd.read_csv('artifacts/protocol/temporal_split_manifest.csv',parse_dates=['start','end'])
    for _,group in split.groupby('project'):
        train,val,test = [group[group.partition==part] for part in ['train','validation','test']]
        assert train.end.max()<val.start.min() and val.end.max()<test.start.min()
    samples = []
    with psycopg.connect(os.environ.get('RESEARCH_DATABASE_URL','postgresql://tawos:tawos_local_dev@localhost:5432/tawos')) as con:
        con.execute('SET TRANSACTION READ ONLY')
        for project in lock['eligible_projects']:
            candidates = data[(data.project==project)&(data.landmark==0)]
            # Stratified, fixed-seed sample for both labels. Scope changes additionally represented.
            chosen = pd.concat([group.sample(n=min(25,len(group)),random_state=20261008) for _,group in candidates.groupby('y')])
            scope = candidates[candidates.cancelled|candidates.removed]
            chosen = pd.concat([chosen,scope.head(5)]).drop_duplicates(['issue_id','sprint_id'])
            for row in chosen.itertuples():
                membership = con.execute("SELECT to_value FROM tawos_raw.change_log WHERE issue_id=%s AND field='Sprint' AND creation_date<=%s ORDER BY creation_date DESC,id DESC LIMIT 1",(row.issue_id,row.start)).fetchone()
                status = con.execute("SELECT to_string FROM tawos_raw.change_log WHERE issue_id=%s AND field='status' AND creation_date<=%s ORDER BY creation_date DESC,id DESC LIMIT 1",(row.issue_id,row.end)).fetchone()
                jid = con.execute('SELECT jiraid FROM tawos_raw.sprint WHERE id=%s',(row.sprint_id,)).fetchone()[0]
                member_ok = jid in sprint_set(membership[0])
                label_ok = row.y==int(normalize(status[0]) not in DONE)
                # Reverse-oriented audit uses first later event's FROM solely to corroborate ground truth.
                later = con.execute("SELECT from_string FROM tawos_raw.change_log WHERE issue_id=%s AND field='status' AND creation_date>%s ORDER BY creation_date,id LIMIT 1",(row.issue_id,row.end)).fetchone()
                corroborated = None if not later else normalize(later[0])==normalize(status[0])
                assert member_ok and label_ok
                if corroborated is not None: assert corroborated
                samples.append({'project':project,'issue_id':row.issue_id,'sprint_id':row.sprint_id,'y':row.y,
                                'sql_status':status[0],'membership_ok':member_ok,'label_ok':label_ok,
                                'reverse_corroborated':corroborated,'cancelled':row.cancelled,'removed':row.removed})
    pd.DataFrame(samples).to_csv(out/'sql_sample_audit.csv',index=False)
    feature_rows = []
    for column in data:
        if column.startswith(('static_','dynamic_')) or column=='cohort_size':
            feature_rows.append({'feature':column,'allowed':not column.endswith('timestamp'),
                                 'availability':'t0' if column.startswith('static_') or column=='cohort_size' else 'landmark',
                                 'missing_fraction':float(data[column].isna().mean()),
                                 'unknown_fraction':float((data[column]=='unknown').mean()) if data[column].dtype=='object' or str(data[column].dtype)=='str' else None,
                                 'source':'timestamped selected changelog fields; cohort aggregate before label filtering'})
    pd.DataFrame(feature_rows).to_csv(out/'feature_dictionary.csv',index=False)
    commitments = pd.read_parquet('data/processed/all_commitments.parquet')
    report = {'snapshots':len(data),'labeled_instances':int(len(data)/4),'commitments_with_membership':len(commitments),
              'unknown_outcomes':int(commitments.y.isna().sum()),'label_coverage':float(commitments.y.notna().mean()),
              'eligible_projects':len(lock['eligible_projects']),'sample_audits':len(samples),'checks_passed':True,
              'manual_business_workflow_audit':False,'inter_rater_agreement':None,
              'scope':'SQL/replay consistency, chronology, label availability, forward feature provenance; no human ground truth confirmation'}
    (out/'data_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
