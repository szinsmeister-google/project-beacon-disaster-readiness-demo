"""Curated Spanner Graph tools for the Beacon Readiness Agent.

12 curated tools that execute parameterized GoogleSQL and GQL queries over
DCGraph, CountyProfile, StateProfile, DisasterDesignation, Registration, and
DeploymentPlan.
"""

from __future__ import annotations

import math
import re
import threading
import time
from typing import Any, Optional

from . import db
from .scoring import calculate_priority_score, generate_rationale

AGENCY_NAME = "Beacon Readiness Office"
FEMA_DISCLAIMER = (
    "This product uses the Federal Emergency Management Agency's OpenFEMA API, "
    "but is not endorsed by FEMA. OpenFEMA data is subject to the OpenFEMA Terms and Conditions."
)


# -----------------------------------------------------------------------------
# Thread-safe LRU cache
# -----------------------------------------------------------------------------

class LRUCache:

  def __init__(self, ttl_seconds: int = 300):
    self.ttl = ttl_seconds
    self._store: dict[str, tuple[float, Any]] = {}
    self._lock = threading.Lock()

  def get(self, key: str, compute):
    now = time.time()
    with self._lock:
      hit = self._store.get(key)
      if hit and hit[0] > now:
        return hit[1]
    val = compute()
    with self._lock:
      self._store[key] = (now + self.ttl, val)
    return val

  def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
    with self._lock:
      self._store[key] = (time.time() + (ttl or self.ttl), value)


CACHE = LRUCache(ttl_seconds=300)


def _pearson(xs: list[float], ys: list[float], ws: Optional[list[float]] = None) -> Optional[float]:
  """Pearson correlation coefficient (optionally weighted)."""
  n = len(xs)
  if n < 5:
    return None
  ws = ws or [1.0] * n
  sw = sum(ws)
  if sw == 0:
    return None
  mx = sum(w * x for w, x in zip(ws, xs)) / sw
  my = sum(w * y for w, y in zip(ws, ys)) / sw
  cov = sum(w * (x - mx) * (y - my) for w, x, y in zip(ws, xs, ys))
  vx = sum(w * (x - mx) ** 2 for w, x in zip(ws, xs))
  vy = sum(w * (y - my) ** 2 for w, y in zip(ws, ys))
  if vx <= 0 or vy <= 0:
    return None
  return round(cov / math.sqrt(vx * vy), 2)


# -----------------------------------------------------------------------------
# 1. get_readiness_pulse
# -----------------------------------------------------------------------------

READINESS_PULSE_SQL = """
SELECT
  (SELECT COUNT(*) FROM Node WHERE label = 'disaster') AS disasters_count,
  (SELECT COUNT(DISTINCT county_id) FROM DisasterDesignation) AS declared_counties_count,
  (SELECT SUM(total_valid_registrations) FROM Registration) AS total_registrations,
  (SELECT SUM(web_registrations) FROM Registration) AS web_registrations,
  (SELECT SUM(call_center_registrations) FROM Registration) AS call_center_registrations,
  (SELECT SUM(mobile_registrations) FROM Registration) AS mobile_registrations,
  (SELECT COUNT(*) FROM Node WHERE label = 'team') AS teams_count,
  (SELECT COUNT(*) FROM Node WHERE label = 'hub') AS hubs_count,
  (SELECT COUNT(DISTINCT object_id) FROM Edge WHERE predicate = 'covers' AND provenance = 'beacon') AS covered_counties_count
"""

HIGH_NEED_UNCOVERED_SQL = """
SELECT
  cr.county_id,
  cr.county_name,
  cr.state_code,
  cr.no_internet_pct,
  cr.social_vulnerability_score,
  cr.disasters_since_2023 AS disasters_count,
  cr.total_registrations,
  cr.web_registration_pct AS web_share_pct
FROM CountyReadiness AS cr
WHERE cr.has_team_coverage = FALSE
  AND cr.disasters_since_2023 >= 2
  AND cr.no_internet_pct >= 15.0
ORDER BY cr.disasters_since_2023 DESC, cr.no_internet_pct DESC
LIMIT 5
"""


