"""LangChain ReAct Agent — real intelligent agent with autonomous tool calling.

The LLM decides: which tools to call, in what order, whether to chain multiple tools,
whether to ask for more info, or whether to transfer to human.

Features:
- Tool Calling: 5 tools the agent can autonomously invoke
- Streaming: SSE-compatible streaming via astream_events
- Memory: Sliding window with LLM summarization
- Guardrails: Input validation, content safety, max iterations
- Observability: Full reasoning trace (tool calls, inputs, outputs)
- Error Recovery: Fallback strategies on tool/API failure
"""

import json
import time
import asyncio
from datetime import datetime
from typing import AsyncGenerator

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain.agents import create_agent

from app.config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    MAX_ITERATIONS, TOOL_TIMEOUT_SEC,
)
from app.knowledge_base import FAQ_DATA
from app.guardrails import sanitize_output
from app.memory import build_chat_history, summarize_history
from app.vector_store import search_similar as vector_search, is_initialized as vector_store_ready
from app.services import order_service, refund_service, troubleshoot_service


# ============================================================
# Tool Definitions — capabilities the Agent can invoke
# ============================================================

# Mock data moved to services/mock_service.py — tools call through service layer


@tool
async def search_faq(query: str) -> str:
    """Search the FAQ knowledge base for answers to common questions.
    Use this when the user asks about policies, procedures, or common issues like
    refunds, orders, coupons, account issues, etc.

    Args:
        query: The user's question or keywords to search for.
    """
    # --- Primary: Vector semantic search (RAG) ---
    if vector_store_ready():
        results = await vector_search(query, top_k=3)
        if results:
            best = results[0]
            # Threshold: cosine similarity > 0.3 means reasonably related
            if best["similarity_score"] > 0.3:
                return json.dumps({
                    "found": True,
                    "question": best["question"],
                    "answer": best["answer"],
                    "category": best["intent"],
                    "similarity_score": round(best["similarity_score"], 4),
                }, ensure_ascii=False)

    # --- Fallback: Keyword-based search ---
    best = None
    best_score = 0
    for faq in FAQ_DATA:
        score = 0
        for kw in faq["keywords"]:
            if kw in query:
                score += len(kw) * 2
        for char in query:
            if char in faq["question"]:
                score += 0.5
        if score > best_score:
            best_score = score
            best = faq

    if best and best_score > 1:
        return json.dumps({
            "found": True, "question": best["question"],
            "answer": best["answer"], "category": best["intent"],
            "similarity_score": min(best_score / 20.0, 1.0),  # normalized heuristic score
        }, ensure_ascii=False)
    return json.dumps({"found": False, "message": "未找到匹配的FAQ，建议转人工客服"}, ensure_ascii=False)


@tool
async def query_order(order_id: str = "") -> str:
    """Query order status and logistics information.
    Use this when the user wants to check their order status, track a package,
    or know delivery details.

    Args:
        order_id: The order ID to query. If empty, return general guidance.
    """
    if not order_id:
        return json.dumps({
            "hint": True,
            "message": "请提供订单号以查询订单状态。您可以在APP「我的订单」中找到订单号，格式如 ORD20260610001"
        }, ensure_ascii=False)

    try:
        order = await asyncio.wait_for(
            order_service.query_order(order_id),
            timeout=TOOL_TIMEOUT_SEC,
        )
    except asyncio.TimeoutError:
        return json.dumps({
            "found": False,
            "message": f"查询订单 {order_id} 超时（>{TOOL_TIMEOUT_SEC}s），请稍后重试或转人工客服。"
        }, ensure_ascii=False)
    if order:
        return json.dumps({
            "found": True, "order_id": order_id, "status": order["status"],
            "product": order["product"], "amount": order["amount"],
            "logistics": order["logistics"], "ordered_at": order["ordered_at"],
        }, ensure_ascii=False)

    return json.dumps({
        "found": False,
        "message": f"未找到订单 {order_id}，请确认订单号是否正确。可尝试的示例订单号：ORD20260610001, ORD20260608002"
    }, ensure_ascii=False)


