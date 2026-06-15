"""FastAPI application — Smart Customer Service Agent API.

Endpoints:
- POST /api/sessions          — Create session
- GET  /api/sessions          — List sessions
- GET  /api/sessions/:id      — Get session detail
- PATCH /api/sessions/:id     — Update session
- POST /api/chat              — Chat (non-streaming)
- POST /api/chat/stream       — Chat (SSE streaming)
- GET  /api/sessions/:id/messages — Get session messages
- POST /api/ratings           — Submit rating
- GET  /api/ratings           — List ratings
- GET  /api/analytics         — Dashboard analytics
- GET  /api/tool-audit        — Tool call audit log
- GET  /api/health            — Health check
"""

import uuid
import json
import time
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.config import CORS_ORIGINS, RATE_LIMIT_PER_MIN, SUMMARY_THRESHOLD
from app.models import ChatRequest, SessionCreate, SessionUpdate, RatingCreate
from app.database import (
    init_db, create_session_db, get_sessions_db, get_session_db,
    update_session_db, add_message_db, get_messages_db, get_all_messages_db,
    add_rating_db, get_ratings_db, add_tool_audit, get_tool_audit_db,
    check_rate_limit,
)
from app.agent import agent_chat, agent_chat_stream
from app.guardrails import validate_input, check_content_safety, sanitize_output
from app.memory import summarize_history
from app.knowledge_base import FAQ_DATA
from app.vector_store import init_vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_vector_store(FAQ_DATA)
    yield

