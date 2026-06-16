# ReAct-Style Refund Agent

This sample uses the current LangChain v1 `create_agent` API for a lightweight
ReAct-style customer support refund assistant. The included evals run locally
without API keys by using a deterministic path over stubbed tools.

## Run local evals

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python evals.py
```

## Run with a real model

Set a LangChain model identifier and provider key, then enable the LLM path:

```bash
export MODEL_ID="openai:gpt-4.1-mini"
export OPENAI_API_KEY="your-key"
export USE_LLM=1
python agent.py
```

LangChain APIs evolve. Check the official docs before using this in production:
https://docs.langchain.com/oss/python/langchain/agents
