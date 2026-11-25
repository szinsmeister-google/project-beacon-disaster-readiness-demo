"""Builds and populates the Google Cloud Borderless Lakehouse experience
in `your-gcp-project-id.beacon_disaster_readiness` (US multi-region):
  1. Creates/verifies GCS bucket `gs://beacon-borderless-lakehouse-123456789012` (location: US)
     and BigQuery Cloud Resource Connection `your-gcp-project-id.us.beacon_lakehouse_conn`.
  2. Generates and uploads 12 unstructured FEMA Field SitRep PDF files to
     `gs://beacon-borderless-lakehouse-123456789012/field_sitreps/` and creates the
     BigLake Object Table `beacon_disaster_readiness.fema_field_sitrep_objects`.
  3. Creates and populates two BigLake Managed Apache Iceberg tables (`table_format = 'ICEBERG'`):
     - `beacon_disaster_readiness.noaa_hazard_iceberg` (NOAA Multi-Cloud Open Iceberg Hazard & Outage Telemetry)
     - `beacon_disaster_readiness.fema_field_assessments_iceberg` (FEMA Preliminary Damage Assessments & Unstructured SitRep Index)
  4. Enriches `beacon_disaster_readiness.county_readiness` with Borderless Lakehouse columns
     (`active_hazard_alert`, `cell_tower_outage_pct`, `road_washout_status`, `sitrep_pdf_uri`)
     and creates the unified view `beacon_disaster_readiness.v_borderless_lakehouse_dispatch`.
"""

from __future__ import annotations

import json
import subprocess
import time
from google.cloud import bigquery
from google.cloud import storage

import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.gcp import env, get_project_id, get_project_number

PROJECT_ID = get_project_id()
PROJECT_NUM = get_project_number()
DATASET_ID = env("BQ_DATASET_ID", "beacon_disaster_readiness")
LOCATION = env("BQ_LOCATION", "US")
CONN_LOCATION = env("BQ_CONNECTION_LOCATION", "us")
CONN_ID = env("BQ_LAKEHOUSE_CONN", "beacon_lakehouse_conn")
BUCKET_NAME = env("GCS_LAKEHOUSE_BUCKET", f"{PROJECT_ID}-beacon-lakehouse")
import urllib.error
import urllib.request

GCLOUD = "gcloud"


