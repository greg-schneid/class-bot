from __future__ import annotations

from src.ai.openai_backend import OpenAIBackend
from src.ai.provider import ModelProvider
from src.ai.qwen_local import QwenLocalBackend
from src.config import Config


def get_model_provider(config: Config) -> ModelProvider:
    backend = config.model_backend.lower()
    if backend == "qwen_local":
        return QwenLocalBackend(config=config)
    if backend == "openai":
        return OpenAIBackend(config=config)
    raise RuntimeError(f"Unsupported MODEL_BACKEND: {config.model_backend}")
