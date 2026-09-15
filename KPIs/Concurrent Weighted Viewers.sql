-- Concurrent Weighted Viewers:
-- Compare the sum of active synthetic viewer weights with the number of active digital sessions over time. 

with cte as
(SELECT
tv_date, channel_id, target_group, viewer_weight,
session_start as ts, 1 AS session_flag
FROM output_active_sessions

UNION ALL

SELECT
tv_date, channel_id, target_group, viewer_weight,
session_finish as ts, -1 AS session_flag
FROM output_active_sessions
)

SELECT
tv_date, channel_id, target_group,
ts,
COUNT(session_count) AS num_sessions,
SUM(viewer_weight * session_count) AS weighted_sum
from
(select 
tv_date, channel_id, target_group, viewer_weight,
ts,
SUM(session_flag) OVER (
PARTITION BY tv_date, channel_id, target_group
ORDER BY ts ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
AS session_count
FROM cte)
GROUP BY 1, 2, 3, 4