@tool
async def check_refund(refund_id: str = "", order_id: str = "") -> str:
    """Check refund eligibility, status, and timeline.
    Use this when the user asks about refund progress, whether they can get a refund,
    or why a refund was rejected.

    Args:
        refund_id: The refund ID to check (optional).
        order_id: The order ID to check refund for (optional).
    """
    if refund_id:
        try:
            ref = await asyncio.wait_for(
                refund_service.check_refund_by_id(refund_id),
                timeout=TOOL_TIMEOUT_SEC,
            )
        except asyncio.TimeoutError:
            return json.dumps({
                "found": False,
                "message": f"查询退款 {refund_id} 超时（>{TOOL_TIMEOUT_SEC}s），请稍后重试或转人工客服。"
            }, ensure_ascii=False)
        if ref:
            return json.dumps({
                "found": True, "refund_id": refund_id, "order_id": ref["order_id"],
                "status": ref["status"], "amount": ref["amount"],
                "reason": ref["reason"], "eta": ref["eta"],
            }, ensure_ascii=False)

    if order_id:
        try:
            result = await asyncio.wait_for(
                refund_service.check_refund_by_order(order_id),
                timeout=TOOL_TIMEOUT_SEC,
            )
        except asyncio.TimeoutError:
            return json.dumps({
                "eligible": False,
                "message": f"查询订单 {order_id} 退款信息超时（>{TOOL_TIMEOUT_SEC}s），请稍后重试或转人工客服。"
            }, ensure_ascii=False)
        if result and result.get("eligible"):
            return json.dumps(result, ensure_ascii=False)
        return json.dumps({
            "eligible": False,
            "message": f"未找到订单 {order_id}，请确认订单号。示例订单号：ORD20260610001"
        }, ensure_ascii=False)

    return json.dumps({
        "hint": True,
        "message": "请提供退款单号或订单号以查询退款状态。示例：退款单号 REF001、REF002，订单号 ORD20260610001"
    }, ensure_ascii=False)


@tool
async def troubleshoot(issue_type: str, description: str = "") -> str:
    """Diagnose technical issues and provide solutions.
    Use this when the user reports app crashes, login problems, payment failures,
    or other technical difficulties.

    Args:
        issue_type: Type of issue: crash, login, payment, slow, other.
        description: Detailed description of the problem.
    """
    try:
        result = await asyncio.wait_for(
            troubleshoot_service.diagnose(issue_type, description),
            timeout=TOOL_TIMEOUT_SEC,
        )
    except asyncio.TimeoutError:
        return json.dumps({
            "found": False,
            "issue_type": issue_type,
            "message": f"故障诊断超时（>{TOOL_TIMEOUT_SEC}s），请稍后重试或转人工客服。",
        }, ensure_ascii=False)
    return json.dumps(result, ensure_ascii=False)


@tool
def transfer_to_human(reason: str = "") -> str:
    """Transfer the conversation to a human customer service agent.
    Use this when: the user explicitly requests human help, the issue is beyond
    automated handling, the user is dissatisfied with AI responses, or complex
    complaints need human judgment.

    Args:
        reason: The reason for transferring to human agent.
    """
    return json.dumps({
        "transferred": True, "reason": reason or "用户请求转人工",
        "wait_time": "预计2-3分钟", "working_hours": "9:00-22:00",
        "message": "正在为您转接人工客服，请稍候...",
    }, ensure_ascii=False)


ALL_TOOLS = [search_faq, query_order, check_refund, troubleshoot, transfer_to_human]


# ============================================================
# Agent Construction — ReAct Agent with Tool Calling
# ============================================================

SYSTEM_PROMPT = """你是一个专业的智能客服Agent，名叫「小智」。你可以自主决策使用多种工具来帮助用户解决问题。

## 你的能力
你可以自主决定使用哪些工具来解决问题，也可以组合使用多个工具。不要猜测答案——先用工具获取信息，再回答用户。

## 可用工具
- search_faq: 搜索FAQ知识库，获取常见问题的标准答案
- query_order: 查询订单状态和物流信息（需要订单号）
- check_refund: 查询退款资格和退款进度（需要退款单号或订单号）
- troubleshoot: 诊断技术问题并提供解决方案（需要问题类型）
- transfer_to_human: 转接人工客服（当问题超出你的处理范围时）

## 决策规则
1. 用户问退款相关问题 → 先用 search_faq 查知识库，再用 check_refund 查具体退款状态
2. 用户问订单相关问题 → 先用 search_faq 查知识库，再用 query_order 查具体订单
3. 用户报技术问题 → 先用 troubleshoot 诊断，提供解决方案
4. 用户明确要求转人工 → 直接调用 transfer_to_human
5. 用户问题复杂或你无法解决 → 主动调用 transfer_to_human 并说明原因
6. 如果工具返回的信息不够，可以追问用户获取更多信息（如订单号）

## 回答要求
- 基于工具返回的数据回答，不要编造信息
- 用简洁友好的中文回复
- 如果需要用户补充信息（如订单号），明确告知
- 在回答末尾标注信息来源格式：[知识库] / [系统查询] / [人工客服]
"""

llm = ChatOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
    model=DEEPSEEK_MODEL,
    temperature=0.2,
    max_tokens=1024,
    streaming=True,  # Enable streaming for SSE
)

react_agent = create_agent(
    model=llm,
    tools=ALL_TOOLS,
    system_prompt=SYSTEM_PROMPT,
)


