## Your Task and the Expected Final Output 

Brief: This should dynamically activate and deactivate internal synthetic viewers when enough unweighted digital sessions match a synthetic viewer's weight.

 To map the external digital sessions into the existing infrastructure, a new approach needs to be developed. This should dynamically activate and deactivate internal synthetic viewers when enough unweighted digital sessions match a synthetic viewers weight. The solution must preserve weighting and demographic consistency and support KPI comparability across multiple aggregation levels. 

- The final output consists of session-shaped records structurally equivalent to the existing synthetic linear-TV 
sessions.
- Records must preserve channel, broadcast day, time interval, demographic bucket, synthetic unit identifier, and 
relevant representational weight fields needed for KPI calculation. 
- No synthetic viewer is allowed to be watching on more than one channel at a time

### Author thoughts:

Output format: 
output_sessions: session_id, viewer_id, channel, tv_day, session_start / finish, target_group, "synthetic unit identifier", viewer_weight
viewer_id <-> (channel, time_interval)

digital_sessions columns: 
session_id, channel_id, tv_day, sesstion_start / finish, target_group,
Missing columns: viewer_id, " synthetic unit identifier", "representational weight"

## Objectives
1. Match digital sessions and synthetic viewer by demographic bucket

I think this suggests that we are not tracking individual viewers in digital_sessions. Only the labels applied in target_group?

Should I use device_id to track individual viewers? I'm still trying to figure out the goal of this KPI.

2. Use representational weights consistently for activation thresholds and capacity limits 

These are viewer_weights?

## Progress
- Not enough memory to hold all viewer_sessions at once, in SQLite or pandas // Future work: Migrate to Duckdb. For now, performance is not meaningfully affected and sqlite integrations are easier to use.
- SQL db built. Query with pd.read_sql_query(sql, conn)
- Should I truncate the db for performance improvement?
- What is Activation / Deactivation?
Example: A synthetic unit in bucket Male 12-29 with weight 10 has activation threshold round(10 x 0.5) = 5 and capacity 
round(10) = 10.
- Dim structure for target_group: viewer_sessions -> viewer_weights -> target_group_mappings -> digital_sessions_target_group. 

## Execution

1. Build SQL db with build_sqlitedb.py
2. Remove duplicates from target_mappings with dedupe_target_group_mappings.py
3. Create digital_demo -> viewer_id map with create_digital_viewer_demo_mapping.py
4. Build pool of synthetic viewers eligible for digital activation
