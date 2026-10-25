
from mcp.server.mcpserver import MCPServer
from docker_tools import (
    list_containers,
    get_container_logs as read_container_logs,
    inspect_container as inspect_docker_container,
)

mcp = MCPServer("AI Docker Monitor")


@mcp.tool()
def get_docker_containers() -> list[dict]:
    """Get all Docker containers, including stopped containers."""
    return list_containers()


@mcp.tool()
def get_stopped_containers() -> list[dict]:
    """Get Docker containers that are not currently running."""
    return [
        container
        for container in list_containers()
        if container["status"] != "running"
    ]


@mcp.tool()
def get_container_logs(
    container_name: str,
    tail: int = 100,
) -> str:
    """Read recent logs; tail must be between 1 and 200."""
    return read_container_logs(container_name, tail)


@mcp.tool()
def inspect_container(container_name: str) -> dict:
    """Get container status, exit code, timestamps, and health."""
    return inspect_docker_container(container_name)


if __name__ == "__main__":
    mcp.run(transport="stdio")
