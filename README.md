# TermAgent
TermAgent is a terminal assistance system that helps users who are unfamiliar with commands or struggle with environment setup, operations, and deployment tasks.

## Features
- Manual mode: select commands through an interactive prompt
- Manual execution: use @ to run a command directly
- Auto mode: not implemented yet

## Model and API
TermAgent uses OpenAI-compatible APIs. Use `term set` to configure the model and endpoint as long as the provider supports the OpenAI client interface.

## Quick Start
python -m term_agent.main help
python -m term_agent.main -h
python -m term_agent.main set --api-key
python -m term_agent.main set --api-base
python -m term_agent.main set --model
python -m term_agent.main run
python -m term_agent.main run -m
