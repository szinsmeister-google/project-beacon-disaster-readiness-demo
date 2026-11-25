-- ============================================================================
-- BigQuery Studio — Borderless Lakehouse Federated Query
-- Joins BigQuery `county_readiness`, Apache Iceberg (`noaa_hazard_iceberg`,
-- `fema_field_assessments_iceberg`), and Unstructured SitRep PDF Object Table
-- (`fema_field_sitrep_objects`). Replace `YOUR_PROJECT_ID` before running.
-- ============================================================================

SELECT
  c.county_name AS priority_county,
  ROUND(c.social_vulnerability_score, 2) AS svi_score,
  h.active_hazard_alert,
  f.road_washout_status,
  f.recommended_mobile_unit,
  obj.uri AS unstructured_sitrep_pdf_uri,
  obj.content_type AS object_format,
  ROUND(c.no_internet_pct, 1) AS no_internet_pct,
  h.cell_tower_outage_pct,
  f.regional_hub,
  f.priority_tier
FROM `YOUR_PROJECT_ID.beacon_disaster_readiness.county_readiness` AS c
JOIN `YOUR_PROJECT_ID.beacon_disaster_readiness.noaa_hazard_iceberg` AS h
  ON c.county_id = h.county_id
JOIN `YOUR_PROJECT_ID.beacon_disaster_readiness.fema_field_assessments_iceberg` AS f
  ON c.county_id = f.county_id
JOIN `YOUR_PROJECT_ID.beacon_disaster_readiness.fema_field_sitrep_objects` AS obj
  ON f.sitrep_pdf_uri = obj.uri
WHERE c.has_team_coverage = FALSE
  AND c.social_vulnerability_score >= 75.0
ORDER BY c.social_vulnerability_score DESC
LIMIT 10;
