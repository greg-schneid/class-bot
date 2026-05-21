from pathlib import Path

from src.docs.manifest import get_classes_message, get_manifest


def test_missing_manifest_returns_empty(tmp_path: Path) -> None:
    manifest = get_manifest(tmp_path / "manifest.json")
    assert manifest == {"version": 1, "courses": {}}


def test_classes_message_for_missing_manifest(tmp_path: Path) -> None:
    assert get_classes_message(tmp_path / "manifest.json") == "No course materials have been uploaded yet."
