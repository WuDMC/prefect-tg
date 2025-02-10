import os
import subprocess
import argparse
from config import Config


def run_command(command, cwd=None):
    """Executes a shell command and handles errors."""
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        exit(1)
    print(result.stdout)


def main():
    parser = argparse.ArgumentParser(description="Deploy infrastructure with Terraform")
    parser.add_argument("--debug", action="store_true", help="Use development environment")
    args = parser.parse_args()

    # Load configuration
    config = Config(debug=args.debug)
    terraform_vars = config.config.get("terraform", {})
    google_cloud = config.config.get("google_cloud", {})

    # Determine environment
    project_id = terraform_vars.get("project_id")
    if args.debug:
        project_id += "-dev"

    bucket = google_cloud.get("backup_bucket")
    region = terraform_vars.get("gcp_region", "europe-west1")

    # Path to Terraform directory
    terraform_dir = os.path.join(os.path.dirname(__file__), "terraform")

    # Create backend configuration
    backend_config = f"""
terraform {{
  backend "gcs" {{
    bucket = "{bucket}"
    prefix = "terraform/state"
  }}
}}
"""
    backend_file = os.path.join(terraform_dir, "backend.tf")
    with open(backend_file, "w") as f:
        f.write(backend_config)

    # Initialize Terraform
    print("[1/3] Initializing Terraform...")
    run_command("terraform init", cwd=terraform_dir)

    # Apply Terraform with variables
    print("[2/3] Applying Terraform...")
    var_args = " ".join([
        f"-var '{key}={value}'" for key, value in terraform_vars.items()
    ])
    run_command(f"terraform apply -auto-approve {var_args}", cwd=terraform_dir)

    print("[3/3] Deployment completed successfully!")


if __name__ == "__main__":
    main()
