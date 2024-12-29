from prefect import task
from prefect.logging import get_run_logger
import os
import logging

from tg_jobs_parser.telegram_helper.telegram_parser import TelegramParser
from tg_jobs_parser.google_cloud_helper.storage_manager import StorageManager
from tg_jobs_parser.google_cloud_helper.bigquery_manager import BigQueryManager
from tg_jobs_parser.utils import json_helper
from tg_jobs_parser.configs import vars, volume_folder_path
from google.api_core.exceptions import NotFound


# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s"
# )
# logging.getLogger("tg_jobs_parser").setLevel(logging.INFO)
#
# logger = logging.getLogger()
#
# if not logger.handlers:
#     console_handler = logging.StreamHandler()
#     console_handler.setLevel(logging.INFO)
#     console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
#     logger.addHandler(console_handler)
#
# logger.setLevel(logging.INFO)


def check_table_exists():
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info(f"Checking if table {vars.BIGQUERY_DATASET}.{vars.BIGQUERY_UPLOAD_STATUS_TABLE} exists.")
        bigquery_manager = BigQueryManager(vars.PROJECT_ID)
        bigquery_manager.client.get_table(
            f"{vars.BIGQUERY_DATASET}.{vars.BIGQUERY_UPLOAD_STATUS_TABLE}"
        )
        return True
    except NotFound:
        prefect_logger.warning("Table not found.")
        return False

def upload_msg_bq(path):
    prefect_logger = get_run_logger()

    if not path:
        prefect_logger.info("No files to process. Be happy!")
        return

    prefect_logger.info(f"Uploading file {path} to BigQuery.")
    bigquery_manager = BigQueryManager(vars.PROJECT_ID)

    return bigquery_manager.load_json_uri_to_bigquery(
        path=path,
        table_id=f"{vars.BIGQUERY_DATASET}.{vars.BIGQUERY_RAW_MESSAGES_TABLE}",
    )

@task
def list_msgs():
    prefect_logger = get_run_logger()

    prefect_logger.info("Listing messages from storage.")
    storage_manager = StorageManager()
    return storage_manager.list_msgs_with_metadata()

@task
def check_files_statuses():
    prefect_logger = get_run_logger()
    if check_table_exists:
        bigquery_manager = BigQueryManager(vars.PROJECT_ID)
        prefect_logger.info("Querying message files statuses from BigQuery.")
        return bigquery_manager.query_msg_files_statuses(
            dataset_id=vars.BIGQUERY_DATASET,
            table_id=vars.BIGQUERY_UPLOAD_STATUS_TABLE,
        )
    else:
        prefect_logger.warning("No uploaded files status to fetch.")
        return []


@task
def process_all_files(gsc_files, last_status_files, output_file):
    prefect_logger = get_run_logger()

    if not gsc_files:
        prefect_logger.info("No files found in storage.")
        return False

    if not last_status_files:
        prefect_logger.info("No files found in BigQuery statuses.")
        return False

    not_processed_files_set = {
        file["filename"] for file in last_status_files if file["status"] != "done"
    }
    if len(not_processed_files_set) == 0:
        prefect_logger.info("All files already proceeded. WELL DONE. >> cerveza time")
        return False

    data = []
    process_status = 0
    process_len = len(gsc_files)
    for file in gsc_files:
        process_status += 1
        logging.info(f"Processed {process_status} from {process_len} GCS files")
        match = vars.MSGS_FILE_PATTERN.match(file["name"])
        if file["name"] in not_processed_files_set and match:
            logging.info(f"File {file['name']} ready to load to BQ.")
        elif file["name"] in not_processed_files_set:
            logging.warning(f"Filename {file['name']} does not match the expected pattern.")
            continue
        else:
            continue

        uploaded = upload_msg_bq(path=file["full_path"])
        if uploaded:
            row = json_helper.make_row_msg_status(file, match, status="done")
            data.append(row)

    if not data:
        prefect_logger.info("No data to save.")
        return False

    json_helper.save_to_line_delimited_json(data, output_file)
    prefect_logger.info(f"Temporary file with uploaded message files created at {output_file}")
    return output_file


