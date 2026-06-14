"""Guardrails — input validation, content safety, and rate limiting."""

import re
from app.config import MAX_INPUT_LENGTH

# Basic patterns for potentially harmful content
UNSAFE_PATTERNS = [
    r"(?i)(bomb|explosive|weapon|hack\s+into|steal|fraud)",
    r"(?i)(自杀|自残|暴力|恐怖)",
]

# Patterns that indicate the user might be trying prompt injection
INJECTION_PATTERNS = [
    r"(?i)(ignore\s+(previous|above|all)\s+instructions)",
    r"(?i)(you\s+are\s+now\s+)",
    r"(?i)(system\s*:\s*)",
    r"(?i)(<\|im_start\|>|<\|im_end\|>)",
]


def validate_input(text: str) -> tuple[bool, str]:
    """Validate user input. Returns (is_valid, reason)."""
    if not text or not text.strip():
        return False, "消息不能为空"

    if len(text) > MAX_INPUT_LENGTH:
        return False, f"消息长度不能超过 {MAX_INPUT_LENGTH} 字符"

    # Check for prompt injection
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text):
            return False, "输入包含不允许的内容"

    return True, ""


def check_content_safety(text: str) -> tuple[bool, str]:
    """Check if content is safe. Returns (is_safe, reason)."""
    for pattern in UNSAFE_PATTERNS:
        if re.search(pattern, text):
            return False, "内容涉及敏感话题，已转人工客服处理"
    return True, ""


def sanitize_output(text: str) -> str:
    """Sanitize agent output before sending to user."""
    # Remove any leaked system prompts (matched pair)
    text = re.sub(r"System prompt:.*?(?=\n|$)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<\|im_start\|>.*?<\|im_end\|>", "", text, flags=re.DOTALL)
    # Remove standalone special tokens
    text = re.sub(r"<\|im_start\|>.*?(?=\n|$)", "", text)
    text = re.sub(r"<\|im_end\|>", "", text)
    return text.strip()
