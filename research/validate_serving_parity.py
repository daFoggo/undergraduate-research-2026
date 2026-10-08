"""Sample trusted local bundles and verify adapter against frozen predictions."""
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.services.risk_inference import score_bundle


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    lock = json.loads(Path('artifacts/protocol/lock.json').read_text())
    snapshots_path = Path('data/processed/snapshots.parquet')
    assert digest(snapshots_path) == lock['dataset_sha256']
    data = pd.read_parquet(snapshots_path)
    records = []
    # Fixed representative fold, not selected by test quality. All main scorers.
    for experiment in ('temporal', 'cross_project'):
        for method in ('business_rule', 'static_catboost', 'dynamic_catboost'):
            for landmark in (.25, .5, .75):
                key = f'{experiment}__XD__{landmark:g}__{method}'
                model_path = Path('artifacts/models') / f'{key}.joblib'
                pred_path = Path('artifacts/predictions') / f'{key}.parquet'
                meta = json.loads((Path('artifacts/runs') / experiment / f'{key}.json').read_text())
                # Only locally generated trusted bundles, never supplied by network clients.
                bundle = joblib.load(model_path)
                assert bundle['run_hash'] == meta['run_hash']
                assert meta['dataset_hash'] == lock['dataset_sha256']
                expected = pd.read_parquet(pred_path).sort_values(['sprint_id', 'issue_id']).head(10)
                keys = ['sprint_id', 'issue_id', 'landmark']
                frame = expected[keys].merge(data, on=keys, validate='one_to_one')
                actual = score_bundle(bundle, frame, method, landmark)
                assert np.allclose(actual.p_raw, expected.p_raw.to_numpy(), rtol=0, atol=1e-12), key
                assert np.allclose(actual.p_calibrated, expected.p.to_numpy(), rtol=0, atol=1e-12), key
                records.append(dict(key=key, n=len(frame), model_sha256=digest(model_path),
                                    prediction_sha256=digest(pred_path), parity=True))
    result = dict(status='pass', scope='sample parity, not production calibration or full cohort validation',
                  fold='XD fixed, not chosen by performance', adapter_hash=digest('app/services/risk_inference.py'),
                  train_source_hash=digest('research/train.py'), bundles=len(records), rows=sum(r['n'] for r in records),
                  records=records)
    out = Path('artifacts/agent_extension/serving_parity.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        if json.loads(out.read_text()) != result:
            raise RuntimeError('Existing parity audit differs, preserve and investigate')
    else:
        out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'records'}))


if __name__ == '__main__':
    main()
