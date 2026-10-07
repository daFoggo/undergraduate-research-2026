from datetime import datetime, timedelta, timezone

import pandas as pd

from research.splits import temporal_split


def test_split_purges_labels_unavailable_at_next_partition():
    base = datetime(2020,1,1,tzinfo=timezone.utc)
    rows = [{'sprint_id':i,'start':base+timedelta(days=i*7),'end':base+timedelta(days=i*7+14)} for i in range(50)]
    split = temporal_split(pd.DataFrame(rows))
    train = split[split.partition=='train']
    val = split[split.partition=='validation']
    test = split[split.partition=='test']
    assert train.end.max() < val.start.min()
    assert val.end.max() < test.start.min()
    assert (split.partition=='purged').any()
