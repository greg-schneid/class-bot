from pathlib import Path

from src.docs.manifest import (
    get_classes_message,
    get_course_code_for_discord_channel,
    get_course_discord_ids,
    get_manifest,
)


def test_missing_manifest_returns_empty(tmp_path: Path) -> None:
    manifest = get_manifest(tmp_path / "manifest.json")
    assert manifest == {"version": 1, "courses": {}}


def test_classes_message_for_missing_manifest(tmp_path: Path) -> None:
    assert get_classes_message(tmp_path / "manifest.json") == "No course materials have been uploaded yet."


def test_course_discord_ids_missing_file_returns_empty_mapping(tmp_path: Path) -> None:
    assert get_course_discord_ids(tmp_path / "course_discord_ids.json") == {}


def test_course_code_is_resolved_from_discord_channel_id(tmp_path: Path) -> None:
    path = tmp_path / "course_discord_ids.json"
    path.write_text('{"mte320":"12345","MTE321":"67890"}', encoding="utf-8")

    assert get_course_code_for_discord_channel("12345", path) == "MTE320"
    assert get_course_code_for_discord_channel(67890, path) == "MTE321"
    assert get_course_code_for_discord_channel("99999", path) is None
