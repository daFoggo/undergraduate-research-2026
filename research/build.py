"""Build commitment cohort and snapshots from timestamped evidence only.

Run from the repository root: python -m research.build
"""
import csv
import hashlib
import json
import os
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import psycopg
from psycopg.rows import dict_row

from research.replay import AMBIGUOUS, CANCELLED, DONE, Event, Timeline, normalize, sprint_set

OUT = Path('artifacts/dataset')
DATA = Path('data/processed')
FIELDS = ('Sprint', 'status', 'resolution', 'priority', 'issuetype', 'assignee', 'Story Points')


def save_csv(name, rows):
    if rows:
        pd.DataFrame(rows).to_csv(OUT/f'{name}.csv', index=False)


def attach_cohort_features(frame):
    """Use observed states for the entire commitment cohort; never inspect outcomes."""
    frame=frame.copy()
    for (_,landmark),group in frame.groupby(['sprint_id','landmark']):
        frame.loc[group.index,'dynamic_cohort_done_fraction']=group.dynamic_is_done.mean()
        frame.loc[group.index,'static_cohort_done_fraction']=group.static_is_done.mean()
        frame.loc[group.index,'cohort_size']=len(group)
    return frame


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    exclusions, rows, summaries, mapping, all_cohorts = [], [], [], [], []
    with psycopg.connect(os.environ.get('RESEARCH_DATABASE_URL', 'postgresql://tawos:tawos_local_dev@localhost:5432/tawos'), row_factory=dict_row) as con:
        con.execute('SET TRANSACTION READ ONLY')
        projects = con.execute('SELECT id,project_key FROM tawos_raw.project ORDER BY id').fetchall()
        all_sprints = con.execute('SELECT * FROM tawos_raw.sprint ORDER BY start_date,id').fetchall()
        for project in projects:
            pid = project['id']
            print(f"Building {project['project_key']}", flush=True)
            sprints = {}
            for sprint in [s for s in all_sprints if s['project_id'] == pid]:
                start, end = sprint['start_date'], sprint['end_date']
                reason = None
                if normalize(sprint['state']) != 'closed' or not start or not end or end <= start:
                    reason = 'sprint_not_closed_or_invalid_dates'
                elif start.year < 2000 or not 1 <= (end-start).total_seconds()/86400 <= 60:
                    reason = 'sprint_date_or_duration_outlier'
                if reason:
                    exclusions.append({'project_id':pid,'sprint_id':sprint['id'],'issue_id':None,'reason':reason})
                else:
                    sprints[sprint['jiraid']] = sprint
            if not sprints:
                summaries.append({'project_id':pid,'project':project['project_key'],'sprints':0,'instances':0,'positive':0,'negative':0})
                continue
            issues = con.execute("""SELECT i.id,i.creation_date FROM tawos_raw.issue i WHERE project_id=%s
                AND EXISTS (SELECT 1 FROM tawos_raw.change_log c WHERE c.issue_id=i.id AND c.field='Sprint')""", (pid,)).fetchall()
            events = defaultdict(list)
            with con.cursor(name=f'project_{pid}') as cursor:
                cursor.execute("""SELECT c.id,c.issue_id,c.creation_date,c.field,c.from_value,c.to_value,
                    c.from_string,c.to_string FROM tawos_raw.change_log c JOIN tawos_raw.issue i ON i.id=c.issue_id
                    WHERE i.project_id=%s AND c.field=ANY(%s) ORDER BY c.issue_id,c.creation_date,c.id""", (pid, list(FIELDS)))
                for event in cursor:
                    if event['creation_date']:
                        events[event['issue_id']].append(Event(event['id'],event['creation_date'],event['field'],event['from_value'],event['to_value'],event['from_string'],event['to_string']))
            p_rows, status_counts = [], Counter()
            for issue in issues:
                iid, created = issue['id'], issue['creation_date']
                timeline = Timeline(events[iid])
                candidates = set()
                bad_membership = False
                for event in timeline.events:
                    if event.field == 'Sprint':
                        try:
                            candidates.update(sprint_set(event.after))
                        except ValueError:
                            bad_membership = True
                if bad_membership:
                    exclusions.append({'project_id':pid,'sprint_id':None,'issue_id':iid,'reason':'unparseable_membership'})
                    continue
                for jiraid in candidates:
                    if jiraid not in sprints:
                        exclusions.append({'project_id':pid,'sprint_id':None,'issue_id':iid,'reason':'missing_sprint_record','jiraid':jiraid})
                        continue
                    sprint = sprints[jiraid]
                    start, end = sprint['start_date'], sprint['end_date']
                    reason = None
                    if not created or created > start:
                        reason = 'created_after_commitment'
                    elif jiraid not in timeline.membership(start):
                        reason = 'no_membership_evidence_at_commitment'
                    elif timeline.uncertain_interval('Sprint',start):
                        reason = 'membership_commitment_inside_missing_history_interval'
                    outcome = timeline.status(end)
                    if reason:
                        exclusions.append({'project_id':pid,'sprint_id':sprint['id'],'issue_id':iid,'reason':reason})
                        continue
                    membership_gaps = timeline.discontinuities('Sprint',end)
                    status_gaps = timeline.discontinuities('status',end)
                    end_uncertain = timeline.uncertain_interval('status',end)
                    label_unknown = outcome == 'unknown' or outcome in AMBIGUOUS or bool(membership_gaps or status_gaps) or end_uncertain
                    if label_unknown:
                        exclusions.append({'project_id':pid,'sprint_id':sprint['id'],'issue_id':iid,
                                           'reason':'history_discontinuity' if membership_gaps or status_gaps or end_uncertain else 'unknown_or_ambiguous_end_status'})
                    # Retain removal/reopen outcomes. Never use current issue status/resolution.
                    static = timeline.features(created,start,end,start)
                    relevant = timeline.before(end)
                    resolutions = [e for e in relevant if e.field == 'resolution']
                    resolution = normalize(resolutions[-1].after_text) if resolutions else ''
                    cancelled = outcome in CANCELLED or any(word in resolution for word in ('duplicate', "won't", 'invalid', 'cancel'))
                    removed = jiraid not in timeline.membership(end)
                    status_counts[outcome] += 1
                    for landmark in (0.0, .25, .5, .75):
                        at = start+(end-start)*landmark
                        dynamic = timeline.features(created,start,end,at)
                        row = {'project_id':pid,'project':project['project_key'],'sprint_id':sprint['id'],'issue_id':iid,
                               'start':start,'end':end,'prediction_at':at,'landmark':landmark,
                               'y':None if label_unknown else int(outcome not in DONE),'end_status':outcome,'cancelled':cancelled,
                               'removed':removed,'y_closed_only':int(outcome!='closed'),
                               'membership_gaps':len(membership_gaps),'status_gaps':len(status_gaps)}
                        row.update({f'static_{key}':value for key,value in static.items()})
                        row.update({f'dynamic_{key}':value for key,value in dynamic.items()})
                        assert datetime.fromisoformat(dynamic['feature_max_timestamp']) <= at
                        p_rows.append(row)
            frame = pd.DataFrame(p_rows)
            if not frame.empty:
                frame=attach_cohort_features(frame)
                # Compute cohort features before outcome exclusion: future labels cannot change features.
                all_cohorts.append(frame[frame.landmark==0].copy())
                frame = frame[frame.y.notna()].copy()
                frame['y'] = frame.y.astype(int)
                cohort = frame[frame.landmark == 0]
                summaries.append({'project_id':pid,'project':project['project_key'],'sprints':cohort.sprint_id.nunique(),
                                  'instances':len(cohort),'positive':int(cohort.y.sum()),'negative':int((cohort.y==0).sum())})
                rows.append(frame)
            else:
                summaries.append({'project_id':pid,'project':project['project_key'],'sprints':0,'instances':0,'positive':0,'negative':0})
            for status,n in status_counts.items():
                mapping.append({'project_id':pid,'status':status,'done':None if status=='unknown' or status in AMBIGUOUS else status in DONE,
                                'instances':n,'rule':'exact terminal whitelist; ambiguous excluded'})
    dataset = pd.concat(rows,ignore_index=True)
    dataset.to_parquet(DATA/'snapshots.parquet',index=False)
    pd.concat(all_cohorts,ignore_index=True).to_parquet(DATA/'all_commitments.parquet',index=False)
    save_csv('project_eligibility', summaries)
    save_csv('exclusion_log', exclusions)
    save_csv('label_mapping',mapping)
    manifest = {'created_at':datetime.now(timezone.utc).isoformat(),'rows':len(dataset),'instances':len(dataset[dataset.landmark==0]),
                'sha256':hashlib.sha256((DATA/'snapshots.parquet').read_bytes()).hexdigest(),
                'fields_observed':FIELDS,'cohort':'explicit last Sprint.to_value at or before Start_Date',
                'outcome':'last observed status.to_string at or before End_Date; unknown excluded',
                'done_statuses':sorted(DONE),'ambiguous_excluded':sorted(AMBIGUOUS),
                'notes':['No final issue field is used as historical feature.','No status before first observed status event: unknown.',
                         'Event counts count only selected fields, not all issue activity.','Dataset eligibility is checked before model training.']}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2),flush=True)


if __name__ == '__main__':
    main()
