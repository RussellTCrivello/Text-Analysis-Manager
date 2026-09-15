"""
Enhanced Widgets for PyQt5 Application
Custom widgets with advanced functionality
"""
import os
import re
from typing import List, Dict, Optional, Callable
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLineEdit, QPushButton,
    QFileDialog, QLabel, QVBoxLayout, QListWidget, QListWidgetItem,
    QTextEdit, QFrame, QScrollArea, QCompleter, QStyledItemDelegate
)
from icons.icon_manager import setup_icon_button, get_icon
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QRegExp, QStringListModel
from PyQt5.QtGui import QKeyEvent, QRegExpValidator, QValidator, QFont, QColor, QPalette
from styles.styles import AppStyles


class AutoCompleteLineEdit(QLineEdit):
    """
    Line edit with autocomplete functionality.
    Shows suggestions from existing database values with "New Entry" indicator.
    """
    
    # Signal when a new value is entered (not in existing list)
    new_value_entered = pyqtSignal(str)
    
    def __init__(self, parent=None, placeholder: str = "", translator=None):
        super().__init__(parent)
        self.translator = translator
        self.existing_values = []
        self._is_new_entry = False
        
        # Setup completer
        self.completer_model = QStringListModel()
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)  # Match anywhere in string
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.setCompleter(self.completer)
        
        # Style the popup and prevent it from affecting parent window size
        popup = self.completer.popup()
        # Set window flags to make popup independent of parent layout
        popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        popup.setStyleSheet(AppStyles.get_component_style('autocomplete_popup'))
        
        # Placeholder
        if placeholder:
            self.setPlaceholderText(placeholder)
        
        # Connect signals
        self.textChanged.connect(self._on_text_changed)
        self.editingFinished.connect(self._on_editing_finished)
    
    def set_suggestions(self, values: List[str]):
        """Set the list of autocomplete suggestions"""
        self.existing_values = [v for v in values if v]  # Filter out empty values
        self.completer_model.setStringList(self.existing_values)
    
    def add_suggestion(self, value: str):
        """Add a new suggestion to the list"""
        if value and value not in self.existing_values:
            self.existing_values.append(value)
            self.completer_model.setStringList(self.existing_values)
    
    def _on_text_changed(self, text: str):
        """Handle text change - check if it's a new value"""
        text = text.strip()
        if text:
            self._is_new_entry = text.lower() not in [v.lower() for v in self.existing_values]
            self._update_style()
        else:
            self._is_new_entry = False
            self._update_style()
    
    def _on_editing_finished(self):
        """Handle editing finished"""
        text = self.text().strip()
        if text and self._is_new_entry:
            self.new_value_entered.emit(text)
    
    def _update_style(self):
        """Update visual style based on new entry status"""
        if self._is_new_entry:
            # Highlight as new entry with a subtle indicator
            self.setStyleSheet(AppStyles.get_component_style('new_entry_highlight'))
            # Update tooltip
            new_text = self.translator.tr('msg_new_entry') if self.translator else "New Entry"
            self.setToolTip(new_text)
        else:
            # Reset to default style
            self.setStyleSheet("")
            self.setToolTip("")
    
    def is_new_entry(self) -> bool:
        """Check if current value is a new entry"""
        return self._is_new_entry