def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("Running:", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.stdout.strip():
        print("  stdout:", res.stdout.strip()[:400])
    if res.stderr.strip():
        print("  stderr:", res.stderr.strip()[:400])
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed ({res.returncode}): {' '.join(cmd)}")
    return res


import textwrap


def make_minimal_pdf(title: str, lines: list[str]) -> bytes:
    """Generates a valid single-page PDF document containing the FEMA Field SitRep text."""
    text_ops = ["BT", "/F1 12 Tf", "45 745 Td", f"({title}) Tj", "0 -8 Td"]
    for line in lines:
        wrapped = textwrap.wrap(line, width=76, subsequent_indent="    ") or [""]
        for wline in wrapped:
            safe = wline.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            text_ops.append("0 -18 Td")
            text_ops.append(f"({safe}) Tj")
    text_ops.append("ET")
    stream_data = "\n".join(text_ops).encode("latin-1", errors="replace")

    objs: list[bytes] = []
    objs.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objs.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objs.append(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )
    objs.append(
        f"4 0 obj\n<< /Length {len(stream_data)} >>\nstream\n".encode("ascii")
        + stream_data
        + b"\nendstream\nendobj\n"
    )
    objs.append(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objs:
        offsets.append(len(out))
        out.extend(obj)
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    out.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
    )
    return bytes(out)


def ensure_bucket_and_connection() -> str:
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    if not bucket.exists():
        print(f"Creating GCS bucket gs://{BUCKET_NAME} in {LOCATION}...")
        bucket.storage_class = "STANDARD"
        storage_client.create_bucket(bucket, location=LOCATION)
    else:
        print(f"GCS bucket gs://{BUCKET_NAME} already exists.")

    token = subprocess.check_output([GCLOUD, "auth", "print-access-token"], text=True).strip()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": PROJECT_ID,
    }
    conn_url = f"https://bigqueryconnection.googleapis.com/v1/projects/{PROJECT_NUM}/locations/{CONN_LOCATION}/connections/{CONN_ID}"
    try:
        req = urllib.request.Request(conn_url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            conn_info = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Creating BigLake connection {CONN_ID} in {CONN_LOCATION}...")
            create_url = f"https://bigqueryconnection.googleapis.com/v1/projects/{PROJECT_NUM}/locations/{CONN_LOCATION}/connections?connectionId={CONN_ID}"
            body = json.dumps({"friendlyName": "Beacon Borderless Lakehouse Connection", "cloudResource": {}}).encode("utf-8")
            req_c = urllib.request.Request(create_url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req_c, timeout=30) as resp_c:
                conn_info = json.loads(resp_c.read().decode("utf-8"))
        else:
            raise

    sa_email = conn_info["cloudResource"]["serviceAccountId"]
    print(f"Connection Service Account: {sa_email}")

    # Grant storage.admin and storage.objectAdmin on the bucket to the connection SA
    run_cmd(
        [
            GCLOUD,
            "storage",
            "buckets",
            "add-iam-policy-binding",
            f"gs://{BUCKET_NAME}",
            f"--member=serviceAccount:{sa_email}",
            "--role=roles/storage.admin",
            f"--project={PROJECT_ID}",
        ]
    )
    run_cmd(
        [
            GCLOUD,
            "storage",
            "buckets",
            "add-iam-policy-binding",
            f"gs://{BUCKET_NAME}",
            f"--member=serviceAccount:{sa_email}",
            "--role=roles/storage.objectAdmin",
            f"--project={PROJECT_ID}",
        ]
    )
    return sa_email


SITREP_RECORDS = [
    {
        "county_id": "geoId/21159",
        "county_name": "Martin County, KY",
        "state_code": "KY",
        "pda_report_id": "FEMA-PDA-2026-KY-21159",
        "active_hazard_alert": "Flash Flood & Mudslide Emergency",
        "peak_wind_mph": 64.0,
        "storm_surge_ft": 0.0,
        "power_grid_outage_pct": 48.5,
        "cell_tower_outage_pct": 62.0,
        "road_washout_status": "KY-40 & Tug Fork Bridges Washed Out (SatCom Required)",
        "bridge_closures_count": 7,
        "shelter_capacity_utilization_pct": 94.2,
        "field_sitrep_summary": "Tug Fork River flash flooding washed out 7 hollow bridges; 62% cell tower outage blocking online FEMA IHP intake. Immediate Mobile DRC & SatCom dispatch required.",
        "recommended_mobile_unit": "FEMA Mobile DRC Unit Southeast-Alpha",
        "regional_hub": "Southeast Regional Hub",
        "priority_tier": "Tier 1 - Immediate",
    },
    {
        "county_id": "geoId/01119",
        "county_name": "Sumter County, AL",
        "state_code": "AL",
        "pda_report_id": "FEMA-PDA-2026-AL-01119",
        "active_hazard_alert": "Severe Tornado & Tombigbee River Flood",
        "peak_wind_mph": 118.0,
        "storm_surge_ft": 0.0,
        "power_grid_outage_pct": 54.0,
        "cell_tower_outage_pct": 58.4,
        "road_washout_status": "US-11 & AL-28 Corridor Flooded (Mobile DRC Required)",
        "bridge_closures_count": 5,
        "shelter_capacity_utilization_pct": 91.5,
        "field_sitrep_summary": "EF-3 tornado track across Black Belt corridor caused 58.4% cell outage and 8.1% web FEMA intake share; survivors require in-person Mobile DRC registration.",
        "recommended_mobile_unit": "FEMA Mobile DRC Unit Southeast-Alpha",
        "regional_hub": "Southeast Regional Hub",
        "priority_tier": "Tier 1 - Immediate",
    },
    {
        "county_id": "geoId/28151",
        "county_name": "Washington County, MS",
        "state_code": "MS",
        "pda_report_id": "FEMA-PDA-2026-MS-28151",
        "active_hazard_alert": "Mississippi Delta Levee Overtop & Severe Wind",
        "peak_wind_mph": 82.0,
        "storm_surge_ft": 0.0,
        "power_grid_outage_pct": 41.2,
        "cell_tower_outage_pct": 46.5,
        "road_washout_status": "US-82 Delta Approach Inundated (High-Water DRC)",
        "bridge_closures_count": 6,
        "shelter_capacity_utilization_pct": 93.0,
        "field_sitrep_summary": "5,558 disaster registrations with 11.9% transit-isolated households and 46.5% cell tower outage in Greenville corridor; Delta-Bravo Mobile DRC staged for dispatch.",
        "recommended_mobile_unit": "FEMA Mobile DRC Unit Delta-Bravo",
        "regional_hub": "Southeast Regional Hub",
        "priority_tier": "Tier 1 - Immediate",
    },
    {
        "county_id": "geoId/28011",
        "county_name": "Bolivar County, MS",
        "state_code": "MS",
        "pda_report_id": "FEMA-PDA-2026-MS-28011",
        "active_hazard_alert": "Delta Agricultural Flood & Grid Outage",
        "peak_wind_mph": 76.0,
        "storm_surge_ft": 0.0,
        "power_grid_outage_pct": 39.8,
        "cell_tower_outage_pct": 44.0,
        "road_washout_status": "MS-1 & Rural Levee Roads Impassable",
        "bridge_closures_count": 4,
        "shelter_capacity_utilization_pct": 88.7,
        "field_sitrep_summary": "3,378 households impacted across rural Bolivar County; sub-station flooding knocked out fixed broadband across high-SVI census tracts.",
        "recommended_mobile_unit": "FEMA Mobile DRC Unit Delta-Bravo",
        "regional_hub": "Southeast Regional Hub",
        "priority_tier": "Tier 1 - Immediate",
    },
    {
        "county_id": "geoId/13141",
        "county_name": "Hancock County, GA",
        "state_code": "GA",
        "pda_report_id": "FEMA-PDA-2026-GA-13141",
        "active_hazard_alert": "Hurricane Wind & Medical Power Emergency",
        "peak_wind_mph": 94.0,
        "storm_surge_ft": 0.0,
        "power_grid_outage_pct": 63.5,
        "cell_tower_outage_pct": 55.2,
        "road_washout_status": "GA-15 & Oconee River Access Downed Timber",
        "bridge_closures_count": 4,
        "shelter_capacity_utilization_pct": 95.1,
        "field_sitrep_summary": "26.5% baseline household internet deficit compounded by 63.5% power outage; high senior (65+) and emPOWER medical device density requires HHS ASPR Mobile Health Unit.",
        "recommended_mobile_unit": "HHS ASPR Mobile Health Unit Delta",
        "regional_hub": "Southeast Regional Hub",
        "priority_tier": "Tier 1 - Immediate",
    },
    {
        "county_id": "geoId/28083",
        "county_name": "Leflore County, MS",
        "state_code": "MS",
        "pda_report_id": "FEMA-PDA-2026-MS-28083",
        "active_hazard_alert": "Yazoo Basin Flood & Backwater Surge",
        "peak_wind_mph": 74.0,
        "storm_surge_ft": 0.0,
        "power_grid_outage_pct": 43.0,
        "cell_tower_outage_pct": 49.0,
        "road_washout_status": "US-49E & Tallahatchie Causeway Restricted",
        "bridge_closures_count": 5,
        "shelter_capacity_utilization_pct": 89.4,
        "field_sitrep_summary": "5,272 registrations with 22.1% no-internet baseline; floodwaters isolating Greenwood low-income housing corridors from fixed FEMA recovery centers.",
        "recommended_mobile_unit": "FEMA Mobile DRC Unit Delta-Bravo",
        "regional_hub": "Southeast Regional Hub",
        "priority_tier": "Tier 1 - Immediate",
    },
    {
        "county_id": "geoId/01063",
        "county_name": "Greene County, AL",
        "state_code": "AL",
        "pda_report_id": "FEMA-PDA-2026-AL-01063",
        "active_hazard_alert": "Black Warrior River Flood & Telecom Blackout",
        "peak_wind_mph": 88.0,
        "storm_surge_ft": 0.0,
        "power_grid_outage_pct": 57.2,
        "cell_tower_outage_pct": 68.5,
        "road_washout_status": "I-20/59 Rural Exits & County Rd 20 Flooded",
        "bridge_closures_count": 6,
        "shelter_capacity_utilization_pct": 92.0,
        "field_sitrep_summary": "25.8% household internet deficit plus 68.5% cell tower blackout; FCC SatCom & Intake Unit Gulf-Echo required to restore emergency survivor registration.",
        "recommended_mobile_unit": "FCC SatCom & Intake Unit Gulf-Echo",
        "regional_hub": "Gulf Coast & South Central Hub",
        "priority_tier": "Tier 1 - Immediate",
    },
    {
        "county_id": "geoId/05041",
        "county_name": "Desha County, AR",
        "state_code": "AR",
        "pda_report_id": "FEMA-PDA-2026-AR-05041",
        "active_hazard_alert": "Arkansas & White River Confluence Flood",
        "peak_wind_mph": 71.0,
        "storm_surge_ft": 0.0,
        "power_grid_outage_pct": 36.4,
        "cell_tower_outage_pct": 42.1,
        "road_washout_status": "US-65 & AR-1 Levee Culvert Washout",
        "bridge_closures_count": 3,
        "shelter_capacity_utilization_pct": 84.5,
        "field_sitrep_summary": "Rural levee overtopping cut fiber backhaul to Dumas and McGehee; mobile satellite intake unit requested by State EOC.",
        "recommended_mobile_unit": "FCC SatCom & Intake Unit Gulf-Echo",
        "regional_hub": "Gulf Coast & South Central Hub",
        "priority_tier": "Tier 2 - High Priority",
    },
    {
        "county_id": "geoId/12065",
        "county_name": "Jefferson County, FL",
        "state_code": "FL",
        "pda_report_id": "FEMA-PDA-2026-FL-12065",
        "active_hazard_alert": "Category 4 Hurricane Storm Surge & Wind",
        "peak_wind_mph": 128.0,
        "storm_surge_ft": 11.5,
        "power_grid_outage_pct": 78.4,
        "cell_tower_outage_pct": 64.0,
        "road_washout_status": "US-98 Coastal Causeway & Canopy Roads Blocked",
        "bridge_closures_count": 8,
        "shelter_capacity_utilization_pct": 96.8,
        "field_sitrep_summary": "11.5-ft Apalachee Bay storm surge and 128 mph winds knocked out 78.4% of grid power; 3,283 registrations require HHS ASPR & Mobile DRC field surge.",
        "recommended_mobile_unit": "HHS ASPR Mobile Health Unit Delta",
        "regional_hub": "Southeast Regional Hub",
        "priority_tier": "Tier 1 - Immediate",
    },
    {
        "county_id": "geoId/13301",
        "county_name": "Warren County, GA",
        "state_code": "GA",
        "pda_report_id": "FEMA-PDA-2026-GA-13301",
        "active_hazard_alert": "Tropical Cyclone Wind & Rural Grid Collapse",
        "peak_wind_mph": 91.0,
        "storm_surge_ft": 0.0,
        "power_grid_outage_pct": 61.0,
        "cell_tower_outage_pct": 59.5,
        "road_washout_status": "US-278 & Briar Creek Bridge Structural Alert",
        "bridge_closures_count": 4,
        "shelter_capacity_utilization_pct": 90.2,
        "field_sitrep_summary": "30.9% baseline household internet deficit (highest among Tier-1 unserved counties) plus 59.5% cell outage; immediate mobile health and intake deployment needed.",
        "recommended_mobile_unit": "HHS ASPR Mobile Health Unit Delta",
        "regional_hub": "Southeast Regional Hub",
        "priority_tier": "Tier 1 - Immediate",
    },
    {
        "county_id": "geoId/48427",
        "county_name": "Starr County, TX",
        "state_code": "TX",
        "pda_report_id": "FEMA-PDA-2026-TX-48427",
        "active_hazard_alert": "Rio Grande Flash Flood & Comms Outage",
        "peak_wind_mph": 68.0,
        "storm_surge_ft": 0.0,
        "power_grid_outage_pct": 34.5,
        "cell_tower_outage_pct": 41.0,
        "road_washout_status": "US-83 Low-Water Crossings Submerged",
        "bridge_closures_count": 3,
        "shelter_capacity_utilization_pct": 85.0,
        "field_sitrep_summary": "Colonias flash flooding along Rio Grande; bilingual mobile satellite intake unit Gulf-Echo staged for deployment.",
        "recommended_mobile_unit": "FCC SatCom & Intake Unit Gulf-Echo",
        "regional_hub": "Gulf Coast & South Central Hub",
        "priority_tier": "Tier 2 - High Priority",
    },
    {
        "county_id": "geoId/21121",
        "county_name": "Knox County, KY",
        "state_code": "KY",
        "pda_report_id": "FEMA-PDA-2026-KY-21121",
        "active_hazard_alert": "Cumberland River Valley Flash Flood",
        "peak_wind_mph": 61.0,
        "storm_surge_ft": 0.0,
        "power_grid_outage_pct": 38.0,
        "cell_tower_outage_pct": 44.5,
        "road_washout_status": "US-25E Feeder Hollows Washed Out",
        "bridge_closures_count": 4,
        "shelter_capacity_utilization_pct": 83.2,
        "field_sitrep_summary": "Appalachian hollow washouts isolating elderly and disability-impacted households; Southeast-Alpha Mobile DRC queued.",
        "recommended_mobile_unit": "FEMA Mobile DRC Unit Southeast-Alpha",
        "regional_hub": "Southeast Regional Hub",
        "priority_tier": "Tier 2 - High Priority",
    },
]


def upload_field_sitrep_pdfs() -> None:
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    print(f"Uploading {len(SITREP_RECORDS)} unstructured FEMA Field SitRep PDFs to gs://{BUCKET_NAME}/field_sitreps/ ...")
    for rec in SITREP_RECORDS:
        cid_clean = rec["county_id"].replace("geoId/", "")
        blob_name = f"field_sitreps/FEMA_SitRep_{rec['state_code']}_{cid_clean}.pdf"
        pdf_bytes = make_minimal_pdf(
            f"FEMA PRELIMINARY DAMAGE ASSESSMENT & FIELD SITREP: {rec['pda_report_id']}",
            [
                f"County: {rec['county_name']} ({rec['county_id']})",
                f"Active Hazard Alert: {rec['active_hazard_alert']}",
                f"Peak Wind: {rec['peak_wind_mph']} mph | Storm Surge: {rec['storm_surge_ft']} ft",
                f"Power Grid Outage: {rec['power_grid_outage_pct']}% | Cell Tower Outage: {rec['cell_tower_outage_pct']}%",
                f"Road & Bridge Status: {rec['road_washout_status']} ({rec['bridge_closures_count']} closures)",
                f"Recommended Dispatch: {rec['recommended_mobile_unit']} ({rec['regional_hub']})",
                f"Priority Tier: {rec['priority_tier']}",
                f"Field SitRep Summary: {rec['field_sitrep_summary']}",
            ],
        )
        blob = bucket.blob(blob_name)
        blob.metadata = {
            "county_id": rec["county_id"],
            "county_name": rec["county_name"],
            "pda_report_id": rec["pda_report_id"],
            "priority_tier": rec["priority_tier"],
            "recommended_mobile_unit": rec["recommended_mobile_unit"],
        }
        blob.upload_from_string(pdf_bytes, content_type="application/pdf")
    print("Uploaded all 12 FEMA Field SitRep PDFs.")


def build_lakehouse_tables() -> None:
    bq_client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    conn_fqn = f"`{PROJECT_ID}.{CONN_LOCATION}.{CONN_ID}`"

    # Wait briefly for IAM propagation if connection was just created
    time.sleep(3)

    print("1. Creating BigLake Object Table `fema_field_sitrep_objects` over unstructured GCS PDFs...")
    sql_obj_table = f"""
    CREATE OR REPLACE EXTERNAL TABLE `{PROJECT_ID}.{DATASET_ID}.fema_field_sitrep_objects`
    WITH CONNECTION {conn_fqn}
    OPTIONS (
      object_metadata = 'SIMPLE',
      uris = ['gs://{BUCKET_NAME}/field_sitreps/*.pdf']
    );
    """
    bq_client.query(sql_obj_table).result()
    print("   Created `fema_field_sitrep_objects`.")

    # Build temporary staging table for explicit 12 priority counties
    print("2. Creating BigLake Managed Apache Iceberg table `noaa_hazard_iceberg`...")
    values_rows = []
    for r in SITREP_RECORDS:
        cid = r["county_id"]
        cname = r["county_name"].replace("'", "\\'")
        sc = r["state_code"]
        pda = r["pda_report_id"]
        haz = r["active_hazard_alert"].replace("'", "\\'")
        wind = r["peak_wind_mph"]
        surge = r["storm_surge_ft"]
        pwr = r["power_grid_outage_pct"]
        cell = r["cell_tower_outage_pct"]
        road = r["road_washout_status"].replace("'", "\\'")
        br = r["bridge_closures_count"]
        sh = r["shelter_capacity_utilization_pct"]
        summ = r["field_sitrep_summary"].replace("'", "\\'")
        unit = r["recommended_mobile_unit"].replace("'", "\\'")
        hub = r["regional_hub"].replace("'", "\\'")
        tier = r["priority_tier"]
        uri = f"gs://{BUCKET_NAME}/field_sitreps/FEMA_SitRep_{sc}_{cid.replace('geoId/', '')}.pdf"
        values_rows.append(
            f"STRUCT('{cid}' AS county_id, '{cname}' AS county_name, '{sc}' AS state_code, "
            f"'{pda}' AS pda_report_id, '{haz}' AS active_hazard_alert, {wind} AS peak_wind_mph, "
            f"{surge} AS storm_surge_ft, {pwr} AS power_grid_outage_pct, {cell} AS cell_tower_outage_pct, "
            f"'{road}' AS road_washout_status, {br} AS bridge_closures_count, "
            f"{sh} AS shelter_capacity_utilization_pct, '{summ}' AS field_sitrep_summary, "
            f"'{uri}' AS sitrep_pdf_uri, '{unit}' AS recommended_mobile_unit, "
            f"'{hub}' AS regional_hub, '{tier}' AS priority_tier)"
        )
    overrides_cte = "SELECT * FROM UNNEST([\n  " + ",\n  ".join(values_rows) + "\n])"

    # Create BigLake Apache Iceberg table 1: noaa_hazard_iceberg
    sql_create_noaa_iceberg = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.noaa_hazard_iceberg` (
      county_id STRING,
      county_name STRING,
      state_code STRING,
      active_hazard_alert STRING,
      peak_wind_mph FLOAT64,
      storm_surge_ft FLOAT64,
      power_grid_outage_pct FLOAT64,
      cell_tower_outage_pct FLOAT64,
      iceberg_catalog_source STRING,
      last_synced_utc TIMESTAMP
    )
    WITH CONNECTION {conn_fqn}
    OPTIONS (
      file_format = 'PARQUET',
      table_format = 'ICEBERG',
      storage_uri = 'gs://{BUCKET_NAME}/iceberg/noaa_hazard_iceberg'
    );
    """
    bq_client.query(sql_create_noaa_iceberg).result()

    sql_insert_noaa_iceberg = f"""
    INSERT INTO `{PROJECT_ID}.{DATASET_ID}.noaa_hazard_iceberg`
    WITH PriorityOverrides AS (
      {overrides_cte}
    )
    SELECT
      c.county_id,
      c.county_name,
      c.state_code,
      COALESCE(
        p.active_hazard_alert,
        CASE
          WHEN c.hurricane_risk_score >= 80 THEN 'Tropical Cyclone & Coastal Surge Watch'
          WHEN c.flood_risk_score >= 75 THEN 'Riverine Flash Flood Watch'
          WHEN c.wildfire_risk_score >= 75 THEN 'Red Flag Wildfire & Smoke Advisory'
          WHEN c.disasters_since_2023 >= 2 THEN 'Severe Storm & Grid Resilience Watch'
          ELSE 'Normal Baseline Monitoring'
        END
      ) AS active_hazard_alert,
      COALESCE(p.peak_wind_mph, ROUND(35.0 + COALESCE(c.hurricane_risk_score, 20.0) * 0.55, 1)) AS peak_wind_mph,
      COALESCE(p.storm_surge_ft, CASE WHEN c.hurricane_risk_score >= 85 THEN ROUND(c.hurricane_risk_score * 0.08, 1) ELSE 0.0 END) AS storm_surge_ft,
      COALESCE(p.power_grid_outage_pct, ROUND(GREATEST(2.0, COALESCE(c.nri_risk_score, 30.0) * 0.38), 1)) AS power_grid_outage_pct,
      COALESCE(p.cell_tower_outage_pct, ROUND(GREATEST(1.5, COALESCE(c.no_internet_pct, 12.0) * 1.45), 1)) AS cell_tower_outage_pct,
      'AWS S3 / NOAA NWS Open Apache Iceberg Catalog (BigLake Zero-ETL)' AS iceberg_catalog_source,
      CURRENT_TIMESTAMP() AS last_synced_utc
    FROM `{PROJECT_ID}.{DATASET_ID}.county_readiness` c
    LEFT JOIN PriorityOverrides p ON c.county_id = p.county_id;
    """
    bq_client.query(sql_insert_noaa_iceberg).result()
    print("   Created & populated BigLake Apache Iceberg table `noaa_hazard_iceberg` (3,144 rows).")

    # Create BigLake Apache Iceberg table 2: fema_field_assessments_iceberg
    print("3. Creating BigLake Managed Apache Iceberg table `fema_field_assessments_iceberg`...")
    sql_create_fema_iceberg = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.fema_field_assessments_iceberg` (
      county_id STRING,
      county_name STRING,
      state_code STRING,
      pda_report_id STRING,
      road_washout_status STRING,
      bridge_closures_count INT64,
      shelter_capacity_utilization_pct FLOAT64,
      field_sitrep_summary STRING,
      sitrep_pdf_uri STRING,
      recommended_mobile_unit STRING,
      regional_hub STRING,
      priority_tier STRING,
      source_catalog STRING
    )
    WITH CONNECTION {conn_fqn}
    OPTIONS (
      file_format = 'PARQUET',
      table_format = 'ICEBERG',
      storage_uri = 'gs://{BUCKET_NAME}/iceberg/fema_field_assessments_iceberg'
    );
    """
    bq_client.query(sql_create_fema_iceberg).result()

    sql_insert_fema_iceberg = f"""
    INSERT INTO `{PROJECT_ID}.{DATASET_ID}.fema_field_assessments_iceberg`
    WITH PriorityOverrides AS (
      {overrides_cte}
    )
    SELECT
      c.county_id,
      c.county_name,
      c.state_code,
      COALESCE(p.pda_report_id, CONCAT('FEMA-PDA-2026-', c.state_code, '-', REPLACE(c.county_id, 'geoId/', ''))) AS pda_report_id,
      COALESCE(
        p.road_washout_status,
        CASE
          WHEN NOT c.has_team_coverage AND c.social_vulnerability_score >= 75.0 THEN 'Secondary Feeder Roads Restricted (Mobile DRC Recommended)'
          ELSE 'Primary Arterial Corridors Open'
        END
      ) AS road_washout_status,
      COALESCE(p.bridge_closures_count, CAST( GREATEST(0, COALESCE(c.disasters_since_2023, 0) - 1) AS INT64)) AS bridge_closures_count,
      COALESCE(p.shelter_capacity_utilization_pct, ROUND(LEAST(98.0, 45.0 + COALESCE(c.social_vulnerability_score, 50.0) * 0.42), 1)) AS shelter_capacity_utilization_pct,
      COALESCE(
        p.field_sitrep_summary,
        CONCAT('FEMA Joint Preliminary Damage Assessment for ', c.county_name, ': SVI ', ROUND(c.social_vulnerability_score, 1), ', No-Internet ', ROUND(c.no_internet_pct, 1), '%.')
      ) AS field_sitrep_summary,
      COALESCE(p.sitrep_pdf_uri, CONCAT('gs://{BUCKET_NAME}/field_sitreps/FEMA_SitRep_', c.state_code, '_', REPLACE(c.county_id, 'geoId/', ''), '.pdf')) AS sitrep_pdf_uri,
      COALESCE(p.recommended_mobile_unit, c.recommended_team) AS recommended_mobile_unit,
      COALESCE(p.regional_hub, c.regional_hub) AS regional_hub,
      COALESCE(p.priority_tier, c.priority_tier) AS priority_tier,
      'BigLake Apache Iceberg + Unstructured GCS Field SitRep Object Table' AS source_catalog
    FROM `{PROJECT_ID}.{DATASET_ID}.county_readiness` c
    LEFT JOIN PriorityOverrides p ON c.county_id = p.county_id
    WHERE c.disasters_since_2023 >= 1 OR p.county_id IS NOT NULL;
    """
    bq_client.query(sql_insert_fema_iceberg).result()
    print("   Created & populated BigLake Apache Iceberg table `fema_field_assessments_iceberg`.")

    # Enrich county_readiness with the Borderless Lakehouse columns so both direct and joined queries run in <1s
    print("4. Adding Borderless Lakehouse columns onto `county_readiness` and creating `v_borderless_lakehouse_dispatch`...")
    for col_name, col_type in [
        ("active_hazard_alert", "STRING"),
        ("cell_tower_outage_pct", "FLOAT64"),
        ("road_washout_status", "STRING"),
        ("sitrep_pdf_uri", "STRING"),
    ]:
        bq_client.query(
            f"ALTER TABLE `{PROJECT_ID}.{DATASET_ID}.county_readiness` ADD COLUMN IF NOT EXISTS {col_name} {col_type};"
        ).result()

    sql_update_cr = f"""
    UPDATE `{PROJECT_ID}.{DATASET_ID}.county_readiness` c
    SET
      active_hazard_alert = n.active_hazard_alert,
      cell_tower_outage_pct = n.cell_tower_outage_pct,
      road_washout_status = COALESCE(f.road_washout_status, 'Primary Arterial Corridors Open'),
      sitrep_pdf_uri = f.sitrep_pdf_uri
    FROM `{PROJECT_ID}.{DATASET_ID}.noaa_hazard_iceberg` n
    LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.fema_field_assessments_iceberg` f
      ON n.county_id = f.county_id
    WHERE c.county_id = n.county_id;
    """
    bq_client.query(sql_update_cr).result()

    sql_view = f"""
    CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET_ID}.v_borderless_lakehouse_dispatch` AS
    SELECT
      c.county_id,
      c.county_name,
      c.state_code,
      ROUND(c.social_vulnerability_score, 2) AS svi_score,
      ROUND(c.no_internet_pct, 1) AS no_internet_pct,
      ROUND(c.web_registration_pct, 1) AS web_intake_pct,
      c.total_registrations,
      ice.active_hazard_alert,
      ice.peak_wind_mph,
      ice.cell_tower_outage_pct,
      pda.road_washout_status,
      pda.bridge_closures_count,
      pda.recommended_mobile_unit,
      pda.regional_hub,
      pda.priority_tier,
      obj.uri AS unstructured_sitrep_pdf_uri,
      obj.size AS pdf_bytes,
      pda.field_sitrep_summary
    FROM `{PROJECT_ID}.{DATASET_ID}.county_readiness` c
    JOIN `{PROJECT_ID}.{DATASET_ID}.noaa_hazard_iceberg` ice
      ON c.county_id = ice.county_id
    JOIN `{PROJECT_ID}.{DATASET_ID}.fema_field_assessments_iceberg` pda
      ON c.county_id = pda.county_id
    LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.fema_field_sitrep_objects` obj
      ON obj.uri = pda.sitrep_pdf_uri
    WHERE c.has_team_coverage = FALSE
      AND c.social_vulnerability_score >= 75.0
      AND c.disasters_since_2023 >= 1
      AND c.total_registrations > 0
      AND c.state_code NOT IN ('AK', 'HI', 'PR')
    ORDER BY c.social_vulnerability_score DESC;
    """
    bq_client.query(sql_view).result()
    print("   Updated `county_readiness` and created view `v_borderless_lakehouse_dispatch`.")

    # Verify the Beat 2C Borderless Lakehouse query speed and output!
    t0 = time.time()
    rows = list(bq_client.query(f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.v_borderless_lakehouse_dispatch` LIMIT 10").result())
    elapsed = time.time() - t0
    print(f"\nVerified Beat 2C Borderless Lakehouse Query ({len(rows)} rows in {elapsed:.2f}s):")
    for r in rows[:5]:
        print(
            f"  - {r['county_name']} (SVI {r['svi_score']}): "
            f"Alert='{r['active_hazard_alert']}' | CellOutage={r['cell_tower_outage_pct']}% | "
            f"Road='{r['road_washout_status']}' | Unit='{r['recommended_mobile_unit']}' | PDF={r['unstructured_sitrep_pdf_uri']} ({r['pdf_bytes']}B)"
        )


if __name__ == "__main__":
    ensure_bucket_and_connection()
    upload_field_sitrep_pdfs()
    build_lakehouse_tables()
