from prefect import flow
from prefect.docker import DockerImage


@flow(log_prints=True)
def my_flow(name: str = "world"):
    print(f"Hello {name}! I'm a flow running on Cloud Run!")


if __name__ == "__main__":
    my_flow.deploy(
        name="my-cloud-run-test-flow",
        work_pool_name="my-cloud-run-pool",
        image=DockerImage(
            name="us-central1-docker.pkg.dev/migroot/prefect-images/my-cloud-run-test-flow:latest",
            platform="linux/amd64",
        )
    )
