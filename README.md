# TermAgent
TermAgent is a terminal assistance system that helps users who are unfamiliar with commands or struggle with environment setup, operations, and deployment tasks.

## Features
- Manual mode: select commands through an interactive prompt
- Manual execution: use @ to run a command directly
- Auto mode: not implemented yet

## Model and API
TermAgent uses OpenAI-compatible APIs. Use `term set` to configure the model and endpoint as long as the provider supports the OpenAI client interface.

## Install
### Install from TestPyPI
```bash
pip install -i https://test.pypi.org/simple/ term-agent --extra-index-url https://pypi.org/simple/
```

## Quick Start
### 1) Check command help
```bash
term help
term -h
```

### 2) Configure API settings
```bash
term set --api-key
term set --api-base
term set --model
```

### 3) Run TermAgent
```bash
term run
term run -m
```
