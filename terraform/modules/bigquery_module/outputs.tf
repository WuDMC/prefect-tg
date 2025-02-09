output "bigquery_table_id" {
  description = "The ID of the BigQuery table"
  value       = google_bigquery_table.example_table.id
}
