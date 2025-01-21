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
        tasks.parse_tg_dialogs(TG_CHANNELS_LOCAL_PATH)
        tasks.update_target_ids(cloud_channels_file=CL_CHANNELS_LOCAL_PATH,
                                tg_channels_file=TG_CHANNELS_LOCAL_PATH,)
        tasks.update_last_updated_ids(
            file1_path=CL_CHANNELS_LOCAL_PATH,
            file2_path=TG_CHANNELS_LOCAL_PATH,
            output_path=MG_CHANNELS_LOCAL_PATH
        )
        # load to gcs info about msgs to parse
        tasks.update_metadata_in_cloud(MG_CHANNELS_LOCAL_PATH)
        tasks.delete_tmp_file(CL_CHANNELS_LOCAL_PATH)
        tasks.delete_tmp_file(TG_CHANNELS_LOCAL_PATH)
        tasks.delete_tmp_file(MG_CHANNELS_LOCAL_PATH)

        statistics = tasks.check_channel_stats()
        prefect_logger.info(f'msg downloaded: {statistics["total_downloaded"]}')
        prefect_logger.info(f'need to download total: {statistics["total_difference"]}')
        prefect_logger.info(f'channels_total: {statistics["channels_total"]}')
        prefect_logger.info(f'channels_done: {statistics["channels_done"]}')
        prefect_logger.info(f'channels_to_update: {statistics["channels_to_update"]}')
        prefect_logger.info(
            f'channels_to_update_ids: {statistics["to_upd_channels_ids"]}'
        )
        prefect_logger.info(f'bad_channels: {statistics["bad_channels"]}')
        prefect_logger.info(f'bad_channels_ids: {statistics["bad_channels_ids"]}')
        gsc_files = tasks.list_msgs()
        prefect_logger.info(f"{len(gsc_files)} GCS files total")
        prefect_logger.info("Stats checked successfully.")
        prefect_logger.info("Telegram Metadata Flow completed successfully.")
    except Exception as e:
        prefect_logger.error(f"Error in telegram_metadata_flow: {e}")
        raise


if __name__ == "__main__":
    find_msg_4parsing()