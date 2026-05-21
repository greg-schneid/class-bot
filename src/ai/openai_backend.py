from __future__ import annotations

from src.ai.provider import GenerationRequest, GenerationResult
from src.config import Config


class OpenAIBackend:
    def __init__(self, config: Config) -> None:
        self.config = config

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self.config.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is missing for MODEL_BACKEND=openai")
        if not self.config.openai_vector_store_id:
            raise RuntimeError("OPENAI_VECTOR_STORE_ID is missing for MODEL_BACKEND=openai")

        raise NotImplementedError("OpenAI backend wiring is not implemented yet.")
