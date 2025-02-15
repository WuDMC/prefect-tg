resource "google_storage_bucket" "bucket" {
  name          = var.gcp_bucket
  project       = var.gcp_project
  location      = var.gcp_region
  storage_class = var.storage_class
  force_destroy = var.force_destroy

  uniform_bucket_level_access = true
}
