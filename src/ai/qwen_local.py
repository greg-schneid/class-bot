from __future__ import annotations

from pathlib import Path

from src.ai.provider import GenerationRequest, GenerationResult
from src.config import Config


class QwenLocalBackend:
    def __init__(self, config: Config) -> None:
        self.config = config

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        script_path = self.config.qwen_script_path
        if script_path is None:
            raise RuntimeError("QWEN_SCRIPT_PATH is not configured")
        if not Path(script_path).exists():
            raise RuntimeError(f"Qwen script not found at {script_path}")

        # Placeholder until we inspect the real script interface.
        prompt_preview = request.user_prompt.strip()[:600]
        return GenerationResult(
            text=(
                "Answer:\n"
                "The local Qwen backend is wired into the app structure, but its adapter still needs "
                "the concrete call contract from the external script.\n\n"
                "Source:\n"
                "Local markdown materials\n\n"
                "Confidence:\n"
                "Ambiguous\n\n"
                "Note:\n"
                f"Adapter stub active. Prompt preview: {prompt_preview}"
            ),
            backend_name="qwen_local",
        )
