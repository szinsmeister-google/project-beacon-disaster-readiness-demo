#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ -f .env ]]; then
  set -a; source .env; set +a
fi

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID in .env}"
SPANNER_INSTANCE="${SPANNER_INSTANCE:-dc-graph-demo}"
BQ_DATASET_ID="${BQ_DATASET_ID:-beacon_disaster_readiness}"
BQ_LAKEHOUSE_CONN="${BQ_LAKEHOUSE_CONN:-beacon_lakehouse_conn}"
GCS_LAKEHOUSE_BUCKET="${GCS_LAKEHOUSE_BUCKET:-${GCP_PROJECT_ID}-beacon-lakehouse}"

echo "Deleting BigQuery dataset ${GCP_PROJECT_ID}:${BQ_DATASET_ID}..."
bq rm -r -f -d "${GCP_PROJECT_ID}:${BQ_DATASET_ID}" || true

echo "Deleting BigLake connection ${BQ_LAKEHOUSE_CONN}..."
bq rm --connection --location="us" "${GCP_PROJECT_ID}.us.${BQ_LAKEHOUSE_CONN}" || true

echo "Deleting GCS bucket gs://${GCS_LAKEHOUSE_BUCKET}..."
gcloud storage rm --recursive "gs://${GCS_LAKEHOUSE_BUCKET}" || true

echo "Deleting Cloud Spanner instance ${SPANNER_INSTANCE}..."
gcloud spanner instances delete "${SPANNER_INSTANCE}" --project="${GCP_PROJECT_ID}" --quiet || true

echo "Cleanup complete."
