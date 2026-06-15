## Smart CS Agent 系统升级路线图

本文档是 smart-cs-agent 项目的系统升级跟踪文档。按 Agent 系统的 6 个核心层面逐一推进优化，每完成一项在此记录变更。

> 最后更新：2026-06-15

---

### 总体进度

| 层面 | 完成度 | 状态 |
|------|--------|------|
| ① 输入预处理层 | 90% | 🟡 可优化 |
| ② 上下文与记忆层 | 85% | 🟡 可优化 |
| ③ Agent 推理层 | 95% | 🟢 接近完成 |
| ④ 工具层 | 90% | 🟡 可优化 |
| ⑤ 输出处理层 | 90% | 🟡 可优化 |
| ⑥ 持久化与可观测层 | 90% | 🟡 可优化 |

---

### ① 输入预处理层

负责请求进入 Agent 前的校验、安全过滤和限流。

**现状：**
- `guardrails.py` 实现了空值/长度校验、prompt 注入检测（正则匹配）、敏感内容过滤
- `database.py` 实现了基于滑动窗口的会话级限流（20 次/分钟）
- 输入校验和 Agent 调用之间有清晰的拦截链路

**待优化项：**

- [ ] **1.1 增强 prompt 注入检测**
  当前只用简单正则匹配了几个英文模式（`ignore previous instructions`、`you are now` 等）。需补充中文注入模式（如"忽略之前的指令"、"你现在是"），以及更隐蔽的间接注入手法。可考虑引入一个 LLM-based 的注入分类器作为二级防线。
  - 涉及文件：`guardrails.py`
  - 优先级：中

- [ ] **1.2 扩充敏感词库与分级处理**
  当前敏感词库较小（十几个中英文词），且处理方式一刀切（直接转人工）。应扩充词库并引入分级：警告级（记录但不拦截）、拦截级（拒绝响应并提示）、严重级（转人工 + 告警）。
  - 涉及文件：`guardrails.py`
  - 优先级：低

- [ ] **1.3 IP 级限流**
  当前限流粒度是 session 级别，新建一个 session 就能重置配额。应增加 IP 级或 user 级的全局限流防止滥用。
  - 涉及文件：`database.py`, `main.py`
  - 优先级：低

---

### ② 上下文与记忆层

负责为 Agent 构建对话上下文，让它"记住"之前聊过什么。

**现状：**
- `memory.py` 实现了两层记忆：最近 8 条原始消息（滑动窗口）+ 超过 16 条时 LLM 自动摘要
- 摘要存到 session 的 summary 字段，下次请求时作为 SystemMessage 注入
- 摘要失败时有字符串拼接的 fallback

**待优化项：**

- [x] **2.1 引入向量语义检索（RAG）替代关键词匹配**
  已使用 DashScope text-embedding-v3 + FAISS 实现语义级别检索。search_faq 工具优先走向量搜索，未配置 API Key 时自动回退关键词匹配。返回结果新增 similarity_score 字段，confidence 从硬编码 0.9 改为使用实际相似度分数。
  - 涉及文件：`vector_store.py`（新）, `agent.py`, `main.py`, `config.py`, `.env.example`, `requirements.txt`
  - 优先级：**高** ✅ 已完成 2026-06-15

- [ ] **2.2 跨会话长期记忆**
  当前记忆只在单个 session 内有效，session 关闭后一切归零。应引入用户级的长期记忆存储（如：用户偏好、历史问题类型、常用订单），跨 session 复用。
  - 涉及文件：`memory.py`, `database.py`（新表）, `agent.py`
  - 优先级：中

- [ ] **2.3 用户画像层**
  目前没有用户画像的概念。可以在 session 和 message 数据基础上构建轻量画像：用户常见问题类型、满意度倾向、是否高频转人工等，供 Agent 在推理时参考。
  - 涉及文件：`database.py`（新表）, `agent.py`（system prompt 动态注入）
  - 优先级：低

- [ ] **2.4 记忆摘要保留原始关键点**
  当前摘要后老消息就只保留一段摘要文本，丢失了结构信息（如哪些工具被调用过、哪些订单被查询过）。摘要时应提取结构化的关键事实（key facts），而非纯自然语言总结。
  - 涉及文件：`memory.py`
  - 优先级：中

---

### ③ Agent 推理层

Agent 的核心大脑，负责决策调用什么工具、如何组合、何时停止。

**现状：**
- 使用 LangChain `create_agent` 构建 ReAct Agent
- DeepSeek 单模型，temperature=0.2，max_tokens=1024
- System prompt 包含 6 条决策规则引导工具选择
- 最大迭代 10 轮（MAX_ITERATIONS）
- 三级错误降级：Agent 失败 → 简单 LLM 链 → 静态消息

