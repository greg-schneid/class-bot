from pathlib import Path
import asyncio
from datetime import datetime, timezone

from src.ai.provider import GenerationResult
from src.config import Config
from src.rag import answerer as answerer_module
from src.rag.answerer import GENERATION_FAILURE_MESSAGE, answer_course_question_async
from src.rag.retrieval import RetrievedCourseContext


def test_answerer_handles_long_question() -> None:
    config = Config(
        discord_token=None,
        discord_application_id=None,
        discord_guild_id=None,
        model_backend="qwen_local",
        qwen_model_name="mlx-community/Qwen3.5-4B-MLX-4bit",
        qwen_max_tokens=512,
        qwen_enable_thinking=False,
        qwen_runtime_mode="subprocess",
        qwen_idle_unload_seconds=0.0,
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
        qwen_runtime_mode="subprocess",
        qwen_idle_unload_seconds=0.0,
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
        qwen_runtime_mode="subprocess",
        qwen_idle_unload_seconds=0.0,
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


def test_answerer_adds_current_datetime_to_system_prompt(monkeypatch) -> None:
    config = Config(
        discord_token=None,
        discord_application_id=None,
        discord_guild_id=None,
        model_backend="qwen_local",
        qwen_model_name="mlx-community/Qwen3.5-4B-MLX-4bit",
        qwen_max_tokens=512,
        qwen_enable_thinking=False,
        qwen_runtime_mode="subprocess",
        qwen_idle_unload_seconds=0.0,
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
    fixed_now = datetime(2026, 5, 21, 13, 45, 0, tzinfo=timezone.utc)
    captured: dict[str, str] = {}

    class CapturingProvider:
        async def generate(self, request):
            captured["system_prompt"] = request.system_prompt
            return GenerationResult(
                text="Answer:\nYes.\n\nSource:\nMTE320.md\n\nConfidence:\nFound\n\nNote:\nChecked local docs.",
                backend_name="test-backend",
            )

    monkeypatch.setattr(answerer_module, "get_model_provider", lambda config: CapturingProvider())
    monkeypatch.setattr(answerer_module, "build_system_prompt", lambda: f"base prompt\n\nCurrent date and time:\n{fixed_now.isoformat()}")

    asyncio.run(
        answer_course_question_async(
            question="Does MTE 320 have mandatory labs?",
            course_hint="MTE320",
            discord_user_id="1",
            discord_channel_id="2",
            config=config,
        )
    )

    assert captured["system_prompt"].endswith(fixed_now.isoformat())


def test_answerer_uses_channel_course_mapping_when_course_hint_missing(monkeypatch, tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "course_discord_ids.json").write_text('{"MTE320":"2"}', encoding="utf-8")

    config = Config(
        discord_token=None,
        discord_application_id=None,
        discord_guild_id=None,
        model_backend="qwen_local",
        qwen_model_name="mlx-community/Qwen3.5-4B-MLX-4bit",
        qwen_max_tokens=512,
        qwen_enable_thinking=False,
        qwen_runtime_mode="subprocess",
        qwen_idle_unload_seconds=0.0,
        openai_api_key=None,
        openai_vector_store_id=None,
        openai_model="gpt-5.4-mini",
        bot_env="dev",
        log_level="INFO",
        max_question_chars=1000,
        max_response_chars=1800,
        data_dir=data_dir,
        course_docs_dir=data_dir / "course_docs",
        course_updates_dir=data_dir / "course_updates",
        manifest_path=data_dir / "manifest.json",
        logs_dir=tmp_path / "logs",
    )
    captured: dict[str, str | None] = {}

    class CapturingProvider:
        async def generate(self, request):
            captured["request_course_hint"] = request.course_hint
            return GenerationResult(
                text="Answer:\nYes.\n\nSource:\nMTE320.md\n\nConfidence:\nFound\n\nNote:\nChecked local docs.",
                backend_name="test-backend",
            )

    def fake_build_retrieval_context(*, config, course_hint):
        captured["retrieval_course_hint"] = course_hint
        return RetrievedCourseContext(
            summary="context",
            source_names=["MTE320.md"],
        )

    monkeypatch.setattr(answerer_module, "get_model_provider", lambda config: CapturingProvider())
    monkeypatch.setattr(answerer_module, "build_retrieval_context", fake_build_retrieval_context)

    answer = asyncio.run(
        answer_course_question_async(
            question="Does MTE 320 have mandatory labs?",
            course_hint=None,
            discord_user_id="1",
            discord_channel_id="2",
            config=config,
        )
    )

    assert answer.answer == "Yes."
    assert captured["retrieval_course_hint"] == "MTE320"
    assert captured["request_course_hint"] == "MTE320"
