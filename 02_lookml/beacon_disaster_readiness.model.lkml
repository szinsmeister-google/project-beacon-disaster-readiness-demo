connection: "your_bigquery_connection"

include: "/views/*.view.lkml"

label: "U.S. Public Sector · Project Beacon Disaster Readiness"

explore: county_readiness {
  label: "Project Beacon · Unified County Readiness & Borderless Lakehouse"
  description: "Single-Explore semantic model uniting 3,144 U.S. counties (Data Commons + OpenFEMA), Spanner DeploymentPlan dispatches, Apache Iceberg hazard telemetry, and unstructured FEMA Field SitRep PDFs."

  join: deployment_plan {
    type: left_outer
    relationship: one_to_one
    sql_on: ${county_readiness.county_id} = ${deployment_plan.county_id} ;;
  }

  join: borderless_lakehouse {
    from: v_borderless_lakehouse_dispatch
    type: left_outer
    relationship: one_to_one
    sql_on: ${county_readiness.county_id} = ${borderless_lakehouse.county_id} ;;
  }

  join: federal_program_summary {
    type: cross
    relationship: many_to_many
  }

  join: national_macro_timeline {
    type: cross
    relationship: many_to_many
  }
}
