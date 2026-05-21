from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv() -> bool:
        return False


load_dotenv()


@dataclass(frozen=True)
class Config:
    discord_token: str
    discord_application_id: str | None
    discord_guild_id: int | None
    model_backend: str
    qwen_script_path: Path | None
    openai_api_key: str | None
    openai_vector_store_id: str | None
    openai_model: str
    bot_env: str
    log_level: str
    max_question_chars: int
    max_response_chars: int
    data_dir: Path
    course_docs_dir: Path
    course_updates_dir: Path
    manifest_path: Path
    logs_dir: Path


def _resolve_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_config() -> Config:
    root = _resolve_root()

    token = os.getenv("DISCORD_TOKEN", "")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is missing")

    guild_id_raw = os.getenv("DISCORD_GUILD_ID")
    model_backend = os.getenv("MODEL_BACKEND", "qwen_local").strip() or "qwen_local"
    qwen_script = os.getenv("QWEN_SCRIPT_PATH")

    return Config(
        discord_token=token,
        discord_application_id=os.getenv("DISCORD_APPLICATION_ID"),
        discord_guild_id=int(guild_id_raw) if guild_id_raw else None,
        model_backend=model_backend,
        qwen_script_path=Path(qwen_script).expanduser() if qwen_script else None,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_vector_store_id=os.getenv("OPENAI_VECTOR_STORE_ID"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        bot_env=os.getenv("BOT_ENV", "dev"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        max_question_chars=int(os.getenv("MAX_QUESTION_CHARS", "1000")),
        max_response_chars=int(os.getenv("MAX_RESPONSE_CHARS", "1800")),
        data_dir=root / "data",
        course_docs_dir=root / "data" / "course_docs",
        course_updates_dir=root / "data" / "course_updates",
        manifest_path=root / "data" / "manifest.json",
        logs_dir=root / "logs",
    )