@task
def update_status_table(file_path):
    prefect_logger = get_run_logger()
    prefect_logger.info(f"Uploading file {file_path} to BigQuery.")
    bigquery_manager = BigQueryManager(vars.PROJECT_ID)

    return bigquery_manager.load_json_to_bigquery(
        json_file_path=file_path,
        table_id=f"{vars.BIGQUERY_DATASET}.{vars.BIGQUERY_UPLOAD_STATUS_TABLE}",
    )




@task
def check_msg_files_in_process():
    prefect_logger = get_run_logger()
    if check_table_exists():
        prefect_logger.info(f" table {vars.BIGQUERY_DATASET}.{vars.BIGQUERY_UPLOAD_STATUS_TABLE} exists.")
        prefect_logger.info("Fetching uploaded files from BigQuery.")
        bigquery_manager = BigQueryManager(vars.PROJECT_ID)

        return bigquery_manager.fetch_data(
            dataset_id=vars.BIGQUERY_DATASET,
            table_id=vars.BIGQUERY_UPLOAD_STATUS_TABLE,
            selected_fields="filename",
        )
    else:
        prefect_logger.warning("No uploaded files to fetch.")
        return []


@task
def download_and_process_files(gsc_files, bigquery_files, output_file):
    prefect_logger = get_run_logger()

    if not gsc_files:
        prefect_logger.info("No files found in storage.")
        return False

    existing_files_set = set(file["filename"] for file in bigquery_files)
    data = []
    process_status = 0
    process_len = len(gsc_files)
    for file in gsc_files:
        process_status += 1
        logging.info(f"Processed {process_status} from {process_len} GCS files")
        # prefect_logger.info(f"Processed {process_status} from {process_len} GCS files")
        if file["name"] in existing_files_set:
            continue

        match = vars.MSGS_FILE_PATTERN.match(file["name"])
        if not match:
            prefect_logger.warning(f"Filename {file['name']} does not match the expected pattern.")
            continue

        row = json_helper.make_row_msg_status(file, match, status="in process")
        data.append(row)

    if not data:
        prefect_logger.info("No new files to process.")
        return False

    # Save data to a temporary file
    json_helper.save_to_line_delimited_json(data, output_file)
    prefect_logger.info(f"Temporary file with msg_files statuses created at {output_file}")

    return output_file


@task
def get_metadata_from_cloud(path):
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Initializing StorageManager...")
        storage_manager = StorageManager()
        prefect_logger.info("Getting metadata from cloud")
        storage_manager.download_channels_metadata(path=path)
        prefect_logger.info(f"Metadata downloaded to {path}")
    except Exception as e:
        prefect_logger.error(f"Error in get_metadata_from_cloud: {e}")
        raise


@task
def parse_tg_dialogs(path):
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Initializing TelegramParser...")
        tg_parser = TelegramParser()
        prefect_logger.info("Start parsing tg dialogs")
        data = tg_parser.get_channels()
        json_helper.save_to_json(data=data, path=path)
        prefect_logger.info(f"Dialogs saved to {path}")
    except Exception as e:
        prefect_logger.error(f"Error in parse_tg_dialogs: {e}")
        raise


@task
def update_target_ids(
        cloud_channels_file,
        tg_channels_file,
        date=vars.START_DATE,
        force=False):
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Initializing TelegramParser...")
        tg_parser = TelegramParser()
        prefect_logger.info("Updating metadata locally")
        cloud_channels = json_helper.read_json(cloud_channels_file) or {}
        tg_channels = json_helper.read_json(tg_channels_file)
        json_helper.set_target_ids(tg_channels, cloud_channels, tg_parser, date, force)
        json_helper.save_to_json(cloud_channels, cloud_channels_file)
        prefect_logger.info(f"Updated metadata saved to {cloud_channels_file}")
    except Exception as e:
        prefect_logger.error(f"Error in update_target_ids: {e}")
        raise


@task
def update_last_updated_ids(
            file1_path,
            file2_path,
            output_path):
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Merging metadata to update last posted IDs in tg channels")
        json_helper.merge_json_files(
            file1_path=file1_path,
            file2_path=file2_path,
            output_path=output_path,
        )
        prefect_logger.info(f"Merged metadata saved to {output_path}")
    except Exception as e:
        prefect_logger.error(f"Error in update_last_updated_ids: {e}")
        raise


