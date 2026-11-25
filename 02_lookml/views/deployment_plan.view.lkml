view: deployment_plan {
  sql_table_name: `beacon_disaster_readiness.deployment_plan` ;;

  dimension: county_id { primary_key: yes type: string sql: ${TABLE}.county_id ;; }
  dimension: action { type: string sql: ${TABLE}.action ;; }
  dimension: assigned_team_id { type: string sql: ${TABLE}.assigned_team_id ;; }
  dimension: priority_tier { type: string sql: ${TABLE}.priority_tier ;; }
  dimension: status { type: string sql: ${TABLE}.status ;; }
  measure: active_dispatches { type: count_distinct sql: ${county_id} ;; }
}
