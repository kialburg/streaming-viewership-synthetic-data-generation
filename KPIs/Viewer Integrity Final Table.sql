-- Viewer Integrity: 
-- No sessions overlap (same as no viewer watches 2 channels at once)
select *
from (
select 
    viewer_id,
    session_start,
    lead(session_start) OVER (PARTITION BY viewer_id ORDER BY session_start) AS next_session_start,
    session_finish,
    lag(session_finish) OVER (PARTITION BY viewer_id ORDER BY session_finish) AS previous_session_finish
from output_active_sessions
)
where session_start <= previous_session_finish
or session_finish >= next_session_start
or session_start IS NULL
or session_finish IS NULL