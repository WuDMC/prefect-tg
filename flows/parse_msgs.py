from prefect import flow
from prefect.logging import get_run_logger
import tasks
import os
from tg_jobs_parser.configs import volume_folder_path

CL_CHANNELS_LOCAL_PATH = os.path.join(volume_folder_path, "f1.2_gsc_channels_metadata.json")
TG_CHANNELS_LOCAL_PATH = os.path.join(volume_folder_path, "f1.2_tg_channels_metadata.json")
MG_CHANNELS_LOCAL_PATH = os.path.join(volume_folder_path, "f1.2_merged_channels_metadata.json")
UP_CHANNELS_LOCAL_PATH = os.path.join(volume_folder_path, "f1.2_uploaded_msgs_metadata.json")


@flow
def parse_msg_n_load2gsc():
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Starting message processing flow")

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
        old_count = len(gsc_files)
        prefect_logger.info(f"{old_count} GCS files total")
        prefect_logger.info("Stats checked successfully.")
        # parse msgs  and save to files
        tasks.parse_messages(CL_CHANNELS_LOCAL_PATH)
        # load to gcs parsed msgs
        prefect_logger.info(f'msg files ready to upload {len([file for file in os.listdir(volume_folder_path) if file.startswith("msgs")])}')
        tasks.upload_msgs_files_to_storage(cl_file_path=CL_CHANNELS_LOCAL_PATH,
                                           up_file_path=UP_CHANNELS_LOCAL_PATH,
                                           output_path=MG_CHANNELS_LOCAL_PATH)
        gsc_files = tasks.list_msgs()
        new_count = len(gsc_files)
        prefect_logger.info(f"{new_count} GCS files total")
        prefect_logger.info(f"Created {new_count - old_count} new GCS files")
        tasks.delete_tmp_file(CL_CHANNELS_LOCAL_PATH)
        tasks.delete_tmp_file(UP_CHANNELS_LOCAL_PATH)
        tasks.delete_tmp_file(MG_CHANNELS_LOCAL_PATH)
        prefect_logger.info("Message processing flow completed successfully")
    except Exception as e:
        prefect_logger.error(f"Error in message processing flow: {e}")
        raise


if __name__ == "__main__":
    parse_msg_n_load2gsc()