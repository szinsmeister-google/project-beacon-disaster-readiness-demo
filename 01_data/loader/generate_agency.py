"""Generates synthetic agency infrastructure (hubs, mobile teams, coverage areas).

Storyline B: Beacon Readiness Office
Generates:
  - 6 Regional Hubs covering all 50 states + DC
  - ~38 Mobile Response Teams based in major metro centers of high-disaster states
  - Coverage edges: each team covers counties within 75 miles of its base county
  - System of Action initial state: DeploymentPlan table

Outputs in data/private/:
  - agency_nodes.csv (Hub and Team nodes)
  - agency_edges.csv (locatedIn, covers, serves edges)
  - deployment_plan.csv (Initial deployment plan)
  - agency_manifest.json (Summary of generated agency resources)

Usage:
  python loader/generate_agency.py
"""

from __future__ import annotations

import csv
import datetime as dt
import math

import pandas as pd

from common import (
    AGENCY_PROVENANCE,
    FIPS_TO_USPS,
    PRIVATE_DIR,
    PUBLIC_DIR,
    USPS_TO_FIPS,
    write_json,
)

# 6 Regional Hubs
HUBS = [
    {
        "id": "beacon/hub/southeast",
        "name": "Southeast Regional Hub",
        "city": "Atlanta, GA",
        "base_county_fips": "13121",  # Fulton County, GA
        "region": "Southeast",
        "states": ["AL", "FL", "GA", "MS", "NC", "SC", "TN"],
    },
    {
        "id": "beacon/hub/northeast",
        "name": "Northeast Regional Hub",
        "city": "Philadelphia, PA",
        "base_county_fips": "42101",  # Philadelphia County, PA
        "region": "Northeast",
        "states": ["CT", "DE", "DC", "MA", "MD", "ME", "NH", "NJ", "NY", "PA", "RI", "VT"],
    },
    {
        "id": "beacon/hub/midwest",
        "name": "Midwest Regional Hub",
        "city": "Chicago, IL",
        "base_county_fips": "17031",  # Cook County, IL
        "region": "Midwest",
        "states": ["IL", "IN", "IA", "KS", "MI", "MN", "MO", "NE", "ND", "OH", "SD", "WI"],
    },
    {
        "id": "beacon/hub/gulfcoast",
        "name": "Gulf Coast & South Central Hub",
        "city": "Houston, TX",
        "base_county_fips": "48201",  # Harris County, TX
        "region": "Gulf Coast",
        "states": ["AR", "LA", "OK", "TX", "NM"],
    },
    {
        "id": "beacon/hub/west",
        "name": "Western & Mountain Hub",
        "city": "Denver, CO",
        "base_county_fips": "08031",  # Denver County, CO
        "region": "West",
        "states": ["AZ", "CO", "ID", "MT", "NV", "UT", "WY"],
    },
    {
        "id": "beacon/hub/pacific",
        "name": "Pacific Regional Hub",
        "city": "Seattle, WA",
        "base_county_fips": "53033",  # King County, WA
        "region": "Pacific",
        "states": ["AK", "CA", "HI", "OR", "WA"],
    },
]

