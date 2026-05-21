from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def get_manifest(manifest_path: Path | None = None) -> dict[str, Any]:
    path = manifest_path or Path(__file__).resolve().parents[2] / "data" / "manifest.json"
    if not path.exists():
        return {"version": 1, "courses": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def get_courses_summary(manifest_path: Path | None = None) -> list[dict[str, Any]]:
    manifest = get_manifest(manifest_path)
    courses = manifest.get("courses", {})
    return [
        {
            "course_code": course_code,
            "display_name": entry.get("display_name", course_code),
            "main_doc": entry.get("main_doc"),
            "updates_doc": entry.get("updates_doc"),
        }
        for course_code, entry in sorted(courses.items())
    ]


def get_classes_message(manifest_path: Path | None = None) -> str:
    courses = get_courses_summary(manifest_path)
    if not courses:
        return "No course materials have been uploaded yet."

    lines = ["Available materials:", ""]
    for course in courses:
        lines.append(course["display_name"])
        if course["main_doc"]:
            lines.append(f"- {Path(course['main_doc']).name}")
        if course["updates_doc"]:
            lines.append(f"- {Path(course['updates_doc']).name}")
        lines.append("")
    return "\n".join(lines).strip()
