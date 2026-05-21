from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GenerationRequest:
    system_prompt: str
    user_prompt: str
    course_hint: str | None


@dataclass(frozen=True)
class GenerationResult:
    text: str
    backend_name: str


class ModelProvider(Protocol):
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate a text response from a backend model."""
