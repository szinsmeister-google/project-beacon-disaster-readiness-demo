# Demo Guide: Project Beacon — U.S. Disaster Readiness & Policy Intelligence on the Agentic Data Cloud

This guide satisfies the 4-Pillar Demo Quality rubric (**Setup**, **How to Access**, **How to Build & Walkthrough**, and **Talking Script for Sellers**) for Customer Engineers, Solutions Architects, and public developers.

---

## Pillar 1: Setup & Prerequisites

### Prerequisites & Required IAM Roles
Deploy into a clean **Argolis** or standard GCP project with Billing enabled. Required IAM roles for deployment:
- `roles/spanner.admin` (Enterprise Cloud Spanner instance + `DCGraph` database)
- `roles/bigquery.admin` & `roles/bigquery.connectionAdmin` (BigQuery Borderless Lakehouse, BigLake Apache Iceberg tables, and Object Tables)
- `roles/storage.admin` (GCS bucket for Apache Iceberg Parquet data and 12 unstructured FEMA Field SitRep PDFs)
- `roles/dataplex.admin` & `roles/datalineage.admin` (Knowledge Catalog Business Glossary, Custom AspectType, EntryLinks, and 5-Stage Lineage)
- `roles/aiplatform.user` & `roles/geminidataanalytics.dataAgentCreator` (Vertex AI Agent Engine + Gemini Conversational Analytics)

### Provision & Deploy
```bash
git clone https://github.com/szinsmeister-google/project-beacon-disaster-readiness-demo.git
cd project-beacon-disaster-readiness-demo
cp .env.example .env
# Populate GCP_PROJECT_ID and GCP_PROJECT_NUMBER in .env

cd click-to-deploy && terraform init && terraform apply -var="project_id=<YOUR_PROJECT_ID>" && cd ..
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./scripts/deploy_all.sh
```

*(Optional Tactical Edge Mode)* To demonstrate disconnected field operations on **Spanner Omni**, run `./scripts/deploy_spanner_omni_local.sh` and set `SPANNER_OMNI_ENDPOINT=localhost:15000`.

### Reset & Teardown
- **Reset between live demos:** `python3 scripts/reset_demo.py`
- **Full cleanup:** `./scripts/cleanup.sh` (or `terraform destroy` in `click-to-deploy/`)

---

## Pillar 2: How to Access the Demo

Open these 5 browser tabs left-to-right before presenting (run `terraform output` in `click-to-deploy/` to print exact project-scoped links):

| Tab | Surface | Direct URL Template | Pre-Flight State |
| --- | --- | --- | --- |
| **Tab 1** | **Data Commons** | `https://datacommons.org/place/country/USA` | United States (`country/USA`) knowledge graph overview loaded. |
| **Tab 2** | **Spanner Studio (`DCGraph`)** | `https://console.cloud.google.com/spanner/instances/dc-graph-demo/databases/readiness_dcgraph/details/query?project=<PROJECT_ID>` | Paste Query Option B (`01_data/sql/spanner_gql_queries.sql`), click **Run**, switch to **Graph** tab (39 nodes, 64 edges). |
| **Tab 3** | **BigQuery Studio (Borderless Lakehouse)** | `https://console.cloud.google.com/bigquery?project=<PROJECT_ID>` | Paste Query Option C (`01_data/sql/bigquery_lakehouse_queries.sql`) joining `noaa_hazard_iceberg`, `fema_field_assessments_iceberg`, and `fema_field_sitrep_objects`. |
| **Tab 4** | **Knowledge Catalog** | `https://console.cloud.google.com/dataplex/studio?project=<PROJECT_ID>` | Open Glossary `beacon-disaster-readiness-glossary` (12 terms) and inspect 5-Stage Lineage on `CountyReadiness`. |
| **Tab 5** | **Gemini Agent & Looker Data App** | Registered Conversational Analytics agent + Looker Data App (`03_looker_data_app/app.js`) | Fresh chat showing the 3 Golden Prompts + Looker M3 Data App at default `$250M` simulator baseline. |

---

## How to Build

