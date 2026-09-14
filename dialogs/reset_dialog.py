"""
Reset Dialog
Provides UI for resetting the database or application settings
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QGroupBox, QRadioButton, QButtonGroup, QWidget
)
from icons.icon_manager import setup_icon_button
from PyQt5.QtCore import Qt
from db.db_config import DatabaseConfig
from db.db_manager import DatabaseManager
from translations.translations import TranslationManager
from styles.styles import AppStyles
from utils.logger import get_logger
from pathlib import Path
import os
import shutil

logger = get_logger(__name__)


class ResetDialog(QDialog):
    """Dialog for resetting database or settings"""
    
    def __init__(self, parent, translator: TranslationManager):
        super().__init__(parent)
        self.translator = translator
        
        self._apply_rtl_direction()
        self.setWindowTitle(translator.tr('menu_reset'))
        # Apply fixed size to prevent resizing on button clicks or content changes
        from styles.styles import AppStyles
        AppStyles.apply_fixed_size(self, 500, 300)
        self.setup_ui()
        self._apply_rtl_direction()
    
    def _apply_rtl_direction(self):
        """Apply RTL/LTR direction based on current language"""
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)
        for child in self.findChildren(QWidget):
            child.setLayoutDirection(direction)
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Warning label
        warning_label = QLabel(self.translator.tr('msg_reset_warning'))
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet(f"color: {AppStyles.get_color('DANGER')}; font-weight: bold;")
        layout.addWidget(warning_label)
        
        # Reset options
        options_group = QGroupBox(self.translator.tr('lbl_reset_options'))
        options_layout = QVBoxLayout(options_group)
        
        self.button_group = QButtonGroup(self)
        
        self.radio_reset_data = QRadioButton(self.translator.tr('radio_reset_data'))
        self.radio_reset_data.setChecked(True)
        self.button_group.addButton(self.radio_reset_data, 1)
        options_layout.addWidget(self.radio_reset_data)
        
        self.radio_reset_all = QRadioButton(self.translator.tr('radio_reset_all'))
        self.button_group.addButton(self.radio_reset_all, 2)
        options_layout.addWidget(self.radio_reset_all)
        
        layout.addWidget(options_group)
        
        # Info label
        info_label = QLabel(self.translator.tr('msg_reset_info'))
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Buttons - properly aligned in a single row
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        btn_layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid (rounding 10px to 16px)
        btn_layout.addStretch()
        
        self.btn_reset = QPushButton()
        setup_icon_button(self.btn_reset, 'btn_reset', self.translator.tr('btn_reset'))
        self.btn_reset.setProperty('class', 'danger')
        # Disable autoDefault to prevent Enter key from triggering buttons unexpectedly
        self.btn_reset.setAutoDefault(False)
        self.btn_reset.setDefault(False)
        self.btn_reset.clicked.connect(self.confirm_reset)
        
        btn_cancel = QPushButton()
        setup_icon_button(btn_cancel, 'btn_cancel', self.translator.tr('btn_cancel'))
        btn_cancel.setAutoDefault(False)
        btn_cancel.setDefault(False)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_reset, alignment=Qt.AlignVCenter)
        btn_layout.addWidget(btn_cancel, alignment=Qt.AlignVCenter)
        layout.addLayout(btn_layout)
    
    def confirm_reset(self):
        """Confirm reset operation"""
        reset_type = "data" if self.radio_reset_data.isChecked() else "all"
        
        confirm_text = (
            self.translator.tr('msg_confirm_reset_data') 
            if reset_type == "data" 
            else self.translator.tr('msg_confirm_reset_all')
        )
        
        reply = QMessageBox.critical(
            self,
            self.translator.tr('msg_warning'),
            confirm_text,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.perform_reset(reset_type)
    
    def perform_reset(self, reset_type: str):
        """Perform the reset operation"""
        try:
            if reset_type == "data":
                # Reset data: Delete all records from tables
                self.reset_database_data()
            else:
                # Reset all: Delete database file and recreate
                self.reset_database_all()
            
            QMessageBox.information(
                self,
                self.translator.tr('msg_success'),
                self.translator.tr('msg_reset_complete')
            )
            self.accept()
            
        except Exception as e:
            logger.error(f"Error during reset: {e}")
            QMessageBox.critical(
                self,
                self.translator.tr('msg_error'),
                f"{self.translator.tr('msg_reset_failed')}: {str(e)}"
            )
    
    def reset_database_data(self):
        """Reset database data (delete all records)"""
        try:
            # Delete all records from tables (in correct order due to foreign keys)
            tables = ['content_analysis', 'contents', 'sources']
            for table in tables:
                try:
                    DatabaseManager.execute_query(f"DELETE FROM {table}", fetch=False)
                except Exception as e:
                    logger.warning(f"Error deleting from {table}: {e}")
                    # Continue with other tables
            
            logger.info("Database data reset completed")
            
        except Exception as e:
            logger.error(f"Error resetting database data: {e}")
            raise
    
    def reset_database_all(self):
        """Reset database completely (delete and recreate)"""
        try:
            # Close connection
            DatabaseConfig.close_connection()
            
            # Get database path
            db_path = DatabaseConfig.get_db_path()
            db_file = Path(db_path)
            
            # Create backup before deletion
            if db_file.exists():
                backup_path = db_file.with_suffix('.sqlite.backup')
                try:
                    shutil.copy2(db_file, backup_path)
                except Exception as e:
                    logger.warning(f"Could not create backup: {e}")
            
            # Delete database file
            if db_file.exists():
                db_file.unlink()
            
            # Reinitialize database
            DatabaseConfig.initialize_database()
            
            logger.info("Database completely reset")
            
        except Exception as e:
            logger.error(f"Error resetting database: {e}")
            # Try to reconnect even if reset failed
            try:
                DatabaseConfig.get_connection()
            except:
                pass
            raise
