"""Deploys the Cymbal agent to Agent Runtime (Gemini Conversational Analytics Agent Platform) and smoke-tests it.

Idempotent. Steps:
  1. Reuses the Agent Runtime instance recorded in data/deployment.json, or creates an empty
     one. Creating it first provisions the platform's service agent
     (service-PROJECT_NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com), which must have
     access to the secret before the agent container starts.
  2. Grants that service agent roles/spanner.databaseUser on the demo database (reads plus the
     shortlist write) and roles/secretmanager.secretAccessor on the Data Commons key.
  3. Runs `adk deploy agent_engine` into that instance with a generated config: plain env
     vars, a Secret Manager reference for the key (the value never leaves Secret Manager),
     and scaling limits.
  4. Asks the deployed agent one question and prints the answer and the tools it called.

Usage:
  python scripts/deploy_agent.py                 # deploy or update, then smoke-test
  python scripts/deploy_agent.py --smoke-test    # only the smoke test
  python scripts/deploy_agent.py --delete        # delete the Agent Runtime instance
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time

from _common import (ADK, AGENT_DIR, AGENT_MODEL, DC_SECRET_ID, DEPLOY_DIR, DESCRIPTION, DISPLAY_NAME,
                     MODEL_LOCATION, PROJECT, REGION, SPANNER_DATABASE, SPANNER_INSTANCE, die, gcloud,
                     load_state, playground_url, project_number, require_project, rerender_docs,
                     retry_gcloud, save_state, vertex_client)

SMOKE_QUESTION = "In two sentences: how are we set for next season and what is our primary coverage gap?"


def ensure_engine(client, state: dict) -> str:
  name = state.get("reasoning_engine")
  if name:
    try:
      client.agent_engines.get(name=name)
      print(f"  reusing {name}")
      return name
    except Exception as e:  # pylint: disable=broad-except
      print(f"  recorded instance is gone ({type(e).__name__}); creating a new one")
  engine = client.agent_engines.create()
  name = engine.api_resource.name
  state["reasoning_engine"] = name
  save_state(state)
  print(f"  created {name}")
  return name


def latest_secret_version() -> str:
  out = gcloud("secrets", "versions", "list", DC_SECRET_ID, "--filter=state=ENABLED",
               "--sort-by=~createTime", "--limit=1", "--format=value(name)")
  if not out:
    die(f"Secret {DC_SECRET_ID} has no enabled version. Run scripts/01_setup_gcp.sh first.")
  return out.rsplit("/", 1)[-1]


def write_config(secret_version: str) -> str:
  config = {
      "display_name": DISPLAY_NAME,
      "description": DESCRIPTION,
      "env_vars": {
          "SPANNER_PROJECT": PROJECT,
          "SPANNER_INSTANCE": SPANNER_INSTANCE,
          "SPANNER_DATABASE": SPANNER_DATABASE,
          "AGENT_MODEL": AGENT_MODEL,
          "MODEL_LOCATION": MODEL_LOCATION,
          "JEV_MODEL": os.environ.get("JEV_MODEL", "gemini-2.5-flash"),
          "JEV_LOCATION": os.environ.get("JEV_LOCATION", "us-central1"),
          "DC_API_KEY": {"secret": DC_SECRET_ID, "version": secret_version},
          "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
          "ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS": "false",
      },
      # One warm instance avoids a cold start on stage; a demo never needs more than a few.
      "min_instances": int(os.environ.get("AGENT_MIN_INSTANCES", "1")),
      "max_instances": int(os.environ.get("AGENT_MAX_INSTANCES", "3")),
      "resource_limits": {"cpu": "2", "memory": "2Gi"},
      "container_concurrency": 5,
      "labels": {"demo": "dc-spanner-graph"},
  }
  DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
  path = DEPLOY_DIR / "agent_engine_config.json"
  path.write_text(json.dumps(config, indent=2))
  return str(path)


def smoke_test(client, name: str, question: str = SMOKE_QUESTION) -> bool:
  print(f"\nSmoke test: {question!r}")
  remote = client.agent_engines.get(name=name)
  t0 = time.time()
  texts, calls, errors = [], [], []
  try:
    for event in remote.stream_query(user_id="deploy-smoke-test", message=question):
      if not isinstance(event, dict):
        continue
      if event.get("error_message") or event.get("error_code"):
        errors.append(f"{event.get('error_code')}: {event.get('error_message')}")
      for part in ((event.get("content") or {}).get("parts") or []):
        call = part.get("function_call") or part.get("functionCall")
        if call:
          calls.append(call.get("name"))
        if part.get("text") and not part.get("thought"):
          texts.append(part["text"])
  except Exception as e:  # pylint: disable=broad-except
    errors.append(f"{type(e).__name__}: {str(e)[:800]}")
  print(f"  tools called: {calls or 'none'}")
  print(f"  answer ({time.time() - t0:.1f}s): {''.join(texts).strip()[:1200] or '(none)'}")
  ok = bool(texts) and not errors
  if errors:
    print(f"  errors: {errors}")
  if not ok:
    engine_id = name.rsplit("/", 1)[-1]
    print("  Logs: gcloud logging read 'resource.type=\"aiplatform.googleapis.com/ReasoningEngine\" AND "
          f"resource.labels.reasoning_engine_id=\"{engine_id}\"' --project {PROJECT} --limit 50 --freshness 30m")
  return ok


def main() -> None:
  ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
  ap.add_argument("--smoke-test", action="store_true", help="Only run the smoke test.")
  ap.add_argument("--delete", action="store_true", help="Delete the Agent Runtime instance.")
  ap.add_argument("--question", default=SMOKE_QUESTION, help="Smoke-test question.")
  args = ap.parse_args()
  require_project()
  state = load_state()
  client = vertex_client()

  if args.delete:
    name = state.get("reasoning_engine")
    if not name:
      print("No Agent Runtime instance recorded in data/deployment.json.")
      return
    print(f"Deleting {name} (and its sessions) ...")
    client.agent_engines.delete(name=name, force=True)
    state.pop("reasoning_engine", None)
    save_state(state)
    print("  deleted")
    return

  if args.smoke_test:
    name = state.get("reasoning_engine") or die("Nothing deployed yet.")
    raise SystemExit(0 if smoke_test(client, name, args.question) else 1)

  print("Checking prerequisites ...")
  gcloud("spanner", "databases", "describe", SPANNER_DATABASE, "--instance", SPANNER_INSTANCE,
         "--format=value(state)")
  version = latest_secret_version()
  print(f"  Spanner {SPANNER_INSTANCE}/{SPANNER_DATABASE} OK; secret {DC_SECRET_ID} version {version}")

  print("1. Agent Runtime instance")
  name = ensure_engine(client, state)

  print("2. Access for the Agent Runtime service agent")
  sa = f"service-{project_number()}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
  retry_gcloud(f"roles/spanner.databaseUser on {SPANNER_DATABASE} to {sa}",
               "spanner", "databases", "add-iam-policy-binding", SPANNER_DATABASE,
               "--instance", SPANNER_INSTANCE, "--member", f"serviceAccount:{sa}",
               "--role", "roles/spanner.databaseUser")
  retry_gcloud(f"roles/secretmanager.secretAccessor on {DC_SECRET_ID} to {sa}",
               "secrets", "add-iam-policy-binding", DC_SECRET_ID, "--member", f"serviceAccount:{sa}",
               "--role", "roles/secretmanager.secretAccessor")

  print("3. adk deploy agent_engine (builds a container; typically 5-10 minutes)")
  config_path = write_config(version)
  cmd = [ADK, "deploy", "agent_engine", "--project", PROJECT, "--region", REGION,
         "--agent_engine_id", name, "--agent_engine_config_file", config_path,
         "--display_name", DISPLAY_NAME, "--description", DESCRIPTION, str(AGENT_DIR)]
  t0 = time.time()
  subprocess.run(cmd, check=True)
  state.update({"deployed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "service_agent": sa, "model": AGENT_MODEL, "region": REGION})
  save_state(state)
  print(f"  deployed in {(time.time() - t0) / 60:.1f} min")

  print("4. Smoke test")
  ok = smoke_test(client, name)
  print(f"\nAgent Runtime: {name}\nPlayground:    {playground_url(name)}")
  rerender_docs()
  print("Next: python scripts/register_ge.py register   (dry run; add --apply to register)")
  raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
  main()