1. **Unified Data Commons × OpenFEMA Spanner Graph (`01_data/schema/ddl.sql` & `01_data/loader/load_spanner.py`):** Loads 3,144 U.S. counties, geographic hierarchies (`continent -> country -> censusregion -> censusdivision -> state -> county`), OpenFEMA disaster declarations/registrations, and agency mobile response teams into a single dynamic-label `CREATE PROPERTY GRAPH DCGraph` schema that runs identically on Managed Cloud Spanner and containerized Spanner Omni.
2. **Borderless Lakehouse (`01_data/01_setup_borderless_lakehouse.py`):** Generates 12 valid unstructured FEMA Field SitRep PDFs in GCS, creates BigLake Object Table `fema_field_sitrep_objects`, provisions two BigLake Managed Apache Iceberg tables (`noaa_hazard_iceberg`, `fema_field_assessments_iceberg`), and exposes unified view `v_borderless_lakehouse_dispatch`.
3. **Knowledge Catalog Governance & 5-Stage Lineage (`04_knowledge_catalog/01_setup_knowledge_catalog.py`):** Provisions 12 federal policy glossary terms (`SVI >= 75.0`, `No Internet >= 18.0%`, `No Vehicle >= 10.0%`), attaches custom `beacon-federal-governance` aspects to `@spanner` entries, creates `definition` and `schema-join` EntryLinks, and publishes 5-stage end-to-end lineage via `datalineage.googleapis.com`.
4. **GEV System-One ADK Agent (`05_agents/readiness_agent/jev.py` & `agent.py`):** Implements `jev_noul` and `jev_choice` 1-token logprob classifiers (`max_output_tokens=1, response_logprobs=True, thinking_budget=0`), `JevGatedMcpToolset` (0.0 ms MCP skip when local Spanner answers the query), and `before_model_jev_router` pre-execution, cutting end-to-end latency from ~18.0s to 3.30s.
5. **Deterministic Golden Playbooks & Looker M3 Data App (`05_agents/deploy_gemini_gda_agent.py`, `02_lookml/`, `03_looker_data_app/app.js`):** Embeds top-of-card Altair specs (`parts[0]`) for zero-drift visualizations alongside a single-Explore LookML model and a `$250M` FEMA Mobile DRC Grant Simulator with Spanner write-back.

---

## Demo Walkthrough (Pillar 3 & Pillar 4: Step-by-Step Walkthrough & Seller Talking Script)

### Beat 1 — Public Ground Truth + Operational Graph (`Tab 1` & `Tab 2`, 0:00 – 1:00)
- **Do:** Briefly show `datacommons.org/place/country/USA`, then run Query Option B in **Spanner Studio** and click **Graph**.
- **Say (Seller Hook):** *"98% of disaster intake assumes broadband and a car—yet our highest-vulnerability counties have up to 35% of households offline. By unifying Google Data Commons geographic hierarchies with live OpenFEMA operations in Spanner Graph, one 10-millisecond ISO GQL query surfaces every Tier-1 vulnerable county with zero mobile response coverage—and runs identically on Cloud Spanner or disconnected Spanner Omni field kits."*
- **See:** 39-node, 64-edge connected graph tracing `North America -> USA -> Region -> State -> Unserved Counties -> Recommended Mobile Units -> FEMA Hubs -> Federal Agencies`.

### Beat 2 — Borderless Lakehouse: Apache Iceberg + Unstructured SitRep PDFs (`Tab 3`, 1:00 – 1:45)
- **Do:** Run Query Option C in **BigQuery Studio** joining `county_readiness`, `noaa_hazard_iceberg`, `fema_field_assessments_iceberg`, and `fema_field_sitrep_objects`.
- **Say (Seller Hook):** *"Field reconnaissance reports arrive as unstructured PDFs in Cloud Storage, while NOAA hazard feeds sit in open Apache Iceberg tables. BigQuery's Borderless Lakehouse joins all three modalities with zero ETL in 1.2 seconds."*
- **See:** Priority counties (`Martin County, KY`, `Taylor County, FL`, `Buncombe County, NC`) paired with live cell-tower outage percentages, road washouts, and GCS SitRep PDF URIs.

### Beat 3 — Statutory Policy Governance in Knowledge Catalog (`Tab 4`, 1:45 – 2:25)
- **Do:** Open `beacon-disaster-readiness-glossary` and click into `Social Vulnerability Score (SVI Tier-1 >= 75.0)` and `Household Digital Divide (No Internet >= 18.0%)`, then view 5-stage lineage.
- **Say (Seller Hook):** *"An AI agent should never improvise federal eligibility rules. Knowledge Catalog binds our 12 statutory thresholds, FedRAMP classifications, and column-level lineage directly to Spanner, BigQuery, Gemini, and Looker."*

### Beat 4 — 5.5x Faster Conversational Analytics & Looker M3 Grant Simulator (`Tab 5`, 2:25 – 3:30)
- **Do:** Ask the Gemini agent: *"How does a county's household internet deficit correlate with online FEMA disaster registration share?"* (OLS scatter plot `r = -0.95` renders at top of card), then *"Which high-vulnerability disaster counties have no mobile response team coverage?"* Switch to the **Looker Data App**, slide the **Federal Mobile Response Grant** to `$250M`, and click **Commit Deployment Plan to Spanner**.
- **Say (Seller Hook):** *"Using GEV System-One routing, we cut agent latency 5.5x—from 18 seconds to 3.3 seconds—with charts pinned to the top of the card. And in our Material Design 3 Looker Data App, commanders simulate a $250M mobile fleet allocation and commit dispatches straight back to Spanner in one click."*
