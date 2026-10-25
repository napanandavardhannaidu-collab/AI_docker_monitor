
import asyncio
import json

import ollama
from mcp import Client, StdioServerParameters

MODEL = "qwen2.5:3b"
MAX_TOOL_ROUNDS = 5

SYSTEM_PROMPT = """
You are a careful AI DevOps assistant.

Use MCP tools to retrieve actual Docker information.

Diagnostic rules:
1. Report container names and statuses exactly as returned by Docker.
2. An exited container is not running. Its exit reason is unknown
   unless reliable evidence establishes the cause.
3. Distinguish observed errors from possible explanations.
4. Never claim a log error caused a container exit unless
   the available evidence supports that conclusion.
5. Never claim a container completed successfully without evidence.
6. If you only have logs, do not invent current container status,
   exit codes, health status, or root causes.
7. If the user asks for logs, summarize relevant errors and timestamps.
8. If evidence is insufficient, explicitly say so.
9. Only perform read-only diagnostics.
10. If a tool fails, explain the failure without inventing results.
11. Use MCP tools when actual Docker information is required.
12. Do not expose secrets or credentials found in logs.
"""


def parse_container_objects(output):
    """Extract container objects from JSON text returned by MCP."""
    decoder = json.JSONDecoder()
    containers = []
    index = 0

    while index < len(output):
        while index < len(output) and output[index].isspace():
            index += 1

        if index >= len(output):
            break

        try:
            data, end_index = decoder.raw_decode(output, index)
            index = end_index
        except json.JSONDecodeError:
            next_object = output.find("{", index + 1)
            if next_object == -1:
                break
            index = next_object
            continue

        if isinstance(data, dict):
            if "name" in data and "status" in data:
                containers.append(data)

            nested = data.get("containers")
            if isinstance(nested, list):
                containers.extend(
                    item
                    for item in nested
                    if isinstance(item, dict)
                    and "name" in item
                    and "status" in item
                )

        elif isinstance(data, list):
            containers.extend(
                item
                for item in data
                if isinstance(item, dict)
                and "name" in item
                and "status" in item
            )

    return containers


def redact_sensitive_lines(text):
    """Hide common secret-bearing log lines before displaying them."""
    sensitive_markers = (
        "password=",
        "passwd=",
        "secret=",
        "api_key=",
        "apikey=",
        "access_token=",
        "authorization:",
        "bearer ",
    )

    safe_lines = []

    for line in text.splitlines():
        lowered = line.lower()

        if any(marker in lowered for marker in sensitive_markers):
            safe_lines.append("[REDACTED: possible sensitive log content]")
        else:
            safe_lines.append(line)

    return "\n".join(safe_lines)


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
    )

    try:
        async with Client(server_params) as client:
            tools_result = await client.list_tools()

            available_tools = {
                tool.name: tool
                for tool in tools_result.tools
            }

            print("\n=== Available MCP Tools ===")
            for tool_name in available_tools:
                print(f"- {tool_name}")

            ollama_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
                for tool in tools_result.tools
            ]

            question = input(
                "\nAsk your Docker monitoring agent: "
            ).strip()

            if not question:
                print("Please enter a question.")
                return

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ]

            all_tool_outputs = []
            final_answer = None

            for round_number in range(MAX_TOOL_ROUNDS):
                try:
                    response = ollama.chat(
                        model=MODEL,
                        messages=messages,
                        tools=ollama_tools,
                    )
                except Exception as exc:
                    print(
                        "\nOllama request failed:",
                        f"{type(exc).__name__}: {exc}",
                    )
                    return

                assistant_message = response["message"]
                messages.append(assistant_message)

                tool_calls = assistant_message.get("tool_calls") or []

                if not tool_calls:
                    final_answer = assistant_message.get(
                        "content",
                        "No response received from the model.",
                    )
                    break

                for tool_call in tool_calls:
                    function = tool_call["function"]
                    tool_name = function["name"]
                    arguments = function.get("arguments") or {}

                    print(f"\nCalling MCP tool: {tool_name}")

                    if tool_name not in available_tools:
                        tool_text = (
                            f"Error: '{tool_name}' is not an available "
                            "MCP tool."
                        )
                        is_error = True
                    else:
                        try:
                            result = await client.call_tool(
                                tool_name,
                                arguments,
                            )

                            text_parts = [
                                item.text
                                for item in result.content
                                if hasattr(item, "text")
                            ]

                            tool_text = "\n".join(text_parts)
                            is_error = bool(result.is_error)

                            if is_error:
                                tool_text = (
                                    "MCP tool reported an error:\n"
                                    + tool_text
                                )

                            if not tool_text:
                                tool_text = (
                                    "The MCP tool returned no text content."
                                )

                        except Exception as exc:
                            tool_text = (
                                f"Tool execution failed: "
                                f"{type(exc).__name__}: {exc}"
                            )
                            is_error = True

                    # Redact common sensitive log lines before printing
                    # or sending tool output back to the model.
                    tool_text = redact_sensitive_lines(tool_text)

                    all_tool_outputs.append(
                        {
                            "tool": tool_name,
                            "output": tool_text,
                            "is_error": is_error,
                        }
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "name": tool_name,
                            "content": tool_text,
                        }
                    )

            else:
                print(
                    "\nMaximum tool-call rounds reached. "
                    "Stopping to prevent an endless loop."
                )

            print("\n=== AI DevOps Agent ===\n")

            if final_answer is not None:
                print(final_answer)
            else:
                print(
                    "The agent did not produce a final answer "
                    "within the tool-call limit."
                )

            print("\n=== MCP Tool Results ===")

            if not all_tool_outputs:
                print("No MCP tools were called.")

            for entry in all_tool_outputs:
                print(f"\nTool: {entry['tool']}")
                print(f"Error: {entry['is_error']}")
                print(entry["output"])

            print("\n=== Verified Docker Status ===")

            found_status = False
            seen_containers = set()

            for entry in all_tool_outputs:
                if entry["is_error"]:
                    continue

                containers = parse_container_objects(entry["output"])

                for container in containers:
                    name = container["name"]
                    status = container["status"]
                    key = (name, status)

                    if key in seen_containers:
                        continue

                    seen_containers.add(key)
                    print(f"{name}: {status}")
                    found_status = True

            if not found_status:
                print(
                    "No structured container status data was returned. "
                    "A log-only tool call does not establish current "
                    "container status."
                )

    except Exception as exc:
        print(
            "\nCould not start or communicate with the MCP server:",
            f"{type(exc).__name__}: {exc}",
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAgent stopped by user.")
