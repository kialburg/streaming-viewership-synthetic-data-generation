-- Demographic Consistincy:
-- Verify that assignments remain within the correct demographic bucket.

SELECT out.session_id, 
out.viewer_id, out.target_group,
dig.target_group
FROM output_sessions_20250907 out
LEFT JOIN digital_20250907_sessions dig 
ON dig.session_id = out.session_id
WHERE out.target_group <> dig.target_group;