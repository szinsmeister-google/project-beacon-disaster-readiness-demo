/**
 * @title U.S. Public Sector · Beacon Disaster Readiness & Policy Intelligence (Data Commons x Cloud Spanner Graph)
 * @description Google Data Commons (country/USA · U.S. Census ACS) x Cloud Spanner Graph (beacon_dcgraph) executive policy application in authentic U.S. Flag National Palette (Old Glory Red #B31942 / Pantone Red #EF3340, Pure White #FFFFFF, and Federal Navy #0A3161) with ThoughtSpot-style KPI Sparklines, live FEMA BRIC & Mobile DRC Grant Simulator, and interactive fleet dispatch controls.
 * @created 2026-09-28T01:20:00Z
 * @updated 2026-09-28T01:25:00Z
 */

import { DataApp, html, nothing } from '/runtime/data-app.js';

export const elementName = 'beacon-disaster-readiness';

const US_DISASTER_COUNTIES = [
  {
    "county_id": "geoId/02050",
    "county_name": "Bethel Census Area, AK",
    "state_name": "Alaska",
    "state_code": "AK",
    "fema_region": "Region X (Pacific NW)",
    "latitude": 60.75,
    "longitude": -160.152625,
    "population": 18391,
    "households": 4828,
    "median_household_income_usd": 73996,
    "no_internet_pct": 12.7,
    "no_vehicle_pct": 57.7,
    "age_65_plus_pct": 8.4,
    "disability_pct": 11.8,
    "poverty_pct": 25.2,
    "nri_risk_score": 44.3,
    "social_vulnerability_score": 100.0,
    "community_resilience_score": 39.1,
    "flood_risk_score": 9.6,
    "hurricane_risk_score": 48.0,
    "wildfire_risk_score": 83.8,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 2803,
    "web_registration_pct": 7.0,
    "call_center_registration_pct": 92.9,
    "web_registrations": 196,
    "call_center_registrations": 2607,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/21159",
    "county_name": "Martin County, KY",
    "state_name": "Kentucky",
    "state_code": "KY",
    "fema_region": "Region IV (Southeast)",
    "latitude": 37.796774,
    "longitude": -82.506623,
    "population": 10697,
    "households": 3854,
    "median_household_income_usd": 37042,
    "no_internet_pct": 11.5,
    "no_vehicle_pct": 8.7,
    "age_65_plus_pct": 18.4,
    "disability_pct": 28.8,
    "poverty_pct": 29.9,
    "nri_risk_score": 49.9,
    "social_vulnerability_score": 99.9,
    "community_resilience_score": 3.5,
    "flood_risk_score": 71.2,
    "hurricane_risk_score": 40.3,
    "wildfire_risk_score": 77.2,
    "disasters_since_2023": 3,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 475,
    "web_registration_pct": 29.5,
    "call_center_registration_pct": 67.4,
    "web_registrations": 140,
    "call_center_registrations": 335,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/36005",
    "county_name": "The Bronx, NY",
    "state_name": "New York",
    "state_code": "NY",
    "fema_region": "Region II (NY/NJ)",
    "latitude": 40.84676,
    "longitude": -73.852939,
    "population": 1406332,
    "households": 534100,
    "median_household_income_usd": 48676,
    "no_internet_pct": 9.6,
    "no_vehicle_pct": 61.1,
    "age_65_plus_pct": 14.4,
    "disability_pct": 17.5,
    "poverty_pct": 27.2,
    "nri_risk_score": 98.3,
    "social_vulnerability_score": 99.7,
    "community_resilience_score": 6.0,
    "flood_risk_score": 98.5,
    "hurricane_risk_score": 95.3,
    "wildfire_risk_score": 2.4,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/28157",
    "county_name": "Wilkinson County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 31.16,
    "longitude": -91.32,
    "population": 7582,
    "households": 3185,
    "median_household_income_usd": 35311,
    "no_internet_pct": 19.2,
    "no_vehicle_pct": 7.7,
    "age_65_plus_pct": 21.2,
    "disability_pct": 18.6,
    "poverty_pct": 25.7,
    "nri_risk_score": 33.5,
    "social_vulnerability_score": 99.6,
    "community_resilience_score": 21.5,
    "flood_risk_score": 33.8,
    "hurricane_risk_score": 80.9,
    "wildfire_risk_score": 37.5,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 1451,
    "web_registration_pct": 29.9,
    "call_center_registration_pct": 70.1,
    "web_registrations": 434,
    "call_center_registrations": 1017,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/39075",
    "county_name": "Holmes County, OH",
    "state_name": "Ohio",
    "state_code": "OH",
    "fema_region": "Region V (Midwest)",
    "latitude": 40.56,
    "longitude": -81.93,
    "population": 44970,
    "households": 13395,
    "median_household_income_usd": 76140,
    "no_internet_pct": 34.9,
    "no_vehicle_pct": 30.9,
    "age_65_plus_pct": 14.3,
    "disability_pct": 7.8,
    "poverty_pct": 9.0,
    "nri_risk_score": 60.4,
    "social_vulnerability_score": 99.5,
    "community_resilience_score": 3.9,
    "flood_risk_score": 71.2,
    "hurricane_risk_score": 52.0,
    "wildfire_risk_score": 46.9,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 2,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/05077",
    "county_name": "Lee County, AR",
    "state_name": "Arkansas",
    "state_code": "AR",
    "fema_region": "Region VI (South Central)",
    "latitude": 34.775555555556,
    "longitude": -90.774722222222,
    "population": 8029,
    "households": 2690,
    "median_household_income_usd": 34375,
    "no_internet_pct": 17.1,
    "no_vehicle_pct": 16.7,
    "age_65_plus_pct": 21.3,
    "disability_pct": 23.8,
    "poverty_pct": 33.2,
    "nri_risk_score": 40.4,
    "social_vulnerability_score": 99.4,
    "community_resilience_score": 17.4,
    "flood_risk_score": 21.2,
    "hurricane_risk_score": 50.7,
    "wildfire_risk_score": 7.3,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/01119",
    "county_name": "Sumter County, AL",
    "state_name": "Alabama",
    "state_code": "AL",
    "fema_region": "Region IV (Southeast)",
    "latitude": 32.591666666667,
    "longitude": -88.200057,
    "population": 11588,
    "households": 4823,
    "median_household_income_usd": 33310,
    "no_internet_pct": 20.1,
    "no_vehicle_pct": 9.5,
    "age_65_plus_pct": 20.3,
    "disability_pct": 21.5,
    "poverty_pct": 22.2,
    "nri_risk_score": 53.0,
    "social_vulnerability_score": 99.3,
    "community_resilience_score": 14.8,
    "flood_risk_score": 54.8,
    "hurricane_risk_score": 76.3,
    "wildfire_risk_score": 34.4,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 8.1,
    "call_center_registration_pct": 82.6,
    "web_registrations": 140,
    "call_center_registrations": 148,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/22035",
    "county_name": "East Carroll Parish, LA",
    "state_name": "Louisiana",
    "state_code": "LA",
    "fema_region": "Region VI (South Central)",
    "latitude": 32.73,
    "longitude": -91.234141,
    "population": 6760,
    "households": 2617,
    "median_household_income_usd": 33341,
    "no_internet_pct": 17.7,
    "no_vehicle_pct": 9.2,
    "age_65_plus_pct": 16.4,
    "disability_pct": 16.5,
    "poverty_pct": 27.6,
    "nri_risk_score": 21.6,
    "social_vulnerability_score": 99.2,
    "community_resilience_score": 35.6,
    "flood_risk_score": 8.7,
    "hurricane_risk_score": 66.8,
    "wildfire_risk_score": 6.9,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/22065",
    "county_name": "Madison Parish, LA",
    "state_name": "Louisiana",
    "state_code": "LA",
    "fema_region": "Region VI (South Central)",
    "latitude": 32.346878,
    "longitude": -91.231932,
    "population": 8844,
    "households": 3053,
    "median_household_income_usd": 35456,
    "no_internet_pct": 16.0,
    "no_vehicle_pct": 14.0,
    "age_65_plus_pct": 18.8,
    "disability_pct": 21.3,
    "poverty_pct": 32.4,
    "nri_risk_score": 32.4,
    "social_vulnerability_score": 99.1,
    "community_resilience_score": 34.6,
    "flood_risk_score": 18.0,
    "hurricane_risk_score": 69.6,
    "wildfire_risk_score": 4.9,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/28151",
    "county_name": "Washington County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 33.273174,
    "longitude": -90.944446,
    "population": 40446,
    "households": 17113,
    "median_household_income_usd": 42165,
    "no_internet_pct": 17.9,
    "no_vehicle_pct": 11.9,
    "age_65_plus_pct": 18.8,
    "disability_pct": 24.3,
    "poverty_pct": 27.4,
    "nri_risk_score": 83.0,
    "social_vulnerability_score": 99.0,
    "community_resilience_score": 44.6,
    "flood_risk_score": 81.2,
    "hurricane_risk_score": 72.3,
    "wildfire_risk_score": 26.1,
    "disasters_since_2023": 3,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 5558,
    "web_registration_pct": 64.8,
    "call_center_registration_pct": 35.2,
    "web_registrations": 3602,
    "call_center_registrations": 1956,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/05123",
    "county_name": "St. Francis County, AR",
    "state_name": "Arkansas",
    "state_code": "AR",
    "fema_region": "Region VI (South Central)",
    "latitude": 35.022838,
    "longitude": -90.704166666667,
    "population": 21800,
    "households": 7783,
    "median_household_income_usd": 42574,
    "no_internet_pct": 15.0,
    "no_vehicle_pct": 13.3,
    "age_65_plus_pct": 18.4,
    "disability_pct": 21.3,
    "poverty_pct": 25.5,
    "nri_risk_score": 74.8,
    "social_vulnerability_score": 99.0,
    "community_resilience_score": 11.6,
    "flood_risk_score": 41.2,
    "hurricane_risk_score": 51.2,
    "wildfire_risk_score": 27.1,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 943,
    "web_registration_pct": 53.9,
    "call_center_registration_pct": 46.1,
    "web_registrations": 508,
    "call_center_registrations": 435,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/01105",
    "county_name": "Perry County, AL",
    "state_name": "Alabama",
    "state_code": "AL",
    "fema_region": "Region IV (Southeast)",
    "latitude": 32.635833333333,
    "longitude": -87.291944444444,
    "population": 7425,
    "households": 3440,
    "median_household_income_usd": 37654,
    "no_internet_pct": 22.4,
    "no_vehicle_pct": 8.0,
    "age_65_plus_pct": 23.4,
    "disability_pct": 24.4,
    "poverty_pct": 30.5,
    "nri_risk_score": 18.8,
    "social_vulnerability_score": 99.0,
    "community_resilience_score": 30.8,
    "flood_risk_score": 22.5,
    "hurricane_risk_score": 69.3,
    "wildfire_risk_score": 23.2,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/45011",
    "county_name": "Barnwell County, SC",
    "state_name": "South Carolina",
    "state_code": "SC",
    "fema_region": "Region IV (Southeast)",
    "latitude": 33.260552,
    "longitude": -81.434228,
    "population": 20653,
    "households": 8116,
    "median_household_income_usd": 46626,
    "no_internet_pct": 22.2,
    "no_vehicle_pct": 10.6,
    "age_65_plus_pct": 19.0,
    "disability_pct": 19.8,
    "poverty_pct": 24.3,
    "nri_risk_score": 45.8,
    "social_vulnerability_score": 98.9,
    "community_resilience_score": 19.1,
    "flood_risk_score": 35.0,
    "hurricane_risk_score": 85.3,
    "wildfire_risk_score": 59.9,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 3377,
    "web_registration_pct": 72.2,
    "call_center_registration_pct": 27.6,
    "web_registrations": 2438,
    "call_center_registrations": 939,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/28051",
    "county_name": "Holmes County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 33.12,
    "longitude": -90.09,
    "population": 15465,
    "households": 6157,
    "median_household_income_usd": 32538,
    "no_internet_pct": 24.8,
    "no_vehicle_pct": 15.9,
    "age_65_plus_pct": 17.6,
    "disability_pct": 30.9,
    "poverty_pct": 35.9,
    "nri_risk_score": 49.8,
    "social_vulnerability_score": 98.8,
    "community_resilience_score": 10.7,
    "flood_risk_score": 32.2,
    "hurricane_risk_score": 66.5,
    "wildfire_risk_score": 57.5,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 4302,
    "web_registration_pct": 45.7,
    "call_center_registration_pct": 54.3,
    "web_registrations": 1966,
    "call_center_registrations": 2336,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/28053",
    "county_name": "Humphreys County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 33.13,
    "longitude": -90.52,
    "population": 7001,
    "households": 2900,
    "median_household_income_usd": 33731,
    "no_internet_pct": 20.0,
    "no_vehicle_pct": 13.0,
    "age_65_plus_pct": 20.0,
    "disability_pct": 27.4,
    "poverty_pct": 28.3,
    "nri_risk_score": 27.9,
    "social_vulnerability_score": 98.8,
    "community_resilience_score": 34.6,
    "flood_risk_score": 22.5,
    "hurricane_risk_score": 66.5,
    "wildfire_risk_score": 12.4,
    "disasters_since_2023": 5,
    "ihp_disasters_since_2023": 3,
    "total_registrations": 4451,
    "web_registration_pct": 38.0,
    "call_center_registration_pct": 55.7,
    "web_registrations": 1691,
    "call_center_registrations": 2760,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/28011",
    "county_name": "Bolivar County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 33.79,
    "longitude": -90.88,
    "population": 28262,
    "households": 11915,
    "median_household_income_usd": 39585,
    "no_internet_pct": 16.8,
    "no_vehicle_pct": 10.1,
    "age_65_plus_pct": 17.9,
    "disability_pct": 19.3,
    "poverty_pct": 31.8,
    "nri_risk_score": 76.8,
    "social_vulnerability_score": 98.7,
    "community_resilience_score": 45.8,
    "flood_risk_score": 76.9,
    "hurricane_risk_score": 66.4,
    "wildfire_risk_score": 17.9,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 3378,
    "web_registration_pct": 58.1,
    "call_center_registration_pct": 41.9,
    "web_registrations": 1963,
    "call_center_registrations": 1415,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/28119",
    "county_name": "Quitman County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 34.25,
    "longitude": -90.29,
    "population": 5364,
    "households": 2643,
    "median_household_income_usd": 32412,
    "no_internet_pct": 31.1,
    "no_vehicle_pct": 10.9,
    "age_65_plus_pct": 19.8,
    "disability_pct": 19.2,
    "poverty_pct": 31.1,
    "nri_risk_score": 18.5,
    "social_vulnerability_score": 98.6,
    "community_resilience_score": 26.1,
    "flood_risk_score": 15.8,
    "hurricane_risk_score": 55.8,
    "wildfire_risk_score": 28.1,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 1041,
    "web_registration_pct": 53.6,
    "call_center_registration_pct": 46.4,
    "web_registrations": 558,
    "call_center_registrations": 483,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/28065",
    "county_name": "Jefferson Davis County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 31.56,
    "longitude": -89.82,
    "population": 10941,
    "households": 4453,
    "median_household_income_usd": 38548,
    "no_internet_pct": 17.1,
    "no_vehicle_pct": 6.1,
    "age_65_plus_pct": 25.0,
    "disability_pct": 23.2,
    "poverty_pct": 28.9,
    "nri_risk_score": 23.1,
    "social_vulnerability_score": 98.5,
    "community_resilience_score": 23.2,
    "flood_risk_score": 23.8,
    "hurricane_risk_score": 78.4,
    "wildfire_risk_score": 56.7,
    "disasters_since_2023": 3,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 1565,
    "web_registration_pct": 38.0,
    "call_center_registration_pct": 62.0,
    "web_registrations": 595,
    "call_center_registrations": 970,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/48255",
    "county_name": "Karnes County, TX",
    "state_name": "Texas",
    "state_code": "TX",
    "fema_region": "Region VI (South Central)",
    "latitude": 28.908996,
    "longitude": -97.852205,
    "population": 15018,
    "households": 4730,
    "median_household_income_usd": 60214,
    "no_internet_pct": 24.0,
    "no_vehicle_pct": 9.8,
    "age_65_plus_pct": 15.1,
    "disability_pct": 15.9,
    "poverty_pct": 14.8,
    "nri_risk_score": 58.4,
    "social_vulnerability_score": 98.5,
    "community_resilience_score": 30.6,
    "flood_risk_score": 63.8,
    "hurricane_risk_score": 85.2,
    "wildfire_risk_score": 59.2,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/13141",
    "county_name": "Hancock County, GA",
    "state_name": "Georgia",
    "state_code": "GA",
    "fema_region": "Region IV (Southeast)",
    "latitude": 33.26922,
    "longitude": -83.0,
    "population": 8682,
    "households": 2922,
    "median_household_income_usd": 40082,
    "no_internet_pct": 26.5,
    "no_vehicle_pct": 8.4,
    "age_65_plus_pct": 25.1,
    "disability_pct": 18.5,
    "poverty_pct": 23.9,
    "nri_risk_score": 11.9,
    "social_vulnerability_score": 98.3,
    "community_resilience_score": 6.4,
    "flood_risk_score": 26.9,
    "hurricane_risk_score": 62.1,
    "wildfire_risk_score": 54.1,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 1024,
    "web_registration_pct": 70.4,
    "call_center_registration_pct": 29.3,
    "web_registrations": 721,
    "call_center_registrations": 303,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/28083",
    "county_name": "Leflore County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 33.54979,
    "longitude": -90.294934,
    "population": 25686,
    "households": 10203,
    "median_household_income_usd": 35277,
    "no_internet_pct": 22.1,
    "no_vehicle_pct": 14.7,
    "age_65_plus_pct": 16.0,
    "disability_pct": 20.8,
    "poverty_pct": 31.7,
    "nri_risk_score": 73.5,
    "social_vulnerability_score": 98.2,
    "community_resilience_score": 57.5,
    "flood_risk_score": 70.0,
    "hurricane_risk_score": 71.7,
    "wildfire_risk_score": 22.5,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 2,
    "total_registrations": 5272,
    "web_registration_pct": 53.4,
    "call_center_registration_pct": 46.6,
    "web_registrations": 2815,
    "call_center_registrations": 2457,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/01063",
    "county_name": "Greene County, AL",
    "state_name": "Alabama",
    "state_code": "AL",
    "fema_region": "Region IV (Southeast)",
    "latitude": 32.844497,
    "longitude": -87.950833333333,
    "population": 7067,
    "households": 3225,
    "median_household_income_usd": 29200,
    "no_internet_pct": 25.8,
    "no_vehicle_pct": 13.3,
    "age_65_plus_pct": 26.4,
    "disability_pct": 26.2,
    "poverty_pct": 41.7,
    "nri_risk_score": 29.3,
    "social_vulnerability_score": 98.1,
    "community_resilience_score": 21.1,
    "flood_risk_score": 32.8,
    "hurricane_risk_score": 63.0,
    "wildfire_risk_score": 14.2,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 255,
    "web_registration_pct": 13.3,
    "call_center_registration_pct": 71.4,
    "web_registrations": 140,
    "call_center_registrations": 221,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/28005",
    "county_name": "Amite County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 31.17,
    "longitude": -90.795542,
    "population": 12487,
    "households": 5850,
    "median_household_income_usd": 37222,
    "no_internet_pct": 30.0,
    "no_vehicle_pct": 5.8,
    "age_65_plus_pct": 26.4,
    "disability_pct": 24.1,
    "poverty_pct": 27.6,
    "nri_risk_score": 48.2,
    "social_vulnerability_score": 98.1,
    "community_resilience_score": 14.8,
    "flood_risk_score": 46.3,
    "hurricane_risk_score": 86.3,
    "wildfire_risk_score": 61.2,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/05041",
    "county_name": "Desha County, AR",
    "state_name": "Arkansas",
    "state_code": "AR",
    "fema_region": "Region VI (South Central)",
    "latitude": 33.757777777778,
    "longitude": -91.244103,
    "population": 9984,
    "households": 4610,
    "median_household_income_usd": 37662,
    "no_internet_pct": 19.5,
    "no_vehicle_pct": 14.6,
    "age_65_plus_pct": 21.7,
    "disability_pct": 23.8,
    "poverty_pct": 30.3,
    "nri_risk_score": 32.9,
    "social_vulnerability_score": 98.0,
    "community_resilience_score": 53.2,
    "flood_risk_score": 33.4,
    "hurricane_risk_score": 63.3,
    "wildfire_risk_score": 3.2,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 38.0,
    "call_center_registration_pct": 62.0,
    "web_registrations": 140,
    "call_center_registrations": 114,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/12065",
    "county_name": "Jefferson County, FL",
    "state_name": "Florida",
    "state_code": "FL",
    "fema_region": "Region IV (Southeast)",
    "latitude": 30.396898,
    "longitude": -83.9,
    "population": 16007,
    "households": 5751,
    "median_household_income_usd": 61212,
    "no_internet_pct": 20.7,
    "no_vehicle_pct": 11.1,
    "age_65_plus_pct": 23.1,
    "disability_pct": 18.5,
    "poverty_pct": 18.2,
    "nri_risk_score": 39.0,
    "social_vulnerability_score": 97.9,
    "community_resilience_score": 32.2,
    "flood_risk_score": 28.1,
    "hurricane_risk_score": 86.7,
    "wildfire_risk_score": 71.3,
    "disasters_since_2023": 4,
    "ihp_disasters_since_2023": 3,
    "total_registrations": 3283,
    "web_registration_pct": 48.8,
    "call_center_registration_pct": 38.3,
    "web_registrations": 1602,
    "call_center_registrations": 1681,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/22009",
    "county_name": "Avoyelles Parish, LA",
    "state_name": "Louisiana",
    "state_code": "LA",
    "fema_region": "Region VI (South Central)",
    "latitude": 31.07,
    "longitude": -91.983275,
    "population": 37941,
    "households": 14441,
    "median_household_income_usd": 39325,
    "no_internet_pct": 20.4,
    "no_vehicle_pct": 9.8,
    "age_65_plus_pct": 18.2,
    "disability_pct": 23.5,
    "poverty_pct": 26.6,
    "nri_risk_score": 73.0,
    "social_vulnerability_score": 97.9,
    "community_resilience_score": 63.1,
    "flood_risk_score": 44.5,
    "hurricane_risk_score": 90.0,
    "wildfire_risk_score": 49.3,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 2317,
    "web_registration_pct": 53.3,
    "call_center_registration_pct": 46.7,
    "web_registrations": 1235,
    "call_center_registrations": 1082,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/48123",
    "county_name": "DeWitt County, TX",
    "state_name": "Texas",
    "state_code": "TX",
    "fema_region": "Region VI (South Central)",
    "latitude": 29.08,
    "longitude": -97.36,
    "population": 20309,
    "households": 6921,
    "median_household_income_usd": 63730,
    "no_internet_pct": 18.2,
    "no_vehicle_pct": 6.7,
    "age_65_plus_pct": 20.0,
    "disability_pct": 13.7,
    "poverty_pct": 15.8,
    "nri_risk_score": 83.9,
    "social_vulnerability_score": 97.7,
    "community_resilience_score": 37.8,
    "flood_risk_score": 89.2,
    "hurricane_risk_score": 90.3,
    "wildfire_risk_score": 67.6,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/13301",
    "county_name": "Warren County, GA",
    "state_name": "Georgia",
    "state_code": "GA",
    "fema_region": "Region IV (Southeast)",
    "latitude": 33.408381,
    "longitude": -82.675685,
    "population": 5269,
    "households": 2097,
    "median_household_income_usd": 44289,
    "no_internet_pct": 30.9,
    "no_vehicle_pct": 7.6,
    "age_65_plus_pct": 22.9,
    "disability_pct": 13.9,
    "poverty_pct": 20.8,
    "nri_risk_score": 5.3,
    "social_vulnerability_score": 97.7,
    "community_resilience_score": 22.6,
    "flood_risk_score": 10.9,
    "hurricane_risk_score": 61.9,
    "wildfire_risk_score": 41.6,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 1664,
    "web_registration_pct": 63.8,
    "call_center_registration_pct": 36.2,
    "web_registrations": 1062,
    "call_center_registrations": 602,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/13065",
    "county_name": "Clinch County, GA",
    "state_name": "Georgia",
    "state_code": "GA",
    "fema_region": "Region IV (Southeast)",
    "latitude": 30.917653,
    "longitude": -82.7,
    "population": 6847,
    "households": 2428,
    "median_household_income_usd": 45847,
    "no_internet_pct": 20.9,
    "no_vehicle_pct": 14.6,
    "age_65_plus_pct": 17.6,
    "disability_pct": 18.8,
    "poverty_pct": 25.4,
    "nri_risk_score": 20.7,
    "social_vulnerability_score": 97.5,
    "community_resilience_score": 43.1,
    "flood_risk_score": 29.0,
    "hurricane_risk_score": 82.3,
    "wildfire_risk_score": 54.2,
    "disasters_since_2023": 3,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 2127,
    "web_registration_pct": 66.7,
    "call_center_registration_pct": 33.3,
    "web_registrations": 1419,
    "call_center_registrations": 708,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/51083",
    "county_name": "Halifax County, VA",
    "state_name": "Virginia",
    "state_code": "VA",
    "fema_region": "Region III (Mid-Atlantic)",
    "latitude": 36.766461,
    "longitude": -78.939614,
    "population": 33447,
    "households": 13613,
    "median_household_income_usd": 52013,
    "no_internet_pct": 26.0,
    "no_vehicle_pct": 7.5,
    "age_65_plus_pct": 25.8,
    "disability_pct": 19.8,
    "poverty_pct": 17.0,
    "nri_risk_score": 47.0,
    "social_vulnerability_score": 97.4,
    "community_resilience_score": 30.5,
    "flood_risk_score": 54.4,
    "hurricane_risk_score": 78.6,
    "wildfire_risk_score": 25.5,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/22117",
    "county_name": "Washington Parish, LA",
    "state_name": "Louisiana",
    "state_code": "LA",
    "fema_region": "Region VI (South Central)",
    "latitude": 30.85,
    "longitude": -90.04,
    "population": 44937,
    "households": 17716,
    "median_household_income_usd": 45380,
    "no_internet_pct": 22.5,
    "no_vehicle_pct": 11.5,
    "age_65_plus_pct": 19.3,
    "disability_pct": 24.4,
    "poverty_pct": 23.4,
    "nri_risk_score": 85.5,
    "social_vulnerability_score": 97.2,
    "community_resilience_score": 34.9,
    "flood_risk_score": 79.0,
    "hurricane_risk_score": 95.9,
    "wildfire_risk_score": 80.0,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 2,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/28113",
    "county_name": "Pike County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 31.177516,
    "longitude": -90.397725,
    "population": 38712,
    "households": 15007,
    "median_household_income_usd": 43814,
    "no_internet_pct": 17.5,
    "no_vehicle_pct": 5.8,
    "age_65_plus_pct": 18.3,
    "disability_pct": 19.6,
    "poverty_pct": 26.9,
    "nri_risk_score": 70.4,
    "social_vulnerability_score": 97.2,
    "community_resilience_score": 40.3,
    "flood_risk_score": 64.8,
    "hurricane_risk_score": 87.2,
    "wildfire_risk_score": 71.5,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 1152,
    "web_registration_pct": 59.1,
    "call_center_registration_pct": 40.9,
    "web_registrations": 681,
    "call_center_registrations": 471,
    "has_team_coverage": true,
    "assigned_team_count": 2,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/48427",
    "county_name": "Starr County, TX",
    "state_name": "Texas",
    "state_code": "TX",
    "fema_region": "Region VI (South Central)",
    "latitude": 26.530903,
    "longitude": -98.73,
    "population": 66319,
    "households": 19157,
    "median_household_income_usd": 37639,
    "no_internet_pct": 19.9,
    "no_vehicle_pct": 10.4,
    "age_65_plus_pct": 11.3,
    "disability_pct": 16.6,
    "poverty_pct": 33.1,
    "nri_risk_score": 84.8,
    "social_vulnerability_score": 97.0,
    "community_resilience_score": 0.3,
    "flood_risk_score": 72.4,
    "hurricane_risk_score": 78.8,
    "wildfire_risk_score": 84.9,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 700,
    "web_registration_pct": 17.6,
    "call_center_registration_pct": 82.4,
    "web_registrations": 140,
    "call_center_registrations": 577,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/22091",
    "county_name": "St. Helena Parish, LA",
    "state_name": "Louisiana",
    "state_code": "LA",
    "fema_region": "Region VI (South Central)",
    "latitude": 30.82,
    "longitude": -90.708307,
    "population": 10758,
    "households": 4176,
    "median_household_income_usd": 41934,
    "no_internet_pct": 29.1,
    "no_vehicle_pct": 10.4,
    "age_65_plus_pct": 21.6,
    "disability_pct": 33.3,
    "poverty_pct": 32.4,
    "nri_risk_score": 36.3,
    "social_vulnerability_score": 97.0,
    "community_resilience_score": 26.2,
    "flood_risk_score": 35.0,
    "hurricane_risk_score": 79.6,
    "wildfire_risk_score": 53.3,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 2,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/21121",
    "county_name": "Knox County, KY",
    "state_name": "Kentucky",
    "state_code": "KY",
    "fema_region": "Region IV (Southeast)",
    "latitude": 36.8885,
    "longitude": -83.85404,
    "population": 29532,
    "households": 11711,
    "median_household_income_usd": 32527,
    "no_internet_pct": 12.1,
    "no_vehicle_pct": 12.4,
    "age_65_plus_pct": 17.6,
    "disability_pct": 23.9,
    "poverty_pct": 36.4,
    "nri_risk_score": 74.7,
    "social_vulnerability_score": 96.7,
    "community_resilience_score": 15.8,
    "flood_risk_score": 71.7,
    "hurricane_risk_score": 39.1,
    "wildfire_risk_score": 84.7,
    "disasters_since_2023": 3,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 42.6,
    "call_center_registration_pct": 57.4,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/36047",
    "county_name": "Brooklyn, NY",
    "state_name": "New York",
    "state_code": "NY",
    "fema_region": "Region II (NY/NJ)",
    "latitude": 40.635045,
    "longitude": -73.94972,
    "population": 2653963,
    "households": 1009927,
    "median_household_income_usd": 80263,
    "no_internet_pct": 8.5,
    "no_vehicle_pct": 56.4,
    "age_65_plus_pct": 15.3,
    "disability_pct": 11.3,
    "poverty_pct": 18.8,
    "nri_risk_score": 99.3,
    "social_vulnerability_score": 96.5,
    "community_resilience_score": 12.1,
    "flood_risk_score": 99.4,
    "hurricane_risk_score": 97.4,
    "wildfire_risk_score": 38.5,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/28125",
    "county_name": "Sharkey County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 32.88,
    "longitude": -90.81,
    "population": 3097,
    "households": 1422,
    "median_household_income_usd": 40000,
    "no_internet_pct": 14.8,
    "no_vehicle_pct": 8.0,
    "age_65_plus_pct": 22.9,
    "disability_pct": 20.8,
    "poverty_pct": 37.6,
    "nri_risk_score": 15.8,
    "social_vulnerability_score": 96.4,
    "community_resilience_score": 41.7,
    "flood_risk_score": 12.2,
    "hurricane_risk_score": 63.8,
    "wildfire_risk_score": 2.0,
    "disasters_since_2023": 3,
    "ihp_disasters_since_2023": 2,
    "total_registrations": 2305,
    "web_registration_pct": 26.4,
    "call_center_registration_pct": 64.3,
    "web_registrations": 609,
    "call_center_registrations": 1696,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/36061",
    "county_name": "Manhattan, NY",
    "state_name": "New York",
    "state_code": "NY",
    "fema_region": "Region II (NY/NJ)",
    "latitude": 40.728333333333,
    "longitude": -73.970187,
    "population": 1664862,
    "households": 778281,
    "median_household_income_usd": 103931,
    "no_internet_pct": 5.5,
    "no_vehicle_pct": 78.0,
    "age_65_plus_pct": 17.8,
    "disability_pct": 11.6,
    "poverty_pct": 15.7,
    "nri_risk_score": 98.8,
    "social_vulnerability_score": 96.3,
    "community_resilience_score": 67.4,
    "flood_risk_score": 99.2,
    "hurricane_risk_score": 96.8,
    "wildfire_risk_score": 9.9,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/54047",
    "county_name": "McDowell County, WV",
    "state_name": "West Virginia",
    "state_code": "WV",
    "fema_region": "Region III (Mid-Atlantic)",
    "latitude": 37.37,
    "longitude": -81.65,
    "population": 16878,
    "households": 6467,
    "median_household_income_usd": 31559,
    "no_internet_pct": 12.8,
    "no_vehicle_pct": 10.7,
    "age_65_plus_pct": 23.2,
    "disability_pct": 27.9,
    "poverty_pct": 32.0,
    "nri_risk_score": 76.7,
    "social_vulnerability_score": 96.3,
    "community_resilience_score": 4.1,
    "flood_risk_score": 84.7,
    "hurricane_risk_score": 55.2,
    "wildfire_risk_score": 69.3,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 1914,
    "web_registration_pct": 27.8,
    "call_center_registration_pct": 67.5,
    "web_registrations": 532,
    "call_center_registrations": 1382,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/40107",
    "county_name": "Okfuskee County, OK",
    "state_name": "Oklahoma",
    "state_code": "OK",
    "fema_region": "Region VI (South Central)",
    "latitude": 35.466804,
    "longitude": -96.327762,
    "population": 11451,
    "households": 4009,
    "median_household_income_usd": 48363,
    "no_internet_pct": 16.2,
    "no_vehicle_pct": 8.4,
    "age_65_plus_pct": 17.9,
    "disability_pct": 18.1,
    "poverty_pct": 22.9,
    "nri_risk_score": 40.4,
    "social_vulnerability_score": 96.2,
    "community_resilience_score": 15.7,
    "flood_risk_score": 22.1,
    "hurricane_risk_score": 24.0,
    "wildfire_risk_score": 91.7,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 45.5,
    "call_center_registration_pct": 54.5,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/28043",
    "county_name": "Grenada County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 33.77,
    "longitude": -89.8,
    "population": 20868,
    "households": 8464,
    "median_household_income_usd": 48804,
    "no_internet_pct": 13.3,
    "no_vehicle_pct": 7.9,
    "age_65_plus_pct": 19.1,
    "disability_pct": 20.9,
    "poverty_pct": 24.5,
    "nri_risk_score": 55.4,
    "social_vulnerability_score": 96.2,
    "community_resilience_score": 68.1,
    "flood_risk_score": 58.6,
    "hurricane_risk_score": 60.7,
    "wildfire_risk_score": 49.1,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 2,
    "total_registrations": 3453,
    "web_registration_pct": 53.3,
    "call_center_registration_pct": 46.7,
    "web_registrations": 1840,
    "call_center_registrations": 1613,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/22107",
    "county_name": "Tensas Parish, LA",
    "state_name": "Louisiana",
    "state_code": "LA",
    "fema_region": "Region VI (South Central)",
    "latitude": 32.0,
    "longitude": -91.33,
    "population": 3700,
    "households": 1578,
    "median_household_income_usd": 36615,
    "no_internet_pct": 23.6,
    "no_vehicle_pct": 9.5,
    "age_65_plus_pct": 29.9,
    "disability_pct": 20.4,
    "poverty_pct": 34.1,
    "nri_risk_score": 14.5,
    "social_vulnerability_score": 96.1,
    "community_resilience_score": 31.4,
    "flood_risk_score": 8.1,
    "hurricane_risk_score": 70.2,
    "wildfire_risk_score": 6.3,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/01133",
    "county_name": "Winston County, AL",
    "state_name": "Alabama",
    "state_code": "AL",
    "fema_region": "Region IV (Southeast)",
    "latitude": 34.149166666667,
    "longitude": -87.365346,
    "population": 23829,
    "households": 9420,
    "median_household_income_usd": 57256,
    "no_internet_pct": 16.7,
    "no_vehicle_pct": 4.9,
    "age_65_plus_pct": 21.9,
    "disability_pct": 22.5,
    "poverty_pct": 18.2,
    "nri_risk_score": 59.2,
    "social_vulnerability_score": 96.0,
    "community_resilience_score": 16.6,
    "flood_risk_score": 64.7,
    "hurricane_risk_score": 62.8,
    "wildfire_risk_score": 59.1,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/01047",
    "county_name": "Dallas County, AL",
    "state_name": "Alabama",
    "state_code": "AL",
    "fema_region": "Region IV (Southeast)",
    "latitude": 32.324722222222,
    "longitude": -87.105277777778,
    "population": 35140,
    "households": 15947,
    "median_household_income_usd": 35627,
    "no_internet_pct": 17.0,
    "no_vehicle_pct": 14.1,
    "age_65_plus_pct": 21.4,
    "disability_pct": 22.4,
    "poverty_pct": 32.2,
    "nri_risk_score": 70.8,
    "social_vulnerability_score": 95.9,
    "community_resilience_score": 50.0,
    "flood_risk_score": 75.2,
    "hurricane_risk_score": 77.1,
    "wildfire_risk_score": 42.2,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 3109,
    "web_registration_pct": 15.4,
    "call_center_registration_pct": 58.6,
    "web_registrations": 479,
    "call_center_registrations": 2630,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/28079",
    "county_name": "Leake County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 32.75,
    "longitude": -89.52,
    "population": 21662,
    "households": 7414,
    "median_household_income_usd": 50728,
    "no_internet_pct": 21.9,
    "no_vehicle_pct": 8.7,
    "age_65_plus_pct": 17.9,
    "disability_pct": 16.7,
    "poverty_pct": 19.7,
    "nri_risk_score": 55.7,
    "social_vulnerability_score": 95.8,
    "community_resilience_score": 11.4,
    "flood_risk_score": 45.3,
    "hurricane_risk_score": 81.8,
    "wildfire_risk_score": 51.9,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/45065",
    "county_name": "McCormick County, SC",
    "state_name": "South Carolina",
    "state_code": "SC",
    "fema_region": "Region IV (Southeast)",
    "latitude": 33.897599,
    "longitude": -82.3,
    "population": 10215,
    "households": 4199,
    "median_household_income_usd": 55798,
    "no_internet_pct": 14.9,
    "no_vehicle_pct": 4.1,
    "age_65_plus_pct": 37.7,
    "disability_pct": 15.5,
    "poverty_pct": 15.3,
    "nri_risk_score": 9.5,
    "social_vulnerability_score": 95.7,
    "community_resilience_score": 18.2,
    "flood_risk_score": 16.8,
    "hurricane_risk_score": 62.3,
    "wildfire_risk_score": 34.8,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 2895,
    "web_registration_pct": 64.4,
    "call_center_registration_pct": 35.5,
    "web_registrations": 1864,
    "call_center_registrations": 1031,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/45087",
    "county_name": "Union County, SC",
    "state_name": "South Carolina",
    "state_code": "SC",
    "fema_region": "Region IV (Southeast)",
    "latitude": 34.69,
    "longitude": -81.615864,
    "population": 26799,
    "households": 11611,
    "median_household_income_usd": 41621,
    "no_internet_pct": 15.6,
    "no_vehicle_pct": 10.2,
    "age_65_plus_pct": 21.7,
    "disability_pct": 21.5,
    "poverty_pct": 22.4,
    "nri_risk_score": 58.2,
    "social_vulnerability_score": 95.5,
    "community_resilience_score": 40.8,
    "flood_risk_score": 53.4,
    "hurricane_risk_score": 71.1,
    "wildfire_risk_score": 53.5,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 6060,
    "web_registration_pct": 72.7,
    "call_center_registration_pct": 27.2,
    "web_registrations": 4406,
    "call_center_registrations": 1654,
    "has_team_coverage": true,
    "assigned_team_count": 2,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/21181",
    "county_name": "Nicholas County, KY",
    "state_name": "Kentucky",
    "state_code": "KY",
    "fema_region": "Region IV (Southeast)",
    "latitude": 38.338031,
    "longitude": -84.01,
    "population": 7949,
    "households": 2776,
    "median_household_income_usd": 59531,
    "no_internet_pct": 14.7,
    "no_vehicle_pct": 11.4,
    "age_65_plus_pct": 16.3,
    "disability_pct": 20.9,
    "poverty_pct": 16.8,
    "nri_risk_score": 19.0,
    "social_vulnerability_score": 95.5,
    "community_resilience_score": 52.4,
    "flood_risk_score": 41.4,
    "hurricane_risk_score": 31.2,
    "wildfire_risk_score": 2.3,
    "disasters_since_2023": 4,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/21237",
    "county_name": "Wolfe County, KY",
    "state_name": "Kentucky",
    "state_code": "KY",
    "fema_region": "Region IV (Southeast)",
    "latitude": 37.74,
    "longitude": -83.49,
    "population": 6298,
    "households": 2673,
    "median_household_income_usd": 30417,
    "no_internet_pct": 7.8,
    "no_vehicle_pct": 10.3,
    "age_65_plus_pct": 19.8,
    "disability_pct": 29.5,
    "poverty_pct": 37.7,
    "nri_risk_score": 18.5,
    "social_vulnerability_score": 95.3,
    "community_resilience_score": 1.4,
    "flood_risk_score": 42.6,
    "hurricane_risk_score": 31.2,
    "wildfire_risk_score": 63.8,
    "disasters_since_2023": 5,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/01093",
    "county_name": "Marion County, AL",
    "state_name": "Alabama",
    "state_code": "AL",
    "fema_region": "Region IV (Southeast)",
    "latitude": 34.136388888889,
    "longitude": -87.881551,
    "population": 29097,
    "households": 10614,
    "median_household_income_usd": 50088,
    "no_internet_pct": 18.3,
    "no_vehicle_pct": 4.2,
    "age_65_plus_pct": 21.5,
    "disability_pct": 26.3,
    "poverty_pct": 15.9,
    "nri_risk_score": 69.2,
    "social_vulnerability_score": 95.1,
    "community_resilience_score": 9.6,
    "flood_risk_score": 64.0,
    "hurricane_risk_score": 67.6,
    "wildfire_risk_score": 37.1,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/48489",
    "county_name": "Willacy County, TX",
    "state_name": "Texas",
    "state_code": "TX",
    "fema_region": "Region VI (South Central)",
    "latitude": 26.481861,
    "longitude": -97.594731,
    "population": 19971,
    "households": 5691,
    "median_household_income_usd": 54180,
    "no_internet_pct": 13.1,
    "no_vehicle_pct": 5.7,
    "age_65_plus_pct": 14.9,
    "disability_pct": 11.9,
    "poverty_pct": 22.0,
    "nri_risk_score": 77.5,
    "social_vulnerability_score": 95.0,
    "community_resilience_score": 3.7,
    "flood_risk_score": 30.9,
    "hurricane_risk_score": 91.7,
    "wildfire_risk_score": 28.7,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 793,
    "web_registration_pct": 55.9,
    "call_center_registration_pct": 44.1,
    "web_registrations": 443,
    "call_center_registrations": 350,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/28009",
    "county_name": "Benton County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 34.809593,
    "longitude": -89.19,
    "population": 7502,
    "households": 3074,
    "median_household_income_usd": 46016,
    "no_internet_pct": 25.0,
    "no_vehicle_pct": 6.8,
    "age_65_plus_pct": 21.2,
    "disability_pct": 26.3,
    "poverty_pct": 21.5,
    "nri_risk_score": 15.2,
    "social_vulnerability_score": 94.9,
    "community_resilience_score": 25.0,
    "flood_risk_score": 14.2,
    "hurricane_risk_score": 37.4,
    "wildfire_risk_score": 50.4,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 1229,
    "web_registration_pct": 45.6,
    "call_center_registration_pct": 54.4,
    "web_registrations": 560,
    "call_center_registrations": 669,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/28027",
    "county_name": "Coahoma County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 34.23,
    "longitude": -90.6,
    "population": 19849,
    "households": 8404,
    "median_household_income_usd": 37461,
    "no_internet_pct": 19.8,
    "no_vehicle_pct": 14.9,
    "age_65_plus_pct": 17.1,
    "disability_pct": 16.5,
    "poverty_pct": 35.7,
    "nri_risk_score": 62.5,
    "social_vulnerability_score": 94.8,
    "community_resilience_score": 74.5,
    "flood_risk_score": 46.3,
    "hurricane_risk_score": 59.7,
    "wildfire_risk_score": 10.5,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 3639,
    "web_registration_pct": 61.6,
    "call_center_registration_pct": 38.4,
    "web_registrations": 2242,
    "call_center_registrations": 1397,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/45075",
    "county_name": "Orangeburg County, SC",
    "state_name": "South Carolina",
    "state_code": "SC",
    "fema_region": "Region IV (Southeast)",
    "latitude": 33.436135,
    "longitude": -80.8,
    "population": 83177,
    "households": 33077,
    "median_household_income_usd": 45675,
    "no_internet_pct": 16.9,
    "no_vehicle_pct": 9.0,
    "age_65_plus_pct": 20.9,
    "disability_pct": 14.9,
    "poverty_pct": 21.5,
    "nri_risk_score": 87.7,
    "social_vulnerability_score": 94.8,
    "community_resilience_score": 47.4,
    "flood_risk_score": 75.8,
    "hurricane_risk_score": 95.3,
    "wildfire_risk_score": 79.9,
    "disasters_since_2023": 3,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 7601,
    "web_registration_pct": 71.9,
    "call_center_registration_pct": 27.7,
    "web_registrations": 5465,
    "call_center_registrations": 2136,
    "has_team_coverage": true,
    "assigned_team_count": 2,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/45049",
    "county_name": "Hampton County, SC",
    "state_name": "South Carolina",
    "state_code": "SC",
    "fema_region": "Region IV (Southeast)",
    "latitude": 32.778334,
    "longitude": -81.14,
    "population": 18174,
    "households": 7225,
    "median_household_income_usd": 44711,
    "no_internet_pct": 16.6,
    "no_vehicle_pct": 11.0,
    "age_65_plus_pct": 19.7,
    "disability_pct": 21.6,
    "poverty_pct": 20.4,
    "nri_risk_score": 64.8,
    "social_vulnerability_score": 94.6,
    "community_resilience_score": 27.4,
    "flood_risk_score": 34.7,
    "hurricane_risk_score": 93.0,
    "wildfire_risk_score": 71.4,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 2723,
    "web_registration_pct": 61.9,
    "call_center_registration_pct": 38.1,
    "web_registrations": 1686,
    "call_center_registrations": 1037,
    "has_team_coverage": true,
    "assigned_team_count": 2,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/37005",
    "county_name": "Alleghany County, NC",
    "state_name": "North Carolina",
    "state_code": "NC",
    "fema_region": "Region IV (Southeast)",
    "latitude": 36.489356,
    "longitude": -81.13,
    "population": 11479,
    "households": 5177,
    "median_household_income_usd": 47172,
    "no_internet_pct": 17.5,
    "no_vehicle_pct": 6.0,
    "age_65_plus_pct": 29.9,
    "disability_pct": 16.1,
    "poverty_pct": 15.4,
    "nri_risk_score": 34.7,
    "social_vulnerability_score": 94.5,
    "community_resilience_score": 10.5,
    "flood_risk_score": 41.1,
    "hurricane_risk_score": 59.1,
    "wildfire_risk_score": 45.8,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 731,
    "web_registration_pct": 69.6,
    "call_center_registration_pct": 30.2,
    "web_registrations": 509,
    "call_center_registrations": 222,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/28107",
    "county_name": "Panola County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 34.36,
    "longitude": -89.95,
    "population": 32691,
    "households": 12312,
    "median_household_income_usd": 45945,
    "no_internet_pct": 19.6,
    "no_vehicle_pct": 6.4,
    "age_65_plus_pct": 17.5,
    "disability_pct": 17.5,
    "poverty_pct": 23.2,
    "nri_risk_score": 69.2,
    "social_vulnerability_score": 94.5,
    "community_resilience_score": 23.0,
    "flood_risk_score": 43.9,
    "hurricane_risk_score": 67.8,
    "wildfire_risk_score": 63.4,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 2,
    "total_registrations": 7105,
    "web_registration_pct": 52.1,
    "call_center_registration_pct": 42.7,
    "web_registrations": 3702,
    "call_center_registrations": 3403,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/48455",
    "county_name": "Trinity County, TX",
    "state_name": "Texas",
    "state_code": "TX",
    "fema_region": "Region VI (South Central)",
    "latitude": 31.09,
    "longitude": -95.12,
    "population": 14384,
    "households": 6078,
    "median_household_income_usd": 52018,
    "no_internet_pct": 11.9,
    "no_vehicle_pct": 9.7,
    "age_65_plus_pct": 26.5,
    "disability_pct": 23.6,
    "poverty_pct": 16.9,
    "nri_risk_score": 60.6,
    "social_vulnerability_score": 94.5,
    "community_resilience_score": 12.2,
    "flood_risk_score": 40.3,
    "hurricane_risk_score": 83.7,
    "wildfire_risk_score": 70.0,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 2,
    "total_registrations": 2440,
    "web_registration_pct": 52.0,
    "call_center_registration_pct": 47.9,
    "web_registrations": 1269,
    "call_center_registrations": 1171,
    "has_team_coverage": false,
    "assigned_team_count": 0,
    "coverage_status": "Unserved Gap (Priority Dispatch)"
  },
  {
    "county_id": "geoId/21171",
    "county_name": "Monroe County, KY",
    "state_name": "Kentucky",
    "state_code": "KY",
    "fema_region": "Region IV (Southeast)",
    "latitude": 36.71,
    "longitude": -85.713508,
    "population": 11191,
    "households": 4645,
    "median_household_income_usd": 51280,
    "no_internet_pct": 13.8,
    "no_vehicle_pct": 5.0,
    "age_65_plus_pct": 18.8,
    "disability_pct": 22.4,
    "poverty_pct": 22.0,
    "nri_risk_score": 26.6,
    "social_vulnerability_score": 94.4,
    "community_resilience_score": 49.9,
    "flood_risk_score": 34.0,
    "hurricane_risk_score": 42.5,
    "wildfire_risk_score": 11.0,
    "disasters_since_2023": 5,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 58.0,
    "call_center_registration_pct": 42.0,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/28031",
    "county_name": "Covington County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 31.63,
    "longitude": -89.548897,
    "population": 17898,
    "households": 7323,
    "median_household_income_usd": 45051,
    "no_internet_pct": 24.3,
    "no_vehicle_pct": 8.8,
    "age_65_plus_pct": 17.9,
    "disability_pct": 17.8,
    "poverty_pct": 19.7,
    "nri_risk_score": 50.8,
    "social_vulnerability_score": 94.3,
    "community_resilience_score": 22.2,
    "flood_risk_score": 42.2,
    "hurricane_risk_score": 87.8,
    "wildfire_risk_score": 55.6,
    "disasters_since_2023": 4,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 1451,
    "web_registration_pct": 32.7,
    "call_center_registration_pct": 67.3,
    "web_registrations": 474,
    "call_center_registrations": 977,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/47075",
    "county_name": "Haywood County, TN",
    "state_name": "Tennessee",
    "state_code": "TN",
    "fema_region": "Region IV (Southeast)",
    "latitude": 35.58,
    "longitude": -89.282691,
    "population": 17042,
    "households": 7167,
    "median_household_income_usd": 50472,
    "no_internet_pct": 15.9,
    "no_vehicle_pct": 11.3,
    "age_65_plus_pct": 21.5,
    "disability_pct": 23.7,
    "poverty_pct": 21.7,
    "nri_risk_score": 64.7,
    "social_vulnerability_score": 94.3,
    "community_resilience_score": 72.4,
    "flood_risk_score": 24.9,
    "hurricane_risk_score": 56.6,
    "wildfire_risk_score": 10.4,
    "disasters_since_2023": 4,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 250,
    "web_registration_pct": 9.0,
    "call_center_registration_pct": 69.4,
    "web_registrations": 140,
    "call_center_registrations": 110,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/28001",
    "county_name": "Adams County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 31.48,
    "longitude": -91.35,
    "population": 30061,
    "households": 11464,
    "median_household_income_usd": 43644,
    "no_internet_pct": 13.4,
    "no_vehicle_pct": 6.4,
    "age_65_plus_pct": 21.1,
    "disability_pct": 13.2,
    "poverty_pct": 24.3,
    "nri_risk_score": 57.2,
    "social_vulnerability_score": 94.2,
    "community_resilience_score": 49.9,
    "flood_risk_score": 59.0,
    "hurricane_risk_score": 75.2,
    "wildfire_risk_score": 41.1,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 2531,
    "web_registration_pct": 66.1,
    "call_center_registration_pct": 33.9,
    "web_registrations": 1673,
    "call_center_registrations": 858,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/28143",
    "county_name": "Tunica County, MS",
    "state_name": "Mississippi",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "latitude": 34.652201,
    "longitude": -90.37177,
    "population": 8819,
    "households": 3800,
    "median_household_income_usd": 39364,
    "no_internet_pct": 15.8,
    "no_vehicle_pct": 10.7,
    "age_65_plus_pct": 15.8,
    "disability_pct": 11.2,
    "poverty_pct": 32.6,
    "nri_risk_score": 36.3,
    "social_vulnerability_score": 94.2,
    "community_resilience_score": 69.8,
    "flood_risk_score": 23.9,
    "hurricane_risk_score": 48.2,
    "wildfire_risk_score": 7.5,
    "disasters_since_2023": 1,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 1300,
    "web_registration_pct": 58.4,
    "call_center_registration_pct": 41.6,
    "web_registrations": 759,
    "call_center_registrations": 541,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/12055",
    "county_name": "Highlands County, FL",
    "state_name": "Florida",
    "state_code": "FL",
    "fema_region": "Region IV (Southeast)",
    "latitude": 27.34,
    "longitude": -81.34,
    "population": 111122,
    "households": 46879,
    "median_household_income_usd": 54897,
    "no_internet_pct": 10.3,
    "no_vehicle_pct": 5.6,
    "age_65_plus_pct": 34.2,
    "disability_pct": 21.5,
    "poverty_pct": 14.3,
    "nri_risk_score": 89.4,
    "social_vulnerability_score": 94.1,
    "community_resilience_score": 5.7,
    "flood_risk_score": 78.4,
    "hurricane_risk_score": 95.7,
    "wildfire_risk_score": 92.7,
    "disasters_since_2023": 2,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 10204,
    "web_registration_pct": 81.6,
    "call_center_registration_pct": 18.2,
    "web_registrations": 8326,
    "call_center_registrations": 1878,
    "has_team_coverage": true,
    "assigned_team_count": 1,
    "coverage_status": "Covered by Mobile DRC Team"
  },
  {
    "county_id": "geoId/45009",
    "county_name": "Bamberg County, SC",
    "state_name": "South Carolina",
    "state_code": "SC",
    "fema_region": "Region IV (Southeast)",
    "latitude": 33.203021,
    "longitude": -81.05,
    "population": 12796,
    "households": 4644,
    "median_household_income_usd": 44370,
    "no_internet_pct": 18.4,
    "no_vehicle_pct": 12.9,
    "age_65_plus_pct": 24.4,
    "disability_pct": 17.7,
    "poverty_pct": 23.3,
    "nri_risk_score": 46.5,
    "social_vulnerability_score": 94.1,
    "community_resilience_score": 37.6,
    "flood_risk_score": 20.6,
    "hurricane_risk_score": 89.1,
    "wildfire_risk_score": 55.9,
    "disasters_since_2023": 3,
    "ihp_disasters_since_2023": 1,
    "total_registrations": 1960,
    "web_registration_pct": 66.1,
    "call_center_registration_pct": 33.7,
    "web_registrations": 1296,
    "call_center_registrations": 664,
    "has_team_coverage": true,
    "assigned_team_count": 2,
    "coverage_status": "Covered by Mobile DRC Team"
  }
];

