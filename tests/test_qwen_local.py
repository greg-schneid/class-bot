from pathlib import Path
import asyncio

from src.ai.provider import GenerationRequest
from src.ai.qwen_local import QwenLocalBackend, _RUNTIME_MANAGER
from src.config import Config


def make_config(*, idle_unload_seconds: float) -> Config:
    return Config(
        discord_token=None,
        discord_application_id=None,
        discord_guild_id=None,
        model_backend="qwen_local",
        qwen_model_name="test-model",
        qwen_max_tokens=128,
        qwen_enable_thinking=False,
        qwen_runtime_mode="in_process",
        qwen_idle_unload_seconds=idle_unload_seconds,
        openai_api_key=None,
        openai_vector_store_id=None,
        openai_model="gpt-5.4-mini",
        bot_env="dev",
        log_level="INFO",
        max_question_chars=1000,
        max_response_chars=1800,
        data_dir=Path("/tmp/data"),
        course_docs_dir=Path("/tmp/data/course_docs"),
        course_updates_dir=Path("/tmp/data/course_updates"),
        manifest_path=Path("/tmp/data/manifest.json"),
        logs_dir=Path("/tmp/logs"),
    )


def test_qwen_backend_unloads_immediately_when_idle_timeout_is_zero(monkeypatch) -> None:
    events: list[str] = []

    class FakeTokenizer:
        def apply_chat_template(self, messages, tokenize, add_generation_prompt, enable_thinking):
            return "prompt"

    def fake_load_runtime(model_name: str):
        events.append(f"load:{model_name}")
        def fake_generate(*args, **kwargs):
            return "Answer:\nYes."

        return type(
            "Runtime",
            (),
            {
                "model": object(),
                "tokenizer": FakeTokenizer(),
                "generate_fn": staticmethod(fake_generate),
            },
        )()

    monkeypatch.setattr("src.ai.qwen_local._load_qwen_runtime", fake_load_runtime)
    monkeypatch.setattr("src.ai.qwen_local.gc.collect", lambda: 0)

    backend = QwenLocalBackend(config=make_config(idle_unload_seconds=0.0))
    asyncio.run(_RUNTIME_MANAGER.unload_now("test-model"))

    result = asyncio.run(
        backend.generate(
            GenerationRequest(
                system_prompt="system",
                user_prompt="user",
                course_hint=None,
            )
        )
    )

    assert result.text == "Answer:\nYes."
    assert events == ["load:test-model"]
    assert "test-model" not in _RUNTIME_MANAGER._runtime_by_model


def test_qwen_backend_subprocess_mode_uses_worker_process(monkeypatch) -> None:
    config = make_config(idle_unload_seconds=0.0)
    config = Config(**{**config.__dict__, "qwen_runtime_mode": "subprocess"})
    captured: dict[str, object] = {}

    class FakeProcess:
        returncode = 0

        async def communicate(self, payload: bytes):
            captured["payload"] = payload.decode("utf-8")
            return (b"worker response", b"")

    async def fake_create_subprocess_exec(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    backend = QwenLocalBackend(config=config)
    result = asyncio.run(
        backend.generate(
            GenerationRequest(
                system_prompt="system",
                user_prompt="user",
                course_hint=None,
            )
        )
    )

    assert result.text == "worker response"
    assert captured["args"][1:] == ("-m", "src.ai.qwen_local_worker")
    assert "\"model_name\": \"test-model\"" in captured["payload"]
