"""Database layer — async SQLite with connection pooling and WAL mode.

Uses a single shared aiosqlite connection (safe because aiosqlite runs
SQLite in a background thread). WAL mode enables concurrent reads.
"""

import aiosqlite
import json
import logging
import os
from datetime import datetime

from app.config import DATABASE_PATH

logger = logging.getLogger(__name__)

# Shared connection (initialized on first use)
_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """Get the shared database connection. Creates it on first call."""
    global _db
    if _db is None:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        _db = await aiosqlite.connect(DATABASE_PATH)
        _db.row_factory = aiosqlite.Row
        # Enable WAL mode for better concurrent read performance
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA busy_timeout=5000")
        logger.info(f"Database connected: {DATABASE_PATH} (WAL mode)")
    return _db


async def close_db():
    """Close the shared database connection. Called during app shutdown."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
        logger.info("Database connection closed")


async def init_db():
    """Create all tables."""
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT '新对话',
            user_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            summary TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            intent TEXT,
            source TEXT,
            confidence REAL,
            tools_called TEXT DEFAULT '[]',
            trace TEXT DEFAULT '[]',
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            msg_id TEXT NOT NULL,
            score INTEGER NOT NULL,
            rated_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
        CREATE TABLE IF NOT EXISTS tool_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            msg_id TEXT,
            tool_name TEXT NOT NULL,
            tool_input TEXT DEFAULT '{}',
            tool_output TEXT DEFAULT '{}',
            duration_ms INTEGER DEFAULT 0,
            success INTEGER DEFAULT 1,
            error TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
        CREATE TABLE IF NOT EXISTS rate_limits (
            session_id TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0,
            window_start TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS user_memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'general',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id TEXT PRIMARY KEY,
            profile_data TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    await db.commit()
    logger.info("Database tables initialized")


# ===== Sessions =====

async def create_session_db(session_id: str, user_id: str) -> dict:
    now = datetime.utcnow().isoformat()
    db = await get_db()
    await db.execute(
        "INSERT INTO sessions (id, title, user_id, status, summary, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, "新对话", user_id, "active", "", now, now)
    )
    await db.commit()
    return {"id": session_id, "title": "新对话", "userId": user_id, "status": "active", "createdAt": now, "updatedAt": now}


async def get_sessions_db() -> list:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM sessions ORDER BY updated_at DESC")
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_session_db(session_id: str) -> dict | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_session_db(session_id: str, **kwargs) -> dict | None:
    kwargs["updated_at"] = datetime.utcnow().isoformat()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [session_id]
    db = await get_db()
    await db.execute(f"UPDATE sessions SET {sets} WHERE id = ?", vals)
    await db.commit()
    return await get_session_db(session_id)


# ===== Messages =====

async def add_message_db(msg: dict) -> dict:
    db = await get_db()
    await db.execute(
        "INSERT INTO messages (id, session_id, role, content, intent, source, confidence, tools_called, trace, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (msg["id"], msg["sessionId"], msg["role"], msg["content"],
         msg.get("intent"), msg.get("source"), msg.get("confidence"),
         json.dumps(msg.get("toolsCalled", []), ensure_ascii=False),
         json.dumps(msg.get("trace", []), ensure_ascii=False),
         msg["timestamp"])
    )
    await db.commit()
    return msg


async def get_messages_db(session_id: str) -> list:
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, session_id as sessionId, role, content, intent, source, confidence, tools_called as toolsCalled, trace, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp",
        (session_id,)
    )
    rows = await cursor.fetchall()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["toolsCalled"] = json.loads(d.get("toolsCalled") or "[]")
        except (json.JSONDecodeError, TypeError):
            d["toolsCalled"] = []
        try:
            d["trace"] = json.loads(d.get("trace") or "[]")
        except (json.JSONDecodeError, TypeError):
            d["trace"] = []
        result.append(d)
    return result


async def get_all_messages_db() -> dict:
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, session_id as sessionId, role, content, intent, source, confidence, tools_called as toolsCalled, trace, timestamp FROM messages ORDER BY timestamp"
    )
    rows = await cursor.fetchall()
    result = {}
    for r in rows:
        d = dict(r)
        try:
            d["toolsCalled"] = json.loads(d.get("toolsCalled") or "[]")
        except (json.JSONDecodeError, TypeError):
            d["toolsCalled"] = []
        try:
            d["trace"] = json.loads(d.get("trace") or "[]")
        except (json.JSONDecodeError, TypeError):
            d["trace"] = []
        sid = d["sessionId"]
        if sid not in result:
            result[sid] = []
        result[sid].append(d)
    return result


async def get_message_count_db(session_id: str) -> int:
    db = await get_db()
    cursor = await db.execute("SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,))
    row = await cursor.fetchone()
    return row[0]


# ===== Ratings =====

async def add_rating_db(session_id: str, msg_id: str, score: int) -> dict:
    now = datetime.utcnow().isoformat()
    db = await get_db()
    await db.execute(
        "INSERT INTO ratings (session_id, msg_id, score, rated_at) VALUES (?, ?, ?, ?)",
        (session_id, msg_id, score, now)
    )
    await db.commit()
    return {"sessionId": session_id, "msgId": msg_id, "score": score, "ratedAt": now}


async def get_ratings_db(session_id: str = None) -> list:
    db = await get_db()
    if session_id:
        cursor = await db.execute("SELECT * FROM ratings WHERE session_id = ?", (session_id,))
    else:
        cursor = await db.execute("SELECT * FROM ratings")
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


# ===== Tool Audit =====

async def add_tool_audit(session_id: str, tool_name: str, tool_input: dict,
                          tool_output: dict, duration_ms: int, success: bool,
                          error: str = None, msg_id: str = None) -> dict:
    now = datetime.utcnow().isoformat()
    db = await get_db()
    await db.execute(
        "INSERT INTO tool_audit (session_id, msg_id, tool_name, tool_input, tool_output, duration_ms, success, error, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (session_id, msg_id, tool_name,
         json.dumps(tool_input, ensure_ascii=False),
         json.dumps(tool_output, ensure_ascii=False),
         duration_ms, 1 if success else 0, error, now)
    )
    await db.commit()
    return {"sessionId": session_id, "toolName": tool_name, "durationMs": duration_ms, "success": success}


async def get_tool_audit_db(session_id: str = None, limit: int = 100) -> list:
    db = await get_db()
    if session_id:
        cursor = await db.execute(
            "SELECT * FROM tool_audit WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit)
        )
    else:
        cursor = await db.execute(
            "SELECT * FROM tool_audit ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
    rows = await cursor.fetchall()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["toolInput"] = json.loads(d.get("tool_input") or "{}")
        except (json.JSONDecodeError, TypeError):
            d["toolInput"] = {}
        try:
            d["toolOutput"] = json.loads(d.get("tool_output") or "{}")
        except (json.JSONDecodeError, TypeError):
            d["toolOutput"] = {}
        d["success"] = bool(d.get("success", 0))
        d.pop("tool_input", None)
        d.pop("tool_output", None)
        result.append(d)
    return result


# ===== Rate Limiting =====

async def check_rate_limit(session_id: str, limit: int) -> bool:
    """Return True if request is allowed, False if rate limited."""
    now = datetime.utcnow()
    db = await get_db()
    cursor = await db.execute("SELECT * FROM rate_limits WHERE session_id = ?", (session_id,))
    row = await cursor.fetchone()
    if not row:
        await db.execute(
            "INSERT INTO rate_limits (session_id, count, window_start) VALUES (?, 1, ?)",
            (session_id, now.isoformat())
        )
        await db.commit()
        return True

    window_start = datetime.fromisoformat(row["window_start"])
    if (now - window_start).total_seconds() > 60:
        await db.execute(
            "UPDATE rate_limits SET count = 1, window_start = ? WHERE session_id = ?",
            (now.isoformat(), session_id)
        )
        await db.commit()
        return True

    if row["count"] >= limit:
        return False

    await db.execute(
        "UPDATE rate_limits SET count = count + 1 WHERE session_id = ?",
        (session_id,)
    )
    await db.commit()
    return True
