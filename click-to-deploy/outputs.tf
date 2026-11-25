output "spanner_studio_url" {
  description = "Direct link to Cloud Spanner Studio query editor for DCGraph."
  value       = "https://console.cloud.google.com/spanner/instances/${google_spanner_instance.beacon.name}/databases/${google_spanner_database.beacon_db.name}/details/query?project=${var.project_id}"
}

output "bigquery_studio_url" {
  description = "Direct link to BigQuery Borderless Lakehouse dataset."
  value       = "https://console.cloud.google.com/bigquery?project=${var.project_id}&p=${var.project_id}&d=${google_bigquery_dataset.beacon.dataset_id}&page=dataset"
}

output "knowledge_catalog_studio_url" {
  description = "Direct link to Knowledge Catalog Studio."
  value       = "https://console.cloud.google.com/dataplex/studio?project=${var.project_id}"
}

output "lakehouse_bucket_uri" {
  description = "GCS bucket storing Apache Iceberg tables and unstructured FEMA SitRep PDFs."
  value       = "gs://${google_storage_bucket.lakehouse_bucket.name}"
}

output "biglake_connection_service_account" {
  description = "Service account for BigLake Apache Iceberg & Object Table federation."
  value       = google_bigquery_connection.lakehouse_conn.cloud_resource[0].service_account_id
}
