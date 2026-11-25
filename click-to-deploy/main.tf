terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.data_location
}

locals {
  secret_project = var.secret_stored_project != "" ? var.secret_stored_project : var.project_id
  required_apis = toset([
    "spanner.googleapis.com",
    "bigquery.googleapis.com",
    "biglake.googleapis.com",
    "bigqueryconnection.googleapis.com",
    "storage.googleapis.com",
    "dataplex.googleapis.com",
    "datalineage.googleapis.com",
    "aiplatform.googleapis.com",
    "geminidataanalytics.googleapis.com",
    "discoveryengine.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
  ])
  runtime_sa_roles = toset([
    "roles/spanner.databaseUser",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/dataplex.catalogEditor",
    "roles/storage.objectAdmin",
    "roles/aiplatform.user",
  ])
}

# 1. Enable Required Google Cloud APIs
resource "google_project_service" "apis" {
  for_each           = local.required_apis
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# 2. Cloud Spanner Instance (Enterprise Edition for ISO GQL Spanner Graph)
resource "google_spanner_instance" "beacon" {
  project          = var.project_id
  name             = var.spanner_instance_id
  config           = "regional-${var.data_location}"
  display_name     = "Project Beacon Data Commons x Spanner Graph"
  processing_units = 100
  edition          = "ENTERPRISE"
  depends_on       = [google_project_service.apis]
}

resource "google_spanner_database" "beacon_db" {
  project             = var.project_id
  instance            = google_spanner_instance.beacon.name
  name                = var.spanner_database_id
  database_dialect    = "GOOGLE_STANDARD_SQL"
  deletion_protection = false
  depends_on          = [google_spanner_instance.beacon]
}

# 3. BigQuery Dataset (US multi-region) for Borderless Lakehouse
resource "google_bigquery_dataset" "beacon" {
  project                    = var.project_id
  dataset_id                 = var.bq_dataset_id
  friendly_name              = "Project Beacon Disaster Readiness (Borderless Lakehouse)"
  description                = "U.S. Public Sector Disaster Readiness combining Data Commons, OpenFEMA, Apache Iceberg hazard telemetry, and unstructured FEMA SitRep PDFs."
  location                   = "US"
  delete_contents_on_destroy = true
  depends_on                 = [google_project_service.apis]
}

# 4. GCS Bucket for Apache Iceberg Tables & Unstructured FEMA SitRep PDFs
resource "google_storage_bucket" "lakehouse_bucket" {
  project                     = var.project_id
  name                        = "${var.project_id}-beacon-lakehouse"
  location                    = "US"
  uniform_bucket_level_access = true
  force_destroy               = true
  depends_on                  = [google_project_service.apis]
}

# 5. BigLake Cloud Resource Connection + IAM Binding on Lakehouse Bucket
resource "google_bigquery_connection" "lakehouse_conn" {
  project       = var.project_id
  connection_id = "beacon_lakehouse_conn"
  location      = "US"
  friendly_name = "Beacon Borderless Lakehouse Connection"
  cloud_resource {}
  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket_iam_member" "lakehouse_conn_sa_access" {
  bucket = google_storage_bucket.lakehouse_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_bigquery_connection.lakehouse_conn.cloud_resource[0].service_account_id}"
}

# 6. Least-Privilege Agent & Enrichment Service Account
resource "google_service_account" "beacon_sa" {
  project      = var.project_id
  account_id   = "beacon-agent-sa"
  display_name = "Project Beacon Agent & Knowledge Catalog SA"
  depends_on   = [google_project_service.apis]
}

resource "google_project_iam_member" "beacon_sa_roles" {
  for_each = local.runtime_sa_roles
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.beacon_sa.email}"
}

# 7. Dynamic Secret Manager Entry for Optional Data Commons API Key Placeholder
resource "random_password" "beacon_session_secret" {
  length  = 24
  special = false
}

resource "google_secret_manager_secret" "beacon_session_secret" {
  project   = local.secret_project
  secret_id = "beacon-demo-session-secret"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "beacon_session_secret_ver" {
  secret      = google_secret_manager_secret.beacon_session_secret.id
  secret_data = random_password.beacon_session_secret.result
}