# Base locations for ~38 Mobile Response Teams (metro centers)
TEAM_BASES = [
    # Southeast
    ("12086", "Miami, FL", "Southeast", 250),
    ("12057", "Tampa, FL", "Southeast", 220),
    ("12095", "Orlando, FL", "Southeast", 200),
    ("12031", "Jacksonville, FL", "Southeast", 180),
    ("13121", "Atlanta, GA", "Southeast", 250),
    ("13051", "Savannah, GA", "Southeast", 160),
    ("37183", "Raleigh, NC", "Southeast", 200),
    ("37119", "Charlotte, NC", "Southeast", 220),
    ("45079", "Columbia, SC", "Southeast", 180),
    ("45019", "Charleston, SC", "Southeast", 180),
    ("47037", "Nashville, TN", "Southeast", 220),
    ("47157", "Memphis, TN", "Southeast", 200),
    ("01073", "Birmingham, AL", "Southeast", 180),
    ("01097", "Mobile, AL", "Southeast", 180),
    ("28049", "Jackson, MS", "Southeast", 180),
    # Kentucky (based in urban Louisville & Lexington; leaves eastern rural coal-country uncovered)
    ("21111", "Louisville, KY", "Southeast", 200),
    ("21067", "Lexington, KY", "Southeast", 180),
    # Gulf Coast / South Central
    ("48201", "Houston, TX", "Gulf Coast", 250),
    ("48113", "Dallas, TX", "Gulf Coast", 240),
    ("48453", "Austin, TX", "Gulf Coast", 200),
    ("48029", "San Antonio, TX", "Gulf Coast", 200),
    ("22071", "New Orleans, LA", "Gulf Coast", 220),
    ("22033", "Baton Rouge, LA", "Gulf Coast", 180),
    ("05119", "Little Rock, AR", "Gulf Coast", 180),
    ("40109", "Oklahoma City, OK", "Gulf Coast", 180),
    # Midwest
    ("17031", "Chicago, IL", "Midwest", 250),
    ("29189", "St. Louis, MO", "Midwest", 220),
    ("29095", "Kansas City, MO", "Midwest", 200),
    ("39049", "Columbus, OH", "Midwest", 200),
    ("39035", "Cleveland, OH", "Midwest", 180),
    ("26163", "Detroit, MI", "Midwest", 200),
    ("18097", "Indianapolis, IN", "Midwest", 200),
    # Northeast
    ("42101", "Philadelphia, PA", "Northeast", 220),
    ("42003", "Pittsburgh, PA", "Northeast", 200),
    ("36061", "New York, NY", "Northeast", 250),
    ("36029", "Buffalo, NY", "Northeast", 180),
    # West / Pacific
    ("08031", "Denver, CO", "West", 220),
    ("04013", "Phoenix, AZ", "West", 220),
    ("06037", "Los Angeles, CA", "Pacific", 250),
    ("06073", "San Diego, CA", "Pacific", 220),
    ("06067", "Sacramento, CA", "Pacific", 200),
    ("53033", "Seattle, WA", "Pacific", 220),
]

