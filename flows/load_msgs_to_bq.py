from prefect import flow
import tasks
from prefect.logging import get_run_logger
import os
from tg_jobs_parser.configs import volume_folder_path

TMP_FILE = os.path.join(volume_folder_path, "tmp_not_uploaded_msg_files.json")

@flow
def load2bq():
    # check BQ status table and find not processed files from GSC, if any upload it yo BQ
    prefect_logger = get_run_logger()
    gsc_files = tasks.list_msgs()
    prefect_logger.info(f"{len(gsc_files)} GCS files total")
    last_status_files = tasks.check_files_statuses()
    prefect_logger.info(f"{len(last_status_files)} last_status_files files total")
    # upload files to bq and save new status to tmp file
    not_processed = sum(1 for item in last_status_files if item.get("status") != "done")
    prefect_logger.info(f"{not_processed} files ready to upload to BQ")
    temp_file = tasks.process_all_files(gsc_files=gsc_files, last_status_files=last_status_files, output_file=TMP_FILE)
    # temp file store metadata what files have been uploaded to update status table BQ
    if temp_file:
        tasks.update_status_table(temp_file)
        tasks.delete_tmp_file(temp_file)
        # stats logging
        uploaded_stats = tasks.check_uploaded_files_statuses()
        prefect_logger.info(uploaded_stats)
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
        prefect_logger.info("Stats checked successfully.")
        raw_stats = tasks.check_raw_messages_statuses()
        prefect_logger.info(raw_stats)
    else:
        prefect_logger.info('all files already in BQ msg table')


if __name__ == "__main__":
    load2bq()