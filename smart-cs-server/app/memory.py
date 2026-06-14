"""Conversation memory management — sliding window with summarization."""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, MEMORY_WINDOW, SUMMARY_THRESHOLD


# Use a lighter model for summarization to save tokens
_summary_llm = ChatOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
    model=DEEPSEEK_MODEL,
    temperature=0,
    max_tokens=256,
)

SUMMARY_PROMPT = """请将以下客服对话历史总结为简洁的要点，保留关键信息（用户意图、已采取的行动、待解决的问题）：

{conversation}

总结："""


def build_chat_history(history: list[dict], session_summary: str = "") -> list:
    """Build LangChain message list from DB history with memory management.

    Strategy:
    - If history <= MEMORY_WINDOW: use all messages
    - If history > SUMMARY_THRESHOLD: prepend summary, use last MEMORY_WINDOW messages
    """
    if not history:
        return []

    messages = []

    # If we have a prior summary, inject it as system context
    if session_summary:
        messages.append(SystemMessage(content=f"之前的对话摘要：{session_summary}"))

    # Use the most recent messages within the window
    recent = history[-MEMORY_WINDOW:] if len(history) > MEMORY_WINDOW else history

    for msg in recent:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "bot":
            messages.append(AIMessage(content=msg["content"]))

    return messages


async def summarize_history(history: list[dict]) -> str:
    """Summarize older conversation history using LLM."""
    if len(history) <= SUMMARY_THRESHOLD:
        return ""

    # Take the older part (everything beyond the window)
    older = history[:-MEMORY_WINDOW]
    if not older:
        return ""

    # Format for summarization
    conv_text = ""
    for msg in older:
        role = "用户" if msg["role"] == "user" else "客服"
        conv_text += f"{role}：{msg['content']}\n"

    try:
        prompt = ChatPromptTemplate.from_template(SUMMARY_PROMPT)
        chain = prompt | _summary_llm
        result = await chain.ainvoke({"conversation": conv_text})
        return result.content
    except Exception:
        # Fallback: simple concatenation summary
        return "；".join([f"用户问：{m['content'][:30]}" for m in older if m["role"] == "user"][:5])
