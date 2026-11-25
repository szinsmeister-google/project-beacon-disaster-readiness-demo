-- =============================================================================
-- Beacon Readiness Office x Data Commons on Spanner Graph -- demo schema
-- Dialect: GoogleSQL. Needs Spanner Graph: a free trial, Enterprise or Enterprise Plus instance.
--
-- Modeled on the production Data Commons Spanner schema (Node / Edge /
-- Observation + a DCGraph property graph). Public Data Commons entities,
-- OpenFEMA disaster declarations, and private agency entities live in the SAME
-- Node and Edge tables (Spanner allows only one node table and one edge table
-- when dynamic labels are used), so the result is one unified knowledge graph.
-- Rows are told apart by `label` and `provenance`.
--
-- Statements are separated by semicolons. Lines starting with "--" are comments
-- and are stripped by loader/load_spanner.py before the DDL is applied.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Graph input tables
-- -----------------------------------------------------------------------------

CREATE TABLE Node (
  subject_id       STRING(1024) NOT NULL, -- DCID (e.g. geoId/39049), disaster (fema/DR-4834), hub, team
  label            STRING(64)   NOT NULL, -- lowercase: continent, country, censusregion, censusdivision,
                                          -- state, county, statisticalvariable, disaster, hub, team
  name             STRING(MAX),           -- short name, e.g. "Franklin County", "DR-4834"
  display_name     STRING(MAX),           -- disambiguated name, e.g. "Franklin County, OH", "DR-4834 - Florida Hurricane Debby"
  provenance       STRING(64)   NOT NULL, -- 'datacommons.org' (public), 'openfema' (program data), 'beacon' (agency resources)
  state_code       STRING(8),             -- USPS code for states, counties, disasters, hubs, teams
  latitude         FLOAT64,
  longitude        FLOAT64,
  description      STRING(MAX),           -- statistical variables: what the variable measures; or disaster description
  incident_type    STRING(64),            -- disasters: 'Severe Storm', 'Flood', 'Hurricane', 'Tornado', 'Fire', etc.
  declaration_date DATE,                  -- disasters: date declared
  fy_declared      INT64,                 -- disasters: fiscal year declared
  hub_region       STRING(64),            -- hubs & teams: e.g. 'Southeast', 'Midwest', 'Gulf Coast'
  capacity         INT64,                 -- teams: daily intake registration capacity
  CONSTRAINT node_label_lowercase CHECK (label = LOWER(label)),
) PRIMARY KEY (subject_id);

CREATE TABLE Edge (
  subject_id STRING(1024) NOT NULL,       -- source node
  predicate  STRING(64)   NOT NULL,       -- lowercase: containedinplace, affectedplace, locatedin, covers, serves
  object_id  STRING(1024) NOT NULL,       -- destination node
  provenance STRING(64)   NOT NULL,       -- 'datacommons.org', 'openfema', 'beacon'
  CONSTRAINT edge_predicate_lowercase CHECK (predicate = LOWER(predicate)),
) PRIMARY KEY (subject_id, predicate, object_id, provenance),
  INTERLEAVE IN PARENT Node ON DELETE CASCADE;

-- -----------------------------------------------------------------------------
-- Public statistics (Data Commons shape: one row per place x variable x date)
-- -----------------------------------------------------------------------------

CREATE TABLE Observation (
  observation_about  STRING(1024) NOT NULL,  -- place DCID (Node.subject_id)
  variable_measured  STRING(1024) NOT NULL,  -- statistical variable DCID (Node.subject_id)
  observation_date   STRING(16)   NOT NULL,  -- as published: 'YYYY' or 'YYYY-MM'
  value              FLOAT64      NOT NULL,
  measurement_method STRING(128),
  observation_period STRING(16),
  unit               STRING(128),
  provenance_id      STRING(256),
  provenance_url     STRING(MAX),
  CONSTRAINT FK_Observation_Place FOREIGN KEY (observation_about) REFERENCES Node (subject_id),
  CONSTRAINT FK_Observation_Variable FOREIGN KEY (variable_measured) REFERENCES Node (subject_id),
) PRIMARY KEY (observation_about, variable_measured, observation_date);

