"""Pulls the public slice of the Data Commons knowledge graph into data/public/.

Public sector slice:
  North America > United States > 4 Census regions > 9 Census divisions
  > 50 states + DC > ~3,100 counties
Statistical variables:
  - Population (Census PEP latest + 5-year prior)
  - Households (Census ACS 5-year)
  - Households with No Internet Access (Census ACS 5-year, S2801 / B28002)
  - Persons 65+ Years (Census ACS 5-year)
  - Persons with Disability (Census ACS 5-year, S1810)
  - Persons Below Poverty Level (Census ACS 5-year)
  - FEMA National Risk Index: composite risk, social vulnerability, community resilience,
    expected annual loss, riverine flooding, hurricane, wildfire risk (FEMA NRI)

Note: Households with No Vehicle (Count_Household_With0AvailableVehicles) is intentionally
held back from Spanner storage to serve as the live Data Commons MCP query in Beat 5.

Usage:
  python loader/fetch_public.py
"""

from __future__ import annotations

import argparse
import collections
import concurrent.futures
import csv
import datetime as dt
import gzip
import re

from common import DC_API_KEY, FIPS_TO_USPS, PUBLIC_DIR, require, write_json
from dc_api import DataCommons

COUNTY_EXPR = "country/USA<-containedInPlace+{typeOf:County}"
STATE_EXPR = "country/USA<-containedInPlace+{typeOf:State}"

POP = "Count_Person"
HH = "Count_Household"
NO_INTERNET = "Count_Household_NoInternetAccess"
AGE_65 = "Count_Person_65OrMoreYears"
DISABILITY = "Count_Person_WithDisability"
POVERTY = "Count_Person_BelowPovertyLevelInThePast12Months"

NRI_RISK = "FemaNaturalHazardRiskIndex_NaturalHazardImpact"
NRI_SOC_VULN = "FemaSocialVulnerability_NaturalHazardImpact"
NRI_RESIL = "FemaCommunityResilience_NaturalHazardImpact"
NRI_EAL = "Annual_ExpectedLoss_NaturalHazardImpact"
NRI_FLOOD = "FemaNaturalHazardRiskIndex_NaturalHazardImpact_RiverineFloodingEvent"
NRI_HURRICANE = "FemaNaturalHazardRiskIndex_NaturalHazardImpact_HurricaneEvent"
NRI_WILDFIRE = "FemaNaturalHazardRiskIndex_NaturalHazardImpact_WildfireEvent"

ACS_VARS = [HH, NO_INTERNET, AGE_65, DISABILITY, POVERTY]
NRI_VARS = [NRI_RISK, NRI_SOC_VULN, NRI_RESIL, NRI_EAL, NRI_FLOOD, NRI_HURRICANE, NRI_WILDFIRE]
ALL_VARS = [POP, *ACS_VARS, *NRI_VARS]

# Facet rules: prefer single consistent measurement method / unit per variable.
FACET_RULES = {
    POP: {"mm": "CensusPEPSurvey", "period": "P1Y"},
    **{v: {"mm": "CensusACS5yrSurvey"} for v in ACS_VARS},
    **{v: {"unit": "FemaNationalRiskScore"} for v in NRI_VARS if v != NRI_EAL},
    NRI_EAL: {"unit": "USDollar"},
}

SAMPLE = {
    "county": [
        "geoId/39049", "geoId/17031", "geoId/48201", "geoId/13121",
        "geoId/08031", "geoId/12086", "geoId/53033", "geoId/21013",
    ],
    "state": ["geoId/39", "geoId/17", "geoId/48", "geoId/13", "geoId/08", "geoId/12"],
    "country": ["country/USA"],
}


def pick_name(names: list[str]) -> str:
  names = [n for n in names if n]
  return min(names, key=len) if names else ""


def first_float(values: list) -> float | None:
  for v in values:
    try:
      return float(v)
    except (TypeError, ValueError):
      continue
  return None


def choose_facet(dc: DataCommons, variable: str, entities: list[str]) -> dict:
  """Chooses one facet for a variable at one geography level."""
  rows, facets = dc.observation([variable], entity_dcids=entities, date="LATEST")
  stats: dict[str, dict] = {}
  for ent, _, date, _, fid, *_ in rows:
    s = stats.setdefault(fid, {"entities": set(), "latest": ""})
    s["entities"].add(ent)
    s["latest"] = max(s["latest"], date or "")
  rule = FACET_RULES.get(variable, {})

  def ok(fid: str, strict: bool) -> bool:
    meta = facets.get(fid, {})
    mm = meta.get("measurementMethod") or ""
    if rule.get("mm") and (mm != rule["mm"] if strict else not mm.startswith(rule["mm"])):
      return False
    if rule.get("period") and meta.get("observationPeriod") != rule["period"]:
      return False
    if rule.get("unit") and meta.get("unit") != rule["unit"]:
      return False
    return True

  candidates = [f for f in stats if ok(f, True)] or [f for f in stats if ok(f, False)] or list(stats)
  if not candidates:
    raise RuntimeError(f"No data for {variable} at {entities[:3]}")
  best = max(candidates, key=lambda f: (len(stats[f]["entities"]), stats[f]["latest"]))
  return {"facet_id": best, "latest": stats[best]["latest"], **facets.get(best, {})}


