view: national_macro_timeline {
  sql_table_name: `beacon_disaster_readiness.national_macro_timeline` ;;

  dimension: year { primary_key: yes type: number sql: ${TABLE}.year ;; }
  measure: total_billion_dollar_events { type: sum sql: ${TABLE}.billion_dollar_events ;; }
  measure: total_disaster_cost_b_usd { type: sum value_format: ""$"0.0"B"" sql: ${TABLE}.total_cost_b_usd ;; }
}
