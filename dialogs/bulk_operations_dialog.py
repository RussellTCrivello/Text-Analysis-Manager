"""
Bulk Operations Dialog
Provides UI for bulk delete, bulk edit, and bulk import operations
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QGroupBox, QRadioButton, QButtonGroup,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QFileDialog, QProgressBar, QTextEdit, QTabWidget, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import List, Dict, Optional
from translations.translations import TranslationManager
from styles.styles import AppStyles
from utils.logger import get_logger
from utils.table_ui import configure_table, set_item_with_tooltip
from icons.icon_manager import setup_icon_button

logger = get_logger(__name__)


class BulkOperationsDialog(QDialog):
    """Dialog for bulk operations"""
    
    operation_completed = pyqtSignal(str, int)  # operation_type, count
    
    def __init__(self, parent, translator: TranslationManager,
                 table_name: str, data: List[Dict], columns: List[tuple],
                 preselected_ids: Optional[List[int]] = None):
        super().__init__(parent)
        self.translator = translator
        self.table_name = table_name
        self.data = data
        self.columns = columns
        # When opened from a table selection bar, carry the user's selection
        # into the dialog while preserving the ability to change it.
        self.preselected_ids = {record_id for record_id in (preselected_ids or [])}
        self.selected_ids = []
        
        self.setWindowTitle(translator.tr('bulk_operations') if hasattr(translator, 'tr') else 'Bulk Operations')
        # Apply fixed size to prevent resizing on button clicks or content changes
        from styles.styles import AppStyles
        AppStyles.apply_fixed_size(self, 800, 600)
        self._apply_rtl_direction()
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
        m = AppStyles.get_spacing(2)
        layout.setContentsMargins(m, m, m, m)
        layout.setSpacing(AppStyles.get_spacing(2))
        
        # Operation type selection
        operation_group = QGroupBox(self.translator.tr('bulk_operation_type') if hasattr(self.translator, 'tr') else 'Operation Type')
        operation_layout = QVBoxLayout(operation_group)
        
        self.operation_group = QButtonGroup(self)
        self.radio_delete = QRadioButton(self.translator.tr('bulk_delete') if hasattr(self.translator, 'tr') else 'Bulk Delete')
        self.radio_edit = QRadioButton(self.translator.tr('bulk_edit') if hasattr(self.translator, 'tr') else 'Bulk Edit')
        self.radio_import = QRadioButton(self.translator.tr('bulk_import') if hasattr(self.translator, 'tr') else 'Bulk Import')
        
        self.operation_group.addButton(self.radio_delete, 0)
        self.operation_group.addButton(self.radio_edit, 1)
        self.operation_group.addButton(self.radio_import, 2)
        
        self.radio_delete.setChecked(True)
        self.radio_delete.toggled.connect(self.on_operation_changed)
        self.radio_edit.toggled.connect(self.on_operation_changed)
        self.radio_import.toggled.connect(self.on_operation_changed)
        
        operation_layout.addWidget(self.radio_delete)
        operation_layout.addWidget(self.radio_edit)
        operation_layout.addWidget(self.radio_import)
        
        layout.addWidget(operation_group)
        
        # Tab widget for different operation views
        self.tabs = QTabWidget()
        
        # Selection tab
        self.selection_tab = self.create_selection_tab()
        self.tabs.addTab(self.selection_tab, self.translator.tr('bulk_select_records') if hasattr(self.translator, 'tr') else 'Select Records')
        
        # Edit tab (for bulk edit)
        self.edit_tab = self.create_edit_tab()
        self.tabs.addTab(self.edit_tab, self.translator.tr('bulk_edit_fields') if hasattr(self.translator, 'tr') else 'Edit Fields')
        
        # Import tab (for bulk import)
        self.import_tab = self.create_import_tab()
        self.tabs.addTab(self.import_tab, self.translator.tr('bulk_import_file') if hasattr(self.translator, 'tr') else 'Import File')
        
        layout.addWidget(self.tabs)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Buttons - properly aligned in a single row
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        btn_layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid (rounding 10px to 16px)
        btn_layout.addStretch()
        
        self.btn_execute = QPushButton(self.translator.tr('btn_execute') if hasattr(self.translator, 'tr') else 'Execute')
        self.btn_execute.setStyleSheet(AppStyles.get_button_style('success'))
        self.btn_execute.clicked.connect(self.execute_operation)
        btn_layout.addWidget(self.btn_execute, alignment=Qt.AlignVCenter)
        
        self.btn_cancel = QPushButton(self.translator.tr('btn_cancel') if hasattr(self.translator, 'tr') else 'Cancel')
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel, alignment=Qt.AlignVCenter)
        
        layout.addLayout(btn_layout)
        
        self.on_operation_changed()
    
    def create_selection_tab(self) -> QWidget:
        """Create selection tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Selection controls
        controls = QHBoxLayout()
        
        self.btn_select_all = QPushButton(self.translator.tr('btn_select_all') if hasattr(self.translator, 'tr') else 'Select All')
        self.btn_select_all.clicked.connect(self.select_all)
        controls.addWidget(self.btn_select_all)
        
        self.btn_deselect_all = QPushButton(self.translator.tr('btn_deselect_all') if hasattr(self.translator, 'tr') else 'Deselect All')
        self.btn_deselect_all.clicked.connect(self.deselect_all)
        controls.addWidget(self.btn_deselect_all)
        
        controls.addStretch()
        
        self.selection_count_label = QLabel(
            self.translator.tr('bulk_selected_count', count=0)
        )
        controls.addWidget(self.selection_count_label)
        
        layout.addLayout(controls)
        
        # Selection table
        self.selection_table = QTableWidget()
        self.selection_table.setObjectName('bulkSelectionTable')
        self.selection_table.setColumnCount(len(self.columns) + 1)  # +1 for checkbox
        headers = [self.translator.tr('btn_select_all', default='Select')] + [col[1] for col in self.columns]
        self.selection_table.setHorizontalHeaderLabels(headers)
        configure_table(self.selection_table, multi_select=True)
        self.selection_table.horizontalHeader().setStretchLastSection(True)
        self.selection_table.setAccessibleName(self.translator.tr(
            'bulk_select_records', default='Select records for bulk operation'
        ))
        self.selection_table.setColumnWidth(0, 64)
        
        # Populate table
        self.selection_table.setRowCount(len(self.data))
        for row_idx, row_data in enumerate(self.data):
            # Checkbox
            checkbox = QCheckBox()
            record_label = row_data.get('name') or row_data.get('title') or row_data.get('id', row_idx + 1)
            checkbox.setAccessibleName(
                f"{self.translator.tr('btn_select_all', default='Select')} {record_label}"
            )
            checkbox.setToolTip(checkbox.accessibleName())
            checkbox.stateChanged.connect(self.update_selection_count)
            checkbox.setChecked(row_data.get('id') in self.preselected_ids)
            self.selection_table.setCellWidget(row_idx, 0, checkbox)

            # Data columns
            for col_idx, (col_key, _, _) in enumerate(self.columns):
                value = row_data.get(col_key, '')
                item = set_item_with_tooltip(
                    self.selection_table, row_idx, col_idx + 1, str(value)[:100]
                )
                item.setToolTip(str(value))
                item.setData(Qt.UserRole, row_data.get('id'))

        self.update_selection_count()
        self.selection_table.resizeColumnsToContents()
        layout.addWidget(self.selection_table)
        self.selection_state_label = QLabel()
        self.selection_state_label.setObjectName('tableStateLabel')
        self.selection_state_label.setAlignment(Qt.AlignCenter)
        self.selection_state_label.setWordWrap(True)
        self.selection_state_label.setStyleSheet(AppStyles.get_component_style('table_state'))
        self.selection_state_label.setText(self.translator.tr(
            'table_empty', default='No records are available for this operation.'
        ))
        self.selection_state_label.setVisible(not bool(self.data))
        layout.addWidget(self.selection_state_label)
        
        return widget
    
    def create_edit_tab(self) -> QWidget:
        """Create bulk edit tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info_label = QLabel(self.translator.tr('bulk_edit_info') if hasattr(self.translator, 'tr') else 
                          'Select fields to update. Leave empty to keep current value.')
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Edit fields (simplified - can be expanded)
        from widgets.widgets import AutoCompleteLineEdit
        
        self.edit_fields = {}
        for col_key, col_name, _ in self.columns:
            if col_key not in ['id', 'date_creation', 'date_modified']:
                field_layout = QHBoxLayout()
                label = QLabel(f"{col_name}:")
                label.setMinimumWidth(150)
                field_layout.addWidget(label)
                
                edit = AutoCompleteLineEdit()
                edit.setPlaceholderText(
                    self.translator.tr('bulk_leave_empty') if hasattr(self.translator, 'tr')
                    else 'Leave empty to keep current value'
                )
                self.edit_fields[col_key] = edit
                field_layout.addWidget(edit)
                
                layout.addLayout(field_layout)
        
        layout.addStretch()
        
        return widget
    
    def create_import_tab(self) -> QWidget:
        """Create bulk import tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info_label = QLabel(self.translator.tr('bulk_import_info') if hasattr(self.translator, 'tr') else 
                          'Select a CSV file to import. The file should have columns matching the table structure.')
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel(self.translator.tr('bulk_import_file') if hasattr(self.translator, 'tr') else 'File:'))
        
        self.import_file_path = QLabel(self.translator.tr('msg_no_file_selected') if hasattr(self.translator, 'tr') else 'No file selected')
        file_layout.addWidget(self.import_file_path)
        
        self.btn_browse = QPushButton(self.translator.tr('btn_browse') if hasattr(self.translator, 'tr') else 'Browse...')
        self.btn_browse.clicked.connect(self.browse_import_file)
        file_layout.addWidget(self.btn_browse)
        
        layout.addLayout(file_layout)
        
        # Preview area
        preview_label = QLabel(self.translator.tr('bulk_import_preview') if hasattr(self.translator, 'tr') else 'Preview:')
        layout.addWidget(preview_label)
        
        self.import_preview = QTextEdit()
        self.import_preview.setReadOnly(True)
        self.import_preview.setMaximumHeight(200)
        layout.addWidget(self.import_preview)
        
        layout.addStretch()
        
        return widget
    
    def on_operation_changed(self):
        """Handle operation type change"""
        if self.radio_delete.isChecked():
            self.tabs.setCurrentIndex(0)
            self.tabs.setTabEnabled(1, False)
            self.tabs.setTabEnabled(2, False)
        elif self.radio_edit.isChecked():
            self.tabs.setCurrentIndex(0)
            self.tabs.setTabEnabled(1, True)
            self.tabs.setTabEnabled(2, False)
        elif self.radio_import.isChecked():
            self.tabs.setCurrentIndex(2)
            self.tabs.setTabEnabled(1, False)
            self.tabs.setTabEnabled(2, True)
        if hasattr(self, 'btn_execute'):
            self.btn_execute.setEnabled(
                self.radio_import.isChecked() or bool(self.selected_ids)
            )
    
    def select_all(self):
        """Select all rows"""
        for row in range(self.selection_table.rowCount()):
            checkbox = self.selection_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
        self.update_selection_count()
    
    def deselect_all(self):
        """Deselect all rows"""
        for row in range(self.selection_table.rowCount()):
            checkbox = self.selection_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
        self.update_selection_count()
    
    def update_selection_count(self):
        """Update selection count label"""
        count = 0
        self.selected_ids = []
        
        for row in range(self.selection_table.rowCount()):
            checkbox = self.selection_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                item = self.selection_table.item(row, 1)
                if item:
                    record_id = item.data(Qt.UserRole)
                    if record_id:
                        self.selected_ids.append(record_id)
                        count += 1
        
        self.selection_count_label.setText(
            self.translator.tr('bulk_selected_count', count=count)
        )
        if hasattr(self, 'btn_execute'):
            self.btn_execute.setEnabled(
                self.radio_import.isChecked() or bool(self.selected_ids)
            )
    
    def browse_import_file(self):
        """Browse for import file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            self.translator.tr('bulk_import_file') if hasattr(self.translator, 'tr') else 'Select Import File',
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if filename:
            self.import_file_path.setText(filename)
            # Preview first few lines
            try:
                import csv
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    preview_lines = []
                    for i, row in enumerate(reader):
                        if i < 5:
                            preview_lines.append(str(dict(row)))
                        else:
                            break
                    self.import_preview.setPlainText('\n'.join(preview_lines))
            except Exception as e:
                self.import_preview.setPlainText(f"Error reading file: {str(e)}")
    
    def execute_operation(self):
        """Execute the selected bulk operation"""
        if self.radio_delete.isChecked():
            self.execute_bulk_delete()
        elif self.radio_edit.isChecked():
            self.execute_bulk_edit()
        elif self.radio_import.isChecked():
            self.execute_bulk_import()
    
    def execute_bulk_delete(self):
        """Execute bulk delete"""
        if not self.selected_ids:
            QMessageBox.warning(self, self.translator.tr('msg_warning') if hasattr(self.translator, 'tr') else 'Warning',
                             self.translator.tr('bulk_no_selection') if hasattr(self.translator, 'tr') else 'No records selected')
            return
        
        reply = QMessageBox.question(
            self,
            self.translator.tr('msg_confirm') if hasattr(self.translator, 'tr') else 'Confirm',
            f"Delete {len(self.selected_ids)} record(s)?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.progress.setVisible(True)
            self.progress.setMaximum(len(self.selected_ids))
            self.progress.setValue(0)
            
            deleted_count = 0
            from db.db_manager import DatabaseManager
            
            for record_id in self.selected_ids:
                try:
                    if self.table_name == 'sources':
                        DatabaseManager.delete_source(record_id)
                    elif self.table_name == 'contents':
                        DatabaseManager.delete_content(record_id)
                    elif self.table_name == 'content_analysis':
                        DatabaseManager.delete_content_analysis(record_id)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting record {record_id}: {e}")
                
                self.progress.setValue(deleted_count)
            
            self.progress.setVisible(False)
            QMessageBox.information(self, self.translator.tr('msg_success') if hasattr(self.translator, 'tr') else 'Success',
                                  f"Deleted {deleted_count} record(s)")
            self.operation_completed.emit('delete', deleted_count)
            self.accept()
    
    def execute_bulk_edit(self):
        """Execute bulk edit"""
        if not self.selected_ids:
            QMessageBox.warning(self, self.translator.tr('msg_warning') if hasattr(self.translator, 'tr') else 'Warning',
                             self.translator.tr('bulk_no_selection') if hasattr(self.translator, 'tr') else 'No records selected')
            return
        
        # Collect field updates
        updates = {}
        for col_key, edit in self.edit_fields.items():
            value = edit.text().strip()
            if value:
                updates[col_key] = value
        
        if not updates:
            QMessageBox.warning(
                self,
                self.translator.tr('msg_warning') if hasattr(self.translator, 'tr') else 'Warning',
                self.translator.tr('bulk_no_fields_update')
            )
            return
        
        self.progress.setVisible(True)
        self.progress.setMaximum(len(self.selected_ids))
        self.progress.setValue(0)
        
        updated_count = 0
        from db.db_manager import DatabaseManager
        
        for record_id in self.selected_ids:
            try:
                if self.table_name == 'sources':
                    source = DatabaseManager.get_source_by_id(record_id)
                    if source:
                        source.update(updates)
                        DatabaseManager.update_source(record_id, source)
                elif self.table_name == 'contents':
                    content = DatabaseManager.get_content_by_id(record_id)
                    if content:
                        content.update(updates)
                        DatabaseManager.update_content(record_id, content)
                elif self.table_name == 'content_analysis':
                    analysis = DatabaseManager.get_analysis_by_id(record_id)
                    if analysis:
                        analysis.update(updates)
                        DatabaseManager.update_content_analysis(record_id, analysis)
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating record {record_id}: {e}")
            
            self.progress.setValue(updated_count)
        
        self.progress.setVisible(False)
        QMessageBox.information(self, self.translator.tr('msg_success') if hasattr(self.translator, 'tr') else 'Success',
                              f"Updated {updated_count} record(s)")
        self.operation_completed.emit('edit', updated_count)
        self.accept()
    
    def execute_bulk_import(self):
        """Execute bulk import"""
        filepath = self.import_file_path.text()
        if not filepath or filepath == "No file selected":
            QMessageBox.warning(
                self,
                self.translator.tr('msg_warning') if hasattr(self.translator, 'tr') else 'Warning',
                self.translator.tr('bulk_select_file')
            )
            return
        
        # Import logic (similar to existing import functions)
        import csv
        imported_count = 0
        errors = []
        
        self.progress.setVisible(True)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.progress.setMaximum(len(rows))
                self.progress.setValue(0)
                
                from db.db_manager import DatabaseManager
                
                for row_num, row in enumerate(rows, 1):
                    try:
                        # Map CSV to database fields (simplified)
                        data = {}
                        for col_key, _, _ in self.columns:
                            if col_key in row:
                                data[col_key] = row[col_key]
                        
                        if self.table_name == 'sources':
                            DatabaseManager.add_source(data)
                        elif self.table_name == 'contents':
                            DatabaseManager.add_content(data)
                        elif self.table_name == 'content_analysis':
                            DatabaseManager.add_content_analysis(data)
                        
                        imported_count += 1
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                    
                    self.progress.setValue(row_num)
            
            self.progress.setVisible(False)
            
            msg = f"Imported {imported_count} record(s)"
            if errors:
                msg += f"\n\nErrors: {len(errors)}\n" + "\n".join(errors[:10])
            
            QMessageBox.information(self, self.translator.tr('msg_success') if hasattr(self.translator, 'tr') else 'Success', msg)
            self.operation_completed.emit('import', imported_count)
            self.accept()
            
        except Exception as e:
            self.progress.setVisible(False)
            QMessageBox.critical(self, self.translator.tr('msg_error') if hasattr(self.translator, 'tr') else 'Error',
                               f"Import failed: {str(e)}")
