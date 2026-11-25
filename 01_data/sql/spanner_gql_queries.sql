-- ============================================================================
-- Cloud Spanner Studio / Spanner Omni — Verified ISO GQL Queries (`GRAPH DCGraph`)
-- ============================================================================

-- Query Option A: Pure North America Data Commons Geographic Hierarchy (25 nodes, 36 edges)
GRAPH DCGraph
MATCH p_dc =
  (na:continent {subject_id: 'northamerica'})<-[:containedinplace]-(usa:country {subject_id: 'country/USA'})
  <-[:containedinplace]-(reg:censusregion)<-[:containedinplace]-(div:censusdivision)
  <-[:containedinplace]-(st:state)<-[:containedinplace]-(c:county)
WHERE c.subject_id IN (
  'geoId/21159', 'geoId/01119', 'geoId/28151', 'geoId/28011',
  'geoId/13141', 'geoId/28083', 'geoId/01063', 'geoId/05041',
  'geoId/12065', 'geoId/13301', 'geoId/48427', 'geoId/21121'
)
OPTIONAL MATCH p_corridor = (c)-[:borders]->(neighbor:county)
RETURN
  TO_JSON(p_dc) AS north_america_datacommons_path,
  TO_JSON(p_corridor) AS county_border_corridor,
  na.name AS continent,
  usa.name AS country,
  reg.name AS census_region,
  div.name AS census_division,
  st.name AS state_name,
  c.name AS county_name,
  c.capacity AS county_population
ORDER BY county_population DESC;

-- Query Option B: Unified Data Commons x Federal Agency Dispatch Graph (39 nodes, 64 edges)
GRAPH DCGraph
MATCH p_main =
  (na:continent {subject_id: 'northamerica'})<-[:containedinplace]-(usa:country {subject_id: 'country/USA'})
  <-[:containedinplace]-(reg:censusregion)<-[:containedinplace]-(div:censusdivision)
  <-[:containedinplace]-(st:state)<-[:containedinplace]-(c:county)
  <-[:recommended_for]-(team:team)-[:dispatchedfrom]->(hub:hub)
  <-[:funds_hub]-(prog:program)<-[:leads]-(ag:agency)-[:governedby]->(usa)
WHERE NOT EXISTS {
  MATCH (:team)-[:covers]->(c2:county)
  WHERE c2.subject_id = c.subject_id
}
OPTIONAL MATCH p_corridor = (c)-[:borders]->(neighbor:county)
RETURN
  TO_JSON(p_main) AS federal_readiness_graph_path,
  TO_JSON(p_corridor) AS county_corridor_path,
  c.name AS county_name,
  st.name AS state_name,
  div.name AS census_division,
  c.capacity AS county_population,
  team.name AS recommended_mobile_unit,
  hub.name AS fema_regional_hub,
  prog.name AS federal_program,
  ag.name AS lead_federal_agency
ORDER BY county_population DESC;
