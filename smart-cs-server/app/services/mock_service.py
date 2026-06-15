"""Mock service implementation — uses hardcoded data for development/demo.

This is the default data source when DATA_SOURCE=mock (or unset).
Swap to real_service.py for production by setting DATA_SOURCE=real in .env.
"""

import json


# ============================================================
# Mock Data
# ============================================================

MOCK_ORDERS = {
    "ORD20260610001": {
        "order_id": "ORD20260610001",
        "status": "已签收",
        "product": "蓝牙耳机 Pro",
        "amount": 299,
        "logistics": "顺丰 SF1234567890",
        "ordered_at": "2026-06-10",
    },
    "ORD20260608002": {
        "order_id": "ORD20260608002",
        "status": "配送中",
        "product": "手机壳套装",
        "amount": 59,
        "logistics": "中通 ZT9876543210",
        "ordered_at": "2026-06-08",
    },
    "ORD20260605003": {
        "order_id": "ORD20260605003",
        "status": "已发货",
        "product": "充电宝 20000mAh",
        "amount": 129,
        "logistics": "圆通 YT5678901234",
        "ordered_at": "2026-06-05",
    },
    "ORD20260603004": {
        "order_id": "ORD20260603004",
        "status": "待发货",
        "product": "数据线三合一",
        "amount": 29,
        "logistics": "待分配",
        "ordered_at": "2026-06-03",
    },
}

MOCK_REFUNDS = {
    "REF001": {
        "refund_id": "REF001",
        "order_id": "ORD20260610001",
        "status": "审核中",
        "amount": 299,
        "reason": "商品质量问题",
        "created_at": "2026-06-12",
        "eta": "1-2个工作日审核",
    },
    "REF002": {
        "refund_id": "REF002",
        "order_id": "ORD20260605003",
        "status": "已通过",
        "amount": 129,
        "reason": "不想要了",
        "created_at": "2026-06-11",
        "eta": "3-5个工作日到账",
    },
}

TROUBLESHOOT_SOLUTIONS = {
    "crash": {
        "steps": [
            "1. 清理APP缓存：设置 → 应用管理 → 清除缓存",
            "2. 更新到最新版本：应用商店检查更新",
            "3. 卸载重装：长按APP图标 → 卸载 → 重新下载安装",
            "4. 检查手机系统版本是否低于最低要求（Android 8.0 / iOS 13）",
        ],
        "tip": "如果重装后仍闪退，可能是手机兼容性问题，建议转人工技术支持。"
    },
    "login": {
        "steps": [
            "1. 忘记密码：登录页 →「忘记密码」→ 手机验证码重置",
            "2. 收不到验证码：检查手机号是否正确 → 查看短信拦截 → 等待60秒后重试",
            "3. 账号被锁定：连续输错5次密码会锁定30分钟，之后自动解锁",
            "4. 第三方登录失败：检查微信/QQ是否正常授权",
        ],
        "tip": "如果以上方法均无效，可能是账号异常，需要人工客服解锁。"
    },
    "payment": {
        "steps": [
            "1. 检查网络连接是否正常",
            "2. 更换支付方式（微信/支付宝/银行卡）",
            "3. 检查银行卡余额和限额",
            "4. 确认是否超过单笔支付限额",
        ],
        "tip": "如果支付扣款但订单未生成，请保留支付截图联系人工客服核实。"
    },
    "slow": {
        "steps": [
            "1. 切换到更稳定的网络（WiFi/4G）",
            "2. 关闭VPN/代理软件",
            "3. 清理APP缓存后重启",
            "4. 检查手机存储空间是否不足",
        ],
        "tip": "如果是特定页面加载慢，可能是服务器维护中，请稍后重试。"
    },
}


# ============================================================
# Mock Service Implementations
# ============================================================

class MockOrderService:
    """Mock order service — returns data from MOCK_ORDERS dict."""

    async def query_order(self, order_id: str) -> dict | None:
        return MOCK_ORDERS.get(order_id)


class MockRefundService:
    """Mock refund service — returns data from MOCK_REFUNDS dict."""

    async def check_refund_by_id(self, refund_id: str) -> dict | None:
        return MOCK_REFUNDS.get(refund_id)

    async def check_refund_by_order(self, order_id: str) -> dict | None:
        order = MOCK_ORDERS.get(order_id)
        if order:
            return {
                "eligible": True,
                "message": f"订单 {order_id}（{order['product']}）当前状态：{order['status']}，可申请退款。",
                "amount": order["amount"],
            }
        return None


class MockTroubleshootService:
    """Mock troubleshoot service — returns data from TROUBLESHOOT_SOLUTIONS dict."""

    async def diagnose(self, issue_type: str, description: str = "") -> dict:
        key = issue_type.lower().strip()
        if key in TROUBLESHOOT_SOLUTIONS:
            sol = TROUBLESHOOT_SOLUTIONS[key]
            return {
                "found": True,
                "issue_type": key,
                "steps": sol["steps"],
                "tip": sol["tip"],
            }
        return {
            "found": True,
            "issue_type": "other",
            "steps": [
                "1. 尝试清理缓存并重启APP",
                "2. 更新到最新版本",
                "3. 切换网络环境重试",
                "4. 如果问题持续，请详细描述错误信息以便进一步诊断",
            ],
            "tip": "提供具体的错误提示或截图可以帮助更快定位问题。",
        }
