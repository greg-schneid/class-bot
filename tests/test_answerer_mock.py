from pathlib import Path
import asyncio

from src.ai.provider import GenerationResult
from src.config import Config
from src.rag import answerer as answerer_module
from src.rag.answerer import GENERATION_FAILURE_MESSAGE, answer_course_question_async


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


def test_answerer_retries_once_and_succeeds(monkeypatch) -> None:
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
        max_question_chars=1000,
        max_response_chars=1800,
        data_dir=Path("/tmp/data"),
        course_docs_dir=Path("/tmp/data/course_docs"),
        course_updates_dir=Path("/tmp/data/course_updates"),
        manifest_path=Path("/tmp/data/manifest.json"),
        logs_dir=Path("/tmp/logs"),
    )

    class FlakyProvider:
        def __init__(self) -> None:
            self.calls = 0

        async def generate(self, request):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary failure")
            return GenerationResult(
                text="Answer:\nYes.\n\nSource:\nMTE320.md\n\nConfidence:\nFound\n\nNote:\nChecked local docs.",
                backend_name="test-backend",
            )

    provider = FlakyProvider()
    monkeypatch.setattr(answerer_module, "get_model_provider", lambda config: provider)

    answer = asyncio.run(
        answer_course_question_async(
            question="Does MTE 320 have mandatory labs?",
            course_hint="MTE320",
            discord_user_id="1",
            discord_channel_id="2",
            config=config,
        )
    )

    assert provider.calls == 2
    assert answer.answer == "Yes."
    assert answer.confidence == "Found"


def test_answerer_returns_fallback_after_two_failures(monkeypatch) -> None:
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
        max_question_chars=1000,
        max_response_chars=1800,
        data_dir=Path("/tmp/data"),
        course_docs_dir=Path("/tmp/data/course_docs"),
        course_updates_dir=Path("/tmp/data/course_updates"),
        manifest_path=Path("/tmp/data/manifest.json"),
        logs_dir=Path("/tmp/logs"),
    )

    class FailingProvider:
        def __init__(self) -> None:
            self.calls = 0

        async def generate(self, request):
            self.calls += 1
            raise RuntimeError("still failing")

    provider = FailingProvider()
    monkeypatch.setattr(answerer_module, "get_model_provider", lambda config: provider)

    answer = asyncio.run(
        answer_course_question_async(
            question="Does MTE 320 have mandatory labs?",
            course_hint="MTE320",
            discord_user_id="1",
            discord_channel_id="2",
            config=config,
        )
    )

    assert provider.calls == 2
    assert answer.answer == GENERATION_FAILURE_MESSAGE