class AutoCompleteTextEdit(QWidget):
    """
    Text area with autocomplete functionality for multiple values.
    Supports comma or semicolon separated values with autocomplete for each.
    """
    
    value_changed = pyqtSignal(str)
    
    def __init__(self, parent=None, separator: str = ',', placeholder: str = "", translator=None):
        super().__init__(parent)
        self.translator = translator
        self.separator = separator
        self.existing_values = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid (rounding 4px to 8px)
        
        # Quick add line with autocomplete
        self.quick_add = AutoCompleteLineEdit(self, placeholder, translator)
        self.quick_add.returnPressed.connect(self._add_value)
        layout.addWidget(self.quick_add)
        
        # Main text area for all values
        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(80)
        placeholder = (self.translator.tr('msg_values_separated', sep=separator)
                      if self.translator and hasattr(self.translator, 'tr')
                      else f"Values separated by '{separator}' or new lines")
        self.text_edit.setPlaceholderText(placeholder)
        self.text_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_edit)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(AppStyles.get_component_style('status_label_muted'))
        layout.addWidget(self.status_label)
    
    def set_suggestions(self, values: List[str]):
        """Set autocomplete suggestions"""
        self.existing_values = values
        self.quick_add.set_suggestions(values)
    
    def _add_value(self):
        """Add value from quick add line to text area"""
        value = self.quick_add.text().strip()
        if value:
            current = self.text_edit.toPlainText().strip()
            if current:
                # Add separator if needed
                if not current.endswith(self.separator) and not current.endswith('\n'):
                    current += f"{self.separator} "
                current += value
            else:
                current = value
            self.text_edit.setPlainText(current)
            self.quick_add.clear()
    
    def _on_text_changed(self):
        """Handle text change"""
        values = self.get_values()
        if values:
            text = (self.translator.tr('msg_entries_count', count=len(values))
                    if self.translator and hasattr(self.translator, 'tr')
                    else f"{len(values)} entries")
            self.status_label.setText(text)
        else:
            self.status_label.setText("")
        self.value_changed.emit(self.get_value())
    
    def get_values(self) -> List[str]:
        """Get list of values"""
        text = self.text_edit.toPlainText()
        values = []
        for line in text.split('\n'):
            for part in line.split(self.separator):
                value = part.strip()
                if value:
                    values.append(value)
        return values
    
    def get_value(self) -> str:
        """Get values as separator-separated string"""
        return self.separator.join(self.get_values())
    
    def set_value(self, value: str):
        """Set values from separator-separated string"""
        if value:
            values = [v.strip() for v in value.split(self.separator) if v.strip()]
            self.text_edit.setPlainText('\n'.join(values))
        else:
            self.text_edit.clear()


