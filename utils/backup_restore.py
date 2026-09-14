"""
Backup and Restore System for SQLite
Handles scheduled backups, incremental backups, encryption, and restore
"""
import os
import json
import shutil
import hashlib
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

from db.db_config import DatabaseConfig
from db.db_manager import DatabaseManager
from config.config_manager import ConfigManager
from utils.logger import get_logger
from utils.duplicate_detector import DuplicateDetector

logger = get_logger(__name__)


class BackupRestoreManager:
    """Manages backup and restore operations"""
    
    def __init__(self):
        """Initialize backup manager"""
        self.config = ConfigManager()
        # Use path_utils for correct backup path when installed (AppData)
        from utils.path_utils import get_backups_dir, is_frozen
        
        if is_frozen():
            self.backup_dir = get_backups_dir()  # Already creates dir
        else:
            backup_path = self.config.get('Backup', 'backup_path', 'backups')
            if not Path(backup_path).is_absolute():
                base_path = Path.cwd()
                self.backup_dir = base_path / backup_path
            else:
                self.backup_dir = Path(backup_path)
            self.backup_dir.mkdir(exist_ok=True, parents=True)
        self.encryption_enabled = self.config.get('Backup', 'encryption', False)
    
    def create_backup(self, backup_type: str = 'FULL', 
                     tables: List[str] = None) -> Tuple[bool, str, Dict]:
        """Create a backup
        
        Args:
            backup_type: 'FULL', 'INCREMENTAL', or 'MANUAL'
            tables: List of table names to backup (None = all tables)
            
        Returns:
            Tuple of (success, backup_path, backup_info)
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"backup_{backup_type.lower()}_{timestamp}.sqlite"
            backup_path = self.backup_dir / backup_filename
            
            # Get tables to backup
            if tables is None:
                tables = ['sources', 'contents', 'content_analysis']
            
            # Create SQLite backup
            success = self._create_sqlite_backup(backup_path, tables)
            
            if not success:
                return False, "", {'error': 'Failed to create backup'}
            
            # Calculate backup size
            backup_size = backup_path.stat().st_size
            
            # Calculate checksum
            checksum = self._calculate_checksum(backup_path)
            
            # Encrypt if enabled
            if self.encryption_enabled:
                encrypted_path = self._encrypt_backup(backup_path)
                if encrypted_path:
                    backup_path = encrypted_path
            
            # Record backup in database
            backup_info = {
                'backup_type': backup_type,
                'backup_path': str(backup_path),
                'backup_size': backup_size,
                'tables_backed_up': tables,
                'is_encrypted': self.encryption_enabled,
                'checksum': checksum,
                'status': 'SUCCESS',
                'created_at': datetime.now().isoformat()
            }
            
            self._record_backup(backup_info)
            
            logger.info(f"Backup created: {backup_path}")
            return True, str(backup_path), backup_info
        
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False, "", {'error': str(e)}
    
    def restore_backup(self, backup_path: str, merge: bool = False) -> Tuple[bool, str]:
        """Restore from backup
        
        Args:
            backup_path: Path to backup file
            merge: If True, merge data instead of replacing (default: False)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                return False, f"Backup file not found: {backup_path}"
            
            # Decrypt if encrypted
            if backup_path.suffix == '.enc':
                decrypted_path = self._decrypt_backup(backup_path)
                if not decrypted_path:
                    return False, "Failed to decrypt backup"
                backup_path = decrypted_path
            elif backup_path.suffix not in ['.sqlite', '.db']:
                # If it's a .sql file, it's an old format backup
                return False, "Old format backup files (.sql) are not supported. Please use .sqlite format."
            
            # Verify checksum
            backup_info = self._get_backup_info(backup_path)
            if backup_info:
                expected_checksum = backup_info.get('checksum')
                if expected_checksum:
                    actual_checksum = self._calculate_checksum(backup_path)
                    if actual_checksum != expected_checksum:
                        return False, "Backup file checksum mismatch - file may be corrupted"
            
            # Restore or merge SQLite backup
            if merge:
                success = self._merge_sqlite_backup(backup_path)
                if success:
                    logger.info(f"Backup merged: {backup_path}")
                    return True, f"Backup merged successfully from {backup_path}"
                else:
                    return False, "Failed to merge backup"
            else:
                success = self._restore_sqlite_backup(backup_path)
                if success:
                    logger.info(f"Backup restored: {backup_path}")
                    return True, f"Backup restored successfully from {backup_path}"
                else:
                    return False, "Failed to restore backup"
        
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False, str(e)
    
    def _get_backup_schema(self, conn: sqlite3.Connection) -> Dict[str, List[str]]:
        """Get column names for each table in backup (handles schema variants)"""
        schema = {}
        cursor = conn.cursor()
        for table in ['sources', 'contents', 'content_analysis']:
            cursor.execute(f"PRAGMA table_info({table})")
            schema[table] = [row[1] for row in cursor.fetchall()]
        return schema
    
    def _check_schema_compatible(self, schema: Dict[str, List[str]]) -> Tuple[bool, str]:
        """Verify backup has required columns for merge. Returns (ok, error_msg)."""
        required = {
            'sources': ['id', 'name', 'type', 'link_sources', 'importance', 'country', 'city',
                        'description', 'accounts', 'note', 'ownership', 'date_entry',
                        'date_creation', 'date_modified'],
            'contents': ['id', 'content_data', 'importance', 'date_content', 'date_creation',
                         'date_modified', 'sources_id'],
            'content_analysis': ['id', 'content_id', 'list_names_people', 'list_names_places',
                                'classification', 'list_sides', 'date_analysis',
                                'date_creation', 'date_modified']
        }
        for table, cols in required.items():
            if table not in schema:
                return False, f"Missing table: {table}"
            have = set(schema[table])
            for c in cols:
                if c not in have:
                    return False, f"Table '{table}' missing required column: {c}"
        # content_analysis needs coordinates OR list_coordinates
        ca_cols = set(schema.get('content_analysis', []))
        if 'list_coordinates' not in ca_cols and 'coordinates' not in ca_cols:
            return False, "Table 'content_analysis' needs 'coordinates' or 'list_coordinates'"
        return True, ""
    
    def validate_backup_file(self, backup_path: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Validate a backup file and return preview info.
        
        Returns:
            Tuple of (is_valid, error_message, preview_info)
            preview_info contains: sources_count, contents_count, analyses_count, file_size, created_at
        """
        try:
            path = Path(backup_path)
            if not path.exists():
                return False, "File not found", None
            
            if path.suffix == '.enc':
                # Encrypted - we can't preview without decrypting
                return True, "", {'encrypted': True, 'file_size': path.stat().st_size}
            
            if path.suffix not in ['.sqlite', '.db']:
                return False, "Invalid file format. Use .sqlite or .db backup files.", None
            
            # Try to open and validate schema
            conn = sqlite3.connect(str(path))
            cursor = conn.cursor()
            
            # Check required tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('sources', 'contents', 'content_analysis')")
            tables = {row[0] for row in cursor.fetchall()}
            
            if 'sources' not in tables or 'contents' not in tables or 'content_analysis' not in tables:
                conn.close()
                return False, "Invalid backup: missing required tables (sources, contents, content_analysis).", None
            
            # Check schema compatibility
            schema = self._get_backup_schema(conn)
            ok, err = self._check_schema_compatible(schema)
            if not ok:
                conn.close()
                return False, f"Incompatible backup schema: {err}", None
            
            # Get record counts
            preview = {'file_size': path.stat().st_size}
            for table in ['sources', 'contents', 'content_analysis']:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                preview[f'{table}_count'] = cursor.fetchone()[0]
            
            # Get creation date from newest record if available
            try:
                cursor.execute("SELECT MAX(date_creation) FROM sources")
                max_date = cursor.fetchone()[0]
                if max_date:
                    preview['latest_date'] = max_date
            except:
                pass
            
            conn.close()
            return True, "", preview
            
        except sqlite3.DatabaseError as e:
            return False, f"Invalid or corrupted database file: {str(e)}", None
        except Exception as e:
            logger.error(f"Error validating backup: {e}")
            return False, str(e), None
    
    def get_backup_list(self, limit: int = 50) -> List[Dict]:
        """Get list of backup files"""
        try:
            backups = []
            # Get all backup files from backup directory
            for backup_file in sorted(self.backup_dir.glob('backup_*.sqlite*'), reverse=True):
                if backup_file.is_file():
                    try:
                        stat = backup_file.stat()
                        backup_info = {
                            'filename': backup_file.name,
                            'path': str(backup_file),
                            'size': stat.st_size,
                            'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'is_encrypted': backup_file.suffix == '.enc'
                        }
                        backups.append(backup_info)
                        if len(backups) >= limit:
                            break
                    except Exception as e:
                        logger.error(f"Error reading backup file {backup_file}: {e}")
            return backups
        except Exception as e:
            logger.error(f"Error getting backup list: {e}")
            return []
    
    def delete_backup(self, backup_path: str) -> Tuple[bool, str]:
        """Delete a backup file"""
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                return False, "Backup file not found"
            
            # Delete file
            backup_path.unlink()
            
            return True, "Backup deleted successfully"
        
        except Exception as e:
            logger.error(f"Error deleting backup: {e}")
            return False, str(e)
    
    def cleanup_old_backups(self, days: int = 30):
        """Clean up backups older than specified days"""
        try:
            cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()
            
            deleted_count = 0
            for backup_file in self.backup_dir.glob('backup_*.sqlite*'):
                if backup_file.is_file():
                    try:
                        if backup_file.stat().st_mtime < cutoff_time:
                            backup_file.unlink()
                            deleted_count += 1
                    except Exception as e:
                        logger.error(f"Error deleting old backup {backup_file}: {e}")
            
            logger.info(f"Cleaned up {deleted_count} old backups")
            return deleted_count
        
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
            return 0
    
    def _create_sqlite_backup(self, backup_path: Path, tables: List[str]) -> bool:
        """Create SQLite backup using SQLite backup API"""
        try:
            source_db = DatabaseConfig.get_db_path()
            
            # Close existing connection to ensure clean backup
            DatabaseConfig.close_connection()
            
            # Connect to source database
            source_conn = sqlite3.connect(source_db)
            
            # Create backup connection
            backup_conn = sqlite3.connect(str(backup_path))
            
            # Use SQLite backup API for online backup
            source_conn.backup(backup_conn)
            
            backup_conn.close()
            source_conn.close()
            
            # Reconnect to database
            DatabaseConfig.get_connection()
            
            return True
        
        except Exception as e:
            logger.error(f"Error creating SQLite backup: {e}")
            # Fallback: copy database file directly (requires closing connection)
            try:
                DatabaseConfig.close_connection()
                source_db = DatabaseConfig.get_db_path()
                if Path(source_db).exists():
                    shutil.copy2(source_db, backup_path)
                    # Reconnect
                    DatabaseConfig.get_connection()
                    return True
            except Exception as e2:
                logger.error(f"Error copying database file: {e2}")
                # Try to reconnect even if backup failed
                try:
                    DatabaseConfig.get_connection()
                except:
                    pass
            return False
    
    def _restore_sqlite_backup(self, backup_path: Path) -> bool:
        """Restore SQLite backup by replacing database file"""
        try:
            # Close existing connection
            DatabaseConfig.close_connection()
            
            # Get current database path
            current_db = DatabaseConfig.get_db_path()
            current_db_path = Path(current_db)
            
            # Create backup of current database before restore
            if current_db_path.exists():
                backup_current = current_db_path.with_suffix('.sqlite.bak')
                shutil.copy2(current_db_path, backup_current)
            
            # Copy backup file to current database location
            shutil.copy2(backup_path, current_db_path)
            
            # Reconnect to database
            DatabaseConfig.get_connection()
            
            return True
        
        except Exception as e:
            logger.error(f"Error restoring SQLite backup: {e}")
            return False
    
    def _merge_sqlite_backup(self, backup_path: Path) -> bool:
        """Merge SQLite backup data into current database. Uses transaction; rolls back on failure."""
        backup_conn = None
        try:
            # Get current database path
            current_db = DatabaseConfig.get_db_path()
            current_db_path = Path(current_db)
            
            # Create backup of current database before merge
            if current_db_path.exists():
                backup_current = current_db_path.with_suffix('.sqlite.bak')
                shutil.copy2(current_db_path, backup_current)
            
            # Connect to both databases
            current_conn = DatabaseConfig.get_connection()
            backup_conn = sqlite3.connect(str(backup_path))
            
            # Enable foreign keys
            current_conn.execute("PRAGMA foreign_keys = ON")
            backup_conn.execute("PRAGMA foreign_keys = ON")
            
            # Detect backup schema (handles coordinates vs list_coordinates, title presence)
            schema = self._get_backup_schema(backup_conn)
            ok, err = self._check_schema_compatible(schema)
            if not ok:
                logger.error(f"Backup schema incompatible: {err}")
                backup_conn.close()
                return False
            
            # Use single transaction - rollback on any failure
            current_conn.execute("BEGIN TRANSACTION")
            
            current_cursor = current_conn.cursor()
            backup_cursor = backup_conn.cursor()
            
            # Mapping dictionaries for ID translation
            sources_id_map = {}  # old_id -> new_id
            contents_id_map = {}  # old_id -> new_id
            
            # Build schema-compatible SELECT for sources (columns are stable)
            backup_cursor.execute("SELECT id, name, type, link_sources, importance, country, city, description, accounts, note, ownership, date_entry, date_creation, date_modified FROM sources")
            backup_sources = backup_cursor.fetchall()
            
            sources_added = 0
            sources_skipped = 0
            
            for old_id, name, source_type, link_sources, importance, country, city, description, accounts, note, ownership, date_entry, date_creation, date_modified in backup_sources:
                # Check if source with same name exists (UNIQUE constraint) - fetch all fields for full comparison
                current_cursor.execute(
                    "SELECT id, name, type, link_sources, importance, country, city, "
                    "description, accounts, note, ownership, date_entry, date_creation, date_modified "
                    "FROM sources WHERE name = ?", (name,)
                )
                existing_row = current_cursor.fetchone()
                
                if existing_row:
                    existing_dict = {
                        'id': existing_row[0],
                        'name': existing_row[1],
                        'type': existing_row[2],
                        'link_sources': existing_row[3],
                        'importance': existing_row[4],
                        'country': existing_row[5],
                        'city': existing_row[6],
                        'description': existing_row[7],
                        'accounts': existing_row[8],
                        'note': existing_row[9],
                        'ownership': existing_row[10],
                        'date_entry': existing_row[11],
                        'date_creation': existing_row[12],
                        'date_modified': existing_row[13]
                    }
                    
                    source_data = {
                        'name': name,
                        'type': source_type,
                        'link_sources': link_sources,
                        'importance': importance,
                        'country': country,
                        'city': city,
                        'description': description,
                        'accounts': accounts,
                        'note': note,
                        'ownership': ownership,
                        'date_entry': date_entry,
                        'date_creation': date_creation,
                        'date_modified': date_modified
                    }
                    
                    # Check if it's a full duplicate (all fields match)
                    if DuplicateDetector.records_match(source_data, existing_dict):
                        sources_skipped += 1
                    else:
                        # Same name but different fields - still use existing ID (UNIQUE constraint)
                        sources_skipped += 1
                    
                    sources_id_map[old_id] = existing_dict['id']
                else:
                    # No source with same name, check for duplicate using all fields (including dates)
                    source_data = {
                        'name': name,
                        'type': source_type,
                        'link_sources': link_sources,
                        'importance': importance,
                        'country': country,
                        'city': city,
                        'description': description,
                        'accounts': accounts,
                        'note': note,
                        'ownership': ownership,
                        'date_entry': date_entry,
                        'date_creation': date_creation,
                        'date_modified': date_modified
                    }
                    
                    is_duplicate, existing = DuplicateDetector.check_duplicate('sources', source_data)
                    
                    if is_duplicate:
                        # Full duplicate found, use existing ID
                        sources_id_map[old_id] = existing.get('id')
                        sources_skipped += 1
                    else:
                        # Insert new source
                        try:
                            current_cursor.execute("""
                                INSERT INTO sources (name, type, link_sources, importance, country, city, description, accounts, note, ownership, date_entry, date_creation, date_modified)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (name, source_type, link_sources, importance, country, city, description, accounts, note, ownership, date_entry, date_creation, date_modified))
                            new_id = current_cursor.lastrowid
                            sources_id_map[old_id] = new_id
                            sources_added += 1
                        except sqlite3.IntegrityError as e:
                            # Handle UNIQUE constraint violation (shouldn't happen, but just in case)
                            if 'UNIQUE constraint' in str(e) and 'name' in str(e):
                                # Source with same name was inserted between our check and insert
                                # Find it and use its ID
                                current_cursor.execute("SELECT id FROM sources WHERE name = ?", (name,))
                                existing_id = current_cursor.fetchone()
                                if existing_id:
                                    sources_id_map[old_id] = existing_id[0]
                                    sources_skipped += 1
                                    logger.warning(f"Source '{name}' was inserted concurrently, using existing ID")
                                else:
                                    raise
                            else:
                                raise
            
            logger.info(f"Merged sources: {sources_added} added, {sources_skipped} skipped")
            
            # Step 2: Merge contents table (schema-compatible: with or without title)
            contents_cols = schema['contents']
            has_title = 'title' in contents_cols
            if has_title:
                backup_cursor.execute("SELECT id, title, content_data, attachments, note, importance, date_content, date_creation, date_modified, sources_id FROM contents")
            else:
                backup_cursor.execute("SELECT id, content_data, attachments, note, importance, date_content, date_creation, date_modified, sources_id FROM contents")
            backup_contents = backup_cursor.fetchall()
            
            contents_added = 0
            contents_skipped = 0
            
            for row in backup_contents:
                if has_title:
                    old_id, title, content_data, attachments, note, importance, date_content, date_creation, date_modified, old_sources_id = row
                else:
                    old_id, content_data, attachments, note, importance, date_content, date_creation, date_modified, old_sources_id = row
                    title = None
                # Map old sources_id to new sources_id
                new_sources_id = sources_id_map.get(old_sources_id)
                if new_sources_id is None:
                    logger.warning(f"Skipping content {old_id}: source {old_sources_id} not found in mapping")
                    continue
                
                # Prepare data dict for duplicate checking (all fields including dates)
                content_data_dict = {
                    'title': title,
                    'content_data': content_data,
                    'attachments': attachments,
                    'note': note,
                    'importance': importance,
                    'date_content': date_content,
                    'date_creation': date_creation,
                    'date_modified': date_modified,
                    'sources_id': new_sources_id
                }
                
                # Check for duplicate using all fields
                is_duplicate, existing = DuplicateDetector.check_duplicate('contents', content_data_dict)
                
                if is_duplicate:
                    # Content already exists, use existing ID
                    contents_id_map[old_id] = existing.get('id')
                    contents_skipped += 1
                else:
                    # Insert content with new sources_id
                    current_cursor.execute("""
                        INSERT INTO contents (title, content_data, attachments, note, importance, date_content, date_creation, date_modified, sources_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (title, content_data, attachments, note, importance, date_content, date_creation, date_modified, new_sources_id))
                    new_id = current_cursor.lastrowid
                    contents_id_map[old_id] = new_id
                    contents_added += 1
            
            logger.info(f"Merged contents: {contents_added} added, {contents_skipped} skipped")
            
            # Step 3: Merge content_analysis table (schema-compatible: coordinates vs list_coordinates)
            ca_cols = schema['content_analysis']
            coord_col = 'list_coordinates' if 'list_coordinates' in ca_cols else 'coordinates'
            backup_cursor.execute(f"SELECT id, content_id, list_names_people, list_names_places, {coord_col}, classification, list_sides, date_analysis, date_creation, date_modified FROM content_analysis")
            backup_analyses = backup_cursor.fetchall()
            
            analyses_added = 0
            analyses_skipped = 0
            
            for row in backup_analyses:
                old_id, old_content_id, list_names_people, list_names_places, list_coordinates, classification, list_sides, date_analysis, date_creation, date_modified = row
                # Map old content_id to new content_id
                new_content_id = contents_id_map.get(old_content_id)
                if new_content_id is None:
                    logger.warning(f"Skipping analysis {old_id}: content {old_content_id} not found in mapping")
                    continue
                
                # Prepare data dict for duplicate checking (all fields including dates)
                analysis_data = {
                    'content_id': new_content_id,
                    'list_names_people': list_names_people,
                    'list_names_places': list_names_places,
                    'list_coordinates': list_coordinates,
                    'classification': classification,
                    'list_sides': list_sides,
                    'date_analysis': date_analysis,
                    'date_creation': date_creation,
                    'date_modified': date_modified
                }
                
                # Check for duplicate using all fields
                is_duplicate, existing = DuplicateDetector.check_duplicate('content_analysis', analysis_data)
                
                if is_duplicate:
                    # Analysis already exists, skip it
                    analyses_skipped += 1
                else:
                    # Insert analysis with new content_id
                    current_cursor.execute("""
                        INSERT INTO content_analysis (content_id, list_names_people, list_names_places, list_coordinates, classification, list_sides, date_analysis, date_creation, date_modified)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (new_content_id, list_names_people, list_names_places, list_coordinates, classification, list_sides, date_analysis, date_creation, date_modified))
                    analyses_added += 1
            
            logger.info(f"Merged content_analysis: {analyses_added} added, {analyses_skipped} skipped")
            
            # Single commit - all or nothing
            current_conn.commit()
            
            # Close backup connection
            backup_conn.close()
            
            return True
        
        except Exception as e:
            logger.error(f"Error merging SQLite backup: {e}")
            # Rollback transaction if we started one
            try:
                current_conn = DatabaseConfig.get_connection()
                current_conn.rollback()
            except Exception:
                pass
            if backup_conn:
                try:
                    backup_conn.close()
                except Exception:
                    pass
            return False
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _encrypt_backup(self, backup_path: Path) -> Optional[Path]:
        """Encrypt backup file"""
        # Simple encryption using Fernet (requires cryptography library)
        try:
            from cryptography.fernet import Fernet
            
            key = self.config.get('Backup', 'encryption_key', '')
            if not key:
                # Generate key if not exists
                key = Fernet.generate_key().decode()
                self.config.set('Backup', 'encryption_key', key)
            
            fernet = Fernet(key.encode())
            
            encrypted_path = backup_path.with_suffix('.enc')
            
            with open(backup_path, 'rb') as f:
                encrypted_data = fernet.encrypt(f.read())
            
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Delete original
            backup_path.unlink()
            
            return encrypted_path
        
        except ImportError:
            logger.warning("cryptography library not available, encryption skipped")
            return None
        except Exception as e:
            logger.error(f"Error encrypting backup: {e}")
            return None
    
    def _decrypt_backup(self, encrypted_path: Path) -> Optional[Path]:
        """Decrypt backup file"""
        try:
            from cryptography.fernet import Fernet
            
            key = self.config.get('Backup', 'encryption_key', '')
            if not key:
                return None
            
            fernet = Fernet(key.encode())
            
            decrypted_path = encrypted_path.with_suffix('.sqlite')
            
            with open(encrypted_path, 'rb') as f:
                decrypted_data = fernet.decrypt(f.read())
            
            with open(decrypted_path, 'wb') as f:
                f.write(decrypted_data)
            
            return decrypted_path
        
        except ImportError:
            logger.warning("cryptography library not available, decryption skipped")
            return None
        except Exception as e:
            logger.error(f"Error decrypting backup: {e}")
            return None
    
    def _record_backup(self, backup_info: Dict):
        """Record backup info (optional - can store in JSON file)"""
        try:
            # Store backup metadata in JSON file
            metadata_file = self.backup_dir / 'backup_metadata.json'
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            backup_path = backup_info['backup_path']
            metadata[backup_path] = backup_info
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error recording backup: {e}")
    
    def _get_backup_info(self, backup_path: Path) -> Optional[Dict]:
        """Get backup info from metadata file"""
        try:
            metadata_file = self.backup_dir / 'backup_metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    return metadata.get(str(backup_path))
            return None
        except Exception as e:
            logger.error(f"Error getting backup info: {e}")
            return None
