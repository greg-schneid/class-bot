from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.config import Config
from src.docs.manifest import get_manifest

GENERAL_COURSE_CODES = {"GENERAL"}


@dataclass(frozen=True)
class RetrievedCourseContext:
    summary: str
    source_names: list[str]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def build_retrieval_context(config: Config, course_hint: str | None) -> RetrievedCourseContext:
    manifest = get_manifest(config.manifest_path)
    courses = manifest.get("courses", {})
    root_dir = config.manifest_path.parent.parent

    if course_hint:
        selected_codes = [course_hint.strip().upper()]
    else:
        selected_codes = sorted(code for code in courses.keys() if code not in GENERAL_COURSE_CODES)
    chunks: list[str] = []
    source_names: list[str] = []

    for course_code in selected_codes:
        entry = courses.get(course_code)
        if not entry:
            continue

        main_doc = entry.get("main_doc")
        updates_doc = entry.get("updates_doc")

        if main_doc:
            main_path = Path(main_doc)
            if not main_path.is_absolute():
                main_path = root_dir / main_path
            if main_path.exists():
                source_names.append(main_path.name)
                chunks.append(f"[{course_code} main]\n{_read_text(main_path)}")

        if updates_doc:
            updates_path = Path(updates_doc)
            if not updates_path.is_absolute():
                updates_path = root_dir / updates_path
            if updates_path.exists():
                source_names.append(updates_path.name)
                chunks.append(f"[{course_code} updates]\n{_read_text(updates_path)}")

    if not chunks:
        return RetrievedCourseContext(
            summary="No local course materials were found for this request.",
            source_names=[],
        )

    return RetrievedCourseContext(
        summary="\n\n".join(chunks),
        source_names=source_names,
    )
