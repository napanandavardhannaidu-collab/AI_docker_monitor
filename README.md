# AI Docker Monitoring Agent

An AI-assisted Docker monitoring project built with Python, Docker SDK, and Ollama. It monitors Docker container events, inspects container status, classifies alerts, and uses a local language model to summarize logs for selected container events.

## Features

- **Docker event monitoring:** Watches container lifecycle events such as create, start, stop, die, restart, destroy, health-status changes, and out-of-memory (OOM) events.
- **Container inspection:** Collects available container status, exit-code, runtime, timestamp, and health information.
- **Alert classification:** Classifies events as INFO, WARNING, or CRITICAL based on available Docker facts.
- **AI-assisted log analysis:** Uses Ollama with a local language model to summarize selected container logs.
- **Local inference:** Supports local model execution without requiring a paid hosted LLM API key.
- **Reconnection handling:** Attempts to recover from Docker errors during the monitoring loop.
- **MCP learning components:** Includes separate MCP-related scripts for experimenting with AI agents and Docker tools.

## Technology Stack

- Python
- Docker Engine and Docker SDK for Python
- Ollama
- `qwen2.5:3b` local language model
- Model Context Protocol (MCP)

## Architecture

1. The Python monitor connects to Docker.
2. Docker container events are received by the monitoring loop.
3. Relevant events trigger container inspection.
4. The monitor classifies alerts using observed Docker information.
5. For selected events, recent logs are collected and summarized by Ollama.
6. The monitor prints event details, alert severity, and the AI-generated summary.

```text
Docker Engine
     |
     v
Python Event Monitor
     |
     v
Container Inspection
     |
     v
Alert Classification
     |
     +----> INFO / WARNING / CRITICAL
     |
     v
Selected Container Logs
     |
     v
Local Ollama Model
     |
     v
AI-Assisted Log Summary
```

## Prerequisites

- Ubuntu or Ubuntu on WSL
- Python 3.12 or a compatible Python version
- Docker Engine accessible from your terminal
- Ollama installed and running
- Sufficient RAM for Docker and the selected local model

## Setup

### 1. Clone the repository

Replace `YOUR_GITHUB_USERNAME` with your GitHub username after publishing the repository.

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/ai-docker-monitor.git
cd ai-docker-monitor
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Download the local model

```bash
ollama pull qwen2.5:3b
```

Verify that the model is available:

```bash
ollama list
```

Make sure Ollama is running and Docker is accessible before starting the monitor.

## Run

Start the monitoring script:

```bash
python monitor.py
```

Stop monitoring with `Ctrl+C`.

The Docker user must have permission to access the Docker daemon. Use the appropriate permissions for your system; avoid running untrusted code with elevated privileges.

## Alert Levels

| Level | Meaning |
|---|---|
| INFO | Informational events, successful exits, or healthy status |
| WARNING | Failed exits, unhealthy status, or unknown exit-code information |
| CRITICAL | Docker-reported out-of-memory events |

Alert levels depend on the event and the information available from Docker. They are not a substitute for a full production alerting system.

## Testing and Verification

During development, the following checks were performed:

- Python syntax compilation for `monitor.py`
- Alert classification for successful and failed exits
- Health-status alert classification
- Direct classification of an OOM event as CRITICAL
- Container event monitoring and AI-assisted log summarization

The OOM check tested the classification logic; it did not deliberately trigger a real out-of-memory event. These checks do not imply that every failure mode has been tested.

## Project Structure

```text
ai-docker-monitor/
├── monitor.py
├── ai_agent.py
├── ai_mcp_agent.py
├── docker_tools.py
├── mcp_client.py
├── mcp_server.py
├── requirements.txt
├── README.md
├── .gitignore
└── tests/
```

The monitoring entry point is `monitor.py`. The MCP-related scripts are included as supporting learning and experimentation components.

## Limitations

- This is a learning and portfolio project, not a production monitoring platform.
- AI-generated summaries may be inaccurate; verify important conclusions against Docker's actual output.
- Monitoring and alert output currently depend on the local runtime and terminal.
- Production use would require additional testing, secure log handling, persistent alert delivery, and operational safeguards.

## Future Improvements

- Add automated unit tests
- Add structured logging and persistent alert history
- Add configurable alert thresholds
- Add a dashboard or notification integration
- Improve startup reconnection and failure handling
- Expand MCP integration tests

## Security

- Do not commit API keys, passwords, tokens, private keys, or `.env` files.
- Treat container logs as untrusted input.
- Review AI-generated analysis before taking operational action.
- This project is intended for read-only monitoring of existing containers; do not add destructive actions without explicit safeguards.

## Author

Nanda


Developed as a hands-on project while learning AI-powered DevOps, Docker monitoring, local LLMs, and MCP.
