"""Shared pytest fixtures for isolated Text Analysis Manager workflows."""
from pathlib import Path

import pytest

from db.db_config import DatabaseConfig


@pytest.fixture
def isolated_database(tmp_path: Path):
    """Use a fresh SQLite database for each test and restore global state."""
    old_path = DatabaseConfig._db_path
    old_connection = DatabaseConfig._connection
    DatabaseConfig.close_connection()
    DatabaseConfig._db_path = str(tmp_path / "test.sqlite")
    ok, error = DatabaseConfig.initialize_database()
    assert ok, error
    try:
        yield tmp_path / "test.sqlite"
    finally:
        DatabaseConfig.close_connection()
        DatabaseConfig._db_path = old_path
        DatabaseConfig._connection = old_connection
