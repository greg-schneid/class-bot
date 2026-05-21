from __future__ import annotations

import asyncio
import gc
import json
import sys
from dataclasses import dataclass
from contextlib import suppress

from src.ai.provider import GenerationRequest, GenerationResult
from src.config import Config


@dataclass
class _LoadedQwenRuntime:
    model: object
    tokenizer: object
    generate_fn: object


@dataclass
class _QueuedGeneration:
    request: GenerationRequest
    future: asyncio.Future[GenerationResult]


class _QwenRuntimeManager:
    def __init__(self) -> None:
        self._runtime_by_model: dict[str, _LoadedQwenRuntime] = {}
        self._unload_tasks: dict[str, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()

    async def get_runtime(self, model_name: str) -> _LoadedQwenRuntime:
        await self._cancel_unload(model_name)
        async with self._lock:
            runtime = self._runtime_by_model.get(model_name)
            if runtime is None:
                runtime = await asyncio.to_thread(_load_qwen_runtime, model_name)
                self._runtime_by_model[model_name] = runtime
            return runtime

    async def schedule_unload(self, model_name: str, idle_seconds: float) -> None:
        await self._cancel_unload(model_name)
        if idle_seconds <= 0:
            await self.unload_now(model_name)
            return

        async def _delayed_unload() -> None:
            try:
                await asyncio.sleep(idle_seconds)
                await self.unload_now(model_name)
            except asyncio.CancelledError:
                return

        self._unload_tasks[model_name] = asyncio.create_task(_delayed_unload())

    async def unload_now(self, model_name: str) -> None:
        async with self._lock:
            runtime = self._runtime_by_model.pop(model_name, None)
        task = self._unload_tasks.pop(model_name, None)
        if task is not None and task is not asyncio.current_task():
            task.cancel()
        if runtime is not None:
            del runtime
            await asyncio.to_thread(gc.collect)

    async def _cancel_unload(self, model_name: str) -> None:
        task = self._unload_tasks.pop(model_name, None)
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


_RUNTIME_MANAGER = _QwenRuntimeManager()


class QwenLocalBackend:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._queue: asyncio.Queue[_QueuedGeneration] = asyncio.Queue()
        self._worker_task: asyncio.Task[None] | None = None
        self._worker_lock = asyncio.Lock()

    async def preload(self) -> None:
        if self.config.qwen_runtime_mode == "subprocess":
            return
        await _RUNTIME_MANAGER.get_runtime(self.config.qwen_model_name)

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        await self._ensure_worker()
        loop = asyncio.get_running_loop()
        future: asyncio.Future[GenerationResult] = loop.create_future()
        await self._queue.put(_QueuedGeneration(request=request, future=future))
        return await future

    async def close(self) -> None:
        worker = self._worker_task
        if worker is None:
            return
        worker.cancel()
        with suppress(asyncio.CancelledError):
            await worker
        self._worker_task = None

    async def _ensure_worker(self) -> None:
        async with self._worker_lock:
            if self._worker_task is None or self._worker_task.done():
                self._worker_task = asyncio.create_task(self._worker_loop())

    async def _worker_loop(self) -> None:
        while True:
            queued = await self._queue.get()
            try:
                result = await self._execute_request(queued.request)
            except Exception as exc:
                if not queued.future.done():
                    queued.future.set_exception(exc)
            else:
                if not queued.future.done():
                    queued.future.set_result(result)
            finally:
                self._queue.task_done()

    async def _execute_request(self, request: GenerationRequest) -> GenerationResult:
        if self.config.qwen_runtime_mode == "subprocess":
            response = await self._generate_via_subprocess(request)
            return GenerationResult(text=response, backend_name="qwen_local")

        runtime = await _RUNTIME_MANAGER.get_runtime(self.config.qwen_model_name)
        try:
            response = await asyncio.to_thread(self._generate_sync, request, runtime)
        finally:
            await _RUNTIME_MANAGER.schedule_unload(
                self.config.qwen_model_name,
                self.config.qwen_idle_unload_seconds,
            )
        return GenerationResult(text=response, backend_name="qwen_local")

    async def _generate_via_subprocess(self, request: GenerationRequest) -> str:
        payload = json.dumps(
            {
                "model_name": self.config.qwen_model_name,
                "max_tokens": self.config.qwen_max_tokens,
                "enable_thinking": self.config.qwen_enable_thinking,
                "system_prompt": request.system_prompt,
                "user_prompt": request.user_prompt,
            }
        ).encode("utf-8")
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "src.ai.qwen_local_worker",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate(payload)
        if process.returncode != 0:
            error_text = stderr.decode("utf-8", errors="replace").strip() or "Qwen worker failed."
            raise RuntimeError(error_text)
        return stdout.decode("utf-8")

    def _generate_sync(self, request: GenerationRequest, runtime: _LoadedQwenRuntime) -> str:
        messages = [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.user_prompt},
        ]
        prompt = runtime.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=self.config.qwen_enable_thinking,
        )
        return runtime.generate_fn(
            runtime.model,
            runtime.tokenizer,
            prompt=prompt,
            max_tokens=self.config.qwen_max_tokens,
            verbose=False,
        )


def _load_qwen_runtime(model_name: str) -> _LoadedQwenRuntime:
    try:
        from mlx_lm import generate, load
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "mlx_lm is not installed. Install the local Qwen runtime dependencies before using MODEL_BACKEND=qwen_local."
        ) from exc

    model, tokenizer = load(model_name)
    return _LoadedQwenRuntime(
        model=model,
        tokenizer=tokenizer,
        generate_fn=generate,
    )
