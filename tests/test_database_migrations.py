"""Schema migration regression tests for databases from older releases."""
import sqlite3

from db.db_config import DatabaseConfig


def test_legacy_title_and_coordinates_columns_are_migrated(tmp_path):
    db_path = tmp_path / "legacy.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                link_sources TEXT NOT NULL,
                importance REAL NOT NULL DEFAULT 0,
                country TEXT NOT NULL,
                city TEXT, description TEXT, accounts TEXT, note TEXT,
                ownership TEXT, date_entry TIMESTAMP,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE contents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_data TEXT NOT NULL, attachments TEXT, note TEXT,
                importance REAL NOT NULL DEFAULT 0, date_content TIMESTAMP,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sources_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE
            );
            CREATE TABLE content_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
                list_names_people TEXT, list_names_places TEXT,
                coordinates TEXT, classification TEXT, list_sides TEXT,
                date_analysis TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO sources(name, type, link_sources, country)
            VALUES ('Legacy', 'Web', 'https://example.test', 'NL');
            INSERT INTO contents(content_data, sources_id) VALUES ('Legacy body', 1);
            INSERT INTO content_analysis(content_id, coordinates)
            VALUES (1, '52.37,4.90');
            """
        )

    old_path = DatabaseConfig._db_path
    old_connection = DatabaseConfig._connection
    DatabaseConfig.close_connection()
    DatabaseConfig._db_path = str(db_path)
    try:
        ok, error = DatabaseConfig.initialize_database()
        assert ok, error
        conn = DatabaseConfig.get_connection()
        content_columns = {row[1] for row in conn.execute("PRAGMA table_info(contents)")}
        analysis_columns = {row[1] for row in conn.execute("PRAGMA table_info(content_analysis)")}
        assert "title" in content_columns
        assert "list_coordinates" in analysis_columns
        assert conn.execute(
            "SELECT list_coordinates FROM content_analysis WHERE id = 1"
        ).fetchone()[0] == "52.37,4.90"
    finally:
        DatabaseConfig.close_connection()
        DatabaseConfig._db_path = old_path
        DatabaseConfig._connection = old_connection
