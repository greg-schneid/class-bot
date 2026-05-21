from pathlib import Path

from src.ai.factory import get_model_provider
from src.ai.openai_backend import OpenAIBackend
from src.ai.qwen_local import QwenLocalBackend
from src.config import Config


def make_config(backend: str) -> Config:
    return Config(
        discord_token="token",
        discord_application_id=None,
        discord_guild_id=None,
        model_backend=backend,
        qwen_script_path=Path("/tmp/test_qwen.py"),
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


def test_factory_selects_qwen() -> None:
    assert isinstance(get_model_provider(make_config("qwen_local")), QwenLocalBackend)


def test_factory_selects_openai() -> None:
    assert isinstance(get_model_provider(make_config("openai")), OpenAIBackend)
