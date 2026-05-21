from __future__ import annotations

from functools import lru_cache

from src.ai.provider import GenerationRequest, GenerationResult
from src.config import Config


class QwenLocalBackend:
    def __init__(self, config: Config) -> None:
        self.config = config

    async def generate(self, request: GenerationRequest) -> GenerationResult:
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
        response = generate_fn(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=self.config.qwen_max_tokens,
            verbose=False,
        )
        return GenerationResult(
            text=response,
            backend_name="qwen_local",
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
