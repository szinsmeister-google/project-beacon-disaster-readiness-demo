"""Provisions end-to-end Google Cloud Knowledge Catalog (Dataplex Universal Catalog)
governance, Business Glossary, Custom Aspect Types, Entry Aspects, EntryLinks,
Ecosystem Entries, and 5-Stage End-to-End Table & Column-Level Data Lineage
for the U.S. Public Sector / North America Data Commons Beacon Disaster Readiness Demo.

Architecture covered:
1. Spanner (`readiness_dcgraph` on `dc-graph-demo`):
   - Creates and populates `KnowledgeCatalogGovernance` table with 16 governed federal contracts
     mapping Knowledge Catalog Glossary Terms <-> Spanner Tables/Columns <-> Google Data Commons DCIDs
     <-> Federal Agency Data Stewards (FEMA, U.S. Census Bureau, CDC/ATSDR, HHS, FCC/NTIA, DOT, NOAA).
2. Knowledge Catalog (`dataplex.googleapis.com`):
   - Creates Business Glossary `beacon-disaster-readiness-glossary` (in `us-central1` and `global`)
   - Creates 4 Federal Policy Categories & 12 Authoritative Business Glossary Terms
   - Creates Custom AspectType `beacon-federal-governance` (in `us-central1` and `global`)
   - Enriches all `@spanner` entries for `readiness_dcgraph` (`CountyReadiness`, `CountyProfile`,
     `StateProfile`, `DisasterSummary`, `DisasterDesignation`, `Registration`, `DeploymentPlan`,
     `NationalMacroTimeline`, `FederalProgramSummary`, `KnowledgeCatalogGovernance`, `Node`, `Edge`,
     `Observation`, and `graphs/DCGraph`) with 1P Aspects (`descriptions`, `overview`, `contacts`,
     `queries`) and Custom Governance Aspects (`beacon-federal-governance`) at both table/graph level
     and column level (`@Schema.<column>`).
   - Creates `definition` EntryLinks from Glossary Terms to Spanner columns and `schema-join` EntryLinks
     across Spanner tables/views/graph.
3. Data Lineage (`datalineage.googleapis.com`):
   - Catalogs 4 Custom Ecosystem Entries (`Google_Data_Commons_USA`, `US_Federal_Disaster_Operations`,
     `Gemini_Enterprise_Beacon_Readiness_Agent`, `Governed_Looker_Beacon_Data_App`) and registers
     the 5-Stage End-to-End Table & Column-Level Data Lineage pipeline.
   - Verifies `lookupContext` output and writes `schema/beacon_knowledge_catalog_context_bundle.yaml`.
"""

from __future__ import annotations

import json
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

import google.auth
import google.auth.transport.requests
from google.cloud import spanner

import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.gcp import env, get_project_id, get_project_number, get_region

PROJECT_ID = get_project_id()
PROJECT_NUM = get_project_number()
INSTANCE_ID = env("SPANNER_INSTANCE", "dc-graph-demo")
DATABASE_ID = env("SPANNER_DATABASE", "readiness_dcgraph")
LOCATION = get_region()
GLOSSARY_ID = env("KC_GLOSSARY_ID", "beacon-disaster-readiness-glossary")
ASPECT_TYPE_ID = env("KC_ASPECT_TYPE_ID", "beacon-federal-governance")

SPANNER_ENTRY_PREFIX = (
    f"projects/{PROJECT_NUM}/locations/{LOCATION}/entryGroups/@spanner/entries/"
    f"spanner.googleapis.com/projects/{PROJECT_ID}/instances/{INSTANCE_ID}/databases/{DATABASE_ID}"
)


def get_headers() -> dict[str, str]:
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json",
        "x-goog-user-project": PROJECT_ID,
    }


