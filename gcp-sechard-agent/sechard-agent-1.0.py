#!/usr/bin/env python3

import vertexai
from vertexai.generative_models import GenerativeModel
import asyncio, os, subprocess, ast, time, logging, sys, random, json
#from serpapi import GoogleSearch 
from serpapi.google_search_results import GoogleSearch #new package complaints


# Author: Dennis Chow
# Version: Gemini 2.5 Vertex AI Port

# Init Vertex AI
vertexai.init(project="p-gs-dteng-cp", location="us-central1") #<--- dont forget to replace ###
chat_model = GenerativeModel(model_name="gemini-2.5-pro") #<-- dont forget to replace ###
chat = chat_model.start_chat()

# Load the full prompt from file
with open("prompt.md", "r") as f:
    prompt_file = f.read()

# Read API secrets from environment
serp_api_key = os.environ["SERP_API"]

# Safety controls
prohibited_commands = ['sudo', 'runas', 'del', 'rm', 'chmod', 'icacls']

# Tool functions
def serpapi(query):
    params = {
        "q": query,
        "location": "Weston, FL, United States",
        "hl": "en",
        "gl": "us",
        "google_domain": "google.com",
        "api_key": serp_api_key
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    print(results)
    return str(results)

def cli(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout.decode())
    return result.stdout.decode()

# Begin execution
if __name__ == "__main__":
    if os.path.exists("logfile"):
        os.remove("logfile")
    else:
        print("no existing log file found, continuing...")

    logging.basicConfig(level=logging.DEBUG, filename="logfile", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

    counter = 1
    tool_output_history = ""

    print("Enter your security automation objective:")
    user_input = sys.stdin.readline().strip()

    # Construct initial prompt
    prompt_text = prompt_file + "\n## User Input\n" + user_input
    history_prompt = prompt_text

    # Initial LLM call
    response = chat.send_message(history_prompt)
    llm_response = response.text
    print("LLM **INITIAL** response output:\n" + llm_response)
    logging.info(llm_response)

    # Agent execution loop
    while counter < 5:
        try:
            parsed_dict = ast.literal_eval(llm_response.strip())
        except Exception as e:
            print(f"Failed to parse response: {e}")
            break

        if 'cli' in parsed_dict:
            if any(cmd in parsed_dict['cli'] for cmd in prohibited_commands):
                raise Exception("**SAFETY GUARDRAIL TRIGGERED**: Attempted to run privileged command.")
            result = cli(parsed_dict['cli'])
            tool_output_history += f"\n\nCLI OUTPUT:\n{result}"

        elif 'serpapi' in parsed_dict:
            result = serpapi(parsed_dict['serpapi'])
            tool_output_history += f"\n\nSERPAPI OUTPUT:\n{result}"

        # Rebuild prompt for next iteration
        history_prompt = prompt_text + "\n## Tool Result Output History\n" + tool_output_history + f"\n## Iteration Counter\n{counter}"
        time.sleep(random.randint(3, 6))

        response = chat.send_message(history_prompt)
        llm_response = response.text
        print(f"LLM **NEXT** response output (iteration {counter}):\n" + llm_response)
        logging.info(llm_response)
        counter += 1

    # Final wrap-up
    final_prompt = history_prompt + "\n## FINAL user input\nWe have exhausted all attempts. What recommended next steps should we action?"
    response = chat.send_message(final_prompt)
    print("LLM **FINAL** response output:\n" + response.text)
    logging.info(response.text)
    logging.info(final_prompt)