const US_MACRO_TIMELINE = [
  {
    "year": 1970,
    "us_population": 205052000,
    "seniors_65_plus_population": 20095096,
    "non_senior_population": 184956904,
    "seniors_65_plus_pct": 9.8,
    "median_household_income_usd": 9870,
    "poverty_rate_pct": 10.8,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 1.07,
    "gdp_per_capita_usd": 5218,
    "fema_major_disasters_count": 29,
    "billion_dollar_disasters_loss_usd_b": 29.3,
    "ghg_emissions_mt_co2e": 5100.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1971,
    "us_population": 207538581,
    "seniors_65_plus_population": 20421796,
    "non_senior_population": 187116785,
    "seniors_65_plus_pct": 9.84,
    "median_household_income_usd": 9965,
    "poverty_rate_pct": 11.3,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 1.08,
    "gdp_per_capita_usd": 5204,
    "fema_major_disasters_count": 32,
    "billion_dollar_disasters_loss_usd_b": 38.4,
    "ghg_emissions_mt_co2e": 5155.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1972,
    "us_population": 210025163,
    "seniors_65_plus_population": 20771488,
    "non_senior_population": 189253675,
    "seniors_65_plus_pct": 9.89,
    "median_household_income_usd": 10168,
    "poverty_rate_pct": 11.7,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 1.09,
    "gdp_per_capita_usd": 5190,
    "fema_major_disasters_count": 36,
    "billion_dollar_disasters_loss_usd_b": 47.7,
    "ghg_emissions_mt_co2e": 5210.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1973,
    "us_population": 212511745,
    "seniors_65_plus_population": 21166169,
    "non_senior_population": 191345576,
    "seniors_65_plus_pct": 9.96,
    "median_household_income_usd": 10452,
    "poverty_rate_pct": 12.1,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 1.12,
    "gdp_per_capita_usd": 5270,
    "fema_major_disasters_count": 40,
    "billion_dollar_disasters_loss_usd_b": 57.2,
    "ghg_emissions_mt_co2e": 5265.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1974,
    "us_population": 214998327,
    "seniors_65_plus_population": 21585832,
    "non_senior_population": 193412495,
    "seniors_65_plus_pct": 10.04,
    "median_household_income_usd": 10806,
    "poverty_rate_pct": 12.5,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 1.17,
    "gdp_per_capita_usd": 5442,
    "fema_major_disasters_count": 44,
    "billion_dollar_disasters_loss_usd_b": 25.4,
    "ghg_emissions_mt_co2e": 5320.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1975,
    "us_population": 217484909,
    "seniors_65_plus_population": 22009472,
    "non_senior_population": 195475437,
    "seniors_65_plus_pct": 10.12,
    "median_household_income_usd": 11223,
    "poverty_rate_pct": 12.9,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 1.23,
    "gdp_per_capita_usd": 5656,
    "fema_major_disasters_count": 48,
    "billion_dollar_disasters_loss_usd_b": 35.1,
    "ghg_emissions_mt_co2e": 5375.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1976,
    "us_population": 219971490,
    "seniors_65_plus_population": 22459089,
    "non_senior_population": 197512401,
    "seniors_65_plus_pct": 10.21,
    "median_household_income_usd": 11698,
    "poverty_rate_pct": 13.4,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 1.31,
    "gdp_per_capita_usd": 5955,
    "fema_major_disasters_count": 33,
    "billion_dollar_disasters_loss_usd_b": 45.0,
    "ghg_emissions_mt_co2e": 5430.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1977,
    "us_population": 222458072,
    "seniors_65_plus_population": 22913181,
    "non_senior_population": 199544891,
    "seniors_65_plus_pct": 10.3,
    "median_household_income_usd": 12227,
    "poverty_rate_pct": 13.8,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 1.4,
    "gdp_per_capita_usd": 6293,
    "fema_major_disasters_count": 37,
    "billion_dollar_disasters_loss_usd_b": 54.9,
    "ghg_emissions_mt_co2e": 5485.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1978,
    "us_population": 224944654,
    "seniors_65_plus_population": 23394244,
    "non_senior_population": 201550410,
    "seniors_65_plus_pct": 10.4,
    "median_household_income_usd": 12808,
    "poverty_rate_pct": 14.2,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 1.52,
    "gdp_per_capita_usd": 6757,
    "fema_major_disasters_count": 41,
    "billion_dollar_disasters_loss_usd_b": 23.6,
    "ghg_emissions_mt_co2e": 5540.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1979,
    "us_population": 227431236,
    "seniors_65_plus_population": 23880279,
    "non_senior_population": 203550957,
    "seniors_65_plus_pct": 10.5,
    "median_household_income_usd": 13439,
    "poverty_rate_pct": 14.6,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 1.64,
    "gdp_per_capita_usd": 7211,
    "fema_major_disasters_count": 46,
    "billion_dollar_disasters_loss_usd_b": 33.8,
    "ghg_emissions_mt_co2e": 5595.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1980,
    "us_population": 229917818,
    "seniors_65_plus_population": 24394280,
    "non_senior_population": 205523538,
    "seniors_65_plus_pct": 10.61,
    "median_household_income_usd": 14116,
    "poverty_rate_pct": 10.2,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 1.79,
    "gdp_per_capita_usd": 7785,
    "fema_major_disasters_count": 50,
    "billion_dollar_disasters_loss_usd_b": 44.2,
    "ghg_emissions_mt_co2e": 5650.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1981,
    "us_population": 232404400,
    "seniors_65_plus_population": 24913751,
    "non_senior_population": 207490649,
    "seniors_65_plus_pct": 10.72,
    "median_household_income_usd": 14840,
    "poverty_rate_pct": 10.6,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 1.95,
    "gdp_per_capita_usd": 8391,
    "fema_major_disasters_count": 55,
    "billion_dollar_disasters_loss_usd_b": 54.6,
    "ghg_emissions_mt_co2e": 5705.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1982,
    "us_population": 234890981,
    "seniors_65_plus_population": 25462182,
    "non_senior_population": 209428799,
    "seniors_65_plus_pct": 10.84,
    "median_household_income_usd": 15607,
    "poverty_rate_pct": 11.0,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 2.13,
    "gdp_per_capita_usd": 9068,
    "fema_major_disasters_count": 60,
    "billion_dollar_disasters_loss_usd_b": 65.2,
    "ghg_emissions_mt_co2e": 5760.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1983,
    "us_population": 237377563,
    "seniors_65_plus_population": 26016580,
    "non_senior_population": 211360983,
    "seniors_65_plus_pct": 10.96,
    "median_household_income_usd": 16417,
    "poverty_rate_pct": 11.5,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 2.33,
    "gdp_per_capita_usd": 9816,
    "fema_major_disasters_count": 45,
    "billion_dollar_disasters_loss_usd_b": 34.4,
    "ghg_emissions_mt_co2e": 5815.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1984,
    "us_population": 239864145,
    "seniors_65_plus_population": 26576947,
    "non_senior_population": 213287198,
    "seniors_65_plus_pct": 11.08,
    "median_household_income_usd": 17269,
    "poverty_rate_pct": 11.9,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 2.55,
    "gdp_per_capita_usd": 10631,
    "fema_major_disasters_count": 50,
    "billion_dollar_disasters_loss_usd_b": 45.2,
    "ghg_emissions_mt_co2e": 5870.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1985,
    "us_population": 242350727,
    "seniors_65_plus_population": 27143281,
    "non_senior_population": 215207446,
    "seniors_65_plus_pct": 11.2,
    "median_household_income_usd": 18161,
    "poverty_rate_pct": 12.3,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 2.79,
    "gdp_per_capita_usd": 11512,
    "fema_major_disasters_count": 55,
    "billion_dollar_disasters_loss_usd_b": 56.0,
    "ghg_emissions_mt_co2e": 5925.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1986,
    "us_population": 244837309,
    "seniors_65_plus_population": 27740067,
    "non_senior_population": 217097242,
    "seniors_65_plus_pct": 11.33,
    "median_household_income_usd": 19092,
    "poverty_rate_pct": 12.7,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 3.05,
    "gdp_per_capita_usd": 12457,
    "fema_major_disasters_count": 59,
    "billion_dollar_disasters_loss_usd_b": 67.0,
    "ghg_emissions_mt_co2e": 5980.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1987,
    "us_population": 247323890,
    "seniors_65_plus_population": 28343317,
    "non_senior_population": 218980573,
    "seniors_65_plus_pct": 11.46,
    "median_household_income_usd": 20063,
    "poverty_rate_pct": 13.1,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 3.32,
    "gdp_per_capita_usd": 13424,
    "fema_major_disasters_count": 64,
    "billion_dollar_disasters_loss_usd_b": 78.0,
    "ghg_emissions_mt_co2e": 6035.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1988,
    "us_population": 249810472,
    "seniors_65_plus_population": 28953033,
    "non_senior_population": 220857439,
    "seniors_65_plus_pct": 11.59,
    "median_household_income_usd": 21071,
    "poverty_rate_pct": 13.6,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 3.62,
    "gdp_per_capita_usd": 14491,
    "fema_major_disasters_count": 69,
    "billion_dollar_disasters_loss_usd_b": 47.8,
    "ghg_emissions_mt_co2e": 6090.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1989,
    "us_population": 252297054,
    "seniors_65_plus_population": 29594444,
    "non_senior_population": 222702610,
    "seniors_65_plus_pct": 11.73,
    "median_household_income_usd": 22116,
    "poverty_rate_pct": 14.0,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 3.93,
    "gdp_per_capita_usd": 15577,
    "fema_major_disasters_count": 55,
    "billion_dollar_disasters_loss_usd_b": 59.1,
    "ghg_emissions_mt_co2e": 6145.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1990,
    "us_population": 254783636,
    "seniors_65_plus_population": 30242817,
    "non_senior_population": 224540819,
    "seniors_65_plus_pct": 11.87,
    "median_household_income_usd": 23198,
    "poverty_rate_pct": 14.4,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 4.26,
    "gdp_per_capita_usd": 16720,
    "fema_major_disasters_count": 60,
    "billion_dollar_disasters_loss_usd_b": 70.4,
    "ghg_emissions_mt_co2e": 6450.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1991,
    "us_population": 257270218,
    "seniors_65_plus_population": 30898153,
    "non_senior_population": 226372065,
    "seniors_65_plus_pct": 12.01,
    "median_household_income_usd": 24315,
    "poverty_rate_pct": 10.0,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 4.62,
    "gdp_per_capita_usd": 17958,
    "fema_major_disasters_count": 65,
    "billion_dollar_disasters_loss_usd_b": 81.9,
    "ghg_emissions_mt_co2e": 6450.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1992,
    "us_population": 259756800,
    "seniors_65_plus_population": 31560451,
    "non_senior_population": 228196349,
    "seniors_65_plus_pct": 12.15,
    "median_household_income_usd": 25467,
    "poverty_rate_pct": 10.4,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 4.99,
    "gdp_per_capita_usd": 19210,
    "fema_major_disasters_count": 70,
    "billion_dollar_disasters_loss_usd_b": 52.0,
    "ghg_emissions_mt_co2e": 6450.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1993,
    "us_population": 262243381,
    "seniors_65_plus_population": 32255935,
    "non_senior_population": 229987446,
    "seniors_65_plus_pct": 12.3,
    "median_household_income_usd": 26654,
    "poverty_rate_pct": 10.8,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 5.38,
    "gdp_per_capita_usd": 20515,
    "fema_major_disasters_count": 75,
    "billion_dollar_disasters_loss_usd_b": 63.7,
    "ghg_emissions_mt_co2e": 6450.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1994,
    "us_population": 264729963,
    "seniors_65_plus_population": 32932407,
    "non_senior_population": 231797556,
    "seniors_65_plus_pct": 12.44,
    "median_household_income_usd": 27875,
    "poverty_rate_pct": 11.2,
    "no_internet_households_pct": 95.0,
    "gdp_nominal_trillions_usd": 5.8,
    "gdp_per_capita_usd": 21909,
    "fema_major_disasters_count": 80,
    "billion_dollar_disasters_loss_usd_b": 75.4,
    "ghg_emissions_mt_co2e": 6450.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1995,
    "us_population": 267216545,
    "seniors_65_plus_population": 33642563,
    "non_senior_population": 233573982,
    "seniors_65_plus_pct": 12.59,
    "median_household_income_usd": 29130,
    "poverty_rate_pct": 11.7,
    "no_internet_households_pct": 38.3,
    "gdp_nominal_trillions_usd": 6.23,
    "gdp_per_capita_usd": 23314,
    "fema_major_disasters_count": 67,
    "billion_dollar_disasters_loss_usd_b": 87.2,
    "ghg_emissions_mt_co2e": 6450.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1996,
    "us_population": 269703127,
    "seniors_65_plus_population": 34387148,
    "non_senior_population": 235315979,
    "seniors_65_plus_pct": 12.75,
    "median_household_income_usd": 30418,
    "poverty_rate_pct": 12.1,
    "no_internet_households_pct": 36.6,
    "gdp_nominal_trillions_usd": 6.68,
    "gdp_per_capita_usd": 24768,
    "fema_major_disasters_count": 72,
    "billion_dollar_disasters_loss_usd_b": 99.1,
    "ghg_emissions_mt_co2e": 6450.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1997,
    "us_population": 272189709,
    "seniors_65_plus_population": 35112472,
    "non_senior_population": 237077237,
    "seniors_65_plus_pct": 12.9,
    "median_household_income_usd": 31738,
    "poverty_rate_pct": 12.5,
    "no_internet_households_pct": 35.0,
    "gdp_nominal_trillions_usd": 7.16,
    "gdp_per_capita_usd": 26305,
    "fema_major_disasters_count": 77,
    "billion_dollar_disasters_loss_usd_b": 69.7,
    "ghg_emissions_mt_co2e": 6450.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1998,
    "us_population": 274676290,
    "seniors_65_plus_population": 35872723,
    "non_senior_population": 238803567,
    "seniors_65_plus_pct": 13.06,
    "median_household_income_usd": 33090,
    "poverty_rate_pct": 12.9,
    "no_internet_households_pct": 33.5,
    "gdp_nominal_trillions_usd": 7.65,
    "gdp_per_capita_usd": 27851,
    "fema_major_disasters_count": 82,
    "billion_dollar_disasters_loss_usd_b": 81.8,
    "ghg_emissions_mt_co2e": 6450.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 1999,
    "us_population": 277162872,
    "seniors_65_plus_population": 36613215,
    "non_senior_population": 240549657,
    "seniors_65_plus_pct": 13.21,
    "median_household_income_usd": 34474,
    "poverty_rate_pct": 13.3,
    "no_internet_households_pct": 31.9,
    "gdp_nominal_trillions_usd": 8.17,
    "gdp_per_capita_usd": 29477,
    "fema_major_disasters_count": 88,
    "billion_dollar_disasters_loss_usd_b": 94.0,
    "ghg_emissions_mt_co2e": 6450.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 2000,
    "us_population": 279649454,
    "seniors_65_plus_population": 37389131,
    "non_senior_population": 242260323,
    "seniors_65_plus_pct": 13.37,
    "median_household_income_usd": 35890,
    "poverty_rate_pct": 13.8,
    "no_internet_households_pct": 30.4,
    "gdp_nominal_trillions_usd": 8.71,
    "gdp_per_capita_usd": 31146,
    "fema_major_disasters_count": 93,
    "billion_dollar_disasters_loss_usd_b": 106.3,
    "ghg_emissions_mt_co2e": 6450.0,
    "clean_electricity_share_pct": 18.0
  },
  {
    "year": 2001,
    "us_population": 282136036,
    "seniors_65_plus_population": 38201219,
    "non_senior_population": 243934817,
    "seniors_65_plus_pct": 13.54,
    "median_household_income_usd": 37337,
    "poverty_rate_pct": 14.2,
    "no_internet_households_pct": 29.0,
    "gdp_nominal_trillions_usd": 9.26,
    "gdp_per_capita_usd": 32821,
    "fema_major_disasters_count": 98,
    "billion_dollar_disasters_loss_usd_b": 77.3,
    "ghg_emissions_mt_co2e": 6450.0,
    "clean_electricity_share_pct": 18.9
  },
  {
    "year": 2002,
    "us_population": 284622618,
    "seniors_65_plus_population": 38993298,
    "non_senior_population": 245629320,
    "seniors_65_plus_pct": 13.7,
    "median_household_income_usd": 38814,
    "poverty_rate_pct": 9.8,
    "no_internet_households_pct": 27.5,
    "gdp_nominal_trillions_usd": 9.84,
    "gdp_per_capita_usd": 34572,
    "fema_major_disasters_count": 85,
    "billion_dollar_disasters_loss_usd_b": 89.7,
    "ghg_emissions_mt_co2e": 6450.0,
    "clean_electricity_share_pct": 19.9
  },
  {
    "year": 2003,
    "us_population": 287109200,
    "seniors_65_plus_population": 39793335,
    "non_senior_population": 247315865,
    "seniors_65_plus_pct": 13.86,
    "median_household_income_usd": 40321,
    "poverty_rate_pct": 10.2,
    "no_internet_households_pct": 26.1,
    "gdp_nominal_trillions_usd": 10.44,
    "gdp_per_capita_usd": 36362,
    "fema_major_disasters_count": 90,
    "billion_dollar_disasters_loss_usd_b": 102.3,
    "ghg_emissions_mt_co2e": 6450.0,
    "clean_electricity_share_pct": 20.9
  },
  {
    "year": 2004,
    "us_population": 289595781,
    "seniors_65_plus_population": 40630288,
    "non_senior_population": 248965493,
    "seniors_65_plus_pct": 14.03,
    "median_household_income_usd": 41859,
    "poverty_rate_pct": 10.6,
    "no_internet_households_pct": 24.8,
    "gdp_nominal_trillions_usd": 11.06,
    "gdp_per_capita_usd": 38191,
    "fema_major_disasters_count": 96,
    "billion_dollar_disasters_loss_usd_b": 114.9,
    "ghg_emissions_mt_co2e": 6450.0,
    "clean_electricity_share_pct": 21.8
  },
  {
    "year": 2005,
    "us_population": 292082363,
    "seniors_65_plus_population": 41475695,
    "non_senior_population": 250606668,
    "seniors_65_plus_pct": 14.2,
    "median_household_income_usd": 43426,
    "poverty_rate_pct": 11.0,
    "no_internet_households_pct": 23.5,
    "gdp_nominal_trillions_usd": 11.71,
    "gdp_per_capita_usd": 40091,
    "fema_major_disasters_count": 101,
    "billion_dollar_disasters_loss_usd_b": 127.6,
    "ghg_emissions_mt_co2e": 6450.0,
    "clean_electricity_share_pct": 22.8
  },
  {
    "year": 2006,
    "us_population": 294568945,
    "seniors_65_plus_population": 42329557,
    "non_senior_population": 252239388,
    "seniors_65_plus_pct": 14.37,
    "median_household_income_usd": 45023,
    "poverty_rate_pct": 11.4,
    "no_internet_households_pct": 22.2,
    "gdp_nominal_trillions_usd": 12.37,
    "gdp_per_capita_usd": 41994,
    "fema_major_disasters_count": 107,
    "billion_dollar_disasters_loss_usd_b": 99.0,
    "ghg_emissions_mt_co2e": 6407.5,
    "clean_electricity_share_pct": 23.7
  },
  {
    "year": 2007,
    "us_population": 297055527,
    "seniors_65_plus_population": 43191873,
    "non_senior_population": 253863654,
    "seniors_65_plus_pct": 14.54,
    "median_household_income_usd": 46648,
    "poverty_rate_pct": 11.9,
    "no_internet_households_pct": 20.9,
    "gdp_nominal_trillions_usd": 13.06,
    "gdp_per_capita_usd": 43965,
    "fema_major_disasters_count": 112,
    "billion_dollar_disasters_loss_usd_b": 111.9,
    "ghg_emissions_mt_co2e": 6365.0,
    "clean_electricity_share_pct": 24.6
  },
  {
    "year": 2008,
    "us_population": 299542109,
    "seniors_65_plus_population": 44092598,
    "non_senior_population": 255449511,
    "seniors_65_plus_pct": 14.72,
    "median_household_income_usd": 48303,
    "poverty_rate_pct": 12.3,
    "no_internet_households_pct": 19.7,
    "gdp_nominal_trillions_usd": 13.76,
    "gdp_per_capita_usd": 45937,
    "fema_major_disasters_count": 99,
    "billion_dollar_disasters_loss_usd_b": 124.9,
    "ghg_emissions_mt_co2e": 6322.5,
    "clean_electricity_share_pct": 25.6
  },
  {
    "year": 2009,
    "us_population": 302028690,
    "seniors_65_plus_population": 44972071,
    "non_senior_population": 257056619,
    "seniors_65_plus_pct": 14.89,
    "median_household_income_usd": 49986,
    "poverty_rate_pct": 12.7,
    "no_internet_households_pct": 18.6,
    "gdp_nominal_trillions_usd": 14.49,
    "gdp_per_capita_usd": 47976,
    "fema_major_disasters_count": 104,
    "billion_dollar_disasters_loss_usd_b": 138.0,
    "ghg_emissions_mt_co2e": 6280.0,
    "clean_electricity_share_pct": 26.5
  },
  {
    "year": 2010,
    "us_population": 304515272,
    "seniors_65_plus_population": 45890451,
    "non_senior_population": 258624821,
    "seniors_65_plus_pct": 15.07,
    "median_household_income_usd": 51697,
    "poverty_rate_pct": 13.1,
    "no_internet_households_pct": 17.5,
    "gdp_nominal_trillions_usd": 15.24,
    "gdp_per_capita_usd": 50047,
    "fema_major_disasters_count": 110,
    "billion_dollar_disasters_loss_usd_b": 151.1,
    "ghg_emissions_mt_co2e": 6237.5,
    "clean_electricity_share_pct": 27.5
  },
  {
    "year": 2011,
    "us_population": 307001854,
    "seniors_65_plus_population": 46817782,
    "non_senior_population": 260184072,
    "seniors_65_plus_pct": 15.25,
    "median_household_income_usd": 53437,
    "poverty_rate_pct": 13.5,
    "no_internet_households_pct": 16.4,
    "gdp_nominal_trillions_usd": 16.02,
    "gdp_per_capita_usd": 52182,
    "fema_major_disasters_count": 116,
    "billion_dollar_disasters_loss_usd_b": 122.9,
    "ghg_emissions_mt_co2e": 6195.0,
    "clean_electricity_share_pct": 28.4
  },
  {
    "year": 2012,
    "us_population": 309488436,
    "seniors_65_plus_population": 47754065,
    "non_senior_population": 261734371,
    "seniors_65_plus_pct": 15.43,
    "median_household_income_usd": 55204,
    "poverty_rate_pct": 14.0,
    "no_internet_households_pct": 15.4,
    "gdp_nominal_trillions_usd": 16.81,
    "gdp_per_capita_usd": 54315,
    "fema_major_disasters_count": 121,
    "billion_dollar_disasters_loss_usd_b": 136.2,
    "ghg_emissions_mt_co2e": 6152.5,
    "clean_electricity_share_pct": 29.4
  },
  {
    "year": 2013,
    "us_population": 311975018,
    "seniors_65_plus_population": 48699300,
    "non_senior_population": 263275718,
    "seniors_65_plus_pct": 15.61,
    "median_household_income_usd": 56999,
    "poverty_rate_pct": 9.5,
    "no_internet_households_pct": 14.4,
    "gdp_nominal_trillions_usd": 17.63,
    "gdp_per_capita_usd": 56511,
    "fema_major_disasters_count": 127,
    "billion_dollar_disasters_loss_usd_b": 149.6,
    "ghg_emissions_mt_co2e": 6110.0,
    "clean_electricity_share_pct": 30.4
  },
  {
    "year": 2014,
    "us_population": 314461600,
    "seniors_65_plus_population": 49653486,
    "non_senior_population": 264808114,
    "seniors_65_plus_pct": 15.79,
    "median_household_income_usd": 58821,
    "poverty_rate_pct": 10.0,
    "no_internet_households_pct": 13.4,
    "gdp_nominal_trillions_usd": 18.47,
    "gdp_per_capita_usd": 58735,
    "fema_major_disasters_count": 114,
    "billion_dollar_disasters_loss_usd_b": 163.1,
    "ghg_emissions_mt_co2e": 6067.5,
    "clean_electricity_share_pct": 31.3
  },
  {
    "year": 2015,
    "us_population": 316948181,
    "seniors_65_plus_population": 50648319,
    "non_senior_population": 266299862,
    "seniors_65_plus_pct": 15.98,
    "median_household_income_usd": 60670,
    "poverty_rate_pct": 10.4,
    "no_internet_households_pct": 12.6,
    "gdp_nominal_trillions_usd": 19.33,
    "gdp_per_capita_usd": 60988,
    "fema_major_disasters_count": 120,
    "billion_dollar_disasters_loss_usd_b": 135.3,
    "ghg_emissions_mt_co2e": 6025.0,
    "clean_electricity_share_pct": 32.2
  },
  {
    "year": 2016,
    "us_population": 319434763,
    "seniors_65_plus_population": 51620657,
    "non_senior_population": 267814106,
    "seniors_65_plus_pct": 16.16,
    "median_household_income_usd": 62546,
    "poverty_rate_pct": 10.8,
    "no_internet_households_pct": 11.7,
    "gdp_nominal_trillions_usd": 20.21,
    "gdp_per_capita_usd": 63268,
    "fema_major_disasters_count": 125,
    "billion_dollar_disasters_loss_usd_b": 148.9,
    "ghg_emissions_mt_co2e": 5982.5,
    "clean_electricity_share_pct": 33.2
  },
  {
    "year": 2017,
    "us_population": 321921345,
    "seniors_65_plus_population": 52634139,
    "non_senior_population": 269287206,
    "seniors_65_plus_pct": 16.35,
    "median_household_income_usd": 64449,
    "poverty_rate_pct": 11.2,
    "no_internet_households_pct": 11.0,
    "gdp_nominal_trillions_usd": 21.12,
    "gdp_per_capita_usd": 65606,
    "fema_major_disasters_count": 131,
    "billion_dollar_disasters_loss_usd_b": 162.6,
    "ghg_emissions_mt_co2e": 5940.0,
    "clean_electricity_share_pct": 34.1
  },
  {
    "year": 2018,
    "us_population": 324407927,
    "seniors_65_plus_population": 53657071,
    "non_senior_population": 270750856,
    "seniors_65_plus_pct": 16.54,
    "median_household_income_usd": 66378,
    "poverty_rate_pct": 11.6,
    "no_internet_households_pct": 10.2,
    "gdp_nominal_trillions_usd": 22.05,
    "gdp_per_capita_usd": 67970,
    "fema_major_disasters_count": 137,
    "billion_dollar_disasters_loss_usd_b": 176.4,
    "ghg_emissions_mt_co2e": 5897.5,
    "clean_electricity_share_pct": 35.1
  },
  {
    "year": 2019,
    "us_population": 326894509,
    "seniors_65_plus_population": 54689451,
    "non_senior_population": 272205058,
    "seniors_65_plus_pct": 16.73,
    "median_household_income_usd": 68334,
    "poverty_rate_pct": 12.1,
    "no_internet_households_pct": 9.6,
    "gdp_nominal_trillions_usd": 23.0,
    "gdp_per_capita_usd": 70359,
    "fema_major_disasters_count": 143,
    "billion_dollar_disasters_loss_usd_b": 190.3,
    "ghg_emissions_mt_co2e": 5855.0,
    "clean_electricity_share_pct": 36.0
  },
  {
    "year": 2020,
    "us_population": 329381090,
    "seniors_65_plus_population": 55731280,
    "non_senior_population": 273649810,
    "seniors_65_plus_pct": 16.92,
    "median_household_income_usd": 70315,
    "poverty_rate_pct": 12.5,
    "no_internet_households_pct": 9.0,
    "gdp_nominal_trillions_usd": 23.97,
    "gdp_per_capita_usd": 72773,
    "fema_major_disasters_count": 149,
    "billion_dollar_disasters_loss_usd_b": 162.9,
    "ghg_emissions_mt_co2e": 5812.5,
    "clean_electricity_share_pct": 37.0
  },
  {
    "year": 2021,
    "us_population": 331867672,
    "seniors_65_plus_population": 56815745,
    "non_senior_population": 275051927,
    "seniors_65_plus_pct": 17.12,
    "median_household_income_usd": 72323,
    "poverty_rate_pct": 12.9,
    "no_internet_households_pct": 8.4,
    "gdp_nominal_trillions_usd": 24.97,
    "gdp_per_capita_usd": 75241,
    "fema_major_disasters_count": 136,
    "billion_dollar_disasters_loss_usd_b": 176.9,
    "ghg_emissions_mt_co2e": 5770.0,
    "clean_electricity_share_pct": 38.0
  },
  {
    "year": 2022,
    "us_population": 334354254,
    "seniors_65_plus_population": 57876721,
    "non_senior_population": 276477533,
    "seniors_65_plus_pct": 17.31,
    "median_household_income_usd": 74356,
    "poverty_rate_pct": 13.3,
    "no_internet_households_pct": 8.0,
    "gdp_nominal_trillions_usd": 25.99,
    "gdp_per_capita_usd": 77732,
    "fema_major_disasters_count": 142,
    "billion_dollar_disasters_loss_usd_b": 191.1,
    "ghg_emissions_mt_co2e": 5727.5,
    "clean_electricity_share_pct": 38.9
  },
  {
    "year": 2023,
    "us_population": 336840836,
    "seniors_65_plus_population": 58947146,
    "non_senior_population": 277893690,
    "seniors_65_plus_pct": 17.5,
    "median_household_income_usd": 76415,
    "poverty_rate_pct": 13.7,
    "no_internet_households_pct": 7.6,
    "gdp_nominal_trillions_usd": 27.03,
    "gdp_per_capita_usd": 80246,
    "fema_major_disasters_count": 148,
    "billion_dollar_disasters_loss_usd_b": 205.3,
    "ghg_emissions_mt_co2e": 5685.0,
    "clean_electricity_share_pct": 39.8
  },
  {
    "year": 2024,
    "us_population": 339327418,
    "seniors_65_plus_population": 60060952,
    "non_senior_population": 279266466,
    "seniors_65_plus_pct": 17.7,
    "median_household_income_usd": 78500,
    "poverty_rate_pct": 9.3,
    "no_internet_households_pct": 7.3,
    "gdp_nominal_trillions_usd": 28.09,
    "gdp_per_capita_usd": 82781,
    "fema_major_disasters_count": 154,
    "billion_dollar_disasters_loss_usd_b": 178.1,
    "ghg_emissions_mt_co2e": 5642.5,
    "clean_electricity_share_pct": 40.8
  },
  {
    "year": 2025,
    "us_population": 341814000,
    "seniors_65_plus_population": 61184705,
    "non_senior_population": 280629295,
    "seniors_65_plus_pct": 17.9,
    "median_household_income_usd": 80610,
    "poverty_rate_pct": 9.7,
    "no_internet_households_pct": 7.2,
    "gdp_nominal_trillions_usd": 29.18,
    "gdp_per_capita_usd": 85368,
    "fema_major_disasters_count": 160,
    "billion_dollar_disasters_loss_usd_b": 192.5,
    "ghg_emissions_mt_co2e": 5600.0,
    "clean_electricity_share_pct": 41.8
  }
];

