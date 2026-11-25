"""Derives CountyProfile and StateProfile rows from the fetched Data Commons observations.

Reads data/public/{places,edges}.csv and observations.csv.gz and writes
data/public/county_profile.csv and state_profile.csv.

Usage:
  python loader/build_profiles.py
"""

from __future__ import annotations

import pandas as pd

from common import PUBLIC_DIR, write_json

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


def latest_val(obs: pd.DataFrame, var: str) -> pd.DataFrame:
  """Returns latest observation per entity for a variable: index=observation_about, cols=[value, observation_date]."""
  d = obs[obs.variable_measured == var].sort_values("observation_date")
  d = d.groupby("observation_about").tail(1)
  return d.set_index("observation_about")[["value", "observation_date"]]


def build_county_profiles(obs: pd.DataFrame, counties: list[str]) -> pd.DataFrame:
  df = pd.DataFrame(index=pd.Index(counties, name="county_id"))

  # Population & 5-year change
  pop = latest_val(obs, POP)
  df["population"] = pop["value"].round().astype("Int64")
  df["population_year"] = pop["observation_date"].str[:4].astype("Int64")

  pop_series = obs[obs.variable_measured == POP].set_index(["observation_about", "observation_date"])["value"]
  five_yr_prior = [
      pop_series.get((c, str(int(y) - 5))) if pd.notna(y) else None
      for c, y in zip(df.index, df["population_year"])
  ]
  prior_s = pd.Series(five_yr_prior, index=df.index, dtype=float)
  df["population_change_5yr_pct"] = (100.0 * (df["population"].astype(float) / prior_s - 1.0)).round(1)

  # Households & Internet
  hh = latest_val(obs, HH)
  df["households"] = hh["value"].round().astype("Int64")
  df["acs_year"] = hh["observation_date"].str[:4].astype("Int64")

  no_int = latest_val(obs, NO_INTERNET)
  df["no_internet_households"] = no_int["value"].round().astype("Int64")
  df["no_internet_pct"] = (100.0 * df["no_internet_households"].astype(float) / df["households"].astype(float)).round(1)

  # Age 65+, Disability, Poverty
  age = latest_val(obs, AGE_65)
  df["age_65_plus"] = age["value"].round().astype("Int64")
  df["age_65_plus_pct"] = (100.0 * df["age_65_plus"].astype(float) / df["population"].astype(float)).round(1)

  disab = latest_val(obs, DISABILITY)
  df["disability_count"] = disab["value"].round().astype("Int64")
  df["disability_pct"] = (100.0 * df["disability_count"].astype(float) / df["population"].astype(float)).round(1)

  pov = latest_val(obs, POVERTY)
  df["poverty_count"] = pov["value"].round().astype("Int64")
  df["poverty_pct"] = (100.0 * df["poverty_count"].astype(float) / df["population"].astype(float)).round(1)

  # NRI Hazard Risks
  df["nri_risk_score"] = latest_val(obs, NRI_RISK)["value"].round(2)
  df["nri_social_vulnerability_score"] = latest_val(obs, NRI_SOC_VULN)["value"].round(2)
  df["nri_community_resilience_score"] = latest_val(obs, NRI_RESIL)["value"].round(2)
  df["nri_expected_annual_loss_usd"] = latest_val(obs, NRI_EAL)["value"].round(0)
  df["nri_flood_risk_score"] = latest_val(obs, NRI_FLOOD)["value"].round(2)
  df["nri_hurricane_risk_score"] = latest_val(obs, NRI_HURRICANE)["value"].round(2)
  df["nri_wildfire_risk_score"] = latest_val(obs, NRI_WILDFIRE)["value"].round(2)

  return df