class SearchableComboBox(QWidget):
    """Searchable combo box with quick-add functionality"""
    
    # Signal emitted when "Add New" is selected
    add_new_requested = pyqtSignal()
    # Signal emitted when selection changes
    selection_changed = pyqtSignal(int, str)  # id, text
    
    def __init__(self, parent=None, allow_add_new: bool = True, add_callback: Optional[Callable] = None, translator=None):
        super().__init__(parent)
        self.allow_add_new = allow_add_new
        self.add_callback = add_callback
        self.translator = translator
        self.items_data = []  # List of dicts with 'id', 'text', 'data'
        self.filtered_items = []
        self._refreshing = False  # Flag to prevent recursion
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # We'll add spacing manually for better control
        
        # Combo box with size policy to prevent layout changes
        self.combo = QComboBox()
        self.combo.setEditable(True)
        # Set size adjust policy to prevent combo from changing size when items change
        self.combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.combo.setMinimumContentsLength(15)  # Fixed minimum content length
        placeholder = self.translator.tr('msg_type_to_search') if self.translator else "Type to search..."
        self.combo.lineEdit().setPlaceholderText(placeholder)
        self.combo.lineEdit().textChanged.connect(self.on_search_text_changed)
        self.combo.currentIndexChanged.connect(self.on_selection_changed)
        layout.addWidget(self.combo, 1)
        
        # Add new button with proper spacing (large margin for RTL/Arabic - significant gap like English)
        if allow_add_new:
            add_btn_spacing = AppStyles.get_spacing(6) if (translator and translator.current_language == 'ar') else 10
            layout.addSpacing(add_btn_spacing)
            
            self.btn_add = QPushButton()
            tooltip = self.translator.tr('btn_add_new') if self.translator else "Add New"
            self.btn_add.setProperty('class', 'success')
            setup_icon_button(self.btn_add, 'btn_add_new', tooltip, size=28, use_white_icon=True)
            # Set fixed size for consistent appearance
            self.btn_add.setFixedSize(32, 32)
            # Disable autoDefault to prevent Enter key from triggering this button
            self.btn_add.setAutoDefault(False)
            self.btn_add.setDefault(False)
            self.btn_add.clicked.connect(self.on_add_new)
            layout.addWidget(self.btn_add, 0, Qt.AlignVCenter)
    
    def set_items(self, items: List[Dict]):
        """Set items for the combo box
        items: List of dicts with 'id' and 'text' keys, optionally 'data'
        """
        self.items_data = items
        self.filtered_items = items.copy()
        self.refresh_combo()
    
    def refresh_combo(self):
        """Refresh combo box with filtered items"""
        if self._refreshing:
            return  # Prevent recursion
        
        self._refreshing = True
        try:
            # Block signals on both combo and lineEdit to prevent recursion
            self.combo.blockSignals(True)
            line_edit = self.combo.lineEdit()
            if line_edit:
                line_edit.blockSignals(True)
            
            self.combo.clear()
            
            # Add filtered items
            for item in self.filtered_items:
                display_text = item.get('text', f"{item.get('id', '')} - {item.get('name', '')}")
                self.combo.addItem(display_text, item.get('id'))
            
            # Add "Add New" option at the end
            if self.allow_add_new and len(self.filtered_items) > 0:
                add_new_text = (self.translator.tr('btn_add_new') if self.translator else "Add New") + "..."
                self.combo.addItem(get_icon('add', 16), add_new_text, -1)
            
            # Unblock signals
            self.combo.blockSignals(False)
            if line_edit:
                line_edit.blockSignals(False)
        finally:
            self._refreshing = False
    
    def on_search_text_changed(self, text: str):
        """Handle search text change"""
        if self._refreshing:
            return  # Prevent recursion
        
        if not text:
            self.filtered_items = self.items_data.copy()
        else:
            text_lower = text.lower()
            self.filtered_items = [
                item for item in self.items_data
                if text_lower in str(item.get('id', '')).lower() or
                   text_lower in str(item.get('name', '')).lower() or
                   text_lower in str(item.get('text', '')).lower()
            ]
        
        self.refresh_combo()
        
        # Restore search text (block signals to prevent recursion)
        if text:
            line_edit = self.combo.lineEdit()
            if line_edit:
                line_edit.blockSignals(True)
                line_edit.setText(text)
                line_edit.setCursorPosition(len(text))
                line_edit.blockSignals(False)
    
    def on_selection_changed(self, index: int):
        """Handle selection change"""
        if index < 0:
            return
        
        item_data = self.combo.itemData(index)
        item_text = self.combo.itemText(index)
        
        # Check if "Add New" was selected
        if item_data == -1:
            self.on_add_new()
            return
        
        # Emit signal with selected id and text
        if item_data is not None:
            self.selection_changed.emit(item_data, item_text)
    
    def on_add_new(self):
        """Handle add new button click"""
        if self.add_callback:
            result = self.add_callback()
            if result:
                # Refresh items and select the new one
                self.refresh_items()
                # Find and select the new item
                for i, item in enumerate(self.items_data):
                    if item.get('id') == result:
                        self.combo.setCurrentIndex(i)
                        break
        else:
            self.add_new_requested.emit()
    
    def refresh_items(self):
        """Refresh the visible list from the current item provider state."""
        # Callers that add a record generally update ``items_data`` in their
        # callback. Rebuilding the filtered view here keeps the add-new control
        # deterministic without relying on a placeholder override.
        self.filtered_items = list(self.items_data)
        self.refresh_combo()
        return self.items_data
    
    def get_selected_id(self) -> Optional[int]:
        """Get currently selected ID"""
        current_data = self.combo.currentData()
        if current_data and current_data != -1:
            return current_data
        return None
    
    def set_selected_id(self, item_id: int):
        """Set selected item by ID"""
        for i in range(self.combo.count()):
            if self.combo.itemData(i) == item_id:
                self.combo.setCurrentIndex(i)
                return
    
    def currentText(self) -> str:
        """Get current text"""
        return self.combo.currentText()


