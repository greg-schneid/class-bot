from __future__ import annotations

from src.docs.manifest import get_classes_message

SOURCE_POLICY_TEXT = (
    "I only answer using uploaded local course materials and manually maintained update notes. "
    "Newer Learn posts, instructor emails, or course staff announcements may override what I find here."
)


def build_classes_response() -> str:
    return get_classes_message()
