import numpy as np
import pandas as pd
import pytest

from app.services.risk_inference import score_bundle


def test_rule_adapter_matches_frozen_rule_and_does_not_claim_calibration():
    frame = pd.DataFrame(dict(landmark=[.5, .5], dynamic_is_done=[0, 1],
                              dynamic_inactive_days=[5., 5.], dynamic_status=['unknown', 'Done']))
    bundle = dict(model=None, features=[], calibrator=None, constant=None, run_hash='test')
    result = score_bundle(bundle, frame, 'business_rule', .5)
    assert np.allclose(result.p_raw, [.7, .01])
    assert result.calibration_scope == 'identity; target deployment calibration unverified'


def test_rejects_landmark_and_missing_features():
    bundle = dict(model=None, features=['static_age_days'], calibrator=None, constant=.5, run_hash='test')
    with pytest.raises(ValueError, match='landmark'):
        score_bundle(bundle, pd.DataFrame({'landmark': [.25]}), 'frequency', .5)
    with pytest.raises(ValueError, match='features'):
        score_bundle(bundle, pd.DataFrame({'landmark': [.5]}), 'frequency', .5)


def test_frequency_preserves_row_order_and_score():
    bundle = dict(model=None, features=[], calibrator=None, constant=.4, run_hash='test')
    frame = pd.DataFrame({'landmark': [.5, .5]}, index=[42, 7])
    result = score_bundle(bundle, frame, 'frequency', .5)
    assert result.p_raw.tolist() == [.4, .4]
    assert result.p_raw.index.tolist() == [42, 7]
