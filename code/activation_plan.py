import pandas as pd
import sqlite3
from config import digital_sessions_target_groups
from datetime import datetime
import sys

def validate_date(date_str: str) -> str:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise SystemExit(f"Invalid date: '{date_str}'. Expected format: YYYY-MM-DD")

date = validate_date(sys.argv[1])
table_date = date.replace("-","")

db_path = "SQLite-db/sessions.db"
conn = sqlite3.connect(db_path)

sessions_df_demos = {}

for demo in digital_sessions_target_groups:
    sessions_df_demos[demo] = pd.read_sql(f"""
    SELECT * FROM digital_{table_date}_activation_sessions
    WHERE target_group = '{demo}'
    """, conn)
    sessions_df_demos[demo]["ts"] = pd.to_datetime(sessions_df_demos[demo]["ts"])
    sessions_df_demos[demo]["channel_id"] = sessions_df_demos[demo]["channel_id"].astype(int)

import numpy as np
# Build sorted list of synthetic viewers from viewer_weights
# What this covers: Sort eligible viewer by:
# 1. Prefer viewers who were not logged in viewer_sessions on this date.
# 2. Ascending representational weight within each demographic bucket

activation_order_df = pd.read_sql(f"""
SELECT * FROM
(SELECT 
demo, viewer_id, viewer_weight,
rank() OVER (
    PARTITION BY demo ORDER BY activated_today, viewer_weight
    ) AS activation_order
FROM
(SELECT demo, dvm.viewer_id, viewer_weight,
CASE WHEN avl.viewer_id IS NULL THEN 0 ELSE 1 END AS activated_today
from digital_viewer_mapping dvm
LEFT JOIN active_viewer_list_{table_date} avl
ON dvm.viewer_id = avl.viewer_id))
order by activation_order;
""", conn)
conn.commit()
conn.close()

# Link Sessions and Set Activation Logic
import time
import logging
import numpy as np
from config import digital_sessions_target_groups

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

start = time.time()
zeros = np.zeros(len(activation_order_df))
links_activation_order_df = pd.concat(
    [
    activation_order_df,
    pd.Series(zeros, name="session_count"), 
    pd.Series(zeros, name="active"), 
    ], 
    axis=1)
links_activation_order_df["channel"] = None

session_viewer_links = {}
links = {}
output_sessions = []
links_arrays = {}  # Store as numpy arrays for faster access
col_idx = {}  # Cache column indices
output_sessions_df_demos = {}

for demo in digital_sessions_target_groups:
    df = links_activation_order_df[links_activation_order_df["demo"]==demo].copy().reset_index(drop=True)
    links[demo] = df
    
    # Cache column positions
    col_idx[demo] = {
        'session_count': df.columns.get_loc("session_count"),
        'channel': df.columns.get_loc("channel"),
        'viewer_id': df.columns.get_loc("viewer_id"),
        'viewer_weight': df.columns.get_loc("viewer_weight"),
        'active': df.columns.get_loc("active")
    }
    
    # Convert to numpy arrays with writeable flag
    links_arrays[demo] = {
        'session_count': np.array(df["session_count"].values, copy=True),
        'channel': np.array(df["channel"].values, copy=True),
        'viewer_id': np.array(df["viewer_id"].values, copy=True),
        'viewer_weight': np.array(df["viewer_weight"].values, copy=True),
        'active': np.array(df["active"].values, copy=True)
    }

def activate_demo(demo, sessions_df):
    
    logger.info(f"Setup time: {time.time() - start:.2f}s")

    loop_start = time.time()
    processed = 0

    for row in sessions_df.itertuples():
        processed += 1
        if processed % 100000 == 0:
            elapsed = time.time() - loop_start
            rate = processed / elapsed
            remaining = (len(sessions_df) - processed) / rate
            logger.info(f"{demo} Progress: {processed}/{len(sessions_df)} {round(processed / len(sessions_df) * 100.0, 1)}% ({rate:.0f}/sec) ~{remaining:.0f}s left")
        
        s_id = row.session_id
        ts = row.ts
        demo = row.target_group
        channel = row.channel_id
        links_df = links[demo]
        arrays = links_arrays[demo]
        idx = col_idx[demo]

        if row.session_event == "start":
            # Vectorized filtering
            mask = ((arrays['channel'] == channel) | (arrays['channel'] == None)) & \
                (arrays['session_count'] <= arrays['viewer_weight'] - 1) & \
                (arrays['active'] == 1)
            possible_indices = np.where(mask)[0]
            
            if len(possible_indices) > 0:
                link_viewer_ind = int(possible_indices[0])
                v_id = arrays['viewer_id'][link_viewer_ind]

                # Update arrays directly
                arrays['session_count'][link_viewer_ind] += 1
                arrays['channel'][link_viewer_ind] = channel
                
                session_viewer_links[(demo, s_id, channel)] = (v_id, link_viewer_ind)

                output_sessions.append((ts, channel, v_id, demo, 0, 1, s_id)) # 0 for linking without activation; 1 for start
            else:
                # Try inactive viewers
                mask = ((arrays['channel'] == channel) | (arrays['channel'] == None)) & \
                    (arrays['session_count'] <= arrays['viewer_weight'] - 1) & \
                    (arrays['active'] == 0)
                possible_indices = np.where(mask)[0]

                if len(possible_indices) > 0:
                    link_viewer_ind = int(possible_indices[0])
                    v_id = arrays['viewer_id'][link_viewer_ind]

                    arrays['session_count'][link_viewer_ind] += 1
                    arrays['channel'][link_viewer_ind] = channel
                    
                    session_viewer_links[(demo, s_id, channel)] = (v_id, link_viewer_ind)
                    
                    # Check Activation
                    if arrays['session_count'][link_viewer_ind] >= round(arrays['viewer_weight'][link_viewer_ind] * 0.5):
                        arrays['active'][link_viewer_ind] = 1
                        output_sessions.append((ts, channel, v_id, demo, 1, 1, s_id)) # 1 for activation; 1 for start
                    else:
                        output_sessions.append((ts, channel, v_id, demo, 0, 1, s_id)) # 0 for linking without activation; 1 for start
                else:
                    logger.warning(f"No viewer found for session {s_id} in {demo}")

        else:  # Session Finish
            try:
                v_id, link_viewer_ind = session_viewer_links[(demo, s_id, channel)]
                arrays['session_count'][link_viewer_ind] -= 1

                # Check Deactivation
                if (arrays['session_count'][link_viewer_ind] < round(arrays['viewer_weight'][link_viewer_ind] * 0.5)) and \
                    (arrays['active'][link_viewer_ind] == 1):
                    arrays['active'][link_viewer_ind] = 0
                    output_sessions.append((ts, channel, v_id, demo, -1, -1, s_id)) # -1 for deactivation; -1 for session_finish
                else:
                    output_sessions.append((ts, channel, v_id, demo, 0, -1, s_id)) # 0 for deactivation; -1 for session_finish
                if arrays['session_count'][link_viewer_ind] < 0:
                    logger.error(f"Sub-zero session_count at {(ts, v_id)}")
            except KeyError:
                logger.warning(f"Viewer not found for session_id: {s_id}")

    logger.info(f"{demo}: Total loop time: {time.time() - loop_start:.2f}s")

    out_df = pd.DataFrame(
        output_sessions,
        columns=["ts","channel_id","viewer_id","target_group","activation_flag", "start_or_finish", "session_id"],
    )
    return out_df