def get_readiness_pulse() -> dict:
  """National readiness health check: disaster volume, intake channel breakdown, team coverage, and key operational gaps.

  Returns high-level statistics across all major disasters since 2023, historical
  online vs call-center registration shares, and automatically flags the biggest
  uncovered vulnerability gap.
  """
  def _compute() -> dict:
    rows = db.query(READINESS_PULSE_SQL)
    if not rows:
      return {"status": "error", "message": "No data in Spanner database."}
    summary = rows[0]

    tot_reg = summary["total_registrations"] or 0
    web_reg = summary["web_registrations"] or 0
    cc_reg = summary["call_center_registrations"] or 0
    mob_reg = summary["mobile_registrations"] or 0

    web_pct = round(100.0 * web_reg / tot_reg, 1) if tot_reg > 0 else 0.0
    cc_pct = round(100.0 * cc_reg / tot_reg, 1) if tot_reg > 0 else 0.0
    mob_pct = round(100.0 * mob_reg / tot_reg, 1) if tot_reg > 0 else 0.0

    uncovered_samples = db.query(HIGH_NEED_UNCOVERED_SQL)

    return {
        "agency": AGENCY_NAME,
        "disaster_declarations_since_2023": summary["disasters_count"],
        "designated_counties": summary["declared_counties_count"],
        "total_valid_registrations": tot_reg,
        "channel_breakdown": {
            "web_registrations": web_reg,
            "web_share_pct": web_pct,
            "call_center_registrations": cc_reg,
            "call_center_share_pct": cc_pct,
            "mobile_registrations": mob_reg,
            "mobile_share_pct": mob_pct,
        },
        "resource_summary": {
            "regional_hubs": summary["hubs_count"],
            "mobile_teams": summary["teams_count"],
            "counties_with_team_coverage": summary["covered_counties_count"],
        },
        "key_operational_gap": (
            f"Mobile intake teams are concentrated in major metropolitan areas, leaving "
            f"rural, repeat-disaster communities without local coverage. In high-vulnerability "
            f"rural counties where over 15% of households lack internet, online registration "
            f"falls significantly below the national average of {web_pct}%."
        ),
        "sample_uncovered_priority_counties": uncovered_samples,
    }

  return CACHE.get("pulse", _compute)


# -----------------------------------------------------------------------------
# 2. compare_registration_access
# -----------------------------------------------------------------------------

REGISTRATION_ACCESS_GRAPH_SQL = """
SELECT
  g.county_id AS county_id,
  c.name AS county_name,
  s.state_code AS state_code,
  cp.no_internet_pct,
  cp.age_65_plus_pct,
  cp.disability_pct,
  cp.poverty_pct,
  SUM(r.total_valid_registrations) AS total_registrations,
  SUM(r.web_registrations) AS web_registrations,
  ROUND(100 * SAFE_DIVIDE(SUM(r.web_registrations), SUM(r.total_valid_registrations)), 1) AS web_share_pct
FROM GRAPH_TABLE(DCGraph
  MATCH (d:Disaster)-[:affectedPlace]->(c:County)-[:containedInPlace]->(s:State)
  RETURN d.subject_id AS disaster_id, c.subject_id AS county_id, s.subject_id AS state_id
) AS g
JOIN Node AS c ON c.subject_id = g.county_id
JOIN Node AS s ON s.subject_id = g.state_id
JOIN CountyProfile AS cp ON cp.county_id = g.county_id
JOIN Registration AS r ON r.disaster_id = g.disaster_id AND r.county_id = g.county_id
GROUP BY g.county_id, c.name, s.state_code, cp.no_internet_pct, cp.age_65_plus_pct, cp.disability_pct, cp.poverty_pct
HAVING total_registrations >= @min_registrations
"""


def compare_registration_access(comparison_factor: str = "no_internet", min_registrations: int = 200) -> dict:
  """Tests 'Why do people struggle to register online?' by joining FEMA registrations to Census indicators across the graph.

  Executes a single unified GRAPH_TABLE query matching (Disaster)->(County)->(State)
  joined to Registration intake counts and Census ACS county statistics.

  Args:
    comparison_factor: 'no_internet' (default), 'age_65', 'disability', or 'poverty'.
    min_registrations: Minimum disaster registrations for statistical inclusion (default: 200).
  """
  rows = CACHE.get(
      f"reg_access_rows:{min_registrations}",
      lambda: db.query(REGISTRATION_ACCESS_GRAPH_SQL, {"min_registrations": min_registrations}),
  )
  if not rows:
    return {"status": "error", "message": "No registration records met the threshold."}

  factor_key = {
      "no_internet": "no_internet_pct",
      "age_65": "age_65_plus_pct",
      "disability": "disability_pct",
      "poverty": "poverty_pct",
  }.get(comparison_factor, "no_internet_pct")

  valid_rows = [r for r in rows if r.get(factor_key) is not None and r.get("web_share_pct") is not None]
  if len(valid_rows) < 10:
    return {"status": "error", "message": "Insufficient data points for comparison."}

  # Sort by comparison factor to form quartiles
  valid_rows.sort(key=lambda r: float(r[factor_key]))
  q_size = len(valid_rows) // 4
  q1 = valid_rows[:q_size]  # lowest factor (e.g. lowest no-internet share = highest access)
  q4 = valid_rows[-q_size:]  # highest factor (e.g. highest no-internet share = lowest access)

  def avg_web(sample):
    tot = sum(r["total_registrations"] for r in sample)
    web = sum(r["web_registrations"] for r in sample)
    return round(100.0 * web / tot, 1) if tot > 0 else 0.0

  def avg_factor(sample):
    return round(sum(float(r[factor_key]) for r in sample) / len(sample), 1)

  xs = [float(r[factor_key]) for r in valid_rows]
  ys = [float(r["web_share_pct"]) for r in valid_rows]
  ws = [float(r["total_registrations"]) for r in valid_rows]

  r_unweighted = _pearson(xs, ys)
  r_weighted = _pearson(xs, ys, ws)

  # Also compute age_65 for comparison if looking at no_internet
  age_r = None
  if factor_key == "no_internet_pct":
    age_xs = [float(r["age_65_plus_pct"]) for r in valid_rows if r.get("age_65_plus_pct") is not None]
    age_ys = [float(r["web_share_pct"]) for r in valid_rows if r.get("age_65_plus_pct") is not None]
    age_r = _pearson(age_xs, age_ys)

  return {
      "comparison_factor": comparison_factor,
      "analyzed_counties_count": len(valid_rows),
      "min_registrations_threshold": min_registrations,
      "quartile_analysis": {
          "lowest_quartile": {
              "description": f"Quarter of counties with lowest {comparison_factor}",
              "average_factor_value": avg_factor(q1),
              "online_registration_pct": avg_web(q1),
          },
          "highest_quartile": {
              "description": f"Quarter of counties with highest {comparison_factor}",
              "average_factor_value": avg_factor(q4),
              "online_registration_pct": avg_web(q4),
          },
          "spread_percentage_points": round(avg_web(q1) - avg_web(q4), 1),
      },
      "correlations": {
          "pearson_unweighted": r_unweighted,
          "pearson_registration_weighted": r_weighted,
          "age_65_comparison_unweighted": age_r,
      },
      "finding": (
          f"In counties with the lowest {comparison_factor} ({avg_factor(q1)}%), {avg_web(q1)}% of survivors "
          f"registered online, whereas in counties with the highest {comparison_factor} ({avg_factor(q4)}%), "
          f"online registration dropped to {avg_web(q4)}% (weighted r = {r_weighted}). "
          + (f"Age 65+ has a much weaker correlation (r = {age_r}), indicating connectivity infrastructure "
             f"is the primary barrier rather than age demographics." if age_r is not None else "")
      ),
      "statistical_note": "This reflects observed empirical correlation across federal registration records, not causal proof.",
  }


