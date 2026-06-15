# Changelog

All notable changes to this project will be documented in this file.

## [2.0.1] — 2026-06-15

### Changed
- README: 修正数据库表数 7→8（新增 users 表未计入）
- README: 修正安全护栏注入模式数 15+→23（含注入检测+内容安全）
- README: 细化前端项目结构目录树（补全 composables/、admin 组件数、chat 组件数）
- README: Vue 徽章版本号精确到 3.5
- 新增 docs/architecture.svg 系统架构图（替代纯 ASCII 文本）
- 新增 docs/scripts/generate_architecture.py SVG 生成脚本（可复用）
- README: 系统架构段落改为 SVG 图 + ASCII 折叠详情

## [2.0.0] — 2026-06-15

### Added
- 用户端与管理端前后端分离（独立路由、独立布局、独立登录页）
- AdminLayout 独立管理后台布局
- AdminLoginView 独立管理员登录页
- RAG 向量语义检索（DashScope text-embedding-v3 + FAISS）
- 跨会话长期记忆（user_memories 表，session 关闭自动提取）
- 用户画像聚合（user_profiles 表，意图/评分/转人工率统计）
- 多模型路由（轻量/完整模型按输入复杂度分流）
- 服务抽象层（Protocol 接口 + mock/real 数据源切换）
- 工具调用超时与重试机制
- 流式推理过程反馈（thinking 事件）
- 输入安全三级分级（BLOCK/WARN/SAFE）
- 数据库连接池 + WAL 模式
- 结构化日志系统
- 管理员 CLI 工具（admin_cli.py）

### Changed
- system prompt 改为动态模板（注入当前时间）
- 响应格式强制 Markdown（表格、列表、粗体）
- 工具调用审计增强（次数、耗时、错误率统计）

### Fixed
- agent.py tool_calls dict/Object 类型兼容
- api.ts 401 处理区分用户端/管理端登录页
- SSE 断连后 AuthRedirectError 不再误提示"流式中断"
- .env 补全所有缺失配置项
- 移除未使用的 pinia-plugin-persistedstate 依赖

## [1.0.0] — Initial Release

### Core
- LangChain ReAct Agent 自主决策引擎
- DeepSeek LLM 单模型推理
- 5 个工具：FAQ检索、订单查询、退款查询、故障诊断、转人工
- SSE 流式推送（token 流 + 工具状态 + done 事件）
- 滑动窗口记忆 + LLM 长对话摘要
- 基础安全护栏（输入验证、注入检测、限流）
- 工具调用审计日志
- SQLite 持久化（sessions、messages、ratings、tool_audit、rate_limits）
- Vue 3 + Vite + Element Plus 前端
- 满意度评价系统
