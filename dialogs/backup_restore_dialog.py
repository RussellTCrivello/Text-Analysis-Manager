"""
Backup and Restore Dialog
Provides UI for creating backups and restoring from backups
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QMessageBox, QFileDialog, QHeaderView,
    QGroupBox, QProgressBar, QCheckBox, QDialogButtonBox, QWidget
)
from icons.icon_manager import setup_icon_button, get_icon
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from typing import Optional
from pathlib import Path
from datetime import datetime
from utils.backup_restore import BackupRestoreManager
from translations.translations import TranslationManager
from utils.logger import get_logger

logger = get_logger(__name__)


def _format_file_size(size_bytes: int) -> str:
    """Format file size for display"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


class ImportBackupPreviewDialog(QDialog):
    """Dialog shown after selecting a backup file - validates and shows preview with Restore/Merge options"""
    
    def __init__(self, parent, translator: TranslationManager, backup_manager: BackupRestoreManager, file_path: str):
        super().__init__(parent)
        self.translator = translator
        self.backup_manager = backup_manager
        self.file_path = file_path
        self.copy_to_folder = False
        
        self._apply_rtl_direction()
        self.setWindowTitle(translator.tr('backup_preview_title'))
        from styles.styles import AppStyles
        AppStyles.apply_fixed_size(self, 450, 320)
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
        """Setup preview UI"""
        layout = QVBoxLayout(self)
        from styles.styles import AppStyles
        AppStyles.apply_layout_spacing(layout, margin_units=2, spacing_units=2)
        
        # Validate file
        is_valid, error_msg, preview = self.backup_manager.validate_backup_file(self.file_path)
        
        if not is_valid:
            error_label = QLabel(f"<b>{self.translator.tr('backup_invalid_file')}</b><br>{error_msg}")
            error_label.setWordWrap(True)
            error_label.setStyleSheet("color: #c0392b; padding: 12px;")
            layout.addWidget(error_label)
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
            btn_box.accepted.connect(self.reject)
            layout.addWidget(btn_box)
            return
        
        # Show preview
        filename = Path(self.file_path).name
        file_label = QLabel(f"<b>{filename}</b>")
        layout.addWidget(file_label)
        
        preview_layout = QVBoxLayout()
        if preview.get('encrypted'):
            preview_layout.addWidget(QLabel(self.translator.tr('backup_preview_encrypted')))
        else:
            preview_layout.addWidget(QLabel(self.translator.tr('backup_preview_sources', count=preview.get('sources_count', 0))))
            preview_layout.addWidget(QLabel(self.translator.tr('backup_preview_contents', count=preview.get('contents_count', 0))))
            preview_layout.addWidget(QLabel(self.translator.tr('backup_preview_analyses', count=preview.get('content_analysis_count', preview.get('analyses_count', 0)))))
        
        size_str = _format_file_size(preview.get('file_size', 0))
        preview_layout.addWidget(QLabel(self.translator.tr('backup_preview_size', size=size_str)))
        layout.addLayout(preview_layout)
        
        # Copy to folder option (only if file is outside backup dir)
        backup_dir = Path(self.backup_manager.backup_dir).resolve()
        file_path_obj = Path(self.file_path).resolve()
        try:
            file_path_obj.relative_to(backup_dir)
            file_in_backup_dir = True
        except ValueError:
            file_in_backup_dir = False
        if not file_in_backup_dir:
            self.copy_check = QCheckBox(self.translator.tr('backup_copy_after_import'))
            self.copy_check.setChecked(True)
            layout.addWidget(self.copy_check)
        
        # Buttons: Restore | Merge | Cancel - with margins for icon buttons
        btn_layout = QHBoxLayout()
        from styles.styles import AppStyles
        btn_layout.setSpacing(AppStyles.get_spacing(3))  # 24px between icon buttons
        btn_layout.addStretch()
        
        self.btn_restore = QPushButton()
        setup_icon_button(self.btn_restore, 'btn_restore', self.translator.tr('btn_restore'))
        self.btn_restore.setAutoDefault(False)
        self.btn_restore.setDefault(False)
        self.btn_restore.clicked.connect(self._on_restore)
        
        self.btn_merge = QPushButton()
        setup_icon_button(self.btn_merge, 'btn_merge', self.translator.tr('btn_merge'))
        self.btn_merge.setAutoDefault(False)
        self.btn_merge.setDefault(False)
        self.btn_merge.clicked.connect(self._on_merge)
        
        btn_cancel = QPushButton()
        setup_icon_button(btn_cancel, 'btn_cancel', self.translator.tr('btn_cancel'))
        btn_cancel.setAutoDefault(False)
        btn_cancel.setDefault(False)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_restore)
        btn_layout.addWidget(self.btn_merge)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def _on_restore(self):
        self.copy_to_folder = getattr(self, 'copy_check', None) and self.copy_check.isChecked()
        self.done(1)  # Restore
    
    def _on_merge(self):
        self.copy_to_folder = getattr(self, 'copy_check', None) and self.copy_check.isChecked()
        self.done(2)  # Merge


