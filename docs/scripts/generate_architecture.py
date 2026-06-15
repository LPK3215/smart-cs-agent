"""Generate system architecture SVG for Smart CS Agent.

Usage:
    cd docs/scripts
    python generate_architecture.py

Output:
    ../architecture.svg

Dependencies: none (pure Python, no third-party libraries required)
"""

SVG_WIDTH = 840
SVG_HEIGHT = 620
BOX_PAD_X = 24
BOX_PAD_Y = 18
FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"


def box(x, y, w, h, rx=8):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="#ffffff" stroke="#d0d5dd" stroke-width="1.5"/>'


def text(x, y, content, size=13, color="#101828", bold=False, anchor="start"):
    weight = "bold" if bold else "normal"
    return f'<text x="{x}" y="{y}" font-family="{FONT_FAMILY}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{content}</text>'


def pill(x, y, w, h, label, fill="#f0f5ff", stroke="#b2cfff", color="#1d4ed8"):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
        f'<text x="{x+w/2}" y="{y+16}" font-family="{FONT_FAMILY}" font-size="11" fill="{color}" font-weight="600" text-anchor="middle">{label}</text>'
    )


def arrow(x1, y1, x2, y2):
    marker = '<marker id="arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#667085"/></marker>'
    return marker + f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#667085" stroke-width="1.5" marker-end="url(#arrow)"/>'


def down_arrow(x, y, label=""):
    parts = [f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y+30}" stroke="#667085" stroke-width="1.5" marker-end="url(#arrow)"/>']
    if label:
        parts.append(f'<text x="{x+12}" y="{y+20}" font-family="{FONT_FAMILY}" font-size="10" fill="#667085">{label}</text>')
    return "\n".join(parts)


def generate():
    parts = []

    # SVG header
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">')
    parts.append('<defs><marker id="arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#667085"/></marker></defs>')
    parts.append(f'<rect width="{SVG_WIDTH}" height="{SVG_HEIGHT}" fill="#f9fafb" rx="12"/>')

    # Title
    parts.append(text(SVG_WIDTH / 2, 32, "Smart CS Agent — 系统架构", size=18, color="#101828", bold=True, anchor="middle"))

    # ── USER CLIENT (top) ──
    parts.append(box(60, 52, 720, 68))
    parts.append(text(80, 76, "用户端 /user", size=14, color="#1d4ed8", bold=True))
    parts.append(text(80, 96, "注册/登录 → 智能对话 → 会话历史 → 满意度评价 → 个人中心", size=11, color="#475467"))
    parts.append(text(700, 76, "Vue 3 + Vite 8 + Element Plus", size=10, color="#98a2b3", anchor="end"))

    # Arrow: User → Server
    parts.append(down_arrow(420, 120, "SSE Stream / REST API"))

    # ── SERVER (middle) ──
    parts.append(box(60, 152, 720, 280))

    # Row 1: Auth / Agent / Guardrails
    parts.append(pill(80, 170, 100, 28, "Auth (JWT)", fill="#ecfdf5", stroke="#a7f3d0", color="#047857"))
    parts.append(pill(200, 170, 130, 28, "ReAct Agent 引擎", fill="#eff6ff", stroke="#bfdbfe", color="#1e40af"))
    parts.append(pill(350, 170, 110, 28, "Guardrails 三级", fill="#fef3c7", stroke="#fcd34d", color="#b45309"))

    # Tool Layer box
    parts.append(box(80, 210, 680, 108, rx=6))
    parts.append(text(95, 230, "Tool Layer（5 个工具，Agent 自主决策调用）", size=12, color="#475467", bold=True))

    # Tool pills
    tools = [
        (95, 248, "FAQ 检索", "#e0e7ff", "#a5b4fc", "#3730a3"),
        (200, 248, "订单查询", "#d1fae5", "#6ee7b7", "#065f46"),
        (305, 248, "退款查询", "#d1fae5", "#6ee7b7", "#065f46"),
        (410, 248, "故障诊断", "#fce7f3", "#f9a8d4", "#9d174d"),
        (515, 248, "转人工", "#fef3c7", "#fcd34d", "#b45309"),
    ]
    for x, y, label, fill, stroke, color in tools:
        parts.append(pill(x, y, 105, 26, label, fill, stroke, color))

    # RAG + Service sub-rows
    parts.append(text(95, 296, "向量检索 (RAG)", size=10, color="#667085", bold=True))
    parts.append(text(195, 296, "FAISS + DashScope text-embedding-v3，余弦相似度 ≥0.3 阈值，自动回退关键词匹配", size=10, color="#98a2b3"))
    parts.append(text(95, 312, "服务抽象层", size=10, color="#667085", bold=True))
    parts.append(text(195, 312, "Protocol 接口定义，mock ⇄ real 一键切换（DATA_SOURCE 配置）", size=10, color="#98a2b3"))

    # Row 3: Memory / User Context / Audit / Analytics
    infra_y = 335
    parts.append(pill(80, infra_y, 155, 28, "Memory 滑动窗口+摘要", fill="#f5f3ff", stroke="#ddd6fe", color="#6d28d9"))
    parts.append(pill(252, infra_y, 155, 28, "User Context 画像+长期记忆", fill="#f5f3ff", stroke="#ddd6fe", color="#6d28d9"))
    parts.append(pill(424, infra_y, 145, 28, "Tool Audit 调用审计", fill="#f5f3ff", stroke="#ddd6fe", color="#6d28d9"))
    parts.append(pill(586, infra_y, 155, 28, "Analytics 数据聚合", fill="#f5f3ff", stroke="#ddd6fe", color="#6d28d9"))

    # Row 4: DB
    parts.append(pill(260, 380, 340, 28, "SQLite (WAL mode, 8 tables)", fill="#f9fafb", stroke="#d0d5dd", color="#475467"))

    # Arrow: Server → Admin
    parts.append(down_arrow(420, 432, ""))

    # ── ADMIN CLIENT (bottom) ──
    parts.append(box(60, 470, 720, 68))
    parts.append(text(80, 494, "管理端 /admin", size=14, color="#7c3aed", bold=True))
    parts.append(text(80, 514, "管理员登录 → 数据仪表盘 → 审计日志 → 会话管理 → 用户管理", size=11, color="#475467"))
    parts.append(text(700, 494, "独立路由 · 独立布局 · AdminLayout", size=10, color="#98a2b3", anchor="end"))

    # Data flow labels
    parts.append(box(60, 555, 720, 50, rx=6))
    parts.append(text(80, 575, "📊 仪表盘组件: StatCards · IntentChart · SourceDonut · RatingChart · ResolutionBars · ToolStatsTable · ConversationTable", size=11, color="#475467"))

    # Footer
    parts.append(text(SVG_WIDTH / 2, SVG_HEIGHT - 12, "Smart CS Agent v2.0 — AI 课程设计 / 竞赛项目 / 企业客服原型", size=10, color="#98a2b3", anchor="middle"))

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    import os
    svg_content = generate()
    output_path = os.path.join(os.path.dirname(__file__), "..", "architecture.svg")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Architecture SVG saved to: {os.path.abspath(output_path)}")
