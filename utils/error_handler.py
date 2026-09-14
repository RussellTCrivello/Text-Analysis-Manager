"""
Comprehensive Error Handling System
Provides centralized error handling, recovery, and reporting functionality
"""
import sys
import traceback
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any, Dict, List
from functools import wraps
from enum import Enum, auto

from PyQt5.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QCheckBox, QApplication, QWidget
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject

from utils.logger import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class ErrorCategory(Enum):
    """Error categories for classification"""
    DATABASE = "database"
    FILE_IO = "file_io"
    NETWORK = "network"
    VALIDATION = "validation"
    UI = "ui"
    IMPORT_EXPORT = "import_export"
    CONFIGURATION = "configuration"
    PERMISSION = "permission"
    UNKNOWN = "unknown"


class AppError(Exception):
    """Custom application error with additional context"""
    
    def __init__(self, message: str, 
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 category: ErrorCategory = ErrorCategory.UNKNOWN,
                 recoverable: bool = True,
                 recovery_action: Optional[str] = None,
                 user_message: Optional[str] = None,
                 original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.category = category
        self.recoverable = recoverable
        self.recovery_action = recovery_action
        self.user_message = user_message or message
        self.original_exception = original_exception
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()


class ErrorReport:
    """Stores error report data"""
    
    def __init__(self, error: Exception, context: Optional[Dict] = None):
        self.timestamp = datetime.now()
        self.error_type = type(error).__name__
        self.message = str(error)
        self.traceback = traceback.format_exc()
        self.context = context or {}
        
        if isinstance(error, AppError):
            self.severity = error.severity.name
            self.category = error.category.value
            self.recoverable = error.recoverable
            self.recovery_action = error.recovery_action
        else:
            self.severity = ErrorSeverity.ERROR.name
            self.category = ErrorCategory.UNKNOWN.value
            self.recoverable = False
            self.recovery_action = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'error_type': self.error_type,
            'message': self.message,
            'traceback': self.traceback,
            'severity': self.severity,
            'category': self.category,
            'recoverable': self.recoverable,
            'recovery_action': self.recovery_action,
            'context': self.context
        }


class ErrorReportDialog(QDialog):
    """Dialog for displaying detailed error information"""
    
    def __init__(self, error_report: ErrorReport, parent=None, translator=None):
        super().__init__(parent)
        self.error_report = error_report
        self.translator = translator
        
        self.setWindowTitle(self._tr('error_report_title', 'Error Report'))
        # Apply fixed size to prevent resizing on button clicks or content changes
        from styles.styles import AppStyles
        AppStyles.apply_fixed_size(self, 600, 400)
        self.setup_ui()
    
    def _tr(self, key: str, default: str) -> str:
        """Translate text"""
        if self.translator and hasattr(self.translator, 'tr'):
            return self.translator.tr(key)
        return default
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Error summary
        severity_colors = {
            'INFO': '#3498DB',
            'WARNING': '#F39C12',
            'ERROR': '#E74C3C',
            'CRITICAL': '#9B59B6'
        }
        
        color = severity_colors.get(self.error_report.severity, '#E74C3C')
        
        summary_label = QLabel(f"""
            <h3 style="color: {color};">{self._tr('error_occurred', 'An error occurred')}</h3>
            <p><b>{self._tr('error_type', 'Type')}:</b> {self.error_report.error_type}</p>
            <p><b>{self._tr('error_category', 'Category')}:</b> {self.error_report.category}</p>
            <p><b>{self._tr('error_severity', 'Severity')}:</b> {self.error_report.severity}</p>
            <p><b>{self._tr('error_time', 'Time')}:</b> {self.error_report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        """)
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label)
        
        # Error message
        message_label = QLabel(f"<p><b>{self._tr('error_message', 'Message')}:</b></p>")
        layout.addWidget(message_label)
        
        message_text = QTextEdit()
        message_text.setPlainText(self.error_report.message)
        message_text.setReadOnly(True)
        message_text.setMaximumHeight(100)
        layout.addWidget(message_text)
        
        # Technical details (expandable)
        details_label = QLabel(f"<p><b>{self._tr('error_details', 'Technical Details')}:</b></p>")
        layout.addWidget(details_label)
        
        details_text = QTextEdit()
        details_text.setPlainText(self.error_report.traceback)
        details_text.setReadOnly(True)
        layout.addWidget(details_text)
        
        # Recovery suggestion
        if self.error_report.recovery_action:
            recovery_label = QLabel(f"""
                <p style="color: #27AE60;"><b>{self._tr('error_recovery', 'Suggested Recovery')}:</b> 
                {self.error_report.recovery_action}</p>
            """)
            recovery_label.setWordWrap(True)
            layout.addWidget(recovery_label)
        
        # Report to log checkbox
        self.log_checkbox = QCheckBox(self._tr('error_save_log', 'Save to error log'))
        self.log_checkbox.setChecked(True)
        layout.addWidget(self.log_checkbox)
        
        # Copy to clipboard checkbox
        self.copy_checkbox = QCheckBox(self._tr('error_copy_clipboard', 'Copy details to clipboard'))
        layout.addWidget(self.copy_checkbox)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_ok = QPushButton(self._tr('btn_ok', 'OK'))
        btn_ok.clicked.connect(self.accept_and_process)
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)
    
    def accept_and_process(self):
        """Process options and close dialog"""
        if self.log_checkbox.isChecked():
            ErrorHandler.save_error_report(self.error_report)
        
        if self.copy_checkbox.isChecked():
            clipboard = QApplication.clipboard()
            report_text = json.dumps(self.error_report.to_dict(), indent=2)
            clipboard.setText(report_text)
        
        self.accept()


