from __future__ import annotations

from src.rag.schemas import BotAnswer


def format_bot_answer(answer: BotAnswer) -> str:
    return (
        f"**Answer:**\n{answer.answer}\n\n"
        f"**Source:**\n{answer.source}\n\n"
        f"**Confidence:**\n{answer.confidence}\n\n"
        f"**Note:**\n{answer.note}"
    )


def truncate_for_discord(text: str, max_chars: int = 1800) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 17] + "\n\n...[truncated]"