@task
def update_metadata_in_cloud(source_file_name):
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Initializing StorageManager...")
        storage_manager = StorageManager()
        prefect_logger.info("Updating metadata in cloud")
        storage_manager.update_channels_metadata(source_file_name=source_file_name)
        prefect_logger.info(f"Metadata in cloud updated with {source_file_name}")
    except Exception as e:
        prefect_logger.error(f"Error in update_metadata_in_cloud: {e}")
        raise





@task
def check_channel_stats():
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Initializing StorageManager...")
        storage_manager = StorageManager()
        prefect_logger.info("Checking stats")
        storage_manager.check_channel_stats()
        return storage_manager.statistics
    except Exception as e:
        prefect_logger.error(f"Error in check_channel_stats: {e}")
        raise



@task
def parse_messages(path):
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Downloading channels metadata")
        storage_manager = StorageManager()
        msg_parser = TelegramParser()

        storage_manager.download_channels_metadata(path=path)
        channels = json_helper.read_json(path)
        process_status = 0
        process_len = len(channels.items())

        for ch_id, channel in channels.items():
            process_status += 1
            prefect_logger.info(f"Processed {process_status} from {process_len} channels")
            if channel["status"] == "bad" or channel["type"] != "ChatType.CHANNEL":
                continue

            prefect_logger.info(f"Parsing messages for channel {ch_id}")
            msgs, left, right = msg_parser.run_chat_parser(channel)

            if msgs:
                json_helper.save_to_line_delimited_json(
                    msgs,
                    os.path.join(
                        volume_folder_path,
                        f"msgs{ch_id}_left_{left}_right_{right}.json",
                    ),
                )
            else:
                prefect_logger.info(f"Nothing to save for channel: {ch_id}")
    except Exception as e:
        prefect_logger.error(f"Error parsing messages: {e}")
        raise


@task
def upload_msgs_files_to_storage(file_path_1, file_path_2, output_path):
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Uploading message files to storage")
        storage_manager = StorageManager()
        results = {}

        for filename in os.listdir(volume_folder_path):
            match = vars.MSGS_FILE_PATTERN.match(filename)
            if match:
                chat_id = match.group("chat_id")
                left = int(match.group("left"))
                right = int(match.group("right"))
                blob_path = f"{chat_id}/{filename}"
                uploaded = storage_manager.upload_message(
                    os.path.join(volume_folder_path, filename), blob_path
                )

                if uploaded:
                    results[chat_id] = {
                        "new_left_saved_id": left,
                        "new_right_saved_id": right,
                        "uploaded_path": blob_path,
                    }
                    storage_manager.delete_local_file(
                        os.path.join(volume_folder_path, filename)
                    )

        json_helper.save_to_json(results, file_path_2)
        json_helper.update_uploaded_borders(file_path_1, file_path_2, output_path)
        storage_manager.update_channels_metadata(output_path)
        prefect_logger.info("Uploaded message files to storage successfully")
    except Exception as e:
        prefect_logger.error(f"Error uploading messages to storage: {e}")
        raise



@task
def delete_tmp_file(file_path):
    prefect_logger = get_run_logger()

    try:
        os.remove(file_path)
        prefect_logger.info(f"Temporary file {file_path} deleted")
    except OSError as e:
        prefect_logger.error(f"Error deleting temporary file {file_path}: {e}")




@task
def check_uploaded_files_statuses():
    # task 6
    prefect_logger = get_run_logger()
    prefect_logger.info(f"Checking {vars.BIGQUERY_DATASET}.{vars.BIGQUERY_UPLOAD_STATUS_TABLE}")
    bigquery_manager = BigQueryManager(vars.PROJECT_ID)

    return bigquery_manager.check_table_stats(
        f"{vars.BIGQUERY_DATASET}.{vars.BIGQUERY_UPLOAD_STATUS_TABLE}"
    )


@task
def check_raw_messages_statuses():
    # task 8
    prefect_logger = get_run_logger()
    bigquery_manager = BigQueryManager(vars.PROJECT_ID)
    prefect_logger.info(f"Checking {vars.BIGQUERY_DATASET}.{vars.BIGQUERY_RAW_MESSAGES_TABLE}")
    return bigquery_manager.check_table_stats(
        f"{vars.BIGQUERY_DATASET}.{vars.BIGQUERY_RAW_MESSAGES_TABLE}"
    )