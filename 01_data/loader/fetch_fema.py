"""Pulls OpenFEMA disaster declarations and assistance registrations into data/public/.

Real federal agency program data (OpenFEMA v2 API, open and free, no key required).
Pulls:
  - Major Disaster Declarations (DR) since 2023-01-01
  - Per-county program declarations (Individual Assistance / IHP, Public Assistance, Hazard Mitigation)
  - Registration intake by disaster x county x channel (web, call center, mobile)
Outputs:
  - data/public/fema_disasters.csv (Disaster nodes for the graph)
  - data/public/fema_edges.csv (Disaster -affectedPlace-> County edges)
  - data/public/fema_designations.csv (DisasterDesignation table rows)
  - data/public/fema_registrations.csv (Registration table rows)
  - data/public/fema_meta.json (Citations, access date, disclaimer, counts)

Usage:
  python loader/fetch_fema.py
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
import pathlib
import urllib.parse
import urllib.request

from common import FEMA_PROVENANCE, FIPS_TO_USPS, PUBLIC_DIR, write_json

FEMA_API_BASE = "https://www.fema.gov/api/open/v2/"
FEMA_DISCLAIMER = (
    "This product uses the Federal Emergency Management Agency's OpenFEMA API, "
    "but is not endorsed by FEMA. OpenFEMA data is subject to the OpenFEMA Terms and Conditions."
)
SINCE_DATE = "2023-01-01T00:00:00.000Z"


def get_openfema(entity: str, params: dict, cache_dir: pathlib.Path | None = None) -> list[dict]:
  """Fetches all pages of an OpenFEMA entity with automatic paging ($top=10000)."""
  cache_file = cache_dir / f"{entity}.json" if cache_dir else None
  if cache_file and cache_file.exists():
    print(f"  [cache] reading {entity} from {cache_file.name}")
    return json.loads(cache_file.read_text())

  out: list[dict] = []
  skip = 0
  while True:
    q = dict(params, **{"$top": "10000", "$skip": str(skip)})
    url = FEMA_API_BASE + entity + "?" + urllib.parse.urlencode(q, safe="$,' ")
    req = urllib.request.Request(
        url.replace(" ", "%20"),
        headers={"User-Agent": "BeaconReadinessDemo/1.0 (Google Cloud Spanner Graph Demo)"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
      data = json.loads(resp.read().decode())
      rows = data.get(entity, [])
    out.extend(rows)
    print(f"  {entity}: retrieved {len(out):,} records ...")
    if len(rows) < 10000:
      break
    skip += 10000

  if cache_file:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(out))
  return out


def main() -> None:
  ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
  ap.add_argument("--since", default=SINCE_DATE, help="Declaration date cutoff (ISO-8601).")
  ap.add_argument("--cache", action="store_true", default=True, help="Cache raw API responses in data/public/.cache")
  ap.add_argument("--no-cache", dest="cache", action="store_false")
  args = ap.parse_args()

  PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
  cache_dir = (PUBLIC_DIR / ".cache") if args.cache else None

  print(f"Fetching OpenFEMA disaster declarations since {args.since[:10]} ...")
  dds_raw = get_openfema(
      "DisasterDeclarationsSummaries",
      {
          "$filter": f"declarationType eq 'DR' and declarationDate ge '{args.since}'",
          "$orderby": "disasterNumber desc",
      },
      cache_dir=cache_dir,
  )

  # Group by disasterNumber to build disaster nodes
  by_dr: dict[int, list[dict]] = collections.defaultdict(list)
  for r in dds_raw:
    by_dr[r["disasterNumber"]].append(r)

  drs = sorted(by_dr.keys())
  min_dr, max_dr = drs[0], drs[-1]
  print(f"  found {len(drs)} major disaster declarations ({min_dr} to {max_dr}) across {len(dds_raw):,} area rows")

  print("Fetching OpenFEMA registration intake records (RI-IHP) ...")
  ri_raw = get_openfema(
      "RegistrationIntakeIndividualsHouseholdPrograms",
      {
          "$filter": f"disasterNumber ge {min_dr} and disasterNumber le {max_dr}",
          "$orderby": "disasterNumber desc",
      },
      cache_dir=cache_dir,
  )
  print(f"  found {len(ri_raw):,} registration intake records across {len({r['disasterNumber'] for r in ri_raw})} disasters")

  # Build county lookup from DDS: (disasterNumber, state, designatedArea) -> 5-digit FIPS
  area_fips: dict[tuple[int, str, str], str] = {}
  for d in dds_raw:
    st_fips = str(d.get("fipsStateCode") or "").zfill(2)
    cty_fips = str(d.get("fipsCountyCode") or "").zfill(3)
    if st_fips in FIPS_TO_USPS and cty_fips != "000" and len(st_fips) == 2 and len(cty_fips) == 3:
      fips = st_fips + cty_fips
      area_fips[(d["disasterNumber"], d["state"], d["designatedArea"])] = fips

  # 1. Disaster nodes (Node table: subject_id = fema/DR-{num}, label = disaster)
  disaster_nodes = []
  for dr_num in drs:
    rows = by_dr[dr_num]
    r0 = rows[0]
    st = r0.get("state") or ""
    inc_type = r0.get("incidentType") or "Other"
    decl_date = (r0.get("declarationDate") or "")[:10]
    fy = r0.get("fyDeclared")
    title = (r0.get("declarationTitle") or "").strip().title()
    decl_str = r0.get("femaDeclarationString") or f"DR-{dr_num}-{st}"
    disp_name = f"{decl_str} ({title})"

    disaster_nodes.append({
        "subject_id": f"fema/DR-{dr_num}",
        "label": "disaster",
        "name": f"DR-{dr_num}",
        "display_name": disp_name,
        "provenance": FEMA_PROVENANCE,
        "state_code": st if st in FIPS_TO_USPS.values() else None,
        "incident_type": inc_type,
        "declaration_date": decl_date,
        "fy_declared": fy,
        "description": f"FEMA Major Disaster Declaration {decl_str}: {title}. Incident type: {inc_type}.",
    })

  # 2. Designations and Edges (Disaster -> County)
  designations = []
  edges = []
  seen_edges = set()
  seen_desig = set()

  for d in dds_raw:
    dr_num = d["disasterNumber"]
    st_fips = str(d.get("fipsStateCode") or "").zfill(2)
    cty_fips = str(d.get("fipsCountyCode") or "").zfill(3)
    if st_fips not in FIPS_TO_USPS or cty_fips == "000":
      continue
    fips = st_fips + cty_fips
    disaster_id = f"fema/DR-{dr_num}"
    county_id = f"geoId/{fips}"

    if (disaster_id, county_id) in seen_desig:
      continue
    seen_desig.add((disaster_id, county_id))

    ihp = bool(d.get("ihProgramDeclared"))
    pa = bool(d.get("paProgramDeclared"))
    hm = bool(d.get("hmProgramDeclared"))
    decl_date = (d.get("declarationDate") or "")[:10]
    inc_type = d.get("incidentType") or "Other"

    designations.append({
        "disaster_id": disaster_id,
        "county_id": county_id,
        "state_code": d.get("state") or FIPS_TO_USPS.get(st_fips, ""),
        "ihp_declared": ihp,
        "pa_declared": pa,
        "hm_declared": hm,
        "declaration_date": decl_date,
        "incident_type": inc_type,
    })

    edge_key = (disaster_id, "affectedplace", county_id)
    if edge_key not in seen_edges:
      seen_edges.add(edge_key)
      edges.append({
          "subject_id": disaster_id,
          "predicate": "affectedplace",
          "object_id": county_id,
          "provenance": FEMA_PROVENANCE,
      })

  # 3. Registrations (disaster x county aggregated)
  reg_agg: dict[tuple[int, str], dict[str, int]] = collections.defaultdict(lambda: collections.Counter())
  unmatched_rows = 0

  for r in ri_raw:
    k = (r["disasterNumber"], r["state"], r["county"])
    fips = area_fips.get(k)
    if not fips:
      unmatched_rows += 1
      continue
    dr_num = r["disasterNumber"]
    tot = int(r.get("totalValidRegistrations") or 0)
    web = int(r.get("validWebRegistrations") or 0)
    cc = int(r.get("validCallCenterRegistrations") or 0)
    mob = int(r.get("validMobileRegistrations") or 0)

    bucket = reg_agg[(dr_num, fips)]
    bucket["tot"] += tot
    bucket["web"] += web
    bucket["cc"] += cc
    bucket["mob"] += mob

  registrations = []
  total_reg_count = 0
  for (dr_num, fips), counts in sorted(reg_agg.items()):
    tot = counts["tot"]
    if tot <= 0:
      continue
    total_reg_count += tot
    web = counts["web"]
    cc = counts["cc"]
    mob = counts["mob"]
    st_code = FIPS_TO_USPS.get(fips[:2], "")

    registrations.append({
        "disaster_id": f"fema/DR-{dr_num}",
        "county_id": f"geoId/{fips}",
        "state_code": st_code,
        "total_valid_registrations": tot,
        "web_registrations": web,
        "call_center_registrations": cc,
        "mobile_registrations": mob,
        "web_share_pct": round(100.0 * web / tot, 1) if tot > 0 else 0.0,
        "call_center_share_pct": round(100.0 * cc / tot, 1) if tot > 0 else 0.0,
        "mobile_share_pct": round(100.0 * mob / tot, 1) if tot > 0 else 0.0,
    })

  # Write CSV deliverables to data/public/
  with open(PUBLIC_DIR / "fema_disasters.csv", "w", newline="") as f:
    cols = ["subject_id", "label", "name", "display_name", "provenance", "state_code",
            "incident_type", "declaration_date", "fy_declared", "description"]
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(disaster_nodes)

  with open(PUBLIC_DIR / "fema_edges.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["subject_id", "predicate", "object_id", "provenance"])
    w.writeheader()
    w.writerows(edges)

  with open(PUBLIC_DIR / "fema_designations.csv", "w", newline="") as f:
    cols = ["disaster_id", "county_id", "state_code", "ihp_declared", "pa_declared", "hm_declared",
            "declaration_date", "incident_type"]
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(designations)

  with open(PUBLIC_DIR / "fema_registrations.csv", "w", newline="") as f:
    cols = ["disaster_id", "county_id", "state_code", "total_valid_registrations",
            "web_registrations", "call_center_registrations", "mobile_registrations",
            "web_share_pct", "call_center_share_pct", "mobile_share_pct"]
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(registrations)

  fetch_meta = {
      "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
      "api_base": FEMA_API_BASE,
      "disclaimer": FEMA_DISCLAIMER,
      "since_cutoff": args.since,
      "counts": {
          "disasters": len(disaster_nodes),
          "designations": len(designations),
          "disaster_county_edges": len(edges),
          "registration_rows": len(registrations),
          "total_valid_registrations": total_reg_count,
          "unmatched_intake_rows": unmatched_rows,
      },
      "endpoints_used": [
          f"{FEMA_API_BASE}DisasterDeclarationsSummaries",
          f"{FEMA_API_BASE}RegistrationIntakeIndividualsHouseholdPrograms",
      ],
  }
  write_json(PUBLIC_DIR / "fema_meta.json", fetch_meta)

  print(f"Successfully processed OpenFEMA data -> {PUBLIC_DIR}:")
  print(f"  {len(disaster_nodes):,} disaster nodes")
  print(f"  {len(edges):,} disaster -> county edges")
  print(f"  {len(designations):,} county designations")
  print(f"  {len(registrations):,} county-level registration records ({total_reg_count:,} total registrations)")


if __name__ == "__main__":
  main()
