import pandas as pd

from research.validate_agent_policy import utc_times


def test_iso_timestamps_with_mixed_fractional_seconds():
    serialized = pd.Series(['2015-12-19 20:19:09.500000+00:00', '2015-12-19 20:19:09+00:00'])
    expected = pd.Series([pd.Timestamp('2015-12-19T20:19:09.5Z'), pd.Timestamp('2015-12-19T20:19:09Z')])
    assert utc_times(serialized).eq(expected).all()
    assert utc_times(expected).eq(expected).all()
