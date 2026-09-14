"""
Timeline Export Dialog
Comprehensive export dialog for timeline events with format preservation and system header
"""
import os
from datetime import datetime
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QRadioButton, QButtonGroup,
    QComboBox, QLineEdit, QFileDialog, QMessageBox,
    QFormLayout, QFrame, QSpinBox, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from translations.translations import TranslationManager
from utils.logger import get_logger
from utils.print_utils import PrintSettings, get_print_settings
from styles.styles import AppStyles
from icons.icon_manager import setup_icon_button

logger = get_logger(__name__)


class TimelineExportDialog(QDialog):
    """
    Comprehensive export dialog for timeline events with:
    - Export format selection (Word, Excel, PDF)
    - System header inclusion option
    - Data scope selection (current page, all filtered, all data)
    - Format preservation
    """
    
    FORMAT_WORD = 'word'
    FORMAT_EXCEL = 'excel'
    FORMAT_PDF = 'pdf'
    
    SCOPE_CURRENT_PAGE = 'current_page'
    SCOPE_FILTERED = 'filtered'
    SCOPE_ALL = 'all'
    
    def __init__(self, parent=None, events: List[Dict] = None,
                 filtered_events: List[Dict] = None,
                 current_page_events: List[Dict] = None,
                 translator: TranslationManager = None):
        """
        Initialize timeline export dialog
        
        Args:
            parent: Parent widget
            events: All events in database
            filtered_events: Currently filtered events
            current_page_events: Events on current page
            translator: Translation manager
        """
        super().__init__(parent)
        self.translator = translator or TranslationManager()
        self.all_events = events or []
        self.filtered_events = filtered_events or []
        self.current_page_events = current_page_events or []
        
        # Export settings
        self.selected_format = self.FORMAT_WORD
        self.selected_scope = self.SCOPE_FILTERED
        self.include_header = True
        self.open_after_export = True
        self.export_path = None
        
        self._apply_rtl_direction()
        self.setWindowTitle(self.translator.tr('export_timeline'))
        AppStyles.apply_fixed_size(self, 600, 500)
        
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
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(AppStyles.get_spacing(2))
        layout.setContentsMargins(AppStyles.get_spacing(2), 
                                 AppStyles.get_spacing(2),
                                 AppStyles.get_spacing(2),
                                 AppStyles.get_spacing(2))
        
        # Title
        title_label = QLabel(self.translator.tr('export_timeline'))
        title_label.setFont(QFont(AppStyles.FONT_FAMILY, 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {AppStyles.get_color('TEXT_PRIMARY')}; padding: 8px;")
        layout.addWidget(title_label)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {AppStyles.get_color('BORDER')};")
        layout.addWidget(sep)
        
        # Data scope selection
        scope_group = QGroupBox(self.translator.tr('export_scope'))
        scope_layout = QVBoxLayout(scope_group)
        
        self.scope_group = QButtonGroup(self)
        
        # Current page option
        events_word = self.translator.tr('timeline_event', default='events')
        current_page_text = f"{self.translator.tr('export_current_page')} ({len(self.current_page_events)} {events_word})"
        current_page_radio = QRadioButton(current_page_text)
        current_page_radio.setProperty('scope', self.SCOPE_CURRENT_PAGE)
        current_page_radio.setEnabled(len(self.current_page_events) > 0)
        self.scope_group.addButton(current_page_radio)
        scope_layout.addWidget(current_page_radio)
        
        # Filtered results option
        filtered_text = f"{self.translator.tr('export_filtered_results')} ({len(self.filtered_events)} {events_word})"
        filtered_radio = QRadioButton(filtered_text)
        filtered_radio.setProperty('scope', self.SCOPE_FILTERED)
        filtered_radio.setChecked(True)  # Default to filtered
        filtered_radio.setEnabled(len(self.filtered_events) > 0)
        self.scope_group.addButton(filtered_radio)
        scope_layout.addWidget(filtered_radio)
        
        # All data option
        all_data_text = f"{self.translator.tr('export_all_data')} ({len(self.all_events)} {events_word})"
        all_radio = QRadioButton(all_data_text)
        all_radio.setProperty('scope', self.SCOPE_ALL)
        all_radio.setEnabled(len(self.all_events) > 0)
        self.scope_group.addButton(all_radio)
        scope_layout.addWidget(all_radio)
        
        layout.addWidget(scope_group)
        
        # Format selection
        format_group = QGroupBox(self.translator.tr('export_format'))
        format_layout = QVBoxLayout(format_group)
        
        self.format_group = QButtonGroup(self)
        
        formats = [
            (self.FORMAT_WORD, '📘', 'export_word_label'),
            (self.FORMAT_EXCEL, '📗', 'export_excel_label'),
            (self.FORMAT_PDF, '📕', 'export_pdf_label'),
        ]
        
        for fmt, icon, label_key in formats:
            label_text = f"{icon} {self.translator.tr(label_key)}"
            radio = QRadioButton(label_text)
            radio.setProperty('format', fmt)
            if fmt == self.FORMAT_WORD:
                radio.setChecked(True)
            self.format_group.addButton(radio)
            format_layout.addWidget(radio)
        
        layout.addWidget(format_group)
        
        # Export options
        options_group = QGroupBox(self.translator.tr('export_options'))
        options_layout = QVBoxLayout(options_group)
        
        # Include system header
        self.include_header_check = QCheckBox(self.translator.tr('export_include_system_header'))
        self.include_header_check.setChecked(self.include_header)
        self.include_header_check.setToolTip(self.translator.tr('export_include_header_hint'))
        options_layout.addWidget(self.include_header_check)
        
        # Preserve formatting
        self.preserve_format_check = QCheckBox(self.translator.tr('export_preserve_format'))
        self.preserve_format_check.setChecked(True)
        self.preserve_format_check.setToolTip(self.translator.tr('export_preserve_format_hint'))
        options_layout.addWidget(self.preserve_format_check)
        
        # Open after export
        self.open_after_check = QCheckBox(self.translator.tr('export_open_after'))
        self.open_after_check.setChecked(self.open_after_export)
        options_layout.addWidget(self.open_after_check)
        
        layout.addWidget(options_group)
        
        # File path
        file_group = QGroupBox(self.translator.tr('export_file'))
        file_layout = QFormLayout(file_group)
        
        file_path_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText(self.translator.tr('export_select_file'))
        file_path_layout.addWidget(self.file_path_edit)
        
        browse_btn = QPushButton(self.translator.tr('btn_browse'))
        browse_btn.clicked.connect(self.browse_file)
        file_path_layout.addWidget(browse_btn)
        
        file_layout.addRow(self.translator.tr('export_file_path'), file_path_layout)
        
        layout.addWidget(file_group)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_cancel = QPushButton(self.translator.tr('btn_cancel'))
        self.btn_cancel.setAutoDefault(False)
        self.btn_cancel.setDefault(False)
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        self.btn_export = QPushButton(self.translator.tr('btn_export'))
        self.btn_export.setStyleSheet(AppStyles.get_component_style('export_btn'))
        self.btn_export.setAutoDefault(False)
        self.btn_export.setDefault(False)
        self.btn_export.clicked.connect(self.accept_export)
        button_layout.addWidget(self.btn_export)
        
        layout.addLayout(button_layout)
    
    def browse_file(self):
        """Browse for export file location"""
        # Get selected format
        selected_radio = self.format_group.checkedButton()
        if selected_radio:
            self.selected_format = selected_radio.property('format')
        
        # Set file filter based on format
        all_files = self.translator.tr('file_filter_all_files')
        format_filters = {
            self.FORMAT_WORD: f"{self.translator.tr('export_word_label')} (*.docx);;{all_files}",
            self.FORMAT_EXCEL: f"{self.translator.tr('export_excel_label')} (*.xlsx);;{all_files}",
            self.FORMAT_PDF: f"{self.translator.tr('export_pdf_label')} (*.pdf);;{all_files}",
        }
        
        file_filter = format_filters.get(self.selected_format, 'All Files (*)')
        
        # Generate default filename
        default_name = f"timeline_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        format_extensions = {
            self.FORMAT_WORD: '.docx',
            self.FORMAT_EXCEL: '.xlsx',
            self.FORMAT_PDF: '.pdf',
        }
        default_name += format_extensions.get(self.selected_format, '.docx')
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.translator.tr('export_save_as'),
            default_name,
            file_filter
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            self.export_path = file_path
    
    def accept_export(self):
        """Accept export and validate"""
        # Get selected format
        selected_radio = self.format_group.checkedButton()
        if selected_radio:
            self.selected_format = selected_radio.property('format')
        
        # Get selected scope
        scope_radio = self.scope_group.checkedButton()
        if scope_radio:
            self.selected_scope = scope_radio.property('scope')
        
        # Get options
        self.include_header = self.include_header_check.isChecked()
        self.preserve_format = self.preserve_format_check.isChecked()
        self.open_after_export = self.open_after_check.isChecked()
        
        # Validate file path
        if not self.file_path_edit.text():
            self.browse_file()
        
        if not self.file_path_edit.text():
            QMessageBox.warning(
                self,
                self.translator.tr('msg_warning'),
                self.translator.tr('export_select_file_warning')
            )
            return
        
        self.export_path = self.file_path_edit.text()
        
        # Validate that we have data to export
        events_to_export = self.get_events_to_export()
        if not events_to_export:
            QMessageBox.warning(
                self,
                self.translator.tr('msg_warning'),
                self.translator.tr('export_no_data')
            )
            return
        
        self.accept()
    
    def get_events_to_export(self) -> List[Dict]:
        """Get events to export based on selected scope"""
        if self.selected_scope == self.SCOPE_CURRENT_PAGE:
            return self.current_page_events
        elif self.selected_scope == self.SCOPE_FILTERED:
            return self.filtered_events
        else:  # SCOPE_ALL
            return self.all_events
    
    def get_export_settings(self) -> Dict:
        """Get export settings as dictionary"""
        return {
            'format': self.selected_format,
            'scope': self.selected_scope,
            'include_header': self.include_header,
            'preserve_format': self.preserve_format,
            'open_after_export': self.open_after_export,
            'file_path': self.export_path,
            'events': self.get_events_to_export()
        }