-- Latest public stats per county, derived from Observation at load time.
CREATE TABLE CountyProfile (
  county_id                        STRING(1024) NOT NULL,
  county_name                      STRING(MAX),   -- e.g. "Franklin County, OH"
  state_id                         STRING(1024),
  state_name                       STRING(MAX),
  state_code                       STRING(8),
  population                       INT64,         -- Census PEP / ACS
  population_year                  INT64,
  population_change_5yr_pct        FLOAT64,
  households                       INT64,         -- ACS 5-year
  no_internet_households           INT64,         -- ACS 5-year (Count_Household_NoInternetAccess)
  no_internet_pct                  FLOAT64,       -- share of households without internet (0-100)
  age_65_plus                      INT64,         -- ACS 5-year (Count_Person_65OrMoreYears)
  age_65_plus_pct                  FLOAT64,       -- share of population 65+ (0-100)
  disability_count                 INT64,         -- ACS 5-year (Count_Person_WithDisability)
  disability_pct                   FLOAT64,       -- share of population with disability (0-100)
  poverty_count                    INT64,         -- ACS 5-year (Count_Person_BelowPovertyLevelInThePast12Months)
  poverty_pct                      FLOAT64,       -- poverty rate (0-100)
  nri_risk_score                   FLOAT64,       -- FEMA National Risk Index composite score
  nri_social_vulnerability_score   FLOAT64,       -- FEMA NRI Social Vulnerability score
  nri_community_resilience_score   FLOAT64,       -- FEMA NRI Community Resilience score
  nri_expected_annual_loss_usd     FLOAT64,       -- FEMA NRI Expected Annual Loss
  nri_flood_risk_score             FLOAT64,       -- Riverine flooding risk score
  nri_hurricane_risk_score         FLOAT64,       -- Hurricane hazard risk score
  nri_wildfire_risk_score          FLOAT64,       -- Wildfire hazard risk score
  acs_year                         INT64,         -- ACS 5-year vintage
  CONSTRAINT FK_CountyProfile_County FOREIGN KEY (county_id) REFERENCES Node (subject_id),
) PRIMARY KEY (county_id);

CREATE TABLE StateProfile (
  state_id                         STRING(1024) NOT NULL,
  state_name                       STRING(MAX),
  state_code                       STRING(8),
  census_division                  STRING(MAX),
  population                       INT64,
  population_year                  INT64,
  population_change_5yr_pct        FLOAT64,
  households                       INT64,
  no_internet_households           INT64,
  no_internet_pct                  FLOAT64,
  age_65_plus                      INT64,
  age_65_plus_pct                  FLOAT64,
  disability_count                 INT64,
  disability_pct                   FLOAT64,
  poverty_count                    INT64,
  poverty_pct                      FLOAT64,
  acs_year                         INT64,
  CONSTRAINT FK_StateProfile_State FOREIGN KEY (state_id) REFERENCES Node (subject_id),
) PRIMARY KEY (state_id);

-- -----------------------------------------------------------------------------
-- Agency Program Data (OpenFEMA declarations & registrations)
-- -----------------------------------------------------------------------------

-- Per-county disaster designations with program flags.
CREATE TABLE DisasterDesignation (
  disaster_id        STRING(1024) NOT NULL,  -- Node.subject_id of disaster, e.g. fema/DR-4834
  county_id          STRING(1024) NOT NULL,  -- Node.subject_id of county, e.g. geoId/21013
  state_code         STRING(8)    NOT NULL,
  ihp_declared       BOOL         NOT NULL,  -- Individual and Households Program
  pa_declared        BOOL         NOT NULL,  -- Public Assistance
  hm_declared        BOOL         NOT NULL,  -- Hazard Mitigation
  declaration_date   DATE         NOT NULL,
  incident_type      STRING(64)   NOT NULL,
  CONSTRAINT FK_DD_Disaster FOREIGN KEY (disaster_id) REFERENCES Node (subject_id),
  CONSTRAINT FK_DD_County FOREIGN KEY (county_id) REFERENCES Node (subject_id),
) PRIMARY KEY (disaster_id, county_id);

-- Aggregated assistance registrations by disaster x county x channel.
CREATE TABLE Registration (
  disaster_id                 STRING(1024) NOT NULL,
  county_id                   STRING(1024) NOT NULL,
  state_code                  STRING(8)    NOT NULL,
  total_valid_registrations   INT64        NOT NULL,
  web_registrations           INT64        NOT NULL,
  call_center_registrations   INT64        NOT NULL,
  mobile_registrations        INT64        NOT NULL,
  web_share_pct               FLOAT64      NOT NULL,
  call_center_share_pct       FLOAT64      NOT NULL,
  mobile_share_pct            FLOAT64      NOT NULL,
  CONSTRAINT FK_Reg_Disaster FOREIGN KEY (disaster_id) REFERENCES Node (subject_id),
  CONSTRAINT FK_Reg_County FOREIGN KEY (county_id) REFERENCES Node (subject_id),
) PRIMARY KEY (disaster_id, county_id);

-- -----------------------------------------------------------------------------
-- System of Action: Deployment Plan (written by the agent)
-- -----------------------------------------------------------------------------

CREATE TABLE DeploymentPlan (
  county_id          STRING(1024) NOT NULL,
  action             STRING(64)   NOT NULL,  -- 'Deploy Mobile Team', 'Establish Recovery Center'
  assigned_team_id   STRING(1024),           -- e.g. beacon/team/04
  priority_tier      STRING(32)   NOT NULL,  -- 'Tier 1 - Immediate', 'Tier 2 - Secondary'
  rationale          STRING(MAX),
  added_by           STRING(256),
  added_at           TIMESTAMP    NOT NULL OPTIONS (allow_commit_timestamp = true),
  status             STRING(32)   NOT NULL,  -- 'Proposed', 'Approved', 'Dispatched'
  CONSTRAINT FK_Plan_County FOREIGN KEY (county_id) REFERENCES Node (subject_id),
) PRIMARY KEY (county_id);