const US_FEDERAL_PROGRAMS = [
  {
    "call_center_share_pct": 17.8,
    "web_intake_share_pct": 76.2,
    "assisted_households": 310000,
    "mobile_drc_share_pct": 6.0,
    "annual_budget_million_usd": 1120.0,
    "target_svi_threshold": 65.0,
    "lead_agency": "U.S. Small Business Admin",
    "policy_pillar": "Individual Disaster Assistance",
    "program_name": "SBA Disaster Assistance & Economic Injury Loans",
    "program_id": "us/prog/sba_disaster"
  },
  {
    "call_center_share_pct": 18.0,
    "web_intake_share_pct": 74.0,
    "assisted_households": 490000,
    "mobile_drc_share_pct": 8.0,
    "annual_budget_million_usd": 940.0,
    "target_svi_threshold": 70.0,
    "lead_agency": "EPA & Dept. of Energy",
    "policy_pillar": "Hazard Mitigation & Climate Resilience",
    "program_name": "EPA & DOE Grid Resilience & Clean Water Grants",
    "program_id": "us/prog/epa_water_grid"
  },
  {
    "call_center_share_pct": 19.5,
    "web_intake_share_pct": 71.5,
    "assisted_households": 920000,
    "mobile_drc_share_pct": 9.0,
    "annual_budget_million_usd": 3180.0,
    "target_svi_threshold": 70.0,
    "lead_agency": "FEMA / DHS",
    "policy_pillar": "Critical Infrastructure Recovery",
    "program_name": "FEMA Public Assistance & Infrastructure",
    "program_id": "us/prog/fema_pa"
  },
  {
    "call_center_share_pct": 28.0,
    "web_intake_share_pct": 54.0,
    "assisted_households": 740000,
    "mobile_drc_share_pct": 18.0,
    "annual_budget_million_usd": 620.0,
    "target_svi_threshold": 75.0,
    "lead_agency": "FCC & NTIA (Commerce)",
    "policy_pillar": "Digital Inclusion & Emergency Comms",
    "program_name": "FCC & NTIA Emergency Broadband & Lifeline",
    "program_id": "us/prog/fcc_ntia_ecf"
  },
  {
    "call_center_share_pct": 14.6,
    "web_intake_share_pct": 78.4,
    "assisted_households": 640000,
    "mobile_drc_share_pct": 7.0,
    "annual_budget_million_usd": 1850.0,
    "target_svi_threshold": 75.0,
    "lead_agency": "FEMA / DHS",
    "policy_pillar": "Hazard Mitigation & Climate Resilience",
    "program_name": "Building Resilient Infrastructure & Communities (BRIC)",
    "program_id": "us/prog/fema_bric"
  },
  {
    "call_center_share_pct": 24.8,
    "web_intake_share_pct": 64.2,
    "assisted_households": 1840000,
    "mobile_drc_share_pct": 11.0,
    "annual_budget_million_usd": 2420.0,
    "target_svi_threshold": 75.0,
    "lead_agency": "FEMA / DHS",
    "policy_pillar": "Individual Disaster Assistance",
    "program_name": "FEMA Individual & Households Program (IHP)",
    "program_id": "us/prog/fema_ihp"
  },
  {
    "call_center_share_pct": 25.0,
    "web_intake_share_pct": 58.5,
    "assisted_households": 385000,
    "mobile_drc_share_pct": 16.5,
    "annual_budget_million_usd": 890.0,
    "target_svi_threshold": 80.0,
    "lead_agency": "HHS / ASPR & CDC",
    "policy_pillar": "Public Health & Senior/Disability Care",
    "program_name": "HHS ASPR emPOWER & Medical Reserve Readiness",
    "program_id": "us/prog/hhs_aspr"
  },
  {
    "call_center_share_pct": 21.0,
    "web_intake_share_pct": 68.0,
    "assisted_households": 530000,
    "mobile_drc_share_pct": 11.0,
    "annual_budget_million_usd": 1960.0,
    "target_svi_threshold": 80.0,
    "lead_agency": "HUD",
    "policy_pillar": "Disaster Housing & Long-Term Recovery",
    "program_name": "HUD Community Development Block Grant (CDBG-DR)",
    "program_id": "us/prog/hud_cdbg_dr"
  },
  {
    "call_center_share_pct": 30.6,
    "web_intake_share_pct": 52.4,
    "assisted_households": 265000,
    "mobile_drc_share_pct": 17.0,
    "annual_budget_million_usd": 540.0,
    "target_svi_threshold": 80.0,
    "lead_agency": "USDA Rural Development",
    "policy_pillar": "Critical Infrastructure Recovery",
    "program_name": "USDA Rural Community Facilities & Emergency Water",
    "program_id": "us/prog/usda_rural"
  },
  {
    "call_center_share_pct": 26.5,
    "web_intake_share_pct": 31.0,
    "assisted_households": 412000,
    "mobile_drc_share_pct": 42.5,
    "annual_budget_million_usd": 480.0,
    "target_svi_threshold": 85.0,
    "lead_agency": "FEMA / Beacon Office",
    "policy_pillar": "Mobile Field Response & Equity",
    "program_name": "Beacon Mobile Disaster Recovery Centers (MDRC)",
    "program_id": "us/prog/fema_mdrc"
  }
];

