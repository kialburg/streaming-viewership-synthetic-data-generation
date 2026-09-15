import sqlite3
from config import model_version

db_path = "SQLite-db/sessions.db"
conn = sqlite3.connect(db_path)

conn.execute("DROP TABLE IF EXISTS digital_viewer_mapping")

conn.execute(f"""
CREATE TABLE digital_viewer_mapping AS
SELECT 
vw.viewer as viewer_id, vw.viewer_weight, tgm.id AS demo, tgm.display_name
FROM viewer_weights vw
JOIN digital_target_group_mappings tgm
ON vw.target_group = tgm.target_group
WHERE vw.model_version='{model_version}'
""")

conn.commit()
conn.close()