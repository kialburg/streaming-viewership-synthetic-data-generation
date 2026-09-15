import sqlite3
import sys
from config import model_version

if len(sys.argv) < 2:
    print("Usage: python create_single_viewer_session.py <viewer_id>")
    sys.exit(1)

date = sys.argv[1]
table_date = date.replace("-","")

db_path = "SQLite-db/sessions.db"
conn = sqlite3.connect(db_path)

conn.execute(f"DROP TABLE IF EXISTS active_viewer_list_{table_date}")

conn.execute(f"""
CREATE TABLE active_viewer_list_{table_date} AS
SELECT DISTINCT viewer_id
FROM viewer_sessions
WHERE tv_day = '{date}'
and model_version = '{model_version}' --arbitrary choice
""")

conn.commit()
conn.close()