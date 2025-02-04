from prefect import flow
from prefect.logging import get_run_logger
import tasks
import os
from tg_jobs_parser.configs import volume_folder_path

CL_CHANNELS_LOCAL_PATH = os.path.join(volume_folder_path, "f1.1_gsc_channels_metadata.json")
TG_CHANNELS_LOCAL_PATH = os.path.join(volume_folder_path, "f1.1_tg_channels_metadata.json")
MG_CHANNELS_LOCAL_PATH = os.path.join(volume_folder_path, "f1.1_merged_channels_metadata.json")


@flow
def find_msg_4parsing():
    # 1
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Starting Telegram Metadata Flow")
        # get ids of messages to parse
        tasks.get_metadata_from_cloud(CL_CHANNELS_LOCAL_PATH)
        tasks.parse_tg_dialogs(tg_channels_file=TG_CHANNELS_LOCAL_PATH, cloud_channels_file=CL_CHANNELS_LOCAL_PATH)
        # merge files to update range what to download
        tasks.update_last_updated_ids(
            cl_file_path=CL_CHANNELS_LOCAL_PATH,
            tg_file_path=TG_CHANNELS_LOCAL_PATH,
            output_path=MG_CHANNELS_LOCAL_PATH
        )
        # load to gcs info about msgs to parse
        tasks.update_metadata_in_cloud(MG_CHANNELS_LOCAL_PATH)
        tasks.delete_tmp_file(CL_CHANNELS_LOCAL_PATH)
        tasks.delete_tmp_file(TG_CHANNELS_LOCAL_PATH)
        tasks.delete_tmp_file(MG_CHANNELS_LOCAL_PATH)

        tasks.check_channel_stats()
        # gsc_files = tasks.list_msgs()
        # prefect_logger.info(f"{len(gsc_files)} GCS files total")
        prefect_logger.info("Stats checked successfully.")
        prefect_logger.info("Telegram Metadata Flow completed successfully.")
    except Exception as e:
        prefect_logger.error(f"Error in telegram_metadata_flow: {e}")
        raise


if __name__ == "__main__":
    find_msg_4parsing()
    STATS_TEMPLATE = {
            "channels_total": 0,
            "channels_done": 0,
            "total_downloaded": 0,
            "download_scope": 0,
            "total_missed": 0,
            "channels_to_update": 0,
            "bad_channels": 0,
            "bad_channels_ids": [],
            "to_upd_channels_ids": [],
        }