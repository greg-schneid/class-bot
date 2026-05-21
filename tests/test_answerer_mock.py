from pathlib import Path
import asyncio

from src.config import Config
from src.rag.answerer import answer_course_question_async


def test_answerer_handles_long_question() -> None:
    config = Config(
        discord_token=None,
        discord_application_id=None,
        discord_guild_id=None,
        model_backend="qwen_local",
        qwen_model_name="mlx-community/Qwen3.5-4B-MLX-4bit",
        qwen_max_tokens=512,
        qwen_enable_thinking=False,
        openai_api_key=None,
        openai_vector_store_id=None,
        openai_model="gpt-5.4-mini",
        bot_env="dev",
        log_level="INFO",
        max_question_chars=5,
        max_response_chars=1800,
        data_dir=Path("/tmp/data"),
        course_docs_dir=Path("/tmp/data/course_docs"),
        course_updates_dir=Path("/tmp/data/course_updates"),
        manifest_path=Path("/tmp/data/manifest.json"),
        logs_dir=Path("/tmp/logs"),
    )
    answer = asyncio.run(
        answer_course_question_async(
            question="too long",
            course_hint=None,
            discord_user_id="1",
            discord_channel_id="2",
            config=config,
        )
    )
    assert answer.confidence == "Not found"
