output "bigquery_table_id" {
  description = "BigQuery Table ID"
  value       = google_bigquery_table.bq_table.id
}
output "bigquery_dataset_id" {
  description = "BigQuery Table ID"
  value       = google_bigquery_dataset.bq_dataset.id
}