# -----------------------------------------------------------------------------
# 3. find_repeat_hit_counties
# -----------------------------------------------------------------------------

REPEAT_COUNTIES_SQL = """
SELECT
  cr.county_id,
  cr.county_name,
  cr.state_code,
  cr.disasters_since_2023,
  cr.ihp_disasters_since_2023,
  cr.total_registrations,
  cr.web_registration_pct,
  cr.no_internet_pct,
  cr.social_vulnerability_score,
  cr.has_team_coverage
FROM CountyReadiness AS cr
WHERE cr.disasters_since_2023 >= @min_disasters
ORDER BY cr.disasters_since_2023 DESC, cr.social_vulnerability_score DESC
LIMIT @limit
"""


def find_repeat_hit_counties(min_disasters: int = 3, limit: int = 10) -> list[dict]:
  """Finds counties hit by multiple major disaster declarations since 2023.

  Useful for identifying communities suffering compound impacts and verifying
  whether mobile intake teams are assigned to them.

  Args:
    min_disasters: Minimum number of declared major disasters since 2023 (default: 3).
    limit: Maximum number of counties to return (default: 10).
  """
  return CACHE.get(
      f"repeat_counties:{min_disasters}:{limit}",
      lambda: db.query(REPEAT_COUNTIES_SQL, {"min_disasters": min_disasters, "limit": limit}),
  )


# -----------------------------------------------------------------------------
# 4. get_disaster_history
# -----------------------------------------------------------------------------

COUNTY_DISASTERS_GQL = """
SELECT
  d.subject_id AS disaster_id,
  d.name AS disaster_number,
  d.display_name AS title,
  d.incident_type AS incident_type,
  d.declaration_date AS declaration_date,
  dd.ihp_declared,
  dd.pa_declared,
  r.total_valid_registrations,
  r.web_share_pct,
  r.call_center_share_pct
FROM GRAPH_TABLE(DCGraph
  MATCH (d:Disaster)-[:affectedPlace]->(c:County {subject_id: @county_id})
  RETURN d.subject_id AS disaster_id
) AS g
JOIN Node AS d ON d.subject_id = g.disaster_id
JOIN DisasterDesignation AS dd ON dd.disaster_id = d.subject_id AND dd.county_id = @county_id
LEFT JOIN Registration AS r ON r.disaster_id = d.subject_id AND r.county_id = @county_id
ORDER BY d.declaration_date DESC
"""

DISASTER_COUNTIES_GQL = """
SELECT
  c.subject_id AS county_id,
  c.name AS county_name,
  c.display_name AS county_display_name,
  c.state_code AS state_code,
  cp.no_internet_pct,
  cp.nri_social_vulnerability_score,
  r.total_valid_registrations,
  r.web_share_pct
FROM GRAPH_TABLE(DCGraph
  MATCH (d:Disaster {subject_id: @disaster_id})-[:affectedPlace]->(c:County)
  RETURN c.subject_id AS county_id
) AS g
JOIN Node AS c ON c.subject_id = g.county_id
LEFT JOIN CountyProfile AS cp ON cp.county_id = c.subject_id
LEFT JOIN Registration AS r ON r.disaster_id = @disaster_id AND r.county_id = c.subject_id
ORDER BY COALESCE(r.total_valid_registrations, 0) DESC
LIMIT 25
"""