app = FastAPI(
    title="智能客服 Agent API",
    version="2.0.0",
    description="LangChain ReAct Agent + SSE Streaming + Memory + Guardrails + Audit",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Health =====

@app.get("/api/health")
async def health_check():
    from app.config import DEEPSEEK_API_KEY
    api_key_configured = bool(DEEPSEEK_API_KEY and DEEPSEEK_API_KEY != "your-api-key-here")
    return {
        "status": "ok",
        "service": "smart-cs-agent",
        "version": "2.0.0",
        "apiKeyConfigured": api_key_configured,
    }


# ===== Sessions =====

@app.post("/api/sessions")
async def create_session(req: SessionCreate = None):
    session_id = f"sess_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:6]}"
    user_id = (req.userId if req else None) or f"user_{uuid.uuid4().hex[:6]}"
    session = await create_session_db(session_id, user_id)
    return session


@app.get("/api/sessions")
async def list_sessions():
    return await get_sessions_db()


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    session = await get_session_db(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session


@app.patch("/api/sessions/{session_id}")
async def update_session(session_id: str, updates: SessionUpdate):
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(400, "No fields to update")
    session = await update_session_db(session_id, **update_data)
    if not session:
        raise HTTPException(404, "Session not found")
    return session


@app.post("/api/sessions/{session_id}/close")
async def close_session(session_id: str):
    session = await update_session_db(session_id, status="closed")
    if not session:
        raise HTTPException(404, "Session not found")
    return session


# ===== Chat (Non-streaming) =====

@app.post("/api/chat")
async def chat(req: ChatRequest):
    # Validate session
    session = await get_session_db(req.sessionId)
    if not session:
        raise HTTPException(404, "Session not found")

    if session.get("status") == "transferred":
        raise HTTPException(400, "对话已转人工，AI 回复已暂停")

    if session.get("status") == "closed":
        raise HTTPException(400, "对话已结束，请创建新会话")

    # Input validation
    is_valid, reason = validate_input(req.message)
    if not is_valid:
        raise HTTPException(400, reason)

    # Content safety
    is_safe, safety_reason = check_content_safety(req.message)
    if not is_safe:
        # Auto-transfer to human
        await update_session_db(req.sessionId, status="transferred")
        return {
            "userMessage": _make_user_msg(req.sessionId, req.message),
            "botMessage": _make_bot_msg(req.sessionId, safety_reason, "human", "human", 0.1),
        }

    # Rate limiting
    if not await check_rate_limit(req.sessionId, RATE_LIMIT_PER_MIN):
        raise HTTPException(429, "请求过于频繁，请稍后再试")

    # Get history
    history = await get_messages_db(req.sessionId)
    session_summary = session.get("summary", "")

    # Memory management: summarize if history is too long
    if len(history) > SUMMARY_THRESHOLD and not session_summary:
        summary = await summarize_history(history)
        if summary:
            await update_session_db(req.sessionId, summary=summary)

    # Add user message
    user_msg = _make_user_msg(req.sessionId, req.message)
    await add_message_db(user_msg)

    # Update session title from first user message
    user_count = len([m for m in history if m["role"] == "user"])
    if user_count == 0:
        title = req.message[:20] + ("..." if len(req.message) > 20 else "")
        await update_session_db(req.sessionId, title=title)

    # Run Agent
    response = await agent_chat(req.message, req.sessionId, history, session_summary)

    # Add bot message
    bot_msg = _make_bot_msg(
        req.sessionId, response["content"],
        response.get("intent"), response.get("source"), response.get("confidence"),
        response.get("tools_called", []), response.get("trace", []),
    )
    await add_message_db(bot_msg)

    # Log tool calls to audit (only tool_result, not tool_call — avoids duplicates)
    for step in response.get("trace", []):
        if step.get("type") == "tool_result":
            await add_tool_audit(
                session_id=req.sessionId, tool_name=step.get("tool", ""),
                tool_input={}, tool_output=step.get("output", {}),
                duration_ms=step.get("duration_ms", 0), success=True, msg_id=bot_msg["id"],
            )

    # Auto-transfer if needed
    if response.get("need_human") or response.get("source") == "human":
        if session.get("status") == "active":
            await update_session_db(req.sessionId, status="transferred")

    return {"userMessage": user_msg, "botMessage": bot_msg}


# ===== Chat (SSE Streaming) =====

@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    # Validate session
    session = await get_session_db(req.sessionId)
    if not session:
        raise HTTPException(404, "Session not found")

    if session.get("status") == "transferred":
        raise HTTPException(400, "对话已转人工，AI 回复已暂停")

    if session.get("status") == "closed":
        raise HTTPException(400, "对话已结束，请创建新会话")

    # Input validation
    is_valid, reason = validate_input(req.message)
    if not is_valid:
        raise HTTPException(400, reason)

    # Content safety
    is_safe, safety_reason = check_content_safety(req.message)
    if not is_safe:
        await update_session_db(req.sessionId, status="transferred")
        async def unsafe_stream():
            yield f"data: {json.dumps({'type': 'error', 'content': safety_reason}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'intent': 'human', 'source': 'human', 'confidence': 0.1, 'need_human': True, 'tools_called': [], 'trace': []}, ensure_ascii=False)}\n\n"
        return StreamingResponse(unsafe_stream(), media_type="text/event-stream")

    # Rate limiting
    if not await check_rate_limit(req.sessionId, RATE_LIMIT_PER_MIN):
        raise HTTPException(429, "请求过于频繁，请稍后再试")

    # Get history
    history = await get_messages_db(req.sessionId)
    session_summary = session.get("summary", "")

    # Memory management
    if len(history) > SUMMARY_THRESHOLD and not session_summary:
        summary = await summarize_history(history)
        if summary:
            await update_session_db(req.sessionId, summary=summary)

    # Add user message
    user_msg = _make_user_msg(req.sessionId, req.message)
    await add_message_db(user_msg)

    # Update session title
    user_count = len([m for m in history if m["role"] == "user"])
    if user_count == 0:
        title = req.message[:20] + ("..." if len(req.message) > 20 else "")
        await update_session_db(req.sessionId, title=title)

    async def event_stream():
        full_content = ""
        metadata = {}
        tool_traces = []

        async for event in agent_chat_stream(req.message, req.sessionId, history, session_summary):
            if event["type"] == "token":
                full_content += event["content"]
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            elif event["type"] == "tool_start":
                tool_traces.append({"type": "tool_call", "tool": event["tool"], "input": event["input"]})
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            elif event["type"] == "tool_end":
                tool_traces.append({
                    "type": "tool_result", "tool": event["tool"],
                    "output": event["output"], "duration_ms": event["duration_ms"],
                })
                # Log to audit
                await add_tool_audit(
                    session_id=req.sessionId, tool_name=event["tool"],
                    tool_input={}, tool_output=event["output"],
                    duration_ms=event["duration_ms"], success=True,
                )
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            elif event["type"] == "done":
                metadata = event

            elif event["type"] == "error":
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        # Save bot message to DB
        full_content = sanitize_output(full_content)
        if not full_content:
            full_content = "抱歉，我无法生成回复，请稍后重试。"

        bot_msg = _make_bot_msg(
            req.sessionId, full_content,
            metadata.get("intent", "unknown"),
            metadata.get("source", "ai"),
            metadata.get("confidence", 0.5),
            metadata.get("tools_called", []),
            tool_traces,
        )
        await add_message_db(bot_msg)

        # Auto-transfer if needed
        if metadata.get("need_human") or metadata.get("source") == "human":
            current = await get_session_db(req.sessionId)
            if current and current.get("status") == "active":
                await update_session_db(req.sessionId, status="transferred")

        yield f"data: {json.dumps({'type': 'done', **metadata}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ===== Messages =====

@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    return await get_messages_db(session_id)


# ===== Ratings =====

@app.post("/api/ratings")
async def create_rating(req: RatingCreate):
    if req.score < 1 or req.score > 5:
        raise HTTPException(400, "Score must be 1-5")
    return await add_rating_db(req.sessionId, req.msgId, req.score)


@app.get("/api/ratings")
async def list_ratings(session_id: str = None):
    return await get_ratings_db(session_id)


# ===== Tool Audit =====

@app.get("/api/tool-audit")
async def get_tool_audit(session_id: str = None, limit: int = 100):
    return await get_tool_audit_db(session_id, limit)


# ===== Analytics =====

@app.get("/api/analytics")
async def get_analytics():
    sessions = await get_sessions_db()
    all_msgs_raw = await get_all_messages_db()
    all_ratings = await get_ratings_db()

    total_messages = []
    for sid, msgs in all_msgs_raw.items():
        total_messages.extend(msgs)

    bot_messages = [m for m in total_messages if m["role"] == "bot"]

    # Intent distribution
    intent_counts = {}
    for m in bot_messages:
        intent = m.get("intent")
        if intent:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1

    # Source distribution
    source_counts = {"ai": 0, "faq": 0, "human": 0, "system": 0}
    for m in bot_messages:
        source = m.get("source")
        if source in source_counts:
            source_counts[source] += 1

    # Status distribution
    status_counts = {"active": 0, "transferred": 0, "closed": 0}
    for s in sessions:
        st = s.get("status", "active")
        if st in status_counts:
            status_counts[st] += 1

    # Satisfaction
    rating_values = [r["score"] for r in all_ratings]
    avg_rating = sum(rating_values) / len(rating_values) if rating_values else 0
    rating_dist = {str(i): 0 for i in range(1, 6)}
    for r in rating_values:
        rating_dist[str(r)] = rating_dist.get(str(r), 0) + 1

    # Intent resolution rate
    intent_resolution = {}
    for m in bot_messages:
        intent = m.get("intent")
        source = m.get("source")
        if intent and intent != "unknown":
            if intent not in intent_resolution:
                intent_resolution[intent] = {"total": 0, "resolved": 0}
            intent_resolution[intent]["total"] += 1
            if source in ("faq", "ai", "system"):
                intent_resolution[intent]["resolved"] += 1

    # Transfer rate
    transfer_rate = (status_counts["transferred"] / len(sessions) * 100) if sessions else 0

    # Tool call stats
    tool_audit = await get_tool_audit_db(limit=1000)
    tool_stats = {}
    for entry in tool_audit:
        name = entry.get("tool_name", "")
        if name not in tool_stats:
            tool_stats[name] = {"count": 0, "total_ms": 0, "errors": 0}
        tool_stats[name]["count"] += 1
        tool_stats[name]["total_ms"] += entry.get("duration_ms", 0)
        if not entry.get("success", True):
            tool_stats[name]["errors"] += 1

    return {
        "totalSessions": len(sessions),
        "totalMessages": len(total_messages),
        "intentCounts": intent_counts,
        "sourceCounts": source_counts,
        "statusCounts": status_counts,
        "avgRating": round(avg_rating, 1),
        "ratingDist": rating_dist,
        "ratingCount": len(rating_values),
        "intentResolution": intent_resolution,
        "transferRate": round(transfer_rate, 1),
        "toolStats": tool_stats,
        "sessions": sessions,
        "allMsgs": all_msgs_raw,
    }


# ===== Helpers =====

def _make_user_msg(session_id: str, content: str) -> dict:
    return {
        "id": f"msg_{uuid.uuid4().hex[:12]}",
        "sessionId": session_id,
        "role": "user",
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
    }


def _make_bot_msg(session_id: str, content: str, intent: str = None,
                   source: str = None, confidence: float = None,
                   tools_called: list = None, trace: list = None) -> dict:
    return {
        "id": f"msg_{uuid.uuid4().hex[:12]}",
        "sessionId": session_id,
        "role": "bot",
        "content": content,
        "intent": intent,
        "source": source,
        "confidence": confidence,
        "toolsCalled": tools_called or [],
        "trace": trace or [],
        "timestamp": datetime.utcnow().isoformat(),
    }