def api_call(
    method: str, url: str, headers: dict[str, str], body: dict[str, Any] | None = None
) -> tuple[int, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
        return e.code, err_body


def wait_for_lro(op_name: str, headers: dict[str, str], max_wait: int = 45) -> None:
    if not op_name or not op_name.startswith("projects/"):
        return
    url = f"https://dataplex.googleapis.com/v1/{op_name}"
    for _ in range(max_wait):
        st, data = api_call("GET", url, headers)
        if st == 200 and isinstance(data, dict) and data.get("done"):
            return
        time.sleep(1)


# =============================================================================
# 1. Spanner `KnowledgeCatalogGovernance` Table & Data
# =============================================================================

KC_GOVERNANCE_DDL = """
CREATE TABLE IF NOT EXISTS KnowledgeCatalogGovernance (
  rule_id                 STRING(64)   NOT NULL,
  business_term           STRING(256)  NOT NULL,
  category                STRING(128)  NOT NULL,
  governed_table          STRING(128)  NOT NULL,
  governed_column         STRING(128)  NOT NULL,
  policy_threshold        STRING(256)  NOT NULL,
  federal_steward         STRING(256)  NOT NULL,
  security_classification STRING(64)   NOT NULL,
  datacommons_dcid        STRING(256)  NOT NULL,
  description             STRING(MAX)  NOT NULL,
) PRIMARY KEY (rule_id)
"""

KC_GOVERNANCE_ROWS = [
    (
        "KC-US-001",
        "Social Vulnerability Score (SVI Tier-1 >= 75.0)",
        "Social Vulnerability & Equity",
        "CountyReadiness",
        "social_vulnerability_score",
        ">= 75.0 (Tier-1 Priority Dispatch)",
        "FEMA Office of Response & Recovery & CDC/ATSDR",
        "FedRAMP High · CUI",
        "FemaSocialVulnerability_NaturalHazardImpact",
        "Composite CDC/ATSDR & FEMA NRI percentile score (0-100) measuring county susceptibility to adverse disaster outcomes.",
    ),
    (
        "KC-US-002",
        "Household Digital Divide (No Internet >= 18.0%)",
        "Digital & Transit Access",
        "CountyReadiness",
        "no_internet_pct",
        ">= 18.0% Severe Digital Deficit",
        "U.S. Census Bureau (ACS) & FCC/NTIA",
        "FedRAMP Moderate · Public",
        "Count_Household_NoInternetAccess",
        "Percentage of county households without broadband or dial-up internet access (U.S. Census ACS 5-Year via Data Commons).",
    ),
    (
        "KC-US-003",
        "Transit-Isolated Households (No Vehicle >= 10.0%)",
        "Digital & Transit Access",
        "CountyReadiness",
        "no_vehicle_pct",
        ">= 10.0% Mobile DRC Required",
        "U.S. Census Bureau (ACS) & DOT/FEMA",
        "FedRAMP Moderate · Public",
        "Count_Household_NoVehicleAvailable",
        "Share of households with zero vehicles available, requiring Mobile Disaster Recovery Center (MDRC) field deployment.",
    ),
    (
        "KC-US-004",
        "Composite Hazard Risk Score (FEMA NRI >= 65.0)",
        "Hazard Risk & Resilience",
        "CountyReadiness",
        "nri_risk_score",
        ">= 65.0 High Multi-Hazard Exposure",
        "FEMA National Risk Index (NRI)",
        "FedRAMP Moderate · Public",
        "FemaNationalRisk_NaturalHazardImpact",
        "FEMA National Risk Index composite multi-hazard risk percentile across 18 natural hazards in Google Data Commons.",
    ),
    (
        "KC-US-005",
        "Community Resilience Index (FEMA NRI < 40.0 Alert)",
        "Hazard Risk & Resilience",
        "CountyReadiness",
        "community_resilience_score",
        "< 40.0 Low Recovery Capacity Alert",
        "FEMA NRI & NIST",
        "FedRAMP Moderate · Public",
        "FemaCommunityResilience_NaturalHazardImpact",
        "FEMA NRI measure of a county's baseline ability to prepare for, adapt to, and recover from major disaster declarations.",
    ),
    (
        "KC-US-006",
        "Expected Annual Disaster Loss (EAL >= $25M USD)",
        "Hazard Risk & Resilience",
        "CountyProfile",
        "nri_expected_annual_loss_usd",
        ">= $25M/yr Priority BRIC Mitigation",
        "FEMA Hazard Mitigation Directorate",
        "FedRAMP Moderate · Public",
        "FemaExpectedAnnualLoss_NaturalHazardImpact",
        "Expected economic loss in USD per year from natural hazards modeled in FEMA NRI and Data Commons.",
    ),
    (
        "KC-US-007",
        "Poverty Rate (Below Federal Line >= 20.0%)",
        "Social Vulnerability & Equity",
        "CountyReadiness",
        "poverty_pct",
        ">= 20.0% Persistent Poverty County",
        "U.S. Census Bureau (ACS) & HHS",
        "FedRAMP Moderate · Public",
        "Count_Person_BelowPovertyLevelInThePast12Months",
        "Share of county residents living below the federal poverty threshold in the past 12 months (Census ACS via Data Commons).",
    ),
    (
        "KC-US-008",
        "Senior Population Share (Aged 65+ >= 20.0%)",
        "Social Vulnerability & Equity",
        "CountyReadiness",
        "age_65_plus_pct",
        ">= 20.0% Aging Disaster Priority",
        "U.S. Census Bureau & HHS Administration for Community Living",
        "FedRAMP Moderate · Public",
        "Count_Person_65OrMoreYears",
        "Percentage of county population aged 65 years and older requiring HHS ASPR emPOWER & eldercare surge support.",
    ),
    (
        "KC-US-009",
        "Disability Access & Functional Needs (>= 18.0%)",
        "Social Vulnerability & Equity",
        "CountyReadiness",
        "disability_pct",
        ">= 18.0% ADA Field Surge Required",
        "U.S. Census Bureau & FEMA Office of Disability Integration",
        "FedRAMP Moderate · Public",
        "Count_Person_WithDisability",
        "Share of civilian non-institutionalized population with a disability (Census ACS 5-Year via Data Commons).",
    ),
    (
        "KC-US-010",
        "Median Resident Household Income (USD)",
        "Social Vulnerability & Equity",
        "CountyReadiness",
        "median_household_income_usd",
        "< $48,000 USD Low-Income IHP Priority",
        "U.S. Census Bureau (ACS)",
        "FedRAMP Moderate · Public",
        "Median_Income_Household",
        "Median annual household income in inflation-adjusted USD from U.S. Census ACS 5-Year Survey.",
    ),
    (
        "KC-US-011",
        "Web Intake Channel Share (< 60.0% Drop-Off)",
        "Federal Response Operations",
        "CountyReadiness",
        "web_registration_pct",
        "< 60.0% Web Intake Drop-Off",
        "FEMA Individual Assistance (IA) & USDS",
        "FedRAMP High · CUI",
        "OpenFEMA_WebRegistrationShare",
        "Percentage of valid FEMA disaster assistance registrations completed online via DisasterAssistance.gov.",
    ),
    (
        "KC-US-012",
        "Mobile Response Team Coverage Status (Beacon DRC)",
        "Federal Response Operations",
        "CountyReadiness",
        "has_team_coverage",
        "FALSE = Unserved Coverage Gap",
        "Beacon Federal Readiness Office (FEMA)",
        "FedRAMP High · CUI",
        "Beacon_MobileTeamCoverage",
        "Boolean indicator tracking whether a Beacon Mobile Disaster Recovery Unit (`beacon/team/*`) is assigned via Spanner Graph `:covers` edge.",
    ),
    (
        "KC-US-013",
        "Major Disaster Declarations Since 2023",
        "Federal Response Operations",
        "CountyReadiness",
        "disasters_since_2023",
        ">= 2 Compounding Disaster Zone",
        "FEMA OpenFEMA Declarations",
        "FedRAMP Moderate · Public",
        "OpenFEMA_DisasterDeclarationsSummaries",
        "Count of distinct Presidential Major Disaster Declarations (`DR-*`) designating the county since FY2023.",
    ),
    (
        "KC-US-014",
        "Riverine & Coastal Flood Risk Score",
        "Hazard Risk & Resilience",
        "CountyReadiness",
        "flood_risk_score",
        ">= 60.0 High Flood Hazard",
        "FEMA NRI & NOAA National Water Center",
        "FedRAMP Moderate · Public",
        "FemaFloodRisk_NaturalHazardImpact",
        "County-level flood hazard risk percentile from FEMA National Risk Index.",
    ),
    (
        "KC-US-015",
        "Hurricane & Severe Storm Risk Score",
        "Hazard Risk & Resilience",
        "CountyReadiness",
        "hurricane_risk_score",
        ">= 60.0 High Hurricane Corridor",
        "FEMA NRI & NOAA NHC",
        "FedRAMP Moderate · Public",
        "FemaHurricaneRisk_NaturalHazardImpact",
        "County-level hurricane wind and storm surge risk percentile from FEMA National Risk Index.",
    ),
    (
        "KC-US-016",
        "Federal Deployment Plan (Cloud Spanner System of Action)",
        "Federal Response Operations",
        "DeploymentPlan",
        "priority_tier",
        "Tier 1 - Immediate Mobile DRC Dispatch",
        "Beacon Readiness Office & FEMA Region I-X",
        "FedRAMP High · Official Action",
        "Beacon_SystemOfAction_DeploymentPlan",
        "Transactional Cloud Spanner write-back table recording Mobile Response Team dispatches approved by field coordinators.",
    ),
]


def setup_spanner_governance_table() -> None:
    print("1. Setting up `KnowledgeCatalogGovernance` table in Cloud Spanner (`readiness_dcgraph`) ...")
    client = spanner.Client(project=PROJECT_ID)
    instance = client.instance(INSTANCE_ID)
    database = instance.database(DATABASE_ID)

    with database.snapshot() as snap:
        res = list(
            snap.execute_sql(
                "SELECT table_name FROM information_schema.tables WHERE table_name = 'KnowledgeCatalogGovernance'"
            )
        )
    if not res:
        print("   Creating table `KnowledgeCatalogGovernance` in Spanner ...")
        op = database.update_ddl([KC_GOVERNANCE_DDL.strip()])
        op.result(timeout=120)
        print("   Table created successfully.")
    else:
        print("   Table `KnowledgeCatalogGovernance` already exists.")

    cols = [
        "rule_id",
        "business_term",
        "category",
        "governed_table",
        "governed_column",
        "policy_threshold",
        "federal_steward",
        "security_classification",
        "datacommons_dcid",
        "description",
    ]
    with database.batch() as batch:
        batch.insert_or_update(
            table="KnowledgeCatalogGovernance",
            columns=cols,
            values=KC_GOVERNANCE_ROWS,
        )
    print(f"   Upserted {len(KC_GOVERNANCE_ROWS)} governed federal contracts into `KnowledgeCatalogGovernance`.")


# =============================================================================
# 2. Knowledge Catalog Business Glossary, Categories, and Terms
# =============================================================================

GLOSSARY_CATEGORIES = [
    {
        "id": "social-vulnerability-equity",
        "displayName": "Social Vulnerability & Equity (CDC/ATSDR SVI & U.S. Census ACS)",
        "description": (
            "Federal demographic equity and vulnerability baselines governed by FEMA Office of Response & Recovery, "
            "CDC/ATSDR Social Vulnerability Index (SVI), HHS ASPR emPOWER, and U.S. Census Bureau American Community Survey (ACS 5-Year) "
            "via Google Data Commons (`country/USA`)."
        ),
    },
    {
        "id": "digital-transit-access",
        "displayName": "Digital Divide & Transit Access (U.S. Census ACS, FCC/NTIA & DOT)",
        "description": (
            "Last-mile household broadband connectivity (`Count_Household_NoInternetAccess`) and zero-vehicle transit isolation "
            "(`Count_Household_NoVehicleAvailable`) metrics determining whether disaster survivors can self-register online at "
            "DisasterAssistance.gov or require in-county Mobile Disaster Recovery Centers (MDRCs)."
        ),
    },
    {
        "id": "hazard-risk-resilience",
        "displayName": "Multi-Hazard Risk & Community Resilience (FEMA National Risk Index & NOAA)",
        "description": (
            "FEMA National Risk Index (NRI) composite multi-hazard risk scores (`nri_risk_score`), Community Resilience Index "
            "(`community_resilience_score`), Expected Annual Disaster Loss (`nri_expected_annual_loss_usd`), and riverine/hurricane/wildfire "
            "exposure percentiles across 3,144 U.S. counties in Google Data Commons."
        ),
    },
    {
        "id": "federal-response-operations",
        "displayName": "Federal Emergency Response & System of Action (OpenFEMA & Beacon DRC)",
        "description": (
            "Operational OpenFEMA Major Disaster Declarations (`DR-*`), Individual & Households Program (IHP) intake channel shares "
            "(Web vs. Call Center vs. Mobile DRC), Spanner Graph mobile response unit coverage (`has_team_coverage`), and transactional "
            "`DeploymentPlan` dispatch governance."
        ),
    },
]

GLOSSARY_TERMS = [
    {
        "id": "social-vulnerability-score",
        "category": "social-vulnerability-equity",
        "displayName": "Social Vulnerability Score (SVI Tier-1 >= 75.0)",
        "description": (
            "Composite CDC/ATSDR Social Vulnerability Index & FEMA National Risk Index percentile score (0–100) measuring a U.S. county's "
            "relative susceptibility to adverse impacts from natural hazards (`social_vulnerability_score`, `nri_social_vulnerability_score`; "
            "Data Commons DCID: `FemaSocialVulnerability_NaturalHazardImpact`). "
            "Policy Rule: Scores >= 75.0 designate Tier-1 Priority Equity Intervention Counties under Justice40 and FEMA Individual Assistance. "
            "Federal Steward: FEMA Office of Response & Recovery & CDC/ATSDR | Security: FedRAMP High · CUI | Certified: Blue-Chip."
        ),
        "links": [
            ("tables/CountyReadiness", "Schema.social_vulnerability_score"),
            ("tables/CountyProfile", "Schema.nri_social_vulnerability_score"),
            ("tables/FederalProgramSummary", "Schema.target_svi_threshold"),
            ("tables/KnowledgeCatalogGovernance", "Schema.business_term"),
        ],
    },
    {
        "id": "household-digital-divide",
        "category": "digital-transit-access",
        "displayName": "Household Digital Divide (No Internet >= 18.0%)",
        "description": (
            "Percentage of households in a U.S. county or state without broadband, cellular data, or dial-up internet access "
            "(`no_internet_pct`, `no_internet_households`; Data Commons DCID: `Count_Household_NoInternetAccess` / `Count_Household`, "
            "U.S. Census Bureau ACS 5-Year Survey). "
            "Policy Rule: Counties with `no_internet_pct >= 18.0%` experience an average 17.8 percentage-point drop in online FEMA "
            "registration (`r = -0.45`) and mandate proactive Mobile Disaster Recovery Center (MDRC) & Call Center surge deployment. "
            "Federal Steward: U.S. Census Bureau (ACS) & FCC/NTIA | Security: FedRAMP Moderate · Public."
        ),
        "links": [
            ("tables/CountyReadiness", "Schema.no_internet_pct"),
            ("tables/CountyProfile", "Schema.no_internet_pct"),
            ("tables/CountyProfile", "Schema.no_internet_households"),
            ("tables/StateProfile", "Schema.no_internet_pct"),
            ("tables/NationalMacroTimeline", "Schema.no_internet_households_pct"),
        ],
    },
    {
        "id": "transit-isolated-households",
        "category": "digital-transit-access",
        "displayName": "Transit-Isolated Households (No Vehicle >= 10.0%)",
        "description": (
            "Percentage of occupied housing units in a U.S. county with zero vehicles available (`no_vehicle_pct`, `no_vehicle_households`; "
            "Data Commons DCID: `Count_Household_NoVehicleAvailable` / `Count_Household_With0AvailableVehicles`, U.S. Census ACS 5-Year). "
            "Policy Rule: `no_vehicle_pct >= 10.0%` indicates survivors cannot travel to fixed regional recovery centers and requires "
            "roving Beacon Mobile DRC field units (`Deploy Mobile Team`). "
            "Federal Steward: U.S. Census Bureau (ACS) & U.S. DOT / FEMA | Security: FedRAMP Moderate · Public."
        ),
        "links": [
            ("tables/CountyReadiness", "Schema.no_vehicle_pct"),
            ("tables/CountyProfile", "Schema.no_vehicle_pct"),
            ("tables/CountyProfile", "Schema.no_vehicle_households"),
        ],
    },
    {
        "id": "composite-hazard-risk-score",
        "category": "hazard-risk-resilience",
        "displayName": "Composite Hazard Risk Score (FEMA NRI >= 65.0)",
        "description": (
            "FEMA National Risk Index (NRI) national percentile score (0–100) evaluating baseline multi-hazard risk across 18 natural hazards "
            "including riverine/coastal flooding (`flood_risk_score`), hurricanes (`hurricane_risk_score`), and wildfires (`wildfire_risk_score`) "
            "(Data Commons DCID: `FemaNationalRisk_NaturalHazardImpact`). "
            "Policy Rule: `nri_risk_score >= 65.0` classifies a county as High Multi-Hazard Exposure for pre-season staging. "
            "Federal Steward: FEMA National Risk Index (NRI) & NOAA | Security: FedRAMP Moderate · Public."
        ),
        "links": [
            ("tables/CountyReadiness", "Schema.nri_risk_score"),
            ("tables/CountyReadiness", "Schema.flood_risk_score"),
            ("tables/CountyReadiness", "Schema.hurricane_risk_score"),
            ("tables/CountyProfile", "Schema.nri_risk_score"),
        ],
    },
    {
        "id": "community-resilience-index",
        "category": "hazard-risk-resilience",
        "displayName": "Community Resilience Index (FEMA NRI < 40.0 Alert)",
        "description": (
            "FEMA National Risk Index (NRI) & HVRI baseline Community Resilience percentile score (0–100) measuring a county's social, "
            "economic, institutional, and infrastructure capacity to prepare for, adapt to, and recover from major disaster declarations "
            "(`community_resilience_score`, `nri_community_resilience_score`; Data Commons DCID: `FemaCommunityResilience_NaturalHazardImpact`). "
            "Policy Rule: Scores `< 40.0` trigger a Low Recovery Capacity Alert requiring extended federal Public Assistance & IA field presence. "
            "Federal Steward: FEMA NRI & NIST Community Resilience Program | Security: FedRAMP Moderate · Public."
        ),
        "links": [
            ("tables/CountyReadiness", "Schema.community_resilience_score"),
            ("tables/CountyProfile", "Schema.nri_community_resilience_score"),
        ],
    },
    {
        "id": "expected-annual-disaster-loss",
        "category": "hazard-risk-resilience",
        "displayName": "Expected Annual Disaster Loss (EAL >= $25M USD)",
        "description": (
            "Modeled Expected Annual Loss (EAL) in USD (`nri_expected_annual_loss_usd` in `CountyProfile` and `billion_dollar_disasters_loss_usd_b` "
            "in `NationalMacroTimeline`; Data Commons DCID: `FemaExpectedAnnualLoss_NaturalHazardImpact`) quantifying average annual economic "
            "damage to buildings, population equivalence, and agriculture from natural hazards. "
            "Policy Rule: Counties with EAL >= $25M USD/yr qualify for priority FEMA Building Resilient Infrastructure and Communities (BRIC) "
            "and Hazard Mitigation Grant Program (HMGP) investments. "
            "Federal Steward: FEMA Hazard Mitigation Directorate & NOAA NCEI | Security: FedRAMP Moderate · Public."
        ),
        "links": [
            ("tables/CountyProfile", "Schema.nri_expected_annual_loss_usd"),
            ("tables/NationalMacroTimeline", "Schema.billion_dollar_disasters_loss_usd_b"),
        ],
    },
    {
        "id": "poverty-rate-federal-line",
        "category": "social-vulnerability-equity",
        "displayName": "Poverty Rate (Below Federal Line >= 20.0%)",
        "description": (
            "Percentage of county or state residents living below the official U.S. Federal Poverty Threshold in the past 12 months "
            "(`poverty_pct`, `poverty_count`, `median_household_income_usd`; Data Commons DCID: "
            "`Count_Person_BelowPovertyLevelInThePast12Months` & `Median_Income_Household`, U.S. Census ACS 5-Year Survey). "
            "Policy Rule: `poverty_pct >= 20.0%` designates a Persistent Poverty County eligible for expedited FEMA Individual & Households "
            "Program (IHP) financial relief and reduced local cost-share. "
            "Federal Steward: U.S. Census Bureau (ACS) & HHS | Security: FedRAMP Moderate · Public."
        ),
        "links": [
            ("tables/CountyReadiness", "Schema.poverty_pct"),
            ("tables/CountyReadiness", "Schema.median_household_income_usd"),
            ("tables/CountyProfile", "Schema.poverty_pct"),
            ("tables/StateProfile", "Schema.poverty_pct"),
            ("tables/NationalMacroTimeline", "Schema.poverty_rate_pct"),
        ],
    },
    {
        "id": "senior-population-share",
        "category": "social-vulnerability-equity",
        "displayName": "Senior Population Share (Aged 65+ >= 20.0%)",
        "description": (
            "Percentage of resident population aged 65 years and older (`age_65_plus_pct`, `age_65_plus`, `seniors_65_plus_pct`; "
            "Data Commons DCID: `Count_Person_65OrMoreYears`, U.S. Census Bureau ACS 5-Year Survey). "
            "Policy Rule: `age_65_plus_pct >= 20.0%` triggers Aging Disaster Priority protocols, coordinating HHS ASPR emPOWER medical-device "
            "power resiliency and eldercare evacuation support. "
            "Federal Steward: U.S. Census Bureau & HHS Administration for Community Living (ACL) | Security: FedRAMP Moderate · Public."
        ),
        "links": [
            ("tables/CountyReadiness", "Schema.age_65_plus_pct"),
            ("tables/CountyProfile", "Schema.age_65_plus_pct"),
            ("tables/StateProfile", "Schema.age_65_plus_pct"),
            ("tables/NationalMacroTimeline", "Schema.seniors_65_plus_pct"),
        ],
    },
    {
        "id": "disability-access-functional-needs",
        "category": "social-vulnerability-equity",
        "displayName": "Disability Access & Functional Needs (>= 18.0%)",
        "description": (
            "Percentage of civilian non-institutionalized population with one or more cognitive, ambulatory, sensory, or independent-living "
            "disabilities (`disability_pct`, `disability_count`; Data Commons DCID: `Count_Person_WithDisability`, U.S. Census ACS 5-Year). "
            "Policy Rule: `disability_pct >= 18.0%` mandates deployment of FEMA Disability Integration Advisors, ASL interpreters, and "
            "ADA-accessible Mobile Disaster Recovery Centers. "
            "Federal Steward: U.S. Census Bureau & FEMA Office of Disability Integration and Coordination | Security: FedRAMP Moderate · Public."
        ),
        "links": [
            ("tables/CountyReadiness", "Schema.disability_pct"),
            ("tables/CountyProfile", "Schema.disability_pct"),
            ("tables/StateProfile", "Schema.disability_pct"),
        ],
    },
    {
        "id": "web-intake-channel-share",
        "category": "federal-response-operations",
        "displayName": "Web Intake Channel Share (< 60.0% Drop-Off)",
        "description": (
            "Percentage of valid FEMA Individual Assistance registrations submitted online via DisasterAssistance.gov (`web_registration_pct` "
            "in `CountyReadiness`, `web_share_pct` in `Registration` and `DisasterSummary`, `web_intake_share_pct` in `FederalProgramSummary`) "
            "versus Phone Call Center (`call_center_registration_pct`) and Mobile DRC (`mobile_share_pct`). "
            "Policy Rule: `web_registration_pct < 60.0%` (compared to the 78.7% high-connectivity benchmark) signals severe digital intake "
            "drop-off and triggers immediate Mobile DRC and Call Center surge routing. "
            "Federal Steward: FEMA Individual Assistance (IA) Division & U.S. Digital Service (USDS) | Security: FedRAMP High · CUI."
        ),
        "links": [
            ("tables/CountyReadiness", "Schema.web_registration_pct"),
            ("tables/CountyReadiness", "Schema.call_center_registration_pct"),
            ("tables/Registration", "Schema.web_share_pct"),
            ("tables/DisasterSummary", "Schema.web_share_pct"),
            ("tables/FederalProgramSummary", "Schema.web_intake_share_pct"),
        ],
    },
    {
        "id": "mobile-response-team-coverage",
        "category": "federal-response-operations",
        "displayName": "Mobile Response Team Coverage Status (Beacon DRC)",
        "description": (
            "Operational Cloud Spanner Graph coverage indicator (`has_team_coverage` and `assigned_team_count` in `CountyReadiness`, derived "
            "from `(t:team)-[:covers]->(c:county)` edges in `DCGraph`). "
            "Policy Rule: `has_team_coverage = FALSE` combined with `disasters_since_2023 >= 1` and `social_vulnerability_score >= 75.0` "
            "identifies an unserved frontline whitespace county requiring immediate mobile unit dispatch. "
            "Federal Steward: Beacon Federal Readiness Office (FEMA Field Operations) | Security: FedRAMP High · CUI."
        ),
        "links": [
            ("tables/CountyReadiness", "Schema.has_team_coverage"),
            ("tables/CountyReadiness", "Schema.assigned_team_count"),
            ("tables/FederalProgramSummary", "Schema.mobile_drc_share_pct"),
        ],
    },
    {
        "id": "federal-deployment-plan",
        "category": "federal-response-operations",
        "displayName": "Federal Deployment Plan (Cloud Spanner System of Action)",
        "description": (
            "Transactional System-of-Action write-back contract in Cloud Spanner (`DeploymentPlan`: `priority_tier`, `action`, "
            "`assigned_team_id`, `status`, `rationale`) recording live Mobile Disaster Recovery Center (MDRC) dispatches and fixed recovery "
            "center activations approved by federal field coordinators in Gemini Conversational Analytics and Governed Looker Data Apps. "
            "Policy Rule: `Tier 1 - Immediate` dispatches target unserved disaster-declared counties with SVI >= 75.0 and No Internet >= 15.0%. "
            "Federal Steward: Beacon Readiness Office & FEMA Regions I–X | Security: FedRAMP High · Official Action."
        ),
        "links": [
            ("tables/DeploymentPlan", "Schema.priority_tier"),
            ("tables/DeploymentPlan", "Schema.action"),
            ("tables/DeploymentPlan", "Schema.assigned_team_id"),
            ("tables/DeploymentPlan", "Schema.status"),
        ],
    },
]


def setup_glossaries_and_terms(headers: dict[str, str]) -> None:
    print("2. Provisioning Knowledge Catalog Business Glossary, Categories & Terms ...")
    for loc in ["us-central1", "global"]:
        g_parent = f"projects/{PROJECT_ID}/locations/{loc}"
        g_name = f"{g_parent}/glossaries/{GLOSSARY_ID}"
        g_display = "U.S. Public Sector · Beacon Federal Disaster Readiness & Emergency Response Glossary"
        g_desc = (
            "Authoritative U.S. Federal Public Sector (FEMA, U.S. Census Bureau, CDC/ATSDR, HHS, HUD/DOT, NOAA) business "
            "glossary governing disaster readiness & equity metrics, Cloud Spanner Graph (`readiness_dcgraph` / `DCGraph`) "
            "operational entities, and North America Google Data Commons (`country/USA`) statistical baselines. "
            "Curated by Sean Zinsmeister (demo-operator@example.com)."
        )
        st, _ = api_call("GET", f"https://dataplex.googleapis.com/v1/{g_name}", headers)
        if st != 200:
            print(f"   Creating Glossary `{GLOSSARY_ID}` in {loc} ...")
            st_c, res_c = api_call(
                "POST",
                f"https://dataplex.googleapis.com/v1/{g_parent}/glossaries?glossaryId={GLOSSARY_ID}",
                headers,
                {"displayName": g_display, "description": g_desc},
            )
            if isinstance(res_c, dict) and "name" in res_c:
                wait_for_lro(res_c["name"], headers)
        else:
            api_call(
                "PATCH",
                f"https://dataplex.googleapis.com/v1/{g_name}?updateMask=displayName,description",
                headers,
                {"name": g_name, "displayName": g_display, "description": g_desc},
            )
            print(f"   Glossary `{GLOSSARY_ID}` updated in {loc}.")

        # Create or Update Categories
        for cat in GLOSSARY_CATEGORIES:
            cat_name = f"{g_name}/categories/{cat['id']}"
            st_cat, _ = api_call("GET", f"https://dataplex.googleapis.com/v1/{cat_name}", headers)
            if st_cat != 200:
                st_cp, _ = api_call(
                    "POST",
                    f"https://dataplex.googleapis.com/v1/{g_name}/categories?categoryId={cat['id']}",
                    headers,
                    {
                        "parent": g_name,
                        "displayName": cat["displayName"],
                        "description": cat["description"],
                    },
                )
                print(f"   [{loc}] Created category `{cat['id']}` -> {st_cp}")
            else:
                api_call(
                    "PATCH",
                    f"https://dataplex.googleapis.com/v1/{cat_name}?updateMask=displayName,description",
                    headers,
                    {
                        "name": cat_name,
                        "parent": g_name,
                        "displayName": cat["displayName"],
                        "description": cat["description"],
                    },
                )

        # Create or Update Terms
        for term in GLOSSARY_TERMS:
            term_name = f"{g_name}/terms/{term['id']}"
            cat_parent = f"{g_name}/categories/{term['category']}"
            st_t, ex_t = api_call("GET", f"https://dataplex.googleapis.com/v1/{term_name}", headers)
            if st_t != 200:
                st_post, _ = api_call(
                    "POST",
                    f"https://dataplex.googleapis.com/v1/{g_name}/terms?termId={term['id']}",
                    headers,
                    {
                        "parent": cat_parent,
                        "displayName": term["displayName"],
                        "description": term["description"],
                    },
                )
                print(f"   [{loc}] Created term `{term['id']}` -> {st_post}")
            else:
                st_patch, _ = api_call(
                    "PATCH",
                    f"https://dataplex.googleapis.com/v1/{term_name}?updateMask=displayName,description",
                    headers,
                    {
                        "name": term_name,
                        "parent": ex_t.get("parent", cat_parent) if isinstance(ex_t, dict) else cat_parent,
                        "displayName": term["displayName"],
                        "description": term["description"],
                    },
                )
                print(f"   [{loc}] Updated term `{term['id']}` -> {st_patch}")


# =============================================================================
# 3. Custom AspectType `beacon-federal-governance` & Entry Aspects
# =============================================================================

BEACON_FEDERAL_ASPECT_TEMPLATE = {
    "displayName": "Beacon U.S. Federal Governance & Data Commons Lineage",
    "description": (
        "Authoritative U.S. Public Sector (FedRAMP / OpenFEMA / OMB M-24-10) data governance, Federal Agency "
        "Data Stewardship, policy pillar alignment, and North America Google Data Commons (`country/USA`) provenance lineage."
    ),
    "metadataTemplate": {
        "index": 1,
        "name": "beacon_federal_governance",
        "type": "record",
        "recordFields": [
            {
                "index": 1,
                "name": "federal_agency_steward",
                "type": "string",
                "constraints": {"required": True},
                "annotations": {
                    "displayName": "Federal Agency Data Steward",
                    "description": "Accountable U.S. Federal Agency or Office (e.g. FEMA ORR, U.S. Census Bureau, CDC/ATSDR, HHS ASPR, FCC/NTIA, NOAA).",
                    "displayOrder": 1,
                },
            },
            {
                "index": 2,
                "name": "fedramp_security_classification",
                "type": "enum",
                "enumValues": [
                    {"index": 1, "name": "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS"},
                    {"index": 2, "name": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED"},
                    {"index": 3, "name": "FEDRAMP_HIGH_OFFICIAL_ACTION"},
                ],
                "constraints": {"required": True},
                "annotations": {
                    "displayName": "FedRAMP / CUI Security Classification",
                    "description": "U.S. Federal FISMA / FedRAMP & CUI data sensitivity tier.",
                    "displayOrder": 2,
                },
            },
            {
                "index": 3,
                "name": "certification_status",
                "type": "enum",
                "enumValues": [
                    {"index": 1, "name": "BLUE_CHIP_CERTIFIED"},
                    {"index": 2, "name": "GOLD_VERIFIED"},
                    {"index": 3, "name": "PROVISIONAL"},
                ],
                "constraints": {"required": True},
                "annotations": {
                    "displayName": "Catalog Certification Status",
                    "description": "Verification status for executive AI & emergency dispatch grounding in Gemini Conversational Analytics.",
                    "displayOrder": 3,
                },
            },
            {
                "index": 4,
                "name": "federal_policy_pillar",
                "type": "string",
                "constraints": {"required": True},
                "annotations": {
                    "displayName": "Federal Policy & Mission Pillar",
                    "description": "Aligned federal mandate (FEMA Individual Assistance, Justice40 Equity, National Risk Index, Broadband Equity BEAD, Mobile DRC Operations).",
                    "displayOrder": 4,
                },
            },
            {
                "index": 5,
                "name": "data_commons_dcids",
                "type": "string",
                "constraints": {"required": False},
                "annotations": {
                    "displayName": "Google Data Commons Provenance & DCIDs",
                    "description": "Linked Google Data Commons statistical variable DCIDs and upstream authorities (country/USA, U.S. Census ACS, FEMA NRI, OpenFEMA).",
                    "displayOrder": 5,
                },
            },
            {
                "index": 6,
                "name": "policy_threshold_rule",
                "type": "string",
                "constraints": {"required": False},
                "annotations": {
                    "displayName": "Operational Policy Threshold & Dispatch Rule",
                    "description": "Deterministic policy threshold used by Gemini Conversational Analytics and Looker Data Apps to evaluate county readiness.",
                    "displayOrder": 6,
                },
            },
        ],
    },
}


def setup_aspect_types(headers: dict[str, str]) -> None:
    print("3. Provisioning Custom AspectType `beacon-federal-governance` ...")
    for loc in ["us-central1", "us-east1", "us", "global"]:
        at_parent = f"projects/{PROJECT_ID}/locations/{loc}"
        at_name = f"{at_parent}/aspectTypes/{ASPECT_TYPE_ID}"
        st, _ = api_call("GET", f"https://dataplex.googleapis.com/v1/{at_name}", headers)
        if st != 200:
            st_c, res_c = api_call(
                "POST",
                f"https://dataplex.googleapis.com/v1/{at_parent}/aspectTypes?aspectTypeId={ASPECT_TYPE_ID}",
                headers,
                BEACON_FEDERAL_ASPECT_TEMPLATE,
            )
            print(f"   [{loc}] Created AspectType `{ASPECT_TYPE_ID}` -> {st_c}")
            if isinstance(res_c, dict) and "name" in res_c:
                wait_for_lro(res_c["name"], headers)
        else:
            print(f"   [{loc}] AspectType `{ASPECT_TYPE_ID}` already exists.")


# =============================================================================
# 4. Rich Entry Metadata (Descriptions, Overview, Contacts, Queries, Aspects)
# =============================================================================

COUNTY_READINESS_FIELDS = [
    {"name": "county_id", "description": "Primary county DCID (`geoId/21193` Perry County, KY; `geoId/28151` Washington County, MS). Joins with `CountyProfile.county_id`, `DeploymentPlan.county_id`, and `Node.subject_id`."},
    {"name": "county_name", "description": "Disambiguated U.S. County & State name (e.g., `Perry County, KY`, `Washington County, MS`, `Owsley County, KY`)."},
    {"name": "state_name", "description": "Full U.S. State or Territory name (e.g., `Kentucky`, `Mississippi`, `Florida`, `North Carolina`)."},
    {"name": "state_code", "description": "2-letter USPS State abbreviation (`KY`, `MS`, `FL`, `NC`, `GA`, `TX`, `LA`)."},
    {"name": "latitude", "description": "WGS84 geographic centroid latitude of the county from U.S. Census TIGER/Line & Data Commons."},
    {"name": "longitude", "description": "WGS84 geographic centroid longitude of the county from U.S. Census TIGER/Line & Data Commons."},
    {"name": "population", "description": "Total county resident population from U.S. Census Bureau ACS 5-Year Survey via Google Data Commons (`Count_Person`)."},
    {"name": "households", "description": "Total occupied housing units / households in the county (`Count_Household`, U.S. Census ACS 5-Year)."},
    {"name": "median_household_income_usd", "description": "[Knowledge Catalog Term: Poverty Rate & Economic Equity] Median annual household income in USD (`Median_Income_Household`, Census ACS). Policy Rule: `< $48,000 USD` flags low-income IHP priority."},
    {"name": "no_internet_pct", "description": "[Knowledge Catalog Term: Household Digital Divide (No Internet >= 18.0%)] Share of households without internet access (`Count_Household_NoInternetAccess`). Policy Rule: `>= 18.0%` mandates Mobile DRC & Call Center surge."},
    {"name": "no_vehicle_pct", "description": "[Knowledge Catalog Term: Transit-Isolated Households (No Vehicle >= 10.0%)] Share of households with zero available vehicles (`Count_Household_NoVehicleAvailable`). Policy Rule: `>= 10.0%` requires Mobile DRC field dispatch."},
    {"name": "age_65_plus_pct", "description": "[Knowledge Catalog Term: Senior Population Share (Aged 65+ >= 20.0%)] Percentage of residents aged 65+ (`Count_Person_65OrMoreYears`). Policy Rule: `>= 20.0%` triggers HHS ASPR emPOWER & eldercare surge."},
    {"name": "disability_pct", "description": "[Knowledge Catalog Term: Disability Access & Functional Needs (>= 18.0%)] Share of residents with a disability (`Count_Person_WithDisability`). Policy Rule: `>= 18.0%` mandates ADA field surge."},
    {"name": "poverty_pct", "description": "[Knowledge Catalog Term: Poverty Rate (Below Federal Line >= 20.0%)] Share of population below the federal poverty line (`Count_Person_BelowPovertyLevelInThePast12Months`). Policy Rule: `>= 20.0%` designates Persistent Poverty County."},
    {"name": "nri_risk_score", "description": "[Knowledge Catalog Term: Composite Hazard Risk Score (FEMA NRI >= 65.0)] FEMA National Risk Index composite multi-hazard risk percentile (`FemaNationalRisk_NaturalHazardImpact`)."},
    {"name": "social_vulnerability_score", "description": "[Knowledge Catalog Term: Social Vulnerability Score (SVI Tier-1 >= 75.0)] CDC/ATSDR & FEMA NRI Social Vulnerability percentile (`FemaSocialVulnerability_NaturalHazardImpact`). Policy Rule: `>= 75.0` designates Tier-1 Priority Dispatch."},
    {"name": "community_resilience_score", "description": "[Knowledge Catalog Term: Community Resilience Index (FEMA NRI < 40.0 Alert)] FEMA NRI Community Resilience percentile (`FemaCommunityResilience_NaturalHazardImpact`). Policy Rule: `< 40.0` triggers Low Recovery Capacity Alert."},
    {"name": "flood_risk_score", "description": "FEMA NRI riverine & coastal flood risk percentile (`FemaFloodRisk_NaturalHazardImpact`)."},
    {"name": "hurricane_risk_score", "description": "FEMA NRI hurricane wind & storm surge risk percentile (`FemaHurricaneRisk_NaturalHazardImpact`)."},
    {"name": "wildfire_risk_score", "description": "FEMA NRI wildfire hazard risk percentile (`FemaWildfireRisk_NaturalHazardImpact`)."},
    {"name": "disasters_since_2023", "description": "Count of distinct Presidential Major Disaster Declarations (`DR-*`) designating the county since FY2023 from OpenFEMA."},
    {"name": "ihp_disasters_since_2023", "description": "Count of Major Disaster Declarations since FY2023 where the Individual & Households Program (`ihp_declared = TRUE`) was activated."},
    {"name": "total_registrations", "description": "Total valid FEMA Individual Assistance registrations across all disasters in the county since FY2023."},
    {"name": "web_registration_pct", "description": "[Knowledge Catalog Term: Web Intake Channel Share (< 60.0% Drop-Off)] Share (%) of FEMA registrations completed online via DisasterAssistance.gov. Policy Rule: `< 60.0%` signals digital intake drop-off."},
    {"name": "call_center_registration_pct", "description": "Share (%) of FEMA registrations completed via the FEMA 1-800 Helpline Call Center."},
    {"name": "has_team_coverage", "description": "[Knowledge Catalog Term: Mobile Response Team Coverage Status (Beacon DRC)] Boolean derived from `DCGraph` (`(team)-[:covers]->(county)`). `FALSE` in disaster-hit high-SVI counties indicates an unserved coverage gap."},
    {"name": "assigned_team_count", "description": "Count of Beacon Mobile Disaster Recovery Teams covering the county via `:covers` edges in `DCGraph`."},
    {"name": "gmap_hybrid_uri", "description": "Pre-calibrated Google Maps Static API Satellite-Hybrid basemap URI (`zoom=4`, Web Mercator aligned) for Gemini Conversational Analytics geospatial charts."},
    {"name": "gmap_terrain_uri", "description": "Pre-calibrated Google Maps Static API Terrain-Roadmap basemap URI (`zoom=4`, Web Mercator aligned) for Gemini Conversational Analytics geospatial charts."},
]

COUNTY_PROFILE_FIELDS = [
    {"name": "county_id", "description": "Primary key U.S. County DCID (`geoId/01001` to `geoId/72153`, 3,144 counties). Foreign key to `Node.subject_id`."},
    {"name": "county_name", "description": "Disambiguated county and state name (e.g., `Washington County, MS`)."},
    {"name": "state_id", "description": "Parent state DCID (`geoId/28` for Mississippi)."},
    {"name": "state_name", "description": "Full U.S. State name."},
    {"name": "state_code", "description": "2-letter USPS State code."},
    {"name": "population", "description": "Total resident population from U.S. Census ACS 5-Year Survey via Google Data Commons (`Count_Person`)."},
    {"name": "population_year", "description": "Reference vintage year for population observation."},
    {"name": "population_change_5yr_pct", "description": "5-year county population change percentage."},
    {"name": "households", "description": "Total occupied housing units (`Count_Household`, U.S. Census ACS 5-Year)."},
    {"name": "no_internet_households", "description": "[Knowledge Catalog Term: Household Digital Divide] Count of households without internet access (`Count_Household_NoInternetAccess`)."},
    {"name": "no_internet_pct", "description": "[Knowledge Catalog Term: Household Digital Divide (No Internet >= 18.0%)] Percentage of households lacking broadband/internet access."},
    {"name": "age_65_plus", "description": "Total residents aged 65 years and older (`Count_Person_65OrMoreYears`)."},
    {"name": "age_65_plus_pct", "description": "[Knowledge Catalog Term: Senior Population Share (Aged 65+ >= 20.0%)] Share (%) of county population aged 65+."},
    {"name": "disability_count", "description": "Total civilian non-institutionalized residents with a disability (`Count_Person_WithDisability`)."},
    {"name": "disability_pct", "description": "[Knowledge Catalog Term: Disability Access & Functional Needs (>= 18.0%)] Share (%) of county population with a disability."},
    {"name": "poverty_count", "description": "Total residents below the federal poverty level (`Count_Person_BelowPovertyLevelInThePast12Months`)."},
    {"name": "poverty_pct", "description": "[Knowledge Catalog Term: Poverty Rate (Below Federal Line >= 20.0%)] County poverty rate (%)."},
    {"name": "nri_risk_score", "description": "[Knowledge Catalog Term: Composite Hazard Risk Score (FEMA NRI >= 65.0)] FEMA National Risk Index composite multi-hazard risk percentile."},
    {"name": "nri_social_vulnerability_score", "description": "[Knowledge Catalog Term: Social Vulnerability Score (SVI Tier-1 >= 75.0)] FEMA NRI & CDC/ATSDR Social Vulnerability percentile."},
    {"name": "nri_community_resilience_score", "description": "[Knowledge Catalog Term: Community Resilience Index (FEMA NRI < 40.0 Alert)] FEMA NRI Community Resilience percentile."},
    {"name": "nri_expected_annual_loss_usd", "description": "[Knowledge Catalog Term: Expected Annual Disaster Loss (EAL >= $25M USD)] Expected annual economic loss in USD from natural hazards (`FemaExpectedAnnualLoss_NaturalHazardImpact`)."},
    {"name": "nri_flood_risk_score", "description": "FEMA NRI riverine & coastal flood hazard risk percentile."},
    {"name": "nri_hurricane_risk_score", "description": "FEMA NRI hurricane hazard risk percentile."},
    {"name": "nri_wildfire_risk_score", "description": "FEMA NRI wildfire hazard risk percentile."},
    {"name": "acs_year", "description": "U.S. Census American Community Survey 5-Year vintage (`2024`)."},
    {"name": "no_vehicle_households", "description": "Count of occupied housing units with zero vehicles available (`Count_Household_NoVehicleAvailable`)."},
    {"name": "no_vehicle_pct", "description": "[Knowledge Catalog Term: Transit-Isolated Households (No Vehicle >= 10.0%)] Percentage of households with zero vehicles available."},
    {"name": "median_household_income_usd", "description": "[Knowledge Catalog Term: Poverty Rate & Economic Equity] Median annual household income in USD (`Median_Income_Household`)."},
    {"name": "gmap_hybrid_uri", "description": "Google Maps Static API Satellite-Hybrid basemap tile URI."},
    {"name": "gmap_terrain_uri", "description": "Google Maps Static API Terrain-Roadmap basemap tile URI."},
]

STATE_PROFILE_FIELDS = [
    {"name": "state_id", "description": "Primary key U.S. State DCID (`geoId/01` to `geoId/72`, 51 states/territories). Joins with `Node.subject_id`."},
    {"name": "state_name", "description": "Official U.S. State name."},
    {"name": "state_code", "description": "2-letter USPS State code."},
    {"name": "census_division", "description": "U.S. Census Bureau Division (e.g., `East South Central`, `South Atlantic`, `Pacific`)."},
    {"name": "population", "description": "State resident population from U.S. Census ACS via Data Commons."},
    {"name": "population_year", "description": "Observation year for state population."},
    {"name": "population_change_5yr_pct", "description": "5-year state population growth percentage."},
    {"name": "households", "description": "Total occupied households in the state."},
    {"name": "no_internet_households", "description": "Statewide households lacking internet access."},
    {"name": "no_internet_pct", "description": "[Knowledge Catalog Term: Household Digital Divide] Statewide percentage of households without internet access."},
    {"name": "age_65_plus", "description": "Statewide population aged 65+."},
    {"name": "age_65_plus_pct", "description": "[Knowledge Catalog Term: Senior Population Share] Statewide percentage of residents aged 65+."},
    {"name": "disability_count", "description": "Statewide population with a disability."},
    {"name": "disability_pct", "description": "[Knowledge Catalog Term: Disability Access & Functional Needs] Statewide disability rate (%)."},
    {"name": "poverty_count", "description": "Statewide population living below the federal poverty threshold."},
    {"name": "poverty_pct", "description": "[Knowledge Catalog Term: Poverty Rate] Statewide poverty rate (%)."},
    {"name": "acs_year", "description": "U.S. Census ACS 5-Year survey vintage."},
]

DISASTER_SUMMARY_FIELDS = [
    {"name": "disaster_id", "description": "OpenFEMA Disaster node ID (`fema/DR-4834-FL`, `fema/DR-4828-NC`). Joins with `Node.subject_id`."},
    {"name": "disaster_number", "description": "Official FEMA Major Disaster Declaration number (`DR-4834`, `DR-4828`)."},
    {"name": "title", "description": "Official OpenFEMA disaster declaration title (e.g., `HURRICANE HELENE`, `SEVERE STORMS, STRAIGHT-LINE WINDS, AND TORNADOES`)."},
    {"name": "incident_type", "description": "FEMA hazard classification (`Hurricane`, `Severe Storm`, `Flood`, `Tornado`, `Fire`, `Winter Storm`)."},
    {"name": "declaration_date", "description": "Presidential Major Disaster Declaration date."},
    {"name": "fiscal_year", "description": "Federal Fiscal Year declared (`2023`–`2026`)."},
    {"name": "state_code", "description": "Designated USPS State code."},
    {"name": "designated_counties", "description": "Count of counties designated under the disaster declaration."},
    {"name": "ihp_counties", "description": "Count of counties authorized for FEMA Individual & Households Program (IHP) assistance."},
    {"name": "total_registrations", "description": "Total valid FEMA Individual Assistance registrations across all channels for this disaster."},
    {"name": "web_registrations", "description": "Registrations completed online via DisasterAssistance.gov."},
    {"name": "call_center_registrations", "description": "Registrations completed via FEMA Helpline Call Centers."},
    {"name": "mobile_registrations", "description": "Registrations completed in person via Mobile Disaster Recovery Units."},
    {"name": "web_share_pct", "description": "[Knowledge Catalog Term: Web Intake Channel Share (< 60.0% Drop-Off)] Percentage of disaster registrations submitted online."},
]

DISASTER_DESIGNATION_FIELDS = [
    {"name": "disaster_id", "description": "Foreign key to `Node.subject_id` (`fema/DR-*`)."},
    {"name": "county_id", "description": "Foreign key to `CountyProfile.county_id` and `Node.subject_id` (`geoId/*`)."},
    {"name": "state_code", "description": "USPS State abbreviation."},
    {"name": "ihp_declared", "description": "True if FEMA Individual and Households Program (IHP) was authorized for the county."},
    {"name": "pa_declared", "description": "True if FEMA Public Assistance (PA) infrastructure funding was authorized."},
    {"name": "hm_declared", "description": "True if FEMA Hazard Mitigation Grant Program (HMGP) was authorized."},
    {"name": "declaration_date", "description": "Official Presidential declaration date."},
    {"name": "incident_type", "description": "Primary hazard incident type."},
]

REGISTRATION_FIELDS = [
    {"name": "disaster_id", "description": "Foreign key to `Node.subject_id` (`fema/DR-*`) and `DisasterDesignation.disaster_id`."},
    {"name": "county_id", "description": "Foreign key to `CountyProfile.county_id` (`geoId/*`)."},
    {"name": "state_code", "description": "USPS State abbreviation."},
    {"name": "total_valid_registrations", "description": "Total valid OpenFEMA Individual Assistance registrations for this `(disaster_id, county_id)` pair."},
    {"name": "web_registrations", "description": "Online web registrations via DisasterAssistance.gov."},
    {"name": "call_center_registrations", "description": "Phone registrations via FEMA Call Centers."},
    {"name": "mobile_registrations", "description": "In-person field registrations via Mobile Disaster Recovery Units."},
    {"name": "web_share_pct", "description": "[Knowledge Catalog Term: Web Intake Channel Share (< 60.0% Drop-Off)] Share (%) of registrations completed online."},
    {"name": "call_center_share_pct", "description": "Share (%) of registrations completed via phone call centers."},
    {"name": "mobile_share_pct", "description": "Share (%) of registrations completed via mobile field teams."},
]

DEPLOYMENT_PLAN_FIELDS = [
    {"name": "county_id", "description": "Target U.S. County DCID (`geoId/*`), foreign key to `CountyProfile.county_id`, `CountyReadiness.county_id`, and `Node.subject_id`."},
    {"name": "action", "description": "[Knowledge Catalog Term: Federal Deployment Plan] Prescribed field intervention (`Deploy Mobile Team`, `Establish Recovery Center`, `Surge Call Center & Starlink Unit`)."},
    {"name": "assigned_team_id", "description": "[Knowledge Catalog Term: Federal Deployment Plan] Assigned Beacon Mobile DRC unit ID (`beacon/team/*`) from `DCGraph`."},
    {"name": "priority_tier", "description": "[Knowledge Catalog Term: Federal Deployment Plan (Cloud Spanner System of Action)] Dispatch tier (`Tier 1 - Immediate`, `Tier 2 - Secondary`)."},
    {"name": "rationale", "description": "Evidence-based operational justification citing Census ACS digital/vehicle deficits, FEMA NRI vulnerability, and OpenFEMA disaster history."},
    {"name": "added_by", "description": "Authorizing coordinator or Gemini Conversational Analytics / Looker Data App agent identity (`demo-operator@example.com`)."},
    {"name": "added_at", "description": "Cloud Spanner commit timestamp (`allow_commit_timestamp = true`) when the deployment order was persisted."},
    {"name": "status", "description": "[Knowledge Catalog Term: Federal Deployment Plan] Operational lifecycle status (`Proposed`, `Approved`, `Dispatched`)."},
]

MACRO_TIMELINE_FIELDS = [
    {"name": "year", "description": "Calendar year (1990–2025) for longitudinal U.S. national series (`country/USA`)."},
    {"name": "us_population", "description": "Total U.S. resident population from U.S. Census Bureau via Google Data Commons (`Count_Person`)."},
    {"name": "seniors_65_plus_population", "description": "Total U.S. population aged 65 years and older (`Count_Person_65OrMoreYears`)."},
    {"name": "seniors_65_plus_pct", "description": "[Knowledge Catalog Term: Senior Population Share (Aged 65+ >= 20.0%)] National share (%) of U.S. population aged 65+."},
    {"name": "median_household_income_usd", "description": "National U.S. median household income in USD (`Median_Income_Household`, Census ACS)."},
    {"name": "poverty_rate_pct", "description": "[Knowledge Catalog Term: Poverty Rate (Below Federal Line >= 20.0%)] National U.S. poverty rate percentage."},
    {"name": "no_internet_households_pct", "description": "[Knowledge Catalog Term: Household Digital Divide (No Internet >= 18.0%)] National share (%) of U.S. households without internet access."},
    {"name": "gdp_nominal_trillions_usd", "description": "U.S. Nominal Gross Domestic Product in Trillions USD (World Bank / BEA Data Commons)."},
    {"name": "gdp_per_capita_usd", "description": "U.S. Nominal GDP per capita in USD (`Amount_EconomicActivity_GrossDomesticProduction_Nominal_PerCapita`)."},
    {"name": "gdp_growth_pct", "description": "Annual U.S. real GDP growth rate percentage."},
    {"name": "fema_major_disasters_count", "description": "Annual count of Presidential Major Disaster Declarations across the United States (OpenFEMA)."},
    {"name": "billion_dollar_disasters_loss_usd_b", "description": "[Knowledge Catalog Term: Expected Annual Disaster Loss (EAL >= $25M USD)] Annual U.S. economic losses in Billions USD from climate and weather disasters (NOAA NCEI / FEMA)."},
    {"name": "ghg_emissions_mt_co2e", "description": "Annual U.S. greenhouse gas emissions in Mt CO2e (EPA / Climate TRACE Data Commons)."},
    {"name": "clean_electricity_share_pct", "description": "Share (%) of U.S. electricity generation from zero-carbon and renewable sources (EIA Data Commons)."},
]

FEDERAL_PROGRAM_FIELDS = [
    {"name": "program_id", "description": "Primary key identifier for the U.S. Federal disaster or equity program."},
    {"name": "program_name", "description": "Official federal program title (e.g., `FEMA Individual & Households Program (IHP)`, `NTIA BEAD Broadband Equity`, `FEMA BRIC Hazard Mitigation`, `HHS ASPR emPOWER`)."},
    {"name": "lead_agency", "description": "Accountable U.S. Federal Department/Agency (`FEMA & DHS`, `NTIA & FCC`, `HHS & CDC/ATSDR`, `HUD & DOT`)."},
    {"name": "policy_pillar", "description": "Strategic federal mission pillar (`Federal Response Operations`, `Digital & Transit Access`, `Hazard Risk & Resilience`, `Social Vulnerability & Equity`)."},
    {"name": "annual_budget_million_usd", "description": "Annual enacted program budget in Million USD."},
    {"name": "assisted_households", "description": "Total U.S. households assisted or covered in the current fiscal year."},
    {"name": "web_intake_share_pct", "description": "[Knowledge Catalog Term: Web Intake Channel Share (< 60.0% Drop-Off)] Percentage of program intake completed via web self-service."},
    {"name": "call_center_share_pct", "description": "Percentage of program intake completed via phone call centers."},
    {"name": "mobile_drc_share_pct", "description": "[Knowledge Catalog Term: Mobile Response Team Coverage Status (Beacon DRC)] Percentage of program intake completed via roving Mobile Disaster Recovery Centers."},
    {"name": "target_svi_threshold", "description": "[Knowledge Catalog Term: Social Vulnerability Score (SVI Tier-1 >= 75.0)] Target Social Vulnerability Index threshold for priority county qualification."},
]

KC_GOVERNANCE_FIELDS = [
    {"name": "rule_id", "description": "Primary key Knowledge Catalog Federal Governance contract ID (`KC-US-001` through `KC-US-016`)."},
    {"name": "business_term", "description": "[Knowledge Catalog Term: Social Vulnerability Score] Official Knowledge Catalog Business Glossary term display name."},
    {"name": "category", "description": "Knowledge Catalog Glossary policy category (`Social Vulnerability & Equity`, `Digital & Transit Access`, `Hazard Risk & Resilience`, `Federal Response Operations`)."},
    {"name": "governed_table", "description": "Governed Cloud Spanner table or view name in `readiness_dcgraph`."},
    {"name": "governed_column", "description": "Governed Cloud Spanner column name bound via Knowledge Catalog `definition` EntryLink."},
    {"name": "policy_threshold", "description": "Quantitative federal policy rule and dispatch threshold."},
    {"name": "federal_steward", "description": "Accountable U.S. Federal Agency Data Steward recorded in Knowledge Catalog Aspects."},
    {"name": "security_classification", "description": "FedRAMP & CUI security classification tier (`FedRAMP Moderate · Public`, `FedRAMP High · CUI`, `FedRAMP High · Official Action`)."},
    {"name": "datacommons_dcid", "description": "Upstream Google Data Commons statistical variable DCID or OpenFEMA / Spanner Graph lineage identifier."},
    {"name": "description", "description": "Authoritative business definition synchronized with `beacon-disaster-readiness-glossary`."},
]

ISO_GQL_QUERY_1 = """GRAPH DCGraph
MATCH p_main =
  (usa:country)<-[:containedinplace]-(reg:censusregion)<-[:containedinplace]-(div:censusdivision)<-[:containedinplace]-(st:state)<-[:containedinplace]-(c:county)
  <-[:recommended_for]-(team:team)-[:dispatchedfrom]->(hub:hub)
  <-[:funds_hub]-(prog:program)<-[:leads]-(ag:agency)-[:governedby]->(usa)
WHERE NOT EXISTS {
  MATCH (:team)-[:covers]->(c2:county)
  WHERE c2.subject_id = c.subject_id
}
OPTIONAL MATCH p_corridor = (c)-[:borders]->(neighbor:county)
RETURN
  TO_JSON(p_main) AS beacon_graph_path,
  TO_JSON(p_corridor) AS county_corridor_path,
  c.display_name AS county_name,
  st.name AS state_name,
  div.name AS census_division,
  reg.name AS census_region,
  team.display_name AS recommended_mobile_unit,
  hub.display_name AS regional_fema_hub,
  prog.display_name AS federal_program,
  ag.display_name AS lead_federal_agency
ORDER BY county_name ASC;"""

ISO_GQL_QUERY_2 = """GRAPH DCGraph
MATCH p = (na:continent)<-[:containedinplace]-(usa:country)<-[:containedinplace]-(reg:censusregion)<-[:containedinplace]-(div:censusdivision)<-[:containedinplace]-(st:state)<-[:containedinplace]-(c:county)<-[:affectedplace]-(d:disaster)
WHERE d.fy_declared >= 2024
RETURN
  TO_JSON(p) AS north_america_dc_path,
  na.name AS continent,
  usa.name AS country,
  reg.name AS census_region,
  div.name AS census_division,
  st.name AS state_name,
  c.display_name AS county_name,
  d.display_name AS disaster_declaration,
  d.incident_type AS incident_type
LIMIT 50;"""


def enrich_spanner_entries(headers: dict[str, str]) -> int:
    print("4. Enriching `@spanner` entries for `readiness_dcgraph` with 1P & Custom Aspects ...")

    entries_spec = [
        {
            "suffix": "tables/CountyReadiness",
            "description": (
                "Blue-Chip Certified analytical view (`CountyReadiness`) uniting 3,144 U.S. counties from Google Data Commons "
                "(U.S. Census ACS 5-Year demographics, broadband/vehicle access, and FEMA National Risk Index scores) with "
                "OpenFEMA Major Disaster Declarations (`DR-*`), Individual Assistance intake channels, and `DCGraph` Mobile DRC team coverage."
            ),
            "overview": (
                "<h3>U.S. Public Sector · Beacon County Disaster Readiness View (<code>CountyReadiness</code>)</h3>"
                "<p><b>Blue-Chip Certified</b> primary analytical view in Cloud Spanner (<code>readiness_dcgraph</code>) governed by "
                "the <b>Beacon Federal Readiness Office (FEMA)</b>, <b>U.S. Census Bureau</b>, and <b>CDC/ATSDR</b> "
                "(Principal Steward: <b>Sean Zinsmeister</b>, <code>demo-operator@example.com</code>).</p>"
                "<ul>"
                "<li><b>North America Data Commons Lineage (<code>country/USA</code>):</b> Harmonizes U.S. Census ACS 5-Year "
                "household broadband deficit (<code>no_internet_pct</code>), transit isolation (<code>no_vehicle_pct</code>), "
                "poverty rate (<code>poverty_pct</code>), senior density (<code>age_65_plus_pct</code>), disability share (<code>disability_pct</code>), "
                "and FEMA National Risk Index percentiles (<code>nri_risk_score</code>, <code>social_vulnerability_score</code>, <code>community_resilience_score</code>).</li>"
                "<li><b>OpenFEMA &amp; Spanner Graph Operational Intelligence:</b> Fuses county disaster counts since FY2023 "
                "(<code>disasters_since_2023</code>), online vs. call-center intake shares (<code>web_registration_pct</code>), "
                "and live Beacon Mobile DRC unit coverage (<code>has_team_coverage</code>) derived from <code>DCGraph</code>.</li>"
                "</ul>"
            ),
            "fields": COUNTY_READINESS_FIELDS,
            "steward": "FEMA Office of Response & Recovery, U.S. Census Bureau & CDC/ATSDR",
            "steward_email": "fema-nri-steward@fema.dhs.gov",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Justice40 Equity, FEMA Individual Assistance & Mobile DRC Operations",
            "dcids": "country/USA | FemaSocialVulnerability_NaturalHazardImpact, Count_Household_NoInternetAccess, Count_Household_NoVehicleAvailable, FemaNationalRisk_NaturalHazardImpact",
            "rule": "social_vulnerability_score >= 75.0 AND no_internet_pct >= 18.0% AND has_team_coverage = FALSE -> Tier-1 Mobile DRC Dispatch",
            "column_aspects": {
                "social_vulnerability_score": (
                    "FEMA Office of Response & Recovery & CDC/ATSDR",
                    "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
                    "Social Vulnerability & Equity (Justice40)",
                    "FemaSocialVulnerability_NaturalHazardImpact",
                    "social_vulnerability_score >= 75.0 designates Tier-1 Priority Dispatch County.",
                ),
                "no_internet_pct": (
                    "U.S. Census Bureau (ACS) & FCC/NTIA",
                    "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
                    "Digital & Transit Access (BEAD)",
                    "Count_Household_NoInternetAccess",
                    "no_internet_pct >= 18.0% triggers Mobile DRC & Call Center surge due to 17.8 pp online intake drop-off.",
                ),
                "no_vehicle_pct": (
                    "U.S. Census Bureau (ACS) & U.S. DOT / FEMA",
                    "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
                    "Digital & Transit Access",
                    "Count_Household_NoVehicleAvailable",
                    "no_vehicle_pct >= 10.0% mandates roving Mobile DRC deployment rather than fixed regional centers.",
                ),
                "nri_risk_score": (
                    "FEMA National Risk Index (NRI) & NOAA",
                    "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
                    "Hazard Risk & Resilience",
                    "FemaNationalRisk_NaturalHazardImpact",
                    "nri_risk_score >= 65.0 classifies county as High Multi-Hazard Exposure.",
                ),
                "community_resilience_score": (
                    "FEMA NRI & NIST",
                    "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
                    "Hazard Risk & Resilience",
                    "FemaCommunityResilience_NaturalHazardImpact",
                    "community_resilience_score < 40.0 triggers Low Recovery Capacity Alert.",
                ),
                "poverty_pct": (
                    "U.S. Census Bureau (ACS) & HHS",
                    "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
                    "Social Vulnerability & Equity",
                    "Count_Person_BelowPovertyLevelInThePast12Months",
                    "poverty_pct >= 20.0% designates Persistent Poverty County.",
                ),
                "age_65_plus_pct": (
                    "U.S. Census Bureau & HHS ACL",
                    "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
                    "Social Vulnerability & Equity",
                    "Count_Person_65OrMoreYears",
                    "age_65_plus_pct >= 20.0% triggers Aging Disaster Priority & HHS emPOWER protocol.",
                ),
                "disability_pct": (
                    "U.S. Census Bureau & FEMA ODI",
                    "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
                    "Social Vulnerability & Equity",
                    "Count_Person_WithDisability",
                    "disability_pct >= 18.0% mandates ADA Field Surge & ASL support.",
                ),
                "web_registration_pct": (
                    "FEMA Individual Assistance (IA) & USDS",
                    "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
                    "Federal Response Operations",
                    "OpenFEMA_WebRegistrationShare",
                    "web_registration_pct < 60.0% flags severe web intake drop-off.",
                ),
                "has_team_coverage": (
                    "Beacon Federal Readiness Office (FEMA)",
                    "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
                    "Federal Response Operations",
                    "SpannerGraph: (team)-[:covers]->(county)",
                    "has_team_coverage = FALSE in disaster-hit high-SVI counties triggers Tier-1 DeploymentPlan action.",
                ),
            },
            "queries": [
                {
                    "description": "1. Identify Priority Tier-1 unserved U.S. disaster counties with high social vulnerability and broadband deficits (Knowledge Catalog Verified Query).",
                    "sql": (
                        "SELECT county_name, state_code, latitude, longitude, social_vulnerability_score, "
                        "no_internet_pct, no_vehicle_pct, nri_risk_score, disasters_since_2023, total_registrations, web_registration_pct "
                        "FROM CountyReadiness WHERE NOT has_team_coverage AND disasters_since_2023 >= 1 "
                        "AND state_code NOT IN ('AK', 'HI', 'PR') ORDER BY social_vulnerability_score DESC LIMIT 25;"
                    ),
                    "source": "USER",
                    "sqlDialect": "GOOGLE_SQL",
                },
                {
                    "description": "2. Evaluate empirical correlation between Census ACS household broadband deficit (no_internet_pct) and OpenFEMA online registration rate (web_registration_pct).",
                    "sql": (
                        "SELECT c.county_name, c.state_code, c.no_internet_pct, r.total_valid_registrations, "
                        "r.web_share_pct, r.call_center_share_pct FROM CountyReadiness c JOIN Registration r "
                        "ON c.county_id = r.county_id WHERE r.total_valid_registrations >= 100 "
                        "ORDER BY r.total_valid_registrations DESC LIMIT 200;"
                    ),
                    "source": "USER",
                    "sqlDialect": "GOOGLE_SQL",
                },
            ],
        },
        {
            "suffix": "tables/CountyProfile",
            "description": (
                "Authoritative county-level socio-demographic, broadband/transit access, and FEMA National Risk Index table across "
                "all 3,144 U.S. counties (`geoId/*`), materialized from Google Data Commons (`Observation`) and U.S. Census ACS 5-Year Survey."
            ),
            "overview": (
                "<h3>U.S. County Demographic &amp; Hazard Risk Profile (<code>CountyProfile</code>)</h3>"
                "<p>Core base table in Cloud Spanner (<code>readiness_dcgraph</code>) storing normalized U.S. Census ACS 5-Year indicators "
                "and FEMA National Risk Index (NRI) scores across all 3,144 U.S. counties and county-equivalents.</p>"
            ),
            "fields": COUNTY_PROFILE_FIELDS,
            "steward": "U.S. Census Bureau (ACS) & FEMA National Risk Index (NRI)",
            "steward_email": "acs-data-steward@census.gov",
            "fedramp": "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
            "pillar": "Social Vulnerability, Digital Divide & Multi-Hazard Risk Baseline",
            "dcids": "country/USA | Count_Person, Count_Household_NoInternetAccess, Count_Household_NoVehicleAvailable, FemaNationalRisk_NaturalHazardImpact, FemaExpectedAnnualLoss_NaturalHazardImpact",
            "rule": "nri_expected_annual_loss_usd >= 25000000 USD qualifies counties for priority FEMA BRIC mitigation grants.",
            "column_aspects": {
                "nri_social_vulnerability_score": (
                    "FEMA NRI & CDC/ATSDR",
                    "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
                    "Social Vulnerability & Equity",
                    "FemaSocialVulnerability_NaturalHazardImpact",
                    "nri_social_vulnerability_score >= 75.0 designates Tier-1 Social Vulnerability.",
                ),
                "nri_expected_annual_loss_usd": (
                    "FEMA Hazard Mitigation Directorate",
                    "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
                    "Hazard Risk & Resilience (BRIC)",
                    "FemaExpectedAnnualLoss_NaturalHazardImpact",
                    "nri_expected_annual_loss_usd >= $25M USD/yr qualifies for priority BRIC hazard mitigation.",
                ),
            },
            "queries": [
                {
                    "description": "Top 15 U.S. counties by FEMA NRI Expected Annual Disaster Loss (EAL USD) and Social Vulnerability.",
                    "sql": (
                        "SELECT county_name, state_code, population, nri_risk_score, nri_social_vulnerability_score, "
                        "nri_community_resilience_score, nri_expected_annual_loss_usd FROM CountyProfile "
                        "ORDER BY nri_expected_annual_loss_usd DESC LIMIT 15;"
                    ),
                    "source": "USER",
                    "sqlDialect": "GOOGLE_SQL",
                }
            ],
        },
        {
            "suffix": "tables/StateProfile",
            "description": (
                "State-level U.S. Census Bureau ACS 5-Year demographic, broadband connectivity, senior share, disability, and poverty "
                "baselines across all 50 U.S. States and Territories (`geoId/01`–`geoId/72`) from Google Data Commons."
            ),
            "overview": (
                "<h3>U.S. State &amp; Territory Demographic Baseline (<code>StateProfile</code>)</h3>"
                "<p>Aggregated state-level U.S. Census ACS 5-Year indicators linked to <code>Node</code> (<code>label = 'state'</code>) "
                "and organized by U.S. Census Division.</p>"
            ),
            "fields": STATE_PROFILE_FIELDS,
            "steward": "U.S. Census Bureau (American Community Survey)",
            "steward_email": "acs-data-steward@census.gov",
            "fedramp": "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
            "pillar": "Federal-State Disaster Readiness & Census Baseline",
            "dcids": "country/USA | State-level Count_Person, Count_Household_NoInternetAccess, Count_Person_65OrMoreYears, Count_Person_BelowPovertyLevelInThePast12Months",
            "rule": "Provides state-level denominators for FEMA Region I–X readiness allocations.",
            "column_aspects": {},
            "queries": [],
        },
        {
            "suffix": "tables/DisasterSummary",
            "description": (
                "Governed analytical view (`DisasterSummary`) summarizing 263 Presidential Major Disaster Declarations (`DR-*`) since FY2023, "
                "joining `Node` (`label = 'disaster'`), `DisasterDesignation`, and `Registration` channel totals."
            ),
            "overview": (
                "<h3>OpenFEMA Major Disaster Declarations Summary View (<code>DisasterSummary</code>)</h3>"
                "<p>Aggregates county designations, Individual &amp; Households Program (IHP) activations, and omnichannel registration "
                "volumes (Web, Call Center, Mobile DRC) across 263 major federal disasters.</p>"
            ),
            "fields": DISASTER_SUMMARY_FIELDS,
            "steward": "FEMA Office of Response & Recovery (OpenFEMA)",
            "steward_email": "openfema-steward@fema.dhs.gov",
            "fedramp": "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
            "pillar": "Federal Emergency Response Operations",
            "dcids": "OpenFEMA API v2 | DisasterDeclarationsSummaries & RegistrationIntakeIndividualsHouseholdPrograms",
            "rule": "web_share_pct < 60.0% across a declared disaster triggers mobile intake surge.",
            "column_aspects": {},
            "queries": [
                {
                    "description": "Top 10 Presidential Major Disaster Declarations by total valid assistance registrations and web intake share.",
                    "sql": (
                        "SELECT disaster_number, title, incident_type, declaration_date, state_code, designated_counties, "
                        "total_registrations, web_share_pct FROM DisasterSummary WHERE total_registrations > 0 "
                        "ORDER BY total_registrations DESC LIMIT 10;"
                    ),
                    "source": "USER",
                    "sqlDialect": "GOOGLE_SQL",
                }
            ],
        },
        {
            "suffix": "tables/DisasterDesignation",
            "description": (
                "Per-county Presidential Major Disaster Declaration designations (`DisasterDesignation`) tracking Individual & Households "
                "Program (`ihp_declared`), Public Assistance (`pa_declared`), and Hazard Mitigation (`hm_declared`) authorizations."
            ),
            "overview": (
                "<h3>OpenFEMA County Disaster Designations (<code>DisasterDesignation</code>)</h3>"
                "<p>Links each <code>disaster_id</code> (<code>fema/DR-*</code>) to its designated <code>county_id</code> (<code>geoId/*</code>) "
                "with federal assistance program flags.</p>"
            ),
            "fields": DISASTER_DESIGNATION_FIELDS,
            "steward": "FEMA Office of Response & Recovery (OpenFEMA)",
            "steward_email": "openfema-steward@fema.dhs.gov",
            "fedramp": "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
            "pillar": "Federal Emergency Response Operations",
            "dcids": "OpenFEMA API v2 | DisasterDeclarationsSummaries",
            "rule": "Counties with >= 2 disaster designations since FY2023 are classified as Compounding Disaster Zones (KC-US-013).",
            "column_aspects": {},
            "queries": [],
        },
        {
            "suffix": "tables/Registration",
            "description": (
                "OpenFEMA Individual & Households Program (IHP) registration intake table (`Registration`) recording 5.3M+ valid household "
                "registrations by `(disaster_id, county_id)` broken down by Web, Call Center, and Mobile Recovery Team channels."
            ),
            "overview": (
                "<h3>OpenFEMA Assistance Registration Intake by Channel (<code>Registration</code>)</h3>"
                "<p>Captures survivor registration volume and channel mix (<code>web_share_pct</code>, <code>call_center_share_pct</code>, "
                "<code>mobile_share_pct</code>) across 1,847 disaster-impacted U.S. counties.</p>"
            ),
            "fields": REGISTRATION_FIELDS,
            "steward": "FEMA Individual Assistance (IA) Division & USDS",
            "steward_email": "fema-ia-steward@fema.dhs.gov",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Federal Emergency Response Operations & Digital Intake Equity",
            "dcids": "OpenFEMA API v2 | RegistrationIntakeIndividualsHouseholdPrograms",
            "rule": "web_share_pct < 60.0% indicates digital intake bottleneck requiring Mobile DRC and Call Center surge.",
            "column_aspects": {},
            "queries": [],
        },
        {
            "suffix": "tables/DeploymentPlan",
            "description": (
                "Transactional System-of-Action write-back table (`DeploymentPlan`) in Cloud Spanner recording approved Mobile Disaster "
                "Recovery Team dispatches, priority tiers, and operational rationales across unserved U.S. counties."
            ),
            "overview": (
                "<h3>Beacon Federal Deployment Plan — System of Action (<code>DeploymentPlan</code>)</h3>"
                "<p>Operational write-back table in Cloud Spanner closing the Agentic Data Cloud loop (<code>See &rarr; Show &rarr; Do</code>) "
                "from Gemini Conversational Analytics and Governed Looker Data Apps.</p>"
            ),
            "fields": DEPLOYMENT_PLAN_FIELDS,
            "steward": "Beacon Federal Readiness Office & FEMA Regions I–X",
            "steward_email": "beacon-ops-steward@fema.dhs.gov",
            "fedramp": "FEDRAMP_HIGH_OFFICIAL_ACTION",
            "pillar": "Federal Emergency Response & Mobile DRC System of Action",
            "dcids": "Beacon_SystemOfAction_DeploymentPlan",
            "rule": "Tier 1 - Immediate dispatches target unserved counties with SVI >= 75.0 and No Internet >= 15.0%.",
            "column_aspects": {
                "priority_tier": (
                    "Beacon Readiness Office & FEMA Regions I–X",
                    "FEDRAMP_HIGH_OFFICIAL_ACTION",
                    "Federal Response Operations",
                    "Beacon_SystemOfAction_DeploymentPlan",
                    "Tier 1 - Immediate Mobile DRC Dispatch for unserved high-SVI disaster counties.",
                ),
            },
            "queries": [
                {
                    "description": "Review active Federal Deployment Plan orders joined with CountyProfile demographics and vulnerability scores.",
                    "sql": (
                        "SELECT dp.county_id, cp.county_name, cp.state_code, dp.action, dp.assigned_team_id, "
                        "dp.priority_tier, dp.status, dp.added_by, dp.added_at, dp.rationale "
                        "FROM DeploymentPlan AS dp LEFT JOIN CountyProfile AS cp ON cp.county_id = dp.county_id "
                        "ORDER BY dp.added_at DESC;"
                    ),
                    "source": "USER",
                    "sqlDialect": "GOOGLE_SQL",
                }
            ],
        },
        {
            "suffix": "tables/NationalMacroTimeline",
            "description": (
                "Longitudinal U.S. macroeconomic, demographic, broadband, disaster loss, and climate time series (1990–2025) for "
                "`country/USA` from Google Data Commons (U.S. Census Bureau, BEA/World Bank, NOAA NCEI, OpenFEMA, EPA/EIA)."
            ),
            "overview": (
                "<h3>United States National Macro &amp; Disaster Timeline 1990–2025 (<code>NationalMacroTimeline</code>)</h3>"
                "<p>National longitudinal baseline tracking U.S. population growth, aging (`seniors_65_plus_pct`), broadband adoption, "
                "FEMA major disaster frequency, and NOAA billion-dollar disaster losses.</p>"
            ),
            "fields": MACRO_TIMELINE_FIELDS,
            "steward": "U.S. Census Bureau, NOAA NCEI & Bureau of Economic Analysis (BEA)",
            "steward_email": "macro-steward@commerce.gov",
            "fedramp": "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
            "pillar": "National Macroeconomic & Climate Resilience Baseline",
            "dcids": "country/USA | Count_Person, Count_Person_65OrMoreYears, Median_Income_Household, Amount_EconomicActivity_GrossDomesticProduction_Nominal",
            "rule": "Provides 35-year national context for rising disaster frequency and digital connectivity trends.",
            "column_aspects": {},
            "queries": [
                {
                    "description": "Longitudinal trend of U.S. FEMA Major Disasters, Billion-Dollar Disaster Losses, and Household Digital Divide (1990-2025).",
                    "sql": (
                        "SELECT year, us_population, seniors_65_plus_pct, no_internet_households_pct, "
                        "fema_major_disasters_count, billion_dollar_disasters_loss_usd_b "
                        "FROM NationalMacroTimeline ORDER BY year ASC;"
                    ),
                    "source": "USER",
                    "sqlDialect": "GOOGLE_SQL",
                }
            ],
        },
        {
            "suffix": "tables/FederalProgramSummary",
            "description": (
                "Executive scorecard of flagship U.S. Federal disaster assistance, hazard mitigation, broadband equity (BEAD), and "
                "vulnerable-population programs (`FederalProgramSummary`) tracking budget, assisted households, and intake channel shares."
            ),
            "overview": (
                "<h3>U.S. Federal Disaster &amp; Equity Program Summary (<code>FederalProgramSummary</code>)</h3>"
                "<p>Cross-agency PMO summary spanning FEMA Individual &amp; Public Assistance, BRIC Hazard Mitigation, NTIA BEAD Broadband, "
                "HUD CDBG-DR, and HHS ASPR emPOWER.</p>"
            ),
            "fields": FEDERAL_PROGRAM_FIELDS,
            "steward": "OMB, FEMA Office of Policy & Program Analysis & NTIA",
            "steward_email": "federal-programs-steward@omb.eop.gov",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Interagency Federal Disaster & Equity Programs",
            "dcids": "Beacon_FederalProgramSummary_FY2026",
            "rule": "Programs serving counties with target_svi_threshold >= 75.0 require hybrid Web + Call Center + Mobile DRC intake.",
            "column_aspects": {},
            "queries": [
                {
                    "description": "Compare annual enacted budget, assisted households, and intake channel shares across U.S. Federal disaster & equity programs.",
                    "sql": (
                        "SELECT program_id, program_name, lead_agency, policy_pillar, annual_budget_million_usd, "
                        "assisted_households, web_intake_share_pct, mobile_drc_share_pct, target_svi_threshold "
                        "FROM FederalProgramSummary ORDER BY annual_budget_million_usd DESC;"
                    ),
                    "source": "USER",
                    "sqlDialect": "GOOGLE_SQL",
                }
            ],
        },
        {
            "suffix": "tables/KnowledgeCatalogGovernance",
            "description": (
                "Authoritative Knowledge Catalog Federal Governance Registry (`KnowledgeCatalogGovernance`) mapping the 16 governed U.S. "
                "Public Sector contracts (`KC-US-001`–`KC-US-016`), policy thresholds, Federal Data Stewards, FedRAMP classifications, and "
                "Google Data Commons DCIDs to Cloud Spanner tables and columns."
            ),
            "overview": (
                "<h3>Knowledge Catalog Federal Governance Registry (<code>KnowledgeCatalogGovernance</code>)</h3>"
                "<p>Mirrors the active <b>Google Cloud Knowledge Catalog</b> metadata graph (<code>beacon-disaster-readiness-glossary</code> "
                "and <code>beacon-federal-governance</code> aspects) inside Cloud Spanner so Gemini Conversational Analytics and Looker agents can inspect "
                "and cite federal policy thresholds and stewards on demand.</p>"
            ),
            "fields": KC_GOVERNANCE_FIELDS,
            "steward": "Beacon Office of the Chief Data Officer & Sean Zinsmeister (demo-operator@example.com)",
            "steward_email": "demo-operator@example.com",
            "fedramp": "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
            "pillar": "OMB M-24-10 Federal AI & Data Governance",
            "dcids": "KnowledgeCatalog: beacon-disaster-readiness-glossary & beacon-federal-governance",
            "rule": "100% of executive AI metrics in Gemini Conversational Analytics must be Blue-Chip Certified with an assigned Federal Agency Steward and FedRAMP classification.",
            "column_aspects": {},
            "queries": [
                {
                    "description": "Inspect all 16 governed federal policy rules, thresholds, stewards, and Data Commons DCIDs in KnowledgeCatalogGovernance.",
                    "sql": (
                        "SELECT rule_id, business_term, category, governed_table, governed_column, "
                        "policy_threshold, federal_steward, security_classification, datacommons_dcid "
                        "FROM KnowledgeCatalogGovernance ORDER BY rule_id ASC;"
                    ),
                    "source": "USER",
                    "sqlDialect": "GOOGLE_SQL",
                }
            ],
        },
        {
            "suffix": "graphs/DCGraph",
            "description": (
                "Unified Cloud Spanner Property Graph (`DCGraph`) fusing the North America Google Data Commons geographic hierarchy "
                "(`NorthAmerica` -> `country/USA` -> 4 Census Regions -> 9 Census Divisions -> 51 States -> 3,144 Counties) and 13 "
                "StatisticalVariables with 263 OpenFEMA Major Disasters (`:affectedplace`) and Beacon Federal Response Operations "
                "(`agency` -> `program` -> `hub` -> `team` -> `:covers` / `:recommended_for` -> `county`)."
            ),
            "overview": (
                "<h3>North America Data Commons &amp; Beacon Federal Readiness Property Graph (<code>DCGraph</code>)</h3>"
                "<p>ISO/IEC 39075 GQL Property Graph in Cloud Spanner (<code>readiness_dcgraph</code>) uniting <b>3,546 nodes</b> and "
                "<b>7,777 directed edges</b> across three provenance domains in a single transactional engine:</p>"
                "<ol>"
                "<li><b>Google Data Commons (<code>datacommons.org</code>):</b> Continent &rarr; Country (<code>country/USA</code>) &rarr; "
                "Census Region &rarr; Census Division &rarr; State &rarr; County (<code>geoId/*</code>) + StatisticalVariables.</li>"
                "<li><b>OpenFEMA Program Data (<code>openfema</code>):</b> 263 Major Disaster Declarations (<code>fema/DR-*</code>) wired via "
                "<code>:affectedplace</code> to designated U.S. counties.</li>"
                "<li><b>Beacon Federal Operations (<code>beacon</code>):</b> Federal Agencies (FEMA, HHS, HUD, DOT/FCC) &rarr; "
                "<code>:leads</code> &rarr; Federal Programs &rarr; <code>:funds_hub</code> &rarr; 6 Regional FEMA Hubs &rarr; "
                "<code>:dispatchedfrom</code> &rarr; 46 Mobile DRC Teams &rarr; <code>:covers</code> / <code>:recommended_for</code> &rarr; U.S. Counties.</li>"
                "</ol>"
            ),
            "fields": [],
            "steward": "Beacon Federal Readiness Office, U.S. Census Bureau & Google Data Commons",
            "steward_email": "demo-operator@example.com",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Unified Knowledge Graph (North America Data Commons × OpenFEMA × Beacon DRC)",
            "dcids": "country/USA | DCGraph (Node + Edge ISO GQL Property Graph)",
            "rule": "Anti-join `WHERE NOT EXISTS { MATCH (:team)-[:covers]->(c) }` pinpoints unserved disaster-declared counties for Tier-1 mobile dispatch.",
            "column_aspects": {},
            "queries": [
                {
                    "description": "1. North America Data Commons x Federal Agency Unserved County Dispatch Loop (ISO GQL)",
                    "sql": ISO_GQL_QUERY_1,
                    "source": "USER",
                    "sqlDialect": "GOOGLE_SQL",
                },
                {
                    "description": "2. Pure North America Data Commons Geographic Hierarchy Traversal (ISO GQL)",
                    "sql": ISO_GQL_QUERY_2,
                    "source": "USER",
                    "sqlDialect": "GOOGLE_SQL",
                },
            ],
        },
        {
            "suffix": "tables/Node",
            "description": (
                "Unified vertex table (`Node`, 3,546 vertices) for `DCGraph` storing North America Data Commons places (`continent`, `country`, "
                "`censusregion`, `censusdivision`, `state`, `county`), `statisticalvariable` nodes, OpenFEMA `disaster` declarations, and "
                "Beacon federal operational entities (`agency`, `program`, `hub`, `team`)."
            ),
            "overview": (
                "<h3>DCGraph Unified Vertex Table (<code>Node</code>)</h3>"
                "<p>Single Spanner vertex table with dynamic label support (<code>LABEL Entity DYNAMIC LABEL (label)</code>) uniting public "
                "Data Commons DCIDs (<code>geoId/*</code>, <code>country/USA</code>) with OpenFEMA disasters (<code>fema/DR-*</code>) and "
                "Beacon response units (<code>beacon/team/*</code>, <code>beacon/hub/*</code>).</p>"
            ),
            "fields": [
                {"name": "subject_id", "description": "Primary key DCID (`geoId/21193`, `country/USA`) or federal entity ID (`fema/DR-4834`, `beacon/team/04`)."},
                {"name": "label", "description": "Dynamic node label (`continent`, `country`, `censusregion`, `censusdivision`, `state`, `county`, `statisticalvariable`, `disaster`, `hub`, `team`, `agency`, `program`)."},
                {"name": "name", "description": "Short canonical entity name (e.g., `Owsley County`, `DR-4834`)."},
                {"name": "display_name", "description": "Disambiguated executive display label (e.g., `Owsley County, KY`, `Bolivar County, MS (SVI: 98.7 · No Net: 16.8% · DRs: 1)`)."},
                {"name": "provenance", "description": "Authoritative source domain (`datacommons.org`, `openfema`, `beacon`)."},
                {"name": "state_code", "description": "2-letter USPS State code."},
                {"name": "latitude", "description": "WGS84 centroid latitude."},
                {"name": "longitude", "description": "WGS84 centroid longitude."},
                {"name": "description", "description": "StatisticalVariable definition or disaster summary description."},
                {"name": "incident_type", "description": "FEMA disaster incident type (`Hurricane`, `Flood`, `Severe Storm`, `Tornado`, `Fire`)."},
                {"name": "declaration_date", "description": "Presidential disaster declaration date."},
                {"name": "fy_declared", "description": "Federal fiscal year declared."},
                {"name": "hub_region", "description": "FEMA / Beacon Hub Region (`Southeast`, `Gulf Coast`, `Midwest`, `Northeast`, `West`, `Pacific`)."},
                {"name": "capacity", "description": "Daily intake registration or operational capacity."},
            ],
            "steward": "U.S. Census Bureau, OpenFEMA & Beacon Knowledge Graph Team",
            "steward_email": "demo-operator@example.com",
            "fedramp": "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
            "pillar": "Unified Knowledge Graph Foundation",
            "dcids": "country/USA | 3,144 Counties, 51 States, 263 Disasters, 46 Mobile Teams, 6 Hubs",
            "rule": "Every county node (`label = 'county'`) joins 1:1 with `CountyProfile.county_id` and `CountyReadiness.county_id`.",
            "column_aspects": {},
            "queries": [],
        },
        {
            "suffix": "tables/Edge",
            "description": (
                "Interleaved directed edge table (`Edge`, 7,777 edges, `INTERLEAVE IN PARENT Node`) for `DCGraph` connecting entities via "
                "dynamic predicates (`containedinplace`, `affectedplace`, `covers`, `locatedin`, `serves`, `recommended_for`, `dispatchedfrom`, "
                "`funds_hub`, `leads`, `governedby`, `borders`)."
            ),
            "overview": (
                "<h3>DCGraph Interleaved Directed Edge Table (<code>Edge</code>)</h3>"
                "<p>Physically co-located with parent <code>Node</code> rows in Cloud Spanner for zero-network-hop ISO GQL graph traversals.</p>"
            ),
            "fields": [
                {"name": "subject_id", "description": "Source vertex ID (`Node.subject_id`)."},
                {"name": "predicate", "description": "Dynamic edge label (`containedinplace`, `affectedplace`, `covers`, `locatedin`, `serves`, `recommended_for`, `dispatchedfrom`, `funds_hub`, `leads`, `governedby`, `borders`)."},
                {"name": "object_id", "description": "Target vertex ID (`Node.subject_id`)."},
                {"name": "provenance", "description": "Edge provenance (`datacommons.org`, `openfema`, `beacon`)."},
            ],
            "steward": "Beacon Federal Readiness Office & Google Data Commons",
            "steward_email": "demo-operator@example.com",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Unified Knowledge Graph Foundation",
            "dcids": "country/USA | DCGraph Directed Relationships",
            "rule": "Edges with `predicate = 'covers'` and `provenance = 'beacon'` define active Mobile DRC coverage.",
            "column_aspects": {},
            "queries": [],
        },
        {
            "suffix": "tables/Observation",
            "description": (
                "Canonical Google Data Commons Statistical Observation table (`Observation`) storing county, state, and national time-series "
                "measurements (`value`, `observation_date`, `unit`, `provenance_url`) for `observation_about` (Place DCID) and "
                "`variable_measured` (StatisticalVariable DCID)."
            ),
            "overview": (
                "<h3>Google Data Commons Statistical Observations (<code>Observation</code>)</h3>"
                "<p>Stores raw U.S. Census Bureau ACS 5-Year Survey and FEMA National Risk Index observations with full DCID and URL provenance.</p>"
            ),
            "fields": [
                {"name": "observation_about", "description": "Target Place DCID (`Node.subject_id`, e.g., `geoId/28151`, `country/USA`)."},
                {"name": "variable_measured", "description": "StatisticalVariable DCID (`Node.subject_id`, e.g., `Count_Household_NoInternetAccess`, `FemaSocialVulnerability_NaturalHazardImpact`)."},
                {"name": "observation_date", "description": "Observation year or period (`YYYY` or `YYYY-MM`)."},
                {"name": "value", "description": "Numeric observation value."},
                {"name": "measurement_method", "description": "Census ACS or FEMA NRI estimation methodology."},
                {"name": "observation_period", "description": "Observation duration (e.g., `P5Y` for ACS 5-Year)."},
                {"name": "unit", "description": "Unit of measure (`Percent`, `USD`, `Person`, `Household`)."},
                {"name": "provenance_id", "description": "Data Commons provenance identifier (`census.gov`, `fema.gov`)."},
                {"name": "provenance_url", "description": "Authoritative upstream federal source URL."},
            ],
            "steward": "U.S. Census Bureau, FEMA NRI & Google Data Commons",
            "steward_email": "datacommons-steward@google.com",
            "fedramp": "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
            "pillar": "Public Statistical Ground Truth (Data Commons)",
            "dcids": "country/USA | All 13 Census ACS & FEMA NRI StatisticalVariables",
            "rule": "Every observation retains its canonical Data Commons `variable_measured` DCID and upstream federal `provenance_url`.",
            "column_aspects": {},
            "queries": [],
        },
    ]

    patched_count = 0
    for spec in entries_spec:
        entry_name = f"{SPANNER_ENTRY_PREFIX}/{spec['suffix']}"
        st_check, _ = api_call("GET", f"https://dataplex.googleapis.com/v1/{entry_name}", headers)
        if st_check != 200:
            print(f"   [Note] Entry `{spec['suffix']}` not found (status {st_check}); skipping.")
            continue

        aspects_payload: dict[str, Any] = {
            "655216118709.global.overview": {
                "aspectType": "projects/655216118709/locations/global/aspectTypes/overview",
                "data": {"content": spec["overview"], "contentType": "HTML"},
            },
            "655216118709.global.contacts": {
                "aspectType": "projects/655216118709/locations/global/aspectTypes/contacts",
                "data": {
                    "identities": [
                        {"role": "steward", "name": "Sean Zinsmeister (Principal Steward · Google Data Cloud)", "id": "demo-operator@example.com"},
                        {"role": "steward", "name": spec["steward"], "id": spec["steward_email"]},
                        {"role": "owner", "name": "Beacon Federal Readiness Office (FEMA / Census / HHS / HUD)", "id": "demo-operator@example.com"},
                    ]
                },
            },
            f"{PROJECT_NUM}.us-central1.data-governance": {
                "aspectType": f"projects/{PROJECT_NUM}/locations/us-central1/aspectTypes/data-governance",
                "data": {
                    "certification_tier": "Gold — Blue-Chip Certified",
                    "data_steward": f"Sean Zinsmeister (demo-operator@example.com) & {spec['steward']}",
                    "compliance_scope": "U.S. Federal FISMA / FedRAMP High / OMB M-24-10 / OpenFEMA",
                    "last_governance_audit": "2026-09-28",
                },
            },
            f"{PROJECT_NUM}.us-central1.{ASPECT_TYPE_ID}": {
                "aspectType": f"projects/{PROJECT_NUM}/locations/us-central1/aspectTypes/{ASPECT_TYPE_ID}",
                "data": {
                    "federal_agency_steward": spec["steward"],
                    "fedramp_security_classification": spec["fedramp"],
                    "certification_status": "BLUE_CHIP_CERTIFIED",
                    "federal_policy_pillar": spec["pillar"],
                    "data_commons_dcids": spec["dcids"],
                    "policy_threshold_rule": spec["rule"],
                },
            },
            "655216118709.global.descriptions": {
                "aspectType": "projects/655216118709/locations/global/aspectTypes/descriptions",
                "data": {
                    "description": spec["description"],
                    "userManaged": True,
                    **({"fields": spec["fields"]} if spec["fields"] else {}),
                },
            },
        }

        # Attach column-level `beacon-federal-governance` aspects on governed schema columns
        for col_name, (c_steward, c_fedramp, c_pillar, c_dcid, c_rule) in spec.get("column_aspects", {}).items():
            aspects_payload[f"{PROJECT_NUM}.us-central1.{ASPECT_TYPE_ID}@Schema.{col_name}"] = {
                "aspectType": f"projects/{PROJECT_NUM}/locations/us-central1/aspectTypes/{ASPECT_TYPE_ID}",
                "data": {
                    "federal_agency_steward": c_steward,
                    "fedramp_security_classification": c_fedramp,
                    "certification_status": "BLUE_CHIP_CERTIFIED",
                    "federal_policy_pillar": c_pillar,
                    "data_commons_dcids": c_dcid,
                    "policy_threshold_rule": c_rule,
                },
            }

        if spec["queries"]:
            aspects_payload["655216118709.global.queries"] = {
                "aspectType": "projects/655216118709/locations/global/aspectTypes/queries",
                "data": {
                    "userManaged": True,
                    "queries": spec["queries"],
                },
            }

        st_p, res_p = api_call(
            "PATCH",
            f"https://dataplex.googleapis.com/v1/{entry_name}?updateMask=aspects",
            headers,
            {"name": entry_name, "aspects": aspects_payload},
        )
        if st_p == 200:
            patched_count += 1
        print(f"   Patched entry `{spec['suffix']}` with 1P + Custom Governance Aspects ({len(spec.get('column_aspects', {}))} col aspects) -> {st_p}")
        if st_p != 200:
            print(f"     [Warn] Error patching {spec['suffix']}: {str(res_p)[:300]}")

    return patched_count


# =============================================================================
# 4B. Enrich Native `@looker` (LookML Views, Explore, Model, Dashboard 519)
#     and `@bigquery` Federated Tables in Knowledge Catalog
# =============================================================================

LOOKER_ENTRY_PREFIX = (
    f"projects/{PROJECT_NUM}/locations/us-east1/entryGroups/@looker/entries/"
    f"looker.googleapis.com/projects/{PROJECT_ID}/locations/us-east1/instances/cloud-bi-opm"
)
LOOKML_MODEL_PREFIX = f"{LOOKER_ENTRY_PREFIX}/lookml_projects/singapore_smart_nation/models/singapore_smart_nation"

BQ_ENTRY_PREFIX = (
    f"projects/{PROJECT_NUM}/locations/us/entryGroups/@bigquery/entries/"
    f"bigquery.googleapis.com/projects/{PROJECT_ID}/datasets/beacon_disaster_readiness"
)

LOOKER_DASHBOARD_519_ELEMENTS = [
    ("2838", "Hero Banner — U.S. Public Sector · Beacon Disaster Readiness & Policy Intelligence"),
    ("2839", "KPI Card 1 — U.S. Population (Census ACS / Data Commons)"),
    ("2840", "KPI Card 2 — FEMA Disaster Registrations (OpenFEMA IA)"),
    ("2841", "KPI Card 3 — Avg Household Digital Divide % (No Internet)"),
    ("2842", "KPI Card 4 — Avg Social Vulnerability Score (FEMA NRI)"),
    ("2843", "Scatter Plot — Household Digital Divide (No Internet %) vs. Web Registration Share % Across U.S. Disaster Counties"),
    ("2844", "Horizontal Bar — Top 10 Unserved High-Vulnerability U.S. Disaster Counties (No Mobile DRC Coverage)"),
    ("2845", "Stacked Area — U.S. Census & Data Commons Population & Seniors (65+) Trajectory (1970–2025)"),
    ("2846", "Stacked Bar — FEMA Disaster Assistance Intake Channel Mix by State (Web vs. Call Center)"),
    ("2847", "Donut Chart — Federal Disaster & Resilience Annual Budget ($M USD) by Policy Pillar"),
    ("2848", "Grouped Column — Compounding Disasters & Mobile Response Coverage by Top Disaster States"),
    ("2849", "Multi-Series Line — NOAA / FEMA Billion-Dollar Disaster Losses ($B) & Major Declarations (2000–2025)"),
    ("2850", "Action Grid Table — Cloud Spanner System of Action: Active Federal Mobile DRC Deployment Plan"),
]


def enrich_looker_and_bigquery_entries(headers: dict[str, str]) -> tuple[int, int]:
    print("4B. Enriching Native `@looker` (LookML Views, Unified Explore, Model, Dashboard 519) & `@bigquery` Entries ...")

    looker_specs = [
        {
            "entry_name": f"{LOOKER_ENTRY_PREFIX}/lookml_projects/singapore_smart_nation",
            "label": "lookml_projects/singapore_smart_nation",
            "description": (
                "Governed Looker Core LookML Semantic Layer Project (`singapore_smart_nation` / Beacon U.S. Public Sector) "
                "defining certified dimensions, measures, joins, and executive dashboards over Cloud Spanner Graph (`readiness_dcgraph`) "
                "and Google Data Commons (`country/USA`)."
            ),
            "overview": (
                "<h3>LookML Semantic Layer Project — Beacon U.S. Public Sector &amp; Data Commons (<code>singapore_smart_nation</code>)</h3>"
                "<p><b>Blue-Chip Certified</b> Looker Core LookML project on <code>cloud-bi-opm</code> governed by Principal Steward "
                "<b>Sean Zinsmeister</b> (<code>demo-operator@example.com</code>) and the <b>Beacon Federal Readiness Office</b>. "
                "Provides a single governed semantic layer uniting 4 LookML views (<code>beacon_county_readiness</code>, "
                "<code>beacon_deployment_plan</code>, <code>beacon_national_macro_timeline</code>, <code>beacon_federal_program_summary</code>), "
                "the unified LookML Explore (<code>beacon_county_readiness</code>), and Looker Executive Dashboard <code>519</code>.</p>"
            ),
            "steward": "Sean Zinsmeister (demo-operator@example.com) & Beacon Federal Readiness Office",
            "steward_email": "demo-operator@example.com",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "LookML Universal Semantic Layer & Governed BI",
            "dcids": "country/USA | LookML Views: beacon_county_readiness, beacon_deployment_plan, beacon_national_macro_timeline, beacon_federal_program_summary",
            "rule": "All executive BI tiles and Data App simulations resolve metrics exclusively through governed LookML definitions.",
            "fields": [],
            "column_aspects": {},
        },
        {
            "entry_name": LOOKML_MODEL_PREFIX,
            "label": "models/singapore_smart_nation",
            "description": (
                "Governed LookML Model (`singapore_smart_nation`) exposing the unified `beacon_county_readiness` Explore "
                "with pre-joined `beacon_deployment_plan`, `beacon_national_macro_timeline`, and `beacon_federal_program_summary` views."
            ),
            "overview": (
                "<h3>LookML Semantic Model (<code>models/singapore_smart_nation</code>)</h3>"
                "<p>Defines governed database connections, caching policies, and the unified <code>beacon_county_readiness</code> Explore "
                "powering Looker Executive Dashboard <code>519</code> with 100% single-Explore cross-filtering across all 13 tiles.</p>"
            ),
            "steward": "Sean Zinsmeister (demo-operator@example.com) & FEMA ORR / U.S. Census Bureau",
            "steward_email": "demo-operator@example.com",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "LookML Semantic Model & Single-Explore Cross-Filtering",
            "dcids": "country/USA | Explore: beacon_county_readiness",
            "rule": "Joins `beacon_deployment_plan` (LEFT OUTER on `county_id`), `beacon_national_macro_timeline`, and `beacon_federal_program_summary` into a single governed Explore.",
            "fields": [],
            "column_aspects": {},
        },
        {
            "entry_name": f"{LOOKML_MODEL_PREFIX}/views/beacon_county_readiness",
            "label": "views/beacon_county_readiness",
            "description": (
                "Blue-Chip Certified LookML View (`beacon_county_readiness`) governing 24 dimensions and 9 measures across "
                "3,144 U.S. counties from Cloud Spanner (`CountyReadiness`) and Google Data Commons (`country/USA`: U.S. Census ACS 5-Year & FEMA NRI)."
            ),
            "overview": (
                "<h3>LookML Semantic View — U.S. County Disaster Readiness (<code>views/beacon_county_readiness</code>)</h3>"
                "<p><b>Blue-Chip Certified</b> LookML view mapping Cloud Spanner's <code>CountyReadiness</code> view and federated BigQuery "
                "table (<code>beacon_disaster_readiness.county_readiness</code>) into governed Looker dimensions and measures:</p>"
                "<ul>"
                "<li><b>Governed Dimensions:</b> <code>county_id</code> (PK), <code>county_name</code>, <code>state_code</code>, "
                "<code>social_vulnerability_score</code>, <code>no_internet_pct</code>, <code>no_vehicle_pct</code>, "
                "<code>nri_risk_score</code>, <code>community_resilience_score</code>, <code>poverty_pct</code>, "
                "<code>age_65_plus_pct</code>, <code>disability_pct</code>, <code>web_registration_pct</code>, <code>has_team_coverage</code>, "
                "<code>coverage_status_label</code>, and <code>vulnerability_tier</code>.</li>"
                "<li><b>Governed Measures:</b> <code>total_population</code>, <code>total_households</code>, "
                "<code>total_fema_registrations</code>, <code>avg_no_internet_pct</code>, <code>avg_social_vulnerability_score</code>, "
                "<code>avg_nri_risk_score</code>, <code>avg_web_registration_pct</code>, and <code>unserved_high_vulnerability_counties</code>.</li>"
                "</ul>"
            ),
            "steward": "FEMA Office of Response & Recovery, U.S. Census Bureau & Sean Zinsmeister",
            "steward_email": "fema-nri-steward@fema.dhs.gov",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "LookML Semantic View — County Vulnerability, Broadband & FEMA Intake",
            "dcids": "country/USA | FemaSocialVulnerability_NaturalHazardImpact, Count_Household_NoInternetAccess, Count_Household_NoVehicleAvailable, FemaNationalRisk_NaturalHazardImpact",
            "rule": "social_vulnerability_score >= 75.0 AND no_internet_pct >= 18.0% AND has_team_coverage = FALSE -> Tier-1 Mobile DRC Dispatch",
            "fields": [
                {"name": "county_id", "description": "Primary key U.S. County DCID (`geoId/*`, 3,144 counties) sourced from Cloud Spanner `CountyReadiness.county_id`."},
                {"name": "county_name", "description": "Disambiguated U.S. County & State name (`Perry County, KY`, `Washington County, MS`)."},
                {"name": "state_code", "description": "2-letter USPS State code."},
                {"name": "state_name", "description": "Official U.S. State name."},
                {"name": "social_vulnerability_score", "description": "[Knowledge Catalog Term: Social Vulnerability Score (SVI Tier-1 >= 75.0)] Governed LookML dimension for CDC/ATSDR & FEMA NRI Social Vulnerability percentile."},
                {"name": "no_internet_pct", "description": "[Knowledge Catalog Term: Household Digital Divide (No Internet >= 18.0%)] Governed LookML dimension for Census ACS percentage of households without internet access."},
                {"name": "no_vehicle_pct", "description": "[Knowledge Catalog Term: Transit-Isolated Households (No Vehicle >= 10.0%)] Governed LookML dimension for Census ACS percentage of households with zero vehicles."},
                {"name": "nri_risk_score", "description": "[Knowledge Catalog Term: Composite Hazard Risk Score (FEMA NRI >= 65.0)] Governed LookML dimension for FEMA NRI multi-hazard risk score."},
                {"name": "community_resilience_score", "description": "[Knowledge Catalog Term: Community Resilience Index (FEMA NRI < 40.0 Alert)] Governed LookML dimension for FEMA NRI community resilience percentile."},
                {"name": "poverty_pct", "description": "[Knowledge Catalog Term: Poverty Rate (Below Federal Line >= 20.0%)] Governed LookML dimension for county poverty rate (%)."},
                {"name": "age_65_plus_pct", "description": "[Knowledge Catalog Term: Senior Population Share (Aged 65+ >= 20.0%)] Governed LookML dimension for share of population aged 65+."},
                {"name": "disability_pct", "description": "[Knowledge Catalog Term: Disability Access & Functional Needs (>= 18.0%)] Governed LookML dimension for share of population with a disability."},
                {"name": "web_registration_pct", "description": "[Knowledge Catalog Term: Web Intake Channel Share (< 60.0% Drop-Off)] Governed LookML dimension for OpenFEMA online web registration share (%)."},
                {"name": "has_team_coverage", "description": "[Knowledge Catalog Term: Mobile Response Team Coverage Status (Beacon DRC)] Governed LookML dimension indicating active `:covers` edge in `DCGraph`."},
                {"name": "avg_social_vulnerability_score", "description": "[Knowledge Catalog Term: Social Vulnerability Score] Governed LookML measure computing average FEMA/CDC SVI score."},
                {"name": "avg_no_internet_pct", "description": "[Knowledge Catalog Term: Household Digital Divide] Governed LookML measure computing average household internet deficit (%)."},
                {"name": "total_fema_registrations", "description": "Governed LookML measure summing valid OpenFEMA Individual Assistance registrations."},
                {"name": "unserved_high_vulnerability_counties", "description": "Governed LookML filtered measure counting disaster-impacted counties with `social_vulnerability_score >= 75` and `has_team_coverage = FALSE`."},
            ],
            "column_aspects": {
                "social_vulnerability_score": (
                    "FEMA Office of Response & Recovery & CDC/ATSDR",
                    "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
                    "Social Vulnerability & Equity (Justice40)",
                    "FemaSocialVulnerability_NaturalHazardImpact",
                    "social_vulnerability_score >= 75.0 designates Tier-1 Priority Dispatch County.",
                ),
                "no_internet_pct": (
                    "U.S. Census Bureau (ACS) & FCC/NTIA",
                    "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
                    "Digital & Transit Access (BEAD)",
                    "Count_Household_NoInternetAccess",
                    "no_internet_pct >= 18.0% triggers Mobile DRC & Call Center surge.",
                ),
                "no_vehicle_pct": (
                    "U.S. Census Bureau (ACS) & U.S. DOT / FEMA",
                    "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
                    "Digital & Transit Access",
                    "Count_Household_NoVehicleAvailable",
                    "no_vehicle_pct >= 10.0% mandates roving Mobile DRC deployment.",
                ),
                "nri_risk_score": (
                    "FEMA National Risk Index (NRI) & NOAA",
                    "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
                    "Hazard Risk & Resilience",
                    "FemaNationalRisk_NaturalHazardImpact",
                    "nri_risk_score >= 65.0 classifies county as High Multi-Hazard Exposure.",
                ),
                "web_registration_pct": (
                    "FEMA Individual Assistance (IA) & USDS",
                    "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
                    "Federal Response Operations",
                    "OpenFEMA_WebRegistrationShare",
                    "web_registration_pct < 60.0% flags severe web intake drop-off.",
                ),
                "has_team_coverage": (
                    "Beacon Federal Readiness Office (FEMA)",
                    "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
                    "Federal Response Operations",
                    "SpannerGraph: (team)-[:covers]->(county)",
                    "has_team_coverage = FALSE in disaster-hit high-SVI counties triggers Tier-1 DeploymentPlan action.",
                ),
            },
        },
        {
            "entry_name": f"{LOOKML_MODEL_PREFIX}/views/beacon_deployment_plan",
            "label": "views/beacon_deployment_plan",
            "description": (
                "Governed LookML View (`beacon_deployment_plan`) over Cloud Spanner's `DeploymentPlan` System of Action table, "
                "enabling Looker Actions API write-back and executive tracking of Tier-1 & Tier-2 Mobile DRC dispatches."
            ),
            "overview": (
                "<h3>LookML Semantic View — Federal Mobile DRC Deployment Plan (<code>views/beacon_deployment_plan</code>)</h3>"
                "<p>Joined into the unified <code>beacon_county_readiness</code> Explore via <code>county_id</code> so executive "
                "dashboards and Looker Data Apps can inspect and trigger live Mobile DRC fleet dispatches in Cloud Spanner.</p>"
            ),
            "steward": "Beacon Federal Readiness Office (FEMA) & Sean Zinsmeister",
            "steward_email": "demo-operator@example.com",
            "fedramp": "FEDRAMP_HIGH_OFFICIAL_ACTION",
            "pillar": "Cloud Spanner System of Action & Looker Actions Write-Back",
            "dcids": "Spanner: readiness_dcgraph.DeploymentPlan",
            "rule": "Joined LEFT OUTER on `county_id` in `explore: beacon_county_readiness`.",
            "fields": [
                {"name": "county_id", "description": "Target U.S. County DCID (`geoId/*`)."},
                {"name": "action", "description": "[Knowledge Catalog Term: Federal Deployment Plan] Prescribed intervention (`Deploy Mobile Team`, `Establish Recovery Center`)."},
                {"name": "assigned_team_id", "description": "[Knowledge Catalog Term: Federal Deployment Plan] Assigned Beacon Mobile DRC unit ID (`beacon/team/*`)."},
                {"name": "priority_tier", "description": "[Knowledge Catalog Term: Federal Deployment Plan] Priority dispatch tier (`Tier 1 - Immediate`, `Tier 2 - Secondary`)."},
                {"name": "status", "description": "[Knowledge Catalog Term: Federal Deployment Plan] Operational status (`Proposed`, `Approved`, `Dispatched`)."},
            ],
            "column_aspects": {},
        },
        {
            "entry_name": f"{LOOKML_MODEL_PREFIX}/views/beacon_national_macro_timeline",
            "label": "views/beacon_national_macro_timeline",
            "description": (
                "Governed LookML View (`beacon_national_macro_timeline`) exposing 1970–2025 longitudinal U.S. Census, BEA, "
                "EPA, and NOAA/FEMA billion-dollar disaster series (`country/USA`) from Cloud Spanner `NationalMacroTimeline`."
            ),
            "overview": (
                "<h3>LookML Semantic View — U.S. National Macro &amp; Disaster Trajectory (<code>views/beacon_national_macro_timeline</code>)</h3>"
                "<p>Provides governed longitudinal dimensions and measures (`us_population`, `seniors_65_plus_pct`, "
                "`billion_dollar_disasters_loss_usd_b`, `fema_major_disasters_count`) joined into the unified `beacon_county_readiness` Explore.</p>"
            ),
            "steward": "U.S. Census Bureau, NOAA NCEI & FEMA",
            "steward_email": "datacommons-steward@google.com",
            "fedramp": "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
            "pillar": "Longitudinal U.S. Demographic & Climate Hazard Baseline (1970–2025)",
            "dcids": "country/USA | Count_Person, Count_Person_65OrMoreYears, FemaExpectedAnnualLoss_NaturalHazardImpact",
            "rule": "Provides 56-year national macro trends for Looker Dashboard 519 KPI sparklines and historical trajectory tiles.",
            "fields": [
                {"name": "year", "description": "Observation year (`1970`–`2025`)."},
                {"name": "us_population", "description": "U.S. resident population (`Count_Person`, Census/Data Commons)."},
                {"name": "seniors_65_plus_pct", "description": "[Knowledge Catalog Term: Senior Population Share] National share (%) of U.S. residents aged 65+."},
                {"name": "billion_dollar_disasters_loss_usd_b", "description": "[Knowledge Catalog Term: Expected Annual Disaster Loss] Annual U.S. billion-dollar disaster losses ($B USD)."},
            ],
            "column_aspects": {},
        },
        {
            "entry_name": f"{LOOKML_MODEL_PREFIX}/views/beacon_federal_program_summary",
            "label": "views/beacon_federal_program_summary",
            "description": (
                "Governed LookML View (`beacon_federal_program_summary`) modeling 10 U.S. Federal disaster, broadband equity, "
                "and social vulnerability programs across FEMA, NTIA/FCC, HHS/CDC, and HUD/DOT (`$19.95B USD` annual budget)."
            ),
            "overview": (
                "<h3>LookML Semantic View — U.S. Federal Disaster &amp; Resilience Programs (<code>views/beacon_federal_program_summary</code>)</h3>"
                "<p>Governs federal program budgets, assisted household counts, and intake channel shares across 7 policy pillars.</p>"
            ),
            "steward": "OMB, FEMA, NTIA/FCC, HHS & HUD",
            "steward_email": "demo-operator@example.com",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Cross-Agency Federal Program Budget & Intake Governance",
            "dcids": "country/USA | FederalProgramSummary (10 Federal Programs)",
            "rule": "Governs the Policy Pillar Donut Chart and cross-agency program allocation metrics on Looker Dashboard 519.",
            "fields": [
                {"name": "program_id", "description": "Primary key federal program identifier."},
                {"name": "program_name", "description": "Official federal program name."},
                {"name": "policy_pillar", "description": "Strategic federal policy pillar."},
                {"name": "total_annual_budget_m", "description": "Governed LookML measure summing annual enacted budget ($M USD)."},
            ],
            "column_aspects": {},
        },
        {
            "entry_name": f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness",
            "label": "explores/beacon_county_readiness",
            "description": (
                "Blue-Chip Certified Unified LookML Explore (`beacon_county_readiness` — \"U.S. Public Sector · Beacon County Disaster Readiness\") "
                "joining `beacon_county_readiness`, `beacon_deployment_plan`, `beacon_national_macro_timeline`, and `beacon_federal_program_summary` "
                "into a single governed semantic graph with 60 fields."
            ),
            "overview": (
                "<h3>Unified LookML Semantic Explore — Beacon U.S. County Disaster Readiness (<code>explores/beacon_county_readiness</code>)</h3>"
                "<p><b>Blue-Chip Certified</b> primary Looker Explore in <code>cloud-bi-opm</code> governed by Principal Steward "
                "<b>Sean Zinsmeister</b> (<code>demo-operator@example.com</code>) and the <b>Beacon Federal Readiness Office</b>.</p>"
                "<ul>"
                "<li><b>Unified Semantic Graph (60 Governed Fields):</b> Joins <code>beacon_county_readiness</code> (3,144 U.S. counties from "
                "Cloud Spanner <code>CountyReadiness</code> &amp; Data Commons <code>country/USA</code>) with <code>beacon_deployment_plan</code> "
                "(Cloud Spanner System of Action), <code>beacon_national_macro_timeline</code> (1970–2025 U.S. Census/NOAA series), and "
                "<code>beacon_federal_program_summary</code> (10 Federal Programs).</li>"
                "<li><b>Zero-Drift Cross-Filtering:</b> Powers all 13 tiles and 3 interactive filters on Looker Executive Dashboard <code>519</code> "
                "and the Governed Looker Data App (<code>274</code>) from a single governed Explore.</li>"
                "</ul>"
            ),
            "steward": "Sean Zinsmeister (demo-operator@example.com) & FEMA / U.S. Census Bureau / CDC",
            "steward_email": "demo-operator@example.com",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "LookML Unified Semantic Explore (60 Governed Dimensions & Measures)",
            "dcids": "country/USA | Spanner: CountyReadiness, DeploymentPlan, NationalMacroTimeline, FederalProgramSummary",
            "rule": "All 13 tiles on Looker Dashboard 519 query `explore: beacon_county_readiness` for 100% consistent governed metrics and cross-filtering.",
            "fields": [
                {"name": "beacon_county_readiness.county_id", "description": "Primary key U.S. County DCID (`geoId/*`, 3,144 counties)."},
                {"name": "beacon_county_readiness.county_name", "description": "Disambiguated U.S. County & State name."},
                {"name": "beacon_county_readiness.social_vulnerability_score", "description": "[Knowledge Catalog Term: Social Vulnerability Score (SVI Tier-1 >= 75.0)] Governed Explore dimension for CDC/FEMA SVI percentile."},
                {"name": "beacon_county_readiness.no_internet_pct", "description": "[Knowledge Catalog Term: Household Digital Divide (No Internet >= 18.0%)] Governed Explore dimension for Census ACS broadband deficit (%)."},
                {"name": "beacon_county_readiness.no_vehicle_pct", "description": "[Knowledge Catalog Term: Transit-Isolated Households (No Vehicle >= 10.0%)] Governed Explore dimension for Census ACS zero-vehicle household share (%)."},
                {"name": "beacon_county_readiness.nri_risk_score", "description": "[Knowledge Catalog Term: Composite Hazard Risk Score (FEMA NRI >= 65.0)] Governed Explore dimension for FEMA NRI composite hazard risk."},
                {"name": "beacon_county_readiness.community_resilience_score", "description": "[Knowledge Catalog Term: Community Resilience Index (FEMA NRI < 40.0 Alert)] Governed Explore dimension for FEMA NRI community resilience."},
                {"name": "beacon_county_readiness.web_registration_pct", "description": "[Knowledge Catalog Term: Web Intake Channel Share (< 60.0% Drop-Off)] Governed Explore dimension for OpenFEMA online web intake share (%)."},
                {"name": "beacon_county_readiness.has_team_coverage", "description": "[Knowledge Catalog Term: Mobile Response Team Coverage Status (Beacon DRC)] Governed Explore dimension for `DCGraph` `:covers` team status."},
                {"name": "beacon_deployment_plan.priority_tier", "description": "[Knowledge Catalog Term: Federal Deployment Plan] Joined Cloud Spanner `DeploymentPlan` dispatch tier."},
                {"name": "beacon_deployment_plan.action", "description": "[Knowledge Catalog Term: Federal Deployment Plan] Joined Cloud Spanner `DeploymentPlan` field action."},
            ],
            "column_aspects": {
                "beacon_county_readiness.social_vulnerability_score": (
                    "FEMA Office of Response & Recovery & CDC/ATSDR",
                    "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
                    "Social Vulnerability & Equity (Justice40)",
                    "FemaSocialVulnerability_NaturalHazardImpact",
                    "social_vulnerability_score >= 75.0 designates Tier-1 Priority Dispatch County.",
                ),
                "beacon_county_readiness.no_internet_pct": (
                    "U.S. Census Bureau (ACS) & FCC/NTIA",
                    "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
                    "Digital & Transit Access (BEAD)",
                    "Count_Household_NoInternetAccess",
                    "no_internet_pct >= 18.0% triggers Mobile DRC & Call Center surge.",
                ),
                "beacon_county_readiness.no_vehicle_pct": (
                    "U.S. Census Bureau (ACS) & U.S. DOT / FEMA",
                    "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
                    "Digital & Transit Access",
                    "Count_Household_NoVehicleAvailable",
                    "no_vehicle_pct >= 10.0% mandates roving Mobile DRC deployment.",
                ),
                "beacon_county_readiness.nri_risk_score": (
                    "FEMA National Risk Index (NRI) & NOAA",
                    "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
                    "Hazard Risk & Resilience",
                    "FemaNationalRisk_NaturalHazardImpact",
                    "nri_risk_score >= 65.0 classifies county as High Multi-Hazard Exposure.",
                ),
                "beacon_county_readiness.web_registration_pct": (
                    "FEMA Individual Assistance (IA) & USDS",
                    "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
                    "Federal Response Operations",
                    "OpenFEMA_WebRegistrationShare",
                    "web_registration_pct < 60.0% flags severe web intake drop-off.",
                ),
                "beacon_county_readiness.has_team_coverage": (
                    "Beacon Federal Readiness Office (FEMA)",
                    "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
                    "Federal Response Operations",
                    "SpannerGraph: (team)-[:covers]->(county)",
                    "has_team_coverage = FALSE in disaster-hit high-SVI counties triggers Tier-1 DeploymentPlan action.",
                ),
            },
        },
        {
            "entry_name": f"{LOOKER_ENTRY_PREFIX}/dashboards/519",
            "label": "dashboards/519",
            "description": (
                "Blue-Chip Certified Looker Executive Dashboard (`dashboards/519`: \"U.S. Public Sector · Beacon Disaster Readiness & "
                "Policy Intelligence (Data Commons x Cloud Spanner Graph)\") styled in the Old Glory Blue (`#3C3B6E`) gradient palette "
                "with 13 governed tiles and live cross-filtering over `explore: beacon_county_readiness`."
            ),
            "overview": (
                "<h3>Looker Executive Dashboard 519 — U.S. Public Sector · Beacon Disaster Readiness &amp; Policy Intelligence</h3>"
                "<p><b>Blue-Chip Certified</b> 13-tile executive command center hosted on <code>https://your-looker-instance.cloud.looker.com/dashboards/519</code> "
                "and governed by Principal Steward <b>Sean Zinsmeister</b> (<code>demo-operator@example.com</code>) and the "
                "<b>Beacon Federal Readiness Office (FEMA / U.S. Census Bureau / HHS / HUD)</b>.</p>"
                "<ul>"
                "<li><b>Old Glory Blue (<code>#3C3B6E</code>, RGB: 60, 59, 110) Visual Foundation:</b> Uses a 10-stop luminous gradient palette "
                "(<code>#252447 &rarr; #3C3B6E &rarr; #4F4E8C &rarr; #6362AB &rarr; #7B7AC4 &rarr; #9594DA &rarr; #B0AFEC &rarr; #CAC9F5 &rarr; #E2E1FA &rarr; #F4F4FC</code>) "
                "with high-contrast <code>#202124</code> typography.</li>"
                "<li><b>Single-Explore LookML Semantic Layer:</b> All 13 tiles (4 KPI Sparklines, Digital Divide vs. Web Intake Scatter Plot, "
                "Top 10 Unserved Disaster Counties, 1970–2025 Census Trajectory, State Channel Mix, Federal Budget Donut, Compounding Disasters, "
                "Billion-Dollar Losses, Expected Annual Loss, and Cloud Spanner <code>DeploymentPlan</code> Action Grid) query "
                "<code>explore: beacon_county_readiness</code> for seamless cross-filtering.</li>"
                "</ul>"
            ),
            "steward": "Sean Zinsmeister (demo-operator@example.com) & Beacon Federal Readiness Office",
            "steward_email": "demo-operator@example.com",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Executive BI Command Center — Old Glory Blue (#3C3B6E) 13-Tile Dashboard",
            "dcids": "country/USA | Looker Dashboard 519 -> Explore: beacon_county_readiness -> Spanner: CountyReadiness & DeploymentPlan",
            "rule": "100% of dashboard tiles are bound to `explore: beacon_county_readiness` with `crossfilter_enabled: true`.",
            "fields": [],
            "column_aspects": {},
        },
    ]

    # Also enrich the 13 Dashboard Elements of Dashboard 519
    for el_id, el_title in LOOKER_DASHBOARD_519_ELEMENTS:
        looker_specs.append({
            "entry_name": f"{LOOKER_ENTRY_PREFIX}/dashboards/519/dashboard_elements/{el_id}",
            "label": f"dashboards/519/dashboard_elements/{el_id}",
            "description": f"Governed Looker Dashboard 519 Tile ({el_id}): {el_title} — powered by LookML Explore `beacon_county_readiness` and Cloud Spanner `readiness_dcgraph`.",
            "overview": (
                f"<h3>Looker Dashboard 519 Element <code>{el_id}</code> — {el_title}</h3>"
                "<p>Governed visualization tile on Looker Executive Dashboard <code>519</code> styled in the Old Glory Blue "
                "(<code>#3C3B6E</code>) gradient ramp and backed by LookML Explore <code>beacon_county_readiness</code>.</p>"
            ),
            "steward": "Sean Zinsmeister (demo-operator@example.com) & Beacon Federal Readiness Office",
            "steward_email": "demo-operator@example.com",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Looker Dashboard 519 Governed Tile",
            "dcids": "country/USA | Explore: beacon_county_readiness",
            "rule": "Inherits LookML metric definitions and Knowledge Catalog business glossary thresholds from `CountyReadiness`.",
            "fields": [],
            "column_aspects": {},
        })

    looker_patched = 0
    for spec in looker_specs:
        entry_name = spec["entry_name"]
        st_check, _ = api_call("GET", f"https://dataplex.googleapis.com/v1/{entry_name}", headers)
        if st_check != 200:
            print(f"   [Note] `@looker` entry `{spec['label']}` not found ({st_check}); skipping.")
            continue

        aspects_payload: dict[str, Any] = {
            "655216118709.global.overview": {
                "aspectType": "projects/655216118709/locations/global/aspectTypes/overview",
                "data": {"content": spec["overview"], "contentType": "HTML"},
            },
            "655216118709.global.contacts": {
                "aspectType": "projects/655216118709/locations/global/aspectTypes/contacts",
                "data": {
                    "identities": [
                        {"role": "steward", "name": "Sean Zinsmeister (Principal Steward · Google Data Cloud)", "id": "demo-operator@example.com"},
                        {"role": "steward", "name": spec["steward"], "id": spec["steward_email"]},
                        {"role": "owner", "name": "Beacon Federal Readiness Office (FEMA / Census / HHS / HUD)", "id": "demo-operator@example.com"},
                    ]
                },
            },
            f"{PROJECT_NUM}.global.{ASPECT_TYPE_ID}": {
                "aspectType": f"projects/{PROJECT_NUM}/locations/global/aspectTypes/{ASPECT_TYPE_ID}",
                "data": {
                    "federal_agency_steward": spec["steward"],
                    "fedramp_security_classification": spec["fedramp"],
                    "certification_status": "BLUE_CHIP_CERTIFIED",
                    "federal_policy_pillar": spec["pillar"],
                    "data_commons_dcids": spec["dcids"],
                    "policy_threshold_rule": spec["rule"],
                },
            },
            f"{PROJECT_NUM}.us-east1.{ASPECT_TYPE_ID}": {
                "aspectType": f"projects/{PROJECT_NUM}/locations/us-east1/aspectTypes/{ASPECT_TYPE_ID}",
                "data": {
                    "federal_agency_steward": spec["steward"],
                    "fedramp_security_classification": spec["fedramp"],
                    "certification_status": "BLUE_CHIP_CERTIFIED",
                    "federal_policy_pillar": spec["pillar"],
                    "data_commons_dcids": spec["dcids"],
                    "policy_threshold_rule": spec["rule"],
                },
            },
            "655216118709.global.descriptions": {
                "aspectType": "projects/655216118709/locations/global/aspectTypes/descriptions",
                "data": {
                    "description": spec["description"],
                    "userManaged": True,
                    **({"fields": spec["fields"]} if spec["fields"] else {}),
                },
            },
        }

        for col_name, (c_steward, c_fedramp, c_pillar, c_dcid, c_rule) in spec.get("column_aspects", {}).items():
            aspects_payload[f"{PROJECT_NUM}.global.{ASPECT_TYPE_ID}@Schema.{col_name}"] = {
                "aspectType": f"projects/{PROJECT_NUM}/locations/global/aspectTypes/{ASPECT_TYPE_ID}",
                "data": {
                    "federal_agency_steward": c_steward,
                    "fedramp_security_classification": c_fedramp,
                    "certification_status": "BLUE_CHIP_CERTIFIED",
                    "federal_policy_pillar": c_pillar,
                    "data_commons_dcids": c_dcid,
                    "policy_threshold_rule": c_rule,
                },
            }

        st_p, res_p = api_call(
            "PATCH",
            f"https://dataplex.googleapis.com/v1/{entry_name}?updateMask=aspects",
            headers,
            {"name": entry_name, "aspects": aspects_payload},
        )
        if st_p == 200:
            looker_patched += 1
        print(f"   Patched `@looker` entry `{spec['label']}` -> {st_p}")
        if st_p != 200:
            print(f"     [Warn] Error patching `{spec['label']}`: {str(res_p)[:300]}")

    # Also enrich the `@bigquery` Borderless Lakehouse (BigLake Apache Iceberg, Object Table & Analytical Serving Tables) in `beacon_disaster_readiness`
    bq_tables = [
        ("tables/county_readiness", "Borderless Lakehouse Analytical Serving Table in BigQuery (`beacon_disaster_readiness.county_readiness`, 3,144 U.S. counties) synchronized with Cloud Spanner `CountyReadiness` and joined with BigLake Apache Iceberg tables (`noaa_hazard_iceberg`, `fema_field_assessments_iceberg`) and BigLake Object Tables (`fema_field_sitrep_objects`) for the Gemini Conversational Analytics Beacon Agent and Looker Semantic Layer (`beacon_county_readiness`)."),
        ("tables/noaa_hazard_iceberg", "BigLake Managed Apache Iceberg Table (`beacon_disaster_readiness.noaa_hazard_iceberg`, 3,144 U.S. counties) storing multi-cloud NOAA storm surge, wind speed, power grid outage, and cell tower outage telemetry in open Apache Iceberg / Parquet format (`gs://beacon-borderless-lakehouse-123456789012/iceberg/noaa_hazard_iceberg`) with zero ETL duplication."),
        ("tables/fema_field_assessments_iceberg", "BigLake Managed Apache Iceberg Table (`beacon_disaster_readiness.fema_field_assessments_iceberg`) storing FEMA & State EOC Preliminary Damage Assessments (`road_washout_status`, `bridge_closures_count`, `shelter_capacity_utilization_pct`, `field_sitrep_summary`, `sitrep_pdf_uri`) in open Apache Iceberg format."),
        ("tables/fema_field_sitrep_objects", "BigLake Object Table (`beacon_disaster_readiness.fema_field_sitrep_objects`) over unstructured FEMA Field SitRep PDF files in Cloud Storage (`gs://beacon-borderless-lakehouse-123456789012/field_sitreps/*.pdf`), governed under one unified security and lineage model."),
        ("tables/v_borderless_lakehouse_dispatch", "Unified Borderless Lakehouse Dispatch View (`beacon_disaster_readiness.v_borderless_lakehouse_dispatch`) federating Data Commons & Spanner readiness with BigLake Apache Iceberg hazard/damage tables and unstructured FEMA Field SitRep PDFs."),
        ("tables/node", "Graph Vertex Table in BigQuery (`beacon_disaster_readiness.node`, 3,546 nodes: U.S. Counties, States, OpenFEMA Disasters, Regional Hubs, Mobile DRC Teams) synchronized with Cloud Spanner Graph `readiness_dcgraph`."),
        ("tables/edge", "Graph Directed Edge Table in BigQuery (`beacon_disaster_readiness.edge`, 7,822 edges: `containedinplace`, `affectedplace`, `locatedin`, `covers`, `serves`) synchronized with Cloud Spanner Graph `readiness_dcgraph`."),
        ("tables/deployment_plan", "Federated BigQuery mirror of Cloud Spanner `DeploymentPlan` serving the Looker Core `beacon_deployment_plan` LookML View."),
        ("tables/national_macro_timeline", "Federated BigQuery mirror of Cloud Spanner `NationalMacroTimeline` (1970–2025 U.S. Census/NOAA series) serving LookML View `beacon_national_macro_timeline`."),
        ("tables/federal_program_summary", "Federated BigQuery mirror of Cloud Spanner `FederalProgramSummary` (10 Federal Programs) serving LookML View `beacon_federal_program_summary`."),
        ("tables/disaster_summary", "Federated BigQuery mirror of Cloud Spanner `DisasterSummary` (263 OpenFEMA Major Disaster Declarations since FY2023)."),
        ("tables/county_profile", "Federated BigQuery mirror of Cloud Spanner `CountyProfile` (3,144 U.S. counties Census ACS & FEMA NRI baseline)."),
        ("tables/state_profile", "Federated BigQuery mirror of Cloud Spanner `StateProfile` (51 U.S. States & Territories Census ACS baseline)."),
        ("tables/knowledge_catalog_governance", "Federated BigQuery mirror of Cloud Spanner `KnowledgeCatalogGovernance` (16 Federal Policy Contracts KC-US-001 to KC-US-016)."),
    ]
    bq_lakehouse_query = (
        "SELECT\n"
        "  c.county_id, c.county_name, c.state_code,\n"
        "  ROUND(c.social_vulnerability_score, 2) AS svi_score,\n"
        "  ROUND(c.no_internet_pct, 1) AS no_internet_pct,\n"
        "  ice.active_hazard_alert,\n"
        "  ice.cell_tower_outage_pct,\n"
        "  pda.road_washout_status,\n"
        "  pda.recommended_mobile_unit,\n"
        "  obj.uri AS unstructured_sitrep_pdf_uri\n"
        "FROM `your-gcp-project-id.beacon_disaster_readiness.county_readiness` c\n"
        "JOIN `your-gcp-project-id.beacon_disaster_readiness.noaa_hazard_iceberg` ice\n"
        "  ON c.county_id = ice.county_id\n"
        "JOIN `your-gcp-project-id.beacon_disaster_readiness.fema_field_assessments_iceberg` pda\n"
        "  ON c.county_id = pda.county_id\n"
        "LEFT JOIN `your-gcp-project-id.beacon_disaster_readiness.fema_field_sitrep_objects` obj\n"
        "  ON obj.uri = pda.sitrep_pdf_uri\n"
        "WHERE c.has_team_coverage = FALSE\n"
        "  AND c.social_vulnerability_score >= 75.0\n"
        "  AND c.disasters_since_2023 >= 1\n"
        "  AND c.total_registrations > 0\n"
        "  AND c.state_code NOT IN ('AK', 'HI', 'PR')\n"
        "ORDER BY svi_score DESC\n"
        "LIMIT 10;"
    )
    bq_patched = 0
    for bq_suf, bq_desc in bq_tables:
        bq_entry = f"{BQ_ENTRY_PREFIX}/{bq_suf}"
        st_b, _ = api_call("GET", f"https://dataplex.googleapis.com/v1/{bq_entry}", headers)
        if st_b != 200:
            continue
        bq_aspects = {
            "655216118709.global.overview": {
                "aspectType": "projects/655216118709/locations/global/aspectTypes/overview",
                "data": {
                    "content": (
                        f"<h3>Google Cloud Borderless Lakehouse Table in BigQuery (<code>beacon_disaster_readiness.{bq_suf.split('/')[-1]}</code>)</h3>"
                        f"<p>{bq_desc}</p>"
                        "<p><b>Google Cloud Borderless Lakehouse Architecture</b>: Unifies <b>Cloud Spanner Graph</b> (<code>readiness_dcgraph</code> operational knowledge graph &amp; System of Action), "
                        "<b>BigLake Managed Apache Iceberg Tables</b> (<code>noaa_hazard_iceberg</code> &amp; <code>fema_field_assessments_iceberg</code> open multi-cloud lakehouse formats), and "
                        "<b>BigLake Object Tables</b> (<code>fema_field_sitrep_objects</code> unstructured FEMA Field SitRep PDFs in Cloud Storage) with zero ETL duplication—powering "
                        "sub-second analytics for the <b>Gemini Conversational Analytics Beacon Agent</b> and <b>Looker Universal Semantic Layer (LookML)</b>.</p>"
                        "<p>Governed by Principal Steward <b>Sean Zinsmeister</b> (<code>demo-operator@example.com</code>) under the Beacon Federal Disaster Readiness Glossary.</p>"
                        + (
                            f"<h4>Ready-to-Run BigQuery Studio Borderless Lakehouse Query</h4>"
                            f"<pre><code>{bq_lakehouse_query}</code></pre>"
                            if bq_suf in ("tables/county_readiness", "tables/noaa_hazard_iceberg", "tables/fema_field_assessments_iceberg", "tables/fema_field_sitrep_objects", "tables/v_borderless_lakehouse_dispatch")
                            else ""
                        )
                    ),
                    "contentType": "HTML",
                },
            },
            "655216118709.global.contacts": {
                "aspectType": "projects/655216118709/locations/global/aspectTypes/contacts",
                "data": {
                    "identities": [
                        {"role": "steward", "name": "Sean Zinsmeister (Principal Steward · Google Data Cloud)", "id": "demo-operator@example.com"},
                        {"role": "owner", "name": "Beacon Federal Readiness Office", "id": "demo-operator@example.com"},
                    ]
                },
            },
            f"{PROJECT_NUM}.global.{ASPECT_TYPE_ID}": {
                "aspectType": f"projects/{PROJECT_NUM}/locations/global/aspectTypes/{ASPECT_TYPE_ID}",
                "data": {
                    "federal_agency_steward": "Beacon Federal Readiness Office (FEMA / NOAA / U.S. Census Bureau) & Sean Zinsmeister",
                    "fedramp_security_classification": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
                    "certification_status": "BLUE_CHIP_CERTIFIED",
                    "federal_policy_pillar": "Google Cloud Borderless Lakehouse (BigLake Apache Iceberg + Unstructured Object Tables + Spanner Graph)",
                    "data_commons_dcids": "country/USA | Borderless Lakehouse: readiness_dcgraph <-> BigLake Apache Iceberg & Object Tables",
                    "policy_threshold_rule": bq_desc,
                },
            },
        }
        st_bp, _ = api_call(
            "PATCH",
            f"https://dataplex.googleapis.com/v1/{bq_entry}?updateMask=aspects",
            headers,
            {"name": bq_entry, "aspects": bq_aspects},
        )
        if st_bp == 200:
            bq_patched += 1
        print(f"   Patched `@bigquery` entry `{bq_suf}` -> {st_bp}")

    return looker_patched, bq_patched


# =============================================================================
# 5. EntryLinks: Glossary Definition Links & Schema-Join Links
#    (Across `@spanner`, `@looker`, and `@bigquery`)
# =============================================================================

TBL_SHORT = {
    "CountyReadiness": "cread",
    "CountyProfile": "cprof",
    "StateProfile": "sprof",
    "DisasterSummary": "dsum",
    "DisasterDesignation": "ddes",
    "Registration": "reg",
    "DeploymentPlan": "dplan",
    "NationalMacroTimeline": "macro",
    "FederalProgramSummary": "fprog",
    "KnowledgeCatalogGovernance": "kcgov",
    "Observation": "obs",
    "Node": "node",
    "Edge": "edge",
}


def setup_entry_links(headers: dict[str, str]) -> tuple[int, int]:
    print("5. Creating Knowledge Catalog EntryLinks (`definition` & `schema-join`) across `@spanner`, `@looker`, and `@bigquery` ...")
    parent_group = f"projects/{PROJECT_NUM}/locations/{LOCATION}/entryGroups/@spanner"

    def_count = 0
    # A1. Glossary Term -> Spanner Column `definition` EntryLinks (in us-central1/@spanner)
    for term in GLOSSARY_TERMS:
        term_entry = (
            f"projects/{PROJECT_NUM}/locations/{LOCATION}/entryGroups/@dataplex/entries/"
            f"projects/{PROJECT_NUM}/locations/{LOCATION}/glossaries/{GLOSSARY_ID}/terms/{term['id']}"
        )
        for tbl_suffix, col_path in term["links"]:
            target_spanner_entry = f"{SPANNER_ENTRY_PREFIX}/{tbl_suffix}"
            st_e, _ = api_call("GET", f"https://dataplex.googleapis.com/v1/{target_spanner_entry}", headers)
            if st_e != 200:
                continue
            raw_tbl = tbl_suffix.split("/")[-1]
            clean_tbl = TBL_SHORT.get(raw_tbl, raw_tbl[:8].lower())
            clean_col = col_path.replace("Schema.", "").replace("_", "-")
            link_id = f"bdef-{term['id'][:16]}-{clean_tbl}-{clean_col[:16]}".lower().strip("-")
            link_body = {
                "entryLinkType": "projects/655216118709/locations/global/entryLinkTypes/definition",
                "entryReferences": [
                    {"name": target_spanner_entry, "path": col_path, "type": "SOURCE"},
                    {"name": term_entry, "type": "TARGET"},
                ],
            }
            st_l, _ = api_call(
                "POST",
                f"https://dataplex.googleapis.com/v1/{parent_group}/entryLinks?entryLinkId={link_id}",
                headers,
                link_body,
            )
            if st_l in (200, 409):
                def_count += 1
            print(f"   [@spanner] Linked term `{term['id']}` -> `{tbl_suffix}:{col_path}` ({st_l})")

    # A2. Glossary Term -> Native `@looker` LookML View & Explore Fields `definition` EntryLinks (in us-east1/@looker)
    looker_group = f"projects/{PROJECT_NUM}/locations/us-east1/entryGroups/@looker"
    global_term_prefix = (
        f"projects/{PROJECT_NUM}/locations/global/entryGroups/@dataplex/entries/"
        f"projects/{PROJECT_NUM}/locations/global/glossaries/{GLOSSARY_ID}/terms"
    )
    looker_term_bindings = [
        ("social-vulnerability-score", f"{LOOKML_MODEL_PREFIX}/views/beacon_county_readiness", "Schema.social_vulnerability_score", "vw-svi"),
        ("social-vulnerability-score", f"{LOOKML_MODEL_PREFIX}/views/beacon_county_readiness", "Schema.avg_social_vulnerability_score", "vw-avg-svi"),
        ("social-vulnerability-score", f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness", "Schema.beacon_county_readiness.social_vulnerability_score", "ex-svi"),
        ("social-vulnerability-score", f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness", "Schema.beacon_county_readiness.avg_social_vulnerability_score", "ex-avg-svi"),
        ("household-digital-divide", f"{LOOKML_MODEL_PREFIX}/views/beacon_county_readiness", "Schema.no_internet_pct", "vw-no-inet"),
        ("household-digital-divide", f"{LOOKML_MODEL_PREFIX}/views/beacon_county_readiness", "Schema.avg_no_internet_pct", "vw-avg-inet"),
        ("household-digital-divide", f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness", "Schema.beacon_county_readiness.no_internet_pct", "ex-no-inet"),
        ("household-digital-divide", f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness", "Schema.beacon_county_readiness.avg_no_internet_pct", "ex-avg-inet"),
        ("transit-isolated-households", f"{LOOKML_MODEL_PREFIX}/views/beacon_county_readiness", "Schema.no_vehicle_pct", "vw-no-veh"),
        ("transit-isolated-households", f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness", "Schema.beacon_county_readiness.no_vehicle_pct", "ex-no-veh"),
        ("composite-hazard-risk-score", f"{LOOKML_MODEL_PREFIX}/views/beacon_county_readiness", "Schema.nri_risk_score", "vw-nri"),
        ("composite-hazard-risk-score", f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness", "Schema.beacon_county_readiness.nri_risk_score", "ex-nri"),
        ("community-resilience-index", f"{LOOKML_MODEL_PREFIX}/views/beacon_county_readiness", "Schema.community_resilience_score", "vw-resil"),
        ("community-resilience-index", f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness", "Schema.beacon_county_readiness.community_resilience_score", "ex-resil"),
        ("expected-annual-disaster-loss", f"{LOOKML_MODEL_PREFIX}/views/beacon_national_macro_timeline", "Schema.billion_dollar_disasters_loss_usd_b", "vw-eal"),
        ("expected-annual-disaster-loss", f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness", "Schema.beacon_national_macro_timeline.billion_dollar_disasters_loss_usd_b", "ex-eal"),
        ("poverty-rate-federal-line", f"{LOOKML_MODEL_PREFIX}/views/beacon_county_readiness", "Schema.poverty_pct", "vw-pov"),
        ("poverty-rate-federal-line", f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness", "Schema.beacon_county_readiness.poverty_pct", "ex-pov"),
        ("senior-population-share", f"{LOOKML_MODEL_PREFIX}/views/beacon_county_readiness", "Schema.age_65_plus_pct", "vw-sen65"),
        ("senior-population-share", f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness", "Schema.beacon_county_readiness.age_65_plus_pct", "ex-sen65"),
        ("disability-access-functional-needs", f"{LOOKML_MODEL_PREFIX}/views/beacon_county_readiness", "Schema.disability_pct", "vw-disab"),
        ("disability-access-functional-needs", f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness", "Schema.beacon_county_readiness.disability_pct", "ex-disab"),
        ("web-intake-channel-share", f"{LOOKML_MODEL_PREFIX}/views/beacon_county_readiness", "Schema.web_registration_pct", "vw-web"),
        ("web-intake-channel-share", f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness", "Schema.beacon_county_readiness.web_registration_pct", "ex-web"),
        ("mobile-response-team-coverage", f"{LOOKML_MODEL_PREFIX}/views/beacon_county_readiness", "Schema.has_team_coverage", "vw-team"),
        ("mobile-response-team-coverage", f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness", "Schema.beacon_county_readiness.has_team_coverage", "ex-team"),
        ("federal-deployment-plan", f"{LOOKML_MODEL_PREFIX}/views/beacon_deployment_plan", "Schema.priority_tier", "vw-plan-tier"),
        ("federal-deployment-plan", f"{LOOKML_MODEL_PREFIX}/views/beacon_deployment_plan", "Schema.action", "vw-plan-act"),
        ("federal-deployment-plan", f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness", "Schema.beacon_deployment_plan.priority_tier", "ex-plan-tier"),
        ("federal-deployment-plan", f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness", "Schema.beacon_deployment_plan.action", "ex-plan-act"),
    ]
    for term_id, lkr_entry, col_path, short_suffix in looker_term_bindings:
        link_id = f"blkr-{term_id[:16]}-{short_suffix}".lower().strip("-")
        link_body = {
            "entryLinkType": "projects/655216118709/locations/global/entryLinkTypes/definition",
            "entryReferences": [
                {"name": lkr_entry, "path": col_path, "type": "SOURCE"},
                {"name": f"{global_term_prefix}/{term_id}", "type": "TARGET"},
            ],
        }
        st_lk, _ = api_call(
            "POST",
            f"https://dataplex.googleapis.com/v1/{looker_group}/entryLinks?entryLinkId={link_id}",
            headers,
            link_body,
        )
        if st_lk in (200, 409):
            def_count += 1
        print(f"   [@looker] Linked term `{term_id}` -> `{short_suffix}:{col_path}` ({st_lk})")

    # B1. Table-to-Table `schema-join` EntryLinks across Spanner Graph & Tables
    joins = [
        (
            "bjoin-readiness-to-deployment-plan",
            "tables/CountyReadiness",
            "CountyReadiness",
            "tables/DeploymentPlan",
            "DeploymentPlan",
            ["county_id"],
            ["county_id"],
            "Joins each U.S. county's disaster readiness & vulnerability profile (`CountyReadiness`) to its active `DeploymentPlan` mobile unit dispatch.",
        ),
        (
            "bjoin-profile-to-readiness",
            "tables/CountyProfile",
            "CountyProfile",
            "tables/CountyReadiness",
            "CountyReadiness",
            ["county_id"],
            ["county_id"],
            "Materializes `CountyReadiness` analytical view from `CountyProfile` Census ACS / FEMA NRI indicators, OpenFEMA registrations, and `DCGraph` team coverage.",
        ),
        (
            "bjoin-profile-to-graph-node",
            "tables/CountyProfile",
            "CountyProfile",
            "tables/Node",
            "Node",
            ["county_id"],
            ["subject_id"],
            "Joins `CountyProfile` (`county_id`) to its corresponding Place vertex (`subject_id`) in `DCGraph` (`Node`) for multi-hop ISO GQL traversal.",
        ),
        (
            "bjoin-node-to-edge",
            "tables/Node",
            "Node",
            "tables/Edge",
            "Edge",
            ["subject_id"],
            ["subject_id"],
            "Interleaved parent-child join between `DCGraph` vertex table (`Node`) and directed edge table (`Edge`).",
        ),
        (
            "bjoin-observation-to-node",
            "tables/Observation",
            "Observation",
            "tables/Node",
            "Node",
            ["observation_about"],
            ["subject_id"],
            "Joins North America Google Data Commons statistical observations (`observation_about`) to `DCGraph` Place nodes (`subject_id`).",
        ),
        (
            "bjoin-designation-to-profile",
            "tables/DisasterDesignation",
            "DisasterDesignation",
            "tables/CountyProfile",
            "CountyProfile",
            ["county_id"],
            ["county_id"],
            "Joins OpenFEMA Presidential Major Disaster Declarations (`DisasterDesignation.county_id`) to U.S. Census / FEMA NRI `CountyProfile`.",
        ),
        (
            "bjoin-registration-to-profile",
            "tables/Registration",
            "Registration",
            "tables/CountyProfile",
            "CountyProfile",
            ["county_id"],
            ["county_id"],
            "Joins OpenFEMA Individual Assistance registration channel metrics (`Registration.county_id`) to `CountyProfile` and `CountyReadiness`.",
        ),
        (
            "bjoin-readiness-to-kc-governance",
            "tables/CountyReadiness",
            "CountyReadiness",
            "tables/KnowledgeCatalogGovernance",
            "KnowledgeCatalogGovernance",
            ["social_vulnerability_score"],
            ["governed_column"],
            "Binds `CountyReadiness` metrics to their authoritative `KnowledgeCatalogGovernance` federal policy contracts and thresholds.",
        ),
    ]
    join_count = 0
    for j_id, src_suf, src_sql, tgt_suf, tgt_sql, src_fields, tgt_fields, desc in joins:
        src_entry = f"{SPANNER_ENTRY_PREFIX}/{src_suf}"
        tgt_entry = f"{SPANNER_ENTRY_PREFIX}/{tgt_suf}"
        payload = {
            "entryLinkType": "projects/655216118709/locations/global/entryLinkTypes/schema-join",
            "entryReferences": [
                {"name": src_entry, "type": "UNSPECIFIED"},
                {"name": tgt_entry, "type": "UNSPECIFIED"},
            ],
            "aspects": {
                "655216118709.global.schema-join": {
                    "aspectType": "projects/655216118709/locations/global/aspectTypes/schema-join",
                    "data": {
                        "userManaged": True,
                        "joins": [
                            {
                                "source": {"name": src_sql, "fields": src_fields},
                                "target": {"name": tgt_sql, "fields": tgt_fields},
                                "description": desc,
                                "type": "FOREIGN_KEY",
                                "inferenceSource": "USER",
                            }
                        ],
                    },
                }
            },
        }
        st_j, _ = api_call(
            "POST",
            f"https://dataplex.googleapis.com/v1/{parent_group}/entryLinks?entryLinkId={j_id}",
            headers,
            payload,
        )
        if st_j in (200, 409):
            join_count += 1
        print(f"   [@spanner] Created schema-join `{j_id}` -> {st_j}")

    # B2. LookML Semantic Layer `schema-join` EntryLinks in `us-east1/@looker`
    looker_joins = [
        (
            "blkr-join-view-readiness-to-plan",
            f"{LOOKML_MODEL_PREFIX}/views/beacon_county_readiness",
            "beacon_county_readiness",
            f"{LOOKML_MODEL_PREFIX}/views/beacon_deployment_plan",
            "beacon_deployment_plan",
            ["county_id"],
            ["county_id"],
            "LookML LEFT OUTER join (`${beacon_county_readiness.county_id} = ${beacon_deployment_plan.county_id}`) in `explore: beacon_county_readiness`.",
        ),
        (
            "blkr-join-view-readiness-to-explore",
            f"{LOOKML_MODEL_PREFIX}/views/beacon_county_readiness",
            "beacon_county_readiness",
            f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness",
            "beacon_county_readiness",
            ["county_id"],
            ["beacon_county_readiness.county_id"],
            "Primary base LookML View (`beacon_county_readiness`) projected into the unified `explore: beacon_county_readiness`.",
        ),
        (
            "blkr-join-view-plan-to-explore",
            f"{LOOKML_MODEL_PREFIX}/views/beacon_deployment_plan",
            "beacon_deployment_plan",
            f"{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness",
            "beacon_county_readiness",
            ["county_id"],
            ["beacon_deployment_plan.county_id"],
            "Joined Cloud Spanner `DeploymentPlan` LookML View (`beacon_deployment_plan`) in `explore: beacon_county_readiness`.",
        ),
    ]
    for j_id, src_entry, src_sql, tgt_entry, tgt_sql, src_fields, tgt_fields, desc in looker_joins:
        payload = {
            "entryLinkType": "projects/655216118709/locations/global/entryLinkTypes/schema-join",
            "entryReferences": [
                {"name": src_entry, "type": "UNSPECIFIED"},
                {"name": tgt_entry, "type": "UNSPECIFIED"},
            ],
            "aspects": {
                "655216118709.global.schema-join": {
                    "aspectType": "projects/655216118709/locations/global/aspectTypes/schema-join",
                    "data": {
                        "userManaged": True,
                        "joins": [
                            {
                                "source": {"name": src_sql, "fields": src_fields},
                                "target": {"name": tgt_sql, "fields": tgt_fields},
                                "description": desc,
                                "type": "FOREIGN_KEY",
                                "inferenceSource": "USER",
                            }
                        ],
                    },
                }
            },
        }
        st_lj, _ = api_call(
            "POST",
            f"https://dataplex.googleapis.com/v1/{looker_group}/entryLinks?entryLinkId={j_id}",
            headers,
            payload,
        )
        if st_lj in (200, 409):
            join_count += 1
        print(f"   [@looker] Created schema-join `{j_id}` -> {st_lj}")

    return def_count, join_count


# =============================================================================
# 6. Ecosystem Entries, Human-Readable LookML & Looker Catalog Entries,
#    and Clean 6-Stage End-to-End Table & Column-Level Data Lineage
# =============================================================================

ECOSYSTEM_ENTRY_GROUP_ID = "beacon-disaster-readiness-lineage"

# Clean, human-readable FQNs (zero truncated domain prefixes and zero raw numeric IDs!)
FQN_DC_USA = "custom:Google_Data_Commons_USA"
FQN_FEDERAL_OPS = "custom:US_Federal_Disaster_Operations"
FQN_GE_AGENT = "custom:Gemini_Enterprise_Beacon_Agent"

FQN_SPANNER_PREFIX = f"spanner:{PROJECT_ID}.regional-{LOCATION}.{INSTANCE_ID}.{DATABASE_ID}"
FQN_SPANNER_GRAPH = f"spanner:graph:{PROJECT_ID}.regional-{LOCATION}.{INSTANCE_ID}.{DATABASE_ID}.DCGraph"
FQN_OBS = f"{FQN_SPANNER_PREFIX}.Observation"
FQN_NODE = f"{FQN_SPANNER_PREFIX}.Node"
FQN_EDGE = f"{FQN_SPANNER_PREFIX}.Edge"
FQN_STATE = f"{FQN_SPANNER_PREFIX}.StateProfile"
FQN_MACRO = f"{FQN_SPANNER_PREFIX}.NationalMacroTimeline"
FQN_FPROG = f"{FQN_SPANNER_PREFIX}.FederalProgramSummary"
FQN_DDES = f"{FQN_SPANNER_PREFIX}.DisasterDesignation"
FQN_REG = f"{FQN_SPANNER_PREFIX}.Registration"
FQN_DSUM = f"{FQN_SPANNER_PREFIX}.DisasterSummary"
FQN_PROFILE = f"{FQN_SPANNER_PREFIX}.CountyProfile"
FQN_READINESS = f"{FQN_SPANNER_PREFIX}.CountyReadiness"
FQN_KC_GOV = f"{FQN_SPANNER_PREFIX}.KnowledgeCatalogGovernance"
FQN_PLAN = f"{FQN_SPANNER_PREFIX}.DeploymentPlan"

# Native `@bigquery` Borderless Lakehouse (BigLake Apache Iceberg, Unstructured Object Tables & Federated Serving Tables)
FQN_BQ_PREFIX = f"bigquery:{PROJECT_ID}.beacon_disaster_readiness"
FQN_BQ_GRAPH = f"{FQN_BQ_PREFIX}.Borderless_Lakehouse_Beacon_Readiness"
FQN_BQ_ICEBERG_NOAA = f"{FQN_BQ_PREFIX}.noaa_hazard_iceberg"
FQN_BQ_ICEBERG_FEMA = f"{FQN_BQ_PREFIX}.fema_field_assessments_iceberg"
FQN_BQ_OBJ_SITREP = f"{FQN_BQ_PREFIX}.fema_field_sitrep_objects"
FQN_BQ_VIEW_DISPATCH = f"{FQN_BQ_PREFIX}.v_borderless_lakehouse_dispatch"
FQN_BQ_NODE = f"{FQN_BQ_PREFIX}.node"
FQN_BQ_EDGE = f"{FQN_BQ_PREFIX}.edge"
FQN_BQ_READINESS = f"{FQN_BQ_PREFIX}.county_readiness"
FQN_BQ_PLAN = f"{FQN_BQ_PREFIX}.deployment_plan"
FQN_BQ_MACRO = f"{FQN_BQ_PREFIX}.national_macro_timeline"
FQN_BQ_FPROG = f"{FQN_BQ_PREFIX}.federal_program_summary"
FQN_BQ_DSUM = f"{FQN_BQ_PREFIX}.disaster_summary"
FQN_BQ_PROFILE = f"{FQN_BQ_PREFIX}.county_profile"
FQN_BQ_STATE = f"{FQN_BQ_PREFIX}.state_profile"
FQN_BQ_KC_GOV = f"{FQN_BQ_PREFIX}.knowledge_catalog_governance"

# Human-Readable LookML Semantic Layer & Looker Dashboard FQNs (renders Looker icon + readable label!)
FQN_LOOKER_INSTANCE = f"{PROJECT_ID}.us-east1.cloud-bi-opm"
FQN_LOOKML_MODEL = f"looker_core:model:{FQN_LOOKER_INSTANCE}.beacon_disaster_readiness.LookML_Model_Beacon_Readiness"
FQN_LOOKML_VIEW_READINESS = f"looker_core:view:{FQN_LOOKER_INSTANCE}.beacon_disaster_readiness.beacon_disaster_readiness.LookML_View_County_Readiness"
FQN_LOOKML_VIEW_PLAN = f"looker_core:view:{FQN_LOOKER_INSTANCE}.beacon_disaster_readiness.beacon_disaster_readiness.LookML_View_Deployment_Plan"
FQN_LOOKML_VIEW_MACRO = f"looker_core:view:{FQN_LOOKER_INSTANCE}.beacon_disaster_readiness.beacon_disaster_readiness.LookML_View_Macro_Timeline"
FQN_LOOKML_VIEW_FPROG = f"looker_core:view:{FQN_LOOKER_INSTANCE}.beacon_disaster_readiness.beacon_disaster_readiness.LookML_View_Federal_Programs"
FQN_LOOKML_EXPLORE_READINESS = f"looker_core:explore:{FQN_LOOKER_INSTANCE}.beacon_disaster_readiness.beacon_disaster_readiness.LookML_Explore_Beacon_Readiness"

# Native `@looker` Explore FQN in us-east1 (kept in sync so opening Tab 5D also shows human-readable tiles!)
FQN_NATIVE_LOOKML_VIEW_READINESS = f"looker_core:view:{FQN_LOOKER_INSTANCE}.singapore_smart_nation.singapore_smart_nation.beacon_county_readiness"
FQN_NATIVE_LOOKML_EXPLORE_READINESS = f"looker_core:explore:{FQN_LOOKER_INSTANCE}.singapore_smart_nation.singapore_smart_nation.beacon_county_readiness"

# Easy-to-Identify Looker Dashboard Elements (instead of numeric 2848, 2845, 2844!)
FQN_TILE_UNSERVED = f"looker_core:dashboard_element:{FQN_LOOKER_INSTANCE}.Looker_Beacon_Executive_Dashboard.Tile_Top_10_Unserved_Counties"
FQN_TILE_SCATTER = f"looker_core:dashboard_element:{FQN_LOOKER_INSTANCE}.Looker_Beacon_Executive_Dashboard.Tile_Digital_Divide_vs_Web_Intake"
FQN_TILE_CHANNEL = f"looker_core:dashboard_element:{FQN_LOOKER_INSTANCE}.Looker_Beacon_Executive_Dashboard.Tile_FEMA_State_Channel_Mix"
FQN_TILE_LOSSES = f"looker_core:dashboard_element:{FQN_LOOKER_INSTANCE}.Looker_Beacon_Executive_Dashboard.Tile_Billion_Dollar_Disaster_Losses"
FQN_TILE_ACTION = f"looker_core:dashboard_element:{FQN_LOOKER_INSTANCE}.Looker_Beacon_Executive_Dashboard.Tile_Spanner_Mobile_DRC_Action_Grid"
FQN_NAMED_LOOKER_TILES = [
    FQN_TILE_UNSERVED,
    FQN_TILE_SCATTER,
    FQN_TILE_CHANNEL,
    FQN_TILE_LOSSES,
    FQN_TILE_ACTION,
]

# Easy-to-Identify Looker Executive Dashboard & Governed Looker Data App (instead of numeric 519!)
FQN_LOOKER_DASHBOARD_519 = f"looker_core:dashboard:{FQN_LOOKER_INSTANCE}.Looker_Beacon_Executive_Dashboard"
FQN_LOOKER_APP = f"looker_core:dashboard:{FQN_LOOKER_INSTANCE}.Looker_Beacon_Grant_Simulator_App"


def setup_ecosystem_entries_and_lineage(headers: dict[str, str]) -> tuple[int, int]:
    print("6. Provisioning Human-Readable LookML & Looker Catalog Entries & Clean 6-Stage Data Lineage ...")

    # A. Ensure Custom EntryTypes exist in us-central1
    entry_types = [
        ("external-knowledge-graph", "Google Data Commons Public Knowledge Graph", "Authoritative public statistical knowledge graph (U.S. Census ACS, FEMA NRI, NOAA NCEI, BEA)."),
        ("federal-operational-system", "U.S. Federal Operational & Disaster System", "Real-time federal disaster declarations, assistance registrations, and field team telemetry from OpenFEMA & Beacon DRC."),
        ("gemini-enterprise-agent", "Gemini Conversational Analytics A2A Data Agent", "Conversational AI & Python code-interpreter agent in Gemini Conversational Analytics auto-grounded in Knowledge Catalog."),
        ("governed-looker-data-app", "Governed Looker Semantic Layer, Dashboard & Data App", "Governed LookML Views, Unified LookML Explore, Executive Dashboard Tiles, and Interactive Grant Simulator App."),
    ]
    for et_id, et_disp, et_desc in entry_types:
        et_url = f"https://dataplex.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/entryTypes?entryTypeId={et_id}"
        st_et, res_et = api_call(
            "POST",
            et_url,
            headers,
            {
                "displayName": et_disp,
                "description": et_desc,
                "platform": "GCP",
                "system": "CUSTOM",
            },
        )
        if st_et == 200 and isinstance(res_et, dict):
            wait_for_lro(res_et.get("name", ""), headers)
        print(f"   EntryType `{et_id}` -> {st_et}")

    # B. Create Custom EntryGroup `beacon-disaster-readiness-lineage` in us-central1
    eg_url = f"https://dataplex.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/entryGroups?entryGroupId={ECOSYSTEM_ENTRY_GROUP_ID}"
    st_eg, res_eg = api_call(
        "POST",
        eg_url,
        headers,
        {
            "displayName": "U.S. Public Sector · Beacon Disaster Readiness — LookML, Looker & Agentic Data Cloud Ecosystem",
            "description": "Cataloged upstream North America Google Data Commons & OpenFEMA sources, Governed LookML Views & Explore, Named Looker Dashboard Tiles, Executive Dashboard, and Gemini Conversational Analytics Agent connected to Cloud Spanner Graph (`readiness_dcgraph`).",
        },
    )
    if st_eg == 200 and isinstance(res_eg, dict):
        wait_for_lro(res_eg.get("name", ""), headers)
    print(f"   EntryGroup `{ECOSYSTEM_ENTRY_GROUP_ID}` -> {st_eg}")

    common_readiness_fields = [
        ("county_id", "STRING", "STRING", "Primary key U.S. County DCID (`geoId/*`, 3,144 counties)."),
        ("county_name", "STRING", "STRING", "Disambiguated U.S. County & State name (`Martin County, KY`, `Sumter County, AL`)."),
        ("state_code", "STRING", "STRING", "2-letter USPS State abbreviation."),
        ("social_vulnerability_score", "FLOAT64", "NUMBER", "[Knowledge Catalog Term: Social Vulnerability Score (SVI Tier-1 >= 75.0)] FEMA/CDC Social Vulnerability percentile."),
        ("no_internet_pct", "FLOAT64", "NUMBER", "[Knowledge Catalog Term: Household Digital Divide (No Internet >= 18.0%)] U.S. Census ACS household internet deficit (%)."),
        ("no_vehicle_pct", "FLOAT64", "NUMBER", "[Knowledge Catalog Term: Transit-Isolated Households (No Vehicle >= 10.0%)] U.S. Census ACS zero-vehicle household share (%)."),
        ("nri_risk_score", "FLOAT64", "NUMBER", "[Knowledge Catalog Term: Composite Hazard Risk Score (FEMA NRI >= 65.0)] FEMA NRI composite multi-hazard risk percentile."),
        ("community_resilience_score", "FLOAT64", "NUMBER", "[Knowledge Catalog Term: Community Resilience Index (FEMA NRI < 40.0 Alert)] FEMA NRI community resilience percentile."),
        ("poverty_pct", "FLOAT64", "NUMBER", "[Knowledge Catalog Term: Poverty Rate (Below Federal Line >= 20.0%)] U.S. Census ACS poverty rate (%)."),
        ("age_65_plus_pct", "FLOAT64", "NUMBER", "[Knowledge Catalog Term: Senior Population Share (Aged 65+ >= 20.0%)] U.S. Census ACS population aged 65+ (%)."),
        ("disability_pct", "FLOAT64", "NUMBER", "[Knowledge Catalog Term: Disability Access & Functional Needs (>= 18.0%)] U.S. Census ACS disability prevalence (%)."),
        ("web_registration_pct", "FLOAT64", "NUMBER", "[Knowledge Catalog Term: Web Intake Channel Share (< 60.0% Drop-Off)] OpenFEMA online web registration share (%)."),
        ("has_team_coverage", "BOOL", "BOOLEAN", "[Knowledge Catalog Term: Mobile Response Team Coverage Status (Beacon DRC)] Active `DCGraph` `:covers` mobile team indicator."),
    ]

    # C. Catalog Human-Readable Ecosystem, LookML Semantic Layer, and Looker Dashboard Entries
    ecosystem_entries = [
        {
            "id": "google-data-commons-usa",
            "type": "external-knowledge-graph",
            "fqn": FQN_DC_USA,
            "system": "DATA_COMMONS",
            "displayName": "Google_Data_Commons_USA (country/USA — U.S. Census ACS 5-Year & FEMA National Risk Index)",
            "description": "Authoritative North America public statistical knowledge graph (`country/USA`) spanning 3,144 U.S. counties and 51 states across U.S. Census Bureau ACS 5-Year Survey, FEMA National Risk Index (NRI), NOAA NCEI, and BEA.",
            "overview": (
                "<h3>Google Data Commons Public Knowledge Graph — North America (<code>Google_Data_Commons_USA</code>)</h3>"
                "<p>Provides authoritative county-level and state-level demographic, broadband connectivity, vehicle access, and "
                "FEMA National Risk Index observations ingested directly into Cloud Spanner Graph (<code>readiness_dcgraph</code>).</p>"
            ),
            "steward": "U.S. Census Bureau, FEMA NRI & Google Data Commons",
            "fedramp": "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
            "pillar": "Stage 1: Public Statistical Ground Truth (North America Data Commons)",
            "dcids": "country/USA | Count_Person, Count_Household_NoInternetAccess, Count_Household_NoVehicleAvailable, FemaSocialVulnerability_NaturalHazardImpact, FemaNationalRisk_NaturalHazardImpact",
            "rule": "All public statistical observations retain their canonical Data Commons DCID (`geoId/*`) and federal provenance URL.",
            "fields": [
                ("dcid", "STRING", "STRING", "Place DCID (e.g. `country/USA`, `geoId/28151` Washington County, MS, `geoId/21159` Martin County, KY)."),
                ("variable_measured", "STRING", "STRING", "StatisticalVariable DCID (e.g. `Count_Household_NoInternetAccess`, `FemaSocialVulnerability_NaturalHazardImpact`)."),
                ("observation_date", "STRING", "STRING", "Observation year (`1970`–`2025`)."),
                ("value", "FLOAT64", "NUMBER", "Official statistical observation value."),
                ("Count_Person", "INT64", "NUMBER", "U.S. Census ACS total resident population."),
                ("Count_Household_NoInternetAccess", "FLOAT64", "NUMBER", "U.S. Census ACS households without internet access (`no_internet_pct`)."),
                ("Count_Household_NoVehicleAvailable", "FLOAT64", "NUMBER", "U.S. Census ACS transit-isolated households with zero vehicles (`no_vehicle_pct`)."),
                ("Count_Person_65OrMoreYears", "FLOAT64", "NUMBER", "U.S. Census ACS senior population aged 65+ (`age_65_plus_pct`)."),
                ("Count_Person_WithDisability", "FLOAT64", "NUMBER", "U.S. Census ACS population with a disability (`disability_pct`)."),
                ("Count_Person_BelowPovertyLevelInThePast12Months", "FLOAT64", "NUMBER", "U.S. Census ACS population below the federal poverty threshold (`poverty_pct`)."),
                ("Median_Income_Household", "INT64", "NUMBER", "U.S. Census ACS median annual household income in USD."),
                ("FemaNationalRisk_NaturalHazardImpact", "FLOAT64", "NUMBER", "FEMA NRI composite multi-hazard risk percentile (`nri_risk_score`)."),
                ("FemaSocialVulnerability_NaturalHazardImpact", "FLOAT64", "NUMBER", "FEMA NRI & CDC/ATSDR Social Vulnerability percentile (`social_vulnerability_score`)."),
                ("FemaCommunityResilience_NaturalHazardImpact", "FLOAT64", "NUMBER", "FEMA NRI Community Resilience percentile (`community_resilience_score`)."),
                ("FemaExpectedAnnualLoss_NaturalHazardImpact", "FLOAT64", "NUMBER", "FEMA NRI Expected Annual Disaster Loss in USD (`nri_expected_annual_loss_usd`)."),
            ],
        },
        {
            "id": "us-federal-disaster-operations",
            "type": "federal-operational-system",
            "fqn": FQN_FEDERAL_OPS,
            "system": "OPENFEMA",
            "displayName": "US_Federal_Disaster_Operations (OpenFEMA Declarations, IA Intake & Beacon Mobile DRC Fleet)",
            "description": "Operational federal telemetry from OpenFEMA API v2 (263 Major Disaster Declarations `DR-*`, 5.3M Individual Assistance registrations across Web/Call Center/Mobile) and Beacon Regional Hubs & 46 Mobile DRC Teams.",
            "overview": (
                "<h3>U.S. Federal Disaster Operations — OpenFEMA &amp; Beacon DRC Fleet (<code>US_Federal_Disaster_Operations</code>)</h3>"
                "<p>Streams Presidential Major Disaster Declarations, county program designations (IHP, PA, HMGP), survivor registration "
                "intake channels, and Beacon Mobile DRC team assignments into Cloud Spanner Graph (<code>readiness_dcgraph</code>).</p>"
            ),
            "steward": "FEMA Office of Response & Recovery (OpenFEMA) & Beacon Readiness Office",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Stage 1: Federal Emergency Response & Field Operations Telemetry",
            "dcids": "OpenFEMA_DisasterDeclarationsSummaries | OpenFEMA_RegistrationIntakeIHP | Beacon_MobileTeamFleet",
            "rule": "Operational feeds are aggregated at the `(disaster_id, county_id)` level under FedRAMP High governance.",
            "fields": [
                ("disaster_id", "STRING", "STRING", "OpenFEMA Major Disaster Declaration ID (`fema/DR-4834-FL`, `fema/DR-4828-NC`)."),
                ("county_id", "STRING", "STRING", "Designated U.S. County FIPS DCID (`geoId/*`)."),
                ("incident_type", "STRING", "STRING", "FEMA hazard incident type (`Hurricane`, `Flood`, `Severe Storm`, `Tornado`, `Fire`)."),
                ("declaration_date", "STRING", "STRING", "Presidential disaster declaration date."),
                ("ihp_declared", "BOOL", "BOOLEAN", "Individual & Households Program (IHP) declaration flag."),
                ("total_valid_registrations", "INT64", "NUMBER", "Total valid FEMA Individual Assistance registrations."),
                ("web_registrations", "INT64", "NUMBER", "Online web portal registrations (DisasterAssistance.gov)."),
                ("call_center_registrations", "INT64", "NUMBER", "FEMA 1-800 Helpline Call Center registrations."),
                ("mobile_registrations", "INT64", "NUMBER", "Roving Mobile Disaster Recovery Center (MDRC) registrations."),
                ("web_share_pct", "FLOAT64", "NUMBER", "Web intake channel share percentage (`web_registration_pct`)."),
                ("assigned_team_id", "STRING", "STRING", "Beacon Mobile DRC unit identifier (`beacon/team/*`)."),
                ("has_team_coverage", "BOOL", "BOOLEAN", "Active mobile team `:covers` assignment indicator."),
            ],
        },
        {
            "id": "lookml-view-beacon-county-readiness",
            "type": "governed-looker-data-app",
            "fqn": FQN_LOOKML_VIEW_READINESS,
            "system": "LOOKER",
            "displayName": "LookML_View_County_Readiness (Governed LookML View: beacon_county_readiness)",
            "description": "Blue-Chip Certified LookML View (`beacon_county_readiness`) modeling 24 dimensions and 9 measures across 3,144 U.S. counties from Cloud Spanner `CountyReadiness` and North America Data Commons (`country/USA`).",
            "overview": (
                "<h3>Governed LookML Semantic View — U.S. County Disaster Readiness (<code>LookML_View_County_Readiness</code>)</h3>"
                "<p><b>Blue-Chip Certified</b> LookML view governed by Principal Steward <b>Sean Zinsmeister</b> (<code>demo-operator@example.com</code>). "
                "Maps Cloud Spanner's <code>CountyReadiness</code> view into certified Looker dimensions and measures bound to the Beacon Federal Disaster Readiness Business Glossary.</p>"
            ),
            "steward": "Sean Zinsmeister (demo-operator@example.com) & FEMA / U.S. Census Bureau",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Stage 4B: Governed LookML Semantic Layer (LookML View)",
            "dcids": "country/USA | LookML View: beacon_county_readiness -> Explore: beacon_county_readiness",
            "rule": "Defines governed LookML measures (`avg_social_vulnerability_score`, `avg_no_internet_pct`, `unserved_high_vulnerability_counties`) over Cloud Spanner `CountyReadiness`.",
            "fields": common_readiness_fields,
        },
        {
            "id": "lookml-view-beacon-deployment-plan",
            "type": "governed-looker-data-app",
            "fqn": FQN_LOOKML_VIEW_PLAN,
            "system": "LOOKER",
            "displayName": "LookML_View_Deployment_Plan (Governed LookML View: beacon_deployment_plan)",
            "description": "Governed LookML View (`beacon_deployment_plan`) modeling Cloud Spanner's `DeploymentPlan` System of Action table for live Mobile DRC fleet dispatch.",
            "overview": (
                "<h3>Governed LookML Semantic View — Federal Mobile DRC Deployment Plan (<code>LookML_View_Deployment_Plan</code>)</h3>"
                "<p>Joined via <code>LEFT OUTER JOIN</code> on <code>county_id</code> into <code>LookML_Explore_Beacon_Readiness</code>.</p>"
            ),
            "steward": "Sean Zinsmeister (demo-operator@example.com) & Beacon Federal Readiness Office",
            "fedramp": "FEDRAMP_HIGH_OFFICIAL_ACTION",
            "pillar": "Stage 4B: Governed LookML Semantic Layer (System of Action View)",
            "dcids": "Spanner: readiness_dcgraph.DeploymentPlan",
            "rule": "Joined on `county_id` in `LookML_Explore_Beacon_Readiness`.",
            "fields": [
                ("county_id", "STRING", "STRING", "Target U.S. County DCID (`geoId/*`)."),
                ("priority_tier", "STRING", "STRING", "Priority dispatch tier (`Tier 1 - Immediate`, `Tier 2 - Secondary`)."),
                ("action", "STRING", "STRING", "Prescribed field intervention (`Deploy Mobile Team`, `Establish Recovery Center`)."),
                ("assigned_team_id", "STRING", "STRING", "Assigned Beacon Mobile DRC unit ID (`beacon/team/*`)."),
                ("status", "STRING", "STRING", "Operational dispatch status (`Proposed`, `Approved`, `Dispatched`)."),
            ],
        },
        {
            "id": "lookml-view-beacon-macro-timeline",
            "type": "governed-looker-data-app",
            "fqn": FQN_LOOKML_VIEW_MACRO,
            "system": "LOOKER",
            "displayName": "LookML_View_Macro_Timeline (Governed LookML View: beacon_national_macro_timeline)",
            "description": "Governed LookML View (`beacon_national_macro_timeline`) modeling 1970–2025 U.S. Census, EPA/EIA, and NOAA/FEMA billion-dollar disaster series (`country/USA`).",
            "overview": (
                "<h3>Governed LookML Semantic View — U.S. Macro &amp; Disaster Trajectory (<code>LookML_View_Macro_Timeline</code>)</h3>"
                "<p>Models 56 years of national Data Commons series (`us_population`, `seniors_65_plus_pct`, `billion_dollar_disasters_loss_usd_b`) in LookML.</p>"
            ),
            "steward": "U.S. Census Bureau, NOAA NCEI & Sean Zinsmeister",
            "fedramp": "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
            "pillar": "Stage 4B: Governed LookML Semantic Layer (Macro Timeline View)",
            "dcids": "country/USA | Count_Person, Count_Person_65OrMoreYears, FemaExpectedAnnualLoss_NaturalHazardImpact",
            "rule": "Powers historical trajectory tiles and KPI sparklines in `Looker_Beacon_Executive_Dashboard`.",
            "fields": [
                ("year", "INT64", "NUMBER", "Observation year (`1970`–`2025`)."),
                ("us_population", "INT64", "NUMBER", "U.S. resident population (`Count_Person`)."),
                ("seniors_65_plus_pct", "FLOAT64", "NUMBER", "Share of U.S. population aged 65+ (%)."),
                ("billion_dollar_disasters_loss_usd_b", "FLOAT64", "NUMBER", "NOAA/FEMA billion-dollar disaster losses ($B USD)."),
            ],
        },
        {
            "id": "lookml-view-beacon-federal-programs",
            "type": "governed-looker-data-app",
            "fqn": FQN_LOOKML_VIEW_FPROG,
            "system": "LOOKER",
            "displayName": "LookML_View_Federal_Programs (Governed LookML View: beacon_federal_program_summary)",
            "description": "Governed LookML View (`beacon_federal_program_summary`) modeling 10 flagship U.S. federal disaster and resilience programs across FEMA, FCC/NTIA, HHS, and HUD.",
            "overview": (
                "<h3>Governed LookML Semantic View — Federal Disaster &amp; Resilience Programs (<code>LookML_View_Federal_Programs</code>)</h3>"
                "<p>Models annual budget (`annual_budget_million_usd`), households helped (`assisted_households`), and online intake share (`web_intake_share_pct`).</p>"
            ),
            "steward": "OMB, FEMA, HUD, HHS & Sean Zinsmeister",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Stage 4B: Governed LookML Semantic Layer (Federal Programs View)",
            "dcids": "country/USA | FederalProgramSummary (10 Flagship Federal Programs)",
            "rule": "Governs federal program budget and channel mix metrics across Looker and Gemini Conversational Analytics.",
            "fields": [
                ("program_id", "STRING", "STRING", "Federal program ID."),
                ("program_name", "STRING", "STRING", "Official federal program name."),
                ("policy_pillar", "STRING", "STRING", "Federal policy pillar."),
                ("annual_budget_million_usd", "FLOAT64", "NUMBER", "Annual enacted budget ($M USD)."),
                ("assisted_households", "INT64", "NUMBER", "Assisted U.S. households."),
                ("web_intake_share_pct", "FLOAT64", "NUMBER", "Online web intake share (%)."),
            ],
        },
        {
            "id": "lookml-explore-beacon-disaster-readiness",
            "type": "governed-looker-data-app",
            "fqn": FQN_LOOKML_EXPLORE_READINESS,
            "system": "LOOKER",
            "displayName": "LookML_Explore_Beacon_Readiness (Unified LookML Explore: beacon_county_readiness)",
            "description": "Blue-Chip Certified Unified LookML Explore (`beacon_county_readiness`) joining `LookML_View_County_Readiness`, `LookML_View_Deployment_Plan`, `LookML_View_Macro_Timeline`, and `LookML_View_Federal_Programs` into a single governed semantic model (60 fields).",
            "overview": (
                "<h3>Unified LookML Semantic Explore — Beacon U.S. Disaster Readiness (<code>LookML_Explore_Beacon_Readiness</code>)</h3>"
                "<p><b>Blue-Chip Certified</b> single source of truth in Looker (<code>cloud-bi-opm</code>) governed by Principal Steward "
                "<b>Sean Zinsmeister</b> (<code>demo-operator@example.com</code>). Unifies all 4 LookML Views so every tile on "
                "<code>Looker_Beacon_Executive_Dashboard</code> and <code>Looker_Beacon_Grant_Simulator_App</code> shares 100% consistent metric definitions and cross-filtering.</p>"
            ),
            "steward": "Sean Zinsmeister (demo-operator@example.com) & FEMA / U.S. Census Bureau / CDC",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Stage 4B: Unified LookML Semantic Explore (Single Source of Truth)",
            "dcids": "country/USA | Unified Explore: beacon_county_readiness (60 Governed Fields)",
            "rule": "100% of Looker Dashboard tiles and Looker Data App simulations query this single governed Explore.",
            "fields": common_readiness_fields + [
                ("priority_tier", "STRING", "STRING", "[Joined from LookML_View_Deployment_Plan] Cloud Spanner dispatch priority tier."),
                ("action", "STRING", "STRING", "[Joined from LookML_View_Deployment_Plan] Prescribed Mobile DRC field intervention."),
            ],
        },
        {
            "id": "tile-top-10-unserved-disaster-counties",
            "type": "governed-looker-data-app",
            "fqn": FQN_TILE_UNSERVED,
            "system": "LOOKER",
            "displayName": "Tile_Top_10_Unserved_Counties (Looker Tile: Top 10 Unserved High-Vulnerability U.S. Disaster Counties)",
            "description": "Governed Looker Dashboard Tile ranking unserved high-vulnerability U.S. disaster counties (`has_team_coverage = FALSE`, `SVI >= 75.0`) powered by `LookML_Explore_Beacon_Readiness`.",
            "overview": "<h3>Looker Visualization Tile — Top 10 Unserved High-Vulnerability U.S. Disaster Counties (<code>Tile_Top_10_Unserved_Counties</code>)</h3><p>Pinpoints Martin County (KY), Sumter County (AL), Washington County (MS), Bolivar County (MS), and Hancock County (GA) for immediate Mobile DRC dispatch.</p>",
            "steward": "Sean Zinsmeister (demo-operator@example.com) & FEMA Field Operations",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Stage 5A: Governed Looker Visualization Tile",
            "dcids": "country/USA | Explore: beacon_county_readiness",
            "rule": "Filters `has_team_coverage = FALSE` AND `disasters_since_2023 >= 1`, ranked by `social_vulnerability_score`.",
            "fields": common_readiness_fields[:6],
        },
        {
            "id": "tile-digital-divide-vs-web-intake",
            "type": "governed-looker-data-app",
            "fqn": FQN_TILE_SCATTER,
            "system": "LOOKER",
            "displayName": "Tile_Digital_Divide_vs_Web_Intake (Looker Tile: Household Digital Divide % vs. Web Registration Share %)",
            "description": "Governed Looker Scatter Plot correlating U.S. Census ACS household internet deficit (`no_internet_pct`) with OpenFEMA online registration share (`web_registration_pct`).",
            "overview": "<h3>Looker Visualization Tile — Digital Divide vs. Online FEMA Registration Share (<code>Tile_Digital_Divide_vs_Web_Intake</code>)</h3><p>Visualizes how broadband deficits (`>= 18.0%`) depress online disaster intake (`< 60.0%`) across U.S. disaster counties.</p>",
            "steward": "Sean Zinsmeister (demo-operator@example.com) & FCC/NTIA / FEMA IA",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Stage 5A: Governed Looker Visualization Tile",
            "dcids": "country/USA | Count_Household_NoInternetAccess, OpenFEMA_WebRegistrationShare",
            "rule": "Correlates `no_internet_pct` (X-axis) against `web_registration_pct` (Y-axis) across disaster-impacted counties.",
            "fields": common_readiness_fields[:6],
        },
        {
            "id": "tile-fema-state-channel-mix",
            "type": "governed-looker-data-app",
            "fqn": FQN_TILE_CHANNEL,
            "system": "LOOKER",
            "displayName": "Tile_FEMA_State_Channel_Mix (Looker Tile: FEMA Disaster Assistance Intake Channel Mix by State)",
            "description": "Governed Looker Stacked Bar Chart comparing Web vs. Call Center vs. Mobile DRC registrations across top disaster-impacted U.S. states.",
            "overview": "<h3>Looker Visualization Tile — FEMA Disaster Assistance Intake Channel Mix by State (<code>Tile_FEMA_State_Channel_Mix</code>)</h3><p>Compares online web intake versus call center and roving Mobile DRC intake across top disaster-impacted states.</p>",
            "steward": "Sean Zinsmeister (demo-operator@example.com) & FEMA Individual Assistance",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Stage 5A: Governed Looker Visualization Tile",
            "dcids": "country/USA | OpenFEMA Registration Channel Telemetry",
            "rule": "Evaluates state-level intake equity against Knowledge Catalog rule KC-US-010 (`web_registration_pct < 60.0%`).",
            "fields": common_readiness_fields[:6],
        },
        {
            "id": "tile-billion-dollar-disaster-losses",
            "type": "governed-looker-data-app",
            "fqn": FQN_TILE_LOSSES,
            "system": "LOOKER",
            "displayName": "Tile_Billion_Dollar_Disaster_Losses (Looker Tile: NOAA / FEMA Billion-Dollar Disaster Losses & Declarations)",
            "description": "Governed Looker Multi-Series Line Chart tracking NOAA NCEI billion-dollar disaster losses (`$B USD`) and FEMA major disaster declarations (`2000–2025`).",
            "overview": "<h3>Looker Visualization Tile — NOAA / FEMA Billion-Dollar Disaster Losses &amp; Declarations (<code>Tile_Billion_Dollar_Disaster_Losses</code>)</h3><p>Tracks longitudinal U.S. disaster losses (`$192.5B` in 2025) and major declarations (`96` in 2025) from `LookML_View_Macro_Timeline`.</p>",
            "steward": "Sean Zinsmeister (demo-operator@example.com) & NOAA NCEI / FEMA",
            "fedramp": "FEDRAMP_MODERATE_PUBLIC_DATA_COMMONS",
            "pillar": "Stage 5A: Governed Looker Visualization Tile",
            "dcids": "country/USA | FemaExpectedAnnualLoss_NaturalHazardImpact",
            "rule": "Evaluates macro hazard loss trajectory against Knowledge Catalog rule KC-US-006 (`EAL >= $25M USD`).",
            "fields": [
                ("year", "INT64", "NUMBER", "Observation year (`2000`–`2025`)."),
                ("billion_dollar_disasters_loss_usd_b", "FLOAT64", "NUMBER", "NOAA/FEMA billion-dollar disaster losses ($B USD)."),
            ],
        },
        {
            "id": "tile-spanner-mobile-drc-action-grid",
            "type": "governed-looker-data-app",
            "fqn": FQN_TILE_ACTION,
            "system": "LOOKER",
            "displayName": "Tile_Spanner_Mobile_DRC_Action_Grid (Looker Tile: Cloud Spanner Active Federal Mobile DRC Deployment Plan)",
            "description": "Governed Looker Action Grid joining Cloud Spanner `DeploymentPlan` with U.S. Census ACS & FEMA NRI county metrics for live field dispatch.",
            "overview": "<h3>Looker Visualization Tile — Cloud Spanner Active Federal Mobile DRC Deployment Plan (<code>Tile_Spanner_Mobile_DRC_Action_Grid</code>)</h3><p>Surfaces the 12 active Tier-1 &amp; Tier-2 Mobile DRC dispatches in Cloud Spanner (`DeploymentPlan`) joined with Census ACS and FEMA NRI county indicators.</p>",
            "steward": "Sean Zinsmeister (demo-operator@example.com) & Beacon Federal Readiness Office",
            "fedramp": "FEDRAMP_HIGH_OFFICIAL_ACTION",
            "pillar": "Stage 5A: Governed Looker Visualization Tile (System of Action)",
            "dcids": "country/USA | Spanner: CountyReadiness JOIN DeploymentPlan",
            "rule": "Triggers transactional Looker Actions write-back to Cloud Spanner `DeploymentPlan`.",
            "fields": common_readiness_fields[:6] + [
                ("priority_tier", "STRING", "STRING", "Cloud Spanner dispatch priority tier."),
                ("action", "STRING", "STRING", "Prescribed Mobile DRC action."),
            ],
        },
        {
            "id": "looker-beacon-executive-dashboard",
            "type": "governed-looker-data-app",
            "fqn": FQN_LOOKER_DASHBOARD_519,
            "system": "LOOKER",
            "displayName": "Looker_Beacon_Executive_Dashboard (U.S. Public Sector · Beacon Disaster Readiness Executive Dashboard)",
            "description": "Blue-Chip Certified 13-Tile Looker Executive Dashboard (`https://your-looker-instance.cloud.looker.com/dashboards/519`) styled in the Old Glory Blue (`#3C3B6E`) gradient palette with live cross-filtering over `LookML_Explore_Beacon_Readiness`.",
            "overview": (
                "<h3>Looker Executive Dashboard — U.S. Public Sector · Beacon Disaster Readiness (<code>Looker_Beacon_Executive_Dashboard</code>)</h3>"
                "<p><b>Blue-Chip Certified</b> 13-tile executive command center hosted on <code>https://your-looker-instance.cloud.looker.com/dashboards/519</code> "
                "and governed by Principal Steward <b>Sean Zinsmeister</b> (<code>demo-operator@example.com</code>). Styled in the Old Glory Blue "
                "(<code>#3C3B6E</code>) luminous gradient palette with 100% single-Explore cross-filtering across all 13 tiles.</p>"
            ),
            "steward": "Sean Zinsmeister (demo-operator@example.com) & Beacon Federal Readiness Office",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Stage 5B: Executive BI Command Center — Old Glory Blue (#3C3B6E) Dashboard",
            "dcids": "country/USA | LookML_Explore_Beacon_Readiness -> Looker_Beacon_Executive_Dashboard -> DeploymentPlan",
            "rule": "Consolidates all governed Looker visualization tiles with interactive cross-filtering and Spanner write-back.",
            "fields": common_readiness_fields,
        },
        {
            "id": "governed-looker-beacon-data-app",
            "type": "governed-looker-data-app",
            "fqn": FQN_LOOKER_APP,
            "system": "LOOKER",
            "displayName": "Looker_Beacon_Grant_Simulator_App (Governed Looker Data App & $250M FEMA Mobile DRC Grant Simulator)",
            "description": "Governed Interactive Looker Data App (`https://your-looker-instance.cloud.looker.com/dashboards/274`) built via the Looker CLI on Looker's semantic layer (`LookML_Explore_Beacon_Readiness`) with transactional write-back to Cloud Spanner `DeploymentPlan`.",
            "overview": (
                "<h3>Governed Looker Data App — Beacon Federal Grant &amp; Fleet Dispatch Simulator (<code>Looker_Beacon_Grant_Simulator_App</code>)</h3>"
                "<p>Interactive application surface of the Agentic Data Cloud loop (<code>See &rarr; Show &rarr; Do</code>). Enables FEMA "
                "and state emergency directors to simulate a <code>$250M USD FEMA Mobile DRC Grant</code> (+10 Mobile DRC &amp; SatCom units) "
                "and commit approved deployment plans straight back to Cloud Spanner <code>DeploymentPlan</code>.</p>"
            ),
            "steward": "Sean Zinsmeister (demo-operator@example.com) & Beacon Readiness Office",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Stage 5B: Agentic Data Cloud — Governed Looker Data Apps (See -> Show -> Do)",
            "dcids": "country/USA | LookML_Explore_Beacon_Readiness",
            "rule": "Runs on Headless Looker with LookML metric governance and transactional write-back to Cloud Spanner `DeploymentPlan`.",
            "fields": common_readiness_fields[:6] + [
                ("simulated_mdrc_units_added", "INT64", "NUMBER", "Simulated additional Mobile Disaster Recovery Units dispatched (+10 units under $250M grant)."),
                ("looker_action_dispatch_status", "STRING", "STRING", "Looker Actions API transactional write-back status to `DeploymentPlan`."),
            ],
        },
        {
            "id": "bigquery-graph-beacon-disaster-readiness",
            "type": "external-knowledge-graph",
            "fqn": FQN_BQ_GRAPH,
            "system": "BIGQUERY",
            "displayName": "Borderless_Lakehouse_Beacon_Readiness (Google Cloud Borderless Lakehouse: BigLake Apache Iceberg + Unstructured SitRep PDFs)",
            "description": "Google Cloud Borderless Lakehouse (`beacon_disaster_readiness`) uniting Cloud Spanner Graph (`readiness_dcgraph`), BigLake Managed Apache Iceberg tables (`noaa_hazard_iceberg`, `fema_field_assessments_iceberg`), and BigLake Object Tables (`fema_field_sitrep_objects` over unstructured FEMA Field SitRep PDFs in Cloud Storage) with zero ETL duplication.",
            "overview": (
                "<h3>Google Cloud Borderless Lakehouse — Multimodal &amp; Open Iceberg Analytics (<code>Borderless_Lakehouse_Beacon_Readiness</code>)</h3>"
                "<p><b>Blue-Chip Certified</b> open, multimodal lakehouse in BigQuery (<code>your-gcp-project-id.beacon_disaster_readiness</code>) "
                "paired with Cloud Spanner Graph (<code>readiness_dcgraph.DCGraph</code>) and governed by Knowledge Catalog.</p>"
                "<ul>"
                "<li><b>Cloud Spanner Graph (Operational Knowledge Graph &amp; System of Action)</b>: Connects UN/US Data Commons geographic hierarchies with live federal dispatch and transactional write-backs to <code>DeploymentPlan</code>.</li>"
                "<li><b>BigLake Managed Apache Iceberg Tables (<code>noaa_hazard_iceberg</code> &amp; <code>fema_field_assessments_iceberg</code>)</b>: Queries open Apache Iceberg / Parquet storm surge, cell outage, and road washout telemetry in place with zero data duplication.</li>"
                "<li><b>BigLake Object Tables (<code>fema_field_sitrep_objects</code>)</b>: Brings unstructured FEMA Preliminary Damage Assessment (PDA) PDF reports in Cloud Storage under the exact same SQL engine, fine-grained security, and end-to-end lineage.</li>"
                "</ul>"
                "<h4>Ready-to-Run BigQuery Studio Borderless Lakehouse Query</h4>"
                "<pre><code>SELECT\n"
                "  c.county_id, c.county_name, c.state_code,\n"
                "  ROUND(c.social_vulnerability_score, 2) AS svi_score,\n"
                "  ROUND(c.no_internet_pct, 1) AS no_internet_pct,\n"
                "  ice.active_hazard_alert,\n"
                "  ice.cell_tower_outage_pct,\n"
                "  pda.road_washout_status,\n"
                "  pda.recommended_mobile_unit,\n"
                "  obj.uri AS unstructured_sitrep_pdf_uri\n"
                "FROM `your-gcp-project-id.beacon_disaster_readiness.county_readiness` c\n"
                "JOIN `your-gcp-project-id.beacon_disaster_readiness.noaa_hazard_iceberg` ice\n"
                "  ON c.county_id = ice.county_id\n"
                "JOIN `your-gcp-project-id.beacon_disaster_readiness.fema_field_assessments_iceberg` pda\n"
                "  ON c.county_id = pda.county_id\n"
                "LEFT JOIN `your-gcp-project-id.beacon_disaster_readiness.fema_field_sitrep_objects` obj\n"
                "  ON obj.uri = pda.sitrep_pdf_uri\n"
                "WHERE c.has_team_coverage = FALSE\n"
                "  AND c.social_vulnerability_score >= 75.0\n"
                "  AND c.disasters_since_2023 >= 1\n"
                "  AND c.total_registrations > 0\n"
                "  AND c.state_code NOT IN ('AK', 'HI', 'PR')\n"
                "ORDER BY svi_score DESC\n"
                "LIMIT 10;</code></pre>"
            ),
            "steward": "Sean Zinsmeister (demo-operator@example.com) & Beacon Federal Readiness Office",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Stage 4B: Google Cloud Borderless Lakehouse (BigLake Apache Iceberg + Unstructured Object Tables + Spanner Graph)",
            "dcids": "country/USA | Borderless Lakehouse: noaa_hazard_iceberg + fema_field_assessments_iceberg + fema_field_sitrep_objects",
            "rule": "Unifies open Apache Iceberg tables, unstructured GCS Field SitRep PDFs, and Spanner operational data in place without ETL silos.",
            "fields": common_readiness_fields,
        },
        {
            "id": "gemini-enterprise-beacon-readiness-agent",
            "type": "gemini-enterprise-agent",
            "fqn": FQN_GE_AGENT,
            "system": "VERTEX_AI_SEARCH",
            "displayName": "Gemini_Enterprise_Beacon_Agent (Beacon Disaster Readiness & Policy Intelligence Agent 14131532519214632868)",
            "description": "Production Conversational Analytics & A2A Agent in Gemini Conversational Analytics (`looker-gemini-enterprise_1789121788250`) powered by the Google Cloud Borderless Lakehouse (`BigLake Apache Iceberg` + `Unstructured Object Tables`), Cloud Spanner Graph (`readiness_dcgraph`), and North America Data Commons (`country/USA`), auto-grounded in Knowledge Catalog.",
            "overview": (
                "<h3>Gemini Conversational Analytics A2A Agent — Beacon Disaster Readiness (<code>Gemini_Enterprise_Beacon_Agent</code>)</h3>"
                "<p>Conversational investigation and geospatial/statistical visualization surface on the Agentic Data Cloud (<code>See &rarr; Show &rarr; Do</code>). "
                "Leverages the <b>Google Cloud Borderless Lakehouse</b> (<code>BigLake Apache Iceberg</code> + <code>Unstructured SitRep Object Tables</code>) alongside <b>Cloud Spanner Graph</b> (<code>readiness_dcgraph</code>), "
                "automatically applies Knowledge Catalog business glossary thresholds (<code>beacon-disaster-readiness-glossary</code>), and recommends Tier-1 Mobile DRC dispatches to <code>DeploymentPlan</code>.</p>"
            ),
            "steward": "Sean Zinsmeister (demo-operator@example.com) & Beacon Federal Readiness Office",
            "fedramp": "FEDRAMP_HIGH_CUI_AGENCY_AGGREGATED",
            "pillar": "Stage 5B: Agentic Data Cloud — Conversational AI Investigation & Action",
            "dcids": "country/USA | All 16 Governed Federal Contracts (KC-US-001 to KC-US-016)",
            "rule": "Every natural-language prompt automatically resolves Knowledge Catalog business glossary thresholds and renders Looker Studio Modern charts or Google Maps.",
            "fields": common_readiness_fields[:8] + [
                ("rule_id", "STRING", "STRING", "Applied Knowledge Catalog federal contract ID (`KC-US-001`–`KC-US-016`)."),
                ("policy_threshold", "STRING", "STRING", "Auto-applied Knowledge Catalog quantitative policy threshold."),
                ("recommended_action", "STRING", "STRING", "Generated Mobile DRC dispatch action written back to `DeploymentPlan`."),
            ],
        },
    ]

    eg_parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/entryGroups/{ECOSYSTEM_ENTRY_GROUP_ID}"
    for ent in ecosystem_entries:
        entry_name = f"{eg_parent}/entries/{ent['id']}"
        schema_fields = [
            {"name": fn, "dataType": dt, "metadataType": mt, "mode": "REQUIRED"}
            for fn, dt, mt, _ in ent["fields"]
        ]
        desc_fields = [
            {"name": fn, "description": fdesc}
            for fn, _, _, fdesc in ent["fields"]
        ]
        entry_payload = {
            "name": entry_name,
            "entryType": f"projects/{PROJECT_ID}/locations/{LOCATION}/entryTypes/{ent['type']}",
            "fullyQualifiedName": ent["fqn"],
            "entrySource": {
                "resource": f"//dataplex.googleapis.com/{entry_name}",
                "system": ent.get("system", "CUSTOM"),
                "platform": "GCP",
                "displayName": ent["displayName"],
                "description": ent["description"],
                "location": LOCATION,
            },
            "aspects": {
                "655216118709.global.schema": {
                    "aspectType": "projects/655216118709/locations/global/aspectTypes/schema",
                    "data": {"fields": schema_fields},
                },
                "655216118709.global.descriptions": {
                    "aspectType": "projects/655216118709/locations/global/aspectTypes/descriptions",
                    "data": {
                        "description": ent["description"],
                        "userManaged": True,
                        "fields": desc_fields,
                    },
                },
                "655216118709.global.overview": {
                    "aspectType": "projects/655216118709/locations/global/aspectTypes/overview",
                    "data": {"content": ent["overview"], "contentType": "HTML"},
                },
                "655216118709.global.contacts": {
                    "aspectType": "projects/655216118709/locations/global/aspectTypes/contacts",
                    "data": {
                        "identities": [
                            {"role": "steward", "name": "Sean Zinsmeister (Principal Steward · Google Data Cloud)", "id": "demo-operator@example.com"},
                            {"role": "steward", "name": ent["steward"], "id": "beacon-data-steward@fema.dhs.gov"},
                            {"role": "owner", "name": "Beacon Federal Readiness Office", "id": "demo-operator@example.com"},
                        ]
                    },
                },
                f"{PROJECT_NUM}.us-central1.{ASPECT_TYPE_ID}": {
                    "aspectType": f"projects/{PROJECT_NUM}/locations/us-central1/aspectTypes/{ASPECT_TYPE_ID}",
                    "data": {
                        "federal_agency_steward": ent["steward"],
                        "fedramp_security_classification": ent["fedramp"],
                        "certification_status": "BLUE_CHIP_CERTIFIED",
                        "federal_policy_pillar": ent["pillar"],
                        "data_commons_dcids": ent["dcids"],
                        "policy_threshold_rule": ent["rule"],
                    },
                },
            },
        }
        if ent.get("queries"):
            entry_payload["aspects"]["655216118709.global.queries"] = {
                "aspectType": "projects/655216118709/locations/global/aspectTypes/queries",
                "data": {"queries": ent["queries"]},
            }
        st_ce, _ = api_call(
            "POST",
            f"https://dataplex.googleapis.com/v1/{eg_parent}/entries?entryId={ent['id']}",
            headers,
            entry_payload,
        )
        if st_ce == 409:
            st_ce, _ = api_call(
                "PATCH",
                f"https://dataplex.googleapis.com/v1/{entry_name}?updateMask=aspects,entrySource,fullyQualifiedName",
                headers,
                entry_payload,
            )
        print(f"   Cataloged Entry `{ent['id']}` (FQN: `{ent['fqn']}`) -> {st_ce}")

    # Also bind Business Glossary Terms & `schema-join` EntryLinks to the human-readable LookML View & Explore entries in `us-central1`
    us_central_eg = f"projects/{PROJECT_NUM}/locations/{LOCATION}/entryGroups/{ECOSYSTEM_ENTRY_GROUP_ID}"
    us_central_term_prefix = (
        f"projects/{PROJECT_NUM}/locations/{LOCATION}/entryGroups/@dataplex/entries/"
        f"projects/{PROJECT_NUM}/locations/{LOCATION}/glossaries/{GLOSSARY_ID}/terms"
    )
    readable_lookml_term_links = [
        ("social-vulnerability-score", "lookml-view-beacon-county-readiness", "Schema.social_vulnerability_score", "rvw-svi"),
        ("social-vulnerability-score", "lookml-explore-beacon-disaster-readiness", "Schema.social_vulnerability_score", "rex-svi"),
        ("social-vulnerability-score", "looker-beacon-executive-dashboard", "Schema.social_vulnerability_score", "rdsh-svi"),
        ("household-digital-divide", "lookml-view-beacon-county-readiness", "Schema.no_internet_pct", "rvw-inet"),
        ("household-digital-divide", "lookml-explore-beacon-disaster-readiness", "Schema.no_internet_pct", "rex-inet"),
        ("household-digital-divide", "looker-beacon-executive-dashboard", "Schema.no_internet_pct", "rdsh-inet"),
        ("transit-isolated-households", "lookml-view-beacon-county-readiness", "Schema.no_vehicle_pct", "rvw-veh"),
        ("transit-isolated-households", "lookml-explore-beacon-disaster-readiness", "Schema.no_vehicle_pct", "rex-veh"),
        ("transit-isolated-households", "looker-beacon-executive-dashboard", "Schema.no_vehicle_pct", "rdsh-veh"),
        ("composite-hazard-risk-score", "lookml-view-beacon-county-readiness", "Schema.nri_risk_score", "rvw-nri"),
        ("composite-hazard-risk-score", "lookml-explore-beacon-disaster-readiness", "Schema.nri_risk_score", "rex-nri"),
        ("composite-hazard-risk-score", "looker-beacon-executive-dashboard", "Schema.nri_risk_score", "rdsh-nri"),
        ("community-resilience-index", "lookml-view-beacon-county-readiness", "Schema.community_resilience_score", "rvw-res"),
        ("community-resilience-index", "lookml-explore-beacon-disaster-readiness", "Schema.community_resilience_score", "rex-res"),
        ("community-resilience-index", "looker-beacon-executive-dashboard", "Schema.community_resilience_score", "rdsh-res"),
        ("web-intake-channel-share", "lookml-view-beacon-county-readiness", "Schema.web_registration_pct", "rvw-web"),
        ("web-intake-channel-share", "lookml-explore-beacon-disaster-readiness", "Schema.web_registration_pct", "rex-web"),
        ("web-intake-channel-share", "looker-beacon-executive-dashboard", "Schema.web_registration_pct", "rdsh-web"),
        ("mobile-response-team-coverage", "lookml-view-beacon-county-readiness", "Schema.has_team_coverage", "rvw-team"),
        ("mobile-response-team-coverage", "lookml-explore-beacon-disaster-readiness", "Schema.has_team_coverage", "rex-team"),
        ("mobile-response-team-coverage", "looker-beacon-executive-dashboard", "Schema.has_team_coverage", "rdsh-team"),
        ("federal-deployment-plan", "lookml-view-beacon-deployment-plan", "Schema.priority_tier", "rvw-plan"),
        ("federal-deployment-plan", "lookml-explore-beacon-disaster-readiness", "Schema.priority_tier", "rex-plan"),
    ]
    for term_id, ent_id, col_path, short_id in readable_lookml_term_links:
        link_id = f"bdef-lkr-{short_id}"
        payload = {
            "entryLinkType": "projects/655216118709/locations/global/entryLinkTypes/definition",
            "entryReferences": [
                {"name": f"{us_central_eg}/entries/{ent_id}", "path": col_path, "type": "SOURCE"},
                {"name": f"{us_central_term_prefix}/{term_id}", "type": "TARGET"},
            ],
        }
        st_el, _ = api_call(
            "POST",
            f"https://dataplex.googleapis.com/v1/{us_central_eg}/entryLinks?entryLinkId={link_id}",
            headers,
            payload,
        )
        if st_el == 409:
            api_call("DELETE", f"https://dataplex.googleapis.com/v1/{us_central_eg}/entryLinks/{link_id}", headers)
            api_call(
                "POST",
                f"https://dataplex.googleapis.com/v1/{us_central_eg}/entryLinks?entryLinkId={link_id}",
                headers,
                payload,
            )

    readable_lookml_joins = [
        ("bjoin-lkr-vw-to-exp", "lookml-view-beacon-county-readiness", "Schema.county_id", "lookml-explore-beacon-disaster-readiness", "Schema.county_id"),
        ("bjoin-lkr-plan-to-exp", "lookml-view-beacon-deployment-plan", "Schema.county_id", "lookml-explore-beacon-disaster-readiness", "Schema.county_id"),
        ("bjoin-lkr-macro-to-exp", "lookml-view-beacon-macro-timeline", "Schema.year", "lookml-explore-beacon-disaster-readiness", "Schema.county_id"),
        ("bjoin-lkr-fprog-to-exp", "lookml-view-beacon-federal-programs", "Schema.program_id", "lookml-explore-beacon-disaster-readiness", "Schema.county_id"),
        ("bjoin-lkr-exp-to-dash", "lookml-explore-beacon-disaster-readiness", "Schema.county_id", "looker-beacon-executive-dashboard", "Schema.county_id"),
        ("bjoin-lkr-exp-to-app", "lookml-explore-beacon-disaster-readiness", "Schema.county_id", "governed-looker-beacon-data-app", "Schema.county_id"),
    ]
    for j_id, s_ent, s_col, t_ent, t_col in readable_lookml_joins:
        j_payload = {
            "entryLinkType": "projects/655216118709/locations/global/entryLinkTypes/schema-join",
            "entryReferences": [
                {"name": f"{us_central_eg}/entries/{s_ent}", "path": s_col, "type": ""},
                {"name": f"{us_central_eg}/entries/{t_ent}", "path": t_col, "type": ""},
            ],
        }
        st_jl, _ = api_call(
            "POST",
            f"https://dataplex.googleapis.com/v1/{us_central_eg}/entryLinks?entryLinkId={j_id}",
            headers,
            j_payload,
        )
        if st_jl == 409:
            api_call("DELETE", f"https://dataplex.googleapis.com/v1/{us_central_eg}/entryLinks/{j_id}", headers)
            api_call(
                "POST",
                f"https://dataplex.googleapis.com/v1/{us_central_eg}/entryLinks?entryLinkId={j_id}",
                headers,
                j_payload,
            )

    # D. Register Clean, Cycle-Free, Layered End-to-End Data Lineage in `datalineage.googleapis.com`
    print("   Registering Clean Left-to-Right Layered Data Lineage (Human-Readable LookML Views -> Unified Explore -> Named Looker Tiles -> Executive Dashboard & Data App -> Spanner DeploymentPlan) ...")

    def ref(fqn: str, field: str | None = None) -> dict[str, Any]:
        r: dict[str, Any] = {"fullyQualifiedName": fqn}
        if field:
            r["field"] = [field]
        return r

    def link(src_fqn: str, tgt_fqn: str, src_field: str | None = None, tgt_field: str | None = None) -> dict[str, Any]:
        return {
            "source": ref(src_fqn, src_field),
            "target": ref(tgt_fqn, tgt_field),
        }

    lineage_processes = [
        {
            "displayName": "Stage 1A. North America Data Commons Ingestion: Google_Data_Commons_USA to Cloud Spanner",
            "originName": "beacon-datacommons-spanner-ingestion",
            "attributes": {
                "pipeline_stage": "STAGE_1A_PUBLIC_DATA_COMMONS_INGESTION",
                "source_system": "Google Data Commons (U.S. Census ACS 5-Year, FEMA NRI, NOAA NCEI, BEA)",
                "target_system": "Cloud Spanner (readiness_dcgraph)",
                "steward": "Sean Zinsmeister (demo-operator@example.com) & U.S. Census Bureau / FEMA NRI",
            },
            "runDisplayName": "Ingest 3144 US Counties + 51 States + 13 Data Commons StatisticalVariables into Spanner",
            "links": [
                link(FQN_DC_USA, FQN_OBS),
                link(FQN_DC_USA, FQN_NODE),
                link(FQN_DC_USA, FQN_EDGE),
                link(FQN_DC_USA, FQN_STATE),
                link(FQN_DC_USA, FQN_MACRO),
                link(FQN_DC_USA, FQN_OBS, "dcid", "observation_about"),
                link(FQN_DC_USA, FQN_OBS, "variable_measured", "variable_measured"),
                link(FQN_DC_USA, FQN_OBS, "observation_date", "observation_date"),
                link(FQN_DC_USA, FQN_OBS, "value", "value"),
                link(FQN_DC_USA, FQN_NODE, "dcid", "subject_id"),
                link(FQN_DC_USA, FQN_STATE, "dcid", "state_id"),
                link(FQN_DC_USA, FQN_STATE, "Count_Person", "population"),
                link(FQN_DC_USA, FQN_STATE, "Count_Household_NoInternetAccess", "no_internet_pct"),
                link(FQN_DC_USA, FQN_STATE, "Count_Person_65OrMoreYears", "age_65_plus_pct"),
                link(FQN_DC_USA, FQN_STATE, "Count_Person_WithDisability", "disability_pct"),
                link(FQN_DC_USA, FQN_STATE, "Count_Person_BelowPovertyLevelInThePast12Months", "poverty_pct"),
                link(FQN_DC_USA, FQN_MACRO, "observation_date", "year"),
                link(FQN_DC_USA, FQN_MACRO, "Count_Person", "us_population"),
                link(FQN_DC_USA, FQN_MACRO, "Count_Person_65OrMoreYears", "seniors_65_plus_pct"),
                link(FQN_DC_USA, FQN_MACRO, "Median_Income_Household", "median_household_income_usd"),
                link(FQN_DC_USA, FQN_MACRO, "Count_Person_BelowPovertyLevelInThePast12Months", "poverty_rate_pct"),
                link(FQN_DC_USA, FQN_MACRO, "Count_Household_NoInternetAccess", "no_internet_households_pct"),
                link(FQN_DC_USA, FQN_MACRO, "FemaExpectedAnnualLoss_NaturalHazardImpact", "billion_dollar_disasters_loss_usd_b"),
            ],
        },
        {
            "displayName": "Stage 1B. US Federal Disaster Operations Sync: US_Federal_Disaster_Operations to Cloud Spanner",
            "originName": "beacon-openfema-federal-telemetry-sync",
            "attributes": {
                "pipeline_stage": "STAGE_1B_OPENFEMA_AND_BEACON_FLEET_SYNC",
                "source_system": "OpenFEMA API v2 (Declarations & Registrations) + Beacon Mobile DRC Fleet",
                "target_system": "Cloud Spanner (readiness_dcgraph)",
                "fedramp_tier": "FedRAMP High · CUI",
            },
            "runDisplayName": "Sync 263 OpenFEMA Major Disasters + 5.3M Registrations + 46 Beacon Mobile Teams into Spanner",
            "links": [
                link(FQN_FEDERAL_OPS, FQN_NODE),
                link(FQN_FEDERAL_OPS, FQN_EDGE),
                link(FQN_FEDERAL_OPS, FQN_DDES),
                link(FQN_FEDERAL_OPS, FQN_REG),
                link(FQN_FEDERAL_OPS, FQN_FPROG),
                link(FQN_FEDERAL_OPS, FQN_NODE, "disaster_id", "subject_id"),
                link(FQN_FEDERAL_OPS, FQN_NODE, "incident_type", "incident_type"),
                link(FQN_FEDERAL_OPS, FQN_NODE, "declaration_date", "declaration_date"),
                link(FQN_FEDERAL_OPS, FQN_EDGE, "assigned_team_id", "subject_id"),
                link(FQN_FEDERAL_OPS, FQN_EDGE, "county_id", "object_id"),
                link(FQN_FEDERAL_OPS, FQN_DDES, "disaster_id", "disaster_id"),
                link(FQN_FEDERAL_OPS, FQN_DDES, "county_id", "county_id"),
                link(FQN_FEDERAL_OPS, FQN_DDES, "ihp_declared", "ihp_declared"),
                link(FQN_FEDERAL_OPS, FQN_DDES, "declaration_date", "declaration_date"),
                link(FQN_FEDERAL_OPS, FQN_DDES, "incident_type", "incident_type"),
                link(FQN_FEDERAL_OPS, FQN_REG, "disaster_id", "disaster_id"),
                link(FQN_FEDERAL_OPS, FQN_REG, "county_id", "county_id"),
                link(FQN_FEDERAL_OPS, FQN_REG, "total_valid_registrations", "total_valid_registrations"),
                link(FQN_FEDERAL_OPS, FQN_REG, "web_registrations", "web_registrations"),
                link(FQN_FEDERAL_OPS, FQN_REG, "call_center_registrations", "call_center_registrations"),
                link(FQN_FEDERAL_OPS, FQN_REG, "mobile_registrations", "mobile_registrations"),
                link(FQN_FEDERAL_OPS, FQN_REG, "web_share_pct", "web_share_pct"),
            ],
        },
        {
            "displayName": "Stage 2. Cloud Spanner ISO GQL Property Graph Projection: Node + Edge to DCGraph",
            "originName": "beacon-spanner-graph-gql-engine",
            "attributes": {
                "pipeline_stage": "STAGE_2_SPANNER_PROPERTY_GRAPH_DDL",
                "graph_name": "DCGraph",
                "query_standard": "ISO/IEC 39075 GQL",
            },
            "runDisplayName": "Project Interleaved Node & Edge Tables into ISO GQL Property Graph DCGraph",
            "links": [
                link(FQN_NODE, FQN_SPANNER_GRAPH),
                link(FQN_EDGE, FQN_SPANNER_GRAPH),
                link(FQN_NODE, FQN_DSUM),
                link(FQN_DDES, FQN_DSUM),
                link(FQN_REG, FQN_DSUM),
                link(FQN_NODE, FQN_DSUM, "subject_id", "disaster_id"),
                link(FQN_NODE, FQN_DSUM, "name", "disaster_number"),
                link(FQN_NODE, FQN_DSUM, "display_name", "title"),
                link(FQN_NODE, FQN_DSUM, "incident_type", "incident_type"),
                link(FQN_REG, FQN_DSUM, "total_valid_registrations", "total_registrations"),
                link(FQN_REG, FQN_DSUM, "web_share_pct", "web_share_pct"),
            ],
        },
        {
            "displayName": "Stage 3. Data Commons + Spanner Graph 3144-County Profile Synthesis: CountyProfile",
            "originName": "beacon-county-profile-synthesis",
            "attributes": {
                "pipeline_stage": "STAGE_3_COUNTY_PROFILE_SYNTHESIS",
                "description": "Materializes 3,144 U.S. county demographic, broadband/vehicle access, and FEMA NRI profiles from Data Commons Observation & DCGraph Place Nodes.",
            },
            "runDisplayName": "Synthesize 3144 US County Profiles from Data Commons Observation & DCGraph Node Hierarchy",
            "links": [
                link(FQN_OBS, FQN_PROFILE),
                link(FQN_NODE, FQN_PROFILE),
                link(FQN_SPANNER_GRAPH, FQN_PROFILE),
                link(FQN_OBS, FQN_PROFILE, "observation_about", "county_id"),
                link(FQN_OBS, FQN_PROFILE, "value", "population"),
                link(FQN_OBS, FQN_PROFILE, "value", "households"),
                link(FQN_OBS, FQN_PROFILE, "value", "median_household_income_usd"),
                link(FQN_OBS, FQN_PROFILE, "value", "no_internet_households"),
                link(FQN_OBS, FQN_PROFILE, "value", "no_internet_pct"),
                link(FQN_OBS, FQN_PROFILE, "value", "no_vehicle_households"),
                link(FQN_OBS, FQN_PROFILE, "value", "no_vehicle_pct"),
                link(FQN_OBS, FQN_PROFILE, "value", "age_65_plus"),
                link(FQN_OBS, FQN_PROFILE, "value", "age_65_plus_pct"),
                link(FQN_OBS, FQN_PROFILE, "value", "disability_count"),
                link(FQN_OBS, FQN_PROFILE, "value", "disability_pct"),
                link(FQN_OBS, FQN_PROFILE, "value", "poverty_count"),
                link(FQN_OBS, FQN_PROFILE, "value", "poverty_pct"),
                link(FQN_OBS, FQN_PROFILE, "value", "nri_risk_score"),
                link(FQN_OBS, FQN_PROFILE, "value", "nri_social_vulnerability_score"),
                link(FQN_OBS, FQN_PROFILE, "value", "nri_community_resilience_score"),
                link(FQN_OBS, FQN_PROFILE, "value", "nri_expected_annual_loss_usd"),
                link(FQN_OBS, FQN_PROFILE, "value", "nri_flood_risk_score"),
                link(FQN_OBS, FQN_PROFILE, "value", "nri_hurricane_risk_score"),
                link(FQN_OBS, FQN_PROFILE, "value", "nri_wildfire_risk_score"),
                link(FQN_NODE, FQN_PROFILE, "subject_id", "county_id"),
                link(FQN_NODE, FQN_PROFILE, "display_name", "county_name"),
                link(FQN_NODE, FQN_PROFILE, "state_code", "state_code"),
            ],
        },
        {
            "displayName": "Stage 4A. Governed CountyReadiness View & Knowledge Catalog Synthesis: CountyReadiness",
            "originName": "beacon-county-readiness-kc-view-engine",
            "attributes": {
                "pipeline_stage": "STAGE_4A_GOVERNED_COUNTY_READINESS_VIEW",
                "glossary": GLOSSARY_ID,
                "aspect_type": ASPECT_TYPE_ID,
            },
            "runDisplayName": "Materialize CountyReadiness View Uniting CountyProfile + Registration + DCGraph + KnowledgeCatalogGovernance",
            "links": [
                link(FQN_PROFILE, FQN_READINESS),
                link(FQN_DDES, FQN_READINESS),
                link(FQN_REG, FQN_READINESS),
                link(FQN_EDGE, FQN_READINESS),
                link(FQN_NODE, FQN_READINESS),
                link(FQN_SPANNER_GRAPH, FQN_READINESS),
                link(FQN_KC_GOV, FQN_READINESS),
                link(FQN_PROFILE, FQN_READINESS, "county_id", "county_id"),
                link(FQN_PROFILE, FQN_READINESS, "county_name", "county_name"),
                link(FQN_PROFILE, FQN_READINESS, "state_name", "state_name"),
                link(FQN_PROFILE, FQN_READINESS, "state_code", "state_code"),
                link(FQN_PROFILE, FQN_READINESS, "population", "population"),
                link(FQN_PROFILE, FQN_READINESS, "households", "households"),
                link(FQN_PROFILE, FQN_READINESS, "median_household_income_usd", "median_household_income_usd"),
                link(FQN_PROFILE, FQN_READINESS, "no_internet_pct", "no_internet_pct"),
                link(FQN_PROFILE, FQN_READINESS, "no_vehicle_pct", "no_vehicle_pct"),
                link(FQN_PROFILE, FQN_READINESS, "age_65_plus_pct", "age_65_plus_pct"),
                link(FQN_PROFILE, FQN_READINESS, "disability_pct", "disability_pct"),
                link(FQN_PROFILE, FQN_READINESS, "poverty_pct", "poverty_pct"),
                link(FQN_PROFILE, FQN_READINESS, "nri_risk_score", "nri_risk_score"),
                link(FQN_PROFILE, FQN_READINESS, "nri_social_vulnerability_score", "social_vulnerability_score"),
                link(FQN_PROFILE, FQN_READINESS, "nri_community_resilience_score", "community_resilience_score"),
                link(FQN_PROFILE, FQN_READINESS, "nri_flood_risk_score", "flood_risk_score"),
                link(FQN_PROFILE, FQN_READINESS, "nri_hurricane_risk_score", "hurricane_risk_score"),
                link(FQN_PROFILE, FQN_READINESS, "nri_wildfire_risk_score", "wildfire_risk_score"),
                link(FQN_PROFILE, FQN_READINESS, "gmap_hybrid_uri", "gmap_hybrid_uri"),
                link(FQN_PROFILE, FQN_READINESS, "gmap_terrain_uri", "gmap_terrain_uri"),
                link(FQN_NODE, FQN_READINESS, "latitude", "latitude"),
                link(FQN_NODE, FQN_READINESS, "longitude", "longitude"),
                link(FQN_DDES, FQN_READINESS, "disaster_id", "disasters_since_2023"),
                link(FQN_DDES, FQN_READINESS, "ihp_declared", "ihp_disasters_since_2023"),
                link(FQN_REG, FQN_READINESS, "total_valid_registrations", "total_registrations"),
                link(FQN_REG, FQN_READINESS, "web_share_pct", "web_registration_pct"),
                link(FQN_REG, FQN_READINESS, "call_center_share_pct", "call_center_registration_pct"),
                link(FQN_EDGE, FQN_READINESS, "predicate", "has_team_coverage"),
                link(FQN_EDGE, FQN_READINESS, "subject_id", "assigned_team_count"),
                link(FQN_KC_GOV, FQN_READINESS, "policy_threshold", "social_vulnerability_score"),
                link(FQN_KC_GOV, FQN_READINESS, "policy_threshold", "no_internet_pct"),
                link(FQN_KC_GOV, FQN_READINESS, "policy_threshold", "no_vehicle_pct"),
                link(FQN_KC_GOV, FQN_READINESS, "policy_threshold", "nri_risk_score"),
                link(FQN_KC_GOV, FQN_READINESS, "policy_threshold", "has_team_coverage"),
            ],
        },
        {
            "displayName": "Stage 4B. Google Cloud Borderless Lakehouse & Governed LookML Semantic Layer: Spanner + BigLake Iceberg + Object Tables to LookML Explore",
            "originName": "beacon-lookml-semantic-layer-compiler",
            "attributes": {
                "pipeline_stage": "STAGE_4B_BORDERLESS_LAKEHOUSE_AND_LOOKML_SEMANTIC_LAYER",
                "borderless_lakehouse": "BigLake Apache Iceberg (noaa_hazard_iceberg, fema_field_assessments_iceberg) + Object Table (fema_field_sitrep_objects) + Spanner Graph (readiness_dcgraph)",
                "looker_instance": "cloud-bi-opm (us-east1)",
                "lookml_views": "LookML_View_County_Readiness + LookML_View_Deployment_Plan + LookML_View_Macro_Timeline + LookML_View_Federal_Programs",
                "lookml_explore": "LookML_Explore_Beacon_Readiness (beacon_county_readiness)",
                "steward": "Sean Zinsmeister (demo-operator@example.com)",
            },
            "runDisplayName": "Federate Spanner Graph + BigLake Apache Iceberg + Unstructured SitRep PDFs into Borderless_Lakehouse_Beacon_Readiness & LookML_Explore_Beacon_Readiness",
            "links": [
                # Step 1: Spanner Tables -> Human-Readable LookML Views & BigQuery Analytical Serving Table (clean 3 outgoing links on CountyReadiness!)
                link(FQN_READINESS, FQN_LOOKML_VIEW_READINESS),
                link(FQN_READINESS, FQN_BQ_READINESS),
                link(FQN_FEDERAL_OPS, FQN_LOOKML_VIEW_PLAN),
                link(FQN_MACRO, FQN_LOOKML_VIEW_MACRO),
                link(FQN_FPROG, FQN_LOOKML_VIEW_FPROG),
                # Step 1B: Borderless Lakehouse Federation in BigQuery (`DCGraph` + `county_readiness` + `noaa_hazard_iceberg` + `fema_field_assessments_iceberg` + `fema_field_sitrep_objects` -> `v_borderless_lakehouse_dispatch` -> `Borderless_Lakehouse_Beacon_Readiness`)
                link(FQN_SPANNER_GRAPH, FQN_BQ_GRAPH),
                link(FQN_BQ_READINESS, FQN_BQ_VIEW_DISPATCH),
                link(FQN_BQ_ICEBERG_NOAA, FQN_BQ_VIEW_DISPATCH),
                link(FQN_BQ_ICEBERG_FEMA, FQN_BQ_VIEW_DISPATCH),
                link(FQN_BQ_OBJ_SITREP, FQN_BQ_VIEW_DISPATCH),
                link(FQN_BQ_VIEW_DISPATCH, FQN_BQ_GRAPH),
                link(FQN_BQ_VIEW_DISPATCH, FQN_LOOKML_EXPLORE_READINESS),
                link(FQN_BQ_READINESS, FQN_BQ_GRAPH),
                link(FQN_BQ_ICEBERG_NOAA, FQN_BQ_GRAPH),
                link(FQN_BQ_ICEBERG_FEMA, FQN_BQ_GRAPH),
                link(FQN_BQ_OBJ_SITREP, FQN_BQ_GRAPH),
                link(FQN_BQ_NODE, FQN_BQ_GRAPH),
                link(FQN_BQ_EDGE, FQN_BQ_GRAPH),
                link(FQN_BQ_READINESS, FQN_LOOKML_VIEW_READINESS),
                # Step 2: The 4 LookML Views + Borderless Lakehouse -> Unified LookML Explore (`LookML_Explore_Beacon_Readiness`)
                link(FQN_LOOKML_VIEW_READINESS, FQN_LOOKML_EXPLORE_READINESS),
                link(FQN_LOOKML_VIEW_PLAN, FQN_LOOKML_EXPLORE_READINESS),
                link(FQN_LOOKML_VIEW_MACRO, FQN_LOOKML_EXPLORE_READINESS),
                link(FQN_LOOKML_VIEW_FPROG, FQN_LOOKML_EXPLORE_READINESS),
                link(FQN_BQ_GRAPH, FQN_LOOKML_EXPLORE_READINESS),
                # Also link native `@looker` view -> native `@looker` explore for direct us-east1 inspection
                link(FQN_NATIVE_LOOKML_VIEW_READINESS, FQN_NATIVE_LOOKML_EXPLORE_READINESS),
                # Column-level links: Spanner `CountyReadiness` -> BigQuery `county_readiness` -> `BigQuery_Graph_Beacon_Readiness`
                link(FQN_READINESS, FQN_BQ_READINESS, "county_id", "county_id"),
                link(FQN_READINESS, FQN_BQ_READINESS, "county_name", "county_name"),
                link(FQN_READINESS, FQN_BQ_READINESS, "state_code", "state_code"),
                link(FQN_READINESS, FQN_BQ_READINESS, "social_vulnerability_score", "social_vulnerability_score"),
                link(FQN_READINESS, FQN_BQ_READINESS, "no_internet_pct", "no_internet_pct"),
                link(FQN_READINESS, FQN_BQ_READINESS, "poverty_pct", "poverty_pct"),
                link(FQN_READINESS, FQN_BQ_READINESS, "has_team_coverage", "has_team_coverage"),
                link(FQN_BQ_READINESS, FQN_BQ_GRAPH, "county_id", "county_id"),
                link(FQN_BQ_READINESS, FQN_BQ_GRAPH, "social_vulnerability_score", "social_vulnerability_score"),
                link(FQN_BQ_READINESS, FQN_BQ_GRAPH, "no_internet_pct", "no_internet_pct"),
                link(FQN_BQ_READINESS, FQN_BQ_GRAPH, "has_team_coverage", "has_team_coverage"),
                # Column-level links: Spanner `CountyReadiness` -> `LookML_View_County_Readiness`
                link(FQN_READINESS, FQN_LOOKML_VIEW_READINESS, "county_id", "county_id"),
                link(FQN_READINESS, FQN_LOOKML_VIEW_READINESS, "county_name", "county_name"),
                link(FQN_READINESS, FQN_LOOKML_VIEW_READINESS, "state_code", "state_code"),
                link(FQN_READINESS, FQN_LOOKML_VIEW_READINESS, "social_vulnerability_score", "social_vulnerability_score"),
                link(FQN_READINESS, FQN_LOOKML_VIEW_READINESS, "no_internet_pct", "no_internet_pct"),
                link(FQN_READINESS, FQN_LOOKML_VIEW_READINESS, "no_vehicle_pct", "no_vehicle_pct"),
                link(FQN_READINESS, FQN_LOOKML_VIEW_READINESS, "nri_risk_score", "nri_risk_score"),
                link(FQN_READINESS, FQN_LOOKML_VIEW_READINESS, "community_resilience_score", "community_resilience_score"),
                link(FQN_READINESS, FQN_LOOKML_VIEW_READINESS, "poverty_pct", "poverty_pct"),
                link(FQN_READINESS, FQN_LOOKML_VIEW_READINESS, "age_65_plus_pct", "age_65_plus_pct"),
                link(FQN_READINESS, FQN_LOOKML_VIEW_READINESS, "disability_pct", "disability_pct"),
                link(FQN_READINESS, FQN_LOOKML_VIEW_READINESS, "web_registration_pct", "web_registration_pct"),
                link(FQN_READINESS, FQN_LOOKML_VIEW_READINESS, "has_team_coverage", "has_team_coverage"),
                # Column-level links: `LookML_View_County_Readiness` & `LookML_View_Deployment_Plan` -> `LookML_Explore_Beacon_Readiness`
                link(FQN_LOOKML_VIEW_READINESS, FQN_LOOKML_EXPLORE_READINESS, "county_id", "county_id"),
                link(FQN_LOOKML_VIEW_READINESS, FQN_LOOKML_EXPLORE_READINESS, "county_name", "county_name"),
                link(FQN_LOOKML_VIEW_READINESS, FQN_LOOKML_EXPLORE_READINESS, "state_code", "state_code"),
                link(FQN_LOOKML_VIEW_READINESS, FQN_LOOKML_EXPLORE_READINESS, "social_vulnerability_score", "social_vulnerability_score"),
                link(FQN_LOOKML_VIEW_READINESS, FQN_LOOKML_EXPLORE_READINESS, "no_internet_pct", "no_internet_pct"),
                link(FQN_LOOKML_VIEW_READINESS, FQN_LOOKML_EXPLORE_READINESS, "no_vehicle_pct", "no_vehicle_pct"),
                link(FQN_LOOKML_VIEW_READINESS, FQN_LOOKML_EXPLORE_READINESS, "nri_risk_score", "nri_risk_score"),
                link(FQN_LOOKML_VIEW_READINESS, FQN_LOOKML_EXPLORE_READINESS, "community_resilience_score", "community_resilience_score"),
                link(FQN_LOOKML_VIEW_READINESS, FQN_LOOKML_EXPLORE_READINESS, "web_registration_pct", "web_registration_pct"),
                link(FQN_LOOKML_VIEW_READINESS, FQN_LOOKML_EXPLORE_READINESS, "has_team_coverage", "has_team_coverage"),
                link(FQN_LOOKML_VIEW_PLAN, FQN_LOOKML_EXPLORE_READINESS, "priority_tier", "priority_tier"),
                link(FQN_LOOKML_VIEW_PLAN, FQN_LOOKML_EXPLORE_READINESS, "action", "action"),
            ],
        },
        {
            "displayName": "Stage 5. Agentic Data Cloud Consumption: Named Looker Tiles + Executive Dashboard + Grant Simulator App + Gemini Conversational Analytics",
            "originName": "beacon-agentic-data-cloud-ge-looker-actions",
            "attributes": {
                "pipeline_stage": "STAGE_5_AGENTIC_DATA_CLOUD_SEE_SHOW_DO",
                "looker_executive_dashboard": "Looker_Beacon_Executive_Dashboard (Old Glory Blue #3C3B6E)",
                "looker_dashboard_tiles": "Tile_Top_10_Unserved_Counties + Tile_Digital_Divide_vs_Web_Intake + Tile_FEMA_State_Channel_Mix + Tile_Billion_Dollar_Disaster_Losses + Tile_Spanner_Mobile_DRC_Action_Grid",
                "conversational_surface": "Gemini_Enterprise_Beacon_Agent (14131532519214632868)",
                "interactive_app_surface": "Looker_Beacon_Grant_Simulator_App (274)",
                "writeback_table": "Cloud Spanner DeploymentPlan",
            },
            "runDisplayName": "Serve Named Looker Tiles to Looker_Beacon_Executive_Dashboard + Looker_Beacon_Grant_Simulator_App + Gemini_Enterprise_Beacon_Agent to Spanner DeploymentPlan",
            "links": [
                # Step 3: Unified LookML Explore -> 5 Easy-to-Identify Looker Visualization Tiles + Governed Looker Grant Simulator App
                *[link(FQN_LOOKML_EXPLORE_READINESS, tile_fqn) for tile_fqn in FQN_NAMED_LOOKER_TILES],
                link(FQN_LOOKML_EXPLORE_READINESS, FQN_LOOKER_APP),
                # Also connect the native `@looker` Explore in us-east1 to the 5 Named Looker Tiles & Grant Simulator App
                *[link(FQN_NATIVE_LOOKML_EXPLORE_READINESS, tile_fqn) for tile_fqn in FQN_NAMED_LOOKER_TILES],
                link(FQN_NATIVE_LOOKML_EXPLORE_READINESS, FQN_LOOKER_APP),
                # Step 4: The 5 Named Looker Visualization Tiles -> Looker_Beacon_Executive_Dashboard (zero cycles!)
                *[link(tile_fqn, FQN_LOOKER_DASHBOARD_519) for tile_fqn in FQN_NAMED_LOOKER_TILES],
                # Step 5: Conversational AI Agent (`Gemini_Enterprise_Beacon_Agent`) fed by `CountyReadiness`, `DCGraph` (Spanner), `BigQuery_Graph_Beacon_Readiness` (BigQuery), `v_borderless_lakehouse_dispatch`, and `KnowledgeCatalogGovernance`
                link(FQN_READINESS, FQN_GE_AGENT),
                link(FQN_SPANNER_GRAPH, FQN_GE_AGENT),
                link(FQN_BQ_GRAPH, FQN_GE_AGENT),
                link(FQN_BQ_VIEW_DISPATCH, FQN_GE_AGENT),
                link(FQN_BQ_READINESS, FQN_GE_AGENT),
                link(FQN_KC_GOV, FQN_GE_AGENT),
                link(FQN_DSUM, FQN_GE_AGENT),
                link(FQN_MACRO, FQN_GE_AGENT),
                link(FQN_FPROG, FQN_GE_AGENT),
                # Step 6: Closed-Loop System of Action Write-Back to Cloud Spanner `DeploymentPlan` and BigQuery `deployment_plan`
                link(FQN_LOOKER_DASHBOARD_519, FQN_PLAN),
                link(FQN_LOOKER_APP, FQN_PLAN),
                link(FQN_GE_AGENT, FQN_PLAN),
                link(FQN_LOOKER_DASHBOARD_519, FQN_BQ_PLAN),
                link(FQN_LOOKER_APP, FQN_BQ_PLAN),
                link(FQN_GE_AGENT, FQN_BQ_PLAN),
                # Column-level links -> Named Looker Tiles & `Looker_Beacon_Executive_Dashboard`
                link(FQN_LOOKML_EXPLORE_READINESS, FQN_TILE_UNSERVED, "county_name", "county_name"),
                link(FQN_LOOKML_EXPLORE_READINESS, FQN_TILE_UNSERVED, "social_vulnerability_score", "social_vulnerability_score"),
                link(FQN_LOOKML_EXPLORE_READINESS, FQN_TILE_UNSERVED, "has_team_coverage", "has_team_coverage"),
                link(FQN_LOOKML_EXPLORE_READINESS, FQN_TILE_SCATTER, "no_internet_pct", "no_internet_pct"),
                link(FQN_LOOKML_EXPLORE_READINESS, FQN_TILE_SCATTER, "web_registration_pct", "web_registration_pct"),
                link(FQN_LOOKML_EXPLORE_READINESS, FQN_TILE_ACTION, "priority_tier", "priority_tier"),
                link(FQN_LOOKML_EXPLORE_READINESS, FQN_TILE_ACTION, "action", "action"),
                link(FQN_TILE_UNSERVED, FQN_LOOKER_DASHBOARD_519, "social_vulnerability_score", "social_vulnerability_score"),
                link(FQN_TILE_SCATTER, FQN_LOOKER_DASHBOARD_519, "no_internet_pct", "no_internet_pct"),
                link(FQN_TILE_SCATTER, FQN_LOOKER_DASHBOARD_519, "web_registration_pct", "web_registration_pct"),
                # Column-level links -> `Looker_Beacon_Grant_Simulator_App`
                link(FQN_LOOKML_EXPLORE_READINESS, FQN_LOOKER_APP, "county_id", "county_id"),
                link(FQN_LOOKML_EXPLORE_READINESS, FQN_LOOKER_APP, "county_name", "county_name"),
                link(FQN_LOOKML_EXPLORE_READINESS, FQN_LOOKER_APP, "social_vulnerability_score", "social_vulnerability_score"),
                link(FQN_LOOKML_EXPLORE_READINESS, FQN_LOOKER_APP, "no_internet_pct", "no_internet_pct"),
                link(FQN_LOOKML_EXPLORE_READINESS, FQN_LOOKER_APP, "no_vehicle_pct", "no_vehicle_pct"),
                # Column-level links -> `Gemini_Enterprise_Beacon_Agent`
                link(FQN_READINESS, FQN_GE_AGENT, "county_id", "county_id"),
                link(FQN_READINESS, FQN_GE_AGENT, "county_name", "county_name"),
                link(FQN_READINESS, FQN_GE_AGENT, "social_vulnerability_score", "social_vulnerability_score"),
                link(FQN_READINESS, FQN_GE_AGENT, "no_internet_pct", "no_internet_pct"),
                link(FQN_READINESS, FQN_GE_AGENT, "no_vehicle_pct", "no_vehicle_pct"),
                link(FQN_READINESS, FQN_GE_AGENT, "nri_risk_score", "nri_risk_score"),
                link(FQN_READINESS, FQN_GE_AGENT, "web_registration_pct", "web_registration_pct"),
                link(FQN_READINESS, FQN_GE_AGENT, "has_team_coverage", "has_team_coverage"),
                link(FQN_KC_GOV, FQN_GE_AGENT, "rule_id", "rule_id"),
                link(FQN_KC_GOV, FQN_GE_AGENT, "policy_threshold", "policy_threshold"),
                # Column-level links -> `DeploymentPlan` (Closed-Loop Action Write-Back)
                link(FQN_LOOKER_DASHBOARD_519, FQN_PLAN, "county_id", "county_id"),
                link(FQN_LOOKER_DASHBOARD_519, FQN_PLAN, "social_vulnerability_score", "priority_tier"),
                link(FQN_LOOKER_APP, FQN_PLAN, "looker_action_dispatch_status", "status"),
                link(FQN_LOOKER_APP, FQN_PLAN, "simulated_mdrc_units_added", "assigned_team_id"),
                link(FQN_GE_AGENT, FQN_PLAN, "recommended_action", "action"),
            ],
        },
    ]

    beacon_origins = {p["originName"] for p in lineage_processes}
    total_processes = 0
    total_links = sum(len(p["links"]) for p in lineage_processes)

    for clean_loc in ["global", "us", "us-central1", "us-east1"]:
        # Clean up any prior Beacon processes AND any Looker Core numeric `/dashboards/519` processes
        page_token = ""
        while True:
            url = f"https://datalineage.googleapis.com/v1/projects/{PROJECT_NUM}/locations/{clean_loc}/processes?pageSize=100"
            if page_token:
                url += f"&pageToken={page_token}"
            st_lp, existing_procs = api_call("GET", url, headers)
            if st_lp == 200 and isinstance(existing_procs, dict):
                for ep in existing_procs.get("processes", []):
                    ep_name = ep.get("name", "")
                    ep_origin = ep.get("origin", {}).get("name", "")
                    ep_dn = str(ep.get("displayName", ""))
                    if ep_name and (
                        ep_origin in beacon_origins
                        or ep_origin.startswith("beacon-")
                        or "/dashboards/519" in ep_origin
                        or ep_dn.startswith("Stage ")
                        or "519" in ep_dn
                    ):
                        api_call("DELETE", f"https://datalineage.googleapis.com/v1/{ep_name}?allowMissing=true", headers)
                page_token = existing_procs.get("nextPageToken", "")
                if not page_token:
                    break
            else:
                break

    for lin_loc in ["us-central1", "us", "us-east1"]:

        for idx, proc_spec in enumerate(lineage_processes, start=1):
            st_pr, proc_res = api_call(
                "POST",
                f"https://datalineage.googleapis.com/v1/projects/{PROJECT_NUM}/locations/{lin_loc}/processes",
                headers,
                {
                    "displayName": proc_spec["displayName"],
                    "attributes": proc_spec["attributes"],
                    "origin": {
                        "sourceType": "CUSTOM",
                        "name": proc_spec["originName"],
                    },
                },
            )
            if st_pr != 200 or not isinstance(proc_res, dict):
                print(f"   [Warn] Failed creating process {proc_spec['displayName']} in {lin_loc}: {st_pr} {proc_res}")
                continue
            proc_name = proc_res["name"]
            start_ts = f"2026-09-28T01:0{idx}:00Z"
            end_ts = f"2026-09-28T01:0{idx}:05Z"
            st_rn, run_res = api_call(
                "POST",
                f"https://datalineage.googleapis.com/v1/{proc_name}/runs",
                headers,
                {
                    "displayName": proc_spec["runDisplayName"],
                    "startTime": start_ts,
                    "endTime": end_ts,
                    "state": "COMPLETED",
                },
            )
            if st_rn != 200 or not isinstance(run_res, dict):
                print(f"   [Warn] Failed creating run in {lin_loc}: {st_rn} {run_res}")
                continue
            run_name = run_res["name"]
            st_ev, ev_res = api_call(
                "POST",
                f"https://datalineage.googleapis.com/v1/{run_name}/lineageEvents",
                headers,
                {
                    "startTime": start_ts,
                    "endTime": end_ts,
                    "links": proc_spec["links"],
                },
            )
            if st_ev != 200:
                print(f"   [Warn] Failed creating lineageEvent for {proc_spec['displayName']} in {lin_loc}: {st_ev} {ev_res}")
            if lin_loc == LOCATION and st_ev == 200:
                total_processes += 1
            print(f"   [{lin_loc}] Registered `{proc_spec['displayName']}` ({len(proc_spec['links'])} table+column links) -> {st_ev}")

    return total_processes, total_links


# =============================================================================
# 7. Verify `lookupContext`, Glossary, Entries, EntryLinks & Data Lineage
# =============================================================================

def verify_all(headers: dict[str, str]) -> None:
    print("7. Verifying `lookupContext` LLM-ready bundle & HTTP 200 OK across `@spanner`, `@looker`, and `@bigquery` resources ...")
    resources = [
        f"{SPANNER_ENTRY_PREFIX}/tables/CountyReadiness",
        f"{SPANNER_ENTRY_PREFIX}/tables/CountyProfile",
        f"{SPANNER_ENTRY_PREFIX}/tables/StateProfile",
        f"{SPANNER_ENTRY_PREFIX}/tables/DisasterSummary",
        f"{SPANNER_ENTRY_PREFIX}/tables/DisasterDesignation",
        f"{SPANNER_ENTRY_PREFIX}/tables/Registration",
        f"{SPANNER_ENTRY_PREFIX}/tables/DeploymentPlan",
        f"{SPANNER_ENTRY_PREFIX}/tables/NationalMacroTimeline",
        f"{SPANNER_ENTRY_PREFIX}/tables/FederalProgramSummary",
        f"{SPANNER_ENTRY_PREFIX}/graphs/DCGraph",
    ]
    st, res = api_call(
        "POST",
        f"https://dataplex.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}:lookupContext",
        headers,
        {"resources": resources, "options": {"all_schema_fields": "true"}},
    )
    print(f"   `lookupContext` (@spanner) status: {st}")
    if st == 200 and isinstance(res, dict) and "context" in res:
        ctx_yaml = res["context"]
        out_path = "beacon_knowledge_catalog_context_bundle.yaml"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(ctx_yaml)
        print(f"   Saved verified Beacon Knowledge Catalog context bundle ({len(ctx_yaml)} bytes) to {out_path}")

    # Verify Glossary, CountyReadiness, DCGraph, Native `@looker` View/Explore/Dashboard 519, and Lineage searchLinks
    g_url = f"https://dataplex.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/glossaries/{GLOSSARY_ID}"
    st_g, g_data = api_call("GET", g_url, headers)
    print(f"   Glossary `{GLOSSARY_ID}` GET status: {st_g} (terms={g_data.get('termCount')}, categories={g_data.get('categoryCount')})")

    cr_url = f"https://dataplex.googleapis.com/v1/{SPANNER_ENTRY_PREFIX}/tables/CountyReadiness?view=ALL"
    st_cr, cr_data = api_call("GET", cr_url, headers)
    print(f"   `@spanner` `CountyReadiness` GET status: {st_cr} (aspects={len(cr_data.get('aspects', {}))})")

    lkr_vw_url = f"https://dataplex.googleapis.com/v1/{LOOKML_MODEL_PREFIX}/views/beacon_county_readiness?view=ALL"
    st_vw, vw_data = api_call("GET", lkr_vw_url, headers)
    print(f"   `@looker` LookML View `beacon_county_readiness` GET status: {st_vw} (aspects={len(vw_data.get('aspects', {}))})")

    lkr_ex_url = f"https://dataplex.googleapis.com/v1/{LOOKML_MODEL_PREFIX}/explores/beacon_county_readiness?view=ALL"
    st_ex, ex_data = api_call("GET", lkr_ex_url, headers)
    print(f"   `@looker` LookML Explore `beacon_county_readiness` GET status: {st_ex} (aspects={len(ex_data.get('aspects', {}))})")

    lkr_dash_url = f"https://dataplex.googleapis.com/v1/{LOOKER_ENTRY_PREFIX}/dashboards/519?view=ALL"
    st_dash, dash_data = api_call("GET", lkr_dash_url, headers)
    print(f"   `@looker` Looker Dashboard `519` GET status: {st_dash} (aspects={len(dash_data.get('aspects', {}))})")

    time.sleep(6)
    st_lin_in, lin_in = api_call(
        "POST",
        f"https://datalineage.googleapis.com/v1/projects/{PROJECT_NUM}/locations/{LOCATION}:searchLinks",
        headers,
        {"target": {"fullyQualifiedName": FQN_READINESS}},
    )
    st_lin_out, lin_out = api_call(
        "POST",
        f"https://datalineage.googleapis.com/v1/projects/{PROJECT_NUM}/locations/{LOCATION}:searchLinks",
        headers,
        {"source": {"fullyQualifiedName": FQN_READINESS}},
    )
    st_lin_lkr, lin_lkr = api_call(
        "POST",
        f"https://datalineage.googleapis.com/v1/projects/{PROJECT_NUM}/locations/us-east1:searchLinks",
        headers,
        {"source": {"fullyQualifiedName": FQN_LOOKML_EXPLORE_READINESS}},
    )
    in_links = len(lin_in.get("links", [])) if isinstance(lin_in, dict) else 0
    out_links = len(lin_out.get("links", [])) if isinstance(lin_out, dict) else 0
    lkr_links = len(lin_lkr.get("links", [])) if isinstance(lin_lkr, dict) else 0
    print(f"   `CountyReadiness` Lineage `searchLinks` status: upstream={st_lin_in} ({in_links} links), downstream={st_lin_out} ({out_links} links)")
    print(f"   `@looker` Explore `beacon_county_readiness` downstream `searchLinks` status: {st_lin_lkr} ({lkr_links} links -> Dashboard 519 & 13 tiles)")


def main() -> None:
    setup_spanner_governance_table()
    headers = get_headers()
    setup_glossaries_and_terms(headers)
    setup_aspect_types(headers)
    patched = enrich_spanner_entries(headers)
    lkr_patched, bq_patched = enrich_looker_and_bigquery_entries(headers)
    def_links, join_links = setup_entry_links(headers)
    procs, lin_links = setup_ecosystem_entries_and_lineage(headers)
    verify_all(headers)
    print(
        f"\n✅ Beacon Knowledge Catalog + Spanner Governance + Native @looker LookML & Dashboard 519 + 6-Stage Data Lineage setup complete! "
        f"(Patched {patched} @spanner entries, {lkr_patched} @looker entries, {bq_patched} @bigquery entries, "
        f"{def_links} definition EntryLinks, {join_links} schema-join EntryLinks, "
        f"{procs} Lineage Processes, {lin_links} table+column lineage links)"
    )


if __name__ == "__main__":
    main()