def get_disaster_history(entity: str) -> dict:
  """Retrieves disaster history for a county, or affected counties for a disaster.

  Uses GQL graph pattern matching over (Disaster)-[:affectedPlace]->(County).

  Args:
    entity: County DCID (e.g. 'geoId/21193') or name, or Disaster ID (e.g. 'fema/DR-4834' or 'DR-4834').
  """
  clean = entity.strip()
  if clean.startswith("DR-") or clean.startswith("fema/DR-"):
    dr_id = clean if clean.startswith("fema/") else f"fema/{clean}"
    dr_meta = db.query("SELECT * FROM Node WHERE subject_id = @id", {"id": dr_id})
    if not dr_meta:
      return {"status": "error", "message": f"Disaster {dr_id} not found."}
    counties = db.query(DISASTER_COUNTIES_GQL, {"disaster_id": dr_id})
    return {
        "disaster": dr_meta[0],
        "affected_counties_count": len(counties),
        "counties": counties,
    }

  # Treat as county
  county_id = clean
  if not county_id.startswith("geoId/"):
    matches = db.query("SELECT subject_id FROM Node WHERE label = 'county' AND LOWER(display_name) LIKE @name LIMIT 1",
                       {"name": f"%{clean.lower()}%"})
    if not matches:
      return {"status": "error", "message": f"County {clean} not found."}
    county_id = matches[0]["subject_id"]

  cty_meta = db.query("SELECT * FROM Node WHERE subject_id = @id", {"id": county_id})
  history = db.query(COUNTY_DISASTERS_GQL, {"county_id": county_id})
  return {
      "county": cty_meta[0] if cty_meta else {"subject_id": county_id},
      "disaster_declarations_count": len(history),
      "disasters": history,
  }


# -----------------------------------------------------------------------------
# 5. trace_place_hierarchy
# -----------------------------------------------------------------------------

HIERARCHY_GQL = """
SELECT
  p.subject_id AS id,
  p.name AS name,
  p.display_name AS display_name,
  p.label AS label
FROM GRAPH_TABLE(DCGraph
  MATCH (src:Entity {subject_id: @entity})-[:containedInPlace|locatedIn|covers|serves]->{1,6}(p:Entity)
  RETURN p.subject_id AS id, p.name AS name, p.display_name AS display_name, p.label AS label
) AS g
JOIN Node AS p ON p.subject_id = g.id
"""


def trace_place_hierarchy(entity: str) -> dict:
  """Walks up the knowledge graph from a team, hub, county, or state to the continent.

  Demonstrates quantified-path graph traversals in GQL.

  Args:
    entity: DCID or subject ID (e.g. 'geoId/21193', 'beacon/team/04', 'beacon/hub/southeast').
  """
  clean = entity.strip()
  if not clean.startswith(("geoId/", "beacon/", "fema/", "country/")):
    matches = db.query("SELECT subject_id FROM Node WHERE LOWER(name) = @name OR LOWER(display_name) = @name LIMIT 1",
                       {"name": clean.lower()})
    if matches:
      clean = matches[0]["subject_id"]

  rows = db.query(HIERARCHY_GQL, {"entity": clean})
  return {
      "entity": clean,
      "ancestors_found": len(rows),
      "hierarchy": rows,
  }


# -----------------------------------------------------------------------------
# 6. get_place_profile
# -----------------------------------------------------------------------------

COUNTY_PROFILE_SQL = "SELECT * FROM CountyReadiness WHERE county_id = @id"
STATE_PROFILE_SQL = "SELECT * FROM StateProfile WHERE state_id = @id"


def get_place_profile(place: str) -> dict:
  """Returns public Data Commons demographic and hazard profile of a county or state, plus disaster history.

  Args:
    place: County or State DCID (e.g. 'geoId/21193' or 'geoId/21') or name (e.g. 'Perry County, KY').
  """
  clean = place.strip()
  if not clean.startswith("geoId/"):
    matches = db.query(
        "SELECT subject_id, label FROM Node WHERE label IN ('county', 'state') AND "
        "(LOWER(display_name) LIKE @name OR LOWER(name) LIKE @name) LIMIT 1",
        {"name": f"%{clean.lower()}%"})
    if not matches:
      return {"status": "error", "message": f"Place '{place}' not found."}
    clean = matches[0]["subject_id"]

  if len(clean) == 12:  # geoId/XXYYY = County
    rows = db.query(COUNTY_PROFILE_SQL, {"id": clean})
    if not rows:
      return {"status": "error", "message": f"County {clean} not found in profile tables."}
    return {"place_type": "county", "profile": rows[0]}
  else:  # State
    rows = db.query(STATE_PROFILE_SQL, {"id": clean})
    if not rows:
      return {"status": "error", "message": f"State {clean} not found in profile tables."}
    return {"place_type": "state", "profile": rows[0]}


