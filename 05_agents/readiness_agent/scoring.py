"""Priority scoring for disaster readiness and mobile team deployment.

Scores candidate counties on objective vulnerability indicators (FEMA National
Risk Index, Social Vulnerability, Census internet access, repeat disaster
declarations) to identify underserved communities that lack mobile team coverage.
"""

from __future__ import annotations

import math


def percentile_ranks(values: list[float | None]) -> list[float | None]:
  """Computes 0-100 percentile rank of each value among the non-null values."""
  indexed = [(v, i) for i, v in enumerate(values) if v is not None and not math.isnan(v)]
  if not indexed:
    return [None] * len(values)
  indexed.sort(key=lambda t: t[0])
  n = len(indexed)
  ranks = [None] * len(values)
  for rank_idx, (_, orig_idx) in enumerate(indexed):
    ranks[orig_idx] = round(100.0 * rank_idx / max(1, n - 1), 1)
  return ranks


def calculate_priority_score(
    nri_risk_score: float | None,
    social_vulnerability_score: float | None,
    no_internet_pct: float | None,
    disasters_count: int,
) -> float:
  """Computes composite readiness priority score (0-100).

  Weights:
    - 35%: FEMA National Risk Index composite hazard score
    - 25%: FEMA Social Vulnerability score
    - 25%: Census ACS share of households lacking internet access
    - 15%: Repeat disaster frequency (scaled: 1 disaster = 25, 2 = 50, 3 = 75, 4+ = 100)
  """
  risk = float(nri_risk_score or 50.0)
  vuln = float(social_vulnerability_score or 50.0)
  internet = min(100.0, max(0.0, float(no_internet_pct or 10.0) * 3.5))  # scale 0-30% internet gap to 0-100
  freq = min(100.0, max(0.0, float(disasters_count) * 25.0))

  composite = 0.35 * risk + 0.25 * vuln + 0.25 * internet + 0.15 * freq
  return round(min(100.0, max(0.0, composite)), 1)


def generate_rationale(
    county_name: str,
    disasters_count: int,
    nri_risk: float | None,
    social_vuln: float | None,
    no_internet_pct: float | None,
    historical_web_pct: float | None,
) -> str:
  """Generates concise, factual rationale for team deployment."""
  parts = []
  if disasters_count >= 2:
    parts.append(f"{disasters_count} disaster declarations since 2023")
  elif disasters_count == 1:
    parts.append("1 recent disaster declaration")

  if nri_risk is not None and nri_risk >= 60:
    parts.append(f"elevated FEMA hazard risk ({nri_risk:.1f})")
  if social_vuln is not None and social_vuln >= 60:
    parts.append(f"high social vulnerability ({social_vuln:.1f})")
  if no_internet_pct is not None and no_internet_pct >= 15:
    parts.append(f"{no_internet_pct:.1f}% households lack internet")
  if historical_web_pct is not None and historical_web_pct < 60:
    parts.append(f"historical online registration only {historical_web_pct:.0f}%")

  parts.append("no mobile response team within 75 miles")
  return f"{county_name}: " + "; ".join(parts) + "."