-- -----------------------------------------------------------------------------
-- Indexes
-- -----------------------------------------------------------------------------

CREATE INDEX NodeByLabel ON Node (label) STORING (name, display_name, state_code);

CREATE INDEX EdgeByObject ON Edge (object_id, predicate, subject_id, provenance), INTERLEAVE IN Node;

CREATE INDEX ObservationByVariableDate ON Observation (variable_measured, observation_date) STORING (value);

CREATE INDEX DesignationByCounty ON DisasterDesignation (county_id, declaration_date DESC);

CREATE INDEX RegistrationByCounty ON Registration (county_id);

-- -----------------------------------------------------------------------------
-- Friendly views (used by Conversational Analytics data agent and ad-hoc SQL)
-- -----------------------------------------------------------------------------

CREATE VIEW CountyReadiness SQL SECURITY INVOKER AS
SELECT
  cp.county_id                      AS county_id,
  cp.county_name                    AS county_name,
  cp.state_code                     AS state_code,
  cp.population                     AS population,
  cp.households                     AS households,
  cp.no_internet_pct                AS no_internet_pct,
  cp.age_65_plus_pct                AS age_65_plus_pct,
  cp.disability_pct                 AS disability_pct,
  cp.poverty_pct                    AS poverty_pct,
  cp.nri_risk_score                 AS nri_risk_score,
  cp.nri_social_vulnerability_score AS social_vulnerability_score,
  cp.nri_community_resilience_score AS community_resilience_score,
  COALESCE(dh.disaster_count, 0)    AS disasters_since_2023,
  COALESCE(dh.ihp_disaster_count, 0) AS ihp_disasters_since_2023,
  COALESCE(rg.total_registrations, 0) AS total_registrations,
  ROUND(100 * SAFE_DIVIDE(rg.web_registrations, rg.total_registrations), 1) AS web_registration_pct,
  ROUND(100 * SAFE_DIVIDE(rg.call_center_registrations, rg.total_registrations), 1) AS call_center_registration_pct,
  COALESCE(tc.covered_by_team, FALSE) AS has_team_coverage,
  tc.team_count                     AS assigned_team_count
FROM CountyProfile AS cp
LEFT JOIN (
  SELECT
    dd.county_id,
    COUNT(DISTINCT dd.disaster_id) AS disaster_count,
    COUNTIF(dd.ihp_declared) AS ihp_disaster_count
  FROM DisasterDesignation AS dd
  GROUP BY dd.county_id
) AS dh ON dh.county_id = cp.county_id
LEFT JOIN (
  SELECT
    r.county_id,
    SUM(r.total_valid_registrations) AS total_registrations,
    SUM(r.web_registrations) AS web_registrations,
    SUM(r.call_center_registrations) AS call_center_registrations
  FROM Registration AS r
  GROUP BY r.county_id
) AS rg ON rg.county_id = cp.county_id
LEFT JOIN (
  SELECT
    e.object_id AS county_id,
    TRUE AS covered_by_team,
    COUNT(DISTINCT e.subject_id) AS team_count
  FROM Edge AS e
  WHERE e.predicate = 'covers' AND e.provenance = 'beacon'
  GROUP BY e.object_id
) AS tc ON tc.county_id = cp.county_id;

CREATE VIEW DisasterSummary SQL SECURITY INVOKER AS
SELECT
  n.subject_id                AS disaster_id,
  n.name                      AS disaster_number,
  n.display_name              AS title,
  n.incident_type             AS incident_type,
  n.declaration_date          AS declaration_date,
  n.fy_declared               AS fiscal_year,
  n.state_code                AS state_code,
  COUNT(DISTINCT dd.county_id) AS designated_counties,
  COUNTIF(dd.ihp_declared)    AS ihp_counties,
  COALESCE(SUM(r.total_valid_registrations), 0) AS total_registrations,
  COALESCE(SUM(r.web_registrations), 0) AS web_registrations,
  COALESCE(SUM(r.call_center_registrations), 0) AS call_center_registrations,
  COALESCE(SUM(r.mobile_registrations), 0) AS mobile_registrations,
  ROUND(100 * SAFE_DIVIDE(SUM(r.web_registrations), SUM(r.total_valid_registrations)), 1) AS web_share_pct
FROM Node AS n
LEFT JOIN DisasterDesignation AS dd ON dd.disaster_id = n.subject_id
LEFT JOIN Registration AS r ON r.disaster_id = n.subject_id AND r.county_id = dd.county_id
WHERE n.label = 'disaster'
GROUP BY n.subject_id, n.name, n.display_name, n.incident_type, n.declaration_date, n.fy_declared, n.state_code;

-- -----------------------------------------------------------------------------
-- The unified property graph
-- -----------------------------------------------------------------------------
CREATE PROPERTY GRAPH DCGraph
  NODE TABLES (
    Node
      LABEL Entity
      DYNAMIC LABEL (label)
  )
  EDGE TABLES (
    Edge
      SOURCE KEY (subject_id) REFERENCES Node (subject_id)
      DESTINATION KEY (object_id) REFERENCES Node (subject_id)
      DYNAMIC LABEL (predicate)
  );
