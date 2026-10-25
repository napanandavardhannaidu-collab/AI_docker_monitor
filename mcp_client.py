
import asyncio

from mcp import Client, StdioServerParameters


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
    )

    async with Client(server_params) as client:
        tools_result = await client.list_tools()

        print("\n=== Available MCP Tools ===")

        for tool in tools_result.tools:
            print(f"- {tool.name}: {tool.description}")

        result = await client.call_tool(
            "get_docker_containers",
            {}
        )

        print("\n=== Docker Container Results ===")

        for item in result.content:
            if hasattr(item, "text"):
                print(item.text)

        if result.is_error:
            print("The MCP tool reported an error.")


if __name__ == "__main__":
    asyncio.run(main())
