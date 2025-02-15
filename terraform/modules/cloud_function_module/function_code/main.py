import os
import json
import logging
from google.cloud import bigquery
import functions_framework

logging.basicConfig(
    level=logging.INFO,
    format='{"message": "%(message)s", "severity": "%(levelname)s"}'
)

@functions_framework.cloud_event
def gcs_to_bigquery(cloud_event):
    """
    Cloud Function triggered by a change in a GCS bucket.
    Processes files where the file name starts with 'msgs'.
    """
    # Извлечение данных события из CloudEvent
    print(f"cloud_event: {cloud_event}")
    event_data = cloud_event.data
    print(f"event_data: {event_data}")
    event_id = cloud_event["id"]
    event_type = cloud_event["type"]
    print(f"Event ID: {event_id}")
    print(f"Event type: {event_type}")
    file_name = event_data['name']
    bucket_name = event_data['bucket']

    # Проверка имени файла

    if not (
        file_name.startswith("job_parser/")  # Убедимся, что файл находится в папке "job_parser"
        and file_name.endswith(".json")     # Проверяем, что файл имеет расширение .json
        and os.path.basename(file_name).startswith("msgs")  # Убедимся, что имя файла начинается с "msgs"
    ):
        print(f"Skipped: {file_name} (does not meet required conditions)")
        return { "success": False, "blob": file_name }


    # Параметры BigQuery
    project_id = os.environ.get("PROJECT_ID")
    dataset_id = os.environ.get("DATASET_ID")
    table_id = os.environ.get("TABLE_ID")

    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    # Путь к файлу в GCS
    uri = f"gs://{bucket_name}/{file_name}"

    # Инициализация клиента BigQuery
    client = bigquery.Client(project=project_id)
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        autodetect=False,
        schema=[
            bigquery.SchemaField("id", "INTEGER"),
            bigquery.SchemaField("empty", "BOOLEAN"),
            bigquery.SchemaField("text", "STRING"),
            bigquery.SchemaField("datetime", "TIMESTAMP"),
            bigquery.SchemaField("date", "DATE"),
            bigquery.SchemaField("link", "STRING"),
            bigquery.SchemaField("sender_chat_id", "STRING"),
            bigquery.SchemaField("sender_chat_user_name", "STRING"),
            bigquery.SchemaField("user", "STRING"),
            bigquery.SchemaField("user_name", "STRING"),
            bigquery.SchemaField("chat_id", "STRING"),
        ]
    )

    # Запуск загрузки в BigQuery
    load_job = client.load_table_from_uri(uri, table_ref, job_config=job_config)
    load_job.result()  # Ожидание завершения задания

    # Логирование успеха
    print(f"Successfully loaded {file_name} into {table_ref}")
    return { "success": True, "blob": file_name }
