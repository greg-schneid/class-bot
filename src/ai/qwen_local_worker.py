from __future__ import annotations

import gc
import json
import sys


def main() -> int:
    payload = json.load(sys.stdin)
    try:
        from mlx_lm import generate, load
        import mlx.core as mx
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "mlx_lm is not installed. Install the local Qwen runtime dependencies before using MODEL_BACKEND=qwen_local."
        ) from exc

    model, tokenizer = load(payload["model_name"])
    messages = [
        {"role": "system", "content": payload["system_prompt"]},
        {"role": "user", "content": payload["user_prompt"]},
    ]
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=payload["enable_thinking"],
    )
    response = generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=payload["max_tokens"],
        verbose=False,
    )
    sys.stdout.write(response)
    sys.stdout.flush()

    del model
    del tokenizer
    gc.collect()
    mx.clear_cache()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
