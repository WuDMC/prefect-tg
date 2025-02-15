output "cloud_function_url" {
  description = "Cloud Function HTTP URL"
  value       = google_cloudfunctions_function.msg2bq.https_trigger_url
}
