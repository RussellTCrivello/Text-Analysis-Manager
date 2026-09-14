"""
Export Preview Dialog
Comprehensive export dialog with data preview, column selection, and format options
"""
import os
import subprocess
import sys
from datetime import datetime
from typing import List, Tuple, Set, Dict, Optional, Any

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QScrollArea, QWidget, QTabWidget, QTableWidget,
    QTableWidgetItem, QGroupBox, QRadioButton, QButtonGroup,
    QComboBox, QLineEdit, QSpinBox, QHeaderView, QFrame,
    QFileDialog, QMessageBox, QSplitter, QGridLayout, QFormLayout,
    QProgressBar, QApplication
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor, QIcon

from icons.icon_manager import setup_icon_button
from translations.translations import TranslationManager
from utils.logger import get_logger
from utils.print_utils import ExportSettings
from styles.styles import AppStyles

logger = get_logger(__name__)


class ExportPreviewDialog(QDialog):
    """
    Comprehensive export dialog with:
    - Data preview (first N rows)
    - Column selection
    - Export format selection (Excel, CSV, Word, PDF)
    - Option to open file after export
    - Data statistics summary
    """
    
    # Export formats
    FORMAT_EXCEL = 'excel'
    FORMAT_CSV = 'csv'
    FORMAT_WORD = 'word'
    FORMAT_PDF = 'pdf'
    FORMAT_JSON = 'json'
    FORMAT_XML = 'xml'
    FORMAT_JSON_LINES = 'jsonl'
    
    def __init__(self, parent=None, data: List[Dict] = None,
                 columns: List[Tuple[str, str]] = None,
                 translator: TranslationManager = None,
                 table_name: str = "data",
                 default_format: str = FORMAT_EXCEL):
        """
        Initialize export preview dialog
        
        Args:
            parent: Parent widget
            data: List of dictionaries containing the data to export
            columns: List of tuples (key, header) for displayed columns
            translator: Translation manager
            table_name: Name of the table/data being exported
            default_format: Default export format
        """
        super().__init__(parent)
        self.translator = translator or TranslationManager()
        self.data = data or []
        self.columns = columns or []
        self.table_name = table_name
        
        # Load settings from ExportSettings
        self.export_settings = ExportSettings()
        self.default_format = default_format or self.export_settings.default_format
        self.selected_format = self.default_format
        self.export_path = None
        self.open_after_export = self.export_settings.open_after_export
        self.include_header = self.export_settings.include_header
        self.translate_fields = self.export_settings.translate_fields
        
        # Get all available keys from data
        self.all_keys = set()
        for row in self.data:
            self.all_keys.update(row.keys())
        
        self._apply_rtl_direction()
        try:
            self.setup_ui()
            self.populate_data()
            self._apply_rtl_direction()
        except Exception as e:
            logger.error(f"Error initializing ExportPreviewDialog: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                self.translator.tr('msg_error'),
                f"Error initializing export dialog: {str(e)}"
            )
            raise
    
    def _apply_rtl_direction(self):
        """Apply RTL/LTR direction based on current language"""
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)
        for child in self.findChildren(QWidget):
            child.setLayoutDirection(direction)
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle(self.translator.tr('export_preview_title'))
        # Apply fixed size to prevent resizing on button clicks or content changes
        from styles.styles import AppStyles
        AppStyles.apply_fixed_size(self, 900, 700)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid (rounding 10px to 16px)
        
        # Main splitter
        splitter = QSplitter(Qt.Vertical)
        
        # Top: Data preview and statistics
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Statistics summary
        stats_frame = QFrame()
        stats_frame.setStyleSheet(AppStyles.get_component_style('export_stats_frame'))
        stats_layout = QHBoxLayout(stats_frame)
        
        # Total records
        total_label = QLabel(f"📊 {self.translator.tr('export_total_records')}: ")
        total_label.setStyleSheet(AppStyles.get_component_style('export_stats_label'))
        self.total_count = QLabel(str(len(self.data)))
        self.total_count.setStyleSheet(AppStyles.get_component_style('export_stats_count'))
        stats_layout.addWidget(total_label)
        stats_layout.addWidget(self.total_count)
        
        stats_layout.addSpacing(30)
        
        # Columns count
        cols_label = QLabel(f"📋 {self.translator.tr('export_columns')}: ")
        cols_label.setStyleSheet(AppStyles.get_component_style('export_stats_label'))
        self.cols_count = QLabel(str(len(self.all_keys)))
        self.cols_count.setStyleSheet(AppStyles.get_component_style('export_stats_count_green'))
        stats_layout.addWidget(cols_label)
        stats_layout.addWidget(self.cols_count)
        
        stats_layout.addStretch()
        
        # Preview limit
        preview_label = QLabel(self.translator.tr('export_preview_rows') + ":")
        self.preview_spin = QSpinBox()
        self.preview_spin.setRange(5, 100)
        self.preview_spin.setValue(20)
        self.preview_spin.valueChanged.connect(self.update_preview)
        stats_layout.addWidget(preview_label)
        stats_layout.addWidget(self.preview_spin)
        
        top_layout.addWidget(stats_frame)
        
        # Preview table
        preview_label = QLabel(f"👁️ {self.translator.tr('export_data_preview')}")
        preview_label.setStyleSheet(AppStyles.get_component_style('export_stats_label'))
        top_layout.addWidget(preview_label)
        
        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setStyleSheet(AppStyles.get_component_style('export_preview_table'))
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.setEditTriggers(QTableWidget.NoEditTriggers)
        top_layout.addWidget(self.preview_table)
        
        splitter.addWidget(top_widget)
        
        # Bottom: Options panel
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left: Column selection
        column_group = QGroupBox(self.translator.tr('export_select_columns'))
        column_layout = QVBoxLayout(column_group)
        
        # Select all/deselect all buttons
        btn_row = QHBoxLayout()
        self.btn_select_all = QPushButton(self.translator.tr('btn_select_all'))
        self.btn_select_all.setAutoDefault(False)
        self.btn_select_all.setDefault(False)
        self.btn_select_all.clicked.connect(self.select_all_columns)
        self.btn_deselect_all = QPushButton(self.translator.tr('btn_deselect_all'))
        self.btn_deselect_all.setAutoDefault(False)
        self.btn_deselect_all.setDefault(False)
        self.btn_deselect_all.clicked.connect(self.deselect_all_columns)
        btn_row.addWidget(self.btn_select_all)
        btn_row.addWidget(self.btn_deselect_all)
        btn_row.addStretch()
        column_layout.addLayout(btn_row)
        
        # Scrollable column list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(250)  # Increased to accommodate width inputs
        
        scroll_widget = QWidget()
        self.column_check_layout = QVBoxLayout(scroll_widget)
        self.column_check_layout.setAlignment(Qt.AlignTop)
        self.column_check_layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid (rounding 2px to 8px)
        
        scroll.setWidget(scroll_widget)
        column_layout.addWidget(scroll)
        
        # Selected columns count
        self.selected_cols_label = QLabel()
        self.selected_cols_label.setStyleSheet(AppStyles.get_component_style('status_label_muted'))
        column_layout.addWidget(self.selected_cols_label)
        
        bottom_layout.addWidget(column_group)
        
        # Right: Export options
        options_group = QGroupBox(self.translator.tr('export_options'))
        options_layout = QVBoxLayout(options_group)
        
        # Format selection
        format_label = QLabel(self.translator.tr('export_format') + ":")
        format_label.setStyleSheet(AppStyles.get_component_style('export_format_label'))
        options_layout.addWidget(format_label)
        
        self.format_group = QButtonGroup(self)
        format_grid = QGridLayout()
        
        formats = [
            (self.FORMAT_EXCEL, '📗 Excel (.xlsx)', 'export_excel_desc'),
            (self.FORMAT_CSV, '📄 CSV (.csv)', 'export_csv_desc'),
            (self.FORMAT_WORD, '📘 Word (.docx)', 'export_word_desc'),
            (self.FORMAT_PDF, '📕 PDF (.pdf)', 'export_pdf_desc'),
            (self.FORMAT_JSON, '📋 JSON (.json)', 'export_json_desc'),
            (self.FORMAT_XML, '📄 XML (.xml)', 'export_xml_desc'),
            (self.FORMAT_JSON_LINES, '📝 JSON Lines (.jsonl)', 'export_jsonl_desc'),
        ]
        
        self.format_radios = {}
        for i, (fmt, label, desc_key) in enumerate(formats):
            radio = QRadioButton(label)
            radio.setProperty('format', fmt)
            if fmt == self.default_format:
                radio.setChecked(True)
            self.format_radios[fmt] = radio
            self.format_group.addButton(radio)
            format_grid.addWidget(radio, i // 2, i % 2)
        
        options_layout.addLayout(format_grid)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(AppStyles.get_component_style('export_separator'))
        options_layout.addWidget(sep)
        
        # Additional options
        self.include_header_check = QCheckBox(self.translator.tr('export_include_header'))
        self.include_header_check.setChecked(self.include_header)
        self.include_header_check.setStyleSheet(AppStyles.get_component_style('export_checkbox_bold'))
        self.include_header_check.setToolTip(self.translator.tr('export_include_header_hint'))
        options_layout.addWidget(self.include_header_check)
        
        self.translate_fields_check = QCheckBox(self.translator.tr('export_translate_fields'))
        self.translate_fields_check.setChecked(self.translate_fields)
        self.translate_fields_check.setStyleSheet(AppStyles.get_component_style('export_checkbox_bold'))
        self.translate_fields_check.setToolTip(self.translator.tr('export_translate_fields_hint'))
        self.translate_fields_check.stateChanged.connect(self.on_translate_fields_changed)
        options_layout.addWidget(self.translate_fields_check)
        
        self.open_after_check = QCheckBox(self.translator.tr('export_open_after'))
        self.open_after_check.setChecked(self.open_after_export)
        self.open_after_check.setStyleSheet(AppStyles.get_component_style('export_checkbox_green'))
        options_layout.addWidget(self.open_after_check)
        
        # File name preview
        filename_layout = QFormLayout()
        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText(self.translator.tr('export_filename_hint'))
        self.update_filename_preview()
        filename_layout.addRow(self.translator.tr('export_filename') + ":", self.filename_edit)
        options_layout.addLayout(filename_layout)
        
        # Connect format change to filename update
        self.format_group.buttonClicked.connect(self.on_format_changed)
        
        options_layout.addStretch()
        bottom_layout.addWidget(options_group)
        
        splitter.addWidget(bottom_widget)
        splitter.setSizes([400, 250])
        
        layout.addWidget(splitter)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        # Export button (prominent)
        self.btn_export = QPushButton(self.translator.tr('btn_export'))
        self.btn_export.setStyleSheet(AppStyles.get_component_style('export_btn'))
        self.btn_export.setMinimumWidth(150)
        # Disable autoDefault to prevent Enter key from triggering buttons unexpectedly
        self.btn_export.setAutoDefault(False)
        self.btn_export.setDefault(False)
        self.btn_export.clicked.connect(self.do_export)
        
        self.btn_cancel = QPushButton(self.translator.tr('btn_cancel'))
        self.btn_cancel.setStyleSheet(AppStyles.get_component_style('export_cancel_btn'))
        self.btn_cancel.setAutoDefault(False)
        self.btn_cancel.setDefault(False)
        self.btn_cancel.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.btn_cancel)
        button_layout.addWidget(self.btn_export)
        
        layout.addLayout(button_layout)
        
        # Store checkboxes and width inputs
        self.column_checkboxes = {}
        self.column_width_inputs = {}  # Store width spinboxes
        
        # Populate column checkboxes
        self.populate_columns()
    
    def populate_columns(self):
        """Populate column selection checkboxes"""
        try:
            # Clear existing
            for i in reversed(range(self.column_check_layout.count())):
                widget = self.column_check_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            self.column_checkboxes.clear()
            self.column_width_inputs.clear()
            
            # Check if we have any data or columns
            if not self.all_keys and not self.columns:
                logger.warning("No columns or data keys available for export")
                return
            
            # Build columns list
            column_dict = {col[0]: col[1] for col in self.columns} if self.columns else {}
            displayed_keys = [col[0] for col in self.columns] if self.columns else []
            
            # Calculate default width per column (equal distribution)
            total_cols = len(displayed_keys) + len([k for k in self.all_keys if k not in displayed_keys])
            if total_cols == 0:
                logger.warning("No columns to display in export dialog")
                return
            default_width = max(5, min(30, 100 // total_cols))
            
            # Get saved column widths and selection from settings
            saved_widths = self.export_settings.column_widths
            saved_selected = set(self.export_settings.last_selected_columns)
            
            # Add displayed columns first (bold)
            for key in displayed_keys:
                header = column_dict.get(key, self.format_field_name(key))
                width = saved_widths.get(key, default_width)
                is_selected = key in saved_selected if saved_selected else True
                self.add_column_checkbox(key, header, is_primary=True, default_width=width, is_checked=is_selected)
            
            # Add other available fields
            other_keys = sorted([k for k in self.all_keys if k not in displayed_keys])
            for key in other_keys:
                header = self.format_field_name(key)
                width = saved_widths.get(key, default_width)
                is_selected = key in saved_selected if saved_selected else True
                self.add_column_checkbox(key, header, is_primary=False, default_width=width, is_checked=is_selected)
            
            self.update_selected_count()
        except Exception as e:
            logger.error(f"Error populating columns: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                self.translator.tr('msg_error'),
                f"Error setting up export dialog: {str(e)}"
            )
    
    def add_column_checkbox(self, key: str, header: str, is_primary: bool, default_width: int = 10, is_checked: bool = True):
        """Add a column checkbox with width ratio input"""
        # Create a horizontal layout for this column row
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        # Use 8px grid spacing
        row_margin_h = AppStyles.get_spacing(1)  # 8px horizontal (rounding 5px to 8px)
        row_margin_v = AppStyles.get_spacing(1)  # 8px vertical (rounding 2px to 8px)
        row_layout.setContentsMargins(row_margin_h, row_margin_v, row_margin_h, row_margin_v)
        row_layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid
        
        # Checkbox
        checkbox = QCheckBox(header)
        checkbox.setChecked(is_checked)
        checkbox.setProperty('column_key', key)
        checkbox.stateChanged.connect(self.on_column_toggled)
        
        if is_primary:
            checkbox.setStyleSheet(AppStyles.get_component_style('export_checkbox_primary'))
        else:
            checkbox.setStyleSheet(AppStyles.get_component_style('export_checkbox_secondary'))
        
        row_layout.addWidget(checkbox, 1)
        
        # Width label
        try:
            width_text = self.translator.tr('export_width')
        except:
            width_text = 'Width'
        width_label = QLabel(width_text + ":")
        width_label.setStyleSheet(AppStyles.get_component_style('export_width_label'))
        width_label.setMinimumWidth(50)
        row_layout.addWidget(width_label)
        
        # Width spinbox (percentage)
        width_spin = QSpinBox()
        width_spin.setRange(5, 60)
        width_spin.setSuffix('%')
        width_spin.setValue(default_width)
        width_spin.setMinimumWidth(70)
        width_spin.setMaximumWidth(80)
        width_spin.setStyleSheet(AppStyles.get_component_style('export_width_spin'))
        width_spin.setProperty('column_key', key)
        width_spin.valueChanged.connect(self.on_width_changed)
        
        row_layout.addWidget(width_spin)
        row_layout.addStretch()
        
        self.column_checkboxes[key] = checkbox
        self.column_width_inputs[key] = width_spin
        self.column_check_layout.addWidget(row_widget)
    
    def format_field_name(self, key: str) -> str:
        """Format field name for display"""
        return key.replace('_', ' ').title()
    
    def translate_field_name(self, key: str) -> str:
        """Translate field name based on current language"""
        # Comprehensive map of all field names to translation keys
        field_translation_map = {
            # Common fields
            'id': 'lbl_id',
            'name': 'lbl_name',
            'type': 'lbl_type',
            'title': 'lbl_title',
            'note': 'lbl_note',
            'description': 'lbl_description',
            'importance': 'lbl_importance',
            
            # Sources table fields
            'link': 'lbl_link_sources',
            'link_sources': 'lbl_link_sources',
            'country': 'lbl_country',
            'city': 'lbl_city',
            'accounts': 'lbl_accounts',
            'ownership': 'lbl_ownership',
            
            # Contents table fields
            'content_data': 'lbl_content_data',
            'attachments': 'lbl_attachments',
            'sources_id': 'lbl_source',
            'source_id': 'lbl_source',
            'source': 'lbl_source',
            'source_name': 'lbl_source',
            
            # Content Analysis table fields
            'content_id': 'lbl_content_id',
            'classification': 'lbl_classification',
            'list_names_people': 'lbl_people',
            'list_names_places': 'lbl_places',
            'list_coordinates': 'lbl_coordinates',
            'list_sides': 'lbl_sides',
            'people': 'lbl_people',
            'people_names': 'lbl_people',
            'places': 'lbl_places',
            'place_names': 'lbl_places',
            'coordinates': 'lbl_coordinates',
            'sides': 'lbl_sides',
            
            # Date fields
            'date_entry': 'lbl_date_entry',
            'date_creation': 'lbl_date_creation',
            'date_modified': 'lbl_date_modified',
            'date_content': 'lbl_date_content',
            'date_analysis': 'lbl_date_analysis',
            
            # All Data tab combined fields
            'record_type': 'lbl_record_type',
            'content_title': 'lbl_title',
            'content_importance': 'lbl_importance',
            'content_date_creation': 'lbl_date_creation',
            'source_date_creation': 'lbl_date_creation',
            'source_date_entry': 'lbl_date_entry',
            'analysis_date_creation': 'lbl_date_creation',
            
            # Report specific fields
            'total': 'report_total',
            'count': 'report_count',
            'percentage': 'report_percentage',
            'average': 'report_average',
            'sum': 'report_sum',
            'category': 'report_category',
            
            # Size and file fields
            'size': 'lbl_size',
            'filename': 'lbl_filename',
            'date': 'lbl_date',
            'actions': 'lbl_actions',
        }
        
        # Get translation key for the field
        tr_key = field_translation_map.get(key.lower())
        if tr_key:
            translated = self.translator.tr(tr_key)
            # Only return translation if it's different from the key (meaning translation exists)
            if translated != tr_key:
                return translated
        
        # Fallback to formatted field name
        return self.format_field_name(key)
    
    def on_translate_fields_changed(self):
        """Handle translate fields checkbox change"""
        self.translate_fields = self.translate_fields_check.isChecked()
        # Update column checkboxes with translated/original names
        self.update_column_display_names()
        self.update_preview()
    
    def update_column_display_names(self):
        """Update column checkbox labels based on translation setting"""
        column_dict = {col[0]: col[1] for col in self.columns} if self.columns else {}
        
        for key, checkbox in self.column_checkboxes.items():
            if self.translate_fields:
                # Use translated name
                display_name = self.translate_field_name(key)
            else:
                # Use original name from columns or formatted key
                display_name = column_dict.get(key, self.format_field_name(key))
            checkbox.setText(display_name)
    
    def on_column_toggled(self):
        """Handle column checkbox toggle"""
        self.update_selected_count()
        self.update_preview()
    
    def on_width_changed(self):
        """Handle width ratio change"""
        # Update total width display if needed
        pass
    
    def update_selected_count(self):
        """Update selected columns count label"""
        selected = sum(1 for cb in self.column_checkboxes.values() if cb.isChecked())
        total = len(self.column_checkboxes)
        self.selected_cols_label.setText(
            f"{self.translator.tr('export_selected')}: {selected} / {total}"
        )
    
    def select_all_columns(self):
        """Select all columns"""
        for checkbox in self.column_checkboxes.values():
            checkbox.setChecked(True)
    
    def deselect_all_columns(self):
        """Deselect all columns"""
        for checkbox in self.column_checkboxes.values():
            checkbox.setChecked(False)
    
    def get_selected_columns(self) -> List[Tuple[str, str]]:
        """Get list of selected columns as (key, header) tuples"""
        selected = []
        column_dict = {col[0]: col[1] for col in self.columns}
        
        # Check if translation is enabled
        should_translate = getattr(self, 'translate_fields_check', None) and self.translate_fields_check.isChecked()
        
        for key, checkbox in self.column_checkboxes.items():
            if checkbox.isChecked():
                if should_translate:
                    # Use translated header
                    header = self.translate_field_name(key)
                else:
                    # Use original header
                    header = column_dict.get(key, self.format_field_name(key))
                selected.append((key, header))
        
        return selected
    
    def get_column_widths(self) -> Dict[str, int]:
        """Get column width ratios as dictionary {column_key: width_percentage}"""
        widths = {}
        selected_keys = set()
        
        # First, get all selected column keys
        for key, checkbox in self.column_checkboxes.items():
            if checkbox.isChecked():
                selected_keys.add(key)
        
        # Then, get widths for selected columns
        for key in selected_keys:
            if key in self.column_width_inputs:
                width_value = self.column_width_inputs[key].value()
                if width_value > 0:  # Only include positive widths
                    widths[key] = width_value
                    logger.debug(f"Column width for {key}: {width_value}%")
        
        logger.info(f"Retrieved column widths for {len(widths)}/{len(selected_keys)} selected columns")
        if widths:
            total = sum(widths.values())
            logger.info(f"Total width percentage: {total}%")
        
        return widths
    
    def populate_data(self):
        """Populate preview table with data"""
        self.update_preview()
    
    def update_preview(self):
        """Update the preview table"""
        selected_columns = self.get_selected_columns()
        if not selected_columns:
            self.preview_table.clear()
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)
            return
        
        preview_count = min(self.preview_spin.value(), len(self.data))
        preview_data = self.data[:preview_count]
        
        # Setup table
        self.preview_table.setColumnCount(len(selected_columns))
        self.preview_table.setRowCount(len(preview_data))
        
        # Set headers
        headers = [col[1] for col in selected_columns]
        self.preview_table.setHorizontalHeaderLabels(headers)
        
        # Populate data
        for row_idx, row_data in enumerate(preview_data):
            for col_idx, (key, _) in enumerate(selected_columns):
                value = row_data.get(key, '')
                if value is None:
                    value = ''
                elif isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M')
                else:
                    value = str(value)
                
                # Truncate long values for preview
                if len(value) > 50:
                    value = value[:47] + '...'
                
                item = QTableWidgetItem(value)
                self.preview_table.setItem(row_idx, col_idx, item)
        
        # Resize columns
        self.preview_table.resizeColumnsToContents()
    
    def on_format_changed(self):
        """Handle format selection change"""
        for fmt, radio in self.format_radios.items():
            if radio.isChecked():
                self.selected_format = fmt
                break
        self.update_filename_preview()
    
    def update_filename_preview(self):
        """Update filename preview based on selected format"""
        extensions = {
            self.FORMAT_EXCEL: '.xlsx',
            self.FORMAT_CSV: '.csv',
            self.FORMAT_WORD: '.docx',
            self.FORMAT_PDF: '.pdf',
            self.FORMAT_JSON: '.json',
            self.FORMAT_XML: '.xml',
            self.FORMAT_JSON_LINES: '.jsonl'
        }
        
        ext = extensions.get(self.selected_format, '.xlsx')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"{self.table_name}_{timestamp}{ext}"
        
        current_text = self.filename_edit.text()
        if not current_text or any(current_text.endswith(e) for e in extensions.values()):
            self.filename_edit.setText(default_name)
    
    def do_export(self):
        """Execute the export"""
        selected_columns = self.get_selected_columns()
        if not selected_columns:
            QMessageBox.warning(
                self,
                self.translator.tr('msg_warning'),
                self.translator.tr('export_no_columns_selected')
            )
            return
        
        # Get file extension and filter
        filters = {
            self.FORMAT_EXCEL: ('Excel Files (*.xlsx)', '.xlsx'),
            self.FORMAT_CSV: ('CSV Files (*.csv)', '.csv'),
            self.FORMAT_WORD: ('Word Documents (*.docx)', '.docx'),
            self.FORMAT_PDF: ('PDF Files (*.pdf)', '.pdf'),
            self.FORMAT_JSON: ('JSON Files (*.json)', '.json'),
            self.FORMAT_XML: ('XML Files (*.xml)', '.xml'),
            self.FORMAT_JSON_LINES: ('JSON Lines Files (*.jsonl)', '.jsonl')
        }
        
        file_filter, ext = filters.get(self.selected_format, filters[self.FORMAT_EXCEL])
        
        # Get filename
        suggested_name = self.filename_edit.text()
        if not suggested_name.endswith(ext):
            suggested_name = suggested_name.rsplit('.', 1)[0] + ext
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.translator.tr('btn_export'),
            suggested_name,
            f"{file_filter};;All Files (*)"
        )
        
        if not filename:
            return
        
        self.export_path = filename
        self.open_after_export = self.open_after_check.isChecked()
        
        # Store selected columns for export
        self.selected_columns_for_export = selected_columns
        
        # Save settings to ExportSettings
        self.export_settings.default_format = self.selected_format
        self.export_settings.open_after_export = self.open_after_export
        self.export_settings.include_header = self.include_header_check.isChecked()
        self.export_settings.translate_fields = self.translate_fields_check.isChecked()
        self.export_settings.column_widths = self.get_column_widths()
        self.export_settings.last_selected_columns = [col[0] for col in selected_columns]
        self.export_settings.save_settings()
        
        self.accept()
    
    def get_export_settings(self) -> Dict[str, Any]:
        """Get all export settings"""
        return {
            'format': self.selected_format,
            'path': self.export_path,
            'columns': self.get_selected_columns(),
            'column_widths': self.get_column_widths(),
            'open_after': self.open_after_export,
            'include_header': self.include_header_check.isChecked() if hasattr(self, 'include_header_check') else False,
            'translate_fields': self.translate_fields_check.isChecked() if hasattr(self, 'translate_fields_check') else False,
            'data': self.data
        }
    
    @staticmethod
    def open_file(filepath: str):
        """Open a file with the default system application"""
        try:
            if sys.platform == 'win32':
                os.startfile(filepath)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', filepath], check=True)
            else:  # Linux
                subprocess.run(['xdg-open', filepath], check=True)
            return True
        except Exception as e:
            logger.error(f"Error opening file: {e}")
            return False
