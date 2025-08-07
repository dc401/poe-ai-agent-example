#!/usr/bin/env python3

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="vertexai")

import vertexai
from vertexai.generative_models import GenerativeModel
import os, subprocess, time, logging, sys, random, ast
from google.cloud import modelarmor_v1

# Detect GCP project ID
GCP_PROJECT_ID = os.environ.get("CLOUD_PROJECT") or os.environ["GCP_PROJECT_ID"]
TEMPLATE_ID = "sechard-inline-guard"
TEMPLATE_PATH = f"projects/{GCP_PROJECT_ID}/locations/us-central1/templates/{TEMPLATE_ID}"

# Use subprocess to setup the Model Armor template (1-time)
def setup_model_armor_template():
    location = "us-central1"
    try:
        list_cmd = [
            "gcloud", "model-armor", "templates", "list",
            f"--location={location}",
            f"--filter=name~{TEMPLATE_ID}",
            "--format=value(name)"
        ]
        existing = subprocess.check_output(list_cmd).decode().strip()

        if TEMPLATE_ID in existing:
            print(f"Model Armor template '{TEMPLATE_ID}' already exists.")
        else:
            print(f"Creating Model Armor template '{TEMPLATE_ID}'...")
            create_cmd = [
                "gcloud", "model-armor", "templates", "create", TEMPLATE_ID,
                f"--location={location}",
                "--display-name=Sechard Guard Template",
                "--text-inspection-config=confidenceLevel=HIGH,"
                "enforcementMode=INSPECT_AND_BLOCK,"
                "detectPromptInjection=true,"
                "detectResponsibleAi=true,"
                "detectSensitiveData=true"
            ]
            subprocess.run(create_cmd, check=True)
            print("Model Armor template created successfully.")
    except subprocess.CalledProcessError as e:
        print("Failed to verify or create Model Armor template.")
        print(e.output.decode())
        sys.exit(1)

# Init Vertex + Gemini
vertexai.init(project=GCP_PROJECT_ID, location="us-central1")
chat_model = GenerativeModel(model_name="gemini-2.5-pro")
chat = chat_model.start_chat()

# Init Model Armor client
model_armor_client = modelarmor_v1.ModelArmorClient()

def sanitize(text, is_user=True):
    if is_user:
        req = modelarmor_v1.SanitizeUserPromptRequest(name=TEMPLATE_PATH, user_prompt_data={"text": text})
        resp = model_armor_client.sanitize_user_prompt(req)
    else:
        req = modelarmor_v1.SanitizeModelResponseRequest(name=TEMPLATE_PATH, model_response_data={"text": text})
        resp = model_armor_client.sanitize_model_response(req)
    result = resp.sanitization_result
    if result.filter_match_state != modelarmor_v1.FilterMatchState.FILTER_MATCH_STATE_UNSPECIFIED:
        raise Exception(f"Blocked by Model Armor: {result.filter_match_state}")
    return result.sanitized_text

# CLI tool
prohibited_commands = ['sudo', 'runas', 'del', 'rm', 'chmod', 'icacls']
def cli(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = result.stdout.decode()
    print(output)
    return output

# Tool parsing
def extract_tool_dict(text):
    if text.startswith("```"):
        text = text.strip("`\n ")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        return ast.literal_eval(text)
    except Exception as e:
        print(f"Parse error: {e}")
        return None

# Prompt load
with open("prompt.md", "r") as f:
    base_prompt = f.read()

def build_prompt(user_input, history, counter):
    return (
        base_prompt +
        "\n\n## User Input\n" + user_input +
        "\n\n## Tool Result Output History\n" + history +
        f"\n\n## Iteration Counter\n{counter}"
    )

if __name__ == "__main__":
    setup_model_armor_template()

    if os.path.exists("logfile"):
        os.remove("logfile")
    logging.basicConfig(level=logging.DEBUG, filename="logfile", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

    print("Enter your security automation objective:")
    user_input = sys.stdin.readline().strip()
    tool_output_history = ""
    counter = 1

    history_prompt = sanitize(build_prompt(user_input, tool_output_history, counter), is_user=True)
    response = chat.send_message(history_prompt)
    llm_response = sanitize(response.text, is_user=False)

    print("LLM **INITIAL** response output:\n" + llm_response)
    logging.info(llm_response)

    while counter < 5:
        tool_block = extract_tool_dict(llm_response)
        if not tool_block:
            print("Unrecognized tool format. Exiting.")
            break

        # Accept flexible formats
        command = None
        if 'cli' in tool_block:
            command = tool_block['cli']
        elif tool_block.get("tool") == "cli" and tool_block.get("command"):
            command = tool_block['command']

        if command:
            if any(cmd in command for cmd in prohibited_commands):
                raise Exception("**SAFETY GUARDRAIL TRIGGERED**")
            result = cli(command)
            tool_output_history += f"\n\nCLI OUTPUT:\n{result}"

        elif tool_block.get("tool") == "search":
            response = chat.send_message(sanitize(build_prompt(user_input, tool_output_history, counter), is_user=True))
            llm_response = sanitize(response.text, is_user=False)
            tool_output_history += f"\n\nSEARCH OUTPUT:\n{llm_response}"

        else:
            print("Unknown tool. Exiting.")
            break

        counter += 1
        history_prompt = sanitize(build_prompt(user_input, tool_output_history, counter), is_user=True)
        response = chat.send_message(history_prompt)
        llm_response = sanitize(response.text, is_user=False)
        print(f"LLM **NEXT** response output (iteration {counter}):\n" + llm_response)
        logging.info(llm_response)

    final_prompt = build_prompt(user_input, tool_output_history, counter) + "\n\n## FINAL user input\nWe have exhausted all attempts. What recommended next steps should we action?"
    final_response = chat.send_message(sanitize(final_prompt, is_user=True))
    final_output = sanitize(final_response.text, is_user=False)
    print("LLM **FINAL** response output:\n" + final_output)
    logging.info(final_output)
    logging.info(final_prompt)
