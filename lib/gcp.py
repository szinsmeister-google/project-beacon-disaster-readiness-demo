"""Environment-driven Google Cloud REST, Cloud Spanner, and Spanner Omni helpers."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import google.auth
import google.auth.transport.requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")


def env(key: str, default: str = "", required: bool = False) -> str:
    val = os.environ.get(key, default).strip()
    if required and not val:
        raise RuntimeError(f"Missing required environment variable: {key}. Copy .env.example to .env first.")
    return val


def get_project_id() -> str:
    return env("GCP_PROJECT_ID", env("GOOGLE_CLOUD_PROJECT", env("SPANNER_PROJECT")), required=True)


def get_project_number() -> str:
    num = env("GCP_PROJECT_NUMBER")
    if num and num != "123456789012":
        return num
    pid = get_project_id()
    st, data = api_call("GET", f"https://cloudresourcemanager.googleapis.com/v1/projects/{pid}")
    if st == 200 and isinstance(data, dict) and data.get("projectNumber"):
        return str(data["projectNumber"])
    raise RuntimeError("Set GCP_PROJECT_NUMBER in .env (could not auto-resolve via Cloud Resource Manager).")


def get_region() -> str:
    return env("GCP_REGION", "us-central1")


def get_access_token() -> str:
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


def get_headers(content_type: str = "application/json") -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "X-Goog-User-Project": get_project_id(),
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def api_call(
    method: str,
    url: str,
    body: Any = None,
    params: dict[str, str] | None = None,
    content_type: str = "application/json",
    timeout: int = 90,
) -> tuple[int, Any]:
    if params:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{urllib.parse.urlencode(params)}"
    if body is None:
        payload = None
    elif isinstance(body, (bytes, bytearray)):
        payload = body
    elif isinstance(body, str):
        payload = body.encode("utf-8")
    else:
        payload = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers=get_headers(content_type), method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if raw and content_type == "application/json":
                try:
                    return resp.status, json.loads(raw)
                except json.JSONDecodeError:
                    return resp.status, raw
            return resp.status, raw
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def wait_for_lro(
    op_name: str,
    base_api: str = "https://dataplex.googleapis.com/v1",
    max_polls: int = 90,
    poll_interval: float = 2.0,
) -> dict[str, Any]:
    if not op_name or not op_name.startswith("projects/"):
        return {}
    url = f"{base_api}/{op_name}"
    for _ in range(max_polls):
        st, data = api_call("GET", url)
        if st == 200 and isinstance(data, dict) and data.get("done"):
            if "error" in data:
                raise RuntimeError(f"Long-running operation failed: {data['error']}")
            return data
        time.sleep(poll_interval)
    raise TimeoutError(f"Timed out waiting for LRO: {op_name}")


def get_spanner_database():
    """Connects transparently to either Managed Cloud Spanner or local Docker Spanner Omni."""
    from google.cloud import spanner

    omni_endpoint = env("SPANNER_OMNI_ENDPOINT")
    db_id = env("SPANNER_DATABASE", "readiness_dcgraph")
    if omni_endpoint:
        from google.cloud.spanner_v1 import InstanceType

        client = spanner.Client(
            client_options={"api_endpoint": omni_endpoint},
            instance_type=InstanceType.OMNI,
            use_plain_text=True,
        )
        return client.instance("default").database(db_id)

    project_id = get_project_id()
    instance_id = env("SPANNER_INSTANCE", "dc-graph-demo")
    client = spanner.Client(project=project_id)
    return client.instance(instance_id).database(db_id)
