#!/usr/bin/env python3

import vertexai
from vertexai.generative_models import GenerativeModel
import os, subprocess, time, logging, sys, random, ast

# Detect Cloud Shell project automatically
GCP_PROJECT_ID = os.environ.get("CLOUD_PROJECT") or os.environ["GCP_PROJECT_ID"]

vertexai.init(project=GCP_PROJECT_ID, location="us-central1")
chat_model = GenerativeModel(model_name="gemini-2.5-pro")
chat = chat_model.start_chat()

# Load the prompt template
with open("prompt.md", "r") as f:
    base_prompt = f.read()

# Guardrails
prohibited_commands = ['sudo', 'runas', 'del', 'rm', 'chmod', 'icacls']

def cli(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = result.stdout.decode()
    print(output)
    return output

def extract_tool_dict(text):
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.strip().strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        return ast.literal_eval(text)
    except Exception as e:
        print(f"Failed to parse tool block: {e}")
        return None

if __name__ == "__main__":
    if os.path.exists("logfile"):
        os.remove("logfile")

    logging.basicConfig(level=logging.DEBUG, filename="logfile", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

    print("Enter your security automation objective:")
    user_input = sys.stdin.readline().strip()

    tool_output_history = ""
    counter = 1

    def build_prompt():
        return (
            base_prompt +
            "\n\n## User Input\n" + user_input +
            "\n\n## Tool Result Output History\n" + tool_output_history +
            f"\n\n## Iteration Counter\n{counter}"
        )

    # Initial LLM message
    history_prompt = build_prompt()
    response = chat.send_message(history_prompt)
    llm_response = response.text
    print("LLM **INITIAL** response output:\n" + llm_response)
    logging.info(llm_response)

    while counter < 5:
        tool_block = extract_tool_dict(llm_response)

        if not tool_block:
            print("Invalid or unrecognized tool format. Exiting.")
            break

        # Handle CLI tool (either {"cli": "..."} or {"tool": "cli", "command": "..."})
        command = None
        if 'cli' in tool_block:
            command = tool_block['cli']
        elif tool_block.get("tool") == "cli" and tool_block.get("command"):
            command = tool_block["command"]

        if command:
            if any(cmd in command for cmd in prohibited_commands):
                raise Exception("**SAFETY GUARDRAIL TRIGGERED**: Dangerous CLI command blocked.")
            result = cli(command)
            tool_output_history += f"\n\nCLI OUTPUT:\n{result}"

        elif tool_block.get("tool") == "search":
            print("Gemini requested a search. Re-prompting with more context...")
            search_response = chat.send_message(build_prompt())
            tool_output_history += f"\n\nSEARCH OUTPUT:\n{search_response.text}"

        else:
            print("Unrecognized tool. Exiting.")
            break

        counter += 1
        history_prompt = build_prompt()
        response = chat.send_message(history_prompt)
        llm_response = response.text
        print(f"LLM **NEXT** response output (iteration {counter}):\n" + llm_response)
        logging.info(llm_response)

    final_prompt = build_prompt() + "\n\n## FINAL user input\nWe have exhausted all attempts. What recommended next steps should we action?"
    response = chat.send_message(final_prompt)
    print("LLM **FINAL** response output:\n" + response.text)
    logging.info(response.text)
    logging.info(final_prompt)
