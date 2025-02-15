terraform {
  required_version = ">= 1.4.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
  credentials = file(var.credentials)
}

module "enable_apis" {
  source      = "./modules/enable_apis"
  gcp_project = var.gcp_project
  api_list = [
    "cloudresourcemanager.googleapis.com", # Управление проектом
    "bigquery.googleapis.com",             # BigQuery API
    "cloudfunctions.googleapis.com",       # Cloud Functions API
    "storage.googleapis.com",              # Cloud Storage API
    "artifactregistry.googleapis.com",     # Для хранения контейнеров
    "cloudbuild.googleapis.com",           # CI/CD для сборки Cloud Functions
    "eventarc.googleapis.com",             # EventArc для триггеров Cloud Storage
    "pubsub.googleapis.com"                # Pub/Sub, требуется для Cloud Functions с GCS-триггером
  ]
}
# Подключение модуля для BigQuery
module "bigquery" {
  source      = "./modules/bigquery_module"
  gcp_project = var.gcp_project
  gcp_region  = var.gcp_region
  bq_dataset  = var.bq_dataset
  bq_table    = var.bq_table
}

module "cloud_storage" {
  source        = "./modules/cloud_storage_module"
  gcp_project   = var.gcp_project
  gcp_region    = var.gcp_region
  gcp_bucket    = var.gcp_bucket
}


# Подключение модуля Cloud Functions
module "cloud_functions" {
  source            = "./modules/cloud_function_module"
  gcp_project       = var.gcp_project
  gcp_region        = var.gcp_region
  gcp_bucket        = var.gcp_bucket
  function_name     = var.function_name
  function_entry_point = var.function_entry_point
  runtime           = var.function_runtime
}
