"""Minimal Data Commons REST v2 client (api.datacommons.org).

Uses POST requests with the X-API-Key header, retries on throttling and server
errors, follows `nextToken` pagination, and chunks large node lists.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Iterable

BASE_URL = "https://api.datacommons.org/v2"


class DataCommons:

  def __init__(self, api_key: str, base_url: str = BASE_URL, timeout: int = 180,
               max_retries: int = 6):
    self.api_key = api_key
    self.base_url = base_url.rstrip("/")
    self.timeout = timeout
    self.max_retries = max_retries
    self.calls = 0

  # --------------------------------------------------------------------------
  def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(body).encode()
    delay = 2.0
    for attempt in range(self.max_retries + 1):
      req = urllib.request.Request(
          f"{self.base_url}/{path}", data=data, method="POST",
          headers={"X-API-Key": self.api_key, "Content-Type": "application/json"})
      try:
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
          self.calls += 1
          return json.loads(resp.read())
      except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:500]
        if e.code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
          time.sleep(delay)
          delay = min(delay * 2, 60)
          continue
        raise RuntimeError(f"Data Commons {path} HTTP {e.code}: {detail}") from e
      except (urllib.error.URLError, TimeoutError) as e:
        if attempt < self.max_retries:
          time.sleep(delay)
          delay = min(delay * 2, 60)
          continue
        raise RuntimeError(f"Data Commons {path} failed: {e}") from e
    raise RuntimeError("unreachable")

  # --------------------------------------------------------------------------
  def node(self, nodes: Iterable[str], prop: str, chunk: int = 400) -> dict[str, dict]:
    """Returns {dcid: {arc_name: [node_or_value dicts]}} for a relation expression."""
    nodes = list(dict.fromkeys(nodes))
    out: dict[str, dict] = {}
    for i in range(0, len(nodes), chunk):
      body: dict[str, Any] = {"nodes": nodes[i:i + chunk], "property": prop}
      while True:
        resp = self._post("node", body)
        for dcid, d in (resp.get("data") or {}).items():
          arcs = out.setdefault(dcid, {})
          for arc, a in (d.get("arcs") or {}).items():
            arcs.setdefault(arc, []).extend(a.get("nodes") or [])
          for p in d.get("properties") or []:
            arcs.setdefault("__properties__", []).append(p)
        token = resp.get("nextToken")
        if not token:
          break
        body["nextToken"] = token
    return out

  def node_values(self, nodes: Iterable[str], props: list[str]) -> dict[str, dict[str, list]]:
    """Returns {dcid: {prop: [value or dcid, ...]}} for outgoing properties."""
    raw = self.node(nodes, "->[" + ", ".join(props) + "]")
    out: dict[str, dict[str, list]] = {}
    for dcid, arcs in raw.items():
      out[dcid] = {p: [n.get("dcid") or n.get("value") for n in arcs.get(p, [])] for p in props}
    return out

  def children(self, parents: Iterable[str], child_type: str) -> dict[str, list[dict]]:
    """Returns {parent: [{dcid, name, types}]} for places contained (transitively) in parent."""
    raw = self.node(parents, f"<-containedInPlace+{{typeOf:{child_type}}}")
    return {p: [n for arc_nodes in arcs.values() for n in arc_nodes if "dcid" in n]
            for p, arcs in raw.items()}

  # --------------------------------------------------------------------------
  def observation(self, variables: list[str], *, entity_dcids: list[str] | None = None,
                  entity_expression: str | None = None, date: str = "LATEST",
                  facet_ids: list[str] | None = None,
                  select: tuple[str, ...] = ("entity", "variable", "date", "value", "facet"),
                  chunk: int = 800) -> tuple[list[tuple], dict[str, dict]]:
    """Fetches observations.

    Returns (rows, facets) where rows are (entity, variable, date, value, facet_id,
    obs_count, earliest, latest) and facets maps facet_id -> facet metadata.
    """
    rows: list[tuple] = []
    facets: dict[str, dict] = {}
    if entity_expression:
      entity_batches = [{"expression": entity_expression}]
    else:
      ids = list(dict.fromkeys(entity_dcids or []))
      entity_batches = [{"dcids": ids[i:i + chunk]} for i in range(0, len(ids), chunk)]
    for entity in entity_batches:
      body: dict[str, Any] = {"date": date, "variable": {"dcids": variables},
                              "entity": entity, "select": list(select)}
      if facet_ids:
        body["filter"] = {"facet_ids": facet_ids}
      while True:
        resp = self._post("observation", body)
        facets.update(resp.get("facets") or {})
        for var, vdata in (resp.get("byVariable") or {}).items():
          for ent, edata in (vdata.get("byEntity") or {}).items():
            for f in edata.get("orderedFacets") or []:
              fid = f.get("facetId")
              obs = f.get("observations") or [{}]
              for o in obs:
                rows.append((ent, var, o.get("date"), o.get("value"), fid,
                             f.get("obsCount"), f.get("earliestDate"), f.get("latestDate")))
        token = resp.get("nextToken")
        if not token:
          break
        body["nextToken"] = token
    return rows, facets
