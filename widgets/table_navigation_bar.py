"""
Table Navigation Bar Widget
Provides navigation controls and position indicators for table viewing
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QLineEdit, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from styles.styles import AppStyles
from translations.translations import TranslationManager
from icons.icon_manager import setup_icon_button


class TableNavigationBar(QWidget):
    """
    Navigation bar for table viewing with position indicators and controls.
    Provides quick navigation to specific rows and shows current position.
    """
    
    # Signals
    go_to_row = pyqtSignal(int)  # Emitted when user wants to go to a specific row
    first_row = pyqtSignal()     # Go to first row
    previous_row = pyqtSignal()  # Go to previous row
    next_row = pyqtSignal()      # Go to next row
    last_row = pyqtSignal()      # Go to last row
    
    def __init__(self, parent=None, translator: TranslationManager = None):
        super().__init__(parent)
        self.translator = translator
        self.current_row = 0
        self.total_rows = 0
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup navigation bar UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Position label
        self.position_label = QLabel()
        self.position_label.setStyleSheet("""
            font-size: 9px;
            color: #666;
            padding: 2px 8px;
        """)
        self.update_position_text()
        layout.addWidget(self.position_label)
        
        layout.addSpacing(8)
        
        # First row button
        self.btn_first = QPushButton("⏮")
        self.btn_first.setFixedSize(28, 24)
        self.btn_first.setToolTip(self.translator.tr('pagination_first') if self.translator else 'First Row')
        self.btn_first.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f5f5f5;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #999;
            }
        """)
        self.btn_first.clicked.connect(self.first_row.emit)
        layout.addWidget(self.btn_first)
        
        # Previous row button
        self.btn_prev = QPushButton("◀")
        self.btn_prev.setFixedSize(28, 24)
        self.btn_prev.setToolTip(self.translator.tr('pagination_previous') if self.translator else 'Previous Row')
        self.btn_prev.setStyleSheet(self.btn_first.styleSheet())
        self.btn_prev.clicked.connect(self.previous_row.emit)
        layout.addWidget(self.btn_prev)
        
        # Go to row input
        go_to_text = self.translator.tr('pagination_page') if self.translator else 'Row'
        self.go_to_label = QLabel(f"{go_to_text}:")
        self.go_to_label.setStyleSheet("font-size: 9px; color: #666;")
        layout.addWidget(self.go_to_label)
        
        self.go_to_input = QLineEdit()
        self.go_to_input.setFixedSize(50, 24)
        self.go_to_input.setPlaceholderText("?")
        self.go_to_input.setStyleSheet("""
            QLineEdit {
                font-size: 9px;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 2px 4px;
            }
            QLineEdit:focus {
                border: 1px solid #3498DB;
            }
        """)
        self.go_to_input.returnPressed.connect(self._on_go_to_pressed)
        layout.addWidget(self.go_to_input)
        
        # Total rows label
        of_text = self.translator.tr('pagination_of') if self.translator else 'of'
        self.total_label = QLabel(f" {of_text} 0")
        self.total_label.setStyleSheet("font-size: 9px; color: #666;")
        layout.addWidget(self.total_label)
        
        # Next row button
        self.btn_next = QPushButton("▶")
        self.btn_next.setFixedSize(28, 24)
        self.btn_next.setToolTip(self.translator.tr('pagination_next') if self.translator else 'Next Row')
        self.btn_next.setStyleSheet(self.btn_first.styleSheet())
        self.btn_next.clicked.connect(self.next_row.emit)
        layout.addWidget(self.btn_next)
        
        # Last row button
        self.btn_last = QPushButton("⏭")
        self.btn_last.setFixedSize(28, 24)
        self.btn_last.setToolTip(self.translator.tr('pagination_last') if self.translator else 'Last Row')
        self.btn_last.setStyleSheet(self.btn_first.styleSheet())
        self.btn_last.clicked.connect(self.last_row.emit)
        layout.addWidget(self.btn_last)
        
        layout.addStretch()
        
        # Update button states
        self.update_button_states()
    
    def _on_go_to_pressed(self):
        """Handle go to row input"""
        try:
            row_num = int(self.go_to_input.text())
            if 1 <= row_num <= self.total_rows:
                self.go_to_row.emit(row_num - 1)  # Convert to 0-based index
            else:
                self.go_to_input.clear()
        except ValueError:
            self.go_to_input.clear()
    
    def set_current_row(self, row: int):
        """Set current row (0-based)"""
        self.current_row = row
        self.update_position_text()
        self.update_button_states()
    
    def set_total_rows(self, total: int):
        """Set total number of rows"""
        self.total_rows = total
        of_text = self.translator.tr('pagination_of') if self.translator else 'of'
        self.total_label.setText(f" {of_text} {total}")
        self.update_position_text()
        self.update_button_states()
    
    def update_position_text(self):
        """Update position label text"""
        if self.translator:
            if self.total_rows > 0:
                self.position_label.setText(
                    self.translator.tr('pagination_row_position', 
                                      current=self.current_row + 1, total=self.total_rows))
            else:
                self.position_label.setText(self.translator.tr('pagination_no_rows'))
        else:
            if self.total_rows > 0:
                self.position_label.setText(f"Row {self.current_row + 1} / {self.total_rows}")
            else:
                self.position_label.setText("No rows")
    
    def update_button_states(self):
        """Update button enabled states based on current position"""
        has_rows = self.total_rows > 0
        is_first = self.current_row == 0
        is_last = self.current_row >= self.total_rows - 1
        
        self.btn_first.setEnabled(has_rows and not is_first)
        self.btn_prev.setEnabled(has_rows and not is_first)
        self.btn_next.setEnabled(has_rows and not is_last)
        self.btn_last.setEnabled(has_rows and not is_last)
    
    def refresh_translations(self):
        """Refresh translations when language changes"""
        if self.translator:
            self.btn_first.setToolTip(self.translator.tr('pagination_first'))
            self.btn_prev.setToolTip(self.translator.tr('pagination_previous'))
            self.btn_next.setToolTip(self.translator.tr('pagination_next'))
            self.btn_last.setToolTip(self.translator.tr('pagination_last'))
            
            go_to_text = self.translator.tr('pagination_page')
            self.go_to_label.setText(f"{go_to_text}:")
            
            of_text = self.translator.tr('pagination_of')
            if self.total_rows > 0:
                self.total_label.setText(f" {of_text} {self.total_rows}")
                self.update_position_text()
