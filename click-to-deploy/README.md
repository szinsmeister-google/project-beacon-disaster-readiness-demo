# Click-to-Deploy (C2D) & Argolis Terraform Kit

Conforms to the `go/demos` Demo Automation Platform requirements:
- Declares all **8 mandatory platform-injected variables** (`project_id`, `project_name`, `project_number`, `org_id`, `gcp_account_name`, `deployment_service_account_name`, `data_location`, `secret_stored_project`).
- Provisions Cloud Spanner Enterprise (`100` PU for ISO GQL `DCGraph`), BigQuery `US` Borderless Lakehouse dataset, uniform-access GCS bucket, BigLake Cloud Resource connection + `roles/storage.objectAdmin` binding, least-privilege IAM SA, and Secret Manager secret.
- Restores secure-by-default Argolis organization policies in `org_policy/project_config.json`.

## Manual Argolis / GCP Run
```bash
cd click-to-deploy
terraform init
terraform apply -var="project_id=${GCP_PROJECT_ID}" -var="data_location=us-central1"
```
