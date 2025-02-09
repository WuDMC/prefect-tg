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
}

module "enable_apis" {
  source      = "./modules/enable_apis"
  gcp_project = var.gcp_project
  api_list = [
    "cloudresourcemanager.googleapis.com", # Для управления проектом
    "bigquery.googleapis.com",             # BigQuery API
    "cloudfunctions.googleapis.com",       # Cloud Functions API
    "storage.googleapis.com",               # Cloud Storage API
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com"
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

# Подключение модуля Cloud Functions
module "cloud_functions" {
  source            = "./modules/cloud_function_module"
  gcp_project       = var.gcp_project
  gcp_region        = var.gcp_region
  function_name     = var.function_name
  function_entry_point = var.function_entry_point
  runtime           = var.function_runtime
}
