"""Guardrails — input validation, content safety, and output sanitization.

Three-tier severity system:
- BLOCK: reject the request immediately (injection, dangerous content)
- WARN: log and allow, but flag for review (borderline patterns)
- SAFE: no issues detected
"""

import logging
import re
from app.config import MAX_INPUT_LENGTH

logger = logging.getLogger(__name__)

# ============================================================
# Prompt injection patterns — BLOCK level
# ============================================================

INJECTION_PATTERNS_BLOCK = [
    # English injection attacks
    (r"(?i)ignore\s+(previous|above|all|prior)\s+instructions", "en_ignore_instructions"),
    (r"(?i)(you\s+are\s+now|act\s+as\s+if|pretend\s+you\s+are)", "en_role_hijack"),
    (r"(?i)disregard\s+(all|previous|your)\s+(rules|instructions|guidelines)", "en_disregard_rules"),
    (r"(?i)reveal\s+(your\s+)?system\s+prompt", "en_reveal_prompt"),
    (r"(?i)what\s+(are|were)\s+your\s+(original\s+)?instructions", "en_ask_instructions"),
    # Special tokens
    (r"<\|im_start\|>|<\|im_end\|>", "special_tokens"),
    (r"<\/?system>|<\/?assistant>|<\/?user>", "chat_ml_tokens"),
    # Chinese injection attacks
    (r"忽略(之前|以上|所有|先前)(的)?(指令|指示|规则|设定)", "zh_ignore_instructions"),
    (r"(你现在是|请扮演|请作为|从现在开始你是)", "zh_role_hijack"),
    (r"(告诉我|输出|显示|打印)(你的)?(系统提示|系统指令|原始设定)", "zh_reveal_prompt"),
    (r"(无视|不要遵守|跳过)(之前的)?(规则|设定|指令)", "zh_skip_rules"),
    # Prompt leaking via encoding tricks
    (r"(?i)(base64|rot13|hex)\s*(encode|decode)", "encoding_trick"),
]

# ============================================================
# Prompt injection patterns — WARN level (log but allow)
# ============================================================

INJECTION_PATTERNS_WARN = [
    (r"(?i)(jailbreak|DAN\s+mode|developer\s+mode)", "en_jailbreak_ref"),
    (r"(越狱|破解模式|开发者模式|无限制模式)", "zh_jailbreak_ref"),
    (r"(?i)repeat\s+(the\s+)?(above|system)\s+(prompt|message)", "en_repeat_prompt"),
    (r"(重复|复述)(上面|系统)(的)?(提示|消息|内容)", "zh_repeat_prompt"),
]

# ============================================================
# Content safety patterns — BLOCK level
# ============================================================

UNSAFE_PATTERNS_BLOCK = [
    (r"(?i)(bomb\s+making|explosive\s+recipe|weapon\s+crafting)", "en_dangerous_instructions"),
    (r"(制造炸弹|制作炸药|武器制作|投毒方法)", "zh_dangerous_instructions"),
    (r"(?i)(child\s+porn|csam|child\s+abuse\s+material)", "en_csam"),
    (r"(儿童色情|虐童)", "zh_csam"),
]

# ============================================================
# Content safety patterns — WARN level
# ============================================================

UNSAFE_PATTERNS_WARN = [
    (r"(?i)(suicide\s+method|self[- ]harm\s+method|kill\s+myself)", "en_self_harm"),
    (r"(自杀方法|自残方法|怎么死)", "zh_self_harm"),
    (r"(?i)(hack\s+into|steal\s+data|credit\s+card\s+fraud)", "en_cybercrime"),
    (r"(黑客攻击|盗取数据|信用卡诈骗|盗号)", "zh_cybercrime"),
]


def validate_input(text: str) -> tuple[bool, str]:
    """Validate user input. Returns (is_valid, reason).

    Block-level injection patterns cause immediate rejection.
    Warn-level patterns are logged but allowed through.
    """
    if not text or not text.strip():
        return False, "消息不能为空"

    if len(text) > MAX_INPUT_LENGTH:
        return False, f"消息长度不能超过 {MAX_INPUT_LENGTH} 字符"

    # Check BLOCK-level injection patterns
    for pattern, tag in INJECTION_PATTERNS_BLOCK:
        if re.search(pattern, text):
            logger.warning(f"Input BLOCKED — injection detected [{tag}]: {text[:80]}...")
            return False, "输入包含不允许的内容"

    # Check WARN-level injection patterns (log but allow)
    for pattern, tag in INJECTION_PATTERNS_WARN:
        if re.search(pattern, text):
            logger.warning(f"Input WARN — suspicious pattern [{tag}]: {text[:80]}...")
            # Allow through but the warning is logged for monitoring

    return True, ""


def check_content_safety(text: str) -> tuple[bool, str]:
    """Check if content is safe. Returns (is_safe, reason).

    Block-level unsafe patterns cause immediate rejection + auto-transfer.
    Warn-level patterns are logged but allowed through.
    """
    # Check BLOCK-level unsafe patterns
    for pattern, tag in UNSAFE_PATTERNS_BLOCK:
        if re.search(pattern, text):
            logger.warning(f"Content BLOCKED — dangerous content [{tag}]: {text[:80]}...")
            return False, "内容涉及敏感话题，已转人工客服处理"

    # Check WARN-level unsafe patterns (log but allow)
    for pattern, tag in UNSAFE_PATTERNS_WARN:
        if re.search(pattern, text):
            logger.warning(f"Content WARN — sensitive topic [{tag}]: {text[:80]}...")

    return True, ""


def sanitize_output(text: str) -> str:
    """Sanitize agent output before sending to user."""
    # Remove any leaked system prompts (matched pair)
    text = re.sub(r"System prompt:.*?(?=\n|$)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<\|im_start\|>.*?<\|im_end\|>", "", text, flags=re.DOTALL)
    # Remove standalone special tokens
    text = re.sub(r"<\|im_start\|>.*?(?=\n|$)", "", text)
    text = re.sub(r"<\|im_end\|>", "", text)
    # Remove ChatML-style tags
    text = re.sub(r"<\/?(system|assistant|user)>", "", text)
    return text.strip()
