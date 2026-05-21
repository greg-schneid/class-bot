from __future__ import annotations

from src.ai.factory import get_model_provider
from src.ai.provider import GenerationRequest
from src.config import Config
from src.rag.prompt_safety import SAFE_BLOCK_MESSAGE, detect_prompt_injection_attempt
from src.rag.prompts import SYSTEM_PROMPT, build_user_prompt
from src.rag.retrieval import build_retrieval_context
from src.rag.schemas import BotAnswer, DEFAULT_NOTE, enforce_safe_answer, parse_model_response
from src.storage.logging import log_interaction

GENERATION_FAILURE_MESSAGE = "Sorry, the bot doesn't appear to be working right now."


async def answer_course_question_async(
    question: str,
    course_hint: str | None,
    discord_user_id: str,
    discord_channel_id: str,
    config: Config,
) -> BotAnswer:
    if len(question) > config.max_question_chars:
        return BotAnswer(
            answer="Question is too long. Please ask a shorter course-related question.",
            source="None",
            confidence="Not found",
            note=DEFAULT_NOTE,
            raw_response="",
        )

    safety_result = detect_prompt_injection_attempt(question)
    if safety_result.blocked:
        blocked_answer = BotAnswer(
            answer=SAFE_BLOCK_MESSAGE,
            source="Safety policy",
            confidence="Not found",
            note=DEFAULT_NOTE,
            raw_response="blocked_by_prompt_safety",
        )
        log_interaction(
            logs_dir=config.logs_dir,
            question=question,
            answer=blocked_answer,
            discord_user_id=discord_user_id,
            discord_channel_id=discord_channel_id,
            backend_name=f"blocked:{safety_result.reason}",
        )
        return blocked_answer

    try:
        retrieval_context = build_retrieval_context(config=config, course_hint=course_hint)
        provider = get_model_provider(config)
        request = GenerationRequest(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(
                question=question,
                course_hint=course_hint,
                retrieval_context=retrieval_context.summary,
            ),
            course_hint=course_hint,
        )
        last_timeout = False
        result = None
        for _attempt in range(2):
            try:
                result = await provider.generate(request)
                break
            except TimeoutError:
                last_timeout = True
            except Exception:
                last_timeout = False
        if result is None:
            if last_timeout:
                raise TimeoutError
            raise RuntimeError("Model generation failed twice.")
        parsed = enforce_safe_answer(parse_model_response(result.text))
        if parsed.source == "Unknown" and retrieval_context.source_names:
            parsed.source = ", ".join(retrieval_context.source_names)

        log_interaction(
            logs_dir=config.logs_dir,
            question=question,
            answer=parsed,
            discord_user_id=discord_user_id,
            discord_channel_id=discord_channel_id,
            backend_name=result.backend_name,
        )
        return parsed
    except TimeoutError:
        return BotAnswer(
            answer=GENERATION_FAILURE_MESSAGE,
            source="None",
            confidence="Not found",
            note=DEFAULT_NOTE,
            raw_response="",
        )
    except Exception:
        return BotAnswer(
            answer=GENERATION_FAILURE_MESSAGE,
            source="None",
            confidence="Ambiguous",
            note=DEFAULT_NOTE,
            raw_response="",
        )
