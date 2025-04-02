from prefect import flow
from prefect.docker import DockerImage
import os


@flow
def find_msg_4parsing():
    from prefect.logging import get_run_logger
    import tasks
    from tg_jobs_parser.configs import volume_folder_path

    CL_CHANNELS_LOCAL_PATH = os.path.join(volume_folder_path, "f1.1_gsc_channels_metadata.json")
    TG_CHANNELS_LOCAL_PATH = os.path.join(volume_folder_path, "f1.1_tg_channels_metadata.json")
    MG_CHANNELS_LOCAL_PATH = os.path.join(volume_folder_path, "f1.1_merged_channels_metadata.json")
    # 1
    prefect_logger = get_run_logger()
    try:
        prefect_logger.info("Starting Telegram Metadata Flow")
        # get ids of messages to parse
        tasks.get_metadata_from_cloud(CL_CHANNELS_LOCAL_PATH)
        tasks.check_channel_stats()

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
    from dotenv import load_dotenv
    from config import Config
    # ✅ Load environment variables
    load_dotenv()

    # ✅ Read config file path from .env
    project_env_file = os.getenv('PROJECT_VARS')
    local_home_folder = os.getenv("VISIONZ_HOME")
    docker_app_folder = '/app'
    gcp_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if not project_env_file:
        print("❌ PROJECT_VARS is not set in .env file!")
        exit(1)

    # ✅ Load configuration from the specified file
    try:
        config = Config(debug=False, env_file=project_env_file)

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        exit(1)



    project = config.get("prefect", "project_name")
    work_pool = config.get("prefect", "work_pool_name")
    # find_msg_4parsing()
    find_msg_4parsing.deploy(
        name=f"{project}-find_msg_4parsing",
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
        },
        cron="0 0,6,12,18 * * *",
    )
