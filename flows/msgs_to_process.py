from prefect import flow
from prefect.logging import get_run_logger
import tasks
import os
from tg_jobs_parser.configs import volume_folder_path

TMP_FILE = os.path.join(volume_folder_path, "tmp_not_processed_msg_files.json")


@flow
def find_msgs2load():
    # find all blobs and check if any not exist in BQ status table
    prefect_logger = get_run_logger()
    prefect_logger.info("Starting f3_msgs_to_process flow.")
    gsc_files = tasks.list_msgs()
    prefect_logger.info(f"{len(gsc_files)} GCS files total")

    bigquery_files = tasks.check_msg_files_in_process()
    prefect_logger.info(f"{len(bigquery_files)} Bigquery files total.")
    prefect_logger.info(f"{len(gsc_files)- len(bigquery_files)}  files will be added in queue")
    # get all files from gcs and all files from BQ table and find not uploaded files
    # todo - revise it, not optimal
    temp_file_path = tasks.download_and_process_files(gsc_files=gsc_files, bigquery_files=bigquery_files, output_file=TMP_FILE)
    prefect_logger.info(f"Temporary file with msg_files statuses created: {temp_file_path}")
    if temp_file_path:
        prefect_logger.info(f"Updating status table with msgs ready to load to BQ")
        # here we add to status table msgs to load to bq
        tasks.update_status_table(temp_file_path)
        tasks.delete_tmp_file(temp_file_path)
        # that  flow get msgs to load from status table and load them
    else:
        prefect_logger.info(f"All files already in BQ status table...heh")

    prefect_logger.info("find_msgs2load_n_load2bq flow completed successfully.")


if __name__ == "__main__":
    find_msgs2load()