# 智能客服 Agent — 前后端分离项目

基于 **LangChain ReAct Agent** 的智能客服系统，LLM 自主决策调用工具，非固定流水线。

## 项目结构

```
smart-cs-agent/
├── smart-cs-web/       # 前端 — Vue 3 + Vite
├── smart-cs-server/    # 后端 — FastAPI + LangChain
├── data/               # SQLite 数据库（运行时自动生成，已 gitignore）
└── README.md
```

## Agent 核心能力

| 能力 | 说明 |
|------|------|
| **ReAct 推理** | LLM 自主 Think→Act→Observe 循环，非固定流水线 |
| **Tool Calling** | 5 个工具自主决策调用：FAQ检索、订单查询、退款查询、故障诊断、转人工 |
| **SSE 流式** | 实时 token 流 + 工具调用状态推送 |
| **Memory** | 滑动窗口 + LLM 长对话摘要 |
| **Guardrails** | 输入验证、注入检测、内容安全、限流 |
| **Observability** | Agent 推理链路可视化（每条消息可展开查看工具调用详情） |
| **Audit** | 工具调用审计日志（调用次数、耗时、错误率） |
| **Error Recovery** | Agent 失败自动降级，SSE 断连自动回退非流式 |
| **Human-in-loop** | 自动转人工 + 手动转人工 |

## 快速启动

### 后端

```bash
cd smart-cs-server

# 1. 创建虚拟环境
python -m venv venv

# 2. 安装依赖
venv/Scripts/pip install -r requirements.txt   # Windows
# venv/bin/pip install -r requirements.txt      # Linux/Mac

# 3. 配置 API Key
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY

# 4. 启动
venv/Scripts/python run.py   # Windows
# venv/bin/python run.py      # Linux/Mac
```

后端运行在 `http://localhost:8000`

### 前端

```bash
cd smart-cs-web

# 1. 安装依赖
npm install

# 2. 开发模式（自动代理到后端）
npm run dev
```

前端运行在 `http://localhost:5173`

### 生产构建

```bash
cd smart-cs-web && npm run build
# 产物在 smart-cs-web/dist/
```

## API 概览

| Endpoint | Method | 说明 |
|----------|--------|------|
| `/api/health` | GET | 健康检查 |
| `/api/sessions` | POST | 创建会话 |
| `/api/sessions` | GET | 会话列表 |
| `/api/chat` | POST | 非流式对话 |
| `/api/chat/stream` | POST | SSE 流式对话 |
| `/api/sessions/:id/messages` | GET | 获取消息历史 |
| `/api/ratings` | POST | 提交满意度评价 |
| `/api/analytics` | GET | 管理后台数据 |
| `/api/tool-audit` | GET | 工具调用审计 |
| `/api/sessions/:id/close` | POST | 关闭会话 |

## SSE 事件格式

```
data: {"type": "token", "content": "您"}
data: {"type": "tool_start", "tool": "query_order", "input": {"order_id": "ORD20260610001"}}
data: {"type": "tool_end", "tool": "query_order", "output": {...}, "duration_ms": 120}
data: {"type": "done", "intent": "order", "source": "system", "confidence": 0.95, ...}
```