class FileAttachmentWidget(QWidget):
    """Widget for file attachments with button"""
    
    files_changed = pyqtSignal(list)  # Emits list of file paths
    
    def __init__(self, parent=None, allow_multiple: bool = True, translator=None):
        super().__init__(parent)
        self.allow_multiple = allow_multiple
        self.translator = translator
        self.file_paths = []
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid (rounding 5px to 8px)
        
        # Graphical attachment marker and descriptive text are separate
        # controls so the icon is never encoded as a Unicode glyph.
        self.attachment_icon = QLabel()
        self.attachment_icon.setPixmap(get_icon('attach_files', 18).pixmap(18, 18))
        self.attachment_icon.setToolTip(
            self.translator.tr('btn_attach_files') if self.translator else 'Attachments'
        )
        layout.addWidget(self.attachment_icon)
        self.label = QLabel(self.translator.tr('msg_no_files') if self.translator else "No files attached")
        self.label.setWordWrap(True)
        self.label.setStyleSheet(AppStyles.get_component_style('attachment_label_empty'))
        layout.addWidget(self.label, 1)
        
        # Attach button
        self.btn_attach = QPushButton()
        attach_tooltip = self.translator.tr('btn_attach_files') if self.translator else "Attach Files"
        setup_icon_button(self.btn_attach, 'btn_attach_files', attach_tooltip)
        self.btn_attach.setProperty('class', 'primary')
        self.btn_attach.clicked.connect(self.attach_files)
        layout.addWidget(self.btn_attach)
        
        # Clear button
        self.btn_clear = QPushButton()
        clear_tooltip = self.translator.tr('btn_clear') if self.translator else "Clear attachments"
        setup_icon_button(self.btn_clear, 'btn_clear', clear_tooltip, size=20)
        self.btn_clear.setMaximumWidth(30)
        self.btn_clear.setProperty('class', 'danger')
        self.btn_clear.clicked.connect(self.clear_files)
        self.btn_clear.setVisible(False)
        layout.addWidget(self.btn_clear)
    
    def attach_files(self):
        """Open file dialog to select files"""
        select_files_text = self.translator.tr('msg_select_files') if self.translator else "Select Files"
        if self.allow_multiple:
            files, _ = QFileDialog.getOpenFileNames(
                self,
                select_files_text,
                "",
                "All Files (*.*)"
            )
        else:
            file, _ = QFileDialog.getOpenFileName(
                self,
                select_files_text,
                "",
                "All Files (*.*)"
            )
            files = [file] if file else []
        
        if files:
            self.file_paths = files
            self.update_display()
            self.files_changed.emit(self.file_paths)
    
    def clear_files(self):
        """Clear attached files"""
        self.file_paths = []
        self.update_display()
        self.files_changed.emit(self.file_paths)
    
    def update_display(self):
        """Update the display label"""
        if not self.file_paths:
            no_files_text = self.translator.tr('msg_no_files') if self.translator else "No files attached"
            self.label.setText(no_files_text)
            self.label.setStyleSheet(AppStyles.get_component_style('attachment_label_empty'))
            self.btn_clear.setVisible(False)
        else:
            if len(self.file_paths) == 1:
                filename = os.path.basename(self.file_paths[0])
                self.label.setText(filename)
            else:
                files_text = self.translator.tr('msg_files_attached', count=len(self.file_paths)) if self.translator else f"{len(self.file_paths)} files attached"
                self.label.setText(files_text)
            self.label.setStyleSheet(AppStyles.get_component_style('attachment_label_filled'))
            self.btn_clear.setVisible(True)
    
    def set_files(self, file_paths: List[str]):
        """Set file paths (from database)"""
        self.file_paths = file_paths if file_paths else []
        self.update_display()
    
    def get_files(self) -> List[str]:
        """Get file paths"""
        return self.file_paths
    
    def get_files_string(self) -> str:
        """Get files as semicolon-separated string for database"""
        return "; ".join(self.file_paths) if self.file_paths else ""


