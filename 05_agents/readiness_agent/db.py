"""Spanner access for the agent.

One lazily created client per process. Analytic reads use a 10-second exact
staleness snapshot (TrueTime-backed, lock-free reads that never block writers);
reads that must see the user's own writes use strong reads.
"""

from __future__ import annotations

import base64
import datetime as dt
import decimal
import os
import pathlib
import threading
from typing import Any

from dotenv import load_dotenv
from google.cloud import spanner
from google.cloud.spanner_v1 import param_types as T

REPO = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(REPO / ".env")

_lock = threading.Lock()
_database = None

STALENESS_SECONDS = 10


def settings() -> dict[str, str]:
  return {
      "project": os.environ.get("SPANNER_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT_ID", ""),
      "instance": os.environ.get("SPANNER_INSTANCE", "dc-graph-demo"),
      "database": os.environ.get("SPANNER_DATABASE", "readiness_dcgraph"),
  }


def database():
  global _database
  with _lock:
    if _database is None:
      s = settings()
      proj = s["project"] or None
      client = None
      omni_endpoint = os.environ.get("SPANNER_OMNI_ENDPOINT", "").strip()
      if omni_endpoint:
        from google.cloud.spanner_v1 import InstanceType
        client = spanner.Client(client_options={"api_endpoint": omni_endpoint}, instance_type=InstanceType.OMNI, use_plain_text=True)
        _database = client.instance("default").database(s["database"])
        return _database
      if False:
        try:
          import subprocess
          from google.oauth2.credentials import Credentials
          tok = subprocess.check_output(
              [gcloud_bin, "auth", "application-default", "print-access-token"],
              text=True, stderr=subprocess.DEVNULL, timeout=10).strip()
          if tok:
            client = spanner.Client(project=proj, credentials=Credentials(tok), disable_builtin_metrics=True)
        except Exception:
          pass
      if client is None:
        client = spanner.Client(project=proj, disable_builtin_metrics=True)
      _database = client.instance(s["instance"]).database(s["database"])
  return _database


def jsonable(v: Any) -> Any:
  if isinstance(v, (dt.datetime, dt.date)):
    return v.isoformat()
  if isinstance(v, decimal.Decimal):
    return float(v)
  if isinstance(v, bytes):
    return base64.b64encode(v).decode()
  if isinstance(v, float):
    return round(v, 4)
  if isinstance(v, list):
    return [jsonable(x) for x in v]
  return v


def _types_for(params: dict[str, Any]) -> dict[str, Any]:
  out = {}
  for k, v in params.items():
    if isinstance(v, bool):
      out[k] = T.BOOL
    elif isinstance(v, int):
      out[k] = T.INT64
    elif isinstance(v, float):
      out[k] = T.FLOAT64
    elif isinstance(v, (list, tuple)):
      out[k] = T.Array(T.STRING)
    else:  # str or None
      out[k] = T.STRING
  return out


def query(sql: str, params: dict[str, Any] | None = None, *, strong: bool = False,
          max_rows: int | None = None, timeout: float = 60) -> list[dict[str, Any]]:
  """Runs a read-only SQL or GQL query and returns rows as JSON-safe dicts."""
  params = params or {}
  kwargs = {} if strong else {"exact_staleness": dt.timedelta(seconds=STALENESS_SECONDS)}
  rows = []
  with database().snapshot(**kwargs) as snap:
    rs = snap.execute_sql(sql, params=params or None,
                          param_types=_types_for(params) or None, timeout=timeout)
    for r in rs:
      rows.append(r)
      if max_rows is not None and len(rows) >= max_rows:
        break
    fields = [f.name for f in (rs.fields or [])]
  return [{k: jsonable(v) for k, v in zip(fields, r)} for r in rows]


def execute_dml(statements: list[tuple[str, dict[str, Any]]]) -> int:
  """Runs DML statements in one read-write transaction; returns rows modified."""

  def work(txn):
    total = 0
    for sql, params in statements:
      total += txn.execute_update(sql, params=params, param_types=_types_for(params))
    return total

  return database().run_in_transaction(work)
