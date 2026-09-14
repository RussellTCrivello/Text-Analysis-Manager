"""
Advanced Search Dialog
Provides visual query builder for advanced search operations
With saved searches and search history support
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QGroupBox, QComboBox, QLineEdit, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QFormLayout, QTextEdit, QScrollArea, QWidget, QInputDialog,
    QListWidget, QListWidgetItem, QSplitter, QTabWidget, QMenu,
    QAction, QToolButton
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QIcon
from typing import List, Dict, Optional
from translations.translations import TranslationManager
from styles.styles import AppStyles
from utils.logger import get_logger
from utils.search_history import get_search_history_manager
from db.db_manager import DatabaseManager

logger = get_logger(__name__)


class AdvancedSearchDialog(QDialog):
    """Advanced search dialog with query builder, saved searches, and history"""
    
    search_executed = pyqtSignal(list)  # Signal emitted when search results are ready
    
    def __init__(self, parent, translator: TranslationManager, table_name: str):
        super().__init__(parent)
        self.translator = translator
        self.table_name = table_name
        self.search_conditions = []
        self.results = []
        self.search_history_manager = get_search_history_manager()
        
        self.setWindowTitle(translator.tr('advanced_search') if hasattr(translator, 'tr') else 'Advanced Search')
        # Apply fixed size to prevent resizing on button clicks or content changes
        from styles.styles import AppStyles
        AppStyles.apply_fixed_size(self, 1000, 800)
        self._apply_rtl_direction()
        self.setup_ui()
        self._apply_rtl_direction()
        self.load_saved_searches()
        self.load_history()
    
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
        
        # Main splitter for search builder and saved searches
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Search Builder
        search_panel = QWidget()
        search_layout = QVBoxLayout(search_panel)
        
        # Query builder section
        builder_group = QGroupBox(self.translator.tr('search_query_builder') if hasattr(self.translator, 'tr') else 'Query Builder')
        builder_layout = QVBoxLayout(builder_group)
        
        # Condition list
        self.conditions_widget = QWidget()
        self.conditions_layout = QVBoxLayout(self.conditions_widget)
        self.conditions_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.conditions_widget)
        scroll.setMinimumHeight(200)
        builder_layout.addWidget(scroll)
        
        # Add condition button
        btn_add = QPushButton(self.translator.tr('search_add_condition') if hasattr(self.translator, 'tr') else 'Add Condition')
        btn_add.clicked.connect(self.add_condition)
        builder_layout.addWidget(btn_add)
        
        search_layout.addWidget(builder_group)
        
        # Logic operator
        logic_layout = QHBoxLayout()
        logic_layout.addWidget(QLabel(self.translator.tr('search_logic') if hasattr(self.translator, 'tr') else 'Logic:'))
        
        self.logic_combo = QComboBox()
        self.logic_combo.addItems(['AND', 'OR'])
        logic_layout.addWidget(self.logic_combo)
        logic_layout.addStretch()
        
        search_layout.addLayout(logic_layout)
        
        # Buttons - properly aligned in a single row
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        from styles.styles import AppStyles
        btn_layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid spacing
        
        self.btn_search = QPushButton(self.translator.tr('btn_search') if hasattr(self.translator, 'tr') else 'Search')
        self.btn_search.setStyleSheet(AppStyles.get_button_style('primary'))
        self.btn_search.clicked.connect(self.execute_search)
        btn_layout.addWidget(self.btn_search, alignment=Qt.AlignVCenter)
        
        self.btn_clear = QPushButton(self.translator.tr('btn_clear') if hasattr(self.translator, 'tr') else 'Clear')
        self.btn_clear.clicked.connect(self.clear_conditions)
        btn_layout.addWidget(self.btn_clear, alignment=Qt.AlignVCenter)
        
        # Save search button with dropdown
        self.btn_save = QToolButton()
        self.btn_save.setText(self.translator.tr('search_save') if hasattr(self.translator, 'tr') else 'Save Search')
        self.btn_save.setPopupMode(QToolButton.MenuButtonPopup)
        
        save_menu = QMenu(self)
        save_new_action = QAction(self.translator.tr('search_save_new') if hasattr(self.translator, 'tr') else 'Save as New', self)
        save_new_action.triggered.connect(self.save_search)
        save_menu.addAction(save_new_action)
        
        save_update_action = QAction(self.translator.tr('search_update') if hasattr(self.translator, 'tr') else 'Update Existing', self)
        save_update_action.triggered.connect(self.update_saved_search)
        save_menu.addAction(save_update_action)
        
        self.btn_save.setMenu(save_menu)
        self.btn_save.clicked.connect(self.save_search)
        btn_layout.addWidget(self.btn_save, alignment=Qt.AlignVCenter)
        
        btn_layout.addStretch()
        
        self.btn_close = QPushButton(self.translator.tr('btn_close') if hasattr(self.translator, 'tr') else 'Close')
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close, alignment=Qt.AlignVCenter)
        
        search_layout.addLayout(btn_layout)
        
        # Results section
        results_group = QGroupBox(self.translator.tr('search_results') if hasattr(self.translator, 'tr') else 'Results')
        results_layout = QVBoxLayout(results_group)
        
        self.results_count_label = QLabel("0 results")
        results_layout.addWidget(self.results_count_label)
        
        self.results_table = QTableWidget()
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        results_layout.addWidget(self.results_table)
        
        search_layout.addWidget(results_group)
        
        main_splitter.addWidget(search_panel)
        
        # Right panel - Saved Searches and History
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Tab widget for saved searches and history
        self.side_tabs = QTabWidget()
        
        # Saved Searches Tab
        saved_tab = QWidget()
        saved_layout = QVBoxLayout(saved_tab)
        
        self.saved_searches_list = QListWidget()
        self.saved_searches_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.saved_searches_list.customContextMenuRequested.connect(self.show_saved_search_context_menu)
        self.saved_searches_list.itemDoubleClicked.connect(self.load_saved_search)
        saved_layout.addWidget(self.saved_searches_list)
        
        saved_btn_layout = QHBoxLayout()
        saved_btn_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        saved_btn_layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid spacing
        btn_load_saved = QPushButton(self.translator.tr('search_load') if hasattr(self.translator, 'tr') else 'Load')
        btn_load_saved.clicked.connect(self.load_selected_saved_search)
        saved_btn_layout.addWidget(btn_load_saved, alignment=Qt.AlignVCenter)
        
        btn_delete_saved = QPushButton(self.translator.tr('btn_delete') if hasattr(self.translator, 'tr') else 'Delete')
        btn_delete_saved.clicked.connect(self.delete_selected_saved_search)
        saved_btn_layout.addWidget(btn_delete_saved, alignment=Qt.AlignVCenter)
        saved_layout.addLayout(saved_btn_layout)
        
        self.side_tabs.addTab(saved_tab, self.translator.tr('search_saved') if hasattr(self.translator, 'tr') else 'Saved Searches')
        
        # History Tab
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        
        self.history_list = QListWidget()
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self.show_history_context_menu)
        self.history_list.itemDoubleClicked.connect(self.load_history_item)
        history_layout.addWidget(self.history_list)
        
        history_btn_layout = QHBoxLayout()
        history_btn_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        history_btn_layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid spacing
        btn_load_history = QPushButton(self.translator.tr('search_load') if hasattr(self.translator, 'tr') else 'Load')
        btn_load_history.clicked.connect(self.load_selected_history_item)
        history_btn_layout.addWidget(btn_load_history, alignment=Qt.AlignVCenter)
        
        btn_clear_history = QPushButton(self.translator.tr('btn_clear') if hasattr(self.translator, 'tr') else 'Clear History')
        btn_clear_history.clicked.connect(self.clear_search_history)
        history_btn_layout.addWidget(btn_clear_history, alignment=Qt.AlignVCenter)
        history_layout.addLayout(history_btn_layout)
        
        self.side_tabs.addTab(history_tab, self.translator.tr('search_history') if hasattr(self.translator, 'tr') else 'History')
        
        # Frequently Used Tab
        frequent_tab = QWidget()
        frequent_layout = QVBoxLayout(frequent_tab)
        
        self.frequent_list = QListWidget()
        self.frequent_list.itemDoubleClicked.connect(self.load_frequent_search)
        frequent_layout.addWidget(self.frequent_list)
        
        self.side_tabs.addTab(frequent_tab, self.translator.tr('search_frequent') if hasattr(self.translator, 'tr') else 'Frequently Used')
        
        right_layout.addWidget(self.side_tabs)
        
        main_splitter.addWidget(right_panel)
        
        # Set splitter sizes (70% left, 30% right)
        main_splitter.setSizes([700, 300])
        
        layout.addWidget(main_splitter)
        
        # Add initial condition
        self.add_condition()
    
    def add_condition(self):
        """Add a new search condition"""
        condition_widget = QWidget()
        condition_layout = QHBoxLayout(condition_widget)
        condition_layout.setContentsMargins(AppStyles.get_spacing(1), AppStyles.get_spacing(1), 
                                           AppStyles.get_spacing(1), AppStyles.get_spacing(1))  # 8px - 8px grid
        
        # Field selector
        field_combo = QComboBox()
        field_combo.setObjectName("field_combo")
        # Get available fields based on table
        if self.table_name == 'sources':
            fields = ['name', 'type', 'country', 'city', 'description', 'note', 'ownership']
        elif self.table_name == 'contents':
            fields = ['title', 'content_data', 'note']
        elif self.table_name == 'content_analysis':
            fields = ['classification', 'list_names_people', 'list_names_places', 'list_sides']
        else:
            fields = []
        
        field_combo.addItems(fields)
        condition_layout.addWidget(field_combo)
        
        # Operator selector
        operator_combo = QComboBox()
        operator_combo.setObjectName("operator_combo")
        operator_combo.addItems(['=', '!=', 'LIKE', 'NOT LIKE', '>', '<', '>=', '<=', 'IS NULL', 'IS NOT NULL'])
        condition_layout.addWidget(operator_combo)
        
        # Value input
        value_edit = QLineEdit()
        value_edit.setObjectName("value_edit")
        value_edit.setPlaceholderText("Value")
        condition_layout.addWidget(value_edit)
        
        # Date picker (if field is date)
        date_edit = QDateEdit()
        date_edit.setObjectName("date_edit")
        date_edit.setCalendarPopup(True)
        date_edit.setVisible(False)
        condition_layout.addWidget(date_edit)
        
        # Remove button
        btn_remove = QPushButton("×")
        btn_remove.setMaximumWidth(30)
        btn_remove.clicked.connect(lambda: self.remove_condition(condition_widget))
        condition_layout.addWidget(btn_remove)
        
        self.conditions_layout.addWidget(condition_widget)
        
        # Show/hide date picker based on field
        def on_field_changed(field):
            is_date = 'date' in field.lower()
            value_edit.setVisible(not is_date)
            date_edit.setVisible(is_date)
        
        # Disable value input for NULL operators
        def on_operator_changed(operator):
            is_null = 'NULL' in operator
            value_edit.setEnabled(not is_null)
            date_edit.setEnabled(not is_null)
            if is_null:
                value_edit.clear()
        
        field_combo.currentTextChanged.connect(on_field_changed)
        operator_combo.currentTextChanged.connect(on_operator_changed)
    
    def remove_condition(self, widget: QWidget):
        """Remove a condition"""
        self.conditions_layout.removeWidget(widget)
        widget.deleteLater()
    
    def clear_conditions(self):
        """Clear all conditions"""
        while self.conditions_layout.count():
            item = self.conditions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.add_condition()
    
    def get_current_conditions(self) -> Dict:
        """Get current conditions from UI"""
        conditions = {}
        logic = self.logic_combo.currentText()
        
        for i in range(self.conditions_layout.count()):
            item = self.conditions_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                field_combo = widget.findChild(QComboBox, "field_combo")
                operator_combo = widget.findChild(QComboBox, "operator_combo")
                value_edit = widget.findChild(QLineEdit, "value_edit")
                date_edit = widget.findChild(QDateEdit, "date_edit")
                
                if field_combo and operator_combo:
                    field = field_combo.currentText()
                    operator = operator_combo.currentText()
                    
                    # Handle NULL operators
                    if 'NULL' in operator:
                        conditions[field] = {
                            'operator': operator,
                            'value': None
                        }
                    elif date_edit and date_edit.isVisible():
                        value = date_edit.date().toString('yyyy-MM-dd')
                        conditions[field] = {
                            'operator': operator,
                            'value': value
                        }
                    elif value_edit and value_edit.text():
                        value = value_edit.text()
                        # Add wildcards for LIKE operator if not present
                        if operator in ['LIKE', 'NOT LIKE'] and '%' not in value:
                            value = f'%{value}%'
                        conditions[field] = {
                            'operator': operator,
                            'value': value
                        }
        
        conditions['logic'] = logic
        return conditions
    
    def set_conditions_from_dict(self, conditions: Dict):
        """Set UI conditions from a dictionary"""
        self.clear_conditions()
        
        logic = conditions.get('logic', 'AND')
        idx = self.logic_combo.findText(logic)
        if idx >= 0:
            self.logic_combo.setCurrentIndex(idx)
        
        first = True
        for field, cond in conditions.items():
            if field == 'logic':
                continue
            
            if not first:
                self.add_condition()
            first = False
            
            # Get the last added condition widget
            last_idx = self.conditions_layout.count() - 1
            if last_idx >= 0:
                item = self.conditions_layout.itemAt(last_idx)
                if item and item.widget():
                    widget = item.widget()
                    field_combo = widget.findChild(QComboBox, "field_combo")
                    operator_combo = widget.findChild(QComboBox, "operator_combo")
                    value_edit = widget.findChild(QLineEdit, "value_edit")
                    date_edit = widget.findChild(QDateEdit, "date_edit")
                    
                    if field_combo:
                        idx = field_combo.findText(field)
                        if idx >= 0:
                            field_combo.setCurrentIndex(idx)
                    
                    if operator_combo and isinstance(cond, dict):
                        operator = cond.get('operator', '=')
                        idx = operator_combo.findText(operator)
                        if idx >= 0:
                            operator_combo.setCurrentIndex(idx)
                        
                        value = cond.get('value')
                        if value is not None:
                            if 'date' in field.lower() and date_edit:
                                date_edit.setDate(QDate.fromString(str(value), 'yyyy-MM-dd'))
                            elif value_edit:
                                # Remove LIKE wildcards for display
                                display_value = str(value).strip('%')
                                value_edit.setText(display_value)
    
    def execute_search(self):
        """Execute the search"""
        conditions = self.get_current_conditions()
        
        # Check if we have any conditions
        has_conditions = any(k != 'logic' for k in conditions.keys())
        if not has_conditions:
            QMessageBox.warning(self, self.translator.tr('msg_warning') if hasattr(self.translator, 'tr') else 'Warning',
                             "Please add at least one search condition")
            return
        
        # Execute search
        try:
            self.results = DatabaseManager.advanced_search(self.table_name, conditions)
            self.display_results()
            
            # Add to history
            search_term = self._get_search_description(conditions)
            self.search_history_manager.add_to_history(
                search_term=search_term,
                table_name=self.table_name,
                conditions=conditions,
                result_count=len(self.results)
            )
            self.load_history()
            
            # Emit signal with results
            self.search_executed.emit(self.results)
            
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error') if hasattr(self.translator, 'tr') else 'Error',
                               f"Search failed: {str(e)}")
            logger.error(f"Advanced search error: {e}")
    
    def _get_search_description(self, conditions: Dict) -> str:
        """Generate a human-readable description of the search"""
        parts = []
        logic = conditions.get('logic', 'AND')
        
        for field, cond in conditions.items():
            if field == 'logic':
                continue
            if isinstance(cond, dict):
                operator = cond.get('operator', '=')
                value = cond.get('value', '')
                if value:
                    parts.append(f"{field} {operator} '{value}'")
                else:
                    parts.append(f"{field} {operator}")
        
        return f" {logic} ".join(parts) if parts else (self.translator.tr('search_empty') if self.translator and hasattr(self.translator, 'tr') else "Empty search")
    
    def display_results(self):
        """Display search results"""
        if not self.results:
            self.results_table.setRowCount(0)
            self.results_count_label.setText("0 results")
            return
        
        # Get column names from first result
        if self.results:
            columns = list(self.results[0].keys())
            self.results_table.setColumnCount(len(columns))
            self.results_table.setHorizontalHeaderLabels(columns)
            self.results_table.setRowCount(len(self.results))
            
            for row_idx, row_data in enumerate(self.results):
                for col_idx, col_key in enumerate(columns):
                    value = row_data.get(col_key, '')
                    item = QTableWidgetItem(str(value)[:200])  # Truncate long values
                    self.results_table.setItem(row_idx, col_idx, item)
            
            self.results_table.resizeColumnsToContents()
            self.results_count_label.setText(f"{len(self.results)} results")
    
    # ==================== Saved Searches ====================
    
    def load_saved_searches(self):
        """Load saved searches into the list"""
        self.saved_searches_list.clear()
        saved = self.search_history_manager.get_saved_searches(self.table_name)
        
        for search in saved:
            item = QListWidgetItem(search.get('name', 'Unnamed'))
            item.setData(Qt.UserRole, search.get('id'))
            item.setToolTip(search.get('description', ''))
            self.saved_searches_list.addItem(item)
        
        # Load frequently used
        self.load_frequently_used()
    
    def load_frequently_used(self):
        """Load frequently used searches"""
        self.frequent_list.clear()
        frequent = self.search_history_manager.get_frequently_used(self.table_name, limit=10)
        
        for search in frequent:
            use_count = search.get('use_count', 0)
            item = QListWidgetItem(f"{search.get('name', 'Unnamed')} ({use_count} uses)")
            item.setData(Qt.UserRole, search.get('id'))
            self.frequent_list.addItem(item)
    
    def save_search(self):
        """Save current search as a new saved search"""
        conditions = self.get_current_conditions()
        
        has_conditions = any(k != 'logic' for k in conditions.keys())
        if not has_conditions:
            QMessageBox.warning(self, self.translator.tr('msg_warning') if hasattr(self.translator, 'tr') else 'Warning',
                             "Please add at least one search condition to save")
            return
        
        name, ok = QInputDialog.getText(
            self,
            self.translator.tr('search_save') if hasattr(self.translator, 'tr') else 'Save Search',
            self.translator.tr('search_enter_name') if hasattr(self.translator, 'tr') else 'Enter a name for this search:'
        )
        
        if ok and name:
            description, _ = QInputDialog.getText(
                self,
                self.translator.tr('search_description') if hasattr(self.translator, 'tr') else 'Description',
                self.translator.tr('search_enter_description') if hasattr(self.translator, 'tr') else 'Enter a description (optional):'
            )
            
            success = self.search_history_manager.save_search(
                name=name,
                table_name=self.table_name,
                conditions=conditions,
                description=description
            )
            
            if success:
                QMessageBox.information(
                    self,
                    self.translator.tr('msg_success') if hasattr(self.translator, 'tr') else 'Success',
                    self.translator.tr('search_saved_success') if hasattr(self.translator, 'tr') else 'Search saved successfully'
                )
                self.load_saved_searches()
            else:
                QMessageBox.warning(
                    self,
                    self.translator.tr('msg_warning') if hasattr(self.translator, 'tr') else 'Warning',
                    self.translator.tr('search_save_failed') if hasattr(self.translator, 'tr') else 'Failed to save search'
                )
    
    def update_saved_search(self):
        """Update an existing saved search"""
        current_item = self.saved_searches_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, self.translator.tr('msg_warning') if hasattr(self.translator, 'tr') else 'Warning',
                             "Please select a saved search to update")
            return
        
        search_id = current_item.data(Qt.UserRole)
        existing = self.search_history_manager.get_saved_search(search_id)
        
        if existing:
            conditions = self.get_current_conditions()
            success = self.search_history_manager.save_search(
                name=existing.get('name'),
                table_name=self.table_name,
                conditions=conditions,
                description=existing.get('description', '')
            )
            
            if success:
                QMessageBox.information(
                    self,
                    self.translator.tr('msg_success') if hasattr(self.translator, 'tr') else 'Success',
                    'Search updated successfully'
                )
                self.load_saved_searches()
    
    def load_selected_saved_search(self):
        """Load the selected saved search"""
        current_item = self.saved_searches_list.currentItem()
        if current_item:
            self.load_saved_search(current_item)
    
    def load_saved_search(self, item: QListWidgetItem):
        """Load a saved search into the query builder"""
        search_id = item.data(Qt.UserRole)
        search = self.search_history_manager.get_saved_search(search_id)
        
        if search:
            conditions = search.get('conditions', {})
            if conditions:
                self.set_conditions_from_dict(conditions)
                self.search_history_manager.increment_use_count(search_id)
                self.load_frequently_used()
    
    def load_frequent_search(self, item: QListWidgetItem):
        """Load a frequently used search"""
        search_id = item.data(Qt.UserRole)
        search = self.search_history_manager.get_saved_search(search_id)
        
        if search:
            conditions = search.get('conditions', {})
            if conditions:
                self.set_conditions_from_dict(conditions)
                self.search_history_manager.increment_use_count(search_id)
                self.load_frequently_used()
    
    def delete_selected_saved_search(self):
        """Delete the selected saved search"""
        current_item = self.saved_searches_list.currentItem()
        if not current_item:
            return
        
        reply = QMessageBox.question(
            self,
            self.translator.tr('msg_confirm') if hasattr(self.translator, 'tr') else 'Confirm',
            self.translator.tr('search_delete_confirm') if hasattr(self.translator, 'tr') else 'Are you sure you want to delete this saved search?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            search_id = current_item.data(Qt.UserRole)
            if self.search_history_manager.delete_saved_search(search_id):
                self.load_saved_searches()
    
    def show_saved_search_context_menu(self, position):
        """Show context menu for saved searches"""
        item = self.saved_searches_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        load_action = QAction(self.translator.tr('search_load') if hasattr(self.translator, 'tr') else 'Load', self)
        load_action.triggered.connect(lambda: self.load_saved_search(item))
        menu.addAction(load_action)
        
        menu.addSeparator()
        
        delete_action = QAction(self.translator.tr('btn_delete') if hasattr(self.translator, 'tr') else 'Delete', self)
        delete_action.triggered.connect(self.delete_selected_saved_search)
        menu.addAction(delete_action)
        
        menu.exec_(self.saved_searches_list.mapToGlobal(position))
    
    # ==================== Search History ====================
    
    def load_history(self):
        """Load search history into the list"""
        self.history_list.clear()
        history = self.search_history_manager.get_history(self.table_name, limit=30)
        
        for entry in history:
            search_term = entry.get('search_term', 'Unknown')
            result_count = entry.get('result_count', 0)
            timestamp = entry.get('timestamp', '')[:10]
            
            display_text = f"{search_term[:50]}... ({result_count} results) - {timestamp}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, entry)
            self.history_list.addItem(item)
    
    def load_selected_history_item(self):
        """Load the selected history item"""
        current_item = self.history_list.currentItem()
        if current_item:
            self.load_history_item(current_item)
    
    def load_history_item(self, item: QListWidgetItem):
        """Load a history item into the query builder"""
        entry = item.data(Qt.UserRole)
        if entry:
            conditions = entry.get('conditions')
            if conditions:
                self.set_conditions_from_dict(conditions)
    
    def clear_search_history(self):
        """Clear search history"""
        reply = QMessageBox.question(
            self,
            self.translator.tr('msg_confirm') if hasattr(self.translator, 'tr') else 'Confirm',
            self.translator.tr('search_clear_history_confirm') if hasattr(self.translator, 'tr') else 'Are you sure you want to clear search history?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.search_history_manager.clear_history(self.table_name)
            self.load_history()
    
    def show_history_context_menu(self, position):
        """Show context menu for history"""
        item = self.history_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        load_action = QAction(self.translator.tr('search_load') if hasattr(self.translator, 'tr') else 'Load', self)
        load_action.triggered.connect(lambda: self.load_history_item(item))
        menu.addAction(load_action)
        
        save_action = QAction(self.translator.tr('search_save') if hasattr(self.translator, 'tr') else 'Save as Search', self)
        save_action.triggered.connect(lambda: self.save_history_as_search(item))
        menu.addAction(save_action)
        
        menu.exec_(self.history_list.mapToGlobal(position))
    
    def save_history_as_search(self, item: QListWidgetItem):
        """Save a history item as a saved search"""
        entry = item.data(Qt.UserRole)
        if entry:
            conditions = entry.get('conditions')
            if conditions:
                self.set_conditions_from_dict(conditions)
                self.save_search()
    
    def get_results(self) -> List[Dict]:
        """Get search results"""
        return self.results
