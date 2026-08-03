"""Real service implementation — production-grade data source behind DATA_SOURCE=real.

This is a *runnable* reference implementation of the three service Protocols defined in
``app.services.base`` (OrderService / RefundService / TroubleshootService). It is intentionally
backed by a local JSON file so it works out-of-the-box without any external dependency, while
showing exactly where you would swap in a real backend (REST/RPC/DB) — just replace the body of
each method with an ``httpx``/``aiosqlite`` call.

Switch on by setting in ``.env``:
    DATA_SOURCE=real

The service layer (``app.services.__init__``) imports this module automatically and falls back to
the mock implementation if the import fails, so the Agent code never changes.
"""

import json
import os
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Persisted "real" dataset lives next to this file. In production you would replace the
# read/write helpers with calls to your real order/refund/ticketing backend.
_DATA_PATH = os.path.join(os.path.dirname(__file__), "real_data.json")


def _load() -> dict:
    """Load the persisted dataset. Async wrapper keeps the public API awaitable."""
    if not os.path.exists(_DATA_PATH):
        return {"orders": {}, "refunds": {}, "troubleshoot": {}}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"real_service: failed to load {_DATA_PATH}: {e}")
        return {"orders": {}, "refunds": {}, "troubleshoot": {}}


def _save(data: dict) -> None:
    try:
        with open(_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.error(f"real_service: failed to save {_DATA_PATH}: {e}")


class RealOrderService:
    """Order operations against a real (here: JSON-backed) backend."""

    async def query_order(self, order_id: str) -> Optional[dict]:
        # Simulate realistic async I/O latency of a backend call.
        await asyncio.sleep(0.01)
        data = await asyncio.to_thread(_load)
        order = data.get("orders", {}).get(order_id)
        if not order:
            return None
        return {
            "order_id": order["order_id"],
            "status": order["status"],
            "product": order["product"],
            "amount": order["amount"],
            "logistics": order.get("logistics", "待分配"),
            "ordered_at": order.get("ordered_at", ""),
        }


class RealRefundService:
    """Refund operations against a real (here: JSON-backed) backend."""

    async def check_refund_by_id(self, refund_id: str) -> Optional[dict]:
        await asyncio.sleep(0.01)
        data = await asyncio.to_thread(_load)
        ref = data.get("refunds", {}).get(refund_id)
        if not ref:
            return None
        return {
            "refund_id": ref["refund_id"],
            "order_id": ref["order_id"],
            "status": ref["status"],
            "amount": ref["amount"],
            "reason": ref["reason"],
            "created_at": ref.get("created_at", ""),
            "eta": ref.get("eta", ""),
        }

    async def check_refund_by_order(self, order_id: str) -> Optional[dict]:
        await asyncio.sleep(0.01)
        data = await asyncio.to_thread(_load)
        order = data.get("orders", {}).get(order_id)
        if not order:
            return None
        # Look for an existing refund record for this order
        for ref in data.get("refunds", {}).values():
            if ref.get("order_id") == order_id:
                return {
                    "eligible": False,
                    "message": f"订单 {order_id} 已有退款单 {ref['refund_id']}，状态：{ref['status']}",
                    "amount": ref["amount"],
                }
        return {
            "eligible": True,
            "message": f"订单 {order_id}（{order['product']}）当前状态：{order['status']}，可申请退款。",
            "amount": order["amount"],
        }


class RealTroubleshootService:
    """Technical diagnosis — here backed by a JSON knowledge base, swap for a real ticketing/RCA API."""

    async def diagnose(self, issue_type: str, description: str = "") -> dict:
        await asyncio.sleep(0.01)
        data = await asyncio.to_thread(_load)
        solutions = data.get("troubleshoot", {})
        key = (issue_type or "").lower().strip()
        if key in solutions:
            sol = solutions[key]
            return {
                "found": True,
                "issue_type": key,
                "steps": sol["steps"],
                "tip": sol.get("tip", ""),
            }
        # Unknown issue — delegate to the knowledge base "other" entry if present
        if "other" in solutions:
            sol = solutions["other"]
            return {
                "found": True,
                "issue_type": "other",
                "steps": sol["steps"],
                "tip": sol.get("tip", ""),
            }
        return {
            "found": False,
            "issue_type": issue_type,
            "steps": [],
            "tip": "未能定位问题，建议转人工客服。",
        }