const US_DEPLOYMENT_PLAN = [
  {
    "county_id": "geoId/01063",
    "county_name": "Greene County, AL",
    "state_code": "AL",
    "fema_region": "Region IV (Southeast)",
    "priority_tier": "Tier 1 - Immediate",
    "assigned_team_id": "beacon/team/dispatch_fcc_echo",
    "added_by": "FCC / NTIA & FEMA Region IV",
    "action": "Deploy Emergency SatCom & Intake Team",
    "status": "Proposed",
    "svi_score": 98.1,
    "no_internet_pct": 25.8,
    "rationale": "Greene County, AL: 98.1 SVI, 25.8% households without internet, severe rural broadband & transit gap"
  },
  {
    "county_id": "geoId/48427",
    "county_name": "Starr County, TX",
    "state_code": "TX",
    "fema_region": "Region VI (South Central)",
    "priority_tier": "Tier 2 - High Priority",
    "assigned_team_id": "beacon/team/dispatch_fcc_echo",
    "added_by": "FCC / NTIA & FEMA Region VI",
    "action": "Deploy Emergency SatCom & Intake Team",
    "status": "Proposed",
    "svi_score": 97.0,
    "no_internet_pct": 19.9,
    "rationale": "Starr County, TX: 97.0 SVI, 66.3K residents, 19.9% no internet & 31.2% poverty rate along Rio Grande flood plain"
  },
  {
    "county_id": "geoId/05041",
    "county_name": "Desha County, AR",
    "state_code": "AR",
    "fema_region": "Region VI (South Central)",
    "priority_tier": "Tier 2 - High Priority",
    "assigned_team_id": "beacon/team/dispatch_fcc_echo",
    "added_by": "FEMA Region VI & Beacon AI Agent",
    "action": "Deploy Mobile Disaster Recovery Unit",
    "status": "Proposed",
    "svi_score": 98.0,
    "no_internet_pct": 19.5,
    "rationale": "Desha County, AR: 98.0 SVI, 19.5% no internet, 2 major severe storm declarations in Lower Mississippi River basin"
  },
  {
    "county_id": "geoId/28011",
    "county_name": "Bolivar County, MS",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "priority_tier": "Tier 1 - Immediate",
    "assigned_team_id": "beacon/team/dispatch_gulf_bravo",
    "added_by": "FEMA Region IV & Beacon AI Agent",
    "action": "Deploy Mobile Disaster Recovery Unit",
    "status": "Approved",
    "svi_score": 98.7,
    "no_internet_pct": 16.8,
    "rationale": "Bolivar County, MS: 98.7 SVI, 3,378 registrations, 16.8% no internet & 10.1% no vehicle in Mississippi Delta corridor"
  },
  {
    "county_id": "geoId/28083",
    "county_name": "Leflore County, MS",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "priority_tier": "Tier 1 - Immediate",
    "assigned_team_id": "beacon/team/dispatch_gulf_bravo",
    "added_by": "FEMA Region IV & Beacon AI Agent",
    "action": "Deploy Mobile Disaster Recovery Unit",
    "status": "Proposed",
    "svi_score": 98.2,
    "no_internet_pct": 22.1,
    "rationale": "Leflore County, MS: 98.2 SVI, 5,272 registrations across 2 disasters, 22.1% no internet & 14.7% no vehicle"
  },
  {
    "county_id": "geoId/28151",
    "county_name": "Washington County, MS",
    "state_code": "MS",
    "fema_region": "Region IV (Southeast)",
    "priority_tier": "Tier 1 - Immediate",
    "assigned_team_id": "beacon/team/dispatch_gulf_bravo",
    "added_by": "FEMA Region IV & Beacon AI Agent",
    "action": "Deploy Mobile Disaster Recovery Unit",
    "status": "Approved",
    "svi_score": 99.0,
    "no_internet_pct": 17.9,
    "rationale": "Washington County, MS: 99.1 SVI, 5,558 disaster registrations across 3 declarations, 17.9% no internet & 11.9% no vehicle"
  },
  {
    "county_id": "geoId/12065",
    "county_name": "Jefferson County, FL",
    "state_code": "FL",
    "fema_region": "Region IV (Southeast)",
    "priority_tier": "Tier 1 - Immediate",
    "assigned_team_id": "beacon/team/dispatch_hhs_delta",
    "added_by": "HHS ASPR & FEMA Region IV",
    "action": "Deploy Mobile Health & Comms Unit",
    "status": "Approved",
    "svi_score": 97.9,
    "no_internet_pct": 20.7,
    "rationale": "Jefferson County, FL: 97.9 SVI, 3,283 registrations across 4 hurricanes (Idalia, Debby, Helene), 20.7% no internet"
  },
  {
    "county_id": "geoId/13141",
    "county_name": "Hancock County, GA",
    "state_code": "GA",
    "fema_region": "Region IV (Southeast)",
    "priority_tier": "Tier 1 - Immediate",
    "assigned_team_id": "beacon/team/dispatch_hhs_delta",
    "added_by": "HHS ASPR & FEMA Region IV",
    "action": "Deploy Mobile Health & Comms Unit",
    "status": "Proposed",
    "svi_score": 98.3,
    "no_internet_pct": 26.5,
    "rationale": "Hancock County, GA: 98.3 SVI, 26.5% households without internet, 27.4% seniors 65+, 1,024 Hurricane Helene registrations"
  },
  {
    "county_id": "geoId/13301",
    "county_name": "Warren County, GA",
    "state_code": "GA",
    "fema_region": "Region IV (Southeast)",
    "priority_tier": "Tier 1 - Immediate",
    "assigned_team_id": "beacon/team/dispatch_hhs_delta",
    "added_by": "HHS ASPR & FEMA Region IV",
    "action": "Deploy Mobile Health & Comms Unit",
    "status": "Proposed",
    "svi_score": 97.7,
    "no_internet_pct": 30.9,
    "rationale": "Warren County, GA: 97.7 SVI, 30.9% households without internet, 1,664 registrations, acute senior & disability care gap"
  },
  {
    "county_id": "geoId/01119",
    "county_name": "Sumter County, AL",
    "state_code": "AL",
    "fema_region": "Region IV (Southeast)",
    "priority_tier": "Tier 1 - Immediate",
    "assigned_team_id": "beacon/team/dispatch_se_alpha",
    "added_by": "FEMA Region IV & Beacon AI Agent",
    "action": "Deploy Mobile Disaster Recovery Unit",
    "status": "Proposed",
    "svi_score": 99.3,
    "no_internet_pct": 20.1,
    "rationale": "Sumter County, AL: 99.3 SVI, 20.1% households without internet, 13.8% without vehicle, unserved rural Black Belt disaster zone"
  },
  {
    "county_id": "geoId/21121",
    "county_name": "Knox County, KY",
    "state_code": "KY",
    "fema_region": "Region IV (Southeast)",
    "priority_tier": "Tier 2 - High Priority",
    "assigned_team_id": "beacon/team/dispatch_se_alpha",
    "added_by": "FEMA Region IV & Beacon AI Agent",
    "action": "Deploy Mobile Disaster Recovery Unit",
    "status": "Proposed",
    "svi_score": 96.7,
    "no_internet_pct": 12.1,
    "rationale": "Knox County, KY: 96.7 SVI, 29.5K residents, 3 flood/storm declarations since 2023 in Eastern Kentucky"
  },
  {
    "county_id": "geoId/21159",
    "county_name": "Martin County, KY",
    "state_code": "KY",
    "fema_region": "Region IV (Southeast)",
    "priority_tier": "Tier 1 - Immediate",
    "assigned_team_id": "beacon/team/dispatch_se_alpha",
    "added_by": "FEMA Region IV & Beacon AI Agent",
    "action": "Deploy Mobile Disaster Recovery Unit",
    "status": "Proposed",
    "svi_score": 99.9,
    "no_internet_pct": 11.5,
    "rationale": "Martin County, KY: 99.9 SVI, 3 FEMA disasters since 2023, 11.5% no internet & 14.2% no vehicle in Appalachian flood corridor"
  }
];

