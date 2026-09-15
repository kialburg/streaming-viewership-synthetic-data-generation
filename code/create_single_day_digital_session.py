import sqlite3
import sys

if len(sys.argv) < 2:
    print("Usage: python create_single_viewer_session.py <viewer_id>")
    sys.exit(1)

date = sys.argv[1]
table_date = date.replace("-","")

db_path = "SQLite-db/sessions.db"
conn = sqlite3.connect(db_path)

conn.execute(f"DROP TABLE IF EXISTS digital_{table_date}_sessions")

conn.execute(f"""
CREATE TABLE digital_{table_date}_sessions AS
SELECT DISTINCT --there are duplicated records
tv_day, channel_id, session_start, session_finish, 
session_duration, session_id, target_group
FROM digital_sessions
WHERE tv_day = '{date}'
""")

conn.commit()
conn.close()