class PercentageSpinBox(QWidget):
    """Widget for importance percentage input and display"""
    
    def __init__(self, parent=None, show_percentage: bool = True):
        super().__init__(parent)
        self.show_percentage = show_percentage
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid (rounding 5px to 8px)
        
        from PyQt5.QtWidgets import QDoubleSpinBox
        
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setRange(0.0, 100.0)
        self.spinbox.setDecimals(2)
        self.spinbox.setSuffix(" %")
        self.spinbox.setSingleStep(0.1)
        layout.addWidget(self.spinbox, 1)
        
        # Progress bar indicator
        from PyQt5.QtWidgets import QProgressBar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setMaximumHeight(20)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress, 2)
        
        # Connect to update progress bar
        self.spinbox.valueChanged.connect(self.update_progress)
    
    def update_progress(self, value: float):
        """Update progress bar"""
        self.progress.setValue(int(value))
    
    def set_value(self, value: float):
        """Set value (0.0-1.0 from database, convert to percentage)"""
        if value is None:
            value = 0.0
        # Convert to float first (handles Decimal types from database)
        value = float(value)
        # Convert from 0.0-1.0 to 0-100
        percentage = value * 100.0
        self.spinbox.setValue(percentage)
    
    def get_value(self) -> float:
        """Get value as 0.0-1.0 for database"""
        # Convert from 0-100 to 0.0-1.0
        return self.spinbox.value() / 100.0
    
    def value(self) -> float:
        """Get value as 0.0-1.0"""
        return self.get_value()
    
    @staticmethod
    def format_percentage(value: float) -> str:
        """Format importance value (0.0-1.0) as percentage string"""
        if value is None:
            return "0.00%"
        # Convert to float first (handles Decimal types from database)
        value = float(value)
        percentage = value * 100.0
        return f"{percentage:.2f}%"


