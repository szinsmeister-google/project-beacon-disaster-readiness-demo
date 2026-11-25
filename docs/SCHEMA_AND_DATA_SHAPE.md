# Ground-Truth Schema Catalog & Verified Proof Ledger

## 1. Cloud Spanner / Spanner Omni Schema (`readiness_dcgraph` · `GRAPH DCGraph`)

| Object | Kind | Primary Key | Description |
| --- | --- | --- | --- |
| `Node` | Dynamic-Label Node Table | `subject_id` | Unified Data Commons (`continent`, `country`, `censusregion`, `censusdivision`, `state`, `county`), OpenFEMA (`disaster`), and agency (`hub`, `team`, `program`, `agency`) nodes |
| `Edge` | Dynamic-Label Edge Table | `(subject_id, predicate, object_id, provenance)` | Interleaved in `Node`; predicates: `containedinplace`, `borders`, `affectedplace`, `covers`, `recommended_for`, `dispatchedfrom`, `funds_hub`, `leads`, `governedby` |
| `Observation` | Statistical Fact Table | `(observation_about, variable_measured, observation_date)` | Data Commons time-series observations (U.S. Census ACS, FEMA NRI) |
| `CountyProfile` | Analytical Snapshot | `county_id` | 3,144 U.S. counties with population, `no_internet_pct`, `no_vehicle_pct`, `age_65_plus_pct`, `disability_pct`, `poverty_pct`, and FEMA NRI scores |
| `DisasterDesignation` | OpenFEMA Declarations | `(disaster_id, county_id)` | Major disaster declarations with `ihp_declared`, `pa_declared`, `hm_declared` |
| `Registration` | OpenFEMA Intake | `(disaster_id, county_id)` | Registration counts and channel shares (`web_share_pct`, `call_center_share_pct`, `mobile_share_pct`) |
| `DeploymentPlan` | System-of-Action Table | `county_id` | Live transactional Mobile DRC dispatch commitments written from Looker or Gemini |
| `CountyReadiness` | SQL View | `county_id` | Joins `CountyProfile`, `DisasterDesignation`, `Registration`, and `Edge` coverage flags |
| `KnowledgeCatalogGovernance` | Policy Audit Table | `rule_id` | 16 governed federal metric contracts mapping Glossary Terms <-> Spanner Columns <-> Data Commons DCIDs |

## 2. BigQuery Borderless Lakehouse (`beacon_disaster_readiness`)

- **BigLake Managed Apache Iceberg (`table_format = 'ICEBERG'`):**
  - `noaa_hazard_iceberg` — Multi-hazard severity, storm surge, power & cell-tower outage percentages
  - `fema_field_assessments_iceberg` — Field reconnaissance damage assessments & SitRep URI bindings
- **BigLake Object Table:**
  - `fema_field_sitrep_objects` — Unstructured PDF metadata view over `gs://<GCS_LAKEHOUSE_BUCKET>/field_sitreps/*.pdf`
- **Unified Federation View:**
  - `v_borderless_lakehouse_dispatch` — Joins `county_readiness`, `noaa_hazard_iceberg`, `fema_field_assessments_iceberg`, and `fema_field_sitrep_objects` in ~1.2 seconds.

## 3. Knowledge Catalog Governance (`beacon-disaster-readiness-glossary`)

- **4 Policy Categories & 12 Governed Terms**, anchored by:
  - `Social Vulnerability Score (SVI Tier-1 >= 75.0)` — FEMA NRI & CDC/ATSDR
  - `Household Digital Divide (No Internet >= 18.0%)` — U.S. Census ACS & FCC/NTIA
  - `Transit-Isolated Households (No Vehicle >= 10.0%)` — U.S. Census ACS & DOT/FEMA
  - `Federal Deployment Plan (Spanner System of Action)` — FEMA Field Operations
