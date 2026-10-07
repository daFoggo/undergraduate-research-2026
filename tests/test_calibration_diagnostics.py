import pandas as pd

from research.evaluate import probability_metrics


def test_constant_scores_do_not_claim_identifiable_calibration_slope():
    metrics=probability_metrics(pd.DataFrame({'y':[0,1,0,1],'p':[.5]*4}))
    assert metrics['calibration_slope'] is None
    assert metrics['calibration_intercept'] is None
    assert metrics['brier']==.25
