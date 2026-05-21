from __future__ import annotations

from src.ai.openai_backend import OpenAIBackend
from src.ai.provider import ModelProvider
from src.ai.qwen_local import QwenLocalBackend
from src.config import Config

_PROVIDER_BY_CONFIG: dict[Config, ModelProvider] = {}


def get_model_provider(config: Config) -> ModelProvider:
    provider = _PROVIDER_BY_CONFIG.get(config)
    if provider is not None:
        return provider

    backend = config.model_backend.lower()
    if backend == "qwen_local":
        provider = QwenLocalBackend(config=config)
    elif backend == "openai":
        provider = OpenAIBackend(config=config)
    else:
        raise RuntimeError(f"Unsupported MODEL_BACKEND: {config.model_backend}")
    _PROVIDER_BY_CONFIG[config] = provider
    return provider