# ============================================================
# Metadata extraction from agent execution
# ============================================================

def _extract_metadata(messages: list) -> dict:
    """Extract intent, source, confidence, trace from agent messages."""
    intent = "unknown"
    source = "ai"
    confidence = 0.7
    need_human = False
    tools_called = []
    trace = []

    for msg in messages:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_name = tc.get("name", "")
                tool_args = tc.get("args", {})
                tools_called.append(tool_name)
                trace.append({
                    "type": "tool_call",
                    "tool": tool_name,
                    "input": tool_args,
                })

                if tool_name == "check_refund":
                    intent = "refund"
                elif tool_name == "query_order":
                    intent = "order"
                elif tool_name == "troubleshoot":
                    intent = "tech"
                elif tool_name == "transfer_to_human":
                    intent = "human"
                    need_human = True
                elif tool_name == "search_faq":
                    if intent == "unknown":
                        intent = "faq"

                if tool_name == "search_faq":
                    source = "faq"
                    confidence = 0.7  # will be updated with actual similarity_score from response
                elif tool_name in ("query_order", "check_refund"):
                    source = "system"
                    confidence = 0.95
                elif tool_name == "transfer_to_human":
                    source = "human"

        # Tool response messages
        if hasattr(msg, 'name') and hasattr(msg, 'content'):
            try:
                output_data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
            except (json.JSONDecodeError, TypeError):
                output_data = msg.content
            trace.append({
                "type": "tool_result",
                "tool": getattr(msg, 'name', ''),
                "output": output_data,
            })

            # Extract similarity_score from search_faq response for dynamic confidence
            tool_name_resp = getattr(msg, 'name', '')
            if tool_name_resp == "search_faq" and isinstance(output_data, dict):
                sim_score = output_data.get("similarity_score")
                if sim_score is not None and isinstance(sim_score, (int, float)):
                    confidence = max(0.5, min(float(sim_score), 1.0))

    if len(tools_called) > 1:
        confidence = min(confidence + 0.05, 1.0)

    # Add reasoning step
    if tools_called:
        trace.insert(0, {
            "type": "reasoning",
            "thought": f"Agent 决定调用工具：{', '.join(tools_called)}",
        })

    return {
        "intent": intent,
        "source": source,
        "confidence": confidence,
        "need_human": need_human,
        "tools_called": tools_called,
        "trace": trace,
    }


# ============================================================
# Non-streaming chat (for backward compat)
# ============================================================

async def agent_chat(user_input: str, session_id: str = None,
                     history: list[dict] = None, session_summary: str = "") -> dict:
    """Run the ReAct Agent and return full result."""
    chat_history = build_chat_history(history or [], session_summary)
    input_messages = chat_history + [HumanMessage(content=user_input)]

    try:
        result = await react_agent.ainvoke(
            {"messages": input_messages},
            config={"recursion_limit": MAX_ITERATIONS},
        )

        output_messages = result.get("messages", [])
        final_content = ""
        for msg in reversed(output_messages):
            if isinstance(msg, AIMessage) and msg.content and not getattr(msg, 'tool_calls', None):
                final_content = msg.content
                break
            elif isinstance(msg, AIMessage) and msg.content:
                final_content = msg.content
                break

        if not final_content:
            final_content = "抱歉，我遇到了一些问题，请稍后重试或转人工客服。"

        final_content = sanitize_output(final_content)
        metadata = _extract_metadata(output_messages)

        return {
            "content": final_content,
            "intent": metadata["intent"],
            "source": metadata["source"],
            "confidence": metadata["confidence"],
            "need_human": metadata["need_human"],
            "tools_called": metadata["tools_called"],
            "trace": metadata["trace"],
        }

    except Exception as e:
        error_msg = str(e)
        # Specific handling for auth errors
        if "Authentication" in error_msg or "401" in error_msg or "api key" in error_msg.lower():
            return {
                "content": "⚠️ AI 服务认证失败，请检查 API Key 配置。当前仍可使用知识库检索和系统查询功能。",
                "intent": "unknown", "source": "ai", "confidence": 0.0,
                "need_human": True, "tools_called": [], "trace": [],
            }
        # Fallback: simple LLM call
        try:
            from langchain_core.prompts import ChatPromptTemplate
            simple_prompt = ChatPromptTemplate.from_messages([
                ("system", "你是智能客服助手，请简洁回答用户问题。如果无法处理，建议用户转人工客服。"),
                ("human", "{input}")
            ])
            chain = simple_prompt | llm
            fallback_result = await chain.ainvoke({"input": user_input})
            return {
                "content": sanitize_output(fallback_result.content),
                "intent": "unknown", "source": "ai", "confidence": 0.3,
                "need_human": True, "tools_called": [], "trace": [],
            }
        except Exception:
            return {
                "content": "抱歉，系统暂时无法响应。请稍后重试或联系人工客服。",
                "intent": "unknown", "source": "ai", "confidence": 0.0,
                "need_human": True, "tools_called": [], "trace": [],
            }


