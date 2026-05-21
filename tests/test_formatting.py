from src.bot.formatting import format_bot_answer, truncate_for_discord
from src.rag.schemas import BotAnswer


def test_format_bot_answer() -> None:
    answer = BotAnswer(
        answer="Yes.",
        source="MTE320.md",
        confidence="Found",
        note="Checked local docs.",
        raw_response="",
    )
    formatted = format_bot_answer(answer)
    assert "**Answer:**" in formatted
    assert "MTE320.md" in formatted


def test_truncate_for_discord() -> None:
    text = "a" * 2000
    truncated = truncate_for_discord(text, max_chars=1800)
    assert len(truncated) <= 1800
    assert truncated.endswith("...[truncated]")