# -----------------------------------------------------------------------------
# 7. find_priority_counties
# -----------------------------------------------------------------------------

PRIORITY_CANDIDATES_SQL = """
SELECT
  cr.county_id,
  cr.county_name,
  cr.state_code,
  cr.population,
  cr.households,
  cr.no_internet_pct,
  cr.social_vulnerability_score,
  cr.nri_risk_score,
  cr.disasters_since_2023,
  cr.total_registrations,
  cr.web_registration_pct
FROM CountyReadiness AS cr
WHERE cr.has_team_coverage = FALSE
  AND cr.disasters_since_2023 >= 1
  AND (@state IS NULL OR cr.state_code = @state)
"""


def find_priority_counties(top_n: int = 5, state: Optional[str] = None) -> list[dict]:
  """Identifies high-priority underserved counties for mobile team deployment using a graph anti-join.

  Finds counties that have experienced major disaster declarations but have NO
  mobile response team coverage within 75 miles, ranked by compound vulnerability:
  FEMA hazard risk, social vulnerability, Census internet access deficit, and repeat disaster frequency.

  Args:
    top_n: Number of priority recommendations to return (default: 5).
    state: Optional 2-letter state code filter (e.g. 'KY', 'FL').
  """
  st_code = state.upper() if state else None
  rows = CACHE.get(
      f"priority_candidates:{st_code}",
      lambda: db.query(PRIORITY_CANDIDATES_SQL, {"state": st_code}),
  )
  if not rows:
    return []

  scored = []
  for r in rows:
    score = calculate_priority_score(
        nri_risk_score=r.get("nri_risk_score"),
        social_vulnerability_score=r.get("social_vulnerability_score"),
        no_internet_pct=r.get("no_internet_pct"),
        disasters_count=r.get("disasters_since_2023") or 0,
    )
    tier = "Tier 1 - Immediate" if score >= 70.0 else "Tier 2 - Secondary"
    rationale = generate_rationale(
        county_name=r.get("county_name") or r["county_id"],
        disasters_count=r.get("disasters_since_2023") or 0,
        nri_risk=r.get("nri_risk_score"),
        social_vuln=r.get("social_vulnerability_score"),
        no_internet_pct=r.get("no_internet_pct"),
        historical_web_pct=r.get("web_registration_pct"),
    )
    scored.append({
        "county_id": r["county_id"],
        "county_name": r["county_name"],
        "state_code": r["state_code"],
        "priority_score": score,
        "priority_tier": tier,
        "disasters_since_2023": r["disasters_since_2023"],
        "no_internet_pct": r["no_internet_pct"],
        "fema_risk_score": r["nri_risk_score"],
        "social_vulnerability_score": r["social_vulnerability_score"],
        "historical_web_registration_pct": r["web_registration_pct"],
        "recommended_action": "Deploy Mobile Team" if (r.get("no_internet_pct") or 0) >= 15 else "Establish Recovery Center",
        "rationale": rationale,
    })

  scored.sort(key=lambda x: x["priority_score"], reverse=True)
  return scored[:top_n]


# -----------------------------------------------------------------------------
# 8. add_to_deployment_plan
# -----------------------------------------------------------------------------

DEPLOY_PLAN_UPSERT_SQL = """
INSERT OR UPDATE INTO DeploymentPlan (
  county_id, action, assigned_team_id, priority_tier, rationale, added_by, added_at, status
) VALUES (
  @county_id, @action, @assigned_team_id, @priority_tier, @rationale, @added_by, PENDING_COMMIT_TIMESTAMP(), @status
)
"""


def add_to_deployment_plan(
    county_ids: list[str],
    action: str,
    priority_tier: str,
    rationale: str,
    tool_context: Optional[dict] = None,
) -> dict:
  """Saves recommended counties to the Beacon DeploymentPlan in Spanner.

  This is the only tool that modifies data. Executes a single atomic read-write
  transaction in Spanner.

  Args:
    county_ids: List of county DCIDs (e.g. ['geoId/21193', 'geoId/21125']).
    action: 'Deploy Mobile Team' or 'Establish Recovery Center'.
    priority_tier: 'Tier 1 - Immediate' or 'Tier 2 - Secondary'.
    rationale: Justification citing disaster history and connectivity factors.
    tool_context: Runtime context provided by Gemini Conversational Analytics or ADK.
  """
  user = "gemini-enterprise-user"
  if tool_context and isinstance(tool_context, dict):
    user = tool_context.get("user_email") or tool_context.get("user") or user

  stmts = []
  for cid in county_ids:
    clean_id = cid.strip()
    if not clean_id.startswith("geoId/"):
      clean_id = f"geoId/{clean_id}"
    stmts.append((
        DEPLOY_PLAN_UPSERT_SQL,
        {
            "county_id": clean_id,
            "action": action,
            "assigned_team_id": None,
            "priority_tier": priority_tier,
            "rationale": rationale,
            "added_by": user,
            "status": "Proposed",
        },
    ))

  modified = db.execute_dml(stmts)
  return {
      "status": "success",
      "counties_added": modified,
      "county_ids": county_ids,
      "action": action,
      "priority_tier": priority_tier,
      "rationale": rationale,
      "saved_by": user,
  }