# ============================================================
# Streaming chat — SSE via astream_events
# ============================================================

async def agent_chat_stream(user_input: str, session_id: str = None,
                             history: list[dict] = None,
                             session_summary: str = "") -> AsyncGenerator[dict, None]:
    """Stream the ReAct Agent execution via astream_events.

    Yields event dicts:
    - {"type": "token", "content": "..."} — LLM token stream
    - {"type": "tool_start", "tool": "...", "input": {...}} — Tool call started
    - {"type": "tool_end", "tool": "...", "output": {...}, "duration_ms": N} — Tool call completed
    - {"type": "done", "intent": "...", "source": "...", ...} — Agent execution complete
    - {"type": "error", "content": "..."} — Error occurred
    """
    chat_history = build_chat_history(history or [], session_summary)
    input_messages = chat_history + [HumanMessage(content=user_input)]

    tools_called = []
    trace = []
    tool_start_times = {}

    try:
        async for event in react_agent.astream_events(
            {"messages": input_messages},
            version="v2",
            config={"recursion_limit": MAX_ITERATIONS},
        ):
            kind = event.get("event", "")

            # LLM token stream
            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    token = chunk.content if isinstance(chunk.content, str) else ""
                    if token:
                        yield {"type": "token", "content": token}

            # Tool call started
            elif kind == "on_tool_start":
                tool_name = event.get("name", "")
                tool_input = event.get("data", {}).get("input", {})
                tools_called.append(tool_name)
                tool_start_times[tool_name] = time.time()
                trace.append({"type": "tool_call", "tool": tool_name, "input": tool_input})
                yield {"type": "tool_start", "tool": tool_name, "input": tool_input}

            # Tool call completed
            elif kind == "on_tool_end":
                tool_name = event.get("name", "")
                tool_output = event.get("data", {}).get("output", {})
                start = tool_start_times.pop(tool_name, time.time())
                duration = int((time.time() - start) * 1000)

                # Parse tool output
                if isinstance(tool_output, str):
                    try:
                        tool_output = json.loads(tool_output)
                    except (json.JSONDecodeError, TypeError):
                        pass

                trace.append({"type": "tool_result", "tool": tool_name, "output": tool_output, "duration_ms": duration})
                yield {"type": "tool_end", "tool": tool_name, "output": tool_output, "duration_ms": duration}

            # LLM call completed (final)
            elif kind == "on_chat_model_end":
                pass  # We handle streaming tokens above

        # Extract metadata
        metadata = _extract_metadata_from_trace(tools_called, trace)

        yield {
            "type": "done",
            "intent": metadata["intent"],
            "source": metadata["source"],
            "confidence": metadata["confidence"],
            "need_human": metadata["need_human"],
            "tools_called": tools_called,
            "trace": trace,
        }

    except Exception as e:
        yield {
            "type": "error",
            "content": f"Agent 执行出错：{str(e)}",
        }


def _extract_metadata_from_trace(tools_called: list, trace: list) -> dict:
    """Extract metadata from the accumulated trace."""
    intent = "unknown"
    source = "ai"
    confidence = 0.7
    need_human = False

    for tool_name in tools_called:
        if tool_name == "check_refund":
            intent = "refund"
        elif tool_name == "query_order":
            intent = "order"
        elif tool_name == "troubleshoot":
            intent = "tech"
        elif tool_name == "transfer_to_human":
            intent = "human"
            need_human = True
        elif tool_name == "search_faq":
            if intent == "unknown":
                intent = "faq"

        if tool_name == "search_faq":
            source = "faq"
            confidence = 0.7  # will be updated from trace if similarity_score available
        elif tool_name in ("query_order", "check_refund"):
            source = "system"
            confidence = 0.95
        elif tool_name == "transfer_to_human":
            source = "human"

    # Extract similarity_score from search_faq trace results for dynamic confidence
    for entry in trace:
        if entry.get("type") == "tool_result" and entry.get("tool") == "search_faq":
            output = entry.get("output", {})
            if isinstance(output, dict):
                sim_score = output.get("similarity_score")
                if sim_score is not None and isinstance(sim_score, (int, float)):
                    confidence = max(0.5, min(float(sim_score), 1.0))

    if len(tools_called) > 1:
        confidence = min(confidence + 0.05, 1.0)

    if not tools_called:
        source = "ai"
        confidence = 0.6

    return {
        "intent": intent,
        "source": source,
        "confidence": confidence,
        "need_human": need_human,
    }


# Backward-compatible alias
chat_pipeline = agent_chat