class ErrorHandler(QObject):
    """Centralized error handler"""
    
    error_occurred = pyqtSignal(object)  # Signal emitted when error occurs
    
    _instance: Optional['ErrorHandler'] = None
    _error_reports: List[ErrorReport] = []
    _error_log_file: Optional[Path] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the error handler"""
        from utils.path_utils import get_logs_dir
        self._error_log_dir = get_logs_dir()
        self._error_log_file = self._error_log_dir / "errors.log"
        
        # Install global exception handler
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._global_exception_handler
    
    def _global_exception_handler(self, exc_type, exc_value, exc_traceback):
        """Global exception handler"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't catch keyboard interrupts
            self._original_excepthook(exc_type, exc_value, exc_traceback)
            return
        
        # Log the error
        logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Create error report
        error_report = ErrorReport(exc_value)
        self._error_reports.append(error_report)
        self.save_error_report(error_report)
        
        # Emit signal
        self.error_occurred.emit(error_report)
    
    @classmethod
    def handle_error(cls, error: Exception, 
                     parent: Optional[QWidget] = None,
                     translator=None,
                     show_dialog: bool = True,
                     context: Optional[Dict] = None) -> ErrorReport:
        """Handle an error with optional user notification"""
        
        # Create error report
        error_report = ErrorReport(error, context)
        cls._error_reports.append(error_report)
        
        # Log the error
        if isinstance(error, AppError):
            if error.severity == ErrorSeverity.CRITICAL:
                logger.critical(f"{error.category.value}: {error.message}", exc_info=True)
            elif error.severity == ErrorSeverity.ERROR:
                logger.error(f"{error.category.value}: {error.message}", exc_info=True)
            elif error.severity == ErrorSeverity.WARNING:
                logger.warning(f"{error.category.value}: {error.message}")
            else:
                logger.info(f"{error.category.value}: {error.message}")
        else:
            logger.error(f"Error: {str(error)}", exc_info=True)
        
        # Show dialog if requested
        if show_dialog:
            cls._show_error_dialog(error, error_report, parent, translator)
        
        # Save to log
        cls.save_error_report(error_report)
        
        return error_report
    
    @classmethod
    def _show_error_dialog(cls, error: Exception, error_report: ErrorReport,
                          parent: Optional[QWidget], translator):
        """Show appropriate error dialog"""
        
        if isinstance(error, AppError):
            if error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.ERROR]:
                # Show detailed error dialog
                dialog = ErrorReportDialog(error_report, parent, translator)
                dialog.exec_()
            elif error.severity == ErrorSeverity.WARNING:
                QMessageBox.warning(
                    parent,
                    translator.tr('msg_warning') if translator else 'Warning',
                    error.user_message
                )
            else:
                QMessageBox.information(
                    parent,
                    translator.tr('msg_info') if translator else 'Information',
                    error.user_message
                )
        else:
            # For standard exceptions, show simple error dialog
            QMessageBox.critical(
                parent,
                translator.tr('msg_error') if translator else 'Error',
                str(error)
            )
    
    @classmethod
    def save_error_report(cls, error_report: ErrorReport):
        """Save error report to log file"""
        if cls._error_log_file is None:
            # Initialize if needed
            ErrorHandler()
        
        try:
            with open(cls._error_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_report.to_dict(), ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Failed to save error report: {e}")
    
    @classmethod
    def get_recent_errors(cls, limit: int = 50) -> List[ErrorReport]:
        """Get recent error reports"""
        return cls._error_reports[-limit:]
    
    @classmethod
    def clear_error_history(cls):
        """Clear error history"""
        cls._error_reports.clear()


def handle_errors(category: ErrorCategory = ErrorCategory.UNKNOWN,
                  show_dialog: bool = True,
                  recovery_action: Optional[str] = None):
    """Decorator for automatic error handling"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AppError:
                raise  # Re-raise AppError as-is
            except Exception as e:
                # Wrap in AppError
                app_error = AppError(
                    message=str(e),
                    severity=ErrorSeverity.ERROR,
                    category=category,
                    recoverable=True,
                    recovery_action=recovery_action,
                    original_exception=e
                )
                
                # Find parent widget in args
                parent = None
                translator = None
                for arg in args:
                    if isinstance(arg, QWidget):
                        parent = arg
                    if hasattr(arg, 'translator'):
                        translator = arg.translator
                    elif hasattr(arg, 'tr'):
                        translator = arg
                
                ErrorHandler.handle_error(
                    app_error,
                    parent=parent,
                    translator=translator,
                    show_dialog=show_dialog,
                    context={'function': func.__name__, 'args': str(args)[:200]}
                )
                
                return None
        return wrapper
    return decorator


def safe_operation(func: Callable, 
                   *args, 
                   default_return=None,
                   error_message: str = "Operation failed",
                   **kwargs) -> Any:
    """Execute a function safely with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"{error_message}: {e}", exc_info=True)
        return default_return


class RetryMixin:
    """Mixin class providing retry functionality"""
    
    @staticmethod
    def retry(max_attempts: int = 3, 
              delay_ms: int = 1000,
              exponential_backoff: bool = True):
        """Decorator for retrying operations"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                current_delay = delay_ms
                
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed: {e}")
                        
                        if attempt < max_attempts - 1:
                            # Wait before retry (non-blocking for Qt)
                            QApplication.processEvents()
                            import time
                            time.sleep(current_delay / 1000.0)
                            
                            if exponential_backoff:
                                current_delay *= 2
                
                raise last_exception
            return wrapper
        return decorator


# Initialize error handler on module import
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance"""
    return _error_handler