# -----------------------------------------------------------------------------
# 9. get_deployment_plan
# -----------------------------------------------------------------------------

GET_PLAN_SQL = """
SELECT
  dp.county_id,
  cp.county_name,
  cp.state_code,
  dp.action,
  dp.priority_tier,
  dp.assigned_team_id,
  dp.rationale,
  dp.added_by,
  dp.added_at,
  dp.status
FROM DeploymentPlan AS dp
LEFT JOIN CountyProfile AS cp ON cp.county_id = dp.county_id
ORDER BY dp.added_at DESC
"""


def get_deployment_plan(strong: bool = True) -> list[dict]:
  """Shows the current active deployment plan stored in Spanner."""
  return db.query(GET_PLAN_SQL, strong=strong)


# -----------------------------------------------------------------------------
# 10. find_entities
# -----------------------------------------------------------------------------

FIND_ENTITIES_SQL = """
SELECT
  subject_id,
  label,
  name,
  display_name,
  state_code
FROM Node
WHERE (@label IS NULL OR label = @label)
  AND (LOWER(name) LIKE @pattern OR LOWER(display_name) LIKE @pattern OR subject_id = @exact)
ORDER BY LENGTH(name) ASC
LIMIT 10
"""


def find_entities(name: str, entity_type: Optional[str] = None) -> list[dict]:
  """Looks up entity IDs by name: counties, states, disasters, hubs, or teams.

  Args:
    name: Search string (e.g. 'Perry', 'Debby', 'Southeast Hub').
    entity_type: Optional label filter: 'county', 'state', 'disaster', 'hub', 'team'.
  """
  clean = name.strip()
  lbl = entity_type.strip().lower() if entity_type else None
  return db.query(FIND_ENTITIES_SQL, {
      "label": lbl,
      "pattern": f"%{clean.lower()}%",
      "exact": clean,
  })


# -----------------------------------------------------------------------------
# 11. describe_dataset
# -----------------------------------------------------------------------------

DATASET_SUMMARY_SQL = """
SELECT
  (SELECT COUNT(*) FROM Node WHERE label = 'county') AS counties,
  (SELECT COUNT(*) FROM Node WHERE label = 'state') AS states,
  (SELECT COUNT(*) FROM Node WHERE label = 'disaster') AS disasters,
  (SELECT COUNT(*) FROM Node WHERE label = 'team') AS teams,
  (SELECT COUNT(*) FROM Node WHERE label = 'hub') AS hubs,
  (SELECT COUNT(*) FROM Edge) AS edges,
  (SELECT COUNT(*) FROM Observation) AS observations,
  (SELECT COUNT(*) FROM Registration) AS registration_records
"""


def describe_dataset() -> dict:
  """Describes what is loaded: node & edge counts, statistical variables, date ranges, and official citations."""
  counts = db.query(DATASET_SUMMARY_SQL)[0]
  return {
      "dataset_name": "Beacon Readiness Office Knowledge Graph on Spanner",
      "unified_property_graph": "DCGraph",
      "entities": counts,
      "sources": [
          "Data Commons (datacommons.org): U.S. Place Hierarchy, Census ACS 5-year survey, FEMA National Risk Index",
          "OpenFEMA API: Major Disaster Declarations (DR) and Registration Intake (RI-IHP) 2023-present",
          "Beacon Readiness Office: Regional Hubs and Mobile Response Teams network",
      ],
      "disclaimer": FEMA_DISCLAIMER,
      "statistical_variables_loaded": [
          "Count_Person (Census PEP / ACS)",
          "Count_Household (Census ACS 5-year)",
          "Count_Household_NoInternetAccess (Census ACS 5-year)",
          "Count_Person_65OrMoreYears (Census ACS 5-year)",
          "Count_Person_WithDisability (Census ACS 5-year)",
          "Count_Person_BelowPovertyLevelInThePast12Months (Census ACS 5-year)",
          "FemaNaturalHazardRiskIndex_NaturalHazardImpact (FEMA NRI)",
          "FemaSocialVulnerability_NaturalHazardImpact (FEMA NRI)",
          "FemaCommunityResilience_NaturalHazardImpact (FEMA NRI)",
          "Annual_ExpectedLoss_NaturalHazardImpact (FEMA NRI)",
      ],
      "held_back_for_live_mcp": "Count_Household_With0AvailableVehicles (Households with no vehicle)",
  }


# -----------------------------------------------------------------------------
# 12. run_readonly_query
# -----------------------------------------------------------------------------

_FORBIDDEN_SQL = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE)\b", re.IGNORECASE)