output_sessions_df = pd.DataFrame(
        columns=["ts","channel_id","viewer_id","target_group","activation_flag", "start_or_finish", "session_id"],
    )

# Run Activation in parallel
from multiprocessing import Pool
num_processes = len(digital_sessions_target_groups)

if __name__ == '__main__':
    with Pool(num_processes) as p:
        output_sessions_df = pd.concat(
            p.starmap(
                activate_demo,
                [(demo, sessions_df_demos[demo]) for demo in sessions_df_demos],
            ),
            ignore_index=True,
        )

conn = sqlite3.connect(db_path)
output_sessions_df.to_sql(name=f"output_sessions_{table_date}", if_exists="replace", con=conn)
# output_sessions_df.to_csv(f"output_sessions_{table_date}")

from config import model_version

try:
    conn.execute(f"DELETE FROM output_active_sessions WHERE tv_date = '{date}'")
    
    conn.execute(f"""
    INSERT INTO output_active_sessions
    select 
        '{date}' AS tv_date,
        channel_id, sesh.target_group, sesh.viewer_id, session_start, session_finish,
        round((julianday(session_finish) - julianday(session_start))* 86400, 0) AS session_duration,
        vw.viewer_weight
    FROM
        (select 
        channel_id,
        viewer_id,
        target_group,
        MAX(CASE WHEN activation_flag = 1 THEN ts END) AS session_start,
        MAX(CASE WHEN activation_flag = -1 THEN ts END) AS session_finish
        from (
            select 
                datetime(ts) AS ts, channel_id, viewer_id, target_group, activation_flag,
                sum(CASE WHEN activation_flag = 1 THEN 1 ELSE 0 END) OVER  
                (PARTITION BY viewer_id order by ts 
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS session_index
            from output_sessions_{table_date}) 
        group by 
            channel_id,viewer_id,target_group,session_index) sesh
        LEFT JOIN  (SELECT DISTINCT viewer, viewer_weight FROM viewer_weights
            WHERE model_version = '{model_version}') vw
            ON vw.viewer = sesh.viewer_id
            /*
            Because we have records in the table that are pre-activation links,
            those show up as session_start = session_finish = NULL. So, we need to filter here to include only sessio.
            */
        WHERE session_start IS NOT NULL 
    """)
except:
    logger.info("Table output_active_sessions doesn't exist yet, creating...")
    conn.execute(f"""
        CREATE TABLE output_active_sessions AS
        select 
            '{date}' AS tv_date,
            channel_id, sesh.target_group, sesh.viewer_id, session_start, session_finish,
            round((julianday(session_finish) - julianday(session_start))* 86400, 0) AS session_duration,
            vw.viewer_weight
        FROM
            (select 
            channel_id,
            viewer_id,
            target_group,
            MAX(CASE WHEN activation_flag = 1 THEN ts END) AS session_start,
            MAX(CASE WHEN activation_flag = -1 THEN ts END) AS session_finish
            from (
                select 
                    datetime(ts) AS ts, channel_id, viewer_id, target_group, activation_flag,
                    sum(CASE WHEN activation_flag = 1 THEN 1 ELSE 0 END) OVER  
                    (PARTITION BY viewer_id order by ts 
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS session_index
                from output_sessions_{table_date}) 
            group by 
                channel_id,viewer_id,target_group,session_index) sesh
            LEFT JOIN  (SELECT DISTINCT viewer, viewer_weight FROM viewer_weights
                WHERE model_version = '{model_version}') vw
                ON vw.viewer = sesh.viewer_id
                /*
                Because we have records in the table that are pre-activation links,
                those show up as session_start = session_finish = NULL. So, we need to filter here to include only sessio.
                */
            WHERE session_start IS NOT NULL 
        """)

conn.commit()
conn.close()