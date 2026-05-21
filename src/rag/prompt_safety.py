from __future__ import annotations

from dataclasses import dataclass
import re


SUSPICIOUS_QUESTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bignore (?:all|any|the|your|previous) instructions\b", re.IGNORECASE),
    re.compile(r"\bdisregard (?:all|any|the|your|previous) instructions\b", re.IGNORECASE),
    re.compile(r"\boverride (?:all|any|the|your|previous) instructions\b", re.IGNORECASE),
    re.compile(r"\bsystem prompt\b", re.IGNORECASE),
    re.compile(r"\bdeveloper message\b", re.IGNORECASE),
    re.compile(r"\bhidden prompt\b", re.IGNORECASE),
    re.compile(r"\breveal\b.*\b(prompt|instructions|chain of thought)\b", re.IGNORECASE),
    re.compile(r"\bshow\b.*\b(prompt|instructions|chain of thought)\b", re.IGNORECASE),
    re.compile(r"\bprint\b.*\b(prompt|instructions|chain of thought)\b", re.IGNORECASE),
    re.compile(r"\broleplay\b", re.IGNORECASE),
    re.compile(r"\bact as\b", re.IGNORECASE),
    re.compile(r"<\s*(?:system|assistant|developer|tool)\s*>", re.IGNORECASE),
    re.compile(r"^\s*(?:system|assistant|developer)\s*:", re.IGNORECASE | re.MULTILINE),
)

CONTROL_TOKEN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"<\|[^>]+?\|>"),
    re.compile(r"```(?:system|assistant|developer)?", re.IGNORECASE),
)

SAFE_BLOCK_MESSAGE = (
    "I can only help with course-related questions about the uploaded materials. "
    "I can't follow requests to ignore instructions, reveal prompts, or change roles."
)


@dataclass(frozen=True)
class PromptSafetyResult:
    blocked: bool
    reason: str | None


def detect_prompt_injection_attempt(question: str) -> PromptSafetyResult:
    normalized = question.strip()
    if not normalized:
        return PromptSafetyResult(blocked=False, reason=None)

    if any(pattern.search(normalized) for pattern in SUSPICIOUS_QUESTION_PATTERNS):
        return PromptSafetyResult(blocked=True, reason="suspicious_meta_instructions")

    if any(pattern.search(normalized) for pattern in CONTROL_TOKEN_PATTERNS):
        return PromptSafetyResult(blocked=True, reason="control_tokens")

    return PromptSafetyResult(blocked=False, reason=None)


def sanitize_untrusted_text(text: str) -> str:
    sanitized = text.replace("```", "` ` `")
    sanitized = re.sub(r"<\|([^>]+?)\|>", r"[token:\1]", sanitized)
    return sanitized
