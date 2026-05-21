from __future__ import annotations

import asyncio
import logging

from src.config import get_config

logger = logging.getLogger(__name__)

try:
    import discord
    from discord import app_commands
except ImportError:  # pragma: no cover
    discord = None
    app_commands = None

from src.bot.commands import SOURCE_POLICY_TEXT, build_classes_response
from src.bot.formatting import format_bot_answer, truncate_for_discord
from src.rag.answerer import answer_course_question_async


def create_bot() -> "discord.Client":
    if discord is None:  # pragma: no cover
        raise RuntimeError("discord.py is not installed. Run `pip install -r requirements.txt` first.")

    config = get_config(require_discord_token=True)
    intents = discord.Intents.default()

    class CourseRepBot(discord.Client):
        def __init__(self) -> None:
            super().__init__(intents=intents)
            self.tree = app_commands.CommandTree(self)

        async def setup_hook(self) -> None:
            if config.discord_guild_id:
                guild = discord.Object(id=config.discord_guild_id)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
            else:
                await self.tree.sync()

    bot = CourseRepBot()

    @bot.tree.command(name="classes", description="List available course materials.")
    async def classes(interaction: "discord.Interaction") -> None:
        await interaction.response.send_message(build_classes_response(), ephemeral=True)

    @bot.tree.command(name="source_policy", description="Explain what sources the bot uses.")
    async def source_policy(interaction: "discord.Interaction") -> None:
        await interaction.response.send_message(SOURCE_POLICY_TEXT, ephemeral=True)

    @bot.tree.command(name="ask", description="Ask a question about class materials.")
    async def ask(
        interaction: "discord.Interaction",
        question: str,
        course: str | None = None,
    ) -> None:
        await interaction.response.defer(thinking=True)
        answer = await answer_course_question_async(
            question=question,
            course_hint=course,
            discord_user_id=str(interaction.user.id),
            discord_channel_id=str(interaction.channel_id),
            config=config,
        )
        formatted = truncate_for_discord(
            format_bot_answer(answer),
            max_chars=config.max_response_chars,
        )
        await interaction.followup.send(formatted)

    return bot


async def _run() -> None:
    config = get_config(require_discord_token=True)
    bot = create_bot()
    if not config.discord_token:  # pragma: no cover
        raise RuntimeError("DISCORD_TOKEN is missing")
    await bot.start(config.discord_token)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run())


if __name__ == "__main__":
    main()