**待优化项：**

- [ ] **3.1 多模型路由**
  当前所有请求走同一个大模型。可以引入路由策略：简单 FAQ 匹配走轻量模型（快、便宜），复杂多步骤推理走大模型（准、贵）。降低延迟和成本。
  - 涉及文件：`agent.py`, `config.py`
  - 优先级：中

- [x] **3.2 推理过程中的用户反馈**
  新增 `thinking` 事件类型：流式输出中工具调用前会先发送自然语言描述（如"正在查询订单 **ORD-xxx** 的信息…"）。每个工具有定制的中文描述模板（TOOL_DESCRIPTIONS），通过 `_describe_tool_call()` 生成。main.py SSE 流已添加 thinking 事件转发。
  - 涉及文件：`agent.py`, `main.py`
  - 优先级：中 ✅ 已完成 2026-06-15

- [x] **3.3 动态 system prompt**
  SYSTEM_PROMPT 改为模板，`build_system_prompt()` 每次请求动态注入当前日期时间。Agent 创建不再绑定静态 prompt，通过 SystemMessage 按请求注入。
  - 涉及文件：`agent.py`
  - 优先级：中 ✅ 已完成 2026-06-15

- [ ] **3.4 工具调用结果的二次验证**
  当前 Agent 直接使用工具返回的结果生成回答，没有验证环节。对于关键操作（如退款状态），可以加一步验证逻辑确保工具结果合理后再呈现给用户。
  - 涉及文件：`agent.py`
  - 优先级：低

---

### ④ 工具层

Agent 可以调用的外部能力，是系统实用性的关键。

**现状：**
- 5 个工具：search_faq、query_order、check_refund、troubleshoot、transfer_to_human
- 全部使用 mock 数据（4 条订单、2 条退款、10 条 FAQ、硬编码故障方案）
- 工具返回结构化 JSON
- 工具调用有审计记录（tool_audit 表）

**待优化项：**

- [x] **4.1 接入真实业务数据源**
  创建了 `services/` 抽象层：`base.py`（Protocol 接口定义）、`mock_service.py`（mock 实现）、`__init__.py`（根据 DATA_SOURCE 配置自动切换）。agent.py 中的 MOCK_ORDERS/MOCK_REFUNDS 和 troubleshoot 硬编码数据已迁移到 mock_service.py。设置 `DATA_SOURCE=real` 并实现 `real_service.py` 即可切换到真实后端。
  - 涉及文件：`services/`（新目录，3 个文件）, `agent.py`, `config.py`, `.env.example`
  - 优先级：**高** ✅ 已完成 2026-06-15

- [x] **4.2 知识库向量化 + RAG**
  与 2.1 联动完成。新增 `vector_store.py` 模块，启动时用 DashScope text-embedding-v3 对 FAQ 数据生成 embeddings 并构建 FAISS 索引。search_faq 工具优先走向量语义检索（cosine similarity > 0.3 阈值），未初始化时自动回退关键词匹配。
  - 涉及文件：`vector_store.py`（新）, `agent.py`, `main.py`
  - 优先级：**高** ✅ 已完成 2026-06-15

- [ ] **4.3 新增工具能力**
  根据业务场景扩充工具：
  - `create_ticket`：创建工单（用户问题记录后异步处理）
  - `send_notification`：发送通知（订单状态变更、退款进度）
  - `query_account`：查询用户账户信息
  - `apply_coupon`：自动发放优惠券（安抚用户）
  - 涉及文件：`agent.py`
  - 优先级：中

- [x] **4.4 工具调用超时与重试**
  所有异步工具（query_order、check_refund、troubleshoot）的 service 调用已包装 `asyncio.wait_for(timeout=TOOL_TIMEOUT_SEC)`。超时后返回友好错误消息并建议转人工。search_faq 的向量检索也有 timeout 保护（通过 vector_store 内部的异常捕获）。
  - 涉及文件：`agent.py`
  - 优先级：中 ✅ 已完成 2026-06-15

---

### ⑤ 输出处理层

Agent 响应返回给用户前的最后把关。

**现状：**
- `sanitize_output` 清除泄漏的 system prompt 和特殊 token
- 元数据提取完整：intent、source、confidence、need_human、tools_called、trace
- SSE 流式输出带 token 流、tool_start/tool_end 事件、done 事件
- 非流式有三级降级（Agent → 简单链 → 静态消息）

**待优化项：**

