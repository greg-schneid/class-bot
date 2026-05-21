from __future__ import annotations

import argparse
import asyncio

from src.bot.formatting import format_bot_answer
from src.config import get_config
from src.rag.answerer import answer_course_question_async


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ask the local class bot a question from the CLI.")
    parser.add_argument("question", help="Question to ask about the course materials.")
    parser.add_argument("--course", help="Optional course code, like MTE320.")
    return parser


async def _run(question: str, course: str | None) -> str:
    config = get_config(require_discord_token=False)
    answer = await answer_course_question_async(
        question=question,
        course_hint=course,
        discord_user_id="cli-user",
        discord_channel_id="cli",
        config=config,
    )
    return format_bot_answer(answer)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    print(asyncio.run(_run(question=args.question, course=args.course)))


if __name__ == "__main__":
    main()
