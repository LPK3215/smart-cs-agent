"""Service layer — abstract interfaces for business data operations.

Defines Protocol-based interfaces that both mock and real implementations
must satisfy. The agent's tool functions call through these interfaces,
making it trivial to swap between mock data and real backend APIs.
"""

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class OrderService(Protocol):
    """Interface for order-related business operations."""

    async def query_order(self, order_id: str) -> Optional[dict]:
        """Query order details by ID.

        Returns:
            Dict with keys: order_id, status, product, amount, logistics, ordered_at
            or None if not found.
        """
        ...


@runtime_checkable
class RefundService(Protocol):
    """Interface for refund-related business operations."""

    async def check_refund_by_id(self, refund_id: str) -> Optional[dict]:
        """Check refund status by refund ID.

        Returns:
            Dict with keys: refund_id, order_id, status, amount, reason, created_at, eta
            or None if not found.
        """
        ...

    async def check_refund_by_order(self, order_id: str) -> Optional[dict]:
        """Check refund eligibility for a given order.

        Returns:
            Dict with keys: eligible (bool), message, amount
            or None if order not found.
        """
        ...


@runtime_checkable
class TroubleshootService(Protocol):
    """Interface for technical troubleshooting operations."""

    async def diagnose(self, issue_type: str, description: str = "") -> dict:
        """Diagnose a technical issue and return solutions.

        Returns:
            Dict with keys: found (bool), issue_type, steps (list), tip
        """
        ...