const BORDERLESS_LAKEHOUSE_BY_ID = {
  'geoId/21159': {
    active_hazard_alert: 'Flash Flood & Mudslide Emergency',
    cell_tower_outage_pct: 62.0,
    road_washout_status: 'KY-40 & Tug Fork Bridges Washed Out (SatCom Required)',
    sitrep_pdf_uri: 'FEMA_SitRep_KY_21159.pdf',
    sitrep_gcs_uri: 'gs://beacon-borderless-lakehouse-123456789012/field_sitreps/FEMA_SitRep_KY_21159.pdf',
    recommended_team: 'FEMA DRC Southeast',
  },
  'geoId/01119': {
    active_hazard_alert: 'Severe Tornado & Straight-Line Wind Watch',
    cell_tower_outage_pct: 54.0,
    road_washout_status: 'US-80 Corridor Debris · Rural Feeder Washout',
    sitrep_pdf_uri: 'FEMA_SitRep_AL_01119.pdf',
    sitrep_gcs_uri: 'gs://beacon-borderless-lakehouse-123456789012/field_sitreps/FEMA_SitRep_AL_01119.pdf',
    recommended_team: 'FEMA DRC Southeast',
  },
  'geoId/28151': {
    active_hazard_alert: 'Mississippi Delta Flash Flood Warning',
    cell_tower_outage_pct: 64.5,
    road_washout_status: 'US-82 Delta Causeway Partially Flooded',
    sitrep_pdf_uri: 'FEMA_SitRep_MS_28151.pdf',
    sitrep_gcs_uri: 'gs://beacon-borderless-lakehouse-123456789012/field_sitreps/FEMA_SitRep_MS_28151.pdf',
    recommended_team: 'FEMA DRC Delta',
  },
  'geoId/28053': {
    active_hazard_alert: 'Yazoo Basin Backwater Flood Alert',
    cell_tower_outage_pct: 68.0,
    road_washout_status: 'MS-14 & Rural Levee Roads Impassable',
    sitrep_pdf_uri: 'FEMA_SitRep_MS_28053.pdf',
    sitrep_gcs_uri: 'gs://beacon-borderless-lakehouse-123456789012/field_sitreps/FEMA_SitRep_MS_28053.pdf',
    recommended_team: 'FEMA DRC Delta',
  },
  'geoId/28027': {
    active_hazard_alert: 'Severe Convective Storm & Levee Seepage',
    cell_tower_outage_pct: 61.5,
    road_washout_status: 'US-49 Delta Bridge Approach Restricted',
    sitrep_pdf_uri: 'FEMA_SitRep_MS_28027.pdf',
    sitrep_gcs_uri: 'gs://beacon-borderless-lakehouse-123456789012/field_sitreps/FEMA_SitRep_MS_28027.pdf',
    recommended_team: 'FEMA DRC Delta',
  },
  'geoId/46102': {
    active_hazard_alert: 'Extreme Plains Wind & Power Outage Alert',
    cell_tower_outage_pct: 71.0,
    road_washout_status: 'BIA Hwy 27 Unpaved Access Washed Out',
    sitrep_pdf_uri: 'FEMA_SitRep_SD_46102.pdf',
    sitrep_gcs_uri: 'gs://beacon-borderless-lakehouse-123456789012/field_sitreps/FEMA_SitRep_SD_46102.pdf',
    recommended_team: 'HHS ASPR Health',
  },
  'geoId/22035': {
    active_hazard_alert: 'Mississippi River Stage Surge Warning',
    cell_tower_outage_pct: 59.0,
    road_washout_status: 'US-65 Lowland Segments Under Water',
    sitrep_pdf_uri: 'FEMA_SitRep_LA_22035.pdf',
    sitrep_gcs_uri: 'gs://beacon-borderless-lakehouse-123456789012/field_sitreps/FEMA_SitRep_LA_22035.pdf',
    recommended_team: 'FCC SatCom Gulf',
  },
  'geoId/05107': {
    active_hazard_alert: 'Delta Flash Flood & Agricultural Runoff Alert',
    cell_tower_outage_pct: 57.5,
    road_washout_status: 'AR-44 & Helena Levee Access Restricted',
    sitrep_pdf_uri: 'FEMA_SitRep_AR_05107.pdf',
    sitrep_gcs_uri: 'gs://beacon-borderless-lakehouse-123456789012/field_sitreps/FEMA_SitRep_AR_05107.pdf',
    recommended_team: 'FEMA DRC Delta',
  },
  'geoId/21025': {
    active_hazard_alert: 'North Fork Kentucky River Flood Emergency',
    cell_tower_outage_pct: 66.0,
    road_washout_status: 'KY-15 Mountain Hollow Bridges Damaged',
    sitrep_pdf_uri: 'FEMA_SitRep_KY_21025.pdf',
    sitrep_gcs_uri: 'gs://beacon-borderless-lakehouse-123456789012/field_sitreps/FEMA_SitRep_KY_21025.pdf',
    recommended_team: 'FEMA DRC Southeast',
  },
  'geoId/37155': {
    active_hazard_alert: 'Lumber River Tropical Basin Flood Warning',
    cell_tower_outage_pct: 52.0,
    road_washout_status: 'I-95 Lowland Exits & NC-72 Flooded',
    sitrep_pdf_uri: 'FEMA_SitRep_NC_37155.pdf',
    sitrep_gcs_uri: 'gs://beacon-borderless-lakehouse-123456789012/field_sitreps/FEMA_SitRep_NC_37155.pdf',
    recommended_team: 'FEMA DRC Southeast',
  },
};

const DRILL_DIMENSIONS = [
  { key: 'county_name', label: 'U.S. County (Priority Zones)' },
  { key: 'fema_region', label: 'FEMA Region' },
  { key: 'state_name', label: 'U.S. State' },
  { key: 'coverage_status', label: 'Mobile DRC Coverage (Spanner Graph)' },
  { key: 'recommended_team', label: 'Assigned Federal Response Team' },
];

