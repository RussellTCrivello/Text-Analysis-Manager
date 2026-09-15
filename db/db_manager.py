"""
Database manager module
Handles all database operations (CRUD) for all tables
SQLite version for single-file EXE packaging
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any
from .db_config import DatabaseConfig
from utils.duplicate_detector import DuplicateDetector
from utils.data_validation import get_validator


class DatabaseManager:
    """Manages all database operations"""

    # The advanced-search dialog builds values from these tables and fields,
    # but the method is also part of the database-facing API. Keep the
    # identifiers whitelisted so a malformed saved search cannot turn into
    # executable SQL.
    _ADVANCED_SEARCH_FIELDS = {
        'sources': {
            'id', 'name', 'type', 'link_sources', 'importance', 'country',
            'city', 'description', 'accounts', 'note', 'ownership',
            'date_entry', 'date_creation', 'date_modified',
        },
        'contents': {
            'id', 'title', 'content_data', 'attachments', 'note', 'importance',
            'date_content', 'date_creation', 'date_modified', 'sources_id',
        },
        'content_analysis': {
            'id', 'content_id', 'list_names_people', 'list_names_places',
            'list_coordinates', 'coordinates', 'classification', 'list_sides',
            'date_analysis', 'date_creation', 'date_modified',
        },
    }
    _ADVANCED_SEARCH_OPERATORS = {
        '=', '!=', 'LIKE', 'NOT LIKE', '>', '<', '>=', '<=',
        'IS NULL', 'IS NOT NULL',
    }

    @staticmethod
    def _validate_payload(table_name: str, data: Dict):
        """Apply the shared backend validation schema before database writes."""
        if not isinstance(data, dict):
            raise ValueError(f"{table_name} data must be a dictionary")
        is_valid, errors = get_validator().validate(table_name, data)
        if not is_valid:
            raise ValueError(f"Invalid {table_name} data: {'; '.join(errors)}")

        # Validate foreign-key references before attempting the write so callers
        # receive a deterministic validation error instead of a low-level
        # sqlite3.IntegrityError wrapped as a generic database exception.
        if table_name == 'contents' and data.get('sources_id') is not None:
            if not DatabaseManager.get_source_by_id(data.get('sources_id')):
                raise ValueError(
                    f"Invalid {table_name} data: source does not exist"
                )
        elif table_name == 'content_analysis' and data.get('content_id') is not None:
            if not DatabaseManager.get_content_by_id(data.get('content_id')):
                raise ValueError(
                    f"Invalid {table_name} data: content does not exist"
                )
    
    @staticmethod
    def execute_query(query: str, params: tuple = None, fetch: bool = True) -> List[Dict]:
        """Execute a query and return results as list of dictionaries"""
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                results = cursor.fetchall()
                # Convert Row objects to dictionaries
                return [dict(row) for row in results]
            else:
                conn.commit()
                return []
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise Exception(f"Database error: {e}")
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
    
    # ========== SOURCES TABLE OPERATIONS ==========
    
    @staticmethod
    def get_all_sources() -> List[Dict]:
        """Get all sources"""
        query = "SELECT * FROM sources ORDER BY date_creation DESC"
        return DatabaseManager.execute_query(query)
    
    @staticmethod
    def get_source_by_id(source_id: int) -> Optional[Dict]:
        """Get source by ID"""
        query = "SELECT * FROM sources WHERE id = ?"
        results = DatabaseManager.execute_query(query, (source_id,))
        return results[0] if results else None
    
    @staticmethod
    def add_source(data: Dict) -> int:
        """Add a new source - validates and checks for duplicates before inserting"""
        DatabaseManager._validate_payload('sources', data)
        # Check for duplicate
        is_duplicate, existing = DuplicateDetector.check_duplicate('sources', data)
        if is_duplicate:
            raise Exception(f"Duplicate source found. A source with the same data already exists (ID: {existing.get('id')})")
        
        query = """
        INSERT INTO sources (name, type, link_sources, importance, country, city, 
                           description, accounts, note, ownership, date_entry, date_creation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data.get('name'),
            data.get('type'),
            data.get('link_sources'),
            data.get('importance', 0.0),
            data.get('country'),
            data.get('city'),
            data.get('description'),
            data.get('accounts'),
            data.get('note'),
            data.get('ownership'),
            data.get('date_entry'),
            data.get('date_creation') or datetime.now()
        )
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise Exception(f"Error adding source: {e}")
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
    
    @staticmethod
    def update_source(source_id: int, data: Dict) -> bool:
        """Update a source after validating its complete payload."""
        DatabaseManager._validate_payload('sources', data)
        query = """
        UPDATE sources SET name = ?, type = ?, link_sources = ?, importance = ?,
                          country = ?, city = ?, description = ?, accounts = ?,
                          note = ?, ownership = ?, date_entry = ?
        WHERE id = ?
        """
        params = (
            data.get('name'),
            data.get('type'),
            data.get('link_sources'),
            data.get('importance', 0.0),
            data.get('country'),
            data.get('city'),
            data.get('description'),
            data.get('accounts'),
            data.get('note'),
            data.get('ownership'),
            data.get('date_entry'),
            source_id
        )
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise Exception(f"Error updating source: {e}")
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
    
    @staticmethod
    def delete_source(source_id: int) -> bool:
        """Delete a source (cascade will delete related contents)"""
        query = "DELETE FROM sources WHERE id = ?"
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (source_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise Exception(f"Error deleting source: {e}")
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
    
    @staticmethod
    def search_sources(search_term: str) -> List[Dict]:
        """Search sources by name, type, country, or description"""
        query = """
        SELECT * FROM sources 
        WHERE name LIKE ? OR type LIKE ? OR country LIKE ? 
           OR description LIKE ? OR city LIKE ?
        ORDER BY date_creation DESC
        """
        search_pattern = f"%{search_term}%"
        return DatabaseManager.execute_query(query, (search_pattern, search_pattern, 
                                                      search_pattern, search_pattern, search_pattern))
    
    # ========== CONTENTS TABLE OPERATIONS ==========
    
    @staticmethod
    def get_all_contents() -> List[Dict]:
        """Get all contents with source name"""
        query = """
        SELECT c.*, s.name as source_name 
        FROM contents c
        LEFT JOIN sources s ON c.sources_id = s.id
        ORDER BY c.date_creation DESC
        """
        return DatabaseManager.execute_query(query)
    
    @staticmethod
    def get_content_by_id(content_id: int) -> Optional[Dict]:
        """Get content by ID"""
        query = """
        SELECT c.*, s.name as source_name 
        FROM contents c
        LEFT JOIN sources s ON c.sources_id = s.id
        WHERE c.id = ?
        """
        results = DatabaseManager.execute_query(query, (content_id,))
        return results[0] if results else None
    
    @staticmethod
    def add_content(data: Dict) -> int:
        """Add new content after validation and duplicate checks."""
        DatabaseManager._validate_payload('contents', data)
        # Check for duplicate
        is_duplicate, existing = DuplicateDetector.check_duplicate('contents', data)
        if is_duplicate:
            raise Exception(f"Duplicate content found. A content with the same data already exists (ID: {existing.get('id')})")
        
        query = """
        INSERT INTO contents (title, content_data, attachments, note, importance, 
                            date_content, date_creation, sources_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data.get('title'),
            data.get('content_data'),
            data.get('attachments'),
            data.get('note'),
            data.get('importance', 0.0),
            data.get('date_content'),
            data.get('date_creation') or datetime.now(),
            data.get('sources_id')
        )
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise Exception(f"Error adding content: {e}")
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
    
    @staticmethod
    def update_content(content_id: int, data: Dict) -> bool:
        """Update content after validating its complete payload."""
        DatabaseManager._validate_payload('contents', data)
        query = """
        UPDATE contents SET title = ?, content_data = ?, attachments = ?, note = ?,
                           importance = ?, date_content = ?, sources_id = ?
        WHERE id = ?
        """
        params = (
            data.get('title'),
            data.get('content_data'),
            data.get('attachments'),
            data.get('note'),
            data.get('importance', 0.0),
            data.get('date_content'),
            data.get('sources_id'),
            content_id
        )
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise Exception(f"Error updating content: {e}")
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
    
    @staticmethod
    def delete_content(content_id: int) -> bool:
        """Delete a content (cascade will delete related analysis)"""
        query = "DELETE FROM contents WHERE id = ?"
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (content_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise Exception(f"Error deleting content: {e}")
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
    
    @staticmethod
    def search_contents(search_term: str) -> List[Dict]:
        """Search contents by content_data, note, or source name"""
        query = """
        SELECT c.*, s.name as source_name 
        FROM contents c
        LEFT JOIN sources s ON c.sources_id = s.id
        WHERE c.content_data LIKE ? OR c.note LIKE ? OR s.name LIKE ?
        ORDER BY c.date_creation DESC
        """
        search_pattern = f"%{search_term}%"
        return DatabaseManager.execute_query(query, (search_pattern, search_pattern, search_pattern))
    
    # ========== CONTENT_ANALYSIS TABLE OPERATIONS ==========
    
    @staticmethod
    def get_all_content_analysis() -> List[Dict]:
        """Get all content analysis with content and source info - includes ALL fields"""
        query = """
        SELECT 
            ca.id,
            ca.content_id,
            ca.list_names_people,
            ca.list_names_places,
            ca.list_coordinates as coordinates,
            ca.classification,
            ca.list_sides,
            ca.date_analysis,
            ca.date_creation,
            ca.date_modified,
            c.id as content_table_id,
            c.title as content_title,
            c.content_data,
            c.attachments as content_attachments,
            c.note as content_note,
            c.importance as content_importance,
            c.date_content,
            c.date_creation as content_date_creation,
            c.date_modified as content_date_modified,
            c.sources_id,
            s.id as source_table_id,
            s.name as source_name,
            s.type as source_type,
            s.link_sources as source_link,
            s.importance as source_importance,
            s.country as source_country,
            s.city as source_city,
            s.description as source_description,
            s.accounts as source_accounts,
            s.note as source_note,
            s.ownership as source_ownership,
            s.date_entry as source_date_entry,
            s.date_creation as source_date_creation,
            s.date_modified as source_date_modified
        FROM content_analysis ca
        LEFT JOIN contents c ON ca.content_id = c.id
        LEFT JOIN sources s ON c.sources_id = s.id
        ORDER BY ca.id DESC
        """
        return DatabaseManager.execute_query(query)
    
    @staticmethod
    def get_analysis_by_id(analysis_id: int) -> Optional[Dict]:
        """Get analysis by ID - includes ALL fields with proper aliasing"""
        query = """
        SELECT 
            ca.id,
            ca.content_id,
            ca.list_names_people,
            ca.list_names_places,
            ca.list_coordinates as coordinates,
            ca.classification,
            ca.list_sides,
            ca.date_analysis,
            ca.date_creation,
            ca.date_modified,
            c.content_data,
            c.date_content,
            s.name as source_name
        FROM content_analysis ca
        LEFT JOIN contents c ON ca.content_id = c.id
        LEFT JOIN sources s ON c.sources_id = s.id
        WHERE ca.id = ?
        """
        results = DatabaseManager.execute_query(query, (analysis_id,))
        return results[0] if results else None
    
    @staticmethod
    def add_content_analysis(data: Dict) -> int:
        """Add analysis after validation and duplicate checks."""
        DatabaseManager._validate_payload('content_analysis', data)
        # Check for duplicate
        is_duplicate, existing = DuplicateDetector.check_duplicate('content_analysis', data)
        if is_duplicate:
            raise Exception(f"Duplicate content analysis found. An analysis with the same data already exists (ID: {existing.get('id')})")
        
        query = """
        INSERT INTO content_analysis (content_id, list_names_people, list_names_places,
                                     list_coordinates, classification, list_sides,
                                     date_analysis, date_creation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data.get('content_id'),
            data.get('list_names_people'),
            data.get('list_names_places'),
            data.get('coordinates', data.get('list_coordinates')),  # API uses either alias
            data.get('classification'),
            data.get('list_sides'),
            data.get('date_analysis') or datetime.now(),
            data.get('date_creation') or datetime.now(),
        )
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise Exception(f"Error adding content analysis: {e}")
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
    
    @staticmethod
    def update_content_analysis(analysis_id: int, data: Dict) -> bool:
        """Update analysis after validating its complete payload."""
        DatabaseManager._validate_payload('content_analysis', data)
        query = """
        UPDATE content_analysis SET content_id = ?, list_names_people = ?,
                                  list_names_places = ?, list_coordinates = ?,
                                  classification = ?, list_sides = ?
        WHERE id = ?
        """
        params = (
            data.get('content_id'),
            data.get('list_names_people'),
            data.get('list_names_places'),
            data.get('coordinates', data.get('list_coordinates')),  # API uses either alias
            data.get('classification'),
            data.get('list_sides'),
            analysis_id
        )
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise Exception(f"Error updating content analysis: {e}")
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
    
    @staticmethod
    def delete_content_analysis(analysis_id: int) -> bool:
        """Delete a content analysis"""
        query = "DELETE FROM content_analysis WHERE id = ?"
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (analysis_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise Exception(f"Error deleting content analysis: {e}")
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
    
    @staticmethod
    def search_content_analysis(search_term: str) -> List[Dict]:
        """Search content analysis by various fields"""
        query = """
        SELECT ca.*, c.content_data, c.date_content, s.name as source_name
        FROM content_analysis ca
        LEFT JOIN contents c ON ca.content_id = c.id
        LEFT JOIN sources s ON c.sources_id = s.id
        WHERE ca.list_names_people LIKE ? OR ca.list_names_places LIKE ?
           OR ca.classification LIKE ? OR ca.list_sides LIKE ?
           OR c.content_data LIKE ?
        ORDER BY ca.id DESC
        """
        search_pattern = f"%{search_term}%"
        return DatabaseManager.execute_query(query, (search_pattern, search_pattern, 
                                                      search_pattern, search_pattern, search_pattern))
    
    @staticmethod
    def get_all_content_ids() -> List[Dict]:
        """Get all content IDs and basic info for dropdowns"""
        query = "SELECT id, SUBSTR(content_data, 1, 100) as preview FROM contents ORDER BY id DESC"
        return DatabaseManager.execute_query(query)
    
    # ========== UNIFIED QUERY OPERATIONS ==========
    
    @staticmethod
    def get_all_data_unified() -> List[Dict]:
        """Get all data from all tables in a unified format
        
        This creates a comprehensive view joining sources, contents, and content_analysis
        Each row represents a complete data record with all related information
        """
        query = """
        SELECT 
            -- Source fields (ALL fields)
            s.id as source_id,
            s.name as source_name,
            s.type as source_type,
            s.link_sources as source_link,
            s.importance as source_importance,
            s.country as source_country,
            s.city as source_city,
            s.description as source_description,
            s.accounts as source_accounts,
            s.note as source_note,
            s.ownership as source_ownership,
            s.date_entry as source_date_entry,
            s.date_creation as source_date_creation,
            s.date_modified as source_date_modified,
            
            -- Content fields (ALL fields)
            c.id as content_id,
            c.title as content_title,
            c.content_data,
            c.attachments as content_attachments,
            c.note as content_note,
            c.importance as content_importance,
            c.date_content,
            c.date_creation as content_date_creation,
            c.date_modified as content_date_modified,
            c.sources_id,
            
            -- Analysis fields (ALL fields)
            ca.id as analysis_id,
            ca.content_id as analysis_content_id,
            ca.classification,
            ca.list_names_people,
            ca.list_names_places,
            ca.list_coordinates as coordinates,
            ca.list_sides,
            ca.date_analysis,
            ca.date_creation as analysis_date_creation,
            ca.date_modified as analysis_date_modified,
            
            -- Record type indicator
            CASE 
                WHEN ca.id IS NOT NULL THEN 'analysis'
                WHEN c.id IS NOT NULL THEN 'content'
                ELSE 'source'
            END as record_type
            
        FROM sources s
        LEFT JOIN contents c ON c.sources_id = s.id
        LEFT JOIN content_analysis ca ON ca.content_id = c.id
        
        ORDER BY 
            COALESCE(ca.date_creation, c.date_creation, s.date_creation) DESC,
            s.id DESC,
            c.id DESC,
            ca.id DESC
        """
        return DatabaseManager.execute_query(query)
    
    @staticmethod
    def get_timeline_events() -> List[Dict]:
        """Get all events for timeline display
        
        Returns events from sources, contents, and content_analysis
        ordered chronologically by their date fields
        """
        query = """
        SELECT 
            -- Source fields
            s.id as source_id,
            s.name as source_name,
            s.type as source_type,
            s.link_sources as source_link,
            s.importance as source_importance,
            s.country as source_country,
            s.city as source_city,
            s.description as source_description,
            s.accounts as source_accounts,
            s.note as source_note,
            s.ownership as source_ownership,
            s.date_entry as source_date_entry,
            s.date_creation as source_date_creation,
            s.date_modified as source_date_modified,
            
            -- Content fields
            c.id as content_id,
            c.title as content_title,
            c.content_data,
            c.attachments as content_attachments,
            c.note as content_note,
            c.importance as content_importance,
            c.date_content,
            c.date_creation as content_date_creation,
            c.date_modified as content_date_modified,
            c.sources_id,
            
            -- Analysis fields
            ca.id as analysis_id,
            ca.content_id as analysis_content_id,
            ca.classification,
            ca.list_names_people,
            ca.list_names_places,
            ca.list_coordinates as coordinates,
            ca.list_sides,
            ca.date_analysis,
            ca.date_creation as analysis_date_creation,
            ca.date_modified as analysis_date_modified,
            
            -- Record type indicator
            CASE 
                WHEN ca.id IS NOT NULL THEN 'analysis'
                WHEN c.id IS NOT NULL THEN 'content'
                ELSE 'source'
            END as record_type,
            
            -- Primary date for sorting (prefer content/analysis dates over creation dates)
            COALESCE(
                ca.date_analysis,
                c.date_content,
                s.date_entry,
                ca.date_creation,
                c.date_creation,
                s.date_creation
            ) as timeline_date
            
        FROM sources s
        LEFT JOIN contents c ON c.sources_id = s.id
        LEFT JOIN content_analysis ca ON ca.content_id = c.id
        
        -- Only include records that have a date
        WHERE COALESCE(
            ca.date_analysis,
            c.date_content,
            s.date_entry,
            ca.date_creation,
            c.date_creation,
            s.date_creation
        ) IS NOT NULL
        
        ORDER BY timeline_date DESC
        """
        return DatabaseManager.execute_query(query)
    
    @staticmethod
    def search_all_data_unified(search_term: str) -> List[Dict]:
        """Search across all unified data"""
        if not search_term:
            return DatabaseManager.get_all_data_unified()
        
        query = """
        SELECT 
            -- Source fields (ALL fields)
            s.id as source_id,
            s.name as source_name,
            s.type as source_type,
            s.link_sources as source_link,
            s.importance as source_importance,
            s.country as source_country,
            s.city as source_city,
            s.description as source_description,
            s.accounts as source_accounts,
            s.note as source_note,
            s.ownership as source_ownership,
            s.date_entry as source_date_entry,
            s.date_creation as source_date_creation,
            s.date_modified as source_date_modified,
            
            -- Content fields (ALL fields)
            c.id as content_id,
            c.title as content_title,
            c.content_data,
            c.attachments as content_attachments,
            c.note as content_note,
            c.importance as content_importance,
            c.date_content,
            c.date_creation as content_date_creation,
            c.date_modified as content_date_modified,
            c.sources_id,
            
            -- Analysis fields (ALL fields)
            ca.id as analysis_id,
            ca.content_id as analysis_content_id,
            ca.classification,
            ca.list_names_people,
            ca.list_names_places,
            ca.list_coordinates as coordinates,
            ca.list_sides,
            ca.date_analysis,
            ca.date_creation as analysis_date_creation,
            ca.date_modified as analysis_date_modified,
            
            -- Record type indicator
            CASE 
                WHEN ca.id IS NOT NULL THEN 'analysis'
                WHEN c.id IS NOT NULL THEN 'content'
                ELSE 'source'
            END as record_type
            
        FROM sources s
        LEFT JOIN contents c ON c.sources_id = s.id
        LEFT JOIN content_analysis ca ON ca.content_id = c.id
        
        WHERE 
            s.name LIKE ? OR s.type LIKE ? OR s.country LIKE ? OR s.city LIKE ? 
            OR s.description LIKE ? OR s.note LIKE ? OR s.accounts LIKE ?
            OR c.content_data LIKE ? OR c.note LIKE ? OR c.title LIKE ?
            OR ca.classification LIKE ? OR ca.list_names_people LIKE ? 
            OR ca.list_names_places LIKE ? OR ca.list_sides LIKE ?
        
        ORDER BY 
            COALESCE(ca.date_creation, c.date_creation, s.date_creation) DESC,
            s.id DESC,
            c.id DESC,
            ca.id DESC
        """
        search_pattern = f"%{search_term}%"
        return DatabaseManager.execute_query(query, (
            search_pattern, search_pattern, search_pattern, search_pattern,
            search_pattern, search_pattern, search_pattern,
            search_pattern, search_pattern, search_pattern,
            search_pattern, search_pattern, search_pattern, search_pattern
        ))
    
    # ========== FULL-TEXT SEARCH OPERATIONS ==========
    # Note: SQLite FTS is different from PostgreSQL. Using LIKE for compatibility.
    
    @staticmethod
    def full_text_search_sources(search_term: str) -> List[Dict]:
        """Full-text search in sources (using LIKE for SQLite compatibility)"""
        query = """
        SELECT *, 1 as rank
        FROM sources
        WHERE name LIKE ? OR description LIKE ? OR note LIKE ?
        ORDER BY date_creation DESC
        """
        search_pattern = f"%{search_term}%"
        return DatabaseManager.execute_query(query, (search_pattern, search_pattern, search_pattern))
    
    @staticmethod
    def full_text_search_contents(search_term: str) -> List[Dict]:
        """Full-text search in contents (using LIKE for SQLite compatibility)"""
        query = """
        SELECT c.*, s.name as source_name, 1 as rank
        FROM contents c
        LEFT JOIN sources s ON c.sources_id = s.id
        WHERE c.content_data LIKE ? OR c.note LIKE ?
        ORDER BY c.date_creation DESC
        """
        search_pattern = f"%{search_term}%"
        return DatabaseManager.execute_query(query, (search_pattern, search_pattern))
    
    # ========== ADVANCED SEARCH OPERATIONS ==========
    
    @staticmethod
    def advanced_search(table_name: str, conditions: Dict[str, Any]) -> List[Dict]:
        """Advanced search with multiple conditions
        
        conditions format:
        {
            'field1': {'operator': '=', 'value': 'value1'},
            'field2': {'operator': '>', 'value': 100},
            'field3': {'operator': 'LIKE', 'value': '%pattern%'},
            'logic': 'AND' or 'OR'
        }
        """
        if table_name not in DatabaseManager._ADVANCED_SEARCH_FIELDS:
            raise ValueError(f"Unsupported table for advanced search: {table_name}")
        if not isinstance(conditions, dict):
            raise ValueError("Search conditions must be a dictionary")

        where_clauses = []
        params = []
        logic = str(conditions.get('logic', 'AND')).upper()
        if logic not in {'AND', 'OR'}:
            raise ValueError("Search logic must be AND or OR")

        allowed_fields = DatabaseManager._ADVANCED_SEARCH_FIELDS[table_name]
        for raw_field, condition in conditions.items():
            if raw_field == 'logic':
                continue
            if not isinstance(condition, dict):
                raise ValueError(f"Invalid condition for field: {raw_field}")

            # The visual dialog uses suffixes when the same field is added
            # more than once (for example, name and name__condition_2).
            # Strip only that internal suffix before validating the SQL
            # identifier.
            field = str(raw_field).split('__condition_', 1)[0]
            if field not in allowed_fields:
                raise ValueError(f"Unsupported search field: {field}")

            operator = str(condition.get('operator', '=')).upper()
            if operator not in DatabaseManager._ADVANCED_SEARCH_OPERATORS:
                raise ValueError(f"Unsupported search operator: {operator}")

            # The public API historically exposed both names for the
            # coordinates field; the current schema stores list_coordinates.
            sql_field = (
                'list_coordinates'
                if table_name == 'content_analysis' and field == 'coordinates'
                else field
            )
            value = condition.get('value')
            if operator in {'IS NULL', 'IS NOT NULL'}:
                where_clauses.append(f"{sql_field} {operator}")
            elif value is not None:
                where_clauses.append(f"{sql_field} {operator} ?")
                params.append(value)

        if not where_clauses:
            return []

        where_clause = f" {logic} ".join(where_clauses)
        query = f"SELECT * FROM {table_name} WHERE {where_clause}"
        return DatabaseManager.execute_query(query, tuple(params))

    # ========== AUTOCOMPLETE OPERATIONS ==========
    
    @staticmethod
    def get_distinct_source_types() -> List[str]:
        """Get all distinct source types for autocomplete"""
        query = "SELECT DISTINCT type FROM sources WHERE type IS NOT NULL AND type != '' ORDER BY type"
        results = DatabaseManager.execute_query(query)
        return [r['type'] for r in results]
    
    @staticmethod
    def get_distinct_countries() -> List[str]:
        """Get all distinct countries for autocomplete"""
        query = "SELECT DISTINCT country FROM sources WHERE country IS NOT NULL AND country != '' ORDER BY country"
        results = DatabaseManager.execute_query(query)
        return [r['country'] for r in results]
    
    @staticmethod
    def get_distinct_cities() -> List[str]:
        """Get all distinct cities for autocomplete"""
        query = "SELECT DISTINCT city FROM sources WHERE city IS NOT NULL AND city != '' ORDER BY city"
        results = DatabaseManager.execute_query(query)
        return [r['city'] for r in results]
    
    @staticmethod
    def get_distinct_ownership() -> List[str]:
        """Get all distinct ownership values for autocomplete"""
        query = "SELECT DISTINCT ownership FROM sources WHERE ownership IS NOT NULL AND ownership != '' ORDER BY ownership"
        results = DatabaseManager.execute_query(query)
        return [r['ownership'] for r in results]
    
    @staticmethod
    def get_distinct_classifications() -> List[str]:
        """Get all distinct classifications for autocomplete"""
        query = "SELECT DISTINCT classification FROM content_analysis WHERE classification IS NOT NULL AND classification != '' ORDER BY classification"
        results = DatabaseManager.execute_query(query)
        return [r['classification'] for r in results]
    
    @staticmethod
    def get_distinct_people() -> List[str]:
        """Get all distinct people names for autocomplete"""
        query = "SELECT DISTINCT list_names_people FROM content_analysis WHERE list_names_people IS NOT NULL AND list_names_people != ''"
        results = DatabaseManager.execute_query(query)
        # Parse comma-separated names
        all_names = set()
        for r in results:
            names = r['list_names_people'].split(',')
            for name in names:
                name = name.strip()
                if name:
                    all_names.add(name)
        return sorted(list(all_names))
    
    @staticmethod
    def get_distinct_places() -> List[str]:
        """Get all distinct place names for autocomplete"""
        query = "SELECT DISTINCT list_names_places FROM content_analysis WHERE list_names_places IS NOT NULL AND list_names_places != ''"
        results = DatabaseManager.execute_query(query)
        # Parse comma-separated places
        all_places = set()
        for r in results:
            places = r['list_names_places'].split(',')
            for place in places:
                place = place.strip()
                if place:
                    all_places.add(place)
        return sorted(list(all_places))
    
    @staticmethod
    def get_distinct_sides() -> List[str]:
        """Get all distinct sides for autocomplete"""
        query = "SELECT DISTINCT list_sides FROM content_analysis WHERE list_sides IS NOT NULL AND list_sides != ''"
        results = DatabaseManager.execute_query(query)
        # Parse comma-separated sides
        all_sides = set()
        for r in results:
            sides = r['list_sides'].split(',')
            for side in sides:
                side = side.strip()
                if side:
                    all_sides.add(side)
        return sorted(list(all_sides))