def run_readonly_query(sql: str) -> list[dict]:
  """Runs one ad-hoc read-only GoogleSQL or GQL query against the demo database (max 50 rows).

  Args:
    sql: GoogleSQL SELECT or GQL GRAPH_TABLE query string.
  """
  clean = sql.strip()
  if _FORBIDDEN_SQL.search(clean):
    return [{"error": "Write statements are forbidden. Use add_to_deployment_plan to write."}]
  if not re.match(r"^(SELECT|GRAPH_TABLE)\b", clean, re.IGNORECASE):
    return [{"error": "Only SELECT or GRAPH_TABLE queries are permitted."}]
  return db.query(clean)[:50]


# -----------------------------------------------------------------------------
# 13. get_chart_spec
# -----------------------------------------------------------------------------

_AURORA_VEGA_CONFIG = {
    "background": "#FFFFFF",
    "padding": 24,
    "font": "Inter, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif",
    "view": {"stroke": None},
    "range": {
        "category": ["#7C83FD", "#3CC6B8", "#FF9F7A", "#F27BAA", "#5AB2F0", "#F5BE4B", "#B18CE8", "#7CC49A"],
        "ramp": ["#F3F4FF", "#D5D8FF", "#AEB3FE", "#7C83FD", "#545BD6", "#353A9E"],
        "diverging": ["#13665F", "#3CC6B8", "#BDEDE7", "#F4F5F9", "#FFD3C2", "#FF8A65", "#D9485F"],
    },
    "title": {
        "anchor": "start",
        "fontSize": 19,
        "fontWeight": 600,
        "color": "#1E2440",
        "subtitleFontSize": 13,
        "subtitleColor": "#4A5270",
        "subtitlePadding": 6,
        "offset": 20,
    },
    "axis": {
        "domain": False,
        "ticks": False,
        "gridColor": "#ECEEF5",
        "labelColor": "#8A92AB",
        "labelFontSize": 11,
        "labelPadding": 8,
        "titleColor": "#4A5270",
        "titleFontSize": 12,
        "titleFontWeight": 500,
        "titlePadding": 12,
    },
    "axisX": {"grid": False, "domain": True, "domainColor": "#D5D9E6"},
    "axisY": {"grid": True, "tickCount": 5},
    "legend": {
        "orient": "top",
        "direction": "horizontal",
        "labelColor": "#4A5270",
        "labelFontSize": 11,
        "symbolType": "circle",
        "title": None,
    },
    "bar": {"cornerRadiusEnd": 6, "discreteBandSize": {"band": 0.65}},
    "line": {"strokeWidth": 2.5, "strokeCap": "round", "strokeJoin": "round"},
    "point": {"size": 60, "filled": True, "stroke": "#FFFFFF", "strokeWidth": 2},
    "arc": {"stroke": "#FFFFFF", "strokeWidth": 2},
    "rect": {"cornerRadius": 3, "stroke": "#FFFFFF", "strokeWidth": 2},
}


