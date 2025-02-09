resource "google_project_service" "enable_apis" {
  for_each = toset(var.api_list)

  service = each.value
  project = var.gcp_project
  disable_on_destroy = false
}
