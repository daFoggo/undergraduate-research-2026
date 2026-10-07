"""Read-only TAWOS feasibility audit; outputs small reproducible research artifacts."""
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg

OUTPUT = Path('artifacts/audit')
QUERIES = {
    'schema': "SELECT table_name,column_name,data_type FROM information_schema.columns WHERE table_schema='tawos_raw' ORDER BY table_name,ordinal_position",
    'project_sprints': """SELECT p.id,p.project_key,p.repository_id,count(s.id) sprints,
        count(s.id) FILTER (WHERE upper(s.state)='CLOSED' AND s.end_date>s.start_date) valid_closed,
        min(s.start_date) first_start,max(s.end_date) last_end,
        count(s.id) FILTER (WHERE extract(epoch FROM s.end_date-s.start_date)/86400 NOT BETWEEN 1 AND 60) unusual_duration,
        count(s.id) FILTER (WHERE abs(extract(epoch FROM s.activated_date-s.start_date))>86400) activated_diff_gt_day
        FROM tawos_raw.project p LEFT JOIN tawos_raw.sprint s ON s.project_id=p.id GROUP BY p.id ORDER BY p.id""",
    'status_values': """SELECT i.project_id,c.field,c.from_string,c.to_string,count(*) n
        FROM tawos_raw.change_log c JOIN tawos_raw.issue i ON i.id=c.issue_id
        WHERE c.field IN ('status','resolution') GROUP BY 1,2,3,4 ORDER BY 1,2,5 DESC""",
    'membership_coverage': """WITH tokens AS (
        SELECT DISTINCT i.project_id,trim(token) token FROM tawos_raw.change_log c
        JOIN tawos_raw.issue i ON i.id=c.issue_id
        CROSS JOIN LATERAL regexp_split_to_table(coalesce(c.from_value,'')||','||coalesce(c.to_value,''),',') token
        WHERE c.field='Sprint' AND trim(token)<>''), matches AS (
        SELECT t.project_id,t.token,count(s.id) match_count FROM tokens t
        LEFT JOIN tawos_raw.sprint s ON s.project_id=t.project_id AND s.jiraid::text=t.token GROUP BY 1,2)
        SELECT project_id,count(*) tokens,count(*) FILTER (WHERE match_count=1) matched,
        count(*) FILTER (WHERE match_count=0) unmatched,count(*) FILTER (WHERE match_count>1) ambiguous
        FROM matches GROUP BY 1 ORDER BY 1""",
    'field_counts': "SELECT field,change_type,count(*) n FROM tawos_raw.change_log GROUP BY 1,2 ORDER BY 3 DESC",
    'sprint_sample': """SELECT c.id,c.issue_id,i.project_id,c.creation_date,c.from_value,c.to_value,c.from_string,c.to_string
        FROM tawos_raw.change_log c JOIN tawos_raw.issue i ON i.id=c.issue_id
        WHERE c.field='Sprint' ORDER BY c.id LIMIT 100""",
    'source_manifest': 'SELECT * FROM research.dataset_imports',
}


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    url = os.environ.get('RESEARCH_DATABASE_URL', 'postgresql://tawos:tawos_local_dev@localhost:5432/tawos')
    manifest = {'started_at': datetime.now(timezone.utc).isoformat(), 'queries': QUERIES, 'outputs': {}}
    with psycopg.connect(url) as connection:
        connection.execute('SET TRANSACTION READ ONLY')
        for name, query in QUERIES.items():
            print(f'Audit {name}', flush=True)
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                with (OUTPUT / f'{name}.csv').open('w', encoding='utf-8', newline='') as handle:
                    writer = csv.writer(handle)
                    writer.writerow([column.name for column in cursor.description])
                    writer.writerows(rows)
                manifest['outputs'][name] = len(rows)
    manifest['finished_at'] = datetime.now(timezone.utc).isoformat()
    (OUTPUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest['outputs']), flush=True)


if __name__ == '__main__':
    main()
