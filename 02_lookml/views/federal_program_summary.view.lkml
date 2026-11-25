view: federal_program_summary {
  sql_table_name: `beacon_disaster_readiness.federal_program_summary` ;;

  dimension: program_short { primary_key: yes type: string sql: ${TABLE}.program_short ;; }
  dimension: lead_agency { type: string sql: ${TABLE}.lead_agency ;; }
  measure: total_households_helped_k { type: sum sql: ${TABLE}.households_helped_k ;; }
  measure: avg_web_intake_share_pct { type: average value_format: "0.0"%"" sql: ${TABLE}.web_intake_share_pct ;; }
}
