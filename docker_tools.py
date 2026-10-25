
import docker


def get_docker_client():
    """Connect to the local Docker Engine."""
    return docker.from_env()


def list_containers():
    """List all Docker containers, including stopped containers."""
    client = get_docker_client()
    containers = client.containers.list(all=True)

    results = []

    for container in containers:
        results.append({
            "id": container.short_id,
            "name": container.name,
            "image": container.image.tags,
            "status": container.status,
        })

    return results


def get_container_logs(container_name, tail=100):
    """Read recent logs from a Docker container."""
    if not isinstance(container_name, str) or not container_name.strip():
        raise ValueError("Container name cannot be empty.")

    if isinstance(tail, bool) or not isinstance(tail, int):
        raise ValueError("tail must be an integer.")

    if not 1 <= tail <= 200:
        raise ValueError("tail must be between 1 and 200.")

    client = get_docker_client()

    try:
        container = client.containers.get(container_name)

        logs = container.logs(
            stdout=True,
            stderr=True,
            tail=tail,
            timestamps=True,
        )

        return logs.decode("utf-8", errors="replace")

    except docker.errors.NotFound:
        raise ValueError(
            f"Container '{container_name}' was not found."
        )


def inspect_container(container_name):
    """Inspect status, exit code, timestamps, and health information."""
    if not isinstance(container_name, str) or not container_name.strip():
        raise ValueError("Container name cannot be empty.")

    client = get_docker_client()

    try:
        container = client.containers.get(container_name)
        container.reload()

        state = container.attrs.get("State", {})
        health = state.get("Health")

        return {
            "name": container.name,
            "id": container.short_id,
            "status": state.get("Status", "unknown"),
            "exit_code": state.get("ExitCode"),
            "error": state.get("Error") or None,
            "started_at": state.get("StartedAt"),
            "finished_at": state.get("FinishedAt"),
            "health_status": (
                health.get("Status")
                if health
                else "not_configured"
            ),
        }

    except docker.errors.NotFound:
        raise ValueError(
            f"Container '{container_name}' was not found."
        )


if __name__ == "__main__":
    print("=== Docker Containers ===")

    try:
        containers = list_containers()

        if not containers:
            print("No Docker containers found.")
        else:
            for container in containers:
                print(
                    f"Name: {container['name']} | "
                    f"Status: {container['status']} | "
                    f"Image: {container['image']}"
                )

    except docker.errors.DockerException as exc:
        print(f"Could not connect to Docker: {exc}")
        raise SystemExit(1)

    print("\n=== Container Inspection: ai-gym-coach ===")

    try:
        details = inspect_container("ai-gym-coach")

        for key, value in details.items():
            print(f"{key}: {value}")

    except (ValueError, docker.errors.DockerException) as exc:
        print(f"Could not inspect container: {exc}")

    print("\n=== Recent Logs: ai-gym-coach ===")

    try:
        logs = get_container_logs("ai-gym-coach", tail=20)

        if logs.strip():
            print(logs)
        else:
            print("No logs were returned for this container.")

    except (ValueError, docker.errors.DockerException) as exc:
        print(f"Could not retrieve container logs: {exc}")
