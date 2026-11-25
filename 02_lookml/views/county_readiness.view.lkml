view: county_readiness {
  sql_table_name: `beacon_disaster_readiness.county_readiness` ;;

  dimension: county_id { primary_key: yes type: string sql: ${TABLE}.county_id ;; }
  dimension: county_name { type: string sql: ${TABLE}.county_name ;; }
  dimension: state_code { type: string sql: ${TABLE}.state_code ;; }
  dimension: fema_region { type: string sql: ${TABLE}.fema_region ;; }
  dimension: has_team_coverage { type: yesno sql: ${TABLE}.has_team_coverage ;; }

  dimension: is_tier1_vulnerable {
    label: "Tier-1 Vulnerable (SVI >= 75.0)"
    type: yesno
    sql: ${TABLE}.social_vulnerability_score >= 75.0 ;;
  }

  dimension: is_digital_divide_hazard {
    label: "Digital Divide Hazard (No Internet >= 18.0%)"
    type: yesno
    sql: ${TABLE}.no_internet_pct >= 18.0 ;;
  }

  measure: county_count { type: count_distinct sql: ${county_id} ;; }
  measure: unserved_tier1_counties {
    label: "Unserved Tier-1 Disaster Counties"
    type: count_distinct
    sql: ${county_id} ;;
    filters: [is_tier1_vulnerable: "yes", has_team_coverage: "no"]
  }
  measure: avg_svi_score { type: average value_format: "0.0" sql: ${TABLE}.social_vulnerability_score ;; }
  measure: avg_no_internet_pct { type: average value_format: "0.0"%"" sql: ${TABLE}.no_internet_pct ;; }
  measure: avg_web_registration_pct { type: average value_format: "0.0"%"" sql: ${TABLE}.web_registration_pct ;; }
  measure: total_population { type: sum sql: ${TABLE}.population ;; }
}
