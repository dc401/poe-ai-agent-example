# poe-ai-agent-example
This is an example build of using Poe.com's API to create an LLM based AI agent that can execute commands and tools in a multi-shot way without relying on LangGraph, LangChain, GCP Vertex, or Amazon Bedrock. It is just a generic multi shot LLM "agent" without the agentic framework.

More information at the Medium article: "[Create Lightweight Agentic AI Tools](https://dwchow.medium.com/create-lightweight-agentic-ai-tools-99a65bd2caa5)"

## Caution
Please note that this is considered a proof of concept piece of code. Although I do show you how to use basic guard rails, this may not protect against everything, including data leaking of important system information in an uncontrolled LLM. You should replace the poe.com agent with a trusted instance of an LLM running in a production or corporate env. Please do NOT run this on a production network without extensive testing and additional guard rails, including consideration for changing from poe.com to any other LLM API client that you TRUST. That being said, there is NO EXPRESSED WARRANTY.

## Summary
This project is a quick and dirty way of using a multi-shot AI agent approach using a single LLM. We wrap poe.com's [fastapi](https://github.com/poe-platform/fastapi_poe) using their standard Python 3.x client and then parse the output appending a large prompt to maintain state. I chose poe.com because of their simple API to be able to use a custom "bot" that has their version of referenced RAG documents or any choice of desired LLM. The demonstrated one is Claude 3.5 Sonnet at the time of this writing, so if you change it, you might have to modify your prompt.md

## Why
To show you that you don't need a fancy framework like Vertex, Bedrock, or LangChain. You can implement very basic, yet limited agents yourself. Other frameworks have nice management and modulation, but if you want to just get a single purpose agent done, this is an easy to use template with multi-shot capabilities. 

## Initial findings
I've found that Claude 3.5 Sonnet at the time of this development likes to deviate from the prompt instructions after about 3 iterations if the prompt becomes excessively large or if you are performing fast, frequent calls, it starts using sudo and commands. However, its thoughts aren't wrong and it wishes to explore.  Poe.com has a fairly limited API so you can't rapid fire too much. With additional guard rails and human in the loop for with additional logic on executed tools, this is promising.

## Features

 - Modular "base" prompt in mark down so you can add and remove tools
 - Exponential back off client adjustment for API key throttling
 - Easy tracing using almost an egregious amount of print statements and logging
 - Very basic prohibited word list guard rails against local system execution
 - Standard in support so you can dynamically call this as a script
 
 ### TODO
 
 - Use multiple chat sessions and track those individually to support for LLMs with less token context
 - Add multi LLM support to bounce ideas off each other
 - Add ability to reference existing documentation and context with RAG without single shot giant prompts
 - Maybe port this to Go? Bleh.

### How to use

    mkdir poe-agent && cd poe-agent
    python3 -m venv .
    source ./bin/activate
    pip3 install -r requirements.txt
    export POE_API='<YOUR-KEY>'
    export SERP_API='<YOUR-KEY>'
    echo "Please determine the OS of the local host we are running and then enumerate what existing hardening settings are enabled." | python3 ./poe-agent.py 

 ## Engage
 Please feel to drop me a line and engage:
 LinkedIn [@dwchow](https://www.linkedin.com/in/dwchow/)
 YouTube [@xtecsystems](https://www.youtube.com/@xtecsystems)
 Medium [@dwchow](https://dwchow.medium.com/)

## Output with Safeguard Trigger
![enter image description here](https://github.com/dc401/poe-ai-agent-example/blob/main/python-poe-ai-agent-output.png?raw=true)

## Output Completing Successfully
![enter image description here](https://github.com/dc401/poe-ai-agent-example/blob/main/python-poe-ai-agent-output-2.png?raw=true)
