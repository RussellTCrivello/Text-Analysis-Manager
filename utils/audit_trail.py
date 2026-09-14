"""
Audit Trail System
Tracks changes and actions in the database (without user roles)
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from db.db_config import DatabaseConfig
from utils.logger import get_logger

logger = get_logger(__name__)


class AuditTrail:
    """Audit trail manager"""
    
    @staticmethod
    def initialize():
        """Initialize audit trail table"""
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    record_id INTEGER,
                    field_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    action_description TEXT,
                    ip_address TEXT,
                    session_id TEXT
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_table_record 
                ON audit_trail(table_name, record_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
                ON audit_trail(timestamp)
            """)
            
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Error initializing audit trail: {e}")
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
    
    @staticmethod
    def log_action(action_type: str, table_name: str, record_id: Optional[int] = None,
                   field_name: Optional[str] = None, old_value: Optional[str] = None,
                   new_value: Optional[str] = None, description: Optional[str] = None):
        """Log an action to audit trail"""
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO audit_trail 
                (timestamp, action_type, table_name, record_id, field_name, 
                 old_value, new_value, action_description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                action_type,  # CREATE, UPDATE, DELETE, VIEW, EXPORT, etc.
                table_name,
                record_id,
                field_name,
                str(old_value)[:500] if old_value else None,  # Truncate long values
                str(new_value)[:500] if new_value else None,
                description
            ))
            
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Error logging audit trail: {e}")
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
    
    @staticmethod
    def log_create(table_name: str, record_id: int, data: Dict, description: str = None):
        """Log record creation"""
        AuditTrail.log_action(
            'CREATE',
            table_name,
            record_id,
            description=description or f"Created new {table_name} record"
        )
    
    @staticmethod
    def log_update(table_name: str, record_id: int, old_data: Dict, new_data: Dict, description: str = None):
        """Log record update with field-level changes"""
        changes = []
        for key in set(list(old_data.keys()) + list(new_data.keys())):
            old_val = old_data.get(key)
            new_val = new_data.get(key)
            if old_val != new_val:
                AuditTrail.log_action(
                    'UPDATE',
                    table_name,
                    record_id,
                    field_name=key,
                    old_value=old_val,
                    new_value=new_val,
                    description=description or f"Updated {table_name} record {record_id}"
                )
                changes.append(key)
        
        if not changes and description:
            # Log general update if no field changes detected
            AuditTrail.log_action(
                'UPDATE',
                table_name,
                record_id,
                description=description
            )
    
    @staticmethod
    def log_delete(table_name: str, record_id: int, data: Dict = None, description: str = None):
        """Log record deletion"""
        AuditTrail.log_action(
            'DELETE',
            table_name,
            record_id,
            old_value=str(data)[:500] if data else None,
            description=description or f"Deleted {table_name} record {record_id}"
        )
    
    @staticmethod
    def log_view(table_name: str, record_id: int = None, description: str = None):
        """Log record view"""
        AuditTrail.log_action(
            'VIEW',
            table_name,
            record_id,
            description=description or f"Viewed {table_name}" + (f" record {record_id}" if record_id else "")
        )
    
    @staticmethod
    def log_export(table_name: str, format: str, record_count: int, description: str = None):
        """Log export operation"""
        AuditTrail.log_action(
            'EXPORT',
            table_name,
            description=description or f"Exported {record_count} records to {format}"
        )
    
    @staticmethod
    def get_history(table_name: str = None, record_id: int = None, 
                   action_type: str = None, limit: int = 100) -> List[Dict]:
        """Get audit trail history"""
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM audit_trail WHERE 1=1"
            params = []
            
            if table_name:
                query += " AND table_name = ?"
                params.append(table_name)
            
            if record_id:
                query += " AND record_id = ?"
                params.append(record_id)
            
            if action_type:
                query += " AND action_type = ?"
                params.append(action_type)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in results]
            
        except sqlite3.Error as e:
            logger.error(f"Error getting audit trail: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
    
    @staticmethod
    def get_record_history(table_name: str, record_id: int) -> List[Dict]:
        """Get history for a specific record"""
        return AuditTrail.get_history(table_name=table_name, record_id=record_id)
    
    @staticmethod
    def clear_old_records(days: int = 90):
        """Clear audit trail records older than specified days"""
        conn = None
        try:
            conn = DatabaseConfig.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            from datetime import timedelta
            cutoff_date = cutoff_date - timedelta(days=days)
            
            cursor.execute("""
                DELETE FROM audit_trail 
                WHERE timestamp < ?
            """, (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Cleared {deleted_count} old audit trail records")
            return deleted_count
            
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Error clearing audit trail: {e}")
            return 0
        finally:
            if conn:
                cursor.close()
                DatabaseConfig.return_connection(conn)
