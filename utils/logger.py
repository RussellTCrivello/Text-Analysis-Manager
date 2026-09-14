"""
Comprehensive Logging System
Handles application logs, error logs, and database query logs
"""
import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional
from config.config_manager import get_config


class AppLogger:
    """Application-wide logging system"""
    
    def __init__(self):
        """Initialize logger"""
        self.config = get_config()
        # Use path_utils for correct log path when installed (AppData)
        from utils.path_utils import get_logs_dir
        self.log_dir = get_logs_dir()
        
        # Configure logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Get log level
        log_level = getattr(logging, self.config.get('Logging', 'level', 'INFO'), logging.INFO)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Console handler with UTF-8 encoding
        import sys
        import io
        if sys.platform == 'win32':
            # Ensure stdout/stderr use UTF-8 (handle None in compiled executables)
            if sys.stdout is not None and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            elif sys.stdout is not None and not hasattr(sys.stdout, 'encoding'):
                try:
                    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
                except (AttributeError, ValueError):
                    pass
            
            if sys.stderr is not None and hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8':
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
            elif sys.stderr is not None and not hasattr(sys.stderr, 'encoding'):
                try:
                    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
                except (AttributeError, ValueError):
                    pass
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(simple_formatter)
        # Set encoding for console output
        if hasattr(console_handler.stream, 'reconfigure'):
            try:
                console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
            except:
                pass
        root_logger.addHandler(console_handler)
        
        # Application log file handler
        if self.config.get('Logging', 'enabled', True):
            app_log_file = self.log_dir / "app.log"
            max_bytes = self.config.get('Logging', 'max_file_size', 10485760)  # 10MB
            backup_count = self.config.get('Logging', 'backup_count', 5)
            
            app_file_handler = logging.handlers.RotatingFileHandler(
                app_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            app_file_handler.setLevel(log_level)
            app_file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(app_file_handler)
        
        # Error log file handler
        if self.config.get('Logging', 'log_errors', True):
            error_log_file = self.log_dir / "errors.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(error_handler)
        
        # Database query log handler
        if self.config.get('Logging', 'log_database_queries', True):
            db_log_file = self.log_dir / "database.log"
            db_handler = logging.handlers.RotatingFileHandler(
                db_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            db_handler.setLevel(logging.DEBUG)
            db_handler.setFormatter(detailed_formatter)
            
            db_logger = logging.getLogger('database')
            db_logger.setLevel(logging.DEBUG)
            db_logger.addHandler(db_handler)
            db_logger.propagate = False
        
        # User actions log handler
        if self.config.get('Logging', 'log_user_actions', True):
            actions_log_file = self.log_dir / "user_actions.log"
            actions_handler = logging.handlers.RotatingFileHandler(
                actions_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            actions_handler.setLevel(logging.INFO)
            actions_handler.setFormatter(detailed_formatter)
            
            actions_logger = logging.getLogger('user_actions')
            actions_logger.setLevel(logging.INFO)
            actions_logger.addHandler(actions_handler)
            actions_logger.propagate = False
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get logger instance"""
        return logging.getLogger(name)
    
    @staticmethod
    def get_db_logger() -> logging.Logger:
        """Get database query logger"""
        return logging.getLogger('database')
    
    @staticmethod
    def get_actions_logger() -> logging.Logger:
        """Get user actions logger"""
        return logging.getLogger('user_actions')
    
    def log_error(self, error: Exception, context: str = ""):
        """Log error with context"""
        logger = logging.getLogger('app')
        logger.error(f"{context}: {str(error)}", exc_info=True)
    
    def log_user_action(self, action: str, details: dict = None):
        """Log user action"""
        logger = self.get_actions_logger()
        details_str = f" - {details}" if details else ""
        logger.info(f"USER_ACTION: {action}{details_str}")
    
    def log_database_query(self, query: str, params: tuple = None, duration: float = None):
        """Log database query"""
        logger = self.get_db_logger()
        params_str = f" | Params: {params}" if params else ""
        duration_str = f" | Duration: {duration:.3f}s" if duration else ""
        logger.debug(f"QUERY: {query}{params_str}{duration_str}")


# Global logger instance
_logger_instance: Optional[AppLogger] = None


def get_logger(name: str = 'app') -> logging.Logger:
    """Get logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AppLogger()
    return _logger_instance.get_logger(name)


def get_db_logger() -> logging.Logger:
    """Get database logger"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AppLogger()
    return _logger_instance.get_db_logger()


def get_actions_logger() -> logging.Logger:
    """Get user actions logger"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AppLogger()
    return _logger_instance.get_actions_logger()
