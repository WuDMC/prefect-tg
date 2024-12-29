from prefect import flow, task
from prefect.deployments import run_deployment
from prefect.logging import get_run_logger
import tasks
import os
from tg_jobs_parser.configs import vars, volume_folder_path

TMP_FILE = os.path.join(volume_folder_path, "tmp_not_processed_msg_files.json")

@task
def trigger_flow_load2bq():
    prefect_logger = get_run_logger()
    prefect_logger.info("Triggering f4_upload_msgs deployment n load2bq flow.")
    run_deployment(name="load2bq/f4_upload_msgs")

@flow
def find_msgs2load_n_load2bq():
    prefect_logger = get_run_logger()
    prefect_logger.info("Starting f1_msgs_to_process flow.")
    gsc_files = tasks.list_msgs()
    prefect_logger.info(f"{len(gsc_files)} GCS files to process.")

    bigquery_files = tasks.check_msg_files_in_process()
    prefect_logger.info(f"{len(bigquery_files)} Bigquery files to process.")
    # get all files from gcs and all files from BQ table and find not uploaded files
    # todo - revise it, not optimal
    tmp_file = tasks.download_and_process_files(gsc_files=gsc_files, bigquery_files=bigquery_files, output_file=TMP_FILE)
    prefect_logger.info(f"Temporary file with msg_files statuses created: {tmp_file}")
    if tmp_file:
        prefect_logger.info(f"Updated status table with msgs ready to load to BQ")
        # here we add to status table msgs to load to bq
        tasks.update_status_table(tmp_file)
        tasks.delete_tmp_file(tmp_file)
        prefect_logger.info(f"Trigger flow to load msgs to BQ")
        # that  flow get msgs to load from status table and load them
        trigger_flow_load2bq()
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

    prefect_logger.info("find_msgs2load_n_load2bq flow completed successfully.")


if __name__ == "__main__":
    find_msgs2load_n_load2bq()