"""
Data Import Dialog with Validation and Preview
Provides comprehensive import functionality with preview, validation, and rollback support
"""
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum, auto

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QGroupBox, QComboBox, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QProgressBar,
    QFileDialog, QTabWidget, QWidget, QFormLayout, QSpinBox,
    QTextEdit, QSplitter, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QColor, QFont

from translations.translations import TranslationManager
from styles.styles import AppStyles
from utils.logger import get_logger
from utils.table_ui import configure_table, set_item_with_tooltip
from utils.error_handler import ErrorHandler, AppError, ErrorSeverity, ErrorCategory
from db.db_manager import DatabaseManager
from icons.icon_manager import get_icon

logger = get_logger(__name__)


class ValidationStatus(Enum):
    """Validation status for import rows"""
    VALID = auto()
    WARNING = auto()
    ERROR = auto()
    SKIPPED = auto()


class ImportValidationRule:
    """Defines a validation rule for import data"""
    
    def __init__(self, field: str, rule_type: str, 
                 value: Any = None, message: str = ""):
        self.field = field
        self.rule_type = rule_type  # required, max_length, pattern, type, unique, foreign_key
        self.value = value
        self.message = message
    
    def validate(self, data: Any, all_data: List[Dict] = None) -> Tuple[bool, str]:
        """Validate data against this rule"""
        if self.rule_type == 'required':
            if data is None or str(data).strip() == '':
                return False, self.message or f"Field '{self.field}' is required"
            return True, ""
        
        elif self.rule_type == 'max_length':
            if data and len(str(data)) > self.value:
                return False, self.message or f"Field '{self.field}' exceeds max length of {self.value}"
            return True, ""
        
        elif self.rule_type == 'type':
            try:
                if self.value == 'int':
                    int(data) if data else None
                elif self.value == 'float':
                    float(data) if data else None
                elif self.value == 'date':
                    if data:
                        datetime.strptime(str(data)[:10], '%Y-%m-%d')
                return True, ""
            except (ValueError, TypeError):
                return False, self.message or f"Field '{self.field}' must be of type {self.value}"
        
        elif self.rule_type == 'unique':
            if all_data and data:
                occurrences = sum(1 for row in all_data if row.get(self.field) == data)
                if occurrences > 1:
                    return False, self.message or f"Field '{self.field}' must be unique"
            return True, ""
        
        return True, ""


class ImportWorker(QThread):
    """Worker thread for performing import operations"""
    
    progress_updated = pyqtSignal(int, int)  # current, total
    row_imported = pyqtSignal(int, bool, str)  # row_index, success, message
    import_completed = pyqtSignal(int, int, list)  # success_count, error_count, errors
    
    def __init__(self, table_name: str, data: List[Dict], 
                 column_mapping: Dict[str, str], parent=None):
        super().__init__(parent)
        self.table_name = table_name
        self.data = data
        self.column_mapping = column_mapping
        self._cancelled = False
    
    def cancel(self):
        """Cancel the import operation"""
        self._cancelled = True
    
    def run(self):
        """Execute the import"""
        success_count = 0
        error_count = 0
        errors = []
        total = len(self.data)
        
        for i, row in enumerate(self.data):
            if self._cancelled:
                break
            
            self.progress_updated.emit(i + 1, total)
            
            try:
                # Map columns
                mapped_row = {}
                for csv_col, db_col in self.column_mapping.items():
                    if db_col and csv_col in row:
                        mapped_row[db_col] = row[csv_col]
                
                # Insert based on table
                if self.table_name == 'sources':
                    DatabaseManager.add_source(mapped_row)
                elif self.table_name == 'contents':
                    DatabaseManager.add_content(mapped_row)
                elif self.table_name == 'content_analysis':
                    DatabaseManager.add_content_analysis(mapped_row)
                else:
                    raise ValueError(f"Unsupported import table: {self.table_name}")
                
                success_count += 1
                self.row_imported.emit(i, True, "")
                
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                errors.append({'row': i, 'error': error_msg})
                self.row_imported.emit(i, False, error_msg)
                logger.error(f"Import error at row {i}: {e}")
        
        self.import_completed.emit(success_count, error_count, errors)


class ImportPreviewDialog(QDialog):
    """Dialog for previewing and validating import data"""
    
    import_completed = pyqtSignal(int, int)  # success_count, error_count
    
    def __init__(self, parent, translator: TranslationManager, table_name: str):
        super().__init__(parent)
        self.translator = translator
        self.table_name = table_name
        self.import_data: List[Dict] = []
        self.validation_results: List[Dict] = []
        self.column_mapping: Dict[str, str] = {}
        self.import_worker: Optional[ImportWorker] = None
        
        self.setWindowTitle(self._tr('import_title', 'Import Data'))
        # Apply fixed size to prevent resizing on button clicks or content changes
        from styles.styles import AppStyles
        AppStyles.apply_fixed_size(self, 1000, 700)
        self._apply_rtl_direction()
        self.setup_ui()
        self._apply_rtl_direction()
        self.setup_validation_rules()
    
    def _apply_rtl_direction(self):
        """Apply RTL/LTR direction based on current language"""
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)
        for child in self.findChildren(QWidget):
            child.setLayoutDirection(direction)
    
    def _tr(self, key: str, default: str, **kwargs) -> str:
        """Translate text, using the supplied fallback when a key is absent."""
        if self.translator and hasattr(self.translator, 'tr'):
            translated = self.translator.tr(key, **kwargs)
            if translated != key:
                return translated
        try:
            return default.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return default
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        m = AppStyles.get_spacing(2)
        layout.setContentsMargins(m, m, m, m)
        layout.setSpacing(AppStyles.get_spacing(2))
        
        # Tab widget for steps
        self.tab_widget = QTabWidget()
        
        # Step 1: File Selection
        file_tab = QWidget()
        file_layout = QVBoxLayout(file_tab)
        
        file_group = QGroupBox(self._tr('import_select_file', 'Select Import File'))
        file_group_layout = QVBoxLayout(file_group)
        
        file_btn_layout = QHBoxLayout()
        file_btn_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        file_btn_layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid spacing
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setPlaceholderText(self._tr('import_select_file_hint', 'Click Browse to select a file...'))
        file_btn_layout.addWidget(self.file_path_edit, alignment=Qt.AlignVCenter)
        
        btn_browse = QPushButton(self._tr('btn_browse', 'Browse'))
        btn_browse.clicked.connect(self.browse_file)
        file_btn_layout.addWidget(btn_browse, alignment=Qt.AlignVCenter)
        
        file_group_layout.addLayout(file_btn_layout)
        
        # File format options
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel(self._tr('import_format', 'File Format:')))
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(['CSV', 'JSON'])
        format_layout.addWidget(self.format_combo)
        
        format_layout.addWidget(QLabel(self._tr('import_encoding', 'Encoding:')))
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(['utf-8', 'utf-8-sig', 'latin-1', 'cp1256', 'cp1252'])
        format_layout.addWidget(self.encoding_combo)
        
        format_layout.addWidget(QLabel(self._tr('import_delimiter', 'Delimiter:')))
        self.delimiter_combo = QComboBox()
        self.delimiter_combo.addItems([',', ';', '\t', '|'])
        format_layout.addWidget(self.delimiter_combo)
        
        format_layout.addStretch()
        file_group_layout.addLayout(format_layout)
        
        file_layout.addWidget(file_group)
        
        # Preview button
        btn_preview = QPushButton(self._tr('import_preview', 'Load and Preview'))
        btn_preview.clicked.connect(self.load_file)
        file_layout.addWidget(btn_preview)
        
        file_layout.addStretch()
        self.tab_widget.addTab(file_tab, self._tr('import_step1', '1. Select File'))
        
        # Step 2: Column Mapping
        mapping_tab = QWidget()
        mapping_layout = QVBoxLayout(mapping_tab)
        
        mapping_group = QGroupBox(self._tr('import_column_mapping', 'Column Mapping'))
        self.mapping_layout = QFormLayout(mapping_group)
        is_rtl = self.translator.current_language == 'ar'
        AppStyles.apply_form_layout_for_language(self.mapping_layout, is_rtl)
        mapping_layout.addWidget(mapping_group)
        
        mapping_info = QLabel(self._tr('import_mapping_info', 
            'Map the columns from your file to the database fields. Leave empty to skip a column.'))
        mapping_info.setWordWrap(True)
        mapping_layout.addWidget(mapping_info)
        
        self.tab_widget.addTab(mapping_tab, self._tr('import_step2', '2. Map Columns'))
        
        # Step 3: Preview and Validation
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        
        # Validation summary
        self.validation_summary = QLabel()
        self.validation_summary.setStyleSheet(AppStyles.get_component_style('validation_summary'))
        preview_layout.addWidget(self.validation_summary)
        self.preview_state_label = QLabel()
        self.preview_state_label.setObjectName('tableStateLabel')
        self.preview_state_label.setAlignment(Qt.AlignCenter)
        self.preview_state_label.setWordWrap(True)
        self.preview_state_label.setStyleSheet(AppStyles.get_component_style('table_state'))
        self.preview_state_label.setVisible(False)
        preview_layout.addWidget(self.preview_state_label)
        
        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setObjectName('importPreviewTable')
        configure_table(self.preview_table, multi_select=True)
        self.preview_table.setAccessibleName(self._tr(
            'import_preview_table', 'Import validation preview'
        ))
        preview_layout.addWidget(self.preview_table)
        from widgets.pagination_widget import PaginationWidget
        self.preview_pagination = PaginationWidget(self.translator, self)
        self.preview_pagination.page_changed.connect(self._render_preview_page)
        self.preview_pagination.page_size_changed.connect(self._render_preview_page)
        preview_layout.addWidget(self.preview_pagination)
        
        # Validation options
        options_layout = QHBoxLayout()
        
        self.skip_errors_check = QCheckBox(self._tr('import_skip_errors', 'Skip rows with errors'))
        self.skip_errors_check.setChecked(True)
        options_layout.addWidget(self.skip_errors_check)
        
        self.validate_btn = QPushButton(self._tr('import_validate', 'Validate Data'))
        self.validate_btn.clicked.connect(self.validate_data)
        options_layout.addWidget(self.validate_btn)
        
        options_layout.addStretch()
        preview_layout.addLayout(options_layout)
        
        self.tab_widget.addTab(preview_tab, self._tr('import_step3', '3. Preview & Validate'))
        
        # Step 4: Import
        import_tab = QWidget()
        import_layout = QVBoxLayout(import_tab)
        
        # Progress section
        progress_group = QGroupBox(self._tr('import_progress', 'Import Progress'))
        progress_group_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        progress_group_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel(self._tr('import_ready', 'Ready to import'))
        progress_group_layout.addWidget(self.progress_label)
        
        import_layout.addWidget(progress_group)
        
        # Import log
        log_group = QGroupBox(self._tr('import_log', 'Import Log'))
        log_layout = QVBoxLayout(log_group)
        
        self.import_log = QTextEdit()
        self.import_log.setReadOnly(True)
        log_layout.addWidget(self.import_log)
        
        import_layout.addWidget(log_group)
        
        self.tab_widget.addTab(import_tab, self._tr('import_step4', '4. Import'))
        
        layout.addWidget(self.tab_widget)
        
        # Bottom buttons - properly aligned in a single row
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        btn_layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid spacing
        
        self.btn_back = QPushButton(self._tr('btn_back', 'Back'))
        self.btn_back.clicked.connect(self.go_back)
        btn_layout.addWidget(self.btn_back, alignment=Qt.AlignVCenter)
        
        self.btn_next = QPushButton(self._tr('btn_next', 'Next'))
        self.btn_next.clicked.connect(self.go_next)
        btn_layout.addWidget(self.btn_next, alignment=Qt.AlignVCenter)
        
        btn_layout.addStretch()
        
        self.btn_import = QPushButton(self._tr('btn_import', 'Start Import'))
        self.btn_import.setStyleSheet(AppStyles.get_button_style('success'))
        self.btn_import.clicked.connect(self.start_import)
        self.btn_import.setEnabled(False)
        btn_layout.addWidget(self.btn_import, alignment=Qt.AlignVCenter)
        
        self.btn_cancel = QPushButton(self._tr('btn_cancel', 'Cancel'))
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel, alignment=Qt.AlignVCenter)
        
        layout.addLayout(btn_layout)
        
        # Connect tab change
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def setup_validation_rules(self):
        """Setup validation rules based on table"""
        self.validation_rules = []
        
        if self.table_name == 'sources':
            self.validation_rules = [
                ImportValidationRule('name', 'required', message='Source name is required'),
                ImportValidationRule('name', 'max_length', 500, 'Name too long'),
                ImportValidationRule('importance', 'type', 'float', 'Importance must be a number'),
            ]
            self.db_columns = ['name', 'type', 'link_sources', 'importance', 'country', 
                              'city', 'description', 'accounts', 'note', 'ownership', 'date_entry']
        
        elif self.table_name == 'contents':
            self.validation_rules = [
                ImportValidationRule('title', 'required', message='Content title is required'),
                ImportValidationRule('sources_id', 'type', 'int', 'Source ID must be a number'),
                ImportValidationRule('importance', 'type', 'float', 'Importance must be a number'),
            ]
            self.db_columns = ['title', 'content_data', 'attachments', 'note', 
                              'importance', 'date_content', 'sources_id']
        
        elif self.table_name == 'content_analysis':
            self.validation_rules = [
                ImportValidationRule('content_id', 'required', message='Content ID is required'),
                ImportValidationRule('content_id', 'type', 'int', 'Content ID must be a number'),
            ]
            self.db_columns = ['content_id', 'list_names_people', 'list_names_places',
                              'coordinates', 'classification', 'list_sides', 'date_analysis']
        else:
            self.db_columns = []
    
    def browse_file(self):
        """Browse for import file"""
        file_filter = "CSV Files (*.csv);;JSON Files (*.json);;All Files (*)"
        filename, _ = QFileDialog.getOpenFileName(
            self,
            self._tr('import_select_file', 'Select Import File'),
            '',
            file_filter
        )
        
        if filename:
            self.file_path_edit.setText(filename)
            # Auto-detect format
            if filename.lower().endswith('.json'):
                self.format_combo.setCurrentText('JSON')
            else:
                self.format_combo.setCurrentText('CSV')
    
    def load_file(self):
        """Load and preview the file"""
        filepath = self.file_path_edit.text()
        if not filepath:
            QMessageBox.warning(self, self._tr('msg_warning', 'Warning'),
                              self._tr('import_select_file_first', 'Please select a file first'))
            return
        
        try:
            file_format = self.format_combo.currentText()
            encoding = self.encoding_combo.currentText()
            
            if file_format == 'CSV':
                delimiter = self.delimiter_combo.currentText()
                self.import_data = self._load_csv(filepath, encoding, delimiter)
            else:
                self.import_data = self._load_json(filepath, encoding)
            
            if not self.import_data:
                QMessageBox.warning(self, self._tr('msg_warning', 'Warning'),
                                  self._tr('import_no_data', 'No data found in file'))
                return
            
            # Setup column mapping
            self._setup_column_mapping()
            
            # Move to next tab
            self.tab_widget.setCurrentIndex(1)
            
            QMessageBox.information(
                self,
                self._tr('msg_success', 'Success'),
                self._tr('import_loaded', f'Loaded {len(self.import_data)} rows')
            )
            
        except Exception as e:
            ErrorHandler.handle_error(
                AppError(
                    message=str(e),
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.IMPORT_EXPORT,
                    recovery_action="Check the file format and encoding"
                ),
                parent=self,
                translator=self.translator
            )
    
    def _load_csv(self, filepath: str, encoding: str, delimiter: str) -> List[Dict]:
        """Load CSV file"""
        data = []
        with open(filepath, 'r', encoding=encoding, newline='') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                data.append(dict(row))
        return data
    
    def _load_json(self, filepath: str, encoding: str) -> List[Dict]:
        """Load JSON file"""
        with open(filepath, 'r', encoding=encoding) as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
        return []
    
    def _setup_column_mapping(self):
        """Setup column mapping UI"""
        # Clear existing mappings
        while self.mapping_layout.count():
            item = self.mapping_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.import_data:
            return
        
        # Get columns from first row
        csv_columns = list(self.import_data[0].keys())
        
        # Create mapping combos
        self.mapping_combos = {}
        for csv_col in csv_columns:
            combo = QComboBox()
            combo.addItem('')  # Empty option to skip
            combo.addItems(self.db_columns)
            
            # Auto-map if column names match
            if csv_col.lower() in [c.lower() for c in self.db_columns]:
                matching = next((c for c in self.db_columns if c.lower() == csv_col.lower()), '')
                idx = combo.findText(matching)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            
            self.mapping_combos[csv_col] = combo
            self.mapping_layout.addRow(csv_col, combo)
    
    def validate_data(self):
        """Validate the import data"""
        # Check if mapping_combos exists (created in update_column_mapping)
        if not hasattr(self, 'mapping_combos') or not self.mapping_combos:
            return
        
        # Get column mapping
        self.column_mapping = {}
        for csv_col, combo in self.mapping_combos.items():
            db_col = combo.currentText()
            if db_col:
                self.column_mapping[csv_col] = db_col
        
        if not self.column_mapping:
            QMessageBox.warning(self, self._tr('msg_warning', 'Warning'),
                              self._tr('import_no_mapping', 'Please map at least one column'))
            return
        
        # Validate each row
        self.validation_results = []
        valid_count = 0
        warning_count = 0
        error_count = 0
        
        for i, row in enumerate(self.import_data):
            result = {
                'row_index': i,
                'status': ValidationStatus.VALID,
                'errors': [],
                'warnings': []
            }
            
            # Map the row
            mapped_row = {}
            for csv_col, db_col in self.column_mapping.items():
                mapped_row[db_col] = row.get(csv_col)
            
            # Apply validation rules
            for rule in self.validation_rules:
                if rule.field in mapped_row:
                    is_valid, message = rule.validate(
                        mapped_row[rule.field], 
                        [self._map_row(r) for r in self.import_data]
                    )
                    if not is_valid:
                        if rule.rule_type == 'required':
                            result['errors'].append(message)
                            result['status'] = ValidationStatus.ERROR
                        else:
                            result['warnings'].append(message)
                            if result['status'] == ValidationStatus.VALID:
                                result['status'] = ValidationStatus.WARNING
            
            if result['status'] == ValidationStatus.VALID:
                valid_count += 1
            elif result['status'] == ValidationStatus.WARNING:
                warning_count += 1
            else:
                error_count += 1
            
            self.validation_results.append(result)
        
        # Update summary
        self.validation_summary.setText(f"""
            <b>{self._tr('import_validation_summary', 'Validation Summary')}:</b><br>
            {self._tr('import_valid', 'Valid')}: {valid_count}<br>
            {self._tr('import_warnings', 'Warnings')}: {warning_count}<br>
            {self._tr('import_errors', 'Errors')}: {error_count}
        """)
        
        # Update preview table
        self._update_preview_table()
        
        # Enable import if we have valid rows
        self.btn_import.setEnabled(valid_count > 0 or 
                                   (self.skip_errors_check.isChecked() and valid_count + warning_count > 0))
    
    def _map_row(self, row: Dict) -> Dict:
        """Map a row using current column mapping"""
        mapped = {}
        for csv_col, db_col in self.column_mapping.items():
            mapped[db_col] = row.get(csv_col)
        return mapped
    
    def _update_preview_table(self):
        """Update validation preview metadata and render its active page."""
        if not self.import_data or not self.validation_results:
            self.preview_table.setRowCount(0)
            self.preview_pagination.current_page = 1
            self.preview_pagination.set_total_items(0)
            self.preview_state_label.setText(self._tr(
                'table_empty', 'Load and validate a file to preview records.'
            ))
            self.preview_state_label.setVisible(True)
            return
        columns = ['Status'] + list(self.column_mapping.keys())
        self.preview_state_label.setVisible(False)
        self.preview_table.setColumnCount(len(columns))
        self.preview_table.setHorizontalHeaderLabels(columns)
        self.preview_pagination.current_page = 1
        self.preview_pagination.set_total_items(len(self.import_data))
        self._render_preview_page()

    def _render_preview_page(self, _page=None):
        """Render validation rows for the current page; validation stays complete."""
        if not self.import_data or not self.validation_results:
            return
        start, end = self.preview_pagination.get_page_range()
        rows = list(zip(self.import_data, self.validation_results))[start:end]
        self.preview_table.setRowCount(len(rows))
        for row_idx, (row, result) in enumerate(rows):
            status = result['status']
            status_item = QTableWidgetItem()
            if status == ValidationStatus.VALID:
                status_item.setIcon(get_icon('validate', 18))
                status_item.setBackground(QColor('#d4edda'))
                status_item.setToolTip(self._tr('import_valid', 'Valid'))
                status_item.setData(Qt.AccessibleTextRole, self._tr('import_valid', 'Valid'))
            elif status == ValidationStatus.WARNING:
                status_item.setIcon(get_icon('warning', 18))
                status_item.setBackground(QColor('#fff3cd'))
                status_item.setToolTip('\n'.join(result['warnings']))
                status_item.setData(Qt.AccessibleTextRole, self._tr('import_warnings', 'Warnings'))
            else:
                status_item.setIcon(get_icon('error', 18))
                status_item.setBackground(QColor('#f8d7da'))
                status_item.setToolTip('\n'.join(result['errors']))
                status_item.setData(Qt.AccessibleTextRole, self._tr('import_errors', 'Errors'))
            self.preview_table.setItem(row_idx, 0, status_item)

            for col_idx, csv_col in enumerate(self.column_mapping.keys()):
                value = row.get(csv_col, '')
                item = set_item_with_tooltip(
                    self.preview_table, row_idx, col_idx + 1, str(value)[:100]
                )
                item.setToolTip(str(value))
                if status == ValidationStatus.ERROR:
                    item.setBackground(QColor('#f8d7da'))
                elif status == ValidationStatus.WARNING:
                    item.setBackground(QColor('#fff3cd'))
            self.preview_table.setRowHeight(row_idx, 38)
        self.preview_table.resizeColumnsToContents()

    def on_tab_changed(self, index: int):
        """Handle tab change"""
        self.btn_back.setEnabled(index > 0)
        self.btn_next.setEnabled(index < 3)
        
        if index == 2:  # Preview tab
            self.validate_data()
    
    def go_back(self):
        """Go to previous tab"""
        current = self.tab_widget.currentIndex()
        if current > 0:
            self.tab_widget.setCurrentIndex(current - 1)
    
    def go_next(self):
        """Go to next tab"""
        current = self.tab_widget.currentIndex()
        if current < 3:
            if current == 0 and not self.import_data:
                QMessageBox.warning(self, self._tr('msg_warning', 'Warning'),
                                  self._tr('import_load_first', 'Please load a file first'))
                return
            self.tab_widget.setCurrentIndex(current + 1)
    
    def start_import(self):
        """Start the import process"""
        # Filter rows based on validation
        rows_to_import = []
        for i, (row, result) in enumerate(zip(self.import_data, self.validation_results)):
            if result['status'] == ValidationStatus.VALID:
                rows_to_import.append(row)
            elif result['status'] == ValidationStatus.WARNING and self.skip_errors_check.isChecked():
                rows_to_import.append(row)
        
        if not rows_to_import:
            QMessageBox.warning(self, self._tr('msg_warning', 'Warning'),
                              self._tr('import_no_valid_rows', 'No valid rows to import'))
            return
        
        # Confirm import
        reply = QMessageBox.question(
            self,
            self._tr('msg_confirm', 'Confirm'),
            self._tr('import_confirm', f'Import {len(rows_to_import)} rows?'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Switch to import tab
        self.tab_widget.setCurrentIndex(3)
        
        # Setup progress
        self.progress_bar.setMaximum(len(rows_to_import))
        self.progress_bar.setValue(0)
        self.import_log.clear()
        
        # Disable buttons during import
        self.btn_import.setEnabled(False)
        self.btn_back.setEnabled(False)
        self.btn_next.setEnabled(False)
        
        # Create and start worker
        self.import_worker = ImportWorker(
            self.table_name,
            rows_to_import,
            self.column_mapping,
            self
        )
        
        self.import_worker.progress_updated.connect(self._on_progress_updated)
        self.import_worker.row_imported.connect(self._on_row_imported)
        self.import_worker.import_completed.connect(self._on_import_completed)
        
        self.import_worker.start()
    
    def _on_progress_updated(self, current: int, total: int):
        """Handle progress update"""
        self.progress_bar.setValue(current)
        self.progress_label.setText(
            self._tr('msg_importing_row', 'Importing row {current} of {total}...',
                     current=current, total=total)
        )
    
    def _on_row_imported(self, row_index: int, success: bool, message: str):
        """Handle row import result"""
        if success:
                self.import_log.append(
                    f"{self._tr('import_valid', 'Valid')} - Row {row_index + 1}: "
                    f"{self._tr('msg_success', 'Success')}"
                )
        else:
                self.import_log.append(
                    f"{self._tr('import_errors', 'Error')} - Row {row_index + 1}: {message}"
                )
    
    def _on_import_completed(self, success_count: int, error_count: int, errors: List):
        """Handle import completion"""
        self.progress_label.setText(
            self._tr('msg_import_completed', 'Import completed: {success} successful, {errors} errors').format(success=success_count, errors=error_count)
        )
        
        self.import_log.append("\n" + "="*50)
        self.import_log.append(f"{self._tr('msg_import_summary', 'Import Summary')}:")
        self.import_log.append(f"  {self._tr('msg_success', 'Successful')}: {success_count}")
        self.import_log.append(f"  {self._tr('msg_error', 'Errors')}: {error_count}")
        
        if errors:
            self.import_log.append(f"\n{self._tr('msg_error', 'Errors')}:")
            for error in errors[:10]:  # Show first 10 errors
                self.import_log.append(f"  Row {error['row'] + 1}: {error['error']}")
            if len(errors) > 10:
                self.import_log.append(f"  {self._tr('msg_more_errors', '... and {count} more errors').format(count=len(errors) - 10)}")
        
        # Re-enable buttons
        self.btn_cancel.setText(self._tr('btn_close', 'Close'))
        
        # Emit completion signal
        self.import_completed.emit(success_count, error_count)
        
        if success_count > 0:
            QMessageBox.information(
                self,
                self._tr('msg_success', 'Success'),
                self._tr('msg_import_success', 'Successfully imported {count} records.').format(count=success_count)
            )
    
    def closeEvent(self, event):
        """Handle dialog close"""
        if self.import_worker and self.import_worker.isRunning():
            reply = QMessageBox.question(
                self,
                self._tr('msg_confirm', 'Confirm'),
                self._tr('import_cancel_confirm', 'Import is in progress. Cancel?'),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.import_worker.cancel()
                self.import_worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
