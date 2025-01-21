#!/usr/bin/env python3
import fastapi_poe as fp
import asyncio, os, subprocess, ast, time, logging, sys
from serpapi import GoogleSearch

#usage
#echo 'Please determine the OS of the local host we are running and then enumerate what existing hardening settings are enabled.' | python3 ./poe-agent.py

#read secrets from environment variables
poe_api_key = os.environ['POE_API']
serp_api_key = os.environ['SERP_API']

#need to use async because bot will have multi-line outputs that need to complete
#https://developer.poe.com/server-bots/accessing-other-bots-on-poe
#use the official botname case sensitive from poe or your custom name of one you created
'''
async def get_responses(api_key, messages, bot_name="Claude-3.5-Sonnet"):
  response = ""
  print(f"Using bot: {bot_name}")
  async for partial in fp.get_bot_response(messages=messages,
                                           bot_name=bot_name,
                                           api_key=poe_api_key,
                                           temperature=0.15):
    if isinstance(partial, fp.PartialResponse) and partial.text:
      response += partial.text

  return response
'''
async def get_responses(api_key, messages, bot_name="Claude-3.5-Sonnet"):
    response = ""
    print(f"Using bot: {bot_name}")
    #try expotential back off
    max_retries = 3
    base_delay = 3

    for attempt in range(max_retries):
        try:
            async for partial in fp.get_bot_response(messages=messages,
                                                   bot_name=bot_name,
                                                   api_key=poe_api_key,
                                                   temperature=0.15):
                if isinstance(partial, fp.PartialResponse) and partial.text:
                    response += partial.text
            return response
        except Exception as e:
            if attempt == max_retries - 1:  #final attempt
                raise e
            wait_time = base_delay * (2 ** attempt)
            print(f"Attempt {attempt + 1} failed, retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
    return response

  
#prepend markdown prompt
prompt_file = open('prompt.md', 'r').read()

#tools for LLM to use
def serpapi(query):
  params = {
  query: "Coffee",
  "location": "Weston, FL, United States",
  "hl": "en",
  "gl": "us",
  "google_domain": "google.com",
  "api_key": serp_api_key
    }
  search = GoogleSearch(params)
  results = search.get_dict()
  print(result)
  return str(results)

def cli(command):
  #need pipe subprocess to standard out to get the output to return
  result = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
  print(result)
  return str(result)

#main driver
if __name__ == "__main__":
  if os.path.exists("logfile"):
     os.remove("logfile")
  else:
     print("no existing log file found, continuing...")
  #state variables
  counter = 1
  tool_output_history = ""
  prohibited_commands = ['sudo', 'runas', 'del', 'rm', 'chmod', 'icacls']
  line = ""

  logging.basicConfig(level=logging.DEBUG, filename="logfile", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")
  #clean up old logfile for this runtime

  #user sample input usage 
  #user_input = 'Please determine the OS of the local host we are running and then enumerate what existing hardening settings are enabled.'

  #read from standard in for easier automation integration
  for line in sys.stdin:
     user_input = str(line)

#construct initial prompt
prompt_text = prompt_file + '\n ## User Input \n' + user_input
message = fp.ProtocolMessage(role="user", content=(prompt_text))
#prompt expected output {'tool' : 'command/query'}
llm_response = asyncio.run(get_responses(poe_api_key, [message]))
print("LLM **INITIAL** response output \n" +llm_response)
logging.info(llm_response)
#multi shot iteration and "agentic execution"
while counter < 5:
    #convert response into dictionary
    parsed_dict = ast.literal_eval(llm_response)
      #extract commands and run tools
    if 'cli' in parsed_dict:
            #quick and dirty  nested for loop, sorry
            if any(cmd in parsed_dict['cli'] for cmd in prohibited_commands):
               raise Exception("**SAFETY GUARDRAIL TRIGGERED**: AI agent tried to run with elevated privileges")
            else:
                result = cli(str(parsed_dict['cli']))
                tool_output_history +=result
    elif 'serpapi' in parsed_dict:
        result = serpapi(str(parsed_dict['serpapi']))
        tool_output_history +=result
    #replace the old prompt with the appended stuff
    appended_prompt_text = prompt_text + '\n' + '## Tool Result Output History' + '\n' + tool_output_history + '\n' + '## Iteration Counter' + '\n' + str(counter)
    #time.sleep(1.5) replaced with expotential back off at the client
    #re-initiate the pull using appended message
    message = fp.ProtocolMessage(role="user", content=(appended_prompt_text))
    llm_response = asyncio.run(get_responses(poe_api_key, [message]))
    print("LLM **NEXT** response output \n" +llm_response)
    print("Running iteration.." + str(counter))
    logging.info(llm_response)
    counter +=1 # need to increment to keep state updated

#last thought known at the end of our shots
appended_prompt_text += '\n' + '## FINAL user input' + '\n' + "We have exhausted all attempts. What recommended next steps should we action?"
message = fp.ProtocolMessage(role="user", content=(appended_prompt_text))
llm_response = asyncio.run(get_responses(poe_api_key, [message]))
print("LLM **FINAL** response output \n" + llm_response)
logging.info(llm_response)
logging.info(appended_prompt_text)
exit()

                               