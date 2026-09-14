"""
Column Selection Dialog for Export
Allows users to select which columns to export
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QCheckBox, QScrollArea, QWidget
)
from icons.icon_manager import setup_icon_button
from PyQt5.QtCore import Qt
from typing import List, Tuple, Set
from translations.translations import TranslationManager
from styles.styles import AppStyles


class ColumnSelectionDialog(QDialog):
    """Dialog for selecting columns to export"""
    
    def __init__(self, parent=None, columns: List[Tuple[str, str]] = None, 
                 translator: TranslationManager = None, 
                 include_all_fields: bool = True,
                 all_available_keys: Set[str] = None):
        """
        Initialize column selection dialog
        
        Args:
            parent: Parent widget
            columns: List of tuples (key, header) for displayed columns
            translator: Translation manager
            include_all_fields: Whether to show all available fields
            all_available_keys: Set of all available keys from data
        """
        super().__init__(parent)
        self.translator = translator or TranslationManager()
        self.columns = columns or []
        self.include_all_fields = include_all_fields
        self.all_available_keys = all_available_keys or set()
        self.selected_keys = set()
        
        self._apply_rtl_direction()
        self.setup_ui()
        self._apply_rtl_direction()
        self.populate_columns()
    
    def _apply_rtl_direction(self):
        """Apply RTL/LTR direction based on current language"""
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)
        for child in self.findChildren(QWidget):
            child.setLayoutDirection(direction)
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle(self.translator.tr('lbl_select_columns'))
        # Apply fixed size to prevent resizing on button clicks or content changes
        from styles.styles import AppStyles
        AppStyles.apply_fixed_size(self, 500, 450)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid (rounding 10px to 16px)
        
        # Label
        label = QLabel(self.translator.tr('msg_select_columns_to_export') + ":")
        layout.addWidget(label)
        
        # Scroll area for checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setAlignment(Qt.AlignTop)
        
        # Container for checkboxes
        self.checkbox_container = QWidget()
        self.checkbox_layout = QVBoxLayout(self.checkbox_container)
        self.checkbox_layout.setAlignment(Qt.AlignTop)
        scroll_layout.addWidget(self.checkbox_container)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Select All / Deselect All buttons
        self.btn_select_all = QPushButton()
        setup_icon_button(self.btn_select_all, 'btn_select_all', self.translator.tr('btn_select_all'))
        # Disable autoDefault to prevent Enter key from triggering buttons unexpectedly
        self.btn_select_all.setAutoDefault(False)
        self.btn_select_all.setDefault(False)
        self.btn_select_all.clicked.connect(self.select_all)
        button_layout.addWidget(self.btn_select_all)
        
        self.btn_deselect_all = QPushButton()
        setup_icon_button(self.btn_deselect_all, 'btn_deselect_all', self.translator.tr('btn_deselect_all'))
        self.btn_deselect_all.setAutoDefault(False)
        self.btn_deselect_all.setDefault(False)
        self.btn_deselect_all.clicked.connect(self.deselect_all)
        button_layout.addWidget(self.btn_deselect_all)
        
        button_layout.addStretch()
        
        self.btn_ok = QPushButton()
        setup_icon_button(self.btn_ok, 'btn_ok', self.translator.tr('btn_ok'))
        self.btn_ok.setAutoDefault(False)
        self.btn_ok.setDefault(False)
        self.btn_ok.clicked.connect(self.accept)
        button_layout.addWidget(self.btn_ok)
        
        self.btn_cancel = QPushButton()
        setup_icon_button(self.btn_cancel, 'btn_cancel', self.translator.tr('btn_cancel'))
        self.btn_cancel.setAutoDefault(False)
        self.btn_cancel.setDefault(False)
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
        
        # Store checkboxes
        self.checkboxes = {}
    
    def populate_columns(self):
        """Populate column checkboxes"""
        # Clear existing checkboxes
        for i in reversed(range(self.checkbox_layout.count())):
            self.checkbox_layout.itemAt(i).widget().setParent(None)
        self.checkboxes.clear()
        
        # Get all columns to display
        export_columns = []
        
        # Add displayed columns first
        column_dict = {col[0]: col[1] for col in self.columns}
        displayed_keys = [col[0] for col in self.columns]
        
        for key in displayed_keys:
            header = column_dict.get(key, self.format_field_name(key))
            export_columns.append((key, header, True))  # True means it's a displayed column
        
        # Add other available fields if include_all_fields is True
        if self.include_all_fields and self.all_available_keys:
            other_keys = sorted([k for k in self.all_available_keys if k not in displayed_keys])
            for key in other_keys:
                header = column_dict.get(key, self.format_field_name(key))
                export_columns.append((key, header, False))  # False means it's an additional field
        
        # Create checkboxes
        for key, header, is_displayed in export_columns:
            checkbox = QCheckBox(header)
            checkbox.setChecked(True)  # All selected by default
            checkbox.setProperty('column_key', key)
            checkbox.setProperty('is_displayed', is_displayed)
            
            # Style displayed columns differently
            if is_displayed:
                checkbox.setStyleSheet(f"font-weight: bold; color: {AppStyles.get_color('TEXT_PRIMARY')}")
            
            self.checkboxes[key] = checkbox
            self.checkbox_layout.addWidget(checkbox)
            self.selected_keys.add(key)
    
    def format_field_name(self, key: str) -> str:
        """Format field name for display (convert snake_case to Title Case)"""
        return key.replace('_', ' ').title()
    
    def select_all(self):
        """Select all columns"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)
            self.selected_keys.add(checkbox.property('column_key'))
    
    def deselect_all(self):
        """Deselect all columns"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
        self.selected_keys.clear()
    
    def get_selected_columns(self) -> List[Tuple[str, str]]:
        """Get list of selected columns as (key, header) tuples"""
        selected = []
        for key, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                header = checkbox.text()
                selected.append((key, header))
                self.selected_keys.add(key)
            else:
                self.selected_keys.discard(key)
        return selected
    
    def exec_(self):
        """Override exec_ to update selected_keys before returning"""
        result = super().exec_()
        if result == QDialog.Accepted:
            # Update selected_keys based on current checkbox states
            self.selected_keys.clear()
            for key, checkbox in self.checkboxes.items():
                if checkbox.isChecked():
                    self.selected_keys.add(key)
        return result