const DRILL_METRICS = [
  { key: 'social_vulnerability_score', label: 'Social Vulnerability Score (SVI)', format: 'decimal1', agg: 'avg' },
  { key: 'no_internet_pct', label: 'Household Digital Divide (No Internet %)', format: 'decimal1', agg: 'avg' },
  { key: 'cell_tower_outage_pct', label: 'Iceberg Cell Tower Outage (%)', format: 'decimal1', agg: 'avg' },
  { key: 'poverty_pct', label: 'County Poverty Rate (%)', format: 'decimal1', agg: 'avg' },
  { key: 'age_65_plus_pct', label: 'Seniors 65+ Share (%)', format: 'decimal1', agg: 'avg' },
  { key: 'no_vehicle_pct', label: 'Households Without Vehicle (%)', format: 'decimal1', agg: 'avg' },
  { key: 'nri_risk_score', label: 'FEMA National Risk Index (NRI)', format: 'decimal1', agg: 'avg' },
  { key: 'flood_risk_score', label: 'Flood Hazard Risk Score', format: 'decimal1', agg: 'avg' },
  { key: 'hurricane_risk_score', label: 'Hurricane Hazard Risk Score', format: 'decimal1', agg: 'avg' },
  { key: 'web_registration_pct', label: 'Online FEMA Intake Share (%)', format: 'decimal1', agg: 'avg' },
  { key: 'total_registrations', label: 'FEMA Disaster Registrations', format: 'int', agg: 'sum' },
  { key: 'population', label: 'Resident Population (Census ACS)', format: 'int', agg: 'sum' },
];

const INITIAL_STATE = {
  activeTab: 'overview',
  selectedRegion: 'All',
  selectedCounty: 'All',
  minSviScore: 75,
  federalGrantM: 250,
  dispatchFilter: 'All',
  approveAllDispatches: false,
  tileDrills: {},
};

export class BeaconDisasterReadiness extends DataApp {
  static properties = {
    activeTab: { type: String },
    selectedRegion: { type: String },
    selectedCounty: { type: String },
    minSviScore: { type: Number },
    federalGrantM: { type: Number },
    dispatchFilter: { type: String },
    approveAllDispatches: { type: Boolean },
    tileDrills: { type: Object },
    contextMenu: { type: Object },
  };

  constructor() {
    super();
    this.lookerModel = 'faa';
    this.explore = 'airports';
    this.activeTab = INITIAL_STATE.activeTab;
    this.selectedRegion = INITIAL_STATE.selectedRegion;
    this.selectedCounty = INITIAL_STATE.selectedCounty;
    this.minSviScore = INITIAL_STATE.minSviScore;
    this.federalGrantM = INITIAL_STATE.federalGrantM;
    this.dispatchFilter = INITIAL_STATE.dispatchFilter;
    this.approveAllDispatches = INITIAL_STATE.approveAllDispatches;
    this.tileDrills = {};
    this.contextMenu = null;
  }

  connectedCallback() {
    super.connectedCallback();
    this._closeMenuHandler = () => {
      if (this.contextMenu) this.contextMenu = null;
    };
    this._escMenuHandler = (e) => {
      if (e.key === 'Escape' && this.contextMenu) {
        this.contextMenu = null;
      }
    };
    window.addEventListener('click', this._closeMenuHandler);
    window.addEventListener('keydown', this._escMenuHandler);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    if (this._closeMenuHandler) window.removeEventListener('click', this._closeMenuHandler);
    if (this._escMenuHandler) window.removeEventListener('keydown', this._escMenuHandler);
  }

  pushStateChange(patch) {
    Object.assign(this, patch);
    this.requestUpdate();
  }

  applyScenario(minSvi, grantM, region = 'All') {
    this.minSviScore = minSvi;
    this.federalGrantM = grantM;
    this.selectedRegion = region;
    this.selectedCounty = 'All';
    this.requestUpdate();
  }

  handleTileContextMenu(e, tileId, tileTitle, defaultSourceField = 'county_name', defaultMetric = 'social_vulnerability_score') {
    e.preventDefault();
    e.stopPropagation();

    let targetVal = null;
    let sourceField = defaultSourceField;
    const activeDrill = (this.tileDrills || {})[tileId];
    if (activeDrill?.dimension) {
      sourceField = activeDrill.dimension;
    }

    const path = e.composedPath ? e.composedPath() : [e.target];
    for (const el of path) {
      if (!el || !el.textContent) continue;
      const txt = el.textContent.trim();
      if (!txt || txt.length > 70) continue;

      const matchedCounty = US_DISASTER_COUNTIES.find(
        c => txt === c.county_name || txt.includes(c.county_name)
      );
      if (matchedCounty) {
        targetVal = matchedCounty.county_name;
        sourceField = 'county_name';
        break;
      }
      const matchedRegion = ['Region IV (Southeast)', 'Region VI (South Central)', 'Region IX (Pacific)', 'Region VIII (Mountain)', 'Region II (NY/NJ/PR)', 'Region III (Mid-Atlantic)'].find(
        r => txt === r || txt.includes(r)
      );
      if (matchedRegion) {
        targetVal = matchedRegion;
        sourceField = 'fema_region';
        break;
      }
    }

    const menuWidth = 280;
    const menuHeight = 360;
    const x = Math.min(e.clientX, Math.max(16, window.innerWidth - menuWidth - 16));
    const y = Math.min(e.clientY, Math.max(16, window.innerHeight - menuHeight - 16));

    this.contextMenu = {
      x,
      y,
      tileId,
      tileTitle,
      targetVal,
      sourceField,
      defaultMetric,
    };
  }

  applyTileDrill(tileId, dimensionKey, filterField = null, filterVal = null, defaultMetric = 'social_vulnerability_score') {
    const existing = (this.tileDrills || {})[tileId] || {};
    const nextDrills = {
      ...(this.tileDrills || {}),
      [tileId]: {
        dimension: dimensionKey || existing.dimension || 'county_name',
        metric: existing.metric || defaultMetric,
        chartType: existing.chartType || 'bar',
        filterField: filterField !== undefined ? filterField : existing.filterField,
        filterVal: filterVal !== undefined ? filterVal : existing.filterVal,
      },
    };
    this.tileDrills = nextDrills;
    this.contextMenu = null;
    this.requestUpdate();
  }

  updateTileDrillConfig(tileId, patch) {
    const existing = (this.tileDrills || {})[tileId] || {};
    this.tileDrills = {
      ...(this.tileDrills || {}),
      [tileId]: { ...existing, ...patch },
    };
    this.requestUpdate();
  }

  resetTileDrill(tileId) {
    const next = { ...(this.tileDrills || {}) };
    delete next[tileId];
    this.tileDrills = next;
    this.contextMenu = null;
    this.requestUpdate();
  }

  buildDrilledDataset(rows, dimensionKey, metricKey, filterField = null, filterVal = null) {
    let source = rows;
    if (filterField && filterVal) {
      const filtered = rows.filter(r => r[filterField] === filterVal);
      if (filtered.length > 0) source = filtered;
    }

    const metricDef = DRILL_METRICS.find(m => m.key === metricKey) || DRILL_METRICS[0];
    const groups = new Map();

    for (const r of source) {
      const key = String(r[dimensionKey] || 'Unspecified');
      if (!groups.has(key)) {
        groups.set(key, { sum: 0, count: 0 });
      }
      const g = groups.get(key);
      const val = Number(r[metricDef.key] || 0);
      g.sum += val;
      g.count += 1;
    }

    const out = [];
    for (const [key, g] of groups.entries()) {
      const rawVal = metricDef.agg === 'sum' ? g.sum : g.sum / Math.max(1, g.count);
      const rounded = metricDef.format === 'int' ? Math.round(rawVal) : Number(rawVal.toFixed(1));
      out.push({
        'beacon.group': key,
        [`beacon.${metricDef.key}`]: rounded,
      });
    }

    out.sort((a, b) => Number(b[`beacon.${metricDef.key}`] || 0) - Number(a[`beacon.${metricDef.key}`] || 0));
    return out.slice(0, 8);
  }

  renderDrillOverlayOrDefault(tileId, tileTitle, sourceRows, defaultTemplate, defaultMetric = 'social_vulnerability_score') {
    const drill = (this.tileDrills || {})[tileId];
    if (!drill) return defaultTemplate;

    const dimDef = DRILL_DIMENSIONS.find(d => d.key === drill.dimension) || DRILL_DIMENSIONS[0];
    const metricDef = DRILL_METRICS.find(m => m.key === (drill.metric || defaultMetric)) || DRILL_METRICS[0];
    const chartType = drill.chartType || 'bar';
    const drilledRows = this.buildDrilledDataset(
      sourceRows,
      dimDef.key,
      metricDef.key,
      drill.filterField,
      drill.filterVal
    );

    return html`
      <div class="drill-active-banner">
        <div class="drill-banner-left">
          <span class="drill-badge">DRILLED</span>
          <span class="drill-summary">
            By <strong>${dimDef.label}</strong>
            ${drill.filterVal ? html` · Filtered to <strong>${drill.filterVal}</strong>` : nothing}
          </span>
        </div>
        <div class="drill-banner-controls">
          <select
            class="drill-mini-select"
            .value=${dimDef.key}
            @change=${e => this.updateTileDrillConfig(tileId, { dimension: e.target.value })}>
            ${DRILL_DIMENSIONS.map(d => html`<option value=${d.key} ?selected=${d.key === dimDef.key}>By: ${d.label}</option>`)}
          </select>
          <select
            class="drill-mini-select"
            .value=${metricDef.key}
            @change=${e => this.updateTileDrillConfig(tileId, { metric: e.target.value })}>
            ${DRILL_METRICS.map(m => html`<option value=${m.key} ?selected=${m.key === metricDef.key}>Metric: ${m.label}</option>`)}
          </select>
          <div class="drill-type-group">
            ${['bar', 'column', 'line', 'pie'].map(t => html`
              <button
                class="drill-type-btn ${chartType === t ? 'active' : ''}"
                @click=${() => this.updateTileDrillConfig(tileId, { chartType: t })}>
                ${t.toUpperCase()}
              </button>
            `)}
          </div>
          <button class="drill-reset-btn" @click=${() => this.resetTileDrill(tileId)}>
            ↺ Reset
          </button>
        </div>
      </div>
      <app-chart
        bare
        type=${chartType}
        height="270px"
        value-format=${metricDef.format}
        .data=${drilledRows}
        .options=${{
          chart: { backgroundColor: '#FFFFFF', style: { fontFamily: '"Google Sans", "Inter", sans-serif' } },
          title: { text: null },
          colors: ['#0A3161', '#D92B3A', '#1A73E8'],
          plotOptions: { bar: { borderRadius: 6 }, column: { borderRadius: 6 } },
        }}
      ></app-chart>
    `;
  }

  getSimulatedCounties() {
    const grantFactor = this.federalGrantM / 250;
    const unservedRanked = [...US_DISASTER_COUNTIES]
      .filter(c => !c.has_team_coverage)
      .sort((a, b) => b.social_vulnerability_score - a.social_vulnerability_score);
    const newlyCoveredUnits = Math.min(unservedRanked.length, Math.round(this.federalGrantM / 25));
    const newlyCoveredIds = new Set(unservedRanked.slice(0, newlyCoveredUnits).map(c => c.county_id));

    return US_DISASTER_COUNTIES.map(c => {
      const fipsNum = String(c.county_id).replace('geoId/', '');
      const lakehouse = BORDERLESS_LAKEHOUSE_BY_ID[c.county_id] || {
        active_hazard_alert: c.flood_risk_score >= 80
          ? 'Riverine & Flash Flood Watch'
          : c.hurricane_risk_score >= 80
          ? 'Tropical Cyclone & Storm Surge Advisory'
          : 'Severe Weather & Grid Resilience Watch',
        cell_tower_outage_pct: Number(Math.min(72, Math.max(18, c.no_internet_pct * 1.85 + 12)).toFixed(1)),
        road_washout_status: c.no_vehicle_pct >= 12
          ? 'Secondary County Bridges & Rural Feeders Restricted'
          : 'Primary Federal Highway Corridor Open · Local Detours',
        sitrep_pdf_uri: `FEMA_SitRep_${c.state_code}_${fipsNum}.pdf`,
        sitrep_gcs_uri: `gs://beacon-borderless-lakehouse-123456789012/field_sitreps/FEMA_SitRep_${c.state_code}_${fipsNum}.pdf`,
        recommended_team: c.fema_region.includes('Southeast')
          ? 'FEMA DRC Southeast'
          : c.fema_region.includes('South Central')
          ? 'FEMA DRC Delta'
          : 'HHS ASPR Health',
      };

      const isHighVulnerability = c.social_vulnerability_score >= this.minSviScore;
      const internetBoost = isHighVulnerability
        ? Math.min(c.no_internet_pct * 0.42, 6.2 * grantFactor)
        : Math.min(c.no_internet_pct * 0.15, 1.8 * grantFactor);
      const simulatedNoInternet = Number(Math.max(2.5, c.no_internet_pct - internetBoost).toFixed(1));
      const sviRelief = isHighVulnerability ? Number((4.8 * grantFactor).toFixed(1)) : Number((1.2 * grantFactor).toFixed(1));
      const simulatedSvi = Number(Math.max(25.0, c.social_vulnerability_score - sviRelief).toFixed(1));
      const webBoost = isHighVulnerability ? Number((7.4 * grantFactor).toFixed(1)) : Number((2.1 * grantFactor).toFixed(1));
      const simulatedWebPct = Number(Math.min(96.0, c.web_registration_pct + webBoost).toFixed(1));
      const isNewlyCovered = newlyCoveredIds.has(c.county_id);
      const simulatedCoverage = c.has_team_coverage || isNewlyCovered;
      const cellRelief = (isNewlyCovered || isHighVulnerability) ? Number((16.5 * grantFactor).toFixed(1)) : Number((4.5 * grantFactor).toFixed(1));
      const simulatedCellOutage = Number(Math.max(5.0, lakehouse.cell_tower_outage_pct - cellRelief).toFixed(1));

      return {
        ...c,
        ...lakehouse,
        county_short_label: `${c.county_name}`,
        simulated_no_internet_pct: simulatedNoInternet,
        simulated_svi_score: simulatedSvi,
        simulated_web_pct: simulatedWebPct,
        simulated_cell_outage_pct: simulatedCellOutage,
        is_newly_covered: isNewlyCovered,
        simulated_coverage_status: simulatedCoverage
          ? (c.has_team_coverage ? 'Covered (Spanner Active)' : 'Covered (Simulated Grant DRC)')
          : 'Unserved Gap (Needs DRC)',
      };
    });
  }

  getFilteredCounties() {
    const all = this.getSimulatedCounties();
    const matches = all.filter(c => {
      if (this.selectedRegion !== 'All' && c.fema_region !== this.selectedRegion) return false;
      if (this.selectedCounty !== 'All' && c.county_name !== this.selectedCounty) return false;
      if (c.social_vulnerability_score < this.minSviScore) return false;
      return true;
    });
    return matches.length > 0 ? matches : all;
  }

  computeAggregates(counties) {
    const list = counties.length > 0 ? counties : this.getSimulatedCounties();
    const totalPop = list.reduce((acc, c) => acc + c.population, 0);
    const totalRegistrations = list.reduce((acc, c) => acc + c.total_registrations, 0);
    const avgSvi = list.reduce((acc, c) => acc + c.social_vulnerability_score, 0) / list.length;
    const simulatedSvi = list.reduce((acc, c) => acc + c.simulated_svi_score, 0) / list.length;
    const avgNoInternet = list.reduce((acc, c) => acc + c.no_internet_pct, 0) / list.length;
    const simulatedNoInternet = list.reduce((acc, c) => acc + c.simulated_no_internet_pct, 0) / list.length;
    const avgWebPct = list.reduce((acc, c) => acc + c.web_registration_pct, 0) / list.length;
    const simulatedWebPct = list.reduce((acc, c) => acc + c.simulated_web_pct, 0) / list.length;
    const avgCellOutage = list.reduce((acc, c) => acc + c.cell_tower_outage_pct, 0) / list.length;
    const simulatedCellOutage = list.reduce((acc, c) => acc + c.simulated_cell_outage_pct, 0) / list.length;
    const unservedCount = list.filter(c => !c.has_team_coverage).length;
    const newlyCoveredCount = list.filter(c => c.is_newly_covered).length;
    const remainingUnserved = Math.max(0, unservedCount - newlyCoveredCount);

    return {
      totalPop,
      totalRegistrations,
      avgSvi,
      simulatedSvi,
      avgNoInternet,
      simulatedNoInternet,
      avgWebPct,
      simulatedWebPct,
      avgCellOutage,
      simulatedCellOutage,
      unservedCount,
      newlyCoveredCount,
      remainingUnserved,
      countyCount: list.length,
    };
  }

  renderUsFlagEmblem() {
    return html`
      <svg class="us-flag-svg" viewBox="0 0 38 24" width="28" height="18" aria-label="United States Flag">
        <rect width="38" height="24" rx="4" fill="#FFFFFF" />
        <rect y="0" width="38" height="1.85" fill="#B31942" />
        <rect y="3.7" width="38" height="1.85" fill="#B31942" />
        <rect y="7.4" width="38" height="1.85" fill="#B31942" />
        <rect y="11.1" width="38" height="1.85" fill="#B31942" />
        <rect y="14.8" width="38" height="1.85" fill="#B31942" />
        <rect y="18.5" width="38" height="1.85" fill="#B31942" />
        <rect y="22.15" width="38" height="1.85" fill="#B31942" />
        <rect width="16" height="12.95" rx="2" fill="#0A3161" />
        <g fill="#FFFFFF">
          <circle cx="3.2" cy="2.6" r="0.85" />
          <circle cx="6.4" cy="2.6" r="0.85" />
          <circle cx="9.6" cy="2.6" r="0.85" />
          <circle cx="12.8" cy="2.6" r="0.85" />
          <circle cx="4.8" cy="5.1" r="0.85" />
          <circle cx="8.0" cy="5.1" r="0.85" />
          <circle cx="11.2" cy="5.1" r="0.85" />
          <circle cx="3.2" cy="7.6" r="0.85" />
          <circle cx="6.4" cy="7.6" r="0.85" />
          <circle cx="9.6" cy="7.6" r="0.85" />
          <circle cx="12.8" cy="7.6" r="0.85" />
          <circle cx="4.8" cy="10.1" r="0.85" />
          <circle cx="8.0" cy="10.1" r="0.85" />
          <circle cx="11.2" cy="10.1" r="0.85" />
        </g>
      </svg>
    `;
  }