- [ ] **5.1 流式输出的实时安全过滤**
  当前 sanitize_output 只在流结束后对完整内容执行，但流式过程中 token 已经实时发给前端了。如果 LLM 在流式过程中输出了敏感内容，用户已经看到。应增加 token 级的缓冲过滤机制。
  - 涉及文件：`main.py`（event_stream）, `guardrails.py`
  - 优先级：中

- [x] **5.2 响应格式化增强**
  system prompt 新增 Markdown 格式要求：粗体突出关键信息、订单信息用表格、步骤用有序列表、选项用无序列表。
  - 涉及文件：`agent.py`（system prompt 模板）
  - 优先级：中 ✅ 已完成 2026-06-15

- [ ] **5.3 置信度驱动的响应策略**
  当前 confidence 值计算了但没有实际用于响应策略。可以：低置信度（<0.5）时主动提示"我不太确定"并建议转人工；高置信度（>0.9）时直接给出答案不附加免责声明。
  - 涉及文件：`agent.py`, `main.py`
  - 优先级：低

---

### ⑥ 持久化与可观测层

数据存储、审计追踪、运行指标。

**现状：**
- 5 张表：sessions、messages、ratings、tool_audit、rate_limits
- 每条消息存储 intent/source/confidence/trace
- analytics 端点做了聚合统计
- aiosqlite 无连接池，每操作独立开关连接

**待优化项：**

- [ ] **6.1 数据库连接池**
  当前每个 DB 操作都 `connect → execute → close`，高并发下性能差。引入 aiosqlite 的连接池（或用 SQLAlchemy async session）复用连接。
  - 涉及文件：`database.py`
  - 优先级：中

- [ ] **6.2 结构化日志**
  当前只有 print 级别的错误输出。引入结构化日志（如 structlog / loguru），统一格式，记录请求 ID、session ID、工具调用链等，方便排查问题。
  - 涉及文件：全局
  - 优先级：中

- [ ] **6.3 健康检查增强**
  `/api/health` 当前只检查 API Key 是否配置。应增加：数据库连通性、LLM API 可达性、当前活跃 session 数、最近 5 分钟错误率等。
  - 涉及文件：`main.py`
  - 优先级：低

- [ ] **6.4 数据归档策略**
  随着使用增长，messages 和 tool_audit 表会越来越大。应设计归档策略：超过 N 天的数据迁移到归档表或导出为文件，保持主表轻量。
  - 涉及文件：`database.py`
  - 优先级：低

---

### 升级执行计划（建议顺序）

按优先级和依赖关系排列的推荐执行顺序：

| 批次 | 任务 | 理由 |
|------|------|------|
| **第一批** | 4.2 知识库 RAG + 2.1 向量检索 | 效果提升最明显，是 Agent 实用化的核心 |
| **第二批** | 4.1 真实数据源接入 + 4.4 工具超时重试 | 让系统从演示走向可用 |
| **第三批** | 3.3 动态 prompt + 3.2 过程反馈 + 5.2 格式化增强 | 提升用户体验 |
| **第四批** | 6.1 连接池 + 6.2 结构化日志 + 1.1 注入检测增强 | 工程化加固 |
| **第五批** | 2.2 跨会话记忆 + 2.3 用户画像 + 3.1 多模型路由 | 高级能力 |

---

### 变更记录

每完成一项升级在此追加记录。

| 日期 | 任务编号 | 变更描述 | 涉及文件 |
|------|----------|----------|----------|
| 2026-06-15 | — | 项目初始化清理：删除遗留 backend/ 目录、修正 README、修正 .env.example、清理未使用导入 | README.md, .env.example, main.py, agent.py |
| 2026-06-15 | 2.1 + 4.2 | RAG 向量语义检索：新增 vector_store.py（DashScope text-embedding-v3 + FAISS），改造 search_faq 工具为语义检索优先 + 关键词回退，confidence 改为实际相似度分数 | vector_store.py（新）, agent.py, main.py, config.py, .env.example, requirements.txt |
| 2026-06-15 | 4.1 + 4.4 | 服务抽象层 + 工具超时：新增 services/ 目录（Protocol 接口 + mock 实现 + DATA_SOURCE 切换），mock 数据从 agent.py 迁出，所有异步工具加 asyncio.wait_for 超时控制 | services/（新目录）, agent.py, config.py, .env.example |
| 2026-06-15 | 3.2 + 3.3 + 5.2 | 动态 prompt + 推理反馈 + 格式化：system prompt 改为动态模板（注入当前时间），流式新增 thinking 事件（工具调用自然语言描述），prompt 引导 Markdown 格式输出 | agent.py, main.py |
