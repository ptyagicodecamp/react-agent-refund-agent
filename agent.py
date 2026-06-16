from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import config

from tools import check_order_status, log_refund_decision, lookup_refund_policy


SYSTEM_PROMPT = """You are a customer support refund assistant.
Read the customer request, check the order, apply the refund policy, decide one of
refund, escalate, or deny, draft a brief customer-facing response, and log the
decision. Always call the order, policy, and logging tools before the final answer.
Return compact JSON with: decision, policy_code, rationale, customer_response."""


def _draft_response(name: str, decision: str, policy_code: str) -> str:
    if decision == "refund":
        return (
            f"Hi {name}, thanks for reaching out. We reviewed your order and "
            f"approved the refund under policy {policy_code}. You will receive "
            "a confirmation once it is processed."
        )
    if decision == "escalate":
        return (
            f"Hi {name}, thanks for reaching out. We need a specialist to review "
            "this request before making a refund decision. We have escalated it "
            "and will follow up with the next update."
        )
    return (
        f"Hi {name}, thanks for reaching out. We reviewed your order and are not "
        f"able to approve a refund under policy {policy_code}. If you think we "
        "missed important details, reply with more information and we can review it."
    )


def deterministic_refund_assistant(case: dict[str, Any]) -> dict[str, Any]:
    """Local, deterministic version used by the sample evals."""
    trace: list[dict[str, Any]] = []

    order = check_order_status(case["order_id"])
    trace.append({"tool": "check_order_status", "output": order})

    policy = lookup_refund_policy(
        order_status=order["status"],
        days_since_delivery=order["days_since_delivery"],
        reason=case["reason"],
        amount=float(order["amount"]),
        flags_csv=",".join(order.get("flags", [])),
    )
    trace.append({"tool": "lookup_refund_policy", "output": policy})

    response = _draft_response(
        name=order.get("customer_name", "there"),
        decision=policy["decision"],
        policy_code=policy["policy_code"],
    )

    log_result = log_refund_decision(
        order_id=case["order_id"],
        customer_id=order.get("customer_id", case.get("customer_id", "unknown")),
        decision=policy["decision"],
        policy_code=policy["policy_code"],
        customer_response=response,
    )
    trace.append({"tool": "log_refund_decision", "output": log_result})

    return {
        "order_id": case["order_id"],
        "decision": policy["decision"],
        "policy_code": policy["policy_code"],
        "rationale": policy["rationale"],
        "customer_response": response,
        "tool_trace": trace,
    }


def build_langchain_agent(model_id: str | None = None):
    """Build the current LangChain v1 ReAct-style agent loop."""
    from langchain.agents import create_agent

    return create_agent(
        model=model_id or config.MODEL_ID,
        tools=[check_order_status, lookup_refund_policy, log_refund_decision],
        system_prompt=SYSTEM_PROMPT,
    )


def run_refund_assistant(case: dict[str, Any], use_llm: bool | None = None) -> Any:
    """Run the assistant. Default is deterministic so evals work without keys."""
    should_use_llm = use_llm if use_llm is not None else config.USE_LLM
    if not should_use_llm:
        return deterministic_refund_assistant(case)

    agent = build_langchain_agent()
    message = (
        f"Customer message: {case['message']}\n"
        f"Order ID: {case['order_id']}\n"
        f"Reason: {case['reason']}"
    )
    return agent.invoke({"messages": [{"role": "user", "content": message}]})


if __name__ == "__main__":
    sample = {
        "order_id": "R-1001",
        "reason": "damaged",
        "message": "My item arrived damaged. Can I get a refund?",
    }
    print(json.dumps(run_refund_assistant(sample), indent=2))
