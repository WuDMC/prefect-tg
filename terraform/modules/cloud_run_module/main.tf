resource "google_cloud_run_service" "prefect_worker" {
  name     = "prefect-worker"
  location = var.gcp_region # Укажи нужный регион

  template {
    spec {
      containers {
        image = "prefecthq/prefect:3-latest"

        env {
          name  = "PREFECT_API_URL"
          value = var.prefect_api_url
        }
        env {
          name  = "PREFECT_API_KEY"
          value = var.prefect_api_key
        }

        args = [
          "prefect", "worker", "start", "--install-policy", "always", "--with-healthcheck", "-p", var.prefect_work_pool, "-t", "cloud-run"
        ]

        startup_probe {
          http_get {
            path = "/health"
            port = 8080
          }
          initial_delay_seconds = 100
          period_seconds        = 20
          timeout_seconds       = 20
        }
      }
    }

    metadata {
      annotations = {
        "run.googleapis.com/no-cpu-throttling" = "true"
        "autoscaling.knative.dev/minScale"    = "1"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "invoker" {
  service  = google_cloud_run_service.prefect_worker.name
  location = google_cloud_run_service.prefect_worker.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.service_account}"
}
