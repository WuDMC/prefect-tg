import os
import subprocess
import argparse
from config import Config
from dotenv import load_dotenv

def run_command(command, cwd=None):
    """Executes a shell command and handles errors."""
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error executing: {command}\n{result.stderr}")
        exit(1)
    print(result.stdout.strip())


def main():
    parser = argparse.ArgumentParser(description="Deploy infrastructure with Terraform")
    parser.add_argument("--debug", action="store_true", help="Use development environment")
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    env_file = os.getenv('PROJECT_VARS')
    if not env_file:
        print("❌ PROJECT_VARS is not set in .env file!")
        exit(1)

    # Load configuration
    try:
        config = Config(debug=args.debug, env_file=env_file)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        exit(1)

    terraform_vars = config.config.get("terraform", {})
    google_cloud = config.config.get("google_cloud", {})





    # Path to Terraform directory
    terraform_dir = os.path.join(os.path.dirname(__file__), "terraform")
    backend_file = os.path.join(terraform_dir, "backend.tf")

    # Ensure Terraform directory exists
    if not os.path.exists(terraform_dir):
        print(f"❌ Terraform directory not found: {terraform_dir}")
        exit(1)

    # Create backend configuration
    backend_config = f"""
    terraform {{
      backend "local" {{
        path = "{os.path.join(terraform_dir, 'terraform.tfstate')}"
      }}
    }}
    """

    try:
        with open(backend_file, "w") as f:
            f.write(backend_config)
        print(f"✅ Created backend configuration: {backend_file}")
    except Exception as e:
        print(f"❌ Error writing backend file: {e}")
        exit(1)

    # Ensure Terraform directory exists
    if not os.path.exists(terraform_dir):
        print(f"❌ Terraform directory not found: {terraform_dir}")
        exit(1)

    # Initialize Terraform
    print("\n⚙️ [1/5] Initializing Terraform...")
    run_command("terraform init -input=false", cwd=terraform_dir)

    # Validate Terraform configuration
    print("\n🔍 [2/5] Validating Terraform configuration...")
    run_command("terraform validate", cwd=terraform_dir)

    service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    # Plan Terraform changes
    print("\n📄 [3/5] Planning Terraform deployment...")
    var_args = " ".join([f"-var '{key}={value}'" for key, value in terraform_vars.items()])
    var_args += f" -var 'credentials={service_account_path}'"

    # Сохраняем план в файл tfplan
    run_command(f"terraform plan -input=false -out=tfplan {var_args}", cwd=terraform_dir)

    # Apply Terraform changes из сохраненного плана
    print("\n🚀 [4/5] Applying Terraform changes...")
    print("terraform apply -auto-approve tfplan")
    run_command("terraform apply -auto-approve tfplan", cwd=terraform_dir)

    print("\n✅ [5/5] Deployment completed successfully!")

if __name__ == "__main__":
    main()
