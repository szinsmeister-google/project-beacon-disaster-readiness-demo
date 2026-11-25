"""Generates the private, synthetic Cymbal Outfitters dataset from real public data.

Everything here is fictional EXCEPT the public inputs it is calibrated on (Data
Commons county profiles and monthly BLS unemployment). The data is designed
backwards from the real numbers:

* Stores sit in real counties (by DCID) with real city names.
* Monthly store sales respond to the county's real unemployment trend (Classic
  big-box stores are more sensitive than small-format Express stores), so the
  region where unemployment really rose is where Classic sales fall.
* Online-order demand is highest in counties whose public profile looks like
  Cymbal's best Express markets, including a few that have no store yet.

Outputs (data/private/): stores.csv, distribution_centers.csv, store_sales.csv.gz,
online_orders.csv.gz and story.json (the answer key used by validate.py and the
demo script; it is never loaded into Spanner).

Usage:
  python loader/generate_private.py [--target-decline -12]
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import math

import numpy as np
import pandas as pd

from common import PRIVATE_DIR, PUBLIC_DIR, REPO_ROOT, write_json

# Load the agent's scoring module by path: importing the cymbal_agent package
# would construct the whole agent (ADK, MCP, Spanner client) just for 100 lines of math.
_spec = importlib.util.spec_from_file_location(
    "cymbal_scoring", REPO_ROOT / "agent" / "cymbal_agent" / "scoring.py")
scoring = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scoring)

SEED = 20260925

# Cymbal operating regions (states with stores) ...
REGIONS = {
    "Great Lakes": ["OH", "MI", "IN", "IL", "WI"],
    "Southeast": ["GA", "NC", "SC", "TN", "FL"],
    "Texas & Plains": ["TX", "OK"],
    "Mountain West": ["CO", "UT", "AZ"],
}
# ... and distribution centers, which also serve states that have no store yet.
DISTRIBUTION_CENTERS = [
    {"id": "cymbal/dc/columbus", "city": "Columbus", "county_id": "geoId/39049",
     "region": "Great Lakes", "serves": ["OH", "MI", "IN", "IL", "WI", "KY", "PA"]},
    {"id": "cymbal/dc/atlanta", "city": "McDonough", "county_id": "geoId/13151",
     "region": "Southeast", "serves": ["GA", "NC", "SC", "TN", "FL", "AL"]},
    {"id": "cymbal/dc/fortworth", "city": "Fort Worth", "county_id": "geoId/48439",
     "region": "Texas & Plains", "serves": ["TX", "OK", "LA", "AR"]},
    {"id": "cymbal/dc/saltlake", "city": "Salt Lake City", "county_id": "geoId/49035",
     "region": "Mountain West", "serves": ["CO", "UT", "AZ", "NV", "ID", "NM"]},
]

N_CLASSIC = 90
N_EXPRESS = 30
SALES_MONTHS = 36
ONLINE_MONTHS = 24
N_PLANTED_UNTAPPED = 6

# Outdoor apparel seasonality, January..December.
SEASON = np.array([0.74, 0.70, 0.86, 0.93, 1.00, 0.97, 0.95, 1.03, 0.94, 1.00, 1.22, 1.66])
SEASON = SEASON / SEASON.mean()
ONLINE_SEASON = np.array([0.80, 0.72, 0.84, 0.90, 0.95, 0.92, 0.93, 1.00, 0.94, 1.02, 1.35, 1.63])
ONLINE_SEASON = ONLINE_SEASON / ONLINE_SEASON.mean()

FORMAT = {
    # base monthly sales at reference size, secular trend per year, avg ticket
    "Classic": {"base": 1.95e6, "ref_sqft": 65_000, "trend": -0.015, "ticket": 92.0},
    "Express": {"base": 4.6e5, "ref_sqft": 11_000, "trend": 0.06, "ticket": 64.0},
}


def month_add(ym: str, k: int) -> str:
  y, m = map(int, ym.split("-"))
  i = y * 12 + (m - 1) + k
  return f"{i // 12:04d}-{i % 12 + 1:02d}"


def months_between(a: str, b: str) -> int:
  ya, ma = map(int, a.split("-"))
  yb, mb = map(int, b.split("-"))
  return (yb - ya) * 12 + (mb - ma)


def main() -> None:
  ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
  ap.add_argument("--target-decline", type=float, default=-12.0,
                  help="Target T3M YoY %% change for Classic comp stores in the region "
                       "where unemployment rose most (sets Classic sensitivity).")
  ap.add_argument("--sales-end", default=None,
                  help="Last sales month YYYY-MM (default: last complete month, capped at "
                       "one month after the latest unemployment data).")
  args = ap.parse_args()
  rng = np.random.default_rng(SEED)
  PRIVATE_DIR.mkdir(parents=True, exist_ok=True)

  cp = pd.read_csv(PUBLIC_DIR / "county_profile.csv")
  cp = cp.dropna(subset=["population", "median_household_income_usd", "unemployment_change_pp"])
  places = pd.read_csv(PUBLIC_DIR / "places.csv", usecols=["subject_id", "latitude", "longitude", "state_code"],
                       dtype={"state_code": str})
  place_info = places.set_index("subject_id")
  cp = cp.merge(places.drop(columns="state_code").rename(columns={"subject_id": "county_id"}),
                on="county_id", how="left")
  cities = pd.read_csv(PUBLIC_DIR / "largest_city.csv").set_index("county_id").city_name
  obs = pd.read_csv(PUBLIC_DIR / "observations.csv.gz", dtype={"observation_date": str})
  unemp = obs[(obs.variable_measured == "UnemploymentRate_Person")
              & (obs.observation_date.str.len() == 7)]
  useries = unemp.pivot_table(index="observation_about", columns="observation_date", values="value")
  latest_u = max(useries.columns)

  today = dt.date.today()
  last_complete = month_add(f"{today.year:04d}-{today.month:02d}", -1)
  sales_end = args.sales_end or min(last_complete, month_add(latest_u, 1))
  sales_months = [month_add(sales_end, -k) for k in range(SALES_MONTHS - 1, -1, -1)]
  online_months = sales_months[-ONLINE_MONTHS:]

  state_region = {s: r for r, ss in REGIONS.items() for s in ss}
  served = {s for d in DISTRIBUTION_CENTERS for s in d["serves"]}
  cp["region"] = cp.state_code.map(state_region)

  # --------------------------------------------------- real-data story check
  store_states = cp[cp.region.notna()]
  w = store_states.population.astype(float)
  region_du = (store_states.unemployment_change_pp * w).groupby(store_states.region).sum() / \
      w.groupby(store_states.region).sum()
  region_du = region_du.sort_values(ascending=False)
  declining = region_du.index[0]
  print("Population-weighted change in unemployment (T3M YoY, pp) by Cymbal region, real BLS data:")
  for r, v in region_du.items():
    print(f"  {r:16s} {v:+.2f}")

  # ------------------------------------------------------------- store sites
  def zs(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / (s.std() or 1)

  cand = cp[cp.region.notna() & (cp.population >= 150_000)].copy()
  cand["affinity"] = (zs(np.log(cand.median_household_income_usd)) + zs(cand.bachelors_or_higher_pct)
                      - 0.5 * zs(cand.median_age_years) + 0.5 * zs(cand.population_change_5yr_pct.fillna(0)))
  slots = []
  for _, c in cand.iterrows():
    for k in range(int(min(4, max(1, round(c.population / 700_000))))):
      slots.append((c.county_id, c.population / (k + 1) ** 1.5))
  weights = np.array([s[1] for s in slots]) ** 0.9
  pick = rng.choice(len(slots), size=N_CLASSIC, replace=False, p=weights / weights.sum())
  classic_sites = [slots[i][0] for i in pick]

  exp_pool = cand[cand.population >= 150_000].sort_values("affinity", ascending=False)
  exp_weights = np.exp(1.6 * exp_pool.affinity.to_numpy())
  exp_idx = rng.choice(len(exp_pool), size=N_EXPRESS, replace=False, p=exp_weights / exp_weights.sum())
  express_sites = exp_pool.county_id.to_numpy()[exp_idx].tolist()

  cpi = cp.set_index("county_id")
  stores = []
  for fmt, sites in (("Classic", classic_sites), ("Express", express_sites)):
    for county_id in sites:
      c = cpi.loc[county_id]
      if fmt == "Classic":
        open_date = dt.date(2008, 3, 1) + dt.timedelta(days=int(rng.integers(0, 365 * 11.5)))
        sqft = int(rng.integers(55, 76) * 1000)
      else:
        open_date = dt.date(2022, 3, 1) + dt.timedelta(days=int(rng.integers(0, 365 * 2.5)))
        sqft = int(rng.integers(9, 15) * 1000)
      city = cities.get(county_id)
      if not isinstance(city, str) or not city:
        city = c.county_name.split(",")[0].replace(" County", "").replace(" Parish", "")
      stores.append({"county_id": county_id, "store_format": fmt, "open_date": open_date,
                     "square_feet": sqft, "city_name": city, "state_code": c.state_code,
                     "cymbal_region": c.region,
                     "latitude": round(float(c.latitude) + rng.normal(0, 0.04), 5) if "latitude" in c else None,
                     "longitude": round(float(c.longitude) + rng.normal(0, 0.04), 5) if "longitude" in c else None})
  stores.sort(key=lambda s: (s["open_date"], s["county_id"]))
  for i, s in enumerate(stores, start=1):
    s["store_id"] = f"cymbal/store/{i:03d}"
    s["name"] = f"{s['store_format']} #{i:03d} - {s['city_name']}"
    s["display_name"] = f"Cymbal {s['store_format']} #{i:03d} - {s['city_name']}, {s['state_code']}"
  stores_df = pd.DataFrame(stores)

  # -------------------------------------------------------------- sales model
  def u3(county: str, ym: str) -> float:
    """3-month trailing average unemployment, lagged one month, using latest available."""
    vals = []
    for k in range(1, 4):
      m = min(month_add(ym, -k), latest_u)
      v = useries.at[county, m] if (county in useries.index and m in useries.columns) else np.nan
      vals.append(v)
    vals = [v for v in vals if not np.isnan(v)]
    return float(np.mean(vals)) if vals else np.nan

  window_start = sales_months[0]
  ref_months = sales_months[:12]
  u_ref = {c: np.nanmean([u3(c, m) for m in ref_months]) for c in stores_df.county_id.unique()}
  u_path = {c: {m: u3(c, m) for m in sales_months} for c in stores_df.county_id.unique()}

  # Calibrate Classic sensitivity so the declining region shows the target decline.
  last3 = sales_months[-3:]
  prior3 = [month_add(m, -12) for m in last3]
  cls = stores_df[(stores_df.store_format == "Classic") & (stores_df.cymbal_region == declining)]
  du_decl = float(np.mean([np.mean([u_path[c][m] for m in last3]) - np.mean([u_path[c][m] for m in prior3])
                           for c in cls.county_id]))
  trend_c = FORMAT["Classic"]["trend"]
  beta_classic = (math.log(1 + args.target_decline / 100) - trend_c) / du_decl if du_decl > 0.05 else -0.08
  beta_classic = float(np.clip(beta_classic, -0.16, -0.03))
  beta = {"Classic": beta_classic, "Express": beta_classic / 4}
  print(f"Declining region: {declining}; Classic-store counties' unemployment change "
        f"{du_decl:+.2f} pp -> Classic sensitivity {beta_classic:.3f} per pp, "
        f"Express {beta['Express']:.3f} per pp")
  if du_decl < 0.3:
    print("  ! Unemployment barely rose there; consider a different story or regions.")

  sales_rows = []
  for s in stores:
    f = FORMAT[s["store_format"]]
    c = cpi.loc[s["county_id"]]
    level = (f["base"] * (s["square_feet"] / f["ref_sqft"]) ** 0.7
             * (c.median_household_income_usd / 75_000) ** 0.35
             * (c.population / 500_000) ** 0.08
             * math.exp(rng.normal(0, 0.12)))
    ticket0 = f["ticket"] * (c.median_household_income_usd / 75_000) ** 0.2 * math.exp(rng.normal(0, 0.05))
    open_ym = s["open_date"].strftime("%Y-%m")
    for m in sales_months:
      age = months_between(open_ym, m)
      if age < 0:
        continue
      t_years = months_between(window_start, m) / 12
      ramp = 0.72 + 0.28 * min(age, 12) / 12 if s["store_format"] == "Express" else 1.0
      econ = beta[s["store_format"]] * (u_path[s["county_id"]][m] - u_ref[s["county_id"]])
      month_idx = int(m[5:]) - 1
      sales = level * SEASON[month_idx] * ramp * math.exp(f["trend"] * t_years + econ + rng.normal(0, 0.03))
      ticket = ticket0 * (1.08 if month_idx == 11 else 1.0) * math.exp(rng.normal(0, 0.02))
      tx = max(1, int(sales / ticket))
      sales_rows.append({"store_id": s["store_id"], "sales_month": f"{m}-01",
                         "net_sales_usd": round(sales, 2), "transactions": tx,
                         "avg_ticket_usd": round(sales / tx, 2)})
  sales_df = pd.DataFrame(sales_rows)

  # ------------------------------------------------ comp-store performance
  latest_month = sales_months[-1]
  cutoff = month_add(latest_month, -15)
  sp = sales_df.assign(ym=sales_df.sales_month.str[:7])
  t3 = sp[sp.ym.isin(last3)].groupby("store_id").net_sales_usd.sum()
  p3 = sp[sp.ym.isin(prior3)].groupby("store_id").net_sales_usd.sum()
  ttm = sp[sp.ym > month_add(latest_month, -12)].groupby("store_id").net_sales_usd.sum()
  perf = stores_df.set_index("store_id").join(pd.DataFrame({"t3": t3, "p3": p3, "ttm": ttm}))
  # Same rule as the StorePerformance view: open on or before the first day of the
  # month 15 months before the latest month.
  perf["comp"] = perf.open_date <= dt.date.fromisoformat(f"{cutoff}-01")
  perf["yoy"] = 100 * (perf.t3 / perf.p3 - 1)
  comp = perf[perf.comp]
  g = comp.groupby(["store_format", "cymbal_region"])[["t3", "p3"]].sum()
  seg = (100 * (g.t3 / g.p3 - 1)).round(1)
  gf = comp.groupby("store_format")[["t3", "p3"]].sum()
  fmt_total = (100 * (gf.t3 / gf.p3 - 1)).round(1)
  print("Comp-store T3M YoY % by format and region:")
  print(seg.unstack(0).to_string())

  # ---------------------------------------------------------- online demand
  top_express = perf[perf.store_format == "Express"].sort_values("ttm", ascending=False).head(8)
  ref_counties = cpi.loc[top_express.county_id.unique()].reset_index().to_dict("records")
  universe = cp[cp.state_code.isin(served)].copy()
  uni_rows = universe.to_dict("records")
  universe["lookalike"] = [r["score"] for r in scoring.lookalike_scores(uni_rows, ref_counties, uni_rows)]
  store_counties = set(stores_df.county_id)
  universe["has_store"] = universe.county_id.isin(store_counties)
  untapped = universe[~universe.has_store & (universe.population >= 120_000)]
  planted = (untapped.assign(k=untapped.lookalike * (1 + untapped.population_change_5yr_pct.fillna(0).clip(-5, 15) / 20))
             .sort_values("k", ascending=False).head(N_PLANTED_UNTAPPED).county_id.tolist())

  online_rows = []
  for _, c in universe.iterrows():
    hh = c.households if not pd.isna(c.households) else c.population / 2.5
    rate = 0.0040 * (max(c.lookalike, 3) / 50) ** 0.85  # orders per household per month
    rate *= 1.25 if c.has_store else 1.0
    rate *= 1.55 if c.county_id in planted else 1.0
    rate *= math.exp(rng.normal(0, 0.15))
    aov = 96.0 * (c.median_household_income_usd / 75_000) ** 0.25
    for m in online_months:
      t_years = months_between(online_months[0], m) / 12
      mu = hh * rate * ONLINE_SEASON[int(m[5:]) - 1] * math.exp(0.12 * t_years)
      orders = int(rng.poisson(max(mu, 0.1)))
      online_rows.append({"county_id": c.county_id, "order_month": f"{m}-01", "orders": orders,
                          "net_sales_usd": round(orders * aov * math.exp(rng.normal(0, 0.03)), 2)})
  online_df = pd.DataFrame(online_rows)

  # --------------------------------------------------------- distribution centers
  dcs = []
  for d in DISTRIBUTION_CENTERS:
    if d["county_id"] not in place_info.index:
      raise SystemExit(f"Distribution-center county {d['county_id']} is missing from places.csv")
    c = place_info.loc[d["county_id"]]
    lat = None if pd.isna(c.latitude) else round(float(c.latitude), 5)
    lng = None if pd.isna(c.longitude) else round(float(c.longitude), 5)
    dcs.append({"dc_id": d["id"], "name": f"{d['city']} DC", "display_name": f"Cymbal {d['city']} DC, {c.state_code}",
                "city_name": d["city"], "state_code": c.state_code, "county_id": d["county_id"],
                "cymbal_region": d["region"], "serves": "|".join(d["serves"]),
                "latitude": lat, "longitude": lng})

  # ------------------------------------------------------------------ write
  stores_df.to_csv(PRIVATE_DIR / "stores.csv", index=False)
  pd.DataFrame(dcs).to_csv(PRIVATE_DIR / "distribution_centers.csv", index=False)
  sales_df.to_csv(PRIVATE_DIR / "store_sales.csv.gz", index=False)
  online_df.to_csv(PRIVATE_DIR / "online_orders.csv.gz", index=False)

  decl_classic = comp[(comp.store_format == "Classic") & (comp.cymbal_region == declining)]
  corr = float(np.corrcoef(
      decl_classic.yoy,
      [np.mean([u_path[c][m] for m in last3]) - np.mean([u_path[c][m] for m in prior3])
       for c in decl_classic.county_id])[0, 1]) if len(decl_classic) > 2 else None
  story = {
      "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
      "seed": SEED,
      "sales_window": [sales_months[0], sales_months[-1]],
      "latest_unemployment_month": latest_u,
      "region_unemployment_change_pp": region_du.round(2).to_dict(),
      "declining_region": declining,
      "declining_region_classic_county_unemployment_change_pp": round(du_decl, 2),
      "sensitivity_per_pp": {k: round(v, 4) for k, v in beta.items()},
      "comp_yoy_pct_by_format": fmt_total.to_dict(),
      "comp_yoy_pct_by_format_region": {f"{k[0]} / {k[1]}": v for k, v in seg.items()},
      "declining_region_classic_yoy_vs_unemployment_corr": None if corr is None else round(corr, 2),
      "store_counts": stores_df.groupby("store_format").size().to_dict(),
      "top_express_stores": top_express[["display_name", "county_id", "ttm"]].round(0).to_dict("records"),
      "planted_untapped_counties": [
          {"county_id": c, "county_name": cpi.loc[c].county_name,
           "lookalike": float(universe.set_index("county_id").loc[c].lookalike)} for c in planted],
      "served_states": sorted(served),
  }
  write_json(PRIVATE_DIR / "story.json", story)
  print(f"Wrote {len(stores_df)} stores, {len(sales_df):,} sales rows, {len(online_df):,} online-order rows, "
        f"{len(dcs)} DCs -> {PRIVATE_DIR}")
  print("Planted untapped counties:", [cpi.loc[c].county_name for c in planted])


if __name__ == "__main__":
  main()
