from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from agent import run_refund_assistant


def _as_dict(result: Any) -> dict[str, Any]:
    if isinstance(result, dict) and "decision" in result:
        return result
    if isinstance(result, dict) and "messages" in result:
        content = result["messages"][-1].content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"decision": "unparseable", "customer_response": content, "tool_trace": []}
    return {"decision": "unparseable", "customer_response": str(result), "tool_trace": []}


def grade_case(case: dict[str, Any], result: dict[str, Any]) -> dict[str, bool]:
    trace_tools = {entry.get("tool") for entry in result.get("tool_trace", [])}
    response = result.get("customer_response", "")

    return {
        "correctness": result.get("decision") == case["expected_decision"],
        "policy_compliance": result.get("policy_code") == case["expected_policy_code"],
        "tool_use_accuracy": {
            "check_order_status",
            "lookup_refund_policy",
            "log_refund_decision",
        }.issubset(trace_tools),
        "response_quality": bool(response)
        and "tool" not in response.lower()
        and len(response.split()) >= 18,
        "escalation_safety": (
            case["expected_decision"] != "escalate"
            or result.get("decision") == "escalate"
        ),
    }


def run_evals(use_llm: bool = False) -> dict[str, Any]:
    cases = json.loads(Path("sample_cases.json").read_text())
    rows = []
    for case in cases:
        result = _as_dict(run_refund_assistant(case, use_llm=use_llm))
        grades = grade_case(case, result)
        rows.append({"id": case["id"], "decision": result.get("decision"), **grades})

    metric_names = [
        "correctness",
        "policy_compliance",
        "tool_use_accuracy",
        "response_quality",
        "escalation_safety",
    ]
    summary = {
        metric: sum(1 for row in rows if row[metric]) / len(rows)
        for metric in metric_names
    }
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    report = run_evals(use_llm=os.getenv("USE_LLM") == "1")
    print(json.dumps(report, indent=2))
