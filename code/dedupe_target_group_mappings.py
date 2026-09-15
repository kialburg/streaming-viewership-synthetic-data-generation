import sqlite3
from config import digital_sessions_target_groups

db_path = "SQLite-db/sessions.db"
conn = sqlite3.connect(db_path)

sql_filter = ', '.join(f"'{tg}'" for tg in digital_sessions_target_groups)

conn.execute("DROP TABLE IF EXISTS digital_target_group_mappings")

conn.execute(f"""
CREATE TABLE digital_target_group_mappings AS
SELECT DISTINCT * FROM target_group_mappings
WHERE id IN ({sql_filter})
""")

conn.commit()
conn.close()