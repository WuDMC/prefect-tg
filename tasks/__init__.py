from prefect import task
from prefect.logging import get_run_logger
import os
import logging
from dotenv import load_dotenv
from config import Config
from tg_jobs_parser.google_cloud_helper.storage_manager import StorageManager
from tg_jobs_parser.utils import json_helper
from tg_jobs_parser.configs import vars, volume_folder_path
from prefect.concurrency.sync import rate_limit


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.getLogger("tg_jobs_parser").setLevel(logging.INFO)

load_dotenv()
env_file = os.getenv('PROJECT_VARS')
logger = logging.getLogger()
global_config = Config(env_file=env_file)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

logger.setLevel(logging.INFO)


@task
def list_msgs():
    # flow 1--8, 2-2, 2-5
    prefect_logger = get_run_logger()

    prefect_logger.info("Listing messages from storage.")
    storage_manager = StorageManager(json_config=global_config.to_json())
    return storage_manager.list_msgs_with_metadata()


@task
def get_metadata_from_cloud(path):
    # flow 1-1
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Initializing StorageManager...")
        storage_manager = StorageManager(json_config=global_config.to_json())
        prefect_logger.info("Getting metadata from cloud")
        storage_manager.download_blob(blob_name=storage_manager.config.source_channels_blob,
                                      path=path)
        prefect_logger.info(f"Metadata downloaded to {path}")
    except Exception as e:
        prefect_logger.error(f"Error in get_metadata_from_cloud: {e}")
        raise


@task
def check_limits():
    # need to create limit pools in advance
    rate_limit("api-calls")
    rate_limit("log-submissions")

@task
def parse_tg_dialogs(tg_channels_file, cloud_channels_file, force=False):
    # flow 1-2
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Initializing TelegramParser...")
        from tg_jobs_parser.telegram_helper.telegram_parser import TelegramParser

        tg_parser = TelegramParser(json_config=global_config.to_json())
        prefect_logger.info("Start parsing tg dialogs")
        channels_data = tg_parser.get_channels()
        json_helper.save_to_json(data=channels_data, path=tg_channels_file)
        prefect_logger.info(f"Dialogs metadata saved to {tg_channels_file}")
        prefect_logger.info("Updating metadata locally")
        cloud_channels = json_helper.read_json(cloud_channels_file) or {}
        date = tg_parser.config.get('telegram', 'start_date')
        # set start date and ids
        prefect_logger.info(f"getting target_ids for date {date}")
        cloud_channels = tg_parser.run_set_start_ids(cloud_channels=cloud_channels, date=date, force=force)
        json_helper.save_to_json(cloud_channels, cloud_channels_file)
        prefect_logger.info(f"Updated metadata saved to {cloud_channels_file}")
    except Exception as e:
        prefect_logger.error(f"Error in parse_tg_dialogs: {e}")
        raise


@task
def update_target_ids(
        cloud_channels_file,
        tg_channels_file,
        force=False):
    # flow 1-3
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Initializing TelegramParser...")
        from tg_jobs_parser.telegram_helper.telegram_parser import TelegramParser

        tg_parser = TelegramParser(json_config=global_config.to_json())
        prefect_logger.info("Updating metadata locally")
        cloud_channels = json_helper.read_json(cloud_channels_file) or {}
        # tg_channels = json_helper.read_json(tg_channels_file)
        date = tg_parser.config.get('telegram', 'start_data')
        tg_parser.run_set_target_ids(cloud_channels=cloud_channels, date=date, force=force)
        # json_helper.set_target_ids(tg_channels, cloud_channels, tg_parser, date, force)
        json_helper.save_to_json(cloud_channels, cloud_channels_file)
        prefect_logger.info(f"Updated metadata saved to {cloud_channels_file}")
    except Exception as e:
        prefect_logger.error(f"Error in update_target_ids: {e}")
        raise


@task
def update_last_updated_ids(
        cl_file_path,
        tg_file_path,
        output_path):
    prefect_logger = get_run_logger()
    # flow 1-4
    try:
        prefect_logger.info("Merging metadata to update last posted IDs in tg channels")
        json_helper.merge_json_files(
            file1_path=cl_file_path,
            file2_path=tg_file_path,
            output_path=output_path,
        )
        prefect_logger.info(f"Merged metadata saved to {output_path}")
    except Exception as e:
        prefect_logger.error(f"Error in update_last_updated_ids: {e}")
        raise


