"""User context — cross-session memory and user profiles.

Provides persistent user-level context that survives across sessions:
- Key facts extracted from conversations (preferences, common issues, etc.)
- Aggregated profile data (issue patterns, satisfaction trends)

This context is injected into the system prompt to personalize agent responses.
"""

import json
import logging
from datetime import datetime

from app.database import get_db

logger = logging.getLogger(__name__)


# ============================================================
# User Memories — key facts extracted from conversations
# ============================================================

async def add_user_memory(user_id: str, content: str, category: str = "general") -> None:
    """Store a key fact about a user.

    Categories: preference, issue_history, account_info, feedback, general
    """
    db = await get_db()
    now = datetime.utcnow().isoformat()
    await db.execute(
        "INSERT INTO user_memories (user_id, content, category, created_at) VALUES (?, ?, ?, ?)",
        (user_id, content, category, now)
    )
    await db.commit()


async def get_user_memories(user_id: str, limit: int = 10) -> list[dict]:
    """Retrieve recent memories for a user."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, content, category, created_at FROM user_memories "
        "WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def extract_memories_from_session(session_id: str, user_id: str) -> int:
    """Extract key facts from a completed session and store as user memories.

    Analyzes the session's messages to extract:
    - Issue types the user encountered
    - Specific orders/refunds discussed
    - Satisfaction signals (ratings)
    - Transfer to human (indicates unresolved issues)

    Returns the number of new memories created.
    """
    db = await get_db()

    # Get session info
    cursor = await db.execute(
        "SELECT status, summary FROM sessions WHERE id = ?", (session_id,)
    )
    session = await cursor.fetchone()
    if not session:
        return 0

    # Get message intents
    cursor = await db.execute(
        "SELECT intent, source, confidence FROM messages WHERE session_id = ? AND role = 'bot'",
        (session_id,)
    )
    bot_messages = await cursor.fetchall()

    count = 0
    intents_seen = set()
    was_transferred = session["status"] == "transferred"

    for msg in bot_messages:
        intent = msg["intent"]
        if intent and intent != "unknown":
            intents_seen.add(intent)

    # Store issue history
    if intents_seen:
        intent_labels = {
            "refund": "退款问题", "order": "订单查询",
            "tech": "技术问题", "faq": "一般咨询", "human": "转人工",
        }
        labels = [intent_labels.get(i, i) for i in intents_seen]
        content = f"用户咨询过：{', '.join(labels)}"
        await add_user_memory(user_id, content, "issue_history")
        count += 1

    # Store transfer signal
    if was_transferred:
        await add_user_memory(user_id, "曾转人工客服（问题可能未完全解决）", "feedback")
        count += 1

    # Store session summary if available
    if session["summary"]:
        summary_short = session["summary"][:200]
        await add_user_memory(user_id, f"历史对话摘要：{summary_short}", "general")
        count += 1

    if count > 0:
        logger.info(f"Extracted {count} memories for user {user_id} from session {session_id}")

    return count


# ============================================================
# User Profiles — aggregated statistics
# ============================================================

async def update_user_profile(user_id: str) -> None:
    """Update aggregated profile data for a user based on all their sessions."""
    db = await get_db()
    now = datetime.utcnow().isoformat()

    # Aggregate session stats
    cursor = await db.execute(
        "SELECT COUNT(*) as total, "
        "SUM(CASE WHEN status = 'transferred' THEN 1 ELSE 0 END) as transferred "
        "FROM sessions WHERE user_id = ?",
        (user_id,)
    )
    stats = await cursor.fetchone()
    total_sessions = stats["total"] or 0
    transferred = stats["transferred"] or 0

    # Get intent distribution from messages
    cursor = await db.execute(
        "SELECT intent, COUNT(*) as cnt FROM messages m "
        "JOIN sessions s ON m.session_id = s.id "
        "WHERE s.user_id = ? AND m.role = 'bot' AND m.intent IS NOT NULL "
        "GROUP BY intent ORDER BY cnt DESC LIMIT 5",
        (user_id,)
    )
    intent_rows = await cursor.fetchall()
    top_intents = {row["intent"]: row["cnt"] for row in intent_rows}

    # Get average rating
    cursor = await db.execute(
        "SELECT AVG(r.score) as avg_score FROM ratings r "
        "JOIN sessions s ON r.session_id = s.id "
        "WHERE s.user_id = ?",
        (user_id,)
    )
    rating_row = await cursor.fetchone()
    avg_rating = round(rating_row["avg_score"], 2) if rating_row["avg_score"] else None

    profile = {
        "total_sessions": total_sessions,
        "transfer_count": transferred,
        "transfer_rate": round(transferred / max(total_sessions, 1), 2),
        "top_intents": top_intents,
        "avg_rating": avg_rating,
        "last_active": now,
    }

    # Upsert profile
    cursor = await db.execute(
        "SELECT user_id FROM user_profiles WHERE user_id = ?", (user_id,)
    )
    existing = await cursor.fetchone()

    if existing:
        await db.execute(
            "UPDATE user_profiles SET profile_data = ?, updated_at = ? WHERE user_id = ?",
            (json.dumps(profile, ensure_ascii=False), now, user_id)
        )
    else:
        await db.execute(
            "INSERT INTO user_profiles (user_id, profile_data, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (user_id, json.dumps(profile, ensure_ascii=False), now, now)
        )
    await db.commit()


async def get_user_profile(user_id: str) -> dict | None:
    """Retrieve the user's aggregated profile."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT profile_data FROM user_profiles WHERE user_id = ?", (user_id,)
    )
    row = await cursor.fetchone()
    if row:
        try:
            return json.loads(row["profile_data"])
        except (json.JSONDecodeError, TypeError):
            return None
    return None


# ============================================================
# Combined context for prompt injection
# ============================================================

async def get_user_context(user_id: str) -> str:
    """Build a context string combining user memories and profile for prompt injection.

    Returns empty string if no context is available (new user, no history).
    """
    if not user_id:
        return ""

    parts = []

    # Profile summary
    profile = await get_user_profile(user_id)
    if profile and profile.get("total_sessions", 0) > 0:
        intent_labels = {
            "refund": "退款", "order": "订单", "tech": "技术",
            "faq": "咨询", "human": "转人工",
        }
        top = profile.get("top_intents", {})
        top_str = ", ".join(
            f"{intent_labels.get(k, k)}({v}次)"
            for k, v in list(top.items())[:3]
        ) if top else "无"
        parts.append(f"历史会话 {profile['total_sessions']} 次，常见问题：{top_str}")
        if profile.get("avg_rating"):
            parts.append(f"平均满意度：{profile['avg_rating']}/5")
        if profile.get("transfer_rate", 0) > 0.3:
            parts.append("注意：该用户转人工频率较高，请尽量详细解答")

    # Recent memories
    memories = await get_user_memories(user_id, limit=5)
    if memories:
        mem_lines = [m["content"] for m in memories]
        parts.append("用户历史记录：" + "；".join(mem_lines))

    if not parts:
        return ""

    return "\n".join(parts)