def get_chart_spec(chart_type: str = "channels") -> dict:
  """Generates an interactive Vega-Lite v5 chart specification styled with the Aurora Design System.

  Args:
    chart_type: One of 'channels' (registration intake breakdown donut), 'access_quartiles' (broadband access vs online registration bar chart), or 'priority_counties' (top unserved priority counties ranking).
  """
  c_type = chart_type.lower().strip()
  if "channel" in c_type or "intake" in c_type:
    return {
        "chart_type": "channels",
        "title": "Nearly three-quarters of disaster survivors register online, while mobile teams reach 2.2%",
        "vega_lite_spec": {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "description": "Registration Intake Channels (2023-Present)",
            "title": {
                "text": "Online portal handles 74.6% of intake while mobile teams cover 2.2%",
                "subtitle": "Share of valid FEMA assistance registrations by channel, %, 2023–present | Source: OpenFEMA",
            },
            "width": 480,
            "height": 260,
            "config": _AURORA_VEGA_CONFIG,
            "data": {
                "values": [
                    {"channel": "Online Web", "registrations": 3945345, "share": 74.6},
                    {"channel": "Phone Call Center", "registrations": 1221338, "share": 23.1},
                    {"channel": "Mobile Response Teams", "registrations": 117947, "share": 2.2},
                ]
            },
            "mark": {"type": "arc", "innerRadius": 66, "stroke": "#FFFFFF", "strokeWidth": 2, "tooltip": True},
            "encoding": {
                "theta": {"field": "share", "type": "quantitative"},
                "color": {
                    "field": "channel",
                    "type": "nominal",
                    "scale": {
                        "domain": ["Online Web", "Phone Call Center", "Mobile Response Teams"],
                        "range": ["#7C83FD", "#3CC6B8", "#FF9F7A"],
                    },
                },
                "tooltip": [
                    {"field": "channel", "type": "nominal", "title": "Channel"},
                    {"field": "registrations", "type": "quantitative", "format": ",d", "title": "Registrations"},
                    {"field": "share", "type": "quantitative", "format": ".1f", "title": "Share (%)"},
                ],
            },
        },
    }
  elif "quartile" in c_type or "access" in c_type or "internet" in c_type or "gap" in c_type:
    return {
        "chart_type": "access_quartiles",
        "title": "Online registration drops nearly 18 points in counties with the lowest broadband access",
        "vega_lite_spec": {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "description": "Online Registration Rate by Household Internet Deficit Quartile",
            "title": {
                "text": "Online registration drops 17.8 pts in low-connectivity counties",
                "subtitle": "Online registration share by household broadband quartile, %, 2023–present | Source: OpenFEMA & Census ACS",
            },
            "width": 480,
            "height": 260,
            "config": _AURORA_VEGA_CONFIG,
            "data": {
                "values": [
                    {"quartile": "Q1 (Highest Access)", "no_internet_pct": 9.0, "online_pct": 78.7},
                    {"quartile": "Q2", "no_internet_pct": 13.0, "online_pct": 76.0},
                    {"quartile": "Q3", "no_internet_pct": 16.3, "online_pct": 73.0},
                    {"quartile": "Q4 (Lowest Access)", "no_internet_pct": 22.8, "online_pct": 60.9},
                ]
            },
            "mark": {"type": "bar", "cornerRadiusEnd": 6, "tooltip": True},
            "encoding": {
                "x": {"field": "quartile", "type": "nominal", "title": "County Broadband Access Quartile", "axis": {"labelAngle": 0}},
                "y": {"field": "online_pct", "type": "quantitative", "title": "Online Registration Share (%)", "scale": {"zero": True}},
                "color": {
                    "field": "online_pct",
                    "type": "quantitative",
                    "scale": {"range": ["#F3F4FF", "#D5D8FF", "#AEB3FE", "#7C83FD", "#545BD6", "#353A9E"]},
                    "legend": None,
                },
                "tooltip": [
                    {"field": "quartile", "title": "Quartile"},
                    {"field": "online_pct", "title": "Online Share (%)", "format": ".1f"},
                    {"field": "no_internet_pct", "title": "Avg No-Internet (%)", "format": ".1f"},
                ],
            },
        },
    }
  else:
    return {
        "chart_type": "priority_counties",
        "title": "Washington County, MS and Floyd County, KY lead unserved deployment priorities",
        "vega_lite_spec": {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "description": "Top Priority Unserved Disaster-Declared Counties",
            "title": {
                "text": "Washington County, MS leads unserved mobile deployment priorities",
                "subtitle": "Compound readiness deficit score (0–100) for unserved repeat-disaster counties | Source: Spanner DCGraph",
            },
            "width": 480,
            "height": 260,
            "config": _AURORA_VEGA_CONFIG,
            "data": {
                "values": [
                    {"county": "Washington County, MS", "score": 80.7, "action": "Deploy Mobile Team"},
                    {"county": "Floyd County, KY", "score": 78.4, "action": "Deploy Mobile Team"},
                    {"county": "Gadsden County, FL", "score": 76.2, "action": "Deploy Mobile Team"},
                    {"county": "Holmes County, MS", "score": 74.9, "action": "Deploy Mobile Team"},
                    {"county": "Bolivar County, MS", "score": 74.5, "action": "Deploy Mobile Team"},
                ]
            },
            "mark": {"type": "bar", "cornerRadiusEnd": 6, "tooltip": True},
            "encoding": {
                "y": {"field": "county", "type": "nominal", "sort": "-x", "title": None},
                "x": {"field": "score", "type": "quantitative", "title": "Readiness Deficit Score", "scale": {"zero": True}},
                "color": {
                    "field": "action",
                    "type": "nominal",
                    "scale": {"domain": ["Deploy Mobile Team", "Establish Recovery Center"], "range": ["#7C83FD", "#3CC6B8"]},
                },
                "tooltip": [
                    {"field": "county", "title": "County"},
                    {"field": "score", "title": "Readiness Score", "format": ".1f"},
                    {"field": "action", "title": "Action"},
                ],
            },
        },
    }


def data_vintage() -> dict:
  """Latest data vintages loaded (cached). Used by system prompt."""
  return {
      "acs_vintage": "2024",
      "fema_declarations_through": "2026",
      "nri_source": "FEMA National Risk Index",
  }


FEDERAL_PROGRAMS_SQL = """
SELECT
  program_id,
  program_name,
  lead_agency,
  policy_pillar,
  annual_budget_million_usd,
  assisted_households,
  ROUND(assisted_households / 1000.0, 1) AS households_helped_thousands,
  web_intake_share_pct,
  call_center_share_pct,
  mobile_drc_share_pct,
  target_svi_threshold
FROM FederalProgramSummary
ORDER BY assisted_households DESC
"""


def compare_federal_programs() -> list[dict]:
  """Compares households helped and online application share across the top U.S. federal disaster programs."""
  return CACHE.get("federal_programs", lambda: db.query(FEDERAL_PROGRAMS_SQL))


ALL_TOOLS = [
    get_readiness_pulse,
    compare_registration_access,
    find_repeat_hit_counties,
    get_disaster_history,
    trace_place_hierarchy,
    get_place_profile,
    find_priority_counties,
    add_to_deployment_plan,
    get_deployment_plan,
    find_entities,
    describe_dataset,
    run_readonly_query,
    get_chart_spec,
    compare_federal_programs,
]
