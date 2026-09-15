-- Total Time Watched:
-- Compare weighted synthetic TTW against unweighted digital TTW. 

SELECT
tv_date, channel_id, target_group, 
sum(session_duration) AS TTW,
sum(session_duration * viewer_weight) AS weighted_TTW
FROM output_active_sessions
GROUP BY 1, 2, 3