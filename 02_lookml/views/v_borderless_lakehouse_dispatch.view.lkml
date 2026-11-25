view: v_borderless_lakehouse_dispatch {
  sql_table_name: `beacon_disaster_readiness.v_borderless_lakehouse_dispatch` ;;

  dimension: county_id { primary_key: yes type: string sql: ${TABLE}.county_id ;; }
  dimension: active_hazard_alert { type: string sql: ${TABLE}.active_hazard_alert ;; }
  dimension: road_washout_status { type: string sql: ${TABLE}.road_washout_status ;; }
  dimension: recommended_mobile_unit { type: string sql: ${TABLE}.recommended_mobile_unit ;; }
  dimension: sitrep_pdf_uri { type: string sql: ${TABLE}.sitrep_pdf_uri ;; }
  measure: avg_cell_tower_outage_pct { type: average value_format: "0.0"%"" sql: ${TABLE}.cell_tower_outage_pct ;; }
}