class BackupThread(QThread):
    """Thread for backup operations to prevent UI freezing"""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    
    def __init__(self, backup_manager: BackupRestoreManager, backup_type: str = 'MANUAL'):
        super().__init__()
        self.backup_manager = backup_manager
        self.backup_type = backup_type
    
    def run(self):
        """Run backup operation"""
        try:
            self.progress.emit("Creating backup...")
            success, backup_path, backup_info = self.backup_manager.create_backup(self.backup_type)
            if success:
                self.finished.emit(True, f"Backup created successfully!\nLocation: {backup_path}")
            else:
                error = backup_info.get('error', 'Unknown error')
                self.finished.emit(False, f"Backup failed: {error}")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class RestoreThread(QThread):
    """Thread for restore operations to prevent UI freezing"""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    
    def __init__(self, backup_manager: BackupRestoreManager, backup_path: str, merge: bool = False):
        super().__init__()
        self.backup_manager = backup_manager
        self.backup_path = backup_path
        self.merge = merge
    
    def run(self):
        """Run restore operation"""
        try:
            if self.merge:
                self.progress.emit("Merging backup...")
            else:
                self.progress.emit("Restoring backup...")
            success, message = self.backup_manager.restore_backup(self.backup_path, merge=self.merge)
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class BackupRestoreDialog(QDialog):
    """Dialog for backup and restore operations"""
    
    def __init__(self, parent, translator: TranslationManager):
        super().__init__(parent)
        self.translator = translator
        self.backup_manager = BackupRestoreManager()
        self.backup_thread = None
        self.restore_thread = None
        
        self._apply_rtl_direction()
        self.setWindowTitle(translator.tr('menu_backup_restore'))
        # Apply fixed size to prevent resizing on button clicks or content changes
        from styles.styles import AppStyles
        AppStyles.apply_fixed_size(self, 700, 500)
        self.setup_ui()
        self.load_backups()
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
        # Use 8px grid spacing system
        from styles.styles import AppStyles
        AppStyles.apply_layout_spacing(layout, margin_units=2, spacing_units=2)  # 16px margins and spacing
        
        # Backup Section
        backup_group = QGroupBox(self.translator.tr('lbl_backup'))
        backup_layout = QVBoxLayout(backup_group)
        
        backup_info = QLabel(self.translator.tr('msg_backup_info'))
        backup_info.setWordWrap(True)
        backup_layout.addWidget(backup_info)
        
        backup_btn_layout = QHBoxLayout()
        backup_btn_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        is_rtl = self.translator.current_language == 'ar'
        btn_spacing = AppStyles.get_spacing(3) if is_rtl else AppStyles.get_spacing(2)  # 24px RTL for icon margins
        backup_btn_layout.setSpacing(btn_spacing)
        self.btn_create_backup = QPushButton()
        setup_icon_button(self.btn_create_backup, 'btn_create_backup', self.translator.tr('btn_create_backup'))
        # Disable autoDefault to prevent Enter key from triggering buttons unexpectedly
        self.btn_create_backup.setAutoDefault(False)
        self.btn_create_backup.setDefault(False)
        self.btn_create_backup.clicked.connect(self.create_backup)
        backup_btn_layout.addWidget(self.btn_create_backup, alignment=Qt.AlignVCenter)
        backup_btn_layout.addStretch()
        backup_layout.addLayout(backup_btn_layout)
        
        layout.addWidget(backup_group)
        
        # Restore Section
        restore_group = QGroupBox(self.translator.tr('lbl_restore'))
        restore_layout = QVBoxLayout(restore_group)
        
        # Backup list table
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(4)
        self.backup_table.setHorizontalHeaderLabels([
            self.translator.tr('lbl_filename'),
            self.translator.tr('lbl_size'),
            self.translator.tr('lbl_date'),
            self.translator.tr('lbl_actions')
        ])
        self.backup_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.backup_table.setSelectionMode(QTableWidget.SingleSelection)
        self.backup_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.backup_table.horizontalHeader().setStretchLastSection(True)
        self.backup_table.setColumnWidth(0, 300)
        self.backup_table.setColumnWidth(1, 100)
        self.backup_table.setColumnWidth(2, 150)
        
        restore_layout.addWidget(self.backup_table)
        
        # Restore buttons - properly aligned with margins to prevent icon cropping
        restore_btn_layout = QHBoxLayout()
        restore_btn_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        restore_btn_layout.setSpacing(btn_spacing)
        self.btn_restore = QPushButton()
        setup_icon_button(self.btn_restore, 'btn_restore', self.translator.tr('btn_restore'))
        self.btn_restore.setAutoDefault(False)
        self.btn_restore.setDefault(False)
        self.btn_restore.clicked.connect(self.restore_backup)
        self.btn_restore.setEnabled(False)
        
        self.btn_merge = QPushButton()
        setup_icon_button(self.btn_merge, 'btn_merge', self.translator.tr('btn_merge'))
        self.btn_merge.setAutoDefault(False)
        self.btn_merge.setDefault(False)
        self.btn_merge.clicked.connect(self.merge_backup)
        self.btn_merge.setEnabled(False)
        
        self.btn_restore_file = QPushButton()
        setup_icon_button(self.btn_restore_file, 'btn_restore_from_file', self.translator.tr('btn_restore_from_file'))
        self.btn_restore_file.setAutoDefault(False)
        self.btn_restore_file.setDefault(False)
        self.btn_restore_file.clicked.connect(self.restore_from_file)
        
        self.btn_delete_backup = QPushButton()
        setup_icon_button(self.btn_delete_backup, 'btn_delete_backup', self.translator.tr('btn_delete'))
        self.btn_delete_backup.setProperty('class', 'danger')
        self.btn_delete_backup.setAutoDefault(False)
        self.btn_delete_backup.setDefault(False)
        self.btn_delete_backup.clicked.connect(self.delete_backup)
        self.btn_delete_backup.setEnabled(False)
        
        self.btn_refresh = QPushButton()
        setup_icon_button(self.btn_refresh, 'btn_refresh', self.translator.tr('btn_refresh'))
        self.btn_refresh.setAutoDefault(False)
        self.btn_refresh.setDefault(False)
        self.btn_refresh.clicked.connect(self.load_backups)
        
        restore_btn_layout.addWidget(self.btn_restore, alignment=Qt.AlignVCenter)
        restore_btn_layout.addWidget(self.btn_merge, alignment=Qt.AlignVCenter)
        restore_btn_layout.addWidget(self.btn_restore_file, alignment=Qt.AlignVCenter)
        restore_btn_layout.addStretch()
        restore_btn_layout.addWidget(self.btn_delete_backup, alignment=Qt.AlignVCenter)
        restore_btn_layout.addWidget(self.btn_refresh, alignment=Qt.AlignVCenter)
        restore_layout.addLayout(restore_btn_layout)
        
        layout.addWidget(restore_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel(self.translator.tr('msg_ready'))
        layout.addWidget(self.status_label)
        
        # Buttons - properly aligned with margins for icon buttons
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        btn_layout.setSpacing(btn_spacing)
        btn_layout.addStretch()
        btn_close = QPushButton()
        setup_icon_button(btn_close, 'btn_close', self.translator.tr('btn_close'))
        btn_close.setAutoDefault(False)
        btn_close.setDefault(False)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close, alignment=Qt.AlignVCenter)
        layout.addLayout(btn_layout)
        
        # Connect table selection
        self.backup_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
    
    def load_backups(self):
        """Load list of backups"""
        try:
            backups = self.backup_manager.get_backup_list()
            self.backup_table.setRowCount(len(backups))
            
            for row, backup in enumerate(backups):
                # Filename
                filename_item = QTableWidgetItem(backup['filename'])
                filename_item.setData(Qt.UserRole, backup['path'])
                self.backup_table.setItem(row, 0, filename_item)
                
                # Size
                size_mb = backup['size'] / (1024 * 1024)
                size_item = QTableWidgetItem(f"{size_mb:.2f} MB")
                self.backup_table.setItem(row, 1, size_item)
                
                # Date
                try:
                    date_obj = datetime.fromisoformat(backup['created_at'])
                    date_str = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    date_str = backup['created_at']
                date_item = QTableWidgetItem(date_str)
                self.backup_table.setItem(row, 2, date_item)
                
                # Encrypted indicator: use an actual icon rather than a
                # Unicode lock glyph, with an accessible tooltip.
                encrypted_item = QTableWidgetItem()
                if backup.get('is_encrypted', False):
                    encrypted_item.setIcon(get_icon('lock', 18))
                    encrypted_item.setToolTip(self.translator.tr('backup_preview_encrypted'))
                    encrypted_item.setData(Qt.AccessibleTextRole, self.translator.tr('backup_preview_encrypted'))
                self.backup_table.setItem(row, 3, encrypted_item)
            
            self.status_label.setText(f"{len(backups)} {self.translator.tr('msg_backups_found').lower()}")
        except Exception as e:
            logger.error(f"Error loading backups: {e}")
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def on_selection_changed(self):
        """Handle table selection change"""
        has_selection = len(self.backup_table.selectedItems()) > 0
        self.btn_restore.setEnabled(has_selection)
        self.btn_merge.setEnabled(has_selection)
        self.btn_delete_backup.setEnabled(has_selection)
    
    def create_backup(self):
        """Create a new backup"""
        reply = QMessageBox.question(
            self,
            self.translator.tr('msg_confirm'),
            self.translator.tr('msg_confirm_backup'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.btn_create_backup.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate
            self.status_label.setText(self.translator.tr('msg_creating_backup'))
            
            self.backup_thread = BackupThread(self.backup_manager, 'MANUAL')
            self.backup_thread.finished.connect(self.on_backup_finished)
            self.backup_thread.progress.connect(self.status_label.setText)
            self.backup_thread.start()
    
    def on_backup_finished(self, success: bool, message: str):
        """Handle backup completion"""
        self.btn_create_backup.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(self, self.translator.tr('msg_success'), message)
            self.load_backups()
        else:
            QMessageBox.critical(self, self.translator.tr('msg_error'), message)
        
        self.status_label.setText(self.translator.tr('msg_ready'))
    
    def restore_backup(self):
        """Restore selected backup (replaces existing data)"""
        selected_items = self.backup_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.translator.tr('msg_warning'),
                              self.translator.tr('msg_select_backup'))
            return
        
        backup_path = selected_items[0].data(Qt.UserRole)
        
        reply = QMessageBox.warning(
            self,
            self.translator.tr('msg_warning'),
            self.translator.tr('msg_confirm_restore'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.btn_restore.setEnabled(False)
            self.btn_merge.setEnabled(False)
            self.btn_restore_file.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            self.status_label.setText(self.translator.tr('msg_restoring_backup'))
            
            self.restore_thread = RestoreThread(self.backup_manager, backup_path, merge=False)
            self.restore_thread.finished.connect(self.on_restore_finished)
            self.restore_thread.progress.connect(self.status_label.setText)
            self.restore_thread.start()
    
    def merge_backup(self):
        """Merge selected backup (adds data to existing)"""
        selected_items = self.backup_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.translator.tr('msg_warning'),
                              self.translator.tr('msg_select_backup'))
            return
        
        backup_path = selected_items[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            self.translator.tr('msg_confirm'),
            self.translator.tr('msg_confirm_merge'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.btn_restore.setEnabled(False)
            self.btn_merge.setEnabled(False)
            self.btn_restore_file.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            self.status_label.setText(self.translator.tr('msg_merging_backup'))
            
            self.restore_thread = RestoreThread(self.backup_manager, backup_path, merge=True)
            self.restore_thread.finished.connect(self.on_restore_finished)
            self.restore_thread.progress.connect(self.status_label.setText)
            self.restore_thread.start()
    
    def restore_from_file(self):
        """Import and restore from a backup file (with validation and preview)"""
        # Default to user's home or Documents for easier access to downloaded/external backups
        import os
        default_dir = os.path.expanduser('~')
        if os.path.exists(os.path.join(default_dir, 'Documents')):
            default_dir = os.path.join(default_dir, 'Documents')
        
        filename, _ = QFileDialog.getOpenFileName(
            self,
            self.translator.tr('backup_import_title'),
            default_dir,
            self.translator.tr('backup_import_file_filter')
        )
        
        if not filename:
            return
        
        # Show preview dialog with validation
        preview_dialog = ImportBackupPreviewDialog(
            self, self.translator, self.backup_manager, filename
        )
        result = preview_dialog.exec_()
        
        if result == 0:  # Cancel or invalid
            return
        
        merge = (result == 2)
        copy_to_folder = getattr(preview_dialog, 'copy_to_folder', False)
        
        # Confirm destructive action
        if merge:
            confirm_msg = self.translator.tr('msg_confirm_merge')
        else:
            confirm_msg = self.translator.tr('msg_confirm_restore')
        
        reply = QMessageBox.warning(
            self,
            self.translator.tr('msg_warning'),
            confirm_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Copy to backup folder first if requested
        if copy_to_folder:
            try:
                import shutil
                dest = Path(self.backup_manager.backup_dir) / Path(filename).name
                if Path(filename).resolve() != dest.resolve():
                    shutil.copy2(filename, dest)
                    filename = str(dest)
            except Exception as e:
                logger.warning(f"Could not copy backup to folder: {e}")
        
        # Run restore/merge
        self.btn_restore.setEnabled(False)
        self.btn_merge.setEnabled(False)
        self.btn_restore_file.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText(
            self.translator.tr('msg_merging_backup') if merge 
            else self.translator.tr('msg_restoring_backup')
        )
        
        self.restore_thread = RestoreThread(self.backup_manager, filename, merge=merge)
        self.restore_thread.finished.connect(self.on_restore_finished)
        self.restore_thread.progress.connect(self.status_label.setText)
        self.restore_thread.start()
    
    def on_restore_finished(self, success: bool, message: str):
        """Handle restore completion"""
        self.btn_restore.setEnabled(True)
        self.btn_merge.setEnabled(True)
        self.btn_restore_file.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(self, self.translator.tr('msg_success'), message)
            # Only show restart message for restore (not merge)
            if not hasattr(self.restore_thread, 'merge') or not self.restore_thread.merge:
                QMessageBox.information(
                    self,
                    self.translator.tr('msg_info'),
                    self.translator.tr('msg_restart_required')
                )
        else:
            QMessageBox.critical(self, self.translator.tr('msg_error'), message)
        
        self.status_label.setText(self.translator.tr('msg_ready'))
    
    def delete_backup(self):
        """Delete selected backup"""
        selected_items = self.backup_table.selectedItems()
        if not selected_items:
            return
        
        backup_path = selected_items[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            self.translator.tr('msg_confirm'),
            self.translator.tr('msg_confirm_delete_backup'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.backup_manager.delete_backup(backup_path)
            if success:
                QMessageBox.information(self, self.translator.tr('msg_success'), message)
                self.load_backups()
            else:
                QMessageBox.critical(self, self.translator.tr('msg_error'), message)
