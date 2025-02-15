resource "null_resource" "zip_function_code" {
  triggers = {
    always_run = timestamp() # Этот триггер заставляет ресурс выполняться каждый раз
  }

  provisioner "local-exec" {
    command = <<EOT
    echo "Current directory: $(pwd)"
    cd ${path.module}/function_code
    echo "Contents of function_code directory:"
    ls
    zip -r ../function_code.zip .
    echo "Created function_code.zip in $(pwd)/../"
    EOT
  }
}



resource "google_storage_bucket_object" "function_code" {
  depends_on = [null_resource.zip_function_code]

  name   = "function_code.zip"
  bucket = google_storage_bucket.function_code_bucket.name
  source = "${path.module}/function_code.zip"

  lifecycle {
    # Удаляет ресурс, если файл не существует
    ignore_changes = [
      source
    ]
  }
}

resource "google_storage_bucket" "function_code_bucket" {
  name     = "${var.gcp_project}-functions-code"
  location = var.gcp_region
}

resource "google_cloudfunctions_function" "example_function" {
  name        = var.function_name
  description = "Example Cloud Function"
  runtime     = var.runtime
  entry_point = var.function_entry_point
  source_archive_bucket = google_storage_bucket.function_code_bucket.name
  source_archive_object = google_storage_bucket_object.function_code.name
#  trigger_http = true
  event_trigger {
    event_type = "google.storage.object.finalize" # Событие при загрузке нового файла
    resource   = var.gcp_bucket # Бакет, который мы создали ранее
  }

  environment_variables = {
    PROJECT_ID  = var.gcp_project
    DATASET_ID  = var.bq_dataset
    TABLE_ID    = var.bq_table
  }
}