COVERAGE_RADIUS_MILES = 75.0


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
  """Calculates great-circle distance between two points on Earth in miles."""
  r_earth = 3958.8  # Earth radius in miles
  phi1, phi2 = math.radians(lat1), math.radians(lat2)
  dphi = math.radians(lat2 - lat1)
  dlambda = math.radians(lon2 - lon1)
  a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
  return 2.0 * r_earth * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def main() -> None:
  PRIVATE_DIR.mkdir(parents=True, exist_ok=True)

  places_file = PUBLIC_DIR / "places.csv"
  if not places_file.exists():
    raise SystemExit(f"Missing {places_file}. Run loader/fetch_public.py first.")

  places = pd.read_csv(places_file, dtype=str)
  counties = places[places.label == "county"].copy()
  counties["latitude"] = pd.to_numeric(counties["latitude"], errors="coerce")
  counties["longitude"] = pd.to_numeric(counties["longitude"], errors="coerce")
  county_map = {row["subject_id"]: row for _, row in counties.iterrows()}

  nodes = []
  edges = []

  # 1. Build Hubs
  print(f"Generating {len(HUBS)} Regional Hubs ...")
  for h in HUBS:
    county_id = f"geoId/{h['base_county_fips']}"
    cty = county_map.get(county_id)
    lat = float(cty["latitude"]) if cty is not None and pd.notna(cty["latitude"]) else None
    lon = float(cty["longitude"]) if cty is not None and pd.notna(cty["longitude"]) else None
    st_code = FIPS_TO_USPS.get(h["base_county_fips"][:2], "")

    nodes.append({
        "subject_id": h["id"],
        "label": "hub",
        "name": h["name"],
        "display_name": f"Beacon {h['name']} ({h['city']})",
        "provenance": AGENCY_PROVENANCE,
        "state_code": st_code,
        "latitude": lat,
        "longitude": lon,
        "hub_region": h["region"],
        "description": f"Beacon Readiness Office regional operations hub for the {h['region']} region.",
    })

    # Located in base county
    edges.append({
        "subject_id": h["id"],
        "predicate": "locatedin",
        "object_id": county_id,
        "provenance": AGENCY_PROVENANCE,
    })

    # Serves states in its region
    for st in h["states"]:
      st_fips = USPS_TO_FIPS.get(st)
      if st_fips:
        edges.append({
            "subject_id": h["id"],
            "predicate": "serves",
            "object_id": f"geoId/{st_fips}",
            "provenance": AGENCY_PROVENANCE,
        })

  # 2. Build Mobile Response Teams & Coverage
  print(f"Generating {len(TEAM_BASES)} Mobile Response Teams with {COVERAGE_RADIUS_MILES} mi coverage radius ...")
  total_coverage_edges = 0
  covered_counties = set()

  for idx, (base_fips, metro_name, reg, cap) in enumerate(TEAM_BASES, start=1):
    team_id = f"beacon/team/{idx:02d}"
    county_id = f"geoId/{base_fips}"
    cty = county_map.get(county_id)
    if cty is None or pd.isna(cty["latitude"]) or pd.isna(cty["longitude"]):
      print(f"  Warning: base county {county_id} not found in places.csv")
      continue

    base_lat = float(cty["latitude"])
    base_lon = float(cty["longitude"])
    st_code = FIPS_TO_USPS.get(base_fips[:2], "")

    nodes.append({
        "subject_id": team_id,
        "label": "team",
        "name": f"Response Team {idx:02d}",
        "display_name": f"Beacon Mobile Response Team {idx:02d} ({metro_name})",
        "provenance": AGENCY_PROVENANCE,
        "state_code": st_code,
        "latitude": base_lat,
        "longitude": base_lon,
        "hub_region": reg,
        "capacity": cap,
        "description": f"Mobile disaster intake and registration unit based in {metro_name}. Daily intake capacity: {cap}.",
    })

    # Team located in base county
    edges.append({
        "subject_id": team_id,
        "predicate": "locatedin",
        "object_id": county_id,
        "provenance": AGENCY_PROVENANCE,
    })

    # Calculate coverage within 75 miles
    for _, other in counties.iterrows():
      if pd.isna(other["latitude"]) or pd.isna(other["longitude"]):
        continue
      dist = haversine_miles(base_lat, base_lon, float(other["latitude"]), float(other["longitude"]))
      if dist <= COVERAGE_RADIUS_MILES:
        other_id = other["subject_id"]
        edges.append({
            "subject_id": team_id,
            "predicate": "covers",
            "object_id": other_id,
            "provenance": AGENCY_PROVENANCE,
        })
        covered_counties.add(other_id)
        total_coverage_edges += 1

  # 3. System of Action: Initial DeploymentPlan
  # Start with an empty plan or 1 pre-existing assignment to verify table structure
  plan_rows = []

  # Save files
  node_cols = ["subject_id", "label", "name", "display_name", "provenance", "state_code",
               "latitude", "longitude", "description", "incident_type", "declaration_date",
               "fy_declared", "hub_region", "capacity"]
  with open(PRIVATE_DIR / "agency_nodes.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=node_cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(nodes)

  with open(PRIVATE_DIR / "agency_edges.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["subject_id", "predicate", "object_id", "provenance"])
    w.writeheader()
    w.writerows(edges)

  with open(PRIVATE_DIR / "deployment_plan.csv", "w", newline="") as f:
    plan_cols = ["county_id", "action", "assigned_team_id", "priority_tier", "rationale",
                 "added_by", "added_at", "status"]
    w = csv.DictWriter(f, fieldnames=plan_cols)
    w.writeheader()
    w.writerows(plan_rows)

  manifest = {
      "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
      "hubs": len(HUBS),
      "teams": len(TEAM_BASES),
      "total_agency_nodes": len(nodes),
      "total_agency_edges": len(edges),
      "coverage_radius_miles": COVERAGE_RADIUS_MILES,
      "total_coverage_edges": total_coverage_edges,
      "unique_counties_covered": len(covered_counties),
      "unique_counties_uncovered": len(counties) - len(covered_counties),
  }
  write_json(PRIVATE_DIR / "agency_manifest.json", manifest)

  # 4. Generate story.json (ground-truth answer key for validation and script rendering)
  fema_disasters = pd.read_csv(PUBLIC_DIR / "fema_disasters.csv")
  fema_desig = pd.read_csv(PUBLIC_DIR / "fema_designations.csv")
  fema_reg = pd.read_csv(PUBLIC_DIR / "fema_registrations.csv")
  cp = pd.read_csv(PUBLIC_DIR / "county_profile.csv")

  tot_reg = int(fema_reg["total_valid_registrations"].sum())
  web_reg = int(fema_reg["web_registrations"].sum())
  cc_reg = int(fema_reg["call_center_registrations"].sum())
  mob_reg = int(fema_reg["mobile_registrations"].sum())

  # County-level aggregation for correlation check
  cty_reg = fema_reg.groupby("county_id").agg({
      "total_valid_registrations": "sum",
      "web_registrations": "sum",
  }).reset_index()
  cty_reg["web_share_pct"] = (100.0 * cty_reg["web_registrations"] / cty_reg["total_valid_registrations"]).round(1)

  merged = pd.merge(cty_reg[cty_reg.total_valid_registrations >= 200], cp, on="county_id", how="inner")
  merged = merged.dropna(subset=["no_internet_pct", "web_share_pct", "age_65_plus_pct"])
  merged = merged.sort_values("no_internet_pct")

  q_len = len(merged) // 4
  q1 = merged.iloc[:q_len]
  q4 = merged.iloc[-q_len:]

  q1_web = round(float(100.0 * q1["web_registrations"].sum() / q1["total_valid_registrations"].sum()), 1)
  q4_web = round(float(100.0 * q4["web_registrations"].sum() / q4["total_valid_registrations"].sum()), 1)

  def pearson(xs, ys, ws=None):
    ws = ws or [1.0] * len(xs)
    sw = sum(ws)
    if sw == 0:
      return 0.0
    mx = sum(w * x for w, x in zip(ws, xs)) / sw
    my = sum(w * y for w, y in zip(ws, ys)) / sw
    cov = sum(w * (x - mx) * (y - my) for w, x, y in zip(ws, xs, ys))
    vx = sum(w * (x - mx) ** 2 for w, x in zip(ws, xs))
    vy = sum(w * (y - my) ** 2 for w, y in zip(ws, ys))
    if vx <= 0 or vy <= 0:
      return 0.0
    return round(cov / math.sqrt(vx * vy), 2)

  xs = merged["no_internet_pct"].tolist()
  ys = merged["web_share_pct"].tolist()
  ws = merged["total_valid_registrations"].tolist()
  zs = merged["age_65_plus_pct"].tolist()

  corr_weighted = pearson(xs, ys, ws)
  corr_unweighted = pearson(xs, ys)
  age_corr = pearson(zs, ys)

  # Find repeat-hit county
  repeat_counts = fema_desig.groupby("county_id")["disaster_id"].nunique().sort_values(ascending=False)
  top_repeat_cid = repeat_counts.index[0]
  top_repeat_row = cp[cp.county_id == top_repeat_cid].iloc[0] if not cp[cp.county_id == top_repeat_cid].empty else None

  story = {
      "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
      "agency_name": "Beacon Readiness Office",
      "disasters_count": len(fema_disasters),
      "declared_counties_count": int(fema_desig["county_id"].nunique()),
      "total_registrations": tot_reg,
      "web_registrations": web_reg,
      "web_share_pct": round(100.0 * web_reg / tot_reg, 1),
      "call_center_registrations": cc_reg,
      "call_center_share_pct": round(100.0 * cc_reg / tot_reg, 1),
      "mobile_registrations": mob_reg,
      "mobile_share_pct": round(100.0 * mob_reg / tot_reg, 1),
      "access_comparison": {
          "counties_analyzed": len(merged),
          "lowest_quartile_no_internet_avg": round(float(q1["no_internet_pct"].mean()), 1),
          "lowest_quartile_web_share_pct": q1_web,
          "highest_quartile_no_internet_avg": round(float(q4["no_internet_pct"].mean()), 1),
          "highest_quartile_web_share_pct": q4_web,
          "spread_pp": round(q1_web - q4_web, 1),
          "correlation_weighted": corr_weighted,
          "correlation_unweighted": corr_unweighted,
          "age_65_correlation_unweighted": age_corr,
      },
      "coverage": {
          "total_teams": len(TEAM_BASES),
          "total_hubs": len(HUBS),
          "covered_counties": len(covered_counties),
          "uncovered_counties": len(counties) - len(covered_counties),
      },
      "top_repeat_county": {
          "county_id": top_repeat_cid,
          "county_name": top_repeat_row["county_name"] if top_repeat_row is not None else top_repeat_cid,
          "state_code": top_repeat_row["state_code"] if top_repeat_row is not None else "",
          "disaster_count": int(repeat_counts.iloc[0]),
      },
  }
  write_json(PRIVATE_DIR / "story.json", story)

  print(f"Agency generation complete -> {PRIVATE_DIR}:")
  print(f"  {len(HUBS)} Hub nodes, {len(TEAM_BASES)} Team nodes")
  print(f"  {len(covered_counties):,} counties covered ({len(counties) - len(covered_counties):,} rural/remote counties uncovered)")
  print(f"  {len(edges):,} total agency edges")
  print(f"  story.json written (national web share: {story['web_share_pct']}%, weighted r: {corr_weighted})")


if __name__ == "__main__":
  main()
