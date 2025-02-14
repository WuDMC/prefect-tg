resource "google_bigquery_dataset" "bq_dataset" {
  dataset_id = var.bq_dataset
  project    = var.gcp_project
  location   = var.gcp_region

  lifecycle {
    prevent_destroy = false
  }
}

resource "google_bigquery_table" "bq_table" {
  dataset_id = google_bigquery_dataset.bq_dataset.dataset_id
  table_id   = var.bq_table
  schema     = file("${path.module}/schema.json")

}
