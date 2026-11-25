# ============================================================================
# Mandatory go/demos Click-to-Deploy (C2D) Platform-Injected Variables (8)
# ============================================================================

variable "project_id" {
  type        = string
  description = "The GCP or Argolis Project ID where Project Beacon resources will be deployed."
}

variable "project_name" {
  type        = string
  description = "The human-readable GCP Project Name."
  default     = ""
}

variable "project_number" {
  type        = string
  description = "The numeric GCP Project Number."
  default     = ""
}

variable "org_id" {
  type        = string
  description = "The GCP Organization ID."
  default     = ""
}

variable "gcp_account_name" {
  type        = string
  description = "The user account email triggering the Click-to-Deploy run."
  default     = ""
}

variable "deployment_service_account_name" {
  type        = string
  description = "The service account used by the Demo Automation Platform to execute Terraform."
  default     = ""
}

variable "data_location" {
  type        = string
  description = "Default Google Cloud region for Spanner and Knowledge Catalog resources."
  default     = "us-central1"
}

variable "secret_stored_project" {
  type        = string
  description = "The GCP project ID where dynamically generated demo secrets are stored."
  default     = ""
}

# ============================================================================
# Demo-Specific Configuration Variables
# ============================================================================

variable "spanner_instance_id" {
  type        = string
  description = "Cloud Spanner instance identifier for DCGraph."
  default     = "dc-graph-demo"
}

variable "spanner_database_id" {
  type        = string
  description = "Cloud Spanner database identifier."
  default     = "readiness_dcgraph"
}

variable "bq_dataset_id" {
  type        = string
  description = "BigQuery dataset identifier for the Borderless Lakehouse."
  default     = "beacon_disaster_readiness"
}