def build_state_profiles(obs: pd.DataFrame, states: list[str]) -> pd.DataFrame:
  df = pd.DataFrame(index=pd.Index(states, name="state_id"))

  pop = latest_val(obs, POP)
  df["population"] = pop["value"].round().astype("Int64")
  df["population_year"] = pop["observation_date"].str[:4].astype("Int64")

  pop_series = obs[obs.variable_measured == POP].set_index(["observation_about", "observation_date"])["value"]
  five_yr_prior = [
      pop_series.get((s, str(int(y) - 5))) if pd.notna(y) else None
      for s, y in zip(df.index, df["population_year"])
  ]
  prior_s = pd.Series(five_yr_prior, index=df.index, dtype=float)
  df["population_change_5yr_pct"] = (100.0 * (df["population"].astype(float) / prior_s - 1.0)).round(1)

  hh = latest_val(obs, HH)
  df["households"] = hh["value"].round().astype("Int64")
  df["acs_year"] = hh["observation_date"].str[:4].astype("Int64")

  no_int = latest_val(obs, NO_INTERNET)
  df["no_internet_households"] = no_int["value"].round().astype("Int64")
  df["no_internet_pct"] = (100.0 * df["no_internet_households"].astype(float) / df["households"].astype(float)).round(1)

  age = latest_val(obs, AGE_65)
  df["age_65_plus"] = age["value"].round().astype("Int64")
  df["age_65_plus_pct"] = (100.0 * df["age_65_plus"].astype(float) / df["population"].astype(float)).round(1)

  disab = latest_val(obs, DISABILITY)
  df["disability_count"] = disab["value"].round().astype("Int64")
  df["disability_pct"] = (100.0 * df["disability_count"].astype(float) / df["population"].astype(float)).round(1)

  pov = latest_val(obs, POVERTY)
  df["poverty_count"] = pov["value"].round().astype("Int64")
  df["poverty_pct"] = (100.0 * df["poverty_count"].astype(float) / df["population"].astype(float)).round(1)

  return df


def main() -> None:
  places = pd.read_csv(PUBLIC_DIR / "places.csv", dtype=str)
  edges = pd.read_csv(PUBLIC_DIR / "edges.csv", dtype=str)
  obs = pd.read_csv(PUBLIC_DIR / "observations.csv.gz", dtype={"observation_date": str})

  name = places.set_index("subject_id")["display_name"]
  code = places.set_index("subject_id")["state_code"]
  counties = places[places.label == "county"]["subject_id"].tolist()
  states = places[places.label == "state"]["subject_id"].tolist()

  print(f"Building profiles for {len(counties):,} counties and {len(states):,} states ...")
  cp = build_county_profiles(obs, counties)
  cp.insert(0, "county_name", [name.get(c) for c in cp.index])
  cp.insert(1, "state_id", [f"geoId/{c[6:8]}" for c in cp.index])
  cp.insert(2, "state_name", [name.get(f"geoId/{c[6:8]}") for c in cp.index])
  cp.insert(3, "state_code", [code.get(c) for c in cp.index])
  cp.reset_index().to_csv(PUBLIC_DIR / "county_profile.csv", index=False)

  div_of = edges[(edges.predicate == "containedinplace") & edges.object_id.str.endswith("Division")]
  div_lookup = div_of.set_index("subject_id")["object_id"]

  sp = build_state_profiles(obs, states)
  sp.insert(0, "state_name", [name.get(s) for s in sp.index])
  sp.insert(1, "state_code", [code.get(s) for s in sp.index])
  sp.insert(2, "census_division", [name.get(div_lookup.get(s)) for s in sp.index])
  sp.reset_index().to_csv(PUBLIC_DIR / "state_profile.csv", index=False)

  summary = {
      "counties": len(cp),
      "states": len(sp),
      "latest_population_year": int(cp["population_year"].dropna().max()) if not cp["population_year"].dropna().empty else None,
      "acs_vintage_year": int(cp["acs_year"].dropna().max()) if not cp["acs_year"].dropna().empty else None,
      "avg_no_internet_pct": round(float(cp["no_internet_pct"].dropna().mean()), 1) if not cp["no_internet_pct"].dropna().empty else None,
      "avg_poverty_pct": round(float(cp["poverty_pct"].dropna().mean()), 1) if not cp["poverty_pct"].dropna().empty else None,
      "counties_with_nri": int(cp["nri_risk_score"].notna().sum()),
  }
  write_json(PUBLIC_DIR / "profile_summary.json", summary)
  print("Profile build complete:")
  print(summary)


if __name__ == "__main__":
  main()
