from src.rag.schemas import BotAnswer, enforce_safe_answer


def test_enforce_safe_answer_downgrades_unsupported_negative_to_not_found() -> None:
    answer = BotAnswer(
        answer="No group projects are mentioned in the provided course materials.",
        source="MTE309.md",
        confidence="Found",
        note="Checked local docs.",
        raw_response="",
    )

    enforced = enforce_safe_answer(answer)

    assert enforced.confidence == "Not found"


def test_enforce_safe_answer_keeps_explicit_found_answers() -> None:
    answer = BotAnswer(
        answer="Yes, the course outline explicitly states that labs are mandatory.",
        source="MTE320.md",
        confidence="Found",
        note="Checked local docs.",
        raw_response="",
    )

    enforced = enforce_safe_answer(answer)

    assert enforced.confidence == "Found"
