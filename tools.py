from __future__ import annotations

from typing import Any


ORDERS: dict[str, dict[str, Any]] = {
    "R-1001": {
        "customer_id": "C-001",
        "customer_name": "Avery",
        "status": "delivered",
        "days_since_delivery": 7,
        "amount": 89.99,
        "flags": [],
    },
    "R-1002": {
        "customer_id": "C-002",
        "customer_name": "Blair",
        "status": "delivered",
        "days_since_delivery": 45,
        "amount": 49.00,
        "flags": [],
    },
    "R-1003": {
        "customer_id": "C-003",
        "customer_name": "Casey",
        "status": "lost",
        "days_since_delivery": 0,
        "amount": 149.00,
        "flags": [],
    },
    "R-1004": {
        "customer_id": "C-004",
        "customer_name": "Devon",
        "status": "delivered",
        "days_since_delivery": 12,
        "amount": 279.00,
        "flags": ["chargeback_open"],
    },
}

DECISION_LOG: list[dict[str, Any]] = []


def check_order_status(order_id: str) -> dict[str, Any]:
    """Return order status details for a refund request."""
    order = ORDERS.get(order_id)
    if not order:
        return {
            "found": False,
            "order_id": order_id,
            "status": "unknown",
            "days_since_delivery": -1,
            "amount": 0.0,
            "flags": ["order_not_found"],
        }
    return {"found": True, "order_id": order_id, **order}


def lookup_refund_policy(
    order_status: str,
    days_since_delivery: int,
    reason: str,
    amount: float = 0.0,
    flags_csv: str = "",
) -> dict[str, Any]:
    """Apply the sample refund policy and return the recommended action."""
    flags = [flag.strip() for flag in flags_csv.split(",") if flag.strip()]
    reason_key = reason.lower().replace(" ", "_")

    if order_status == "unknown" or "order_not_found" in flags:
        return {
            "decision": "escalate",
            "policy_code": "ORDER_NOT_FOUND",
            "rationale": "The order could not be verified.",
        }

    if "chargeback_open" in flags:
        return {
            "decision": "escalate",
            "policy_code": "CHARGEBACK_OPEN",
            "rationale": "Open payment disputes require specialist review.",
        }

    if amount >= 500:
        return {
            "decision": "escalate",
            "policy_code": "HIGH_VALUE_ORDER",
            "rationale": "High-value refunds require manager approval.",
        }

    if order_status in {"lost", "stuck_in_transit"}:
        return {
            "decision": "refund",
            "policy_code": "SHIPMENT_FAILURE",
            "rationale": "Lost or stalled shipments are refundable.",
        }

    if order_status == "already_refunded":
        return {
            "decision": "deny",
            "policy_code": "ALREADY_REFUNDED",
            "rationale": "The order has already been refunded.",
        }

    if (
        order_status == "delivered"
        and days_since_delivery <= 30
        and reason_key in {"damaged", "wrong_item", "missing_item"}
    ):
        return {
            "decision": "refund",
            "policy_code": "DELIVERED_30_DAY_DEFECT",
            "rationale": "Damaged, wrong, or missing items are refundable within 30 days.",
        }

    if order_status == "delivered" and days_since_delivery > 30:
        return {
            "decision": "deny",
            "policy_code": "OUTSIDE_RETURN_WINDOW",
            "rationale": "The request is outside the 30-day refund window.",
        }

    return {
        "decision": "deny",
        "policy_code": "NO_POLICY_MATCH",
        "rationale": "The request does not meet the sample refund criteria.",
    }


def log_refund_decision(
    order_id: str,
    customer_id: str,
    decision: str,
    policy_code: str,
    customer_response: str,
) -> dict[str, Any]:
    """Log the final refund decision. This stub writes to an in-memory list."""
    record = {
        "order_id": order_id,
        "customer_id": customer_id,
        "decision": decision,
        "policy_code": policy_code,
        "customer_response": customer_response,
    }
    DECISION_LOG.append(record)
    return {"logged": True, "record": record}
