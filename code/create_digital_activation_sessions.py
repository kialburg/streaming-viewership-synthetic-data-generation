import sqlite3
import sys

if len(sys.argv) < 2:
    print("Usage: python create_single_viewer_session.py <viewer_id>")
    sys.exit(1)

date = sys.argv[1]
table_date = date.replace("-","")

db_path = "SQLite-db/sessions.db"
conn = sqlite3.connect(db_path)

conn.execute(f"DROP TABLE IF EXISTS digital_{table_date}_activation_sessions")

conn.execute(f"""
CREATE TABLE digital_{table_date}_activation_sessions AS
-- SQLite
WITH cte AS
(SELECT 
session_start AS ts, target_group, channel_id, 1 AS change, 'start' AS session_event, session_id
FROM digital_{table_date}_sessions

UNION ALL 

SELECT
session_finish AS ts, target_group, channel_id, -1 AS change, 'end' AS session_event, session_id
FROM digital_{table_date}_sessions
)

SELECT 
ts,
target_group,
channel_id,
session_event,
session_id
FROM cte

order by ts
;
""")

conn.commit()
conn.close()