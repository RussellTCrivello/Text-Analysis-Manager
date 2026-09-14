"""Attachment storage and path-safety regression tests."""
from pathlib import Path

import pytest

from utils.attachment_manager import AttachmentManager


def test_attachment_copy_is_collision_safe_and_removable(tmp_path):
    source = tmp_path / "résumé.txt"
    source.write_text("Unicode attachment", encoding="utf-8")
    manager = AttachmentManager(str(tmp_path / "attachments"))

    first_ok, first_path = manager.add_attachment("Research / Source", str(source))
    second_ok, second_path = manager.add_attachment("Research / Source", str(source))

    assert first_ok and second_ok
    assert Path(first_path).exists() and Path(second_path).exists()
    assert first_path != second_path
    assert len(manager.get_attachments("Research / Source")) == 2
    assert manager.remove_attachment(first_path)
    assert not Path(first_path).exists()


def test_attachment_copy_rejects_missing_and_reports_copy_failure(tmp_path, monkeypatch):
    manager = AttachmentManager(str(tmp_path / "attachments"))
    missing_ok, missing_error = manager.add_attachment(
        "Research source", str(tmp_path / "missing.txt")
    )
    assert not missing_ok
    assert "not a regular file" in missing_error

    source = tmp_path / "source.txt"
    source.write_text("content", encoding="utf-8")
    def fail_copy(*_args, **_kwargs):
        raise OSError("copy blocked")

    monkeypatch.setattr("utils.attachment_manager.shutil.copy2", fail_copy)
    copied_ok, copy_error = manager.add_attachment("Research source", str(source))
    assert not copied_ok
    assert "copy blocked" in copy_error


def test_attachment_removal_cannot_escape_managed_root(tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("must remain", encoding="utf-8")
    manager = AttachmentManager(str(tmp_path / "attachments"))

    assert not manager.remove_attachment(str(outside))
    assert outside.exists()
    safe_path = Path(manager.get_source_folder("../../outside")).resolve()
    safe_path.relative_to(Path(manager.source_folder).resolve())