class CoordinateInputWidget(QWidget):
    """Widget for multiple coordinate input with validation and formatting"""
    
    value_changed = pyqtSignal(str)  # Emits formatted coordinate string
    
    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.translator = translator
        self.coordinates = []  # List of (lat, lon) tuples
        self.setup_ui()
    
    def setup_ui(self):
        """Setup coordinate input UI with support for multiple coordinates"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid (rounding 5px to 8px)
        
        # Scroll area for coordinate list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        scroll.setMinimumHeight(150)
        
        scroll_widget = QWidget()
        self.coord_layout = QVBoxLayout(scroll_widget)
        self.coord_layout.setContentsMargins(0, 0, 0, 0)
        self.coord_layout.setSpacing(5)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Add button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_add = QPushButton()
        add_text = self.translator.tr('msg_add_coordinate') if self.translator and hasattr(self.translator, 'tr') else "Add Coordinate"
        setup_icon_button(self.btn_add, 'btn_add', add_text)
        # Disable autoDefault to prevent Enter key from triggering this button
        self.btn_add.setAutoDefault(False)
        self.btn_add.setDefault(False)
        self.btn_add.clicked.connect(self.add_coordinate)
        btn_layout.addWidget(self.btn_add)
        layout.addLayout(btn_layout)
        
        # Add initial empty coordinate if none exist
        if not self.coordinates:
            self.add_coordinate()
    
    def add_coordinate(self, lat: str = "", lon: str = ""):
        """Add a new coordinate input row"""
        coord_frame = QFrame()
        coord_frame.setFrameStyle(QFrame.Box)
        coord_layout = QHBoxLayout(coord_frame)
        # Use 8px grid spacing
        coord_margin = AppStyles.get_spacing(1)  # 8px
        coord_layout.setContentsMargins(coord_margin, coord_margin, coord_margin, coord_margin)
        coord_spacing = AppStyles.get_spacing(2) if (self.translator and self.translator.current_language == 'ar') else AppStyles.get_spacing(1)
        coord_layout.setSpacing(coord_spacing)
        
        # Latitude input
        lat_edit = QLineEdit()
        lat_placeholder = self.translator.tr('msg_latitude_placeholder') if self.translator and hasattr(self.translator, 'tr') else "Latitude (e.g., 40.7128)"
        lat_edit.setPlaceholderText(lat_placeholder)
        lat_validator = QRegExpValidator(QRegExp(r'^-?\d+\.?\d*$'))
        lat_edit.setValidator(lat_validator)
        lat_edit.textChanged.connect(lambda: self.on_coordinate_changed(coord_frame))
        if lat:
            lat_edit.setText(lat)
        lat_label = self.translator.tr('lbl_latitude') if self.translator and hasattr(self.translator, 'tr') else 'Lat'
        coord_layout.addWidget(QLabel(f"{lat_label}:"), 0)
        coord_layout.addWidget(lat_edit, 1)
        
        # Longitude input
        lon_edit = QLineEdit()
        lon_placeholder = self.translator.tr('msg_longitude_placeholder') if self.translator and hasattr(self.translator, 'tr') else "Longitude (e.g., -74.0060)"
        lon_edit.setPlaceholderText(lon_placeholder)
        lon_validator = QRegExpValidator(QRegExp(r'^-?\d+\.?\d*$'))
        lon_edit.setValidator(lon_validator)
        lon_edit.textChanged.connect(lambda: self.on_coordinate_changed(coord_frame))
        if lon:
            lon_edit.setText(lon)
        lon_label = self.translator.tr('lbl_longitude') if self.translator and hasattr(self.translator, 'tr') else 'Lon'
        coord_layout.addWidget(QLabel(f"{lon_label}:"), 0)
        coord_layout.addWidget(lon_edit, 1)
        
        # Add spacing between inputs and buttons - more for RTL
        add_spacing = AppStyles.get_spacing(3) if (self.translator and self.translator.current_language == 'ar') else 15
        coord_layout.addSpacing(add_spacing)
        
        # Remove button (delete icon)
        btn_remove = QPushButton()
        remove_text = self.translator.tr('msg_remove') if self.translator and hasattr(self.translator, 'tr') else "Remove"
        setup_icon_button(btn_remove, 'btn_remove', remove_text, size=24)
        # Disable autoDefault to prevent Enter key from triggering this button
        btn_remove.setAutoDefault(False)
        btn_remove.setDefault(False)
        btn_remove.clicked.connect(lambda: self.remove_coordinate(coord_frame))
        coord_layout.addWidget(btn_remove)
        
        # Format button
        btn_format = QPushButton()
        format_text = self.translator.tr('msg_format_coordinate') if self.translator and hasattr(self.translator, 'tr') else "Format as: lat, lon"
        setup_icon_button(btn_format, 'btn_format', format_text, size=24)
        btn_format.setAutoDefault(False)
        btn_format.setDefault(False)
        btn_format.clicked.connect(lambda: self.format_coordinate(coord_frame))
        coord_layout.addWidget(btn_format)
        
        self.coord_layout.addWidget(coord_frame)
        self.coordinates.append((lat_edit, lon_edit, coord_frame))
    
    def remove_coordinate(self, coord_frame: QFrame):
        """Remove a coordinate input row"""
        # Find and remove from coordinates list
        for i, (lat_edit, lon_edit, frame) in enumerate(self.coordinates):
            if frame == coord_frame:
                self.coordinates.pop(i)
                break
        
        # Remove from layout
        coord_frame.setParent(None)
        coord_frame.deleteLater()
        
        # If no coordinates left, add one empty
        if not self.coordinates:
            self.add_coordinate()
        
        self.emit_value_changed()
    
    def format_coordinate(self, coord_frame: QFrame):
        """Format a single coordinate"""
        for lat_edit, lon_edit, frame in self.coordinates:
            if frame == coord_frame:
                lat = lat_edit.text().strip()
                lon = lon_edit.text().strip()
                
                if lat and lon:
                    try:
                        lat_val = float(lat)
                        lon_val = float(lon)
                        
                        # Validate ranges
                        error_style = AppStyles.get_component_style('input_error')
                        if -90 <= lat_val <= 90 and -180 <= lon_val <= 180:
                            lat_edit.setText(f"{lat_val:.6f}")
                            lon_edit.setText(f"{lon_val:.6f}")
                            lat_edit.setStyleSheet("")
                            lon_edit.setStyleSheet("")
                        else:
                            if not (-90 <= lat_val <= 90):
                                lat_edit.setStyleSheet(error_style)
                            else:
                                lat_edit.setStyleSheet("")
                            if not (-180 <= lon_val <= 180):
                                lon_edit.setStyleSheet(error_style)
                            else:
                                lon_edit.setStyleSheet("")
                    except ValueError:
                        pass
                break
    
    def on_coordinate_changed(self, coord_frame: QFrame):
        """Handle coordinate change"""
        error_style = AppStyles.get_component_style('input_error')
        for lat_edit, lon_edit, frame in self.coordinates:
            if frame == coord_frame:
                lat = lat_edit.text().strip()
                lon = lon_edit.text().strip()
                
                if lat and lon:
                    try:
                        lat_val = float(lat)
                        lon_val = float(lon)
                        
                        # Validate ranges
                        if not (-90 <= lat_val <= 90):
                            lat_edit.setStyleSheet(error_style)
                        else:
                            lat_edit.setStyleSheet("")
                        
                        if not (-180 <= lon_val <= 180):
                            lon_edit.setStyleSheet(error_style)
                        else:
                            lon_edit.setStyleSheet("")
                    except ValueError:
                        pass
                else:
                    lat_edit.setStyleSheet("")
                    lon_edit.setStyleSheet("")
                
                self.emit_value_changed()
                break
    
    def emit_value_changed(self):
        """Emit value changed signal"""
        value = self.get_value()
        self.value_changed.emit(value)
    
    def get_value(self) -> str:
        """Get formatted coordinate string (semicolon-separated)"""
        coords = []
        for lat_edit, lon_edit, _ in self.coordinates:
            lat = lat_edit.text().strip()
            lon = lon_edit.text().strip()
            
            if lat and lon:
                try:
                    lat_val = float(lat)
                    lon_val = float(lon)
                    
                    # Only include valid coordinates
                    if -90 <= lat_val <= 90 and -180 <= lon_val <= 180:
                        coords.append(f"{lat_val}, {lon_val}")
                except ValueError:
                    pass
        
        return "; ".join(coords)
    
    def set_value(self, value: str):
        """Set coordinate values from string (semicolon-separated format: "lat1, lon1; lat2, lon2")"""
        # Clear existing coordinates
        for _, _, frame in self.coordinates:
            frame.setParent(None)
            frame.deleteLater()
        self.coordinates = []
        
        if not value:
            self.add_coordinate()
            return
        
        try:
            # Parse semicolon-separated coordinates (supports both old single format and new multiple format)
            # If no semicolon, treat as single coordinate (backward compatibility)
            if ';' in value:
                coord_strings = [c.strip() for c in value.split(';') if c.strip()]
            else:
                # Single coordinate (old format)
                coord_strings = [value.strip()] if value.strip() else []
            
            for coord_str in coord_strings:
                # Parse "lat, lon" format
                parts = coord_str.split(',')
                if len(parts) == 2:
                    lat = parts[0].strip()
                    lon = parts[1].strip()
                    self.add_coordinate(lat, lon)
            
            # If no valid coordinates found, add one empty
            if not self.coordinates:
                self.add_coordinate()
        except Exception:
            # If parsing fails, add one empty coordinate
            self.add_coordinate()


class MultiEmailUrlWidget(QWidget):
    """Widget for multiple email addresses and URLs input"""
    
    value_changed = pyqtSignal(list)  # Emits list of emails/URLs
    
    # Email regex pattern
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # URL regex pattern
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    def __init__(self, parent=None, separator: str = ';', translator=None):
        super().__init__(parent)
        self.separator = separator
        self.translator = translator
        self.setup_ui()
    
    def setup_ui(self):
        """Setup multi-email/URL input UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid (rounding 5px to 8px)
        
        # Text edit for multiple entries
        self.text_edit = QTextEdit()
        placeholder = (self.translator.tr('msg_accounts_placeholder')
                      if self.translator and hasattr(self.translator, 'tr')
                      else f"Enter multiple emails or URLs separated by '{self.separator}' or new lines.\n"
                            f"Example: email1@example.com; email2@example.com\n"
                            f"         https://example.com; http://another.com")
        self.text_edit.setPlaceholderText(placeholder)
        self.text_edit.setMaximumHeight(100)
        self.text_edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.text_edit)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(AppStyles.get_component_style('status_label_muted'))
        layout.addWidget(self.status_label)
        
        # Buttons layout - extra spacing for RTL
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_spacing = AppStyles.get_spacing(3) if (self.translator and self.translator.current_language == 'ar') else AppStyles.get_spacing(1)
        btn_layout.setSpacing(btn_spacing)
        
        self.btn_validate = QPushButton()
        validate_text = self.translator.tr('msg_validate_entries') if self.translator and hasattr(self.translator, 'tr') else "Validate all entries"
        setup_icon_button(self.btn_validate, 'btn_validate', validate_text, size=20)
        self.btn_validate.clicked.connect(self.validate_all)
        btn_layout.addWidget(self.btn_validate)
        
        self.btn_format = QPushButton()
        format_text = self.translator.tr('msg_format_entries') if self.translator and hasattr(self.translator, 'tr') else "Format entries (one per line)"
        setup_icon_button(self.btn_format, 'btn_format', format_text, size=20)
        self.btn_format.clicked.connect(self.format_entries)
        btn_layout.addWidget(self.btn_format)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def on_text_changed(self):
        """Handle text change"""
        text = self.text_edit.toPlainText()
        entries = self.parse_entries(text)
        self.value_changed.emit(entries)
        self.update_status(len(entries))
    
    def parse_entries(self, text: str) -> List[str]:
        """Parse text into list of entries"""
        if not text:
            return []
        
        # Split by separator or newlines
        entries = []
        for line in text.split('\n'):
            for entry in line.split(self.separator):
                entry = entry.strip()
                if entry:
                    entries.append(entry)
        
        return entries
    
    def validate_all(self):
        """Validate all entries"""
        text = self.text_edit.toPlainText()
        entries = self.parse_entries(text)
        
        if not entries:
            no_entries_msg = self.translator.tr('msg_no_entries_to_validate') if hasattr(self, 'translator') and self.translator else 'No entries to validate'
            self.status_label.setText(no_entries_msg)
            self.status_label.setStyleSheet(AppStyles.get_component_style('status_label_muted'))
            return
        
        valid_count = 0
        invalid_entries = []
        
        for entry in entries:
            is_email = bool(self.EMAIL_PATTERN.match(entry))
            is_url = bool(self.URL_PATTERN.match(entry))
            
            if is_email or is_url:
                valid_count += 1
            else:
                invalid_entries.append(entry)
        
        translator = getattr(self, 'translator', None)
        if invalid_entries:
            message = (
                translator.tr(
                    'msg_invalid_entries_count',
                    count=len(invalid_entries),
                    entries=', '.join(invalid_entries[:3])
                )
                if translator else
                f"Warning: {len(invalid_entries)} invalid: {', '.join(invalid_entries[:3])}"
            )
            self.status_label.setText(message)
            self.status_label.setStyleSheet(AppStyles.get_component_style('status_label_error'))
        else:
            message = (
                translator.tr('msg_valid_entries_count', count=valid_count)
                if translator else f"Valid: all {valid_count} entries"
            )
            self.status_label.setText(message)
            self.status_label.setStyleSheet(AppStyles.get_component_style('status_label_success'))
    
    def format_entries(self):
        """Format entries (one per line)"""
        text = self.text_edit.toPlainText()
        entries = self.parse_entries(text)
        
        if entries:
            formatted = '\n'.join(entries)
            self.text_edit.setPlainText(formatted)
    
    def get_value(self) -> str:
        """Get entries as separator-separated string"""
        text = self.text_edit.toPlainText()
        entries = self.parse_entries(text)
        return self.separator.join(entries)
    
    def set_value(self, value: str):
        """Set entries from separator-separated string"""
        if not value:
            return
        
        # Parse and format
        entries = [e.strip() for e in value.split(self.separator) if e.strip()]
        if entries:
            self.text_edit.setPlainText('\n'.join(entries))
    
    def get_entries(self) -> List[str]:
        """Get list of entries"""
        text = self.text_edit.toPlainText()
        return self.parse_entries(text)
    
    def update_status(self, count: int):
        """Update status label"""
        if count == 0:
            self.status_label.setText("")
        else:
            self.status_label.setText(f"{count} entry/entries")
            self.status_label.setStyleSheet(AppStyles.get_component_style('status_label_muted'))
