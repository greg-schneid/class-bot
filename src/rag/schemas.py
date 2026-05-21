from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Confidence = Literal["Found", "Ambiguous", "Not found"]

DEFAULT_NOTE = (
    "I only checked uploaded course materials. Newer Learn announcements, instructor emails, "
    "or Learn posts may override this."
)


@dataclass
class BotAnswer:
    answer: str
    source: str
    confidence: Confidence
    note: str
    raw_response: str


def parse_model_response(text: str) -> BotAnswer:
    sections: dict[str, str] = {}
    current_key: str | None = None
    buffer: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped in {"Answer:", "Source:", "Confidence:", "Note:"}:
            if current_key is not None:
                sections[current_key] = "\n".join(buffer).strip()
            current_key = stripped[:-1].lower()
            buffer = []
            continue
        buffer.append(line)

    if current_key is not None:
        sections[current_key] = "\n".join(buffer).strip()

    confidence = sections.get("confidence", "Ambiguous")
    if confidence not in {"Found", "Ambiguous", "Not found"}:
        confidence = "Ambiguous"

    answer = sections.get("answer")
    if not answer:
        return BotAnswer(
            answer="I had trouble formatting the answer, and I could not safely verify the result.",
            source="Unknown",
            confidence="Ambiguous",
            note=DEFAULT_NOTE,
            raw_response=text,
        )

    return BotAnswer(
        answer=answer,
        source=sections.get("source", "Unknown"),
        confidence=confidence,
        note=sections.get("note", DEFAULT_NOTE),
        raw_response=text,
    )


def enforce_safe_answer(bot_answer: BotAnswer) -> BotAnswer:
    if bot_answer.confidence not in {"Found", "Ambiguous", "Not found"}:
        bot_answer.confidence = "Ambiguous"
    if not bot_answer.note:
        bot_answer.note = DEFAULT_NOTE
    if len(bot_answer.answer) > 1200:
        bot_answer.answer = bot_answer.answer[:1200] + "..."
    if not bot_answer.source:
        bot_answer.source = "Unknown"
    return bot_answer
