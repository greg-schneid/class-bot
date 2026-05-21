from __future__ import annotations

from pathlib import Path


def validate_course_doc_name(path: Path) -> list[str]:
    warnings: list[str] = []
    lowered = path.name.lower()
    if lowered in {"outline.md", "document.md", "scan.md", "untitled.md"}:
        warnings.append(f"Filename is too generic: {path.name}")
    if path.suffix.lower() != ".md":
        warnings.append(f"Expected markdown file, got: {path.name}")
    return warnings
