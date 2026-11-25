# Argolis CE Setup & `go/demos` Publishing Guide

This guide walks Google Cloud Customer Engineers (CEs) through deploying **Project Beacon** into an **Argolis** project and registering it on **`go/demos`**.

---

## 1. Argolis Sandbox Checklist

1. **Create or select a clean Argolis project** with Billing enabled and `>= 100` Cloud Spanner Processing Units quota in `us-central1`.
2. **Organization Policy Compliance:**
   - All GCS buckets enforce `uniform_bucket_level_access = true`.
   - Zero public SSH firewall rules (`0.0.0.0/0`), zero hardcoded credentials, and BigLake federation uses Terraform-managed `google_bigquery_connection` with least-privilege bucket IAM.
   - `click-to-deploy/org_policy/project_config.json` keeps standard Argolis org policies restored (`true`).
3. **Authenticate & Deploy:**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   gcloud config set project <YOUR_ARGOLIS_PROJECT_ID>
   gcloud auth application-default set-quota-project <YOUR_ARGOLIS_PROJECT_ID>

   cp .env.example .env
   # Set GCP_PROJECT_ID and GCP_PROJECT_NUMBER in .env

   cd click-to-deploy && terraform init && terraform apply -var="project_id=<YOUR_ARGOLIS_PROJECT_ID>" && cd ..
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ./scripts/deploy_all.sh
   ```
4. **Optional: Deploy ADK + GEV Agent to Vertex AI Agent Engine:**
   ```bash
   python3 05_agents/deploy_adk_agent.py
   ```
5. **Optional: Disconnected Tactical Edge Demo (Spanner Omni):**
   ```bash
   ./scripts/deploy_spanner_omni_local.sh
   ```

---

## 2. Launching on `go/demos` (Git-Based Demo & Click-to-Deploy)

1. **Metadata Manifest (`_metadata.yaml`):** Pre-validated against `go/demos` rules:
   - 4 active `ProductsV3` slugs (`cloud_spanner`, `bigquery`, `dataplex`, `looker_google_cloud_core`).
   - Pure Markdown block scalars (`|`), zero HTML tags, <= 1,000 characters per section.
   - Points `demo_guide` to the 4-Pillar `DEMO_GUIDE.md` with literal `## How to Build` and `## Demo Walkthrough` headings.
2. **Click-to-Deploy (`click-to-deploy/`):**
   - Declares all **8 mandatory Demo Automation variables** in `click-to-deploy/variables.tf`.
   - After submitting on `go/demos/demo/bulk`, copy your assigned `<DEMO_ID>`, uncomment `click_to_deploy_path: <DEMO_ID>-project-beacon-disaster-readiness-demo/tree/main/click-to-deploy` in `_metadata.yaml`, and run **Sync -> Validate -> Update Demo**.
