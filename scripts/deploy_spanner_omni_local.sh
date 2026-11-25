#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPANNER_DATABASE="${SPANNER_DATABASE:-readiness_dcgraph}"
OMNI_IMAGE="${SPANNER_OMNI_IMAGE:-us-docker.pkg.dev/spanner-omni/images/spanner-omni:2026.r2.1-beta}"

echo "Starting containerized Spanner Omni (${OMNI_IMAGE}) on localhost:15000..."
docker volume create spanner >/dev/null
docker rm -f spanneromni >/dev/null 2>&1 || true
docker run -d --network host --name spanneromni -v "spanner:/spanner" "${OMNI_IMAGE}" start-single-server

echo "Waiting 8s for Spanner Omni to initialize..."
sleep 8

docker exec spanneromni /google/spanner/bin/spanner databases create "${SPANNER_DATABASE}" || true
docker cp "${ROOT_DIR}/01_data/schema/ddl.sql" spanneromni:/tmp/ddl.sql
docker exec spanneromni /google/spanner/bin/spanner databases ddl update "${SPANNER_DATABASE}" --ddl-file=/tmp/ddl.sql

echo ""
echo "Spanner Omni is ready at localhost:15000 (database: ${SPANNER_DATABASE})!"
echo "Export SPANNER_OMNI_ENDPOINT=localhost:15000 in your shell or .env to point Project Beacon to Spanner Omni."
