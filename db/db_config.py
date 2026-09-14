"""
Database configuration module
Handles database connections and configuration for SQLite
Optimized for single-file EXE packaging
"""
import sqlite3
import os
import sys
from pathlib import Path
from typing import Optional

class DatabaseConfig:
    """Database configuration class for SQLite"""
    
    # Database filename
    DB_NAME = "research_db.sqlite"
    
    # Connection (SQLite doesn't need pooling, but we cache it)
    _connection: Optional[sqlite3.Connection] = None
    _db_path: Optional[str] = None
    
    @classmethod
    def get_db_path(cls) -> str:
        """Get the database file path, handling both development and EXE modes"""
        if cls._db_path:
            return cls._db_path
        
        # Check if running as PyInstaller bundle
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running as compiled EXE
            # Store database in user's AppData directory
            if sys.platform == 'win32':
                appdata = os.environ.get('APPDATA', '')
                if not appdata:
                    # Fallback to user home directory
                    appdata = os.path.expanduser('~')
                appdata_dir = os.path.join(appdata, 'TextAnalysisManager')
            else:
                # Linux/Mac
                appdata_dir = os.path.join(os.path.expanduser('~'), '.TextAnalysisManager')
            
            # Create directory if it doesn't exist
            try:
                os.makedirs(appdata_dir, exist_ok=True)
            except OSError as e:
                raise Exception(f"Cannot create database directory '{appdata_dir}': {e}")
            
            db_path = os.path.join(appdata_dir, cls.DB_NAME)
        else:
            # Running as script - store in project directory
            try:
                base_path = Path(__file__).parent.parent
                db_path = os.path.join(base_path, cls.DB_NAME)
                # Test if we can write to this location
                test_file = os.path.join(base_path, '.db_write_test')
                try:
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                except (OSError, IOError):
                    # Can't write to project directory, use user's home directory instead
                    home_dir = os.path.expanduser('~')
                    db_path = os.path.join(home_dir, cls.DB_NAME)
            except Exception:
                # Fallback to user's home directory
                home_dir = os.path.expanduser('~')
                db_path = os.path.join(home_dir, cls.DB_NAME)
        
        cls._db_path = db_path
        return db_path
    
    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        """Get a database connection"""
        if cls._connection is None:
            db_path = cls.get_db_path()
            cls._connection = sqlite3.connect(
                db_path,
                check_same_thread=False,  # Allow use from multiple threads
                timeout=30.0  # Wait up to 30 seconds for locks
            )
            # Enable foreign keys
            cls._connection.execute("PRAGMA foreign_keys = ON")
            # Return rows as dictionaries
            cls._connection.row_factory = sqlite3.Row
        return cls._connection
    
    @classmethod
    def close_connection(cls):
        """Close the database connection"""
        if cls._connection:
            cls._connection.close()
            cls._connection = None
    
    @classmethod
    def close_all_connections(cls):
        """Close all connections (alias for close_connection for compatibility)"""
        cls.close_connection()
    
    @classmethod
    def return_connection(cls, conn):
        """Return a connection (no-op for SQLite, kept for compatibility)"""
        # SQLite doesn't use connection pooling, so this is a no-op
        pass
    
    @classmethod
    def test_connection(cls) -> bool:
        """Test database connection"""
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    @classmethod
    def initialize_database(cls):
        """Initialize database and create tables if needed"""
        # Import here to avoid circular imports
        from utils.audit_trail import AuditTrail
        
        # Initialize audit trail
        AuditTrail.initialize()
        """Initialize the database and create tables if they don't exist"""
        try:
            # Ensure database path is set and directory exists
            db_path = cls.get_db_path()
            
            # Ensure parent directory exists
            db_dir = os.path.dirname(db_path)
            if db_dir:
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except OSError as e:
                    raise Exception(f"Cannot create database directory '{db_dir}': {e}")
            
            # Get connection (this will create the database file if it doesn't exist)
            conn = cls.get_connection()
            cursor = conn.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create sources table
            cursor.execute("""
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
            )
            """)
            
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_sources_name_unique ON sources (name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sources_type ON sources (type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sources_importance ON sources (importance DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sources_date_creation ON sources (date_creation DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sources_country ON sources (country)")
            
            # Create contents table
            cursor.execute("""
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
            )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_contents_sources_id ON contents (sources_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_contents_title ON contents (title)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_contents_date_content ON contents (date_content DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_contents_importance ON contents (importance DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_contents_date_creation ON contents (date_creation DESC)")
            
            # Create content_analysis table
            cursor.execute("""
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
            )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_analysis_content_id ON content_analysis (content_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_analysis_classification ON content_analysis (classification)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_analysis_date_analysis ON content_analysis (date_analysis DESC)")
            
            # Create triggers
            cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trigger_sources_update_timestamp
                AFTER UPDATE ON sources
                FOR EACH ROW
                WHEN NEW.date_modified = OLD.date_modified
            BEGIN
                UPDATE sources SET date_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """)
            
            cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trigger_contents_update_timestamp
                AFTER UPDATE ON contents
                FOR EACH ROW
                WHEN NEW.date_modified = OLD.date_modified
            BEGIN
                UPDATE contents SET date_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """)
            
            cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trigger_content_analysis_update_timestamp
                AFTER UPDATE ON content_analysis
                FOR EACH ROW
                WHEN NEW.date_modified = OLD.date_modified
            BEGIN
                UPDATE content_analysis SET date_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """)
            
            conn.commit()
            cursor.close()
            return (True, None)  # Return success and no error
        except Exception as e:
            error_msg = f"Error initializing database: {e}\nDatabase path: {cls.get_db_path()}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return (False, str(e))  # Return failure and error message
