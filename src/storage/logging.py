from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src.rag.schemas import BotAnswer


def _hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()


def log_interaction(
    logs_dir: Path,
    question: str,
    answer: BotAnswer,
    discord_user_id: str,
    discord_channel_id: str,
    backend_name: str,
) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "discord_user_id_hash": _hash_user_id(discord_user_id),
        "channel_id": discord_channel_id,
        "question": question,
        "answer": answer.answer,
        "source": answer.source,
        "confidence": answer.confidence,
        "backend_name": backend_name,
    }
    with (logs_dir / "bot.log").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")
