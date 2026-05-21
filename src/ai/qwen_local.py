from __future__ import annotations

import asyncio
from functools import lru_cache

from src.ai.provider import GenerationRequest, GenerationResult
from src.config import Config


class QwenLocalBackend:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._generation_lock = asyncio.Lock()

    async def preload(self) -> None:
        await asyncio.to_thread(_load_qwen_runtime, self.config.qwen_model_name)

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        async with self._generation_lock:
            response = await asyncio.to_thread(self._generate_sync, request)
        return GenerationResult(
            text=response,
            backend_name="qwen_local",
        )

    def _generate_sync(self, request: GenerationRequest) -> str:
        model, tokenizer, generate_fn = _load_qwen_runtime(self.config.qwen_model_name)
        messages = [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.user_prompt},
        ]
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=self.config.qwen_enable_thinking,
        )
        return generate_fn(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=self.config.qwen_max_tokens,
            verbose=False,
        )


@lru_cache(maxsize=2)
def _load_qwen_runtime(model_name: str):
    try:
        from mlx_lm import generate, load
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "mlx_lm is not installed. Install the local Qwen runtime dependencies before using MODEL_BACKEND=qwen_local."
        ) from exc

    model, tokenizer = load(model_name)
    return model, tokenizer, generate
