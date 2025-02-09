resource "google_bigquery_dataset" "example_dataset" {
  dataset_id = var.bq_dataset
  project    = var.gcp_project
  location   = var.gcp_region
}

resource "google_bigquery_table" "example_table" {
  dataset_id = google_bigquery_dataset.example_dataset.dataset_id
  table_id   = var.bq_table
  schema     = file("${path.module}/schema.json")
}
