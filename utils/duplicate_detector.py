"""
Duplicate Detection Utility
Checks for duplicate records across all fields for all tables
"""
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
from db.db_config import DatabaseConfig
from utils.logger import get_logger

logger = get_logger(__name__)


class DuplicateDetector:
    """Detects duplicate records across all fields"""
    
    # Only exclude 'id' - compare ALL other fields including dates for accurate duplicate detection
    # (date_creation, date_modified are meaningful - same content with different dates = different records)
    EXCLUDED_FIELDS = {'id'}
    
    @staticmethod
    def normalize_value(value: Any) -> Any:
        """Normalize a value for comparison (handle None, empty strings, whitespace)"""
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value if value else None
        if isinstance(value, (int, float)) and value == 0:
            return value  # Preserve 0 vs None distinction for numbers
        return value
    
    @staticmethod
    def _values_equal(val1: Any, val2: Any) -> bool:
        """Compare two values for equality, handling datetime/string variations"""
        v1 = DuplicateDetector.normalize_value(val1)
        v2 = DuplicateDetector.normalize_value(val2)
        if v1 is None and v2 is None:
            return True
        if v1 is None or v2 is None:
            return False
        # Normalize datetime strings for comparison (e.g. "2024-01-01 12:00:00" vs "2024-01-01T12:00:00")
        if isinstance(v1, str) and isinstance(v2, str) and ('-' in str(v1) or 'T' in str(v1)):
            s1 = str(v1).replace('T', ' ').split('.')[0]
            s2 = str(v2).replace('T', ' ').split('.')[0]
            return s1 == s2
        return v1 == v2
    
    @staticmethod
    def records_match(record1: Dict, record2: Dict, excluded_fields: set = None) -> bool:
        """Check if two records match on all non-excluded fields"""
        if excluded_fields is None:
            excluded_fields = DuplicateDetector.EXCLUDED_FIELDS
        
        # Compare the fields supplied by the candidate record.  New-record
        # payloads intentionally omit generated columns such as id and
        # timestamps; comparing the union of keys would make every such
        # candidate look different from an existing row.
        all_fields = set(record1.keys()) - excluded_fields
        
        # Check each candidate field (except excluded ones)
        for field in all_fields:
            if field in excluded_fields:
                continue
            
            val1 = record1.get(field)
            val2 = record2.get(field)
            
            # If values don't match, records are different (use _values_equal for date/datetime handling)
            if not DuplicateDetector._values_equal(val1, val2):
                return False
        
        # All non-excluded fields match
        return True
    
    @staticmethod
    def find_duplicate_source(data: Dict) -> Optional[Dict]:
        """Find duplicate source record by checking all fields"""
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            
            # Get all sources (include all fields for full comparison)
            cursor.execute("""
                SELECT id, name, type, link_sources, importance, country, city,
                       description, accounts, note, ownership, date_entry,
                       date_creation, date_modified
                FROM sources
            """)
            
            existing_sources = cursor.fetchall()
            
            # Convert to dictionaries (all fields for exact duplicate matching)
            for row in existing_sources:
                existing = {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'link_sources': row[3],
                    'importance': row[4],
                    'country': row[5],
                    'city': row[6],
                    'description': row[7],
                    'accounts': row[8],
                    'note': row[9],
                    'ownership': row[10],
                    'date_entry': row[11],
                    'date_creation': row[12],
                    'date_modified': row[13]
                }
                
                if DuplicateDetector.records_match(data, existing):
                    return existing
            
            return None
            
        except sqlite3.Error as e:
            logger.error(f"Error checking for duplicate source: {e}")
            return None
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
    
    @staticmethod
    def find_duplicate_content(data: Dict) -> Optional[Dict]:
        """Find duplicate content record by checking all fields"""
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            
            # Get all contents (include all fields for full comparison including dates)
            cursor.execute("""
                SELECT id, title, content_data, attachments, note, importance,
                       date_content, date_creation, date_modified, sources_id
                FROM contents
            """)
            
            existing_contents = cursor.fetchall()
            
            # Convert to dictionaries (all fields for exact duplicate matching)
            for row in existing_contents:
                existing = {
                    'id': row[0],
                    'title': row[1],
                    'content_data': row[2],
                    'attachments': row[3],
                    'note': row[4],
                    'importance': row[5],
                    'date_content': row[6],
                    'date_creation': row[7],
                    'date_modified': row[8],
                    'sources_id': row[9]
                }
                
                if DuplicateDetector.records_match(data, existing):
                    return existing
            
            return None
            
        except sqlite3.Error as e:
            logger.error(f"Error checking for duplicate content: {e}")
            return None
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
    
    @staticmethod
    def find_duplicate_content_analysis(data: Dict) -> Optional[Dict]:
        """Find duplicate content_analysis record by checking all fields"""
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            
            # Get all content_analysis (include all fields for full comparison including dates)
            cursor.execute("""
                SELECT id, content_id, list_names_people, list_names_places,
                       list_coordinates, classification, list_sides, date_analysis,
                       date_creation, date_modified
                FROM content_analysis
            """)
            
            existing_analyses = cursor.fetchall()
            
            # Convert to dictionaries (all fields for exact duplicate matching)
            for row in existing_analyses:
                existing = {
                    'id': row[0],
                    'content_id': row[1],
                    'list_names_people': row[2],
                    'list_names_places': row[3],
                    'list_coordinates': row[4],
                    'classification': row[5],
                    'list_sides': row[6],
                    'date_analysis': row[7],
                    'date_creation': row[8],
                    'date_modified': row[9]
                }
                
                # Map 'coordinates' to 'list_coordinates' for comparison
                data_copy = data.copy()
                if 'coordinates' in data_copy and 'list_coordinates' not in data_copy:
                    data_copy['list_coordinates'] = data_copy.pop('coordinates', None)
                
                if DuplicateDetector.records_match(data_copy, existing):
                    return existing
            
            return None
            
        except sqlite3.Error as e:
            logger.error(f"Error checking for duplicate content_analysis: {e}")
            return None
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
    
    @staticmethod
    def check_duplicate(table_name: str, data: Dict) -> Tuple[bool, Optional[Dict]]:
        """Check for duplicate record in specified table
        
        Returns:
            Tuple of (is_duplicate, existing_record)
        """
        if table_name == 'sources':
            existing = DuplicateDetector.find_duplicate_source(data)
            return existing is not None, existing
        elif table_name == 'contents':
            existing = DuplicateDetector.find_duplicate_content(data)
            return existing is not None, existing
        elif table_name == 'content_analysis':
            existing = DuplicateDetector.find_duplicate_content_analysis(data)
            return existing is not None, existing
        else:
            logger.warning(f"Unknown table name for duplicate check: {table_name}")
            return False, None
