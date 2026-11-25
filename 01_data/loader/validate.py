"""Validates the loaded Spanner database against the generator's answer key.

Run after load_spanner.py. Checks in order:
  1. Row counts in Spanner vs. what the loader wrote (data/load_manifest.json).
  2. Graph integrity: teams/hubs located in valid counties, counties linked to states,
     no dangling edges, and case-insensitive dynamic labels in GQL.
  3. Every agent tool against the live database, comparing outputs against data/private/story.json.
  4. The Conversational Analytics verified queries (ca_agent/verified_queries.json).
  5. Optionally (--write-test) the write path: add a deployment plan row, read it back, clear it.

Writes data/demo_numbers.json: the verified numbers the demo script quotes.

Usage:
  python loader/validate.py [--write-test] [--verbose]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import traceback
from typing import Any, Callable

from common import DATA_DIR, PRIVATE_DIR, REPO_ROOT, read_json, write_json

from readiness_agent import db, tools  # pylint: disable=g-import-not-at-top

TABLES = [
    "Node", "Edge", "Observation", "CountyProfile", "StateProfile",
    "DisasterDesignation", "Registration", "DeploymentPlan",
]
CA_QUERIES_FILE = REPO_ROOT / "ca_agent" / "verified_queries.json"

RESULTS: list[tuple[str, str, str]] = []
NUMBERS: dict[str, Any] = {}
VERBOSE = False


def record(status: str, name: str, detail: str = "") -> None:
  RESULTS.append((status, name, detail))
  print(f"  {status:4s}  {name}" + (f": {detail}" if detail else ""), flush=True)


def run(name: str, fn: Callable[[], Any]) -> Any:
  try:
    return fn()
  except Exception as e:  # pylint: disable=broad-except
    record("FAIL", name, f"{type(e).__name__}: {str(e)[:400]}")
    if VERBOSE:
      traceback.print_exc()
    return None


def q(sql: str, params: dict | None = None) -> list[dict]:
  return db.query(sql, params, strong=True)


def q1(sql: str, params: dict | None = None) -> Any:
  rows = q(sql, params)
  return next(iter(rows[0].values())) if rows else None


def section(title: str) -> None:
  print(f"\n== {title}", flush=True)


# =============================================================================
# 1. Row counts
# =============================================================================

def check_row_counts(manifest: dict | None) -> dict[str, int]:
  counts = {t: q1(f"SELECT COUNT(*) AS n FROM {t}") for t in TABLES}
  written = (manifest or {}).get("rows_written", {})
  for t in TABLES:
    n = counts[t]
    if t == "DeploymentPlan":
      record("INFO", "DeploymentPlan rows", f"{n} (run scripts/reset_demo.py to clear before demo)")
      continue
    if t not in written:
      record("PASS" if n else "FAIL", f"{t} rows", f"{n:,} (no manifest comparison)")
    elif n == written[t]:
      record("PASS", f"{t} rows", f"{n:,}")
    elif n < written[t]:
      record("WARN", f"{t} rows", f"{n:,} in Spanner vs {written[t]:,} written")
    else:
      record("FAIL", f"{t} rows", f"{n:,} in Spanner vs {written[t]:,} written")
  return counts


# =============================================================================
# 2. Graph integrity
# =============================================================================

UNLOCATED_SQL = """
SELECT n.subject_id FROM Node AS n
LEFT JOIN (
  SELECT e.subject_id AS subject_id, COUNT(*) AS counties
  FROM Edge AS e JOIN Node AS c ON c.subject_id = e.object_id
  WHERE e.predicate = 'locatedin' AND c.label = 'county'
  GROUP BY e.subject_id
) AS k ON k.subject_id = n.subject_id
WHERE n.label IN ('team', 'hub') AND COALESCE(k.counties, 0) != 1
LIMIT 5
"""

ORPHAN_COUNTY_SQL = """
SELECT n.subject_id FROM Node AS n
LEFT JOIN (
  SELECT DISTINCT e.subject_id AS subject_id
  FROM Edge AS e JOIN Node AS s ON s.subject_id = e.object_id
  WHERE e.predicate = 'containedinplace' AND s.label = 'state'
) AS p ON p.subject_id = n.subject_id
WHERE n.label = 'county' AND p.subject_id IS NULL
LIMIT 5
"""

DANGLING_SQL = """
SELECT COUNT(*) AS n FROM Edge AS e
LEFT JOIN Node AS o ON o.subject_id = e.object_id
WHERE o.subject_id IS NULL
"""

GRAPH_NODES_SQL = """
SELECT g.label, COUNT(*) AS n
FROM GRAPH_TABLE(DCGraph MATCH (x:Entity) RETURN x.label AS label) AS g
GROUP BY g.label
"""

CAMELCASE_LABELS_SQL = """
SELECT
  (SELECT COUNT(*) FROM GRAPH_TABLE(DCGraph MATCH (d:Disaster) RETURN d.subject_id AS id)) AS disasters,
  (SELECT COUNT(*) FROM GRAPH_TABLE(DCGraph MATCH (t:Team) RETURN t.subject_id AS id)) AS teams,
  (SELECT COUNT(*) FROM GRAPH_TABLE(DCGraph MATCH (h:Hub) RETURN h.subject_id AS id)) AS hubs,
  (SELECT COUNT(*) FROM GRAPH_TABLE(
     DCGraph MATCH (:Disaster)-[:affectedPlace]->(c:County)-[:containedInPlace]->(:State)
     RETURN c.subject_id AS id)) AS disaster_county_state_paths
