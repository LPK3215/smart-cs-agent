"""Tests for the service layer (mock + real implementations against Protocols)."""

import pytest

from app.services.base import OrderService, RefundService, TroubleshootService
from app.services import order_service, refund_service, troubleshoot_service
from app.services.real_service import (
    RealOrderService,
    RealRefundService,
    RealTroubleshootService,
)


@pytest.mark.asyncio
async def test_mock_order_service():
    order = await order_service.query_order("ORD20260610001")
    assert order is not None
    assert order["order_id"] == "ORD20260610001"


@pytest.mark.asyncio
async def test_real_order_service_matches_protocol():
    assert isinstance(RealOrderService(), OrderService)
    svc = RealOrderService()
    order = await svc.query_order("SO20240101001")
    assert order["status"] == "已发货"


@pytest.mark.asyncio
async def test_real_refund_service():
    assert isinstance(RealRefundService(), RefundService)
    svc = RealRefundService()
    ref = await svc.check_refund_by_id("RF20240101001")
    assert ref["status"] == "审核中"
    eligible = await svc.check_refund_by_order("SO20240101002")
    assert eligible["eligible"] is True


@pytest.mark.asyncio
async def test_real_troubleshoot_service():
    assert isinstance(RealTroubleshootService(), TroubleshootService)
    svc = RealTroubleshootService()
    res = await svc.diagnose("login")
    assert res["found"] is True
    assert len(res["steps"]) > 0
    # unknown issue falls back to "other"
    res2 = await svc.diagnose("unknown-xyz")
    assert res2["found"] is True
    assert res2["issue_type"] == "other"


@pytest.mark.asyncio
async def test_services_are_protocol_conformant():
    assert isinstance(order_service, OrderService)
    assert isinstance(refund_service, RefundService)
    assert isinstance(troubleshoot_service, TroubleshootService)
