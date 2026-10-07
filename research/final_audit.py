"""Current-state completion audit for the declared stage-1 through stage-4 scope."""
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=Path.cwd()
    lock=json.loads(Path('artifacts/protocol/lock.json').read_text())
    assert digest(Path('artifacts/protocol/config.json'))==lock['config_sha256']
    assert digest(Path('data/processed/snapshots.parquet'))==lock['dataset_sha256']
    validation=json.loads(Path('artifacts/validation/prediction_validation.json').read_text())
    assert validation['complete'] and validation['checks_passed'] and validation['checked']==672
    audit=pd.read_csv('artifacts/validation/prediction_audit.csv')
    assert len(audit)==672 and audit.checks_passed.all()
    for row in audit.itertuples():
        assert digest(Path('artifacts/predictions')/f'{row.key}.parquet')==row.prediction_sha256
        assert digest(Path('artifacts/models')/f'{row.key}.joblib')==row.model_sha256
    frozen=[]
    for filename in ['artifacts/protocol/config.json','artifacts/protocol/temporal_split_manifest.csv',
                     'artifacts/protocol/cross_project_split_manifest.csv','documents/Protocol_v1.md','research/train.py']:
        registered=subprocess.check_output(['git','show',f'2f3a73f:{filename}']).decode('utf-8').replace('\r\n','\n').strip()
        current=Path(filename).read_text(encoding='utf-8').replace('\r\n','\n').strip()
        assert current==registered,f'Frozen method changed after registration: {filename}'
        frozen.append(filename)
    results=Path('artifacts/results')
    evaluation=json.loads((results/'manifest.json').read_text())
    assert evaluation['prediction_files']==672
    assert evaluation['dataset_sha256']==lock['dataset_sha256']
    budget=pd.read_csv(results/'sprint_alert_metrics.csv')
    assert (budget.k==np.ceil(budget.q*budget.n)).all()
    assert (budget.false_alerts==budget.k-budget.tp).all()
    assert (budget.tp<=budget.positives).all() and (budget.tp<=budget.k).all()
    sequence=pd.read_csv(results/'sequential_sprint_metrics.csv')
    alerts=pd.read_csv(results/'sequential_alert_log.csv')
    keys=['experiment','model','sprint_id']
    assert not alerts.duplicated(keys+['issue_id']).any()
    assert (sequence.k<=sequence.budget_cap).all()
    counted=alerts.groupby(keys).agg(actual_k=('issue_id','size'),actual_tp=('y','sum')).reset_index()
    checked=sequence.merge(counted,on=keys,how='left').fillna({'actual_k':0,'actual_tp':0})
    assert (checked.k==checked.actual_k).all() and (checked.tp==checked.actual_tp).all()
    expected_tables={'probability_metrics.csv':96,'project_probability_metrics.csv':1344,
                     'alert_budget_metrics.csv':144,'paired_comparisons.csv':60,
                     'sequential_alert_metrics.csv':12,'posthoc_comparisons.csv':6}
    for filename,count in expected_tables.items():
        frame=pd.read_csv(results/filename)
        assert len(frame)==count,(filename,len(frame),count)
    report=Path('documents/Bao_cao_nghien_cuu_giai_doan_4.md')
    for target in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
        if not target.startswith(('http:','https:')):
            assert (report.parent/target).resolve().is_file(),target
    figures=['calibration_temporal.png','calibration_cross_project.png','landmark_budget_temporal.png',
             'landmark_budget_cross_project.png','project_differences.png']
    for filename in figures:
        assert (results/filename).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    # Enrich the original exclusions without overwriting pre-fit evidence.
    original=pd.read_csv('artifacts/dataset/exclusion_log.csv')
    projects=pd.read_csv('artifacts/audit/project_sprints.csv').set_index('id').project_key
    original['project']=original.project_id.map(projects)
    original['exclusion_level']=np.where(original.issue_id.isna(),'sprint',np.where(original.sprint_id.isna(),'issue_or_sprint_reference','issue_sprint'))
    def source(reason):
        if reason=='created_after_commitment': return 'issue.creation_date; sprint.start_date'
        if reason.startswith('sprint_'): return 'sprint.state/start_date/end_date'
        if reason in ['unknown_or_ambiguous_end_status','history_discontinuity']: return 'change_log.status/Sprint; change_log.creation_date; sprint.end_date'
        return 'change_log.Sprint.from_value/to_value; change_log.creation_date; sprint.start_date'
    original['source_fields_and_timestamp']=original.reason.map(source)
    original['decided_by']='registered_research_pipeline'
    original['decision_date']='2026-10-08'
    original['protocol_version']='1.0'
    original['enrichment_note']='Provenance columns added after evaluation; original exclusions and dataset unchanged.'
    original.to_csv('artifacts/dataset/exclusion_log_enriched.csv',index=False)
    requirements={
        'protocol_and_questions':['documents/Protocol_v1.md','artifacts/protocol/config.json','artifacts/protocol/lock.json'],
        'data_audit_and_citations':['documents/Data_card_TAWOS.md','documents/Literature_and_methods.md','documents/references.bib','artifacts/audit/source_manifest.csv'],
        'cohort_labels_and_exclusions':['artifacts/dataset/project_eligibility.csv','artifacts/dataset/exclusion_log_enriched.csv','artifacts/dataset/label_mapping.csv','artifacts/validation/sql_sample_audit.csv'],
        'snapshots_features_and_leakage_checks':['data/processed/snapshots.parquet','artifacts/validation/feature_dictionary.csv','artifacts/validation/data_validation.json','tests/test_replay.py','tests/test_cohort_features.py'],
        'temporal_and_project_splits':['artifacts/protocol/temporal_split_manifest.csv','artifacts/protocol/cross_project_split_manifest.csv','tests/test_splits.py'],
        'trained_baselines_dynamic_ablation_and_calibration':['artifacts/validation/prediction_audit.csv','artifacts/validation/prediction_validation.json'],
        'evaluation_uncertainty_budget_and_leadtime':['artifacts/results/probability_metrics.csv','artifacts/results/paired_comparisons.csv','artifacts/results/sensitivity_metrics.csv','artifacts/results/sequential_alert_log.csv'],
        'analysis_and_reproducibility':['documents/Bao_cao_nghien_cuu_giai_doan_4.md','documents/Thao_luan_ket_qua.md','documents/Reproduce_research.md','artifacts/environment/runtime.json'],
        'progress_decisions_and_checkpoints':['documents/Research_progress.md'],
    }
    for paths in requirements.values():
        for filename in paths: assert Path(filename).is_file() and Path(filename).stat().st_size>0,filename
    report={'audited_at':datetime.now(timezone(timedelta(hours=7))).isoformat(),'scope':'registered archival study through phase 4',
            'requirements':requirements,'frozen_pre_fit_artifacts_unchanged':frozen,'prediction_triplets_unchanged':672,
            'sequential_budget_and_dedup_verified':True,'result_tables_checked':expected_tables,'figures':figures,
            'checks_passed':True,
            'limitations_not_claimed_complete':['human business workflow ground truth/inter-rater agreement','historical changes to sprint dates',
                                               'live intervention/Agentick integration (phase 5+)','exhaustive SOTA search or novel algorithm proof'],
            'note':'Completion of the registered offline study is distinct from production deployment or publication acceptance.'}
    Path('artifacts/validation/completion_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'checks_passed':True,'requirements_checked':len(requirements),'triplets':672,'tables':expected_tables},indent=2))


if __name__=='__main__': main()
