"""Service layer — provides service instances based on DATA_SOURCE config.

Usage:
    from app.services import order_service, refund_service, troubleshoot_service

    result = await order_service.query_order("ORD20260610001")

Set DATA_SOURCE=mock (default) or DATA_SOURCE=real in .env to switch.
When DATA_SOURCE=real, you must implement real_service.py with the same interfaces.
"""

import logging

from app.config import DATA_SOURCE

logger = logging.getLogger(__name__)

if DATA_SOURCE == "real":
    # Production: real backend APIs
    try:
        from app.services.real_service import (
            RealOrderService,
            RealRefundService,
            RealTroubleshootService,
        )
        order_service = RealOrderService()
        refund_service = RealRefundService()
        troubleshoot_service = RealTroubleshootService()
        logger.info("Service layer: using REAL backend services")
    except ImportError:
        logger.warning(
            "DATA_SOURCE=real but real_service.py not found — falling back to mock. "
            "Create app/services/real_service.py with RealOrderService, "
            "RealRefundService, RealTroubleshootService classes."
        )
        from app.services.mock_service import (
            MockOrderService,
            MockRefundService,
            MockTroubleshootService,
        )
        order_service = MockOrderService()
        refund_service = MockRefundService()
        troubleshoot_service = MockTroubleshootService()
else:
    # Development/demo: mock data
    from app.services.mock_service import (
        MockOrderService,
        MockRefundService,
        MockTroubleshootService,
    )
    order_service = MockOrderService()
    refund_service = MockRefundService()
    troubleshoot_service = MockTroubleshootService()
    logger.info("Service layer: using MOCK data services")
