#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found. Run: cp .env.example .env and set GCP_PROJECT_ID first."
  exit 1
fi

set -a
source .env
set +a

echo "=== [1/4] Loading Data Commons + OpenFEMA Graph into Spanner (DCGraph) ==="
python3 01_data/loader/load_spanner.py

echo "=== [2/4] Building BigQuery Borderless Lakehouse (Apache Iceberg + SitRep PDF Object Table) ==="
python3 01_data/01_setup_borderless_lakehouse.py

echo "=== [3/4] Configuring Knowledge Catalog Glossary, AspectType, EntryLinks & 5-Stage Lineage ==="
python3 04_knowledge_catalog/01_setup_knowledge_catalog.py

echo "=== [4/4] Deploying Gemini Data Analytics Golden Playbooks ==="
python3 05_agents/deploy_gemini_gda_agent.py

echo ""
echo "DONE! Project Beacon is live in project ${GCP_PROJECT_ID}."
echo "Spanner Studio:    https://console.cloud.google.com/spanner/instances/${SPANNER_INSTANCE}/databases/${SPANNER_DATABASE}/details/query?project=${GCP_PROJECT_ID}"
echo "BigQuery Studio:   https://console.cloud.google.com/bigquery?project=${GCP_PROJECT_ID}"
echo "Knowledge Catalog: https://console.cloud.google.com/dataplex/studio?project=${GCP_PROJECT_ID}"
