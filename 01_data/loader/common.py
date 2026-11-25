"""Shared settings and helpers for the loader scripts."""

from __future__ import annotations

import json
import os
import pathlib
import sys

from dotenv import load_dotenv

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
PUBLIC_DIR = DATA_DIR / "public"
PRIVATE_DIR = DATA_DIR / "private"
SCHEMA_FILE = REPO_ROOT / "schema" / "ddl.sql"

# Make the agent package importable so the loader and the agent share one
# definition of the market-similarity scoring.
sys.path.insert(0, str(REPO_ROOT / "agent"))

load_dotenv(REPO_ROOT / ".env")

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
SPANNER_INSTANCE = os.environ.get("SPANNER_INSTANCE", "dc-graph-demo")
SPANNER_DATABASE = os.environ.get("SPANNER_DATABASE", "readiness_dcgraph")
DC_API_KEY = os.environ.get("DC_API_KEY", "")

PUBLIC_PROVENANCE = "datacommons.org"
FEMA_PROVENANCE = "openfema"
AGENCY_PROVENANCE = "beacon"
PRIVATE_PROVENANCE = "beacon"

# USPS codes for the 50 states + DC, keyed by 2-digit FIPS code.
FIPS_TO_USPS = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO",
    "09": "CT", "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI",
    "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
    "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
    "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
    "54": "WV", "55": "WI", "56": "WY",
}
USPS_TO_FIPS = {v: k for k, v in FIPS_TO_USPS.items()}


def require(value: str, name: str) -> str:
  if not value:
    sys.exit(f"Missing {name}. Set it in {REPO_ROOT / '.env'}.")
  return value


def write_json(path: pathlib.Path, obj) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str))


def read_json(path: pathlib.Path):
  return json.loads(path.read_text())


def get_spanner_client(project: str | None = None):
  from google.cloud import spanner  # pylint: disable=g-import-not-at-top
  proj = project or PROJECT or os.environ.get("GCP_PROJECT_ID", "")
  if not os.environ.get("SPANNER_EMULATOR_HOST"):
    try:
      import subprocess
      from google.oauth2.credentials import Credentials
      tok = subprocess.check_output(
          ["gcloud", "auth", "application-default", "print-access-token"],
          text=True, stderr=subprocess.DEVNULL, timeout=10).strip()
      if tok:
        return spanner.Client(project=proj, credentials=Credentials(tok))
    except Exception:
      pass
  return spanner.Client(project=proj)