"""


def check_graph(counts: dict[str, int]) -> None:
  bad = q(UNLOCATED_SQL)
  record("PASS" if not bad else "FAIL", "Every team and hub is located in exactly one county",
         "" if not bad else f"e.g. {[r['subject_id'] for r in bad]}")
  orphans = q(ORPHAN_COUNTY_SQL)
  record("PASS" if not orphans else "FAIL", "Every county has a parent state",
         "" if not orphans else f"e.g. {[r['subject_id'] for r in orphans]}")
  dangling = q1(DANGLING_SQL)
  record("PASS" if dangling == 0 else "FAIL", "No edge points at a missing node", f"{dangling} dangling")

  nodes = {r["label"]: r["n"] for r in q(GRAPH_NODES_SQL)}
  total = sum(nodes.values())
  record("PASS" if total == counts["Node"] else "FAIL", "Graph sees every Node row",
         f"{total:,} nodes ({', '.join(f'{k}={v}' for k, v in sorted(nodes.items()))})")

  cc = q(CAMELCASE_LABELS_SQL)[0]
  record("PASS" if cc["disaster_county_state_paths"] > 0 else "FAIL",
         "GQL queries with camelCase labels work",
         f"disasters={cc['disasters']}, teams={cc['teams']}, paths={cc['disaster_county_state_paths']:,}")


# =============================================================================
# 3. Agent tools
# =============================================================================

def check_pulse(story: dict) -> None:
  res = tools.get_readiness_pulse()
  tot = res.get("total_valid_registrations", 0)
  expected_tot = story.get("total_registrations", 0)
  disasters = res.get("disaster_declarations_since_2023", 0)
  expected_disasters = story.get("disasters_count", 0)

  record("PASS" if disasters == expected_disasters else "WARN",
         "get_readiness_pulse disaster count", f"{disasters} (expected {expected_disasters})")
  record("PASS" if tot == expected_tot else "WARN",
         "get_readiness_pulse total registrations", f"{tot:,} (expected {expected_tot:,})")

  ch = res.get("channel_breakdown", {})
  NUMBERS["disaster_declarations_since_2023"] = disasters
  NUMBERS["designated_counties"] = res.get("designated_counties")
  NUMBERS["total_valid_registrations"] = tot
  NUMBERS["web_share_pct"] = ch.get("web_share_pct")
  NUMBERS["call_center_share_pct"] = ch.get("call_center_share_pct")
  NUMBERS["mobile_share_pct"] = ch.get("mobile_share_pct")


def check_compare_access(story: dict) -> None:
  res = tools.compare_registration_access("no_internet")
  q = res.get("quartile_analysis", {})
  q1_val = q.get("lowest_quartile", {}).get("online_registration_pct")
  q4_val = q.get("highest_quartile", {}).get("online_registration_pct")
  corr = res.get("correlations", {}).get("pearson_registration_weighted")

  record("PASS" if q1_val is not None and q4_val is not None and q1_val > q4_val else "FAIL",
         "compare_registration_access shows higher online registration where internet access is higher",
         f"lowest no-internet: {q1_val}% vs highest no-internet: {q4_val}%")

  record("PASS" if corr is not None and corr < -0.20 else "FAIL",
         "compare_registration_access negative correlation confirmed", f"weighted r = {corr}")

  # Compare with age_65
  age_res = tools.compare_registration_access("age_65")
  age_corr = age_res.get("correlations", {}).get("pearson_unweighted")
  record("PASS" if age_corr is not None and abs(age_corr) < abs(corr or 0) else "WARN",
         "age 65+ correlation is weaker than internet access", f"age_65 r = {age_corr} vs no_internet r = {corr}")

  NUMBERS["low_no_internet_web_pct"] = q1_val
  NUMBERS["high_no_internet_web_pct"] = q4_val
  NUMBERS["quartile_spread_pp"] = round(float(q1_val or 0) - float(q4_val or 0), 1)
  NUMBERS["internet_weighted_correlation"] = corr
  NUMBERS["age_65_correlation"] = age_corr


def check_repeat_counties() -> None:
  res = tools.find_repeat_hit_counties(min_disasters=3, limit=8)
  record("PASS" if len(res) >= 3 else "FAIL", "find_repeat_hit_counties returns repeat-hit communities",
         f"returned {len(res)} counties, top: {res[0]['county_name']} ({res[0]['disasters_since_2023']} disasters)")
  if res:
    top = res[0]
    NUMBERS["top_repeat_county_name"] = top["county_name"]
    NUMBERS["top_repeat_county_disasters"] = top["disasters_since_2023"]
    NUMBERS["top_repeat_county_social_vuln"] = top.get("social_vulnerability_score")


def check_disaster_history() -> None:
  top_dr = q1("SELECT disaster_id FROM Registration ORDER BY total_valid_registrations DESC LIMIT 1")
  dr_clean = top_dr.replace("fema/", "") if top_dr else "DR-4834"
  res = tools.get_disaster_history(dr_clean)
  record("PASS" if res.get("affected_counties_count", 0) > 0 else "FAIL",
         f"get_disaster_history({dr_clean})",
         f"{res.get('affected_counties_count')} affected counties found")


def check_hierarchy() -> None:
  res = tools.trace_place_hierarchy("beacon/team/01")
  record("PASS" if res.get("ancestors_found", 0) >= 3 else "FAIL",
         "trace_place_hierarchy walks from team through county to country/continent",
         f"{res.get('ancestors_found')} ancestors found")


def check_priority_counties() -> None:
  res = tools.find_priority_counties(top_n=5)
  record("PASS" if len(res) == 5 else "FAIL", "find_priority_counties returns top 5 unserved counties",
         f"top: {res[0]['county_name']} (score {res[0]['priority_score']}, {res[0]['recommended_action']})")
  if res:
    top = res[0]
    NUMBERS["priority_county_1_id"] = top["county_id"]
    NUMBERS["priority_county_1_name"] = top["county_name"]
    NUMBERS["priority_county_1_score"] = top["priority_score"]
    NUMBERS["priority_county_1_action"] = top["recommended_action"]
    NUMBERS["priority_county_1_rationale"] = top["rationale"]
    if len(res) > 1:
      NUMBERS["priority_county_2_name"] = res[1]["county_name"]
    if len(res) > 2:
      NUMBERS["priority_county_3_name"] = res[2]["county_name"]


def check_write() -> None:
  test_cid = "geoId/21193"  # Perry County, KY
  add_res = tools.add_to_deployment_plan(
      county_ids=[test_cid],
      action="Deploy Mobile Team",
      priority_tier="Tier 1 - Immediate",
      rationale="Automated validation test",
  )
  record("PASS" if add_res.get("status") == "success" else "FAIL",
         "add_to_deployment_plan writes row to Spanner", f"{add_res.get('counties_added')} rows")

  plan = tools.get_deployment_plan()
  found = any(r["county_id"] == test_cid for r in plan)
  record("PASS" if found else "FAIL", "get_deployment_plan reads back inserted row", f"{len(plan)} rows in plan")

  # Clean up test row
  db.execute_dml([("DELETE FROM DeploymentPlan WHERE county_id = @id", {"id": test_cid})])
  record("PASS", "Cleaned up DeploymentPlan test row")


def check_ca_queries() -> None:
  if not CA_QUERIES_FILE.exists():
    record("FAIL", "ca_agent/verified_queries.json exists")
    return
  queries = json.loads(CA_QUERIES_FILE.read_text())
  passed = 0
  for i, item in enumerate(queries, start=1):
    try:
      _ = q(item["sql"])
      passed += 1
    except Exception as e:
      record("FAIL", f"CA query #{i}: {item['question'][:45]}", str(e)[:200])
  record("PASS" if passed == len(queries) else "FAIL",
         f"All {len(queries)} Conversational Analytics verified queries execute cleanly", f"{passed}/{len(queries)} passed")


def check_dataset_summary() -> None:
  res = tools.describe_dataset()
  disclaimer = res.get("disclaimer", "")
  record("PASS" if "OpenFEMA" in disclaimer else "FAIL", "describe_dataset includes OpenFEMA disclaimer")


def main() -> None:
  ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
  ap.add_argument("--write-test", action="store_true", help="Run write-path tests.")
  ap.add_argument("--verbose", action="store_true", help="Print stack traces on failure.")
  args = ap.parse_args()
  global VERBOSE
  VERBOSE = args.verbose

  manifest_file = DATA_DIR / "load_manifest.json"
  manifest = read_json(manifest_file) if manifest_file.exists() else None
  story_file = PRIVATE_DIR / "story.json"
  story = read_json(story_file) if story_file.exists() else {}

  section("1. Row Counts")
  counts = run("row_counts", lambda: check_row_counts(manifest))

  if counts:
    section("2. Graph Integrity")
    run("graph", lambda: check_graph(counts))

  section("3. Agent Tools")
  run("pulse", lambda: check_pulse(story))
  run("compare_access", lambda: check_compare_access(story))
  run("repeat_counties", check_repeat_counties)
  run("disaster_history", check_disaster_history)
  run("hierarchy", check_hierarchy)
  run("priority_counties", check_priority_counties)

  if args.write_test:
    section("4. System of Action: Write Path")
    run("write_test", check_write)

  section("5. Conversational Analytics Queries")
  run("ca_queries", check_ca_queries)

  section("6. Dataset Catalog")
  run("dataset_summary", check_dataset_summary)

  write_json(DATA_DIR / "demo_numbers.json", {
      "verified_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
      "numbers": NUMBERS,
  })

  fails = [r for r in RESULTS if r[0] == "FAIL"]
  warns = [r for r in RESULTS if r[0] == "WARN"]
  passes = [r for r in RESULTS if r[0] == "PASS"]
  print(f"\nValidation Summary: {len(passes)} PASSED, {len(warns)} WARNINGS, {len(fails)} FAILED")
  if fails:
    sys.exit(1)


if __name__ == "__main__":
  main()
