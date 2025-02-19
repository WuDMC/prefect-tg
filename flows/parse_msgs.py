from prefect import flow
from prefect.docker import DockerImage
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
        tasks.check_channel_stats()
        gsc_files = tasks.list_msgs()
        old_count = len(gsc_files)
        prefect_logger.info(f"{old_count} GCS files total")
        prefect_logger.info("Stats checked successfully.")
        # parse msgs  and save to files
        tasks.parse_messages(CL_CHANNELS_LOCAL_PATH)
        # load to gcs parsed msgs
        prefect_logger.info(
            f'msg files ready to upload {len([file for file in os.listdir(volume_folder_path) if file.startswith("msgs")])}')
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
        tasks.check_channel_stats()
        prefect_logger.info("Message processing flow completed successfully")
    except Exception as e:
        prefect_logger.error(f"Error in message processing flow: {e}")
        raise


if __name__ == "__main__":
    from dotenv import load_dotenv
    from config import Config

    # ✅ Load environment variables
    load_dotenv()

    project_env_file = os.getenv('PROJECT_VARS')
    local_home_folder = os.getenv("VISIONZ_HOME")
    docker_app_folder = '/app'
    gcp_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    # ✅ Read config file path from .env
    env_file = os.getenv('PROJECT_VARS')
    if not env_file:
        print("❌ PROJECT_VARS is not set in .env file!")
        exit(1)

    # ✅ Load configuration from the specified file
    try:
        config = Config(debug=True, env_file=env_file)

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        exit(1)

    project = config.get("prefect", "project_name")
    work_pool = config.get("prefect", "work_pool_name")
    # parse_msg_n_load2gsc()
    parse_msg_n_load2gsc.deploy(
        name=f"{project}-parse_msg_n_load2gsc",
        work_pool_name=work_pool,
        image=DockerImage(
            name=f"{project}-image:latest",
            platform="linux/amd64",
            dockerfile="_Dockerfile",
        ),
        job_variables={
            "env": {
                "VISIONZ_HOME": docker_app_folder,
                "GOOGLE_APPLICATION_CREDENTIALS": gcp_creds.replace(local_home_folder, docker_app_folder),
                "PROJECT_VARS": project_env_file.replace(local_home_folder, docker_app_folder),
                "GCP_REGION": os.getenv("GCP_REGION")
            },
            "keep_job": True,
            "timeout": 3600
        }
    )
