from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter

from src.config import get_config
from src.rag.answerer import answer_course_question_async


@dataclass(frozen=True)
class StressCase:
    case_id: str
    course: str
    question: str
    expected_confidence: str
    expected_keywords: tuple[str, ...]


STRESS_CASES: tuple[StressCase, ...] = (
    StressCase("MTE309-01", "MTE309", "What is the grading breakdown for MTE 309?", "Found", ("Homework", "Quiz 1", "Midterm", "Final")),
    StressCase("MTE309-02", "MTE309", "When is Quiz 1 for MTE 309?", "Found", ("June 5", "11:30", "PSE")),
    StressCase("MTE309-03", "MTE309", "When is the MTE 309 midterm?", "Found", ("June 22", "1:30", "PSE")),
    StressCase("MTE309-04", "MTE309", "Are homework assignments graded in MTE 309?", "Found", ("0%", "Homework")),
    StressCase("MTE309-05", "MTE309", "What aids are allowed on MTE 309 quizzes and exams?", "Found", ("crib sheet", "non-programmable calculator", "Property Tables")),
    StressCase("MTE309-06", "MTE309", "Is there a group project in MTE 309?", "Not found", ("could not find",)),
    StressCase("MTE320-01", "MTE320", "Does MTE 320 have mandatory labs?", "Found", ("mandatory", "labs")),
    StressCase("MTE320-02", "MTE320", "How many labs are there in MTE 320?", "Found", ("5 labs",)),
    StressCase("MTE320-03", "MTE320", "When is the MTE 320 midterm exam?", "Found", ("June 24, 2026", "1:30", "PSE")),
    StressCase("MTE320-04", "MTE320", "Are MTE 320 labs done individually or in groups?", "Found", ("groups of two",)),
    StressCase("MTE320-05", "MTE320", "What is the late penalty for MTE 320 lab reports?", "Found", ("20%", "100%")),
    StressCase("MTE320-06", "MTE320", "What is the final exam date and time for MTE 320?", "Found", ("TBA",)),
    StressCase("MTE321-01", "MTE321", "When is the MTE 321 midterm?", "Found", ("June 25", "1:30", "PSE")),
    StressCase("MTE321-02", "MTE321", "What time is the MTE 321 tutorial?", "Found", ("Friday", "2:30", "3:20")),
    StressCase("MTE321-03", "MTE321", "How many teaching assistants are listed for MTE 321?", "Found", ("Three", "TA")),
    StressCase("MTE321-04", "MTE321", "Are MTE 321 lectures in person?", "Found", ("in-person",)),
    StressCase("MTE321-05", "MTE321", "What is Project 1 due date for MTE 321?", "Found", ("June 19", "11:59")),
    StressCase("MTE321-06", "MTE321", "Is attendance worth a percentage grade in MTE 321?", "Not found", ("could not find",)),
    StressCase("MTE325-01", "MTE325", "Who is the instructor for MTE 325?", "Found", ("Allyson Giannikouris",)),
    StressCase("MTE325-02", "MTE325", "Are MTE 325 tutorials recorded?", "Found", ("not recorded",)),
    StressCase("MTE325-03", "MTE325", "Is there a required textbook for MTE 325?", "Found", ("no required textbook",)),
    StressCase("MTE325-04", "MTE325", "When do MTE 325 lab sessions begin?", "Found", ("May 25", "Lab 1")),
    StressCase("MTE325-05", "MTE325", "Does MTE 325 have additional costs for students?", "Found", ("no additional costs",)),
    StressCase("MTE325-06", "MTE325", "What technologies are required for MTE 325?", "Found", ("LEARN", "CROWDMARK", "Odyssey")),
    StressCase("MTE351-01", "MTE351", "Who teaches MTE 351?", "Found", ("Nahid Rahmati",)),
    StressCase("MTE351-02", "MTE351", "When is the MTE 351 midterm?", "Found", ("26-Jun-2026", "1:30")),
    StressCase("MTE351-03", "MTE351", "When is the final project report due in MTE 351?", "Found", ("05-August-26",)),
    StressCase("MTE351-04", "MTE351", "What textbook is required for MTE 351?", "Found", ("William J. Palm", "Required")),
    StressCase("MTE351-05", "MTE351", "What are the instructor office hours for MTE 351?", "Found", ("Tuesdays", "4:30", "5:30")),
    StressCase("MTE351-06", "MTE351", "Does MTE 351 have mandatory labs?", "Not found", ("could not find",)),
)


