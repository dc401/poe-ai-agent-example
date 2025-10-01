# SecHard Agent: AI-Powered OS Security Enumeration with Anomaly Detection

[![License: MIT](https://pfst.cf2.poecdn.net/base/image/2c89badab92b5ee0afea1a6328677fab597eaa5d90b21f6a29384f9eaac3cbc0?pmaid=478858866)](https://opensource.org/licenses/MIT)  
[![Python 3.8+](https://pfst.cf2.poecdn.net/base/image/615ff68347b1a24604be37f6c9bba422591b71f2fb4927934fa1df6431ae9bb3?pmaid=478858871)](https://www.python.org/downloads/)

## Overview

SecHard Agent is a Python-based system designed to automate operating system security enumeration, hardening recommendations, and validation using Google's Gemini AI model (via Vertex AI). It includes tools for running CLI commands, searching external resources, and monitoring agent behavior for security anomalies. The system logs agent activities, detects outliers (e.g., unusual inference times or response entropy), and includes a tester for simulating edge cases like prompt injections or high-entropy responses.

This project is ideal for security analysts testing AI agents in controlled environments, with built-in guardrails to prevent dangerous commands and continuous monitoring to flag potential security drifts (e.g., model overload or evasion attempts).

This is based off the [SecHard-Agent v1.1](https://github.com/dc401/poe-ai-agent-example/blob/main/gcp-sechard-agent/sechard-agent-1.1.py) of Dennis Chow's original code to show continuous monitoring at runtime with instrumentation vs. rely on CSP model guard

Key components:

-   **AI Agent**: Handles security tasks with iterative tool usage.
-   **Monitoring**: Real-time anomaly detection in logs.
-   **Testing**: Automated edge-case simulations.
-   **Visualization**: Insights from anomalies (via an external graph).

## Features

-   **AI-Driven Security Tasks**: Enumerate and harden OS settings using CLI and search tools.
-   **Guardrails**: Blocks prohibited commands (e.g., `rm`, `sudo`).
-   **Behavioral Logging**: Tracks inference time, response length, entropy, and tool execution.
-   **Anomaly Detection**: Uses statistical methods (Z-scores, IQR) to alert on outliers.
-   **Edge-Case Testing**: Simulates probing, injections, and high-complexity scenarios.
-   **Insights Dashboard**: Summarizes key anomalies for quick analysis.

## Installation

1.  **Prerequisites**:
    
    -   Python 3.8+.
    -   Google Cloud Project with Vertex AI enabled (set `GCP_PROJECT_ID` environment variable).
    -   Access to Gemini model via Vertex AI.
2.  **Clone the Repository**:
    
    ```awk
    git clone https://github.com/your-repo/sechard-agent.git
    cd sechard-agent
    
    ```
    
3.  **Install Dependencies**:  
    Use the provided `requirements.txt`:
    
    basic
    
    ```basic
    pip install -r requirements.txt
    
    ```
    
    This includes libraries like `vertexai`, `numpy`, `pydantic`, and others for AI, logging, and stats.
    
4.  **Setup Environment**:
    
    -   Ensure you're authenticated with Google Cloud (e.g., `gcloud auth login`).
    -   Activate a virtual environment if needed: `python -m venv venv && source venv/bin/activate`.

## Usage

### Running the AI Agent

The core script is `sechard-agent-1.1-conmon.py`. It prompts for a security objective and iterates through tools.

```apache
python sechard-agent-1.1-conmon.py

```

-   Input example: "Check if BitLocker is enabled on Windows."
-   Output: Logs to `agent_behavior.log` and console. Final recommendations after up to 5 iterations.

### Monitoring Anomalies

Run the monitor in a separate terminal to tail logs and generate alerts:

```vim
python log_monitor.py

```

-   Monitors `agent_behavior.log` in real-time.
-   Writes alerts to `alerts.log` (e.g., outliers in inference time).

### Testing for Anomalies

Use `anomaly_tester.py` to simulate edge cases:

```apache
python anomaly_tester.py --agent-script sechard-agent-1.1-conmon.py --iterations 5

```

-   Randomly selects from predefined edge cases (e.g., prompt injections).
-   Ensure `log_monitor.py` is running to capture alerts.

### Viewing Insights

Access the external URL `graph.html` for a summary slide of key anomalies (content excerpt):

-   Extreme Inference Times: Likely prompt injections.
-   High Response Lengths: Possible data exfiltration.
-   Entropy Spikes: Noisy responses from probing.
-   Exec Time Outliers: Guardrail triggers.

## Files Overview

-   **sechard-agent-1.1-conmon.py**: Main AI agent script using Gemini for security tasks. Loads `prompt.md`, logs to `agent_behavior.log`, and enforces guardrails.
-   **prompt.md**: System prompt template defining the agent's role, tools (CLI, search), and response format (Python dict).
-   **log_monitor.py**: Continuous monitor for `agent_behavior.log`. Detects outliers using Z-scores/IQR and writes to `alerts.log`.
-   **anomaly_tester.py**: Tester script for running edge-case inputs against the agent to simulate anomalies.
-   **agent_behavior.log**: Sample log of agent events (inference, tool executions) with metrics like inference time and entropy.
-   **alerts.log**: Sample alerts from outlier detection (e.g., high inference times indicating potential drifts).
-   **requirements.txt**: List of Python dependencies for easy installation.
-   **graph.html** (external): Visualization of anomaly insights (use provided content for reference).

## How It Works

1.  **Agent Execution**: User inputs a goal → Agent plans tools iteratively → Logs metrics.
2.  **Monitoring**: `log_monitor.py` polls logs → Computes stats → Alerts on outliers.
3.  **Testing**: `anomaly_tester.py` feeds edge cases → Triggers anomalies → Review `alerts.log`.
4.  **Insights**: Use `graph.html` content to analyze top risks like model overload or probing attacks.

## Contributing

Contributions welcome! Fork the repo, create a feature branch, and submit a pull request. Focus areas:

-   Enhance guardrails or add new tools.
-   Improve anomaly detection algorithms.
-   Add support for more AI models.

## License

This project is licensed under the MIT License. See LICENSE for details.