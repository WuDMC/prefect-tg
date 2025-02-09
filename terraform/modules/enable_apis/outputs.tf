output "enabled_apis" {
  description = "List of enabled APIs"
  value       = keys(google_project_service.enable_apis)
}
