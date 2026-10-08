"""Trusted in-memory research bundle scoring, without selecting a deployment model.

No model loading from user-supplied paths and no public API added. Callers must
construct provenance-checked as-of snapshots and enforce authorization separately.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from research.train import logit, prepare


@dataclass(frozen=True)
class RiskScores:
    p_raw: pd.Series
    p_calibrated: pd.Series
    run_hash: str
    calibration_scope: str


def score_bundle(bundle, frame, method, landmark):
    if method not in {'frequency', 'business_rule', 'static_lr', 'static_catboost',
                      'dynamic_catboost', 'dynamic_no_cohort'}:
        raise ValueError('Unsupported method')
    if landmark not in {0., .25, .5, .75} or 'landmark' not in frame or not frame.landmark.eq(landmark).all():
        raise ValueError('Bundle landmark mismatch or unsupported landmark')
    if frame.empty:
        raise ValueError('Empty snapshot')
    columns = bundle['features']
    if not set(columns).issubset(frame.columns):
        raise ValueError('Missing bundle features')
    if method == 'frequency':
        raw = np.full(len(frame), bundle['constant'], dtype=float)
    elif method == 'business_rule':
        required = {'dynamic_is_done', 'dynamic_inactive_days', 'dynamic_status'}
        if not required.issubset(frame.columns):
            raise ValueError('Missing rule features')
        raw = np.where(frame.dynamic_is_done == 1, .01,
                       np.clip(.5 + .02 * frame.dynamic_inactive_days +
                               .1 * (frame.dynamic_status == 'unknown'), .01, .99))
    else:
        if bundle['model'] is None:
            raise ValueError('Missing fitted model')
        prepared, _ = prepare(frame, columns)
        raw = bundle['model'].predict_proba(prepared)[:, 1]
    if not np.isfinite(raw).all() or not ((raw >= 0) & (raw <= 1)).all():
        raise ValueError('Non-finite or out-of-range model output')
    calibrator = bundle.get('calibrator')
    calibrated = calibrator.predict_proba(logit(raw))[:, 1] if calibrator is not None else raw.copy()
    if not np.isfinite(calibrated).all() or not ((calibrated >= 0) & (calibrated <= 1)).all():
        raise ValueError('Invalid calibrated output')
    scope = ('validation-fitted sigmoid; target deployment calibration unverified' if calibrator is not None
             else 'identity; target deployment calibration unverified')
    return RiskScores(pd.Series(raw, index=frame.index, name='p_raw'),
                      pd.Series(calibrated, index=frame.index, name='p_calibrated'),
                      bundle['run_hash'], scope)
