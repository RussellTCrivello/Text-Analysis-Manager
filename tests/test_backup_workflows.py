"""Backup integrity and failure-path regression tests."""
import sqlite3

from db.db_config import DatabaseConfig
from db.db_manager import DatabaseManager
from utils.backup_restore import BackupRestoreManager


def test_full_and_partial_backups_record_scope(isolated_database, tmp_path):
    source_id = DatabaseManager.add_source({
        "name": "Backup source",
        "type": "Web",
        "link_sources": "https://example.test",
        "importance": 0.5,
        "country": "NL",
    })
    DatabaseManager.add_content({
        "title": "Backup content",
        "content_data": "body",
        "importance": 0.2,
        "sources_id": source_id,
    })

    manager = BackupRestoreManager()
    manager.backup_dir = tmp_path / "backups"
    manager.backup_dir.mkdir()

    ok, full_path, full_info = manager.create_backup("FULL")
    assert ok and full_info["tables_backed_up"] == [
        "sources", "contents", "content_analysis"
    ]
    valid, error, preview = manager.validate_backup_file(full_path)
    assert valid, error
    assert preview["sources_count"] == 1
    assert preview["contents_count"] == 1

    ok, source_path, source_info = manager.create_backup("MANUAL", ["sources"])
    assert ok and source_info["tables_backed_up"] == ["sources"]
    with sqlite3.connect(source_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM contents").fetchone()[0] == 0


def test_corrupt_backup_is_rejected_and_delete_is_scoped(isolated_database, tmp_path):
    manager = BackupRestoreManager()
    manager.backup_dir = tmp_path / "backups"
    manager.backup_dir.mkdir()
    DatabaseManager.add_source({
        "name": "Integrity source",
        "type": "Web",
        "link_sources": "https://example.test",
        "importance": 0.5,
        "country": "NL",
    })
    ok, backup_path, _ = manager.create_backup("FULL")
    assert ok

    with open(backup_path, "ab") as handle:
        handle.write(b"corruption")
    restored, message = manager.restore_backup(backup_path)
    assert not restored
    assert "checksum" in message.lower()

    outside = tmp_path / "outside.sqlite"
    outside.write_bytes(b"keep")
    deleted, message = manager.delete_backup(str(outside))
    assert not deleted
    assert outside.exists()


def test_selective_parent_restore_refuses_cascade_data_loss(isolated_database, tmp_path):
    source_id = DatabaseManager.add_source({
        "name": "Referenced source",
        "type": "Web",
        "link_sources": "https://example.test",
        "importance": 0.5,
        "country": "NL",
    })
    DatabaseManager.add_content({
        "title": "Keep this content",
        "content_data": "body",
        "importance": 0.2,
        "sources_id": source_id,
    })

    manager = BackupRestoreManager()
    manager.backup_dir = tmp_path / "backups"
    manager.backup_dir.mkdir()
    ok, backup_path, _ = manager.create_backup("MANUAL", ["sources"])
    assert ok

    restored, message = manager.restore_backup(backup_path)
    assert not restored
    assert "restore" in message.lower()
    with sqlite3.connect(DatabaseConfig.get_db_path()) as conn:
        assert conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM contents").fetchone()[0] == 1


def test_selective_child_restore_preserves_parent_rows(isolated_database, tmp_path):
    source_id = DatabaseManager.add_source({
        "name": "Analysis source",
        "type": "Web",
        "link_sources": "https://example.test",
        "importance": 0.5,
        "country": "NL",
    })
    content_id = DatabaseManager.add_content({
        "title": "Analyzed content",
        "content_data": "body",
        "importance": 0.2,
        "sources_id": source_id,
    })
    DatabaseManager.add_content_analysis({
        "content_id": content_id,
        "classification": "first",
    })

    manager = BackupRestoreManager()
    manager.backup_dir = tmp_path / "backups"
    manager.backup_dir.mkdir()
    ok, backup_path, _ = manager.create_backup("MANUAL", ["content_analysis"])
    assert ok
    DatabaseManager.add_content_analysis({
        "content_id": content_id,
        "classification": "second",
    })

    restored, message = manager.restore_backup(backup_path)
    assert restored, message
    with sqlite3.connect(DatabaseConfig.get_db_path()) as conn:
        assert conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM contents").fetchone()[0] == 1
        assert conn.execute("SELECT classification FROM content_analysis").fetchone()[0] == "first"
