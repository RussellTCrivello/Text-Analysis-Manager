"""
Create database tables - SQLite version for single-file EXE packaging
Only creates essential tables: sources, contents, content_analysis
"""
import sys
import io
import sqlite3
from db.db_config import DatabaseConfig

# Set UTF-8 encoding for stdout/stderr on Windows
if sys.platform == 'win32':
    # Check if stdout/stderr exist and have encoding attribute (may be None in compiled executables)
    if sys.stdout is not None and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    elif sys.stdout is not None and not hasattr(sys.stdout, 'encoding'):
        # stdout exists but has no encoding attribute (compiled executable)
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass  # If buffer doesn't exist, skip
    
    if sys.stderr is not None and hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    elif sys.stderr is not None and not hasattr(sys.stderr, 'encoding'):
        # stderr exists but has no encoding attribute (compiled executable)
        try:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass  # If buffer doesn't exist, skip

# Get database connection
conn = DatabaseConfig.get_connection()
cursor = conn.cursor()

# Enable foreign keys
cursor.execute("PRAGMA foreign_keys = ON")

# Create sources table (SQLite syntax)
create_source_table = """
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    link_sources TEXT NOT NULL,
    importance REAL NOT NULL DEFAULT 0.0 CHECK (importance >= 0.0 AND importance <= 1.0),
    country TEXT NOT NULL,
    city TEXT NULL,
    description TEXT NULL,
    accounts TEXT NULL,
    note TEXT NULL,
    ownership TEXT NULL,
    date_entry TIMESTAMP NULL,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modified TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_importance_range CHECK (importance >= 0.0 AND importance <= 1.0)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_sources_name_unique ON sources (name);
CREATE INDEX IF NOT EXISTS idx_sources_type ON sources (type);
CREATE INDEX IF NOT EXISTS idx_sources_importance ON sources (importance DESC);
CREATE INDEX IF NOT EXISTS idx_sources_date_creation ON sources (date_creation DESC);
CREATE INDEX IF NOT EXISTS idx_sources_country ON sources (country);
"""

# Create contents table (SQLite syntax)
create_contents_table = """
CREATE TABLE IF NOT EXISTS contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NULL,
    content_data TEXT NOT NULL,
    attachments TEXT NULL,
    note TEXT NULL,
    importance REAL NOT NULL DEFAULT 0.0 CHECK (importance >= 0.0 AND importance <= 1.0),
    date_content TIMESTAMP NULL,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modified TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    sources_id INTEGER NOT NULL,
    FOREIGN KEY (sources_id) REFERENCES sources(id) ON DELETE CASCADE,
    CONSTRAINT chk_contents_importance_range CHECK (importance >= 0.0 AND importance <= 1.0)
);

CREATE INDEX IF NOT EXISTS idx_contents_sources_id ON contents (sources_id);
CREATE INDEX IF NOT EXISTS idx_contents_date_content ON contents (date_content DESC);
CREATE INDEX IF NOT EXISTS idx_contents_importance ON contents (importance DESC);
CREATE INDEX IF NOT EXISTS idx_contents_date_creation ON contents (date_creation DESC);
"""

# Create content_analysis table (SQLite syntax)
create_content_analysis_table = """
CREATE TABLE IF NOT EXISTS content_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    list_names_people TEXT NULL,
    list_names_places TEXT NULL,
    list_coordinates TEXT NULL,
    classification TEXT NULL,
    list_sides TEXT NULL,
    date_analysis TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modified TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_content_analysis_content_id ON content_analysis (content_id);
CREATE INDEX IF NOT EXISTS idx_content_analysis_classification ON content_analysis (classification);
CREATE INDEX IF NOT EXISTS idx_content_analysis_date_analysis ON content_analysis (date_analysis DESC);
"""

# Execute table creation
print("Creating tables...")
cursor.executescript(create_source_table)
cursor.executescript(create_contents_table)
cursor.executescript(create_content_analysis_table)

# Create triggers (SQLite syntax - simpler than PostgreSQL)
print("Creating triggers...")
cursor.executescript("""
DROP TRIGGER IF EXISTS trigger_sources_update_timestamp;
CREATE TRIGGER trigger_sources_update_timestamp
    AFTER UPDATE ON sources
    FOR EACH ROW
    WHEN NEW.date_modified = OLD.date_modified
BEGIN
    UPDATE sources SET date_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
""")

cursor.executescript("""
DROP TRIGGER IF EXISTS trigger_contents_update_timestamp;
CREATE TRIGGER trigger_contents_update_timestamp
    AFTER UPDATE ON contents
    FOR EACH ROW
    WHEN NEW.date_modified = OLD.date_modified
BEGIN
    UPDATE contents SET date_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
""")

cursor.executescript("""
DROP TRIGGER IF EXISTS trigger_content_analysis_update_timestamp;
CREATE TRIGGER trigger_content_analysis_update_timestamp
    AFTER UPDATE ON content_analysis
    FOR EACH ROW
    WHEN NEW.date_modified = OLD.date_modified
BEGIN
    UPDATE content_analysis SET date_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
""")

# Commit and close
conn.commit()
cursor.close()
DatabaseConfig.close_connection()

print("Tables created successfully!")
print(f"Database location: {DatabaseConfig.get_db_path()}")