def main() -> None:
  ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
  ap.add_argument("--workers", type=int, default=6)
  args = ap.parse_args()

  dc = DataCommons(require(DC_API_KEY, "DC_API_KEY"))
  PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

  # ---------------------------------------------------------------- places
  print("Fetching the place hierarchy ...")
  state_nodes = dc.children(["country/USA"], "State").get("country/USA", [])
  states = sorted({n["dcid"] for n in state_nodes
                   if re.fullmatch(r"geoId/\d{2}", n["dcid"]) and n["dcid"][6:] in FIPS_TO_USPS})
  state_vals = dc.node_values(states, ["name", "containedInPlace", "latitude", "longitude"])
  state_division: dict[str, str] = {}
  for s in states:
    divs = [d for d in state_vals[s]["containedInPlace"] if d and d.startswith("usc/") and d.endswith("Division")]
    if divs:
      state_division[s] = divs[0]
  divisions = sorted(set(state_division.values()))
  div_vals = dc.node_values(divisions, ["name", "containedInPlace"])
  division_region = {d: next((r for r in div_vals[d]["containedInPlace"] if r and r.endswith("Region")), None)
                     for d in divisions}
  regions = sorted({r for r in division_region.values() if r})
  region_vals = dc.node_values(regions + ["country/USA", "northamerica"], ["name"])

  county_nodes = dc.children(["country/USA"], "County").get("country/USA", [])
  counties = sorted({n["dcid"] for n in county_nodes
                     if re.fullmatch(r"geoId/\d{5}", n["dcid"]) and n["dcid"][6:8] in FIPS_TO_USPS})
  county_name = {n["dcid"]: n.get("name", "") for n in county_nodes}
  print(f"  {len(regions)} regions, {len(divisions)} divisions, {len(states)} states, "
        f"{len(counties)} candidate counties")
  county_vals = dc.node_values(counties, ["name", "latitude", "longitude"])

  # --------------------------------------------------------- stat var nodes
  sv_vals = dc.node_values(ALL_VARS, ["name", "description"])

  # ----------------------------------------------------------------- facets
  print("Choosing one facet per variable and geography level ...")
  chosen: dict[str, dict[str, dict]] = {}
  for level, sample in SAMPLE.items():
    chosen[level] = {}
    for v in ALL_VARS:
      try:
        chosen[level][v] = choose_facet(dc, v, sample)
      except RuntimeError as e:
        print(f"  ! {level} {v}: {e}")
    for v, f in chosen[level].items():
      print(f"  {level:7s} {v:55s} {f.get('measurementMethod')!s:28s} unit={f.get('unit')!s:18s} "
            f"latest={f['latest']}")

  # ----------------------------------------------------------- observations
  obs: dict[tuple, tuple] = {}  # (entity, var, date) -> (value, facet_id)

  def keep(rows, level: str) -> int:
    n = 0
    for ent, var, date, value, fid, *_ in rows:
      f = chosen[level].get(var)
      if f and fid == f["facet_id"] and value is not None and date:
        obs[(ent, var, date)] = (float(value), fid)
        n += 1
    return n

  def fetch(level: str, variables: list[str], date: str, expr=None, dcids=None) -> int:
    variables = [v for v in variables if v in chosen[level]]
    if not variables:
      return 0
    rows, _ = dc.observation(variables, entity_expression=expr, entity_dcids=dcids, date=date,
                             facet_ids=sorted({chosen[level][v]["facet_id"] for v in variables}))
    return keep(rows, level)

  targets = {
      "county": {"expr": COUNTY_EXPR},
      "state": {"expr": STATE_EXPR},
      "country": {"dcids": ["country/USA"]},
  }
  jobs = []
  for level, t in targets.items():
    # Fetch latest for all ACS and NRI variables
    vars_latest = [v for v in (ACS_VARS + NRI_VARS) if v in chosen[level]]
    if vars_latest:
      jobs.append((level, vars_latest, "LATEST", t))
    # For population, fetch latest and latest - 5 years for trend
    if POP in chosen[level]:
      latest_pop = int(chosen[level][POP]["latest"][:4])
      jobs.append((level, [POP], str(latest_pop), t))
      jobs.append((level, [POP], str(latest_pop - 5), t))

  print(f"Fetching observations in {len(jobs)} requests ...")
  with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
    futs = {pool.submit(fetch, lvl, vs, d, t.get("expr"), t.get("dcids")): (lvl, vs, d)
            for lvl, vs, d, t in jobs}
    done = 0
    for fut in concurrent.futures.as_completed(futs):
      fut.result()
      done += 1
      print(f"  completed {done}/{len(futs)} requests ({len(obs):,} observations collected)")

  latest_pop_c = chosen["county"][POP]["latest"][:4]
  current = {c for c in counties if (c, POP, latest_pop_c) in obs}
  dropped = sorted(set(counties) - current)
  if dropped:
    print(f"  dropped {len(dropped)} counties without {latest_pop_c} population")
  counties = sorted(current)

  # ----------------------------------------------------------------- write
  def lat_lng(vals):
    return first_float(vals.get("latitude", [])), first_float(vals.get("longitude", []))

  places = [
      {"subject_id": "northamerica", "label": "continent",
       "name": pick_name(region_vals.get("northamerica", {}).get("name", [])) or "North America"},
      {"subject_id": "country/USA", "label": "country", "name": "United States"},
  ]
  edges = [("country/USA", "containedinplace", "northamerica")]
  for r in regions:
    places.append({"subject_id": r, "label": "censusregion", "name": pick_name(region_vals[r]["name"])})
    edges.append((r, "containedinplace", "country/USA"))
  for d in divisions:
    places.append({"subject_id": d, "label": "censusdivision", "name": pick_name(div_vals[d]["name"])})
    if division_region.get(d):
      edges.append((d, "containedinplace", division_region[d]))
  for s in states:
    lat, lng = lat_lng(state_vals[s])
    code = FIPS_TO_USPS[s[6:]]
    name = pick_name(state_vals[s]["name"])
    places.append({"subject_id": s, "label": "state", "name": name, "display_name": name,
                   "state_code": code, "latitude": lat, "longitude": lng})
    edges.append((s, "containedinplace", "country/USA"))
    if state_division.get(s):
      edges.append((s, "containedinplace", state_division[s]))
  for c in counties:
    vals = county_vals.get(c, {})
    lat, lng = lat_lng(vals)
    code = FIPS_TO_USPS[c[6:8]]
    name = pick_name(vals.get("name", [])) or county_name.get(c, c)
    places.append({"subject_id": c, "label": "county", "name": name,
                   "display_name": f"{name}, {code}", "state_code": code,
                   "latitude": lat, "longitude": lng})
    edges.append((c, "containedinplace", f"geoId/{c[6:8]}"))
  for p in places:
    p.setdefault("display_name", p["name"])
  for v in ALL_VARS:
    places.append({"subject_id": v, "label": "statisticalvariable",
                   "name": pick_name(sv_vals.get(v, {}).get("name", [])) or v,
                   "display_name": pick_name(sv_vals.get(v, {}).get("name", [])) or v,
                   "description": (sv_vals.get(v, {}).get("description") or [""])[0]})

  place_cols = ["subject_id", "label", "name", "display_name", "state_code", "latitude",
                "longitude", "description"]
  with open(PUBLIC_DIR / "places.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=place_cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(places)

  with open(PUBLIC_DIR / "edges.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["subject_id", "predicate", "object_id"])
    w.writerows(sorted(set(edges)))

  keep_entities = set(counties) | set(states) | {"country/USA"}
  facet_meta = {f["facet_id"]: f for lvl in chosen.values() for f in lvl.values()}
  n_obs = 0
  with gzip.open(PUBLIC_DIR / "observations.csv.gz", "wt", newline="") as f:
    w = csv.writer(f)
    w.writerow(["observation_about", "variable_measured", "observation_date", "value",
                "measurement_method", "observation_period", "unit", "provenance_id", "provenance_url"])
    for (ent, var, date), (value, fid) in sorted(obs.items()):
      if ent not in keep_entities:
        continue
      m = facet_meta.get(fid, {})
      w.writerow([ent, var, date, value, m.get("measurementMethod", ""), m.get("observationPeriod", ""),
                  m.get("unit", ""), m.get("provenanceId") or m.get("importName", ""),
                  m.get("provenanceUrl", "")])
      n_obs += 1

  per_var = collections.Counter(var for (ent, var, _) in obs if ent in keep_entities)
  write_json(PUBLIC_DIR / "fetch_meta.json", {
      "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
      "api_calls": dc.calls,
      "counts": {"regions": len(regions), "divisions": len(divisions), "states": len(states),
                 "counties": len(counties), "observations": n_obs},
      "observations_per_variable": dict(per_var),
      "facets": chosen,
  })
  print(f"Done: {len(places):,} nodes, {len(set(edges)):,} edges, {n_obs:,} observations "
        f"in {dc.calls} API calls -> {PUBLIC_DIR}")


if __name__ == "__main__":
  main()