@dataclass(frozen=True)
class StressResult:
    case: StressCase
    answer: str
    source: str
    confidence: str
    note: str
    raw_response: str
    duration_seconds: float

    @property
    def keyword_match(self) -> bool:
        haystack = f"{self.answer}\n{self.source}\n{self.raw_response}".lower()
        return all(keyword.lower() in haystack for keyword in self.case.expected_keywords)

    @property
    def confidence_match(self) -> bool:
        return self.confidence == self.case.expected_confidence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a fixed stress test suite and write a markdown review file.")
    parser.add_argument(
        "--output",
        default="tmp/stress_test_results.md",
        help="Where to write the markdown review file.",
    )
    return parser


async def run_case(case: StressCase) -> StressResult:
    config = get_config(require_discord_token=False)
    start = perf_counter()
    answer = await answer_course_question_async(
        question=case.question,
        course_hint=case.course,
        discord_user_id="stress-test",
        discord_channel_id="stress-test-cli",
        config=config,
    )
    duration = perf_counter() - start
    return StressResult(
        case=case,
        answer=answer.answer,
        source=answer.source,
        confidence=answer.confidence,
        note=answer.note,
        raw_response=answer.raw_response,
        duration_seconds=duration,
    )


async def run_all_cases() -> list[StressResult]:
    results: list[StressResult] = []
    for case in STRESS_CASES:
        results.append(await run_case(case))
    return results


def render_markdown(results: list[StressResult]) -> str:
    generated_at = datetime.now().isoformat(timespec="seconds")
    confidence_passes = sum(result.confidence_match for result in results)
    keyword_passes = sum(result.keyword_match for result in results)

    lines = [
        "# Stress Test Results",
        "",
        f"Generated at: `{generated_at}`",
        f"Total cases: **{len(results)}**",
        f"Confidence matches: **{confidence_passes}/{len(results)}**",
        f"Keyword heuristic matches: **{keyword_passes}/{len(results)}**",
        "",
        "Each case is explicitly course-scoped, so the runner always passes a `course_hint` to the answerer.",
        "",
        "## Summary",
        "",
        "| Case | Course | Expected | Actual | Keyword Match | Time (s) |",
        "|---|---|---|---|---|---:|",
    ]

    for result in results:
        lines.append(
            f"| {result.case.case_id} | {result.case.course} | {result.case.expected_confidence} | "
            f"{result.confidence} | {'yes' if result.keyword_match else 'no'} | {result.duration_seconds:.2f} |"
        )

    lines.extend(["", "## Full Outputs", ""])

    for result in results:
        lines.extend(
            [
                f"### {result.case.case_id}",
                "",
                f"- Course: `{result.case.course}`",
                f"- Question: {result.case.question}",
                f"- Expected confidence: `{result.case.expected_confidence}`",
                f"- Expected keywords: `{', '.join(result.case.expected_keywords)}`",
                f"- Actual confidence: `{result.confidence}`",
                f"- Keyword heuristic match: `{'yes' if result.keyword_match else 'no'}`",
                f"- Duration: `{result.duration_seconds:.2f}s`",
                "",
                "**Answer**",
                "",
                result.answer,
                "",
                "**Source**",
                "",
                result.source,
                "",
                "**Note**",
                "",
                result.note,
                "",
            ]
        )

    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results = asyncio.run(run_all_cases())
    output_path.write_text(render_markdown(results), encoding="utf-8")
    print(f"Wrote stress test report to {output_path}")


if __name__ == "__main__":
    main()
