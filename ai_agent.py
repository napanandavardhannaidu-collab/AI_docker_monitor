
import ollama
import json

from docker_tools import list_containers


def analyze_docker():
    containers = list_containers()

    if not containers:
        print("No Docker containers found.")
        return

    # Display the actual Docker status before AI analysis
    print("\n=== Actual Docker Status ===")

    for container in containers:
        print(
            f"Name: {container['name']} | "
            f"Status: {container['status']}"
        )

    prompt = f"""
You are a careful AI DevOps assistant.

Analyze this Docker data collected directly by Python:
{json.dumps(containers, indent=2)}

Rules:
1. Trust the status field as the source of truth.
2. Never infer status from the image, ID, or other fields.
3. Report each container's name and exact status.
4. Explain what exited means.
5. Suggest safe diagnostic commands.
6. Do not invent logs, errors, or root causes.
7. Do not execute commands or restart containers.
8. If information is insufficient, say so clearly.
"""

    response = ollama.chat(
        model="qwen2.5:3b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    print("\n=== AI Docker Analysis ===\n")
    print(response["message"]["content"])


if __name__ == "__main__":
    analyze_docker()