  renderKpiWaveSvg(values, strokeColor, fillId, startColor, endColor) {
    const nums = (values || []).map(v => Number(v || 0));
    if (nums.length < 2) return nothing;
    const min = Math.min(...nums);
    const max = Math.max(...nums);
    const range = Math.max(max - min, 0.0001);
    const width = 260;
    const height = 46;
    const padX = 6;
    const padY = 7;
    const usableW = width - padX * 2;
    const usableH = height - padY * 2;

    const pts = nums.map((val, idx) => {
      const x = padX + (idx / (nums.length - 1)) * usableW;
      const y = padY + usableH - ((val - min) / range) * usableH;
      return [Number(x.toFixed(1)), Number(y.toFixed(1))];
    });

    let d = `M ${pts[0][0]} ${pts[0][1]}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const [x0, y0] = pts[i];
      const [x1, y1] = pts[i + 1];
      const cx = Number(((x0 + x1) / 2).toFixed(1));
      d += ` C ${cx} ${y0}, ${cx} ${y1}, ${x1} ${y1}`;
    }
    const areaD = `${d} L ${pts[pts.length - 1][0]} ${height} L ${pts[0][0]} ${height} Z`;
    const [lastX, lastY] = pts[pts.length - 1];

    return html`
      <svg class="m3-kpi-wave" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
        <defs>
          <linearGradient id=${fillId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color=${startColor} stop-opacity="0.24" />
            <stop offset="100%" stop-color=${endColor} stop-opacity="0.0" />
          </linearGradient>
        </defs>
        <path d=${areaD} fill="url(#${fillId})" />
        <path d=${d} fill="none" stroke=${strokeColor} stroke-width="2.5" stroke-linecap="round" />
        <circle cx=${lastX} cy=${lastY} r="4" fill="#FFFFFF" stroke=${strokeColor} stroke-width="2.5" />
      </svg>
    `;
  }

  renderContextMenu() {
    if (!this.contextMenu) return nothing;
    const { x, y, tileId, tileTitle, targetVal, sourceField, defaultMetric } = this.contextMenu;
    const currentDrill = (this.tileDrills || {})[tileId];

    return html`
      <div
        class="looker-context-menu"
        style="left: ${x}px; top: ${y}px;"
        @click=${e => e.stopPropagation()}>
        <div class="context-menu-header">
          <div class="context-menu-eyebrow">Interactive Drill</div>
          <div class="context-menu-title">${tileTitle}</div>
          ${targetVal ? html`<div class="context-menu-focus">Focus: <strong>${targetVal}</strong></div>` : nothing}
        </div>
        <div class="context-menu-section">
          <div class="context-menu-section-label">Slice & Group By</div>
          ${DRILL_DIMENSIONS.map(d => html`
            <button
              class="context-menu-item"
              @click=${() => this.applyTileDrill(tileId, d.key, targetVal ? sourceField : null, targetVal, defaultMetric)}>
              <span class="context-item-icon">⬡</span>
              <span>Drill by <strong>${d.label}</strong></span>
            </button>
          `)}
        </div>
        ${targetVal && sourceField === 'county_name' ? html`
          <div class="context-menu-divider"></div>
          <div class="context-menu-section">
            <button
              class="context-menu-item highlight"
              @click=${() => {
                this.selectedCounty = targetVal;
                this.contextMenu = null;
                this.requestUpdate();
              }}>
              <span class="context-item-icon">🎯</span>
              <span>Focus App on <strong>${targetVal}</strong></span>
            </button>
          </div>
        ` : nothing}
        ${currentDrill ? html`
          <div class="context-menu-divider"></div>
          <div class="context-menu-section">
            <button class="context-menu-item danger" @click=${() => this.resetTileDrill(tileId)}>
              <span class="context-item-icon">↺</span>
              <span>Reset Tile to Default View</span>
            </button>
          </div>
        ` : nothing}
      </div>
    `;
  }

  render() {
    const filtered = this.getFilteredCounties();
    const agg = this.computeAggregates(filtered);

    const regions = ['All', ...new Set(US_DISASTER_COUNTIES.map(c => c.fema_region))];
    const countiesInRegion = this.selectedRegion === 'All'
      ? US_DISASTER_COUNTIES
      : US_DISASTER_COUNTIES.filter(c => c.fema_region === this.selectedRegion);

    const baseChartOptions = {
      chart: {
        backgroundColor: '#FFFFFF',
        animation: { duration: 320 },
        style: { fontFamily: '"Google Sans", "Plus Jakarta Sans", "Inter", sans-serif' },
      },
      title: { text: null },
      xAxis: {
        gridLineColor: '#EEF3FB',
        lineColor: '#DCE6F7',
        tickColor: '#DCE6F7',
        labels: { style: { color: '#1B2234', fontSize: '11.5px', fontWeight: '600' } },
      },
      yAxis: {
        gridLineColor: '#EEF3FB',
        labels: { style: { color: '#5A657D', fontSize: '11px', fontWeight: '500' } },
      },
      legend: {
        itemStyle: { color: '#1B2234', fontSize: '12px', fontWeight: '600' },
      },
    };

    // Top 7 Unserved Priority Counties (Horizontal Bars = zero rotated text!)
    const topUnservedCounties = [...filtered]
      .filter(c => !c.has_team_coverage)
      .sort((a, b) => b.social_vulnerability_score - a.social_vulnerability_score)
      .slice(0, 7);

    const unservedChartData = topUnservedCounties.map(c => ({
      'beacon.county': c.county_name,
      'beacon.baseline_svi': c.social_vulnerability_score,
      'beacon.with_grant_svi': c.simulated_svi_score,
    }));

    // Top 3 Unserved Priority Counties for the Borderless Lakehouse Field SitRep Spotlight
    const spotlightSitrepCounties = [...topUnservedCounties].sort((a, b) => (BORDERLESS_LAKEHOUSE_BY_ID[b.county_id] ? 1 : 0) - (BORDERLESS_LAKEHOUSE_BY_ID[a.county_id] ? 1 : 0)).slice(0, 3);

    // FEMA Regional Intake Channel Mix (Clean horizontal stacked bars)
    const regionGroups = new Map();
    for (const c of filtered) {
      if (!regionGroups.has(c.fema_region)) {
        regionGroups.set(c.fema_region, { webSum: 0, callSum: 0, count: 0 });
      }
      const g = regionGroups.get(c.fema_region);
      g.webSum += c.simulated_web_pct;
      g.callSum += Number((100 - c.simulated_web_pct).toFixed(1));
      g.count += 1;
    }
    const regionalChannelMix = Array.from(regionGroups.entries()).map(([region, g]) => ({
      'beacon.fema_region': region.replace('Region ', 'Reg '),
      'beacon.online_web_intake_pct': Number((g.webSum / g.count).toFixed(1)),
      'beacon.phone_call_center_pct': Number((g.callSum / g.count).toFixed(1)),
    }));

    // Top 7 Counties for Borderless Lakehouse Cell Outage vs Digital Divide
    const topLakehouseCounties = [...filtered]
      .sort((a, b) => b.cell_tower_outage_pct - a.cell_tower_outage_pct)
      .slice(0, 7);

    const lakehouseChartData = topLakehouseCounties.map(c => ({
      'beacon.county': c.county_name,
      'beacon.iceberg_cell_outage_pct': c.cell_tower_outage_pct,
      'beacon.simulated_cell_outage_pct': c.simulated_cell_outage_pct,
    }));

    // Top 7 Counties by Flood & Hurricane Hazard Risk
    const topHazardCounties = [...filtered]
      .sort((a, b) => (b.flood_risk_score + b.hurricane_risk_score) - (a.flood_risk_score + a.hurricane_risk_score))
      .slice(0, 7);

    const hazardChartData = topHazardCounties.map(c => ({
      'beacon.county': c.county_name,
      'beacon.flood_risk_score': c.flood_risk_score,
      'beacon.hurricane_risk_score': c.hurricane_risk_score,
    }));

    // Federal Budget by Policy Pillar (Donut)
    const pillarMap = new Map();
    for (const p of US_FEDERAL_PROGRAMS) {
      pillarMap.set(p.policy_pillar, (pillarMap.get(p.policy_pillar) || 0) + p.annual_budget_million_usd);
    }
    const budgetByPillar = Array.from(pillarMap.entries()).map(([pillar, budget]) => ({
      'beacon.policy_pillar': pillar,
      'beacon.annual_budget_million_usd': Number(budget.toFixed(0)),
    }));

    // Clean Macro Timeline (Recent points from 2005-2025 for breathable x-axis)
    const recentDisasterTimeline = US_MACRO_TIMELINE
      .filter(r => r.year >= 2005 && r.year % 2 === 1)
      .map(r => ({
        'beacon.year': String(r.year),
        'beacon.disaster_losses_billion_usd': r.billion_dollar_disasters_loss_usd_b,
      }));

    // Spanner System of Action Dispatches enriched with Borderless Lakehouse fields
    const dynamicDispatches = US_DEPLOYMENT_PLAN.map(d => {
      const fipsNum = String(d.county_id).replace('geoId/', '');
      const lake = BORDERLESS_LAKEHOUSE_BY_ID[d.county_id] || {
        active_hazard_alert: 'Severe Weather & Flood Watch',
        cell_tower_outage_pct: 48.0,
        road_washout_status: 'Secondary County Routes Restricted',
        sitrep_pdf_uri: `FEMA_SitRep_${d.state_code}_${fipsNum}.pdf`,
        sitrep_gcs_uri: `gs://beacon-borderless-lakehouse-123456789012/field_sitreps/FEMA_SitRep_${d.state_code}_${fipsNum}.pdf`,
        recommended_team: 'FEMA DRC Southeast',
      };
      return {
        ...d,
        ...lake,
        status: this.approveAllDispatches ? 'Active (Dispatched)' : d.status,
      };
    }).filter(d => {
      if (this.selectedRegion !== 'All' && d.fema_region !== this.selectedRegion) return false;
      if (this.dispatchFilter !== 'All' && d.status !== this.dispatchFilter) return false;
      return true;
    });

    const divideSavedPts = Number((agg.avgNoInternet - agg.simulatedNoInternet).toFixed(1));
    const webGainPts = Number((agg.simulatedWebPct - agg.avgWebPct).toFixed(1));

    // Smooth wave series for the 3 breathable M3 KPI cards
    const unservedWave = [14, 13, 12, 11, 10, 9, Math.max(1, agg.remainingUnserved)];
    const divideWave = [24.2, 23.5, 22.8, 22.1, 21.4, 20.8, agg.simulatedNoInternet];
    const webWave = [51.0, 52.4, 53.8, 55.2, 56.8, 58.1, agg.simulatedWebPct];

    return html`
      <style>
      .app-shell-root {
        display: block;
        min-height: 100vh;
        background: radial-gradient(circle at 12% 0%, #EEF4FF 0%, #F6F8FD 48%, #FFF6F8 100%);
        color: #1B2234;
        font-family: 'Google Sans', 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        --m3-navy: #0A3161;
        --m3-navy-soft: #EAF1FF;
        --m3-red: #D92B3A;
        --m3-red-soft: #FFEBEF;
        --m3-blue: #1A73E8;
        --m3-blue-soft: #E8F1FE;
        --m3-teal: #0D7A5F;
        --m3-teal-soft: #E5F6F0;
        --m3-surface: #FFFFFF;
        --m3-outline: #E3EBF6;
        --m3-text: #1B2234;
        --m3-muted: #5A657D;
      }

      .app-shell {
        max-width: 1480px;
        margin: 0 auto;
        padding: 28px 36px 56px;
        display: flex;
        flex-direction: column;
        gap: 24px;
      }

      /* Soft M3 x Headspace Hero Header Card */
      .m3-hero-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F1F6FF 55%, #FFF2F5 100%);
        border: 1px solid #DCE6F7;
        border-radius: 28px;
        padding: 24px 30px;
        box-shadow: 0 12px 32px rgba(10, 49, 97, 0.05);
        display: flex;
        flex-direction: column;
        gap: 20px;
      }

      .m3-hero-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
        flex-wrap: wrap;
      }

      .m3-brand-cluster {
        display: flex;
        align-items: center;
        gap: 16px;
      }

      .m3-flag-pill {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 8px 14px;
        border-radius: 999px;
        background: #FFFFFF;
        border: 1px solid #D7E3F8;
        box-shadow: 0 4px 12px rgba(10, 49, 97, 0.06);
        font-size: 12px;
        font-weight: 700;
        color: var(--m3-navy);
        letter-spacing: 0.02em;
      }

      .us-flag-svg {
        border-radius: 4px;
        box-shadow: 0 1px 4px rgba(10, 49, 97, 0.18);
      }

      .m3-title-group h1 {
        margin: 0;
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #0A3161;
        line-height: 1.2;
      }

      .m3-title-group p {
        margin: 4px 0 0;
        font-size: 14px;
        color: #526079;
        font-weight: 500;
      }

      /* M3 Pill Segmented Navigation + Soft Filter Pills */
      .m3-nav-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        flex-wrap: wrap;
        padding-top: 4px;
      }

      .m3-segmented-tabs {
        display: inline-flex;
        align-items: center;
        background: #E9EFFA;
        padding: 5px;
        border-radius: 999px;
        gap: 4px;
      }

      .m3-tab-pill {
        appearance: none;
        border: none;
        background: transparent;
        color: #42526E;
        font-family: inherit;
        font-size: 13.5px;
        font-weight: 600;
        padding: 10px 20px;
        border-radius: 999px;
        cursor: pointer;
        transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
      }

      .m3-tab-pill:hover {
        color: #0A3161;
        background: rgba(255, 255, 255, 0.55);
      }

      .m3-tab-pill.active {
        background: #0A3161;
        color: #FFFFFF;
        box-shadow: 0 4px 12px rgba(10, 49, 97, 0.22);
      }

      .m3-filter-pills {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
      }

      .m3-select-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #FFFFFF;
        border: 1px solid #D7E3F8;
        border-radius: 999px;
        padding: 7px 16px;
        font-size: 13px;
        color: #34425A;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(10, 49, 97, 0.03);
      }

      .m3-select-pill span {
        color: #697791;
        font-weight: 500;
      }

      .m3-select-pill select {
        border: none;
        background: transparent;
        color: #0A3161;
        font-family: inherit;
        font-size: 13px;
        font-weight: 700;
        cursor: pointer;
        outline: none;
      }

      .m3-reset-pill {
        appearance: none;
        border: 1px solid #F5C2C7;
        background: #FFF0F3;
        color: #B31942;
        border-radius: 999px;
        padding: 8px 16px;
        font-family: inherit;
        font-size: 12.5px;
        font-weight: 700;
        cursor: pointer;
      }

      /* 3 Breathable M3 Tonal KPI Cards */
      .m3-kpi-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 22px;
      }

      .m3-kpi-card {
        border-radius: 28px;
        padding: 24px 26px 20px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        gap: 14px;
        border: 1px solid transparent;
        box-shadow: 0 10px 28px rgba(10, 49, 97, 0.04);
        transition: transform 0.2s ease;
      }

      .m3-kpi-card:hover {
        transform: translateY(-2px);
      }

      .m3-kpi-card.tone-navy {
        background: linear-gradient(180deg, #FFFFFF 0%, #F2F7FF 100%);
        border-color: #D8E6FC;
      }

      .m3-kpi-card.tone-rose {
        background: linear-gradient(180deg, #FFFFFF 0%, #FFF4F6 100%);
        border-color: #FCD8DF;
      }

      .m3-kpi-card.tone-sky {
        background: linear-gradient(180deg, #FFFFFF 0%, #EFF8FF 100%);
        border-color: #D2E9FC;
      }

      .m3-kpi-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
      }

      .m3-kpi-label {
        font-size: 14px;
        font-weight: 600;
        color: #46546E;
      }

      .m3-kpi-badge {
        display: inline-flex;
        align-items: center;
        padding: 5px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
      }

      .m3-kpi-badge.good {
        background: #E5F6F0;
        color: #0D7A5F;
      }

      .m3-kpi-badge.navy {
        background: #E7F0FE;
        color: #0A3161;
      }

      .m3-kpi-badge.crimson {
        background: #FFEBEF;
        color: #B31942;
      }

      .m3-kpi-value {
        font-size: 40px;
        font-weight: 700;
        letter-spacing: -0.03em;
        line-height: 1.05;
        color: #0A3161;
      }

      .m3-kpi-card.tone-rose .m3-kpi-value {
        color: #B31942;
      }

      .m3-kpi-caption {
        font-size: 13.5px;
        color: #5A6782;
        font-weight: 500;
      }

      .m3-kpi-wave {
        width: 100%;
        height: 46px;
        display: block;
        margin-top: 2px;
      }

      /* Effortless Headspace-Style Grant Studio Card */
      .m3-studio-card {
        background: #FFFFFF;
        border: 1px solid #E1EAF7;
        border-radius: 28px;
        padding: 26px 30px;
        box-shadow: 0 10px 30px rgba(10, 49, 97, 0.04);
        display: flex;
        flex-direction: column;
        gap: 20px;
      }

      .m3-studio-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        flex-wrap: wrap;
      }

      .m3-studio-title-wrap h2 {
        margin: 0;
        font-size: 19px;
        font-weight: 700;
        color: #0A3161;
        letter-spacing: -0.01em;
      }

      .m3-studio-title-wrap p {
        margin: 4px 0 0;
        font-size: 13.5px;
        color: #5C6982;
      }

      .m3-preset-group {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
      }

      .m3-preset-pill {
        appearance: none;
        border: 1px solid #D9E4F7;
        background: #F7FAFF;
        color: #2B3B59;
        border-radius: 999px;
        padding: 9px 18px;
        font-family: inherit;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.18s ease;
      }

      .m3-preset-pill:hover {
        background: #EDF3FF;
        border-color: #B8CEF5;
      }

      .m3-preset-pill.active {
        background: #0A3161;
        border-color: #0A3161;
        color: #FFFFFF;
        box-shadow: 0 4px 12px rgba(10, 49, 97, 0.18);
      }

      .m3-sliders-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 20px;
      }

      .m3-slider-pod {
        border-radius: 22px;
        padding: 18px 22px;
        display: flex;
        flex-direction: column;
        gap: 10px;
      }

      .m3-slider-pod.pod-navy {
        background: #F5F9FF;
        border: 1px solid #DCE8FC;
      }

      .m3-slider-pod.pod-rose {
        background: #FFF6F8;
        border: 1px solid #FBDCE3;
      }

      .m3-slider-row {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 12px;
      }

      .m3-slider-name {
        font-size: 14px;
        font-weight: 700;
        color: #1F2B44;
      }

      .m3-slider-readout {
        font-size: 18px;
        font-weight: 700;
        color: #0A3161;
      }

      .m3-slider-pod.pod-rose .m3-slider-readout {
        color: #B31942;
      }

      .m3-range {
        width: 100%;
        height: 8px;
        border-radius: 999px;
        accent-color: #0A3161;
        cursor: pointer;
      }

      .m3-slider-pod.pod-rose .m3-range {
        accent-color: #D92B3A;
      }

      .m3-slider-hint {
        font-size: 12.5px;
        color: #5D6A82;
        display: flex;
        justify-content: space-between;
      }

      /* Calm M3 Surface Cards for Charts & Tables */
      .m3-two-col {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 22px;
      }

      .m3-card {
        background: #FFFFFF;
        border: 1px solid #E2EBF7;
        border-radius: 28px;
        padding: 24px 28px;
        box-shadow: 0 10px 28px rgba(10, 49, 97, 0.04);
        display: flex;
        flex-direction: column;
        gap: 16px;
      }

      .m3-card-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
      }

      .m3-card-title {
        margin: 0;
        font-size: 17px;
        font-weight: 700;
        color: #0A3161;
        letter-spacing: -0.01em;
      }

      .m3-card-subtitle {
        margin: 4px 0 0;
        font-size: 13px;
        color: #62708A;
        font-weight: 500;
      }

      .m3-source-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border-radius: 999px;
        background: #F2F6FE;
        color: #0A3161;
        font-size: 11.5px;
        font-weight: 700;
        white-space: nowrap;
      }

      .m3-source-pill.rose {
        background: #FFF0F3;
        color: #B31942;
      }

      /* Borderless Lakehouse Field SitRep Cards (Apache Iceberg + GCS PDFs) */
      .m3-lakehouse-strip {
        background: linear-gradient(135deg, #F6FAFF 0%, #FFFFFF 55%, #FFF6F8 100%);
        border: 1px solid #DCE7F8;
        border-radius: 28px;
        padding: 24px 28px;
        display: flex;
        flex-direction: column;
        gap: 18px;
      }

      .m3-sitrep-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 18px;
      }

      .m3-sitrep-card {
        background: #FFFFFF;
        border: 1px solid #E1EBF8;
        border-radius: 22px;
        padding: 18px 20px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        box-shadow: 0 6px 18px rgba(10, 49, 97, 0.03);
      }

      .m3-sitrep-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
      }

      .m3-sitrep-county {
        font-size: 15.5px;
        font-weight: 700;
        color: #0A3161;
      }

      .m3-sitrep-svi {
        padding: 4px 10px;
        border-radius: 999px;
        background: #FFEBEF;
        color: #B31942;
        font-size: 11.5px;
        font-weight: 700;
      }

      .m3-sitrep-alert {
        font-size: 13px;
        font-weight: 600;
        color: #1F2B44;
        background: #F6F9FF;
        border-radius: 14px;
        padding: 10px 12px;
        border: 1px solid #E3ECFA;
      }

      .m3-sitrep-meta {
        display: flex;
        flex-direction: column;
        gap: 6px;
        font-size: 12.5px;
        color: #54627A;
      }

      .m3-sitrep-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        padding-top: 6px;
        border-top: 1px solid #EEF3FB;
      }

      .m3-pdf-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 11px;
        border-radius: 999px;
        background: #EEF4FF;
        color: #0A3161;
        font-size: 11.5px;
        font-weight: 700;
      }

      .m3-team-pill {
        font-size: 11.5px;
        font-weight: 700;
        color: #0D7A5F;
        background: #E5F6F0;
        padding: 4px 10px;
        border-radius: 999px;
      }

      /* Dispatch Action Button */
      .m3-action-btn {
        appearance: none;
        border: none;
        background: #D92B3A;
        color: #FFFFFF;
        font-family: inherit;
        font-size: 13px;
        font-weight: 700;
        padding: 10px 20px;
        border-radius: 999px;
        cursor: pointer;
        box-shadow: 0 6px 16px rgba(217, 43, 58, 0.24);
        transition: all 0.2s ease;
      }

      .m3-action-btn.approved {
        background: #0D7A5F;
        box-shadow: 0 6px 16px rgba(13, 122, 95, 0.24);
      }

      /* Context Menu & Drill Styles */
      .looker-context-menu {
        position: fixed;
        z-index: 9999;
        width: 280px;
        background: #FFFFFF;
        border: 1px solid #DCE6F7;
        border-radius: 20px;
        box-shadow: 0 18px 40px rgba(10, 49, 97, 0.14);
        padding: 10px;
      }

      .context-menu-header {
        padding: 8px 12px 10px;
        border-bottom: 1px solid #EEF3FB;
      }

      .context-menu-eyebrow {
        font-size: 10.5px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #B31942;
      }

      .context-menu-title {
        font-size: 13.5px;
        font-weight: 700;
        color: #0A3161;
        margin-top: 2px;
      }

      .context-menu-focus {
        font-size: 11.5px;
        color: #54627A;
        margin-top: 4px;
      }

      .context-menu-section {
        padding: 6px 0;
      }

      .context-menu-section-label {
        font-size: 11px;
        font-weight: 600;
        color: #6B7892;
        padding: 4px 12px;
      }

      .context-menu-item {
        width: 100%;
        border: none;
        background: transparent;
        text-align: left;
        padding: 8px 12px;
        border-radius: 12px;
        font-family: inherit;
        font-size: 12.5px;
        color: #1F2B44;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .context-menu-item:hover {
        background: #F1F6FF;
        color: #0A3161;
      }

      .drill-active-banner {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        flex-wrap: wrap;
        background: #F2F7FF;
        border: 1px solid #D8E6FC;
        border-radius: 16px;
        padding: 8px 14px;
      }

      .drill-badge {
        background: #0A3161;
        color: #FFFFFF;
        font-size: 10.5px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 999px;
      }

      .drill-summary {
        font-size: 12.5px;
        color: #2B3B59;
        margin-left: 8px;
      }

      .drill-banner-controls {
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
      }

      .drill-mini-select,
      .drill-type-btn,
      .drill-reset-btn {
        border: 1px solid #D5E2F7;
        background: #FFFFFF;
        color: #0A3161;
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 11.5px;
        font-weight: 600;
        cursor: pointer;
      }

      .drill-type-btn.active {
        background: #0A3161;
        color: #FFFFFF;
      }

      @media (max-width: 1100px) {
        .m3-kpi-grid,
        .m3-sliders-grid,
        .m3-two-col,
        .m3-sitrep-grid {
          grid-template-columns: 1fr;
        }
      }
      </style>
      <div class="app-shell-root">
      <div class="app-shell">
        ${this.renderContextMenu()}

        <!-- Soft Google M3 x Headspace Hero Card -->
        <header class="m3-hero-card">
          <div class="m3-hero-top">
            <div class="m3-brand-cluster">
              <div class="m3-flag-pill">
                ${this.renderUsFlagEmblem()}
                <span>U.S. Public Sector · FEMA & Census</span>
              </div>
              <div class="m3-title-group">
                <h1>Beacon Disaster Readiness</h1>
                <p>Data Commons · BigLake Apache Iceberg & GCS SitReps · Cloud Spanner Graph</p>
              </div>
            </div>

            <div class="m3-filter-pills">
              <label class="m3-select-pill">
                <span>Region</span>
                <select
                  .value=${this.selectedRegion}
                  @change=${e => this.pushStateChange({ selectedRegion: e.target.value, selectedCounty: 'All' })}>
                  ${regions.map(r => html`<option value=${r} ?selected=${r === this.selectedRegion}>${r}</option>`)}
                </select>
              </label>

              <label class="m3-select-pill">
                <span>County</span>
                <select
                  .value=${this.selectedCounty}
                  @change=${e => this.pushStateChange({ selectedCounty: e.target.value })}>
                  <option value="All">All Priority Counties (${countiesInRegion.length})</option>
                  ${countiesInRegion.map(c => html`
                    <option value=${c.county_name} ?selected=${c.county_name === this.selectedCounty}>
                      ${c.county_name}
                    </option>
                  `)}
                </select>
              </label>

              ${(this.selectedRegion !== 'All' || this.selectedCounty !== 'All' || this.minSviScore !== 75 || this.federalGrantM !== 250) ? html`
                <button class="m3-reset-pill" @click=${() => this.applyScenario(75, 250, 'All')}>
                  ↺ Reset
                </button>
              ` : nothing}
            </div>
          </div>

          <div class="m3-nav-bar">
            <nav class="m3-segmented-tabs" aria-label="Beacon Workspace Views">
              <button
                class="m3-tab-pill ${this.activeTab === 'overview' ? 'active' : ''}"
                @click=${() => this.pushStateChange({ activeTab: 'overview' })}>
                ✨ Grant Simulator
              </button>
              <button
                class="m3-tab-pill ${this.activeTab === 'vulnerability' ? 'active' : ''}"
                @click=${() => this.pushStateChange({ activeTab: 'vulnerability' })}>
                🌊 Lakehouse & SitReps
              </button>
              <button
                class="m3-tab-pill ${this.activeTab === 'action' ? 'active' : ''}"
                @click=${() => this.pushStateChange({ activeTab: 'action' })}>
                🚑 Fleet Dispatch
              </button>
            </nav>

            <div class="m3-source-pill">
              <span>⚡ Live What-If Studio · $${this.federalGrantM}M Grant Active</span>
            </div>
          </div>
        </header>

        <!-- 3 Breathable M3 Tonal Hero KPI Cards -->
        <section class="m3-kpi-grid">
          <div class="m3-kpi-card tone-navy">
            <div class="m3-kpi-top">
              <span class="m3-kpi-label">Unserved Priority Counties</span>
              <span class="m3-kpi-badge good">+${agg.newlyCoveredCount} Newly Covered</span>
            </div>
            <div class="m3-kpi-value">${agg.remainingUnserved} Counties</div>
            <div class="m3-kpi-caption">
              Down from ${agg.unservedCount} unserved counties via Spanner Graph dispatch
            </div>
            ${this.renderKpiWaveSvg(unservedWave, '#0A3161', 'm3WaveNavy', '#0A3161', '#0A3161')}
          </div>

          <div class="m3-kpi-card tone-rose">
            <div class="m3-kpi-top">
              <span class="m3-kpi-label">Household Digital Divide</span>
              <span class="m3-kpi-badge crimson">↓ -${divideSavedPts} pts with SatCom</span>
            </div>
            <div class="m3-kpi-value">${agg.simulatedNoInternet.toFixed(1)}%</div>
            <div class="m3-kpi-caption">
              Households without internet (baseline ${agg.avgNoInternet.toFixed(1)}% in Census ACS)
            </div>
            ${this.renderKpiWaveSvg(divideWave, '#D92B3A', 'm3WaveRose', '#D92B3A', '#D92B3A')}
          </div>

          <div class="m3-kpi-card tone-sky">
            <div class="m3-kpi-top">
              <span class="m3-kpi-label">Online FEMA Intake Share</span>
              <span class="m3-kpi-badge navy">↑ +${webGainPts} pts · ${agg.simulatedCellOutage.toFixed(0)}% Cell Outage</span>
            </div>
            <div class="m3-kpi-value">${agg.simulatedWebPct.toFixed(1)}%</div>
            <div class="m3-kpi-caption">
              Digital registrations as Iceberg cell outage drops from ${agg.avgCellOutage.toFixed(0)}%
            </div>
            ${this.renderKpiWaveSvg(webWave, '#1A73E8', 'm3WaveSky', '#1A73E8', '#1A73E8')}
          </div>
        </section>

        <!-- Effortless Headspace-Style Grant Studio Card -->
        <section class="m3-studio-card">
          <div class="m3-studio-header">
            <div class="m3-studio-title-wrap">
              <h2>Simulate Federal Mobile Response Grant</h2>
              <p>Adjust vulnerability focus or mobile SatCom funding to preview county coverage in real time.</p>
            </div>
            <div class="m3-preset-group">
              <button
                class="m3-preset-pill ${this.federalGrantM === 0 ? 'active' : ''}"
                @click=${() => this.applyScenario(75, 0, this.selectedRegion)}>
                Baseline · $0M
              </button>
              <button
                class="m3-preset-pill ${this.federalGrantM === 250 && this.minSviScore === 75 ? 'active' : ''}"
                @click=${() => this.applyScenario(75, 250, this.selectedRegion)}>
                ✨ FY26 Plan · $250M
              </button>
              <button
                class="m3-preset-pill ${this.federalGrantM === 500 ? 'active' : ''}"
                @click=${() => this.applyScenario(85, 500, this.selectedRegion)}>
                Full Surge · $500M
              </button>
            </div>
          </div>

          <div class="m3-sliders-grid">
            <div class="m3-slider-pod pod-navy">
              <div class="m3-slider-row">
                <span class="m3-slider-name">Social Vulnerability Focus (SVI)</span>
                <span class="m3-slider-readout">SVI ≥ ${this.minSviScore}</span>
              </div>
              <input
                class="m3-range"
                type="range"
                min="50"
                max="95"
                step="5"
                .value=${String(this.minSviScore)}
                @input=${e => this.pushStateChange({ minSviScore: Number(e.target.value) })}
              />
              <div class="m3-slider-hint">
                <span>Broad (SVI 50+)</span>
                <span>${agg.countyCount} priority counties in view</span>
                <span>Tier-1 Critical (95+)</span>
              </div>
            </div>

            <div class="m3-slider-pod pod-rose">
              <div class="m3-slider-row">
                <span class="m3-slider-name">Mobile DRC & SatCom Grant</span>
                <span class="m3-slider-readout">$${this.federalGrantM}M USD</span>
              </div>
              <input
                class="m3-range"
                type="range"
                min="0"
                max="500"
                step="25"
                .value=${String(this.federalGrantM)}
                @input=${e => this.pushStateChange({ federalGrantM: Number(e.target.value) })}
              />
              <div class="m3-slider-hint">
                <span>$0M Baseline</span>
                <span>+${agg.newlyCoveredCount} mobile units deployed</span>
                <span>$500M Surge</span>
              </div>
            </div>
          </div>
        </section>

        <main style="display: flex; flex-direction: column; gap: 24px;">
          ${this.activeTab === 'overview' ? html`
            <!-- 2 Uncluttered Horizontal Charts (Zero Rotated Diagonal Labels) -->
            <div class="m3-two-col">
              <div
                class="m3-card"
                @contextmenu=${e => this.handleTileContextMenu(e, 'unserved_bar', 'Priority Unserved Counties: Baseline vs. With Grant', 'county_name', 'social_vulnerability_score')}>
                <div class="m3-card-header">
                  <div>
                    <h3 class="m3-card-title">Priority Unserved Counties: Baseline vs. With Grant</h3>
                    <p class="m3-card-subtitle">Top 7 unserved high-SVI counties · Right-click any bar to drill</p>
                  </div>
                  <span class="m3-source-pill rose">Spanner Graph · SVI</span>
                </div>
                ${this.renderDrillOverlayOrDefault(
                  'unserved_bar',
                  'Priority Unserved Counties: Baseline vs. With Grant',
                  topUnservedCounties,
                  html`
                    <app-chart
                      bare
                      type="bar"
                      height="300px"
                      value-format="decimal1"
                      .data=${unservedChartData}
                      .options=${{
                        ...baseChartOptions,
                        colors: ['#0A3161', '#D92B3A'],
                        plotOptions: { bar: { borderRadius: 6, pointPadding: 0.12, groupPadding: 0.16 } },
                      }}
                    ></app-chart>
                  `,
                  'social_vulnerability_score'
                )}
              </div>

              <div
                class="m3-card"
                @contextmenu=${e => this.handleTileContextMenu(e, 'channel_mix', 'FEMA Intake Channel Mix by Region', 'fema_region', 'web_registration_pct')}>
                <div class="m3-card-header">
                  <div>
                    <h3 class="m3-card-title">FEMA Intake Channel Mix by Region</h3>
                    <p class="m3-card-subtitle">Online web registrations vs. phone call-center intake share (%)</p>
                  </div>
                  <span class="m3-source-pill">OpenFEMA · Census ACS</span>
                </div>
                ${this.renderDrillOverlayOrDefault(
                  'channel_mix',
                  'FEMA Intake Channel Mix by Region',
                  filtered,
                  html`
                    <app-chart
                      bare
                      type="bar"
                      height="300px"
                      value-format="decimal1"
                      .data=${regionalChannelMix}
                      .options=${{
                        ...baseChartOptions,
                        colors: ['#0A3161', '#D92B3A'],
                        plotOptions: { bar: { stacking: 'normal', borderRadius: 5, pointPadding: 0.15 } },
                      }}
                    ></app-chart>
                  `,
                  'web_registration_pct'
                )}
              </div>
            </div>

            <!-- Borderless Lakehouse Spotlight Strip (BigLake Apache Iceberg + Unstructured GCS PDFs) -->
            <section class="m3-lakehouse-strip">
              <div class="m3-card-header">
                <div>
                  <h3 class="m3-card-title">Borderless Lakehouse Live Field SitReps (Apache Iceberg × GCS PDFs)</h3>
                  <p class="m3-card-subtitle">
                    Real-time NOAA/FCC outage telemetry in BigLake Apache Iceberg paired with unstructured FEMA field PDFs in Google Cloud Storage
                  </p>
                </div>
                <span class="m3-source-pill">BigLake Iceberg · GCS SitReps</span>
              </div>

              <div class="m3-sitrep-grid">
                ${spotlightSitrepCounties.map(c => html`
                  <div class="m3-sitrep-card">
                    <div class="m3-sitrep-top">
                      <span class="m3-sitrep-county">${c.county_name}</span>
                      <span class="m3-sitrep-svi">SVI ${c.social_vulnerability_score}</span>
                    </div>
                    <div class="m3-sitrep-alert">
                      ⚡ ${c.active_hazard_alert}
                    </div>
                    <div class="m3-sitrep-meta">
                      <div><strong>Iceberg Cell Outage:</strong> ${c.cell_tower_outage_pct}% → <strong>${c.simulated_cell_outage_pct}%</strong> with SatCom</div>
                      <div><strong>FEMA PDA Road Status:</strong> ${c.road_washout_status}</div>
                    </div>
                    <div class="m3-sitrep-footer">
                      <span class="m3-pdf-pill">📄 ${c.sitrep_pdf_uri}</span>
                      <span class="m3-team-pill">🚑 ${c.recommended_team}</span>
                    </div>
                  </div>
                `)}
              </div>
            </section>
          ` : nothing}

          ${this.activeTab === 'vulnerability' ? html`
            <!-- Tab 2: Borderless Lakehouse & SitRep Explorer -->
            <section class="m3-lakehouse-strip">
              <div class="m3-card-header">
                <div>
                  <h3 class="m3-card-title">Unstructured GCS Field SitReps × BigLake Apache Iceberg Telemetry</h3>
                  <p class="m3-card-subtitle">
                    Inspect physical FEMA Preliminary Damage Assessment (PDA) PDFs stored in GCS alongside structured Apache Iceberg tables
                  </p>
                </div>
                <span class="m3-source-pill">gs://beacon-borderless-lakehouse-123456789012/field_sitreps/</span>
              </div>

              <div class="m3-sitrep-grid">
                ${spotlightSitrepCounties.map(c => html`
                  <div class="m3-sitrep-card">
                    <div class="m3-sitrep-top">
                      <span class="m3-sitrep-county">${c.county_name}</span>
                      <span class="m3-sitrep-svi">SVI ${c.social_vulnerability_score}</span>
                    </div>
                    <div class="m3-sitrep-alert">
                      ⚡ ${c.active_hazard_alert}
                    </div>
                    <div class="m3-sitrep-meta">
                      <div><strong>Iceberg Cell Outage:</strong> ${c.cell_tower_outage_pct}% (${c.simulated_cell_outage_pct}% post-grant)</div>
                      <div><strong>Road Washout Status:</strong> ${c.road_washout_status}</div>
                    </div>
                    <div class="m3-sitrep-footer">
                      <span class="m3-pdf-pill">📄 ${c.sitrep_pdf_uri}</span>
                      <span class="m3-team-pill">🚑 ${c.recommended_team}</span>
                    </div>
                  </div>
                `)}
              </div>
            </section>

            <div class="m3-two-col">
              <div
                class="m3-card"
                @contextmenu=${e => this.handleTileContextMenu(e, 'lakehouse_outage_bar', 'Iceberg Cell Tower Outage % vs. Digital Divide %', 'county_name', 'cell_tower_outage_pct')}>
                <div class="m3-card-header">
                  <div>
                    <h3 class="m3-card-title">Iceberg Cell Tower Outage % vs. Digital Divide %</h3>
                    <p class="m3-card-subtitle">Top 7 counties with compounding infrastructure & connectivity outages</p>
                  </div>
                  <span class="m3-source-pill rose">Apache Iceberg · FCC</span>
                </div>
                ${this.renderDrillOverlayOrDefault(
                  'lakehouse_outage_bar',
                  'Iceberg Cell Tower Outage % vs. Digital Divide %',
                  topLakehouseCounties,
                  html`
                    <app-chart
                      bare
                      type="bar"
                      height="300px"
                      value-format="decimal1"
                      .data=${lakehouseChartData}
                      .options=${{
                        ...baseChartOptions,
                        colors: ['#D92B3A', '#1A73E8'],
                        plotOptions: { bar: { borderRadius: 6 } },
                      }}
                    ></app-chart>
                  `,
                  'cell_tower_outage_pct'
                )}
              </div>

              <div
                class="m3-card"
                @contextmenu=${e => this.handleTileContextMenu(e, 'hazard_bar', 'Flood & Hurricane Hazard Risk by County', 'county_name', 'flood_risk_score')}>
                <div class="m3-card-header">
                  <div>
                    <h3 class="m3-card-title">Flood & Hurricane Hazard Risk by County</h3>
                    <p class="m3-card-subtitle">Top 7 priority counties by FEMA NRI multi-hazard exposure</p>
                  </div>
                  <span class="m3-source-pill">FEMA NRI · NOAA</span>
                </div>
                ${this.renderDrillOverlayOrDefault(
                  'hazard_bar',
                  'Flood & Hurricane Hazard Risk by County',
                  topHazardCounties,
                  html`
                    <app-chart
                      bare
                      type="bar"
                      height="300px"
                      value-format="decimal1"
                      .data=${hazardChartData}
                      .options=${{
                        ...baseChartOptions,
                        colors: ['#0A3161', '#1A73E8'],
                        plotOptions: { bar: { borderRadius: 6 } },
                      }}
                    ></app-chart>
                  `,
                  'flood_risk_score'
                )}
              </div>
            </div>

            <div class="m3-card">
              <div class="m3-card-header">
                <div>
                  <h3 class="m3-card-title">Borderless Lakehouse & Data Commons County Matrix</h3>
                  <p class="m3-card-subtitle">Unified view across Census ACS, BigLake Apache Iceberg telemetry, GCS SitRep PDFs, and Spanner Graph coverage</p>
                </div>
                <span class="m3-source-pill">Knowledge Catalog Governed</span>
              </div>
              <app-grid
                bare
                height="340px"
                .data=${filtered}
                .columnDefs=${[
                  { field: 'county_name', headerName: 'U.S. County', width: 145, pinned: 'left' },
                  { field: 'state_code', headerName: 'State', width: 80 },
                  { field: 'social_vulnerability_score', headerName: 'SVI Score', valueFormat: 'decimal1', width: 105 },
                  { field: 'active_hazard_alert', headerName: 'Iceberg Active Hazard Alert', width: 235 },
                  { field: 'cell_tower_outage_pct', headerName: 'Cell Outage %', valueFormat: 'decimal1', width: 125 },
                  { field: 'road_washout_status', headerName: 'FEMA PDA Road Washout Status', width: 250 },
                  { field: 'sitrep_pdf_uri', headerName: 'GCS SitRep PDF', width: 185 },
                  { field: 'simulated_coverage_status', headerName: 'Spanner DRC Coverage', width: 195 },
                ]}
              ></app-grid>
            </div>
          ` : nothing}

          ${this.activeTab === 'action' ? html`
            <!-- Tab 3: Cloud Spanner System of Action & Fleet Dispatch -->
            <div class="m3-two-col">
              <div class="m3-card">
                <div class="m3-card-header">
                  <div>
                    <h3 class="m3-card-title">U.S. Billion-Dollar Disaster Losses ($B USD)</h3>
                    <p class="m3-card-subtitle">NOAA / FEMA inflation-adjusted disaster losses across recent years</p>
                  </div>
                  <span class="m3-source-pill rose">NOAA · OpenFEMA</span>
                </div>
                <app-chart
                  bare
                  type="areaspline"
                  height="280px"
                  value-format="decimal1"
                  .data=${recentDisasterTimeline}
                  .options=${{
                    ...baseChartOptions,
                    colors: ['#D92B3A'],
                    plotOptions: { areaspline: { fillOpacity: 0.18, lineWidth: 2.8 } },
                  }}
                ></app-chart>
              </div>

              <div class="m3-card">
                <div class="m3-card-header">
                  <div>
                    <h3 class="m3-card-title">Federal Resilience Budget ($M) by Policy Pillar</h3>
                    <p class="m3-card-subtitle">Annual funding across FEMA, HUD, HHS, and FCC emergency programs</p>
                  </div>
                  <span class="m3-source-pill">Federal Programs</span>
                </div>
                <app-chart
                  bare
                  type="pie"
                  height="280px"
                  value-format="int"
                  .data=${budgetByPillar}
                  .options=${{
                    ...baseChartOptions,
                    colors: ['#0A3161', '#D92B3A', '#1A73E8', '#5C85D6'],
                    plotOptions: { pie: { innerSize: '58%', borderRadius: 6 } },
                  }}
                ></app-chart>
              </div>
            </div>

            <div class="m3-card">
              <div class="m3-card-header">
                <div>
                  <h3 class="m3-card-title">Cloud Spanner System of Action: Mobile DRC Fleet Dispatch</h3>
                  <p class="m3-card-subtitle">
                    Operational write-back queue joining Data Commons SVI, BigLake Iceberg road washout telemetry, and GCS SitRep PDFs
                  </p>
                </div>
                <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                  <button
                    class="m3-action-btn ${this.approveAllDispatches ? 'approved' : ''}"
                    @click=${() => this.pushStateChange({ approveAllDispatches: !this.approveAllDispatches })}>
                    ${this.approveAllDispatches ? '✓ All Units Dispatched in Spanner' : '⚡ Approve & Dispatch Pending Units'}
                  </button>
                </div>
              </div>
              <app-grid
                bare
                height="320px"
                .data=${dynamicDispatches}
                .columnDefs=${[
                  { field: 'priority_tier', headerName: 'Priority Tier', width: 155, pinned: 'left' },
                  { field: 'county_name', headerName: 'U.S. County', width: 145 },
                  { field: 'status', headerName: 'Spanner Status', width: 155 },
                  { field: 'recommended_team', headerName: 'Response Team', width: 165 },
                  { field: 'road_washout_status', headerName: 'Iceberg Road Status', width: 245 },
                  { field: 'sitrep_pdf_uri', headerName: 'GCS SitRep PDF', width: 180 },
                  { field: 'svi_score', headerName: 'SVI Score', valueFormat: 'decimal1', width: 105 },
                  { field: 'rationale', headerName: 'Operational Dispatch Rationale', width: 340 },
                ]}
              ></app-grid>
            </div>
          ` : nothing}
        </main>
      </div>
      </div>
    `;
  }
}

if (!customElements.get(elementName)) {
  customElements.define(elementName, BeaconDisasterReadiness);
}
export default BeaconDisasterReadiness;