@task
def update_metadata_in_cloud(source_file_name):
    #flow 1-5
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Initializing StorageManager...")
        storage_manager = StorageManager(json_config=global_config.to_json())
        prefect_logger.info("Updating metadata in cloud")
        storage_manager.update_channels_metadata(source_file_name=source_file_name)
        prefect_logger.info(f"Metadata in cloud updated with {source_file_name}")
    except Exception as e:
        prefect_logger.error(f"Error in update_metadata_in_cloud: {e}")
        raise


@task
def check_channel_stats():
    # flow 1-7, 2-1
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Initializing StorageManager...")
        storage_manager = StorageManager(json_config=global_config.to_json())
        prefect_logger.info("Checking stats")
        storage_manager.check_channel_stats(type_filter="ChatType.CHANNEL")
        statistics = storage_manager.statistics
        prefect_logger.info(f'total download scope: {statistics["download_scope"]}')
        prefect_logger.info(f'msg downloaded: {statistics["total_downloaded"]}')
        prefect_logger.info(f'Left to download: {statistics["download_scope"] - statistics["total_downloaded"]}')
        prefect_logger.info(f'channels_total: {statistics["channels_total"]}')
        prefect_logger.info(f'channels_done: {statistics["channels_done"]}')
        prefect_logger.info(f'channels_to_update: {statistics["channels_to_update"]}')
        prefect_logger.info(
            f'channels_to_update_ids: {statistics["to_upd_channels_ids"]}'
        )
        prefect_logger.info(f'bad_channels: {statistics["bad_channels"]}')
        prefect_logger.info(f'bad_channels_ids: {statistics["bad_channels_ids"]}')
        return statistics
    except Exception as e:
        prefect_logger.error(f"Error in check_channel_stats: {e}")
        raise


@task
def parse_messages(path):
    # flow 2-3
    last_index = "last_index.txt"

    def get_last_index(filename):
        try:
            with open(filename, "r") as file:
                value = file.read().strip()
                try:
                    logging.warning(f'Found last index file with value {value}')
                    return int(value)
                except ValueError:
                    logging.warning(f"error: fie {filename} not found")
                    return 0
        except FileNotFoundError:
            logging.warning(f"error: fie {filename} not found")
            return 0
        except Exception as e:
            logging.warning(f"reading file error {e}")
            return 0

    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Start parsing messages")

        storage_manager = StorageManager(json_config=global_config.to_json())
        from tg_jobs_parser.telegram_helper.telegram_parser import TelegramParser

        msg_parser = TelegramParser(json_config=global_config.to_json())
        if not os.path.exists(path):
            prefect_logger.info("Downloading channels metadata")
            storage_manager.download_blob(blob_name=storage_manager.config.source_channels_blob,
                                          path=path)
            process_status = 0
        else:
            prefect_logger.info(f"File {path} with channels found")
            # process_status = get_last_index(last_index)
            process_status = 0
            prefect_logger.info(f"Continue parsing from {process_status}")
        channels = json_helper.read_json(path)
        process_len = len(channels.items())
        for ch_id, channel in channels.items():
            with open(last_index, "w") as file:
                file.write(str(process_status))
            process_status += 1
            prefect_logger.info(f"Processed {process_status} from {process_len} channels")
            if channel["status"] == "bad" or channel["type"] != "ChatType.CHANNEL":
                continue

            prefect_logger.info(f"Parsing messages for channel {ch_id}")
            msgs, left, right = msg_parser.run_chat_parser(channel)
            prefect_logger.info(f"Parsed {len(msgs)} messages for channel {ch_id}")

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
def upload_msgs_files_to_storage(cl_file_path, up_file_path, output_path):
    # flow 2-4
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Uploading message files to storage")
        storage_manager = StorageManager(json_config=global_config.to_json())
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
                    prefect_logger.info(f' file {blob_path} uploaded: {uploaded}')
                    results[chat_id] = {
                        "new_left_saved_id": left,
                        "new_right_saved_id": right,
                        "uploaded_path": blob_path,
                    }
                    os.remove(os.path.join(volume_folder_path, filename))

        json_helper.save_to_json(results, up_file_path)
        json_helper.update_uploaded_borders(cl_file_path, up_file_path, output_path)
        storage_manager.update_channels_metadata(output_path)
        prefect_logger.info("Uploaded message files to storage successfully")
    except Exception as e:
        prefect_logger.error(f"Error uploading messages to storage: {e}")
        raise


@task
def delete_tmp_file(file_path):
    # flow 1-6, 2-6
    prefect_logger = get_run_logger()

    try:
        os.remove(file_path)
        prefect_logger.info(f"Temporary file {file_path} deleted")
    except OSError as e:
        prefect_logger.error(f"Error deleting temporary file {file_path}: {e}")