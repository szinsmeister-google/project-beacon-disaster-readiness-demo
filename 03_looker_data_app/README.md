# Project Beacon — Material Design 3 Looker Data App

Interactive Looker Data App (`app.js`) uniting Google Data Commons (`country/USA`) and Cloud Spanner Graph (`DCGraph`):
- **FEMA Mobile DRC & BRIC Grant Simulator:** Slide the governed **Knowledge Catalog SVI Threshold (`>= 75.0`)** and **$10M–$250M Grant Allocation** to compute Mobile DRC vans (`$1.2M/unit`), ADA Para-Transit shuttles (`$450K/unit`), and projected drop in unserved offline households.
- **One-Click Spanner Write-Back:** Commits prioritized county dispatch actions directly into `DeploymentPlan` in Cloud Spanner or Spanner Omni.

## Deploy via Looker Data Apps Toolkit
```bash
git clone https://github.com/looker-open-source/looker-data-apps.git ~/looker-data-apps
cp 03_looker_data_app/app.js ~/looker-data-apps/apps/beacon-disaster-readiness/app.js
cd ~/looker-data-apps && ./scripts/deploy.sh beacon-disaster-readiness
```
