import pandas as pd

from research.build import attach_cohort_features


def test_unknown_or_changed_future_outcomes_do_not_change_cohort_features():
    cohort=pd.DataFrame({'sprint_id':[1,1,1],'landmark':[.5,.5,.5],
                         'static_is_done':[0,0,0],'dynamic_is_done':[1,0,0],
                         'y':[0,1,None],'end_status':['done','open','unknown']})
    original=attach_cohort_features(cohort)
    changed=attach_cohort_features(cohort.assign(y=[1,None,0],end_status=['reopened','unknown','done']))
    columns=['dynamic_cohort_done_fraction','static_cohort_done_fraction','cohort_size']
    pd.testing.assert_frame_equal(original[columns],changed[columns])
    assert original.cohort_size.eq(3).all()
    assert original.dynamic_cohort_done_fraction.eq(1/3).all()
