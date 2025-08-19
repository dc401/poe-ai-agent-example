# 🔐 Sechard Agent — Secure OS Enumeration and Hardening Assistant

  
This project is a security-focused, Vertex AI–powered CLI agent that automates operating system enumeration and security hardening analysis. It leverages **Gemini 2.5 Pro**, executes CLI commands safely, and enforces **inline AI safety** using **Model Armor** with high-confidence blocking. 

Ported from the original code: https://github.com/dc401/poe-ai-agent-example

---
## 📦 Requirements

- Python 3.10+ (Cloud Shell default works)
- gcloud CLI installed and authenticated
- IAM permissions to use:
- Vertex AI
- Security Command Center (Model Armor API)
---
## ⚙️ Setup (Google Cloud Shell)

Run these steps **inside Cloud Shell**:

### 1. Create a virtual environment

```bash

python3  -m  venv  sechard-agent

source  sechard-agent/bin/activate

````
  
### 2. Install Python dependencies
```bash

pip3  install  -r  requirements.txt

```

---
  

## 🛡️ First-Time Model Armor Setup (Automated)

 At the time of this port, the Python SDK did not expose all the correct fields needed for model armor guard rail template creation and tuning. We call the gcloud CLI as a sub process just to get it going. You will need the correct GCP API and IAM permissions for this to work.
 
The agent will automatically:
* Check for an existing **Model Armor template**
* Create one if missing using `gcloud`

* Enforce:
* Prompt Injection Detection
* Responsible AI Filters
* Sensitive Data Detection
* Block on high-confidence matches

This is handled via subprocess — **no manual template setup is needed.**

---
## 🧠 Prompt Template

Make sure the file `prompt.md` exists in the project root with this content:
```

You are a security analyst assistant focused on enumeration, hardening, and validating operating system security settings.

You may use **one tool per step** to accomplish the user’s goal.

Available tools:
- **cli** — run a shell command (e.g., `whoami`, `uname -a`, `powershell Get-BitLockerVolume`)
- **search** — retrieve information from external sources if you’re unsure or need more data

At each step, respond with only a Python-style dictionary, either inline or in a code block:

Examples:
{"cli": "whoami", "thought": "check current user context"}
{"tool": "search", "thought": "need to look up current macOS hardening baselines"}

Do not explain your answer outside the dictionary. Only return the next tool to run or final recommendation.
```
---
## 🚀 Run the Agent

```bash
echo  "what OS are we on and what security controls are currently active?" | python3  sechard-agent.py
```
You’ll see:
* Gemini’s CLI recommendations
* Executed output
* Inline LLM output chain
* Final thoughts
Logs are saved in `logfile`.

---
## 📁 File Structure
```
sechard-agent/
├── sechard-agent-1.2.py # Main entry point
├── prompt.md # System prompt config
├── logfile # Logs (generated on run)
├── requirements.txt # Pip dependencies
```
---

## 🧰 Helpful Commands

To test Model Armor template manually:

```bash
gcloud  model-armor  templates  list  --location=us-central1
```
To delete and re-create:

```bash
gcloud  model-armor  templates  delete  sechard-inline-guard  --location=us-central1
```
---

## ✅ Features

* ✅ Vertex AI Gemini 2.5 Pro integration

* ✅ Safe shell execution (with blocked commands)

* ✅ Search fallback via LLM

* ✅ Inline prompt and response sanitization using Model Armor

* ✅ Automatic enforcement template creation using `gcloud`

---

## 🛑 Default Blocked Commands

```python
['sudo', 'runas', 'del', 'rm', 'chmod', 'icacls']
```

You can customize this in the script under `prohibited_commands`.

---

## 🧩 Optional Enhancements

* Add grounding via Vertex AI Search
* Stream output from Gemini
* Function calling via JSON-schema tools
* CI/CD deployment on Cloud Run or Cloud Functions
---

### 🔢 Sechard Agent Versions Explained
| Version | Key Features | Recommended Use |
|---------|--------------|------------------|
| **1.0** | - Initial Vertex AI port from Poe agent <br> - CLI execution and `serpapi`-based search tool <br> - No Model Armor <br> - Static project ID | For testing legacy Poe logic or if you need SerpAPI |
| **1.1** | - Fully dynamic prompt and response using Gemini <br> - Search tool fallback without SerpAPI <br> - GCP project auto-detected via Cloud Shell <br> - Simple CLI tool use <br> - Guardrails for dangerous commands <br> - Cleaner prompt iteration | Best for lightweight Gemini agent testing **without** safety inspection |
| **1.2** | - All features of 1.1 <br> - **Model Armor** sanitization (prompt and response) <br> - One-time template setup via `gcloud` subprocess <br> - Enforces blocking on: Prompt Injection, Sensitive Data, and Responsible AI <br> - HIGH confidence enforcement <br> - Warning suppression for Vertex SDK <br> - Hardened CLI tool execution with LLM assist | 🔐 Recommended for **production use**, security reviews, and sensitive environments |


---

### 🧪 How to Try Them
In your `sechard-agent/` folder:
```bash
python3  sechard-agent-1.0.py  # Original, uses SerpAPI
python3  sechard-agent-1.1.py  # Simplified Gemini logic, no Model Armor
python3  sechard-agent.py  # (1.2) Final secure version with Model Armor
```

> ✅ `sechard-agent.py` is the current and most hardened version.


---

## 📄 License

MIT License © 2025 Dennis Chow
