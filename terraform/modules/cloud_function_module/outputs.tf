output "cloud_function_url" {
  description = "Cloud Function HTTP URL"
  value       = google_cloudfunctions_function.example_function.https_trigger_url
}
