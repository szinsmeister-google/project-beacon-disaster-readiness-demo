"""Creates the Spanner database (if needed) and bulk-loads public + agency data.

Reads data/public/* (fetch_public.py, fetch_fema.py, build_profiles.py) and
data/private/* (generate_agency.py). Uses Application Default Credentials or
SPANNER_EMULATOR_HOST when testing locally.

Usage:
  python loader/load_spanner.py                # create DB if missing, then load
  python loader/load_spanner.py --recreate     # drop and recreate the database first
  python loader/load_spanner.py --ddl-only     # just create the database schema
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import math
import os
import re
import time

import pandas as pd
from google.api_core import exceptions as gexc
from google.cloud import spanner

from common import (
    DATA_DIR,
    PRIVATE_DIR,
    PUBLIC_DIR,
    PUBLIC_PROVENANCE,
    SCHEMA_FILE,
    SPANNER_DATABASE,
    SPANNER_INSTANCE,
    get_spanner_client,
    write_json,
)

NODE_COLS = [
    "subject_id", "label", "name", "display_name", "provenance", "state_code",
    "latitude", "longitude", "description", "incident_type", "declaration_date",
    "fy_declared", "hub_region", "capacity",
]
EDGE_COLS = ["subject_id", "predicate", "object_id", "provenance"]
OBS_COLS = [
    "observation_about", "variable_measured", "observation_date", "value",
    "measurement_method", "observation_period", "unit", "provenance_id", "provenance_url",
]


def ddl_statements() -> list[str]:
  text = re.sub(r"--[^\n]*", "", SCHEMA_FILE.read_text())
  return [s.strip() for s in text.split(";") if s.strip()]


def clean(v):
  """Converts pandas/numpy scalars (including NaN/NA) to Spanner-friendly Python values."""
  if v is None or isinstance(v, (str, bytes, dt.date, bool)):
    return v
  try:
    if pd.isna(v):
      return None
  except (TypeError, ValueError):
    pass
  return v.item() if hasattr(v, "item") else v


def to_date(v):
  if v is None or (isinstance(v, float) and math.isnan(v)):
    return None
  if isinstance(v, dt.date):
    return v
  s = str(v).strip()
  if not s:
    return None
  return dt.date.fromisoformat(s[:10])


INT_COLS = {
    "population", "population_year", "households", "acs_year", "fy_declared", "capacity",
    "no_internet_households", "age_65_plus", "disability_count", "poverty_count",
    "total_valid_registrations", "web_registrations", "call_center_registrations",
    "mobile_registrations",
}


def rows_of(df: pd.DataFrame, cols: list[str]) -> list[tuple]:
  df = df[cols].copy()
  for c in INT_COLS.intersection(cols):
    df[c] = pd.to_numeric(df[c], errors="coerce").round().astype("Int64")
  return [tuple(clean(v) for v in rec) for rec in df.itertuples(index=False, name=None)]


def load(database, table: str, cols: list[str], rows: list[tuple], batch: int = 2000,
         workers: int = 4) -> int:
  if not rows:
    print(f"  {table:20s}         0 rows (skipped empty)")
    return 0
  t0 = time.time()
  chunks = [rows[i:i + batch] for i in range(0, len(rows), batch)]

  def write(chunk):
    for attempt in range(5):
      try:
        with database.batch() as b:
          b.insert_or_update(table=table, columns=cols, values=chunk)
        return len(chunk)
      except (gexc.Aborted, gexc.DeadlineExceeded, gexc.ServiceUnavailable):
        time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to write a batch to {table}")

  done = 0
  with concurrent.futures.ThreadPoolExecutor(workers) as pool:
    for n in pool.map(write, chunks):
      done += n
  print(f"  {table:20s} {done:>9,} rows  ({time.time() - t0:.1f}s)")
  return done


def main() -> None:
  ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
  ap.add_argument("--recreate", action="store_true", help="Drop and recreate the database.")
  ap.add_argument("--ddl-only", action="store_true", help="Create the schema and stop.")
  args = ap.parse_args()

  proj = os.environ.get("GOOGLE_CLOUD_PROJECT") or "test-project"
  client = get_spanner_client(proj)
  instance = client.instance(SPANNER_INSTANCE)
  if not instance.exists():
    configs = list(client.list_instance_configs())
    cfg_name = configs[0].name if configs else f"projects/{proj}/instanceConfigs/emulator-config"
    print(f"Creating instance {SPANNER_INSTANCE} ({cfg_name}) ...")
    instance = client.instance(SPANNER_INSTANCE, configuration_name=cfg_name, node_count=1)
    instance.create().result(timeout=120)
  database = instance.database(SPANNER_DATABASE)

  if args.recreate and database.exists():
    print(f"Dropping database {SPANNER_DATABASE} ...")
    database.drop()
    database = instance.database(SPANNER_DATABASE)
  if not database.exists():
    stmts = ddl_statements()
    print(f"Creating database {SPANNER_DATABASE} with {len(stmts)} DDL statements ...")
    database = instance.database(SPANNER_DATABASE, ddl_statements=stmts)
    database.create().result(timeout=1800)
    print("  schema ready")
  else:
    print(f"Database {SPANNER_DATABASE} exists; loading into the existing schema.")
  if args.ddl_only:
    return

  # ------------------------------------------------------------------ public places & observations
  places = pd.read_csv(PUBLIC_DIR / "places.csv", dtype={"state_code": str})
  places["provenance"] = PUBLIC_PROVENANCE
  pub_edges = pd.read_csv(PUBLIC_DIR / "edges.csv", dtype=str)
  pub_edges["provenance"] = PUBLIC_PROVENANCE
  obs = pd.read_csv(PUBLIC_DIR / "observations.csv.gz", dtype={"observation_date": str},
                    keep_default_na=False, na_values={"value": [""]})
  county_profile = pd.read_csv(PUBLIC_DIR / "county_profile.csv")
  state_profile = pd.read_csv(PUBLIC_DIR / "state_profile.csv")

  # ------------------------------------------------------------------ OpenFEMA program data
  fema_disasters = pd.read_csv(PUBLIC_DIR / "fema_disasters.csv", dtype={"state_code": str})
  fema_edges = pd.read_csv(PUBLIC_DIR / "fema_edges.csv", dtype=str)
  fema_desig = pd.read_csv(PUBLIC_DIR / "fema_designations.csv")
  fema_reg = pd.read_csv(PUBLIC_DIR / "fema_registrations.csv")

  fema_disasters["declaration_date"] = fema_disasters["declaration_date"].map(to_date)
  fema_desig["declaration_date"] = fema_desig["declaration_date"].map(to_date)

  # ------------------------------------------------------------------ Agency data
  agency_nodes = pd.read_csv(PRIVATE_DIR / "agency_nodes.csv", dtype={"state_code": str})
  agency_edges = pd.read_csv(PRIVATE_DIR / "agency_edges.csv", dtype=str)

  # Harmonize all Node records
  for df in (places, fema_disasters, agency_nodes):
    for c in NODE_COLS:
      if c not in df:
        df[c] = None

  nodes = pd.concat([places[NODE_COLS], fema_disasters[NODE_COLS], agency_nodes[NODE_COLS]], ignore_index=True)
  edges = pd.concat([pub_edges[EDGE_COLS], fema_edges[EDGE_COLS], agency_edges[EDGE_COLS]], ignore_index=True)

  node_ids = set(nodes.subject_id)
  missing = set(edges.object_id) - node_ids
  if missing:
    print(f"  Warning: {len(missing)} edges point to unknown nodes (e.g. {sorted(missing)[:5]}). Filtering out.")
    edges = edges[edges.object_id.isin(node_ids)]

  obs = obs[obs.observation_about.isin(node_ids)]
  for c in ["measurement_method", "observation_period", "unit", "provenance_id", "provenance_url"]:
    obs[c] = obs[c].replace("", None)

  # Filter designations and registrations to valid nodes
  fema_desig = fema_desig[fema_desig.disaster_id.isin(node_ids) & fema_desig.county_id.isin(node_ids)]
  fema_reg = fema_reg[fema_reg.disaster_id.isin(node_ids) & fema_reg.county_id.isin(node_ids)]

  print("Loading into Spanner ...")
  written = {
      "Node": load(database, "Node", NODE_COLS, rows_of(nodes, NODE_COLS)),
      "Edge": load(database, "Edge", EDGE_COLS, rows_of(edges, EDGE_COLS)),
      "Observation": load(database, "Observation", OBS_COLS, rows_of(obs, OBS_COLS), batch=2500),
  }
  cp_cols = list(county_profile.columns)
  written["CountyProfile"] = load(database, "CountyProfile", cp_cols, rows_of(county_profile, cp_cols))
  sp_cols = list(state_profile.columns)
  written["StateProfile"] = load(database, "StateProfile", sp_cols, rows_of(state_profile, sp_cols))
  desig_cols = list(fema_desig.columns)
  written["DisasterDesignation"] = load(database, "DisasterDesignation", desig_cols, rows_of(fema_desig, desig_cols))
  reg_cols = list(fema_reg.columns)
  written["Registration"] = load(database, "Registration", reg_cols, rows_of(fema_reg, reg_cols))

  write_json(DATA_DIR / "load_manifest.json", {
      "loaded_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
      "project": proj,
      "instance": SPANNER_INSTANCE,
      "database": SPANNER_DATABASE,
      "rows_written": written,
      "disasters": int(len(fema_disasters)),
      "hubs": int((agency_nodes["label"] == "hub").sum()),
      "teams": int((agency_nodes["label"] == "team").sum()),
  })

  try:
    database.update_ddl(["ANALYZE"]).result(timeout=900)
    print("  optimizer statistics refreshed (ANALYZE)")
  except Exception as e:
    print(f"  (skipped ANALYZE: {e})")

  with database.snapshot(multi_use=True) as snap:
    for table in ["Node", "Edge", "Observation", "CountyProfile", "StateProfile",
                  "DisasterDesignation", "Registration", "DeploymentPlan"]:
      n = list(snap.execute_sql(f"SELECT COUNT(*) FROM {table}"))[0][0]
      print(f"  {table:20s} {n:>9,} rows in Spanner")
    try:
      labels = list(snap.execute_sql(
          "SELECT g.label, COUNT(*) AS nodes "
          "FROM GRAPH_TABLE(DCGraph MATCH (n) RETURN n.label AS label) AS g "
          "GROUP BY g.label ORDER BY nodes DESC"))
      print("  graph nodes by label:", {r[0]: r[1] for r in labels})
    except Exception as e:
      print(f"  (graph check: {e})")


if __name__ == "__main__":
  main()
