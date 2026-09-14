"""
Pagination Widget for Table Views
Provides pagination controls for large datasets with compact modern styling
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, 
    QSpinBox, QComboBox, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QCursor
from translations.translations import TranslationManager
from styles.styles import AppStyles
from icons.icon_manager import get_icon


class CircularNavButton(QPushButton):
    """Modern compact circular navigation button with icons."""
    
    def __init__(self, icon_name: str, tooltip_text: str = "", parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        self.setToolTip(tooltip_text)
        self.setObjectName("circularNavButton")
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Set icon with smaller size
        self._setup_icon()
    
    def _setup_icon(self):
        """Setup the button icon - smaller for compact design"""
        icon = get_icon(self.icon_name, 18)
        if not icon.isNull():
            self.setIcon(icon)
            self.setIconSize(QSize(18, 18))


class PageIndicatorLabel(QLabel):
    """Compact page indicator with pill shape."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pageIndicatorButton")
        self.setAlignment(Qt.AlignCenter)


class ModernPageSpinBox(QSpinBox):
    """Compact modern spinbox for page input."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("modernPageSpinBox")
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(QCursor(Qt.IBeamCursor))


class ModernPageSizeCombo(QComboBox):
    """Compact styled combo box for page size selection."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("modernPageSizeCombo")
        self.setCursor(QCursor(Qt.PointingHandCursor))


class PaginationWidget(QWidget):
    """Modern compact pagination control widget"""
    
    page_changed = pyqtSignal(int)  # Emitted when page changes
    page_size_changed = pyqtSignal(int)  # Emitted when page size changes
    
    def __init__(self, translator: TranslationManager, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.current_page = 1
        self.page_size = 50
        self.total_items = 0
        self.total_pages = 0
        
        # Apply RTL/LTR direction based on current language
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)
        
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """Setup pagination UI with compact modern design"""
        # Compact fixed sizes (no DPI scaling to avoid issues)
        BTN_SIZE = 36
        INDICATOR_HEIGHT = 36
        SPIN_WIDTH = 60
        COMBO_WIDTH = 70
        
        # Main container
        self.setObjectName("paginationWidget")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(60)  # Fixed height for consistency
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Inner container
        container = QFrame()
        container.setObjectName("premiumPaginationContainer")
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        container_layout = QHBoxLayout(container)
        # Use 8px grid spacing
        container_margin_h = AppStyles.get_spacing(2)  # 16px horizontal
        container_margin_v = AppStyles.get_spacing(1)  # 8px vertical
        container_layout.setContentsMargins(container_margin_h, container_margin_v, container_margin_h, container_margin_v)
        container_layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid
        container_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment for all items
        
        # LEFT: Records info - ensure full text display
        self.records_label = QLabel()
        self.records_label.setObjectName("recordsInfoLabel")
        self.records_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.records_label.setMinimumWidth(150)  # Ensure enough width for full text
        self.records_label.setFixedHeight(36)  # Fixed height for consistent alignment
        container_layout.addWidget(self.records_label, alignment=Qt.AlignVCenter)
        
        container_layout.addStretch()
        
        # CENTER: Navigation controls
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid spacing
        nav_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        
        # First page button
        self.btn_first = CircularNavButton("btn_page_first", "")
        self.btn_first.setFixedSize(BTN_SIZE, BTN_SIZE)
        self.btn_first.clicked.connect(self.go_to_first)
        nav_layout.addWidget(self.btn_first, alignment=Qt.AlignVCenter)
        
        # Previous button
        self.btn_prev = CircularNavButton("btn_page_prev", "")
        self.btn_prev.setFixedSize(BTN_SIZE, BTN_SIZE)
        self.btn_prev.clicked.connect(self.go_to_previous)
        nav_layout.addWidget(self.btn_prev, alignment=Qt.AlignVCenter)
        
        # Page indicator - ensure full text display
        self.page_indicator = PageIndicatorLabel()
        self.page_indicator.setFixedHeight(INDICATOR_HEIGHT)
        self.page_indicator.setMinimumWidth(150)  # Wider to show "Page X of Y" fully
        nav_layout.addWidget(self.page_indicator, alignment=Qt.AlignVCenter)
        
        # Next button
        self.btn_next = CircularNavButton("btn_page_next", "")
        self.btn_next.setFixedSize(BTN_SIZE, BTN_SIZE)
        self.btn_next.clicked.connect(self.go_to_next)
        nav_layout.addWidget(self.btn_next, alignment=Qt.AlignVCenter)
        
        # Last page button
        self.btn_last = CircularNavButton("btn_page_last", "")
        self.btn_last.setFixedSize(BTN_SIZE, BTN_SIZE)
        self.btn_last.clicked.connect(self.go_to_last)
        nav_layout.addWidget(self.btn_last, alignment=Qt.AlignVCenter)
        
        container_layout.addLayout(nav_layout)
        
        container_layout.addStretch()
        
        # RIGHT: Page size selector
        right_section = QHBoxLayout()
        right_section.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid spacing
        right_section.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        
        # Page input spinbox
        self.page_spin = ModernPageSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setMaximum(1)
        self.page_spin.setFixedSize(SPIN_WIDTH, BTN_SIZE)
        self.page_spin.valueChanged.connect(self.on_page_changed)
        right_section.addWidget(self.page_spin, alignment=Qt.AlignVCenter)
        
        # Items per page label - ensure full text display
        self.items_per_page_label = QLabel()
        self.items_per_page_label.setObjectName("itemsPerPageLabel")
        self.items_per_page_label.setMinimumWidth(100)  # Ensure enough width for translated text
        self.items_per_page_label.setFixedHeight(BTN_SIZE)  # Fixed height for consistent alignment
        right_section.addWidget(self.items_per_page_label, alignment=Qt.AlignVCenter)
        
        # Page size combo
        self.page_size_combo = ModernPageSizeCombo()
        self.page_size_combo.addItems(['25', '50', '100', '200', '500'])
        self.page_size_combo.setCurrentText(str(self.page_size))
        self.page_size_combo.setFixedSize(COMBO_WIDTH, BTN_SIZE)
        self.page_size_combo.currentTextChanged.connect(self.on_page_size_changed)
        right_section.addWidget(self.page_size_combo, alignment=Qt.AlignVCenter)
        
        container_layout.addLayout(right_section)
        
        main_layout.addWidget(container)
        
        # Apply modern stylesheet
        self._apply_stylesheet()
        
        # Enable keyboard focus for Page Up/Down
        self.setFocusPolicy(Qt.StrongFocus)
    
    def keyPressEvent(self, event):
        """Handle Page Up/Down for keyboard navigation"""
        if event.key() == Qt.Key_PageUp:
            self.go_to_previous()
            event.accept()
        elif event.key() == Qt.Key_PageDown:
            self.go_to_next()
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def _apply_stylesheet(self):
        """Apply modern CSS styling"""
        self.setStyleSheet(AppStyles.get_premium_pagination_style())
    
    def set_total_items(self, total: int):
        """Set total number of items"""
        self.total_items = total
        self.calculate_pages()
        self.update_display()
    
    def set_page_size(self, size: int):
        """Set page size"""
        self.page_size = size
        self.page_size_combo.setCurrentText(str(size))
        self.calculate_pages()
        self.update_display()
    
    def calculate_pages(self):
        """Calculate total pages"""
        if self.page_size > 0:
            self.total_pages = max(1, (self.total_items + self.page_size - 1) // self.page_size)
        else:
            self.total_pages = 1
        
        # Ensure current page is valid
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        if self.current_page < 1:
            self.current_page = 1
        
        self.page_spin.setMaximum(self.total_pages)
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(self.current_page)
        self.page_spin.blockSignals(False)
    
    def update_display(self):
        """Update pagination display with translations"""
        # Get translated strings
        page_text = self.translator.tr('pagination_page') if hasattr(self.translator, 'tr') else 'Page'
        of_text = self.translator.tr('pagination_of') if hasattr(self.translator, 'tr') else 'of'
        showing_text = self.translator.tr('pagination_showing') if hasattr(self.translator, 'tr') else 'Showing'
        items_per_page_text = self.translator.tr('pagination_items_per_page') if hasattr(self.translator, 'tr') else 'Items per page'
        
        # Update page indicator
        self.page_indicator.setText(f"{page_text} {self.current_page} {of_text} {self.total_pages}")
        
        # Update items per page label
        self.items_per_page_label.setText(items_per_page_text)
        
        # Update records info with range
        start = (self.current_page - 1) * self.page_size + 1 if self.total_items > 0 else 0
        end = min(self.current_page * self.page_size, self.total_items)
        
        if self.total_items == 0:
            self.records_label.setText(f"{showing_text} 0–0 {of_text} 0")
        else:
            self.records_label.setText(f"{showing_text} {start}–{end} {of_text} {self.total_items}")
        
        # Update button states
        self.btn_first.setEnabled(self.current_page > 1)
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < self.total_pages)
        self.btn_last.setEnabled(self.current_page < self.total_pages)
        
        # Update tooltips with translations
        first_tip = self.translator.tr('pagination_first') if hasattr(self.translator, 'tr') else 'First Page'
        prev_tip = self.translator.tr('pagination_previous') if hasattr(self.translator, 'tr') else 'Previous Page'
        next_tip = self.translator.tr('pagination_next') if hasattr(self.translator, 'tr') else 'Next Page'
        last_tip = self.translator.tr('pagination_last') if hasattr(self.translator, 'tr') else 'Last Page'
        
        self.btn_first.setToolTip(first_tip)
        self.btn_prev.setToolTip(prev_tip)
        self.btn_next.setToolTip(next_tip)
        self.btn_last.setToolTip(last_tip)
    
    def go_to_first(self):
        """Go to first page"""
        if self.current_page != 1:
            self.current_page = 1
            self.page_spin.blockSignals(True)
            self.page_spin.setValue(1)
            self.page_spin.blockSignals(False)
            self.page_changed.emit(1)
            self.update_display()
    
    def go_to_previous(self):
        """Go to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            self.page_spin.blockSignals(True)
            self.page_spin.setValue(self.current_page)
            self.page_spin.blockSignals(False)
            self.page_changed.emit(self.current_page)
            self.update_display()
    
    def go_to_next(self):
        """Go to next page"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.page_spin.blockSignals(True)
            self.page_spin.setValue(self.current_page)
            self.page_spin.blockSignals(False)
            self.page_changed.emit(self.current_page)
            self.update_display()
    
    def go_to_last(self):
        """Go to last page"""
        if self.current_page != self.total_pages:
            self.current_page = self.total_pages
            self.page_spin.blockSignals(True)
            self.page_spin.setValue(self.current_page)
            self.page_spin.blockSignals(False)
            self.page_changed.emit(self.current_page)
            self.update_display()
    
    def on_page_changed(self, page: int):
        """Handle page number change"""
        if page != self.current_page and 1 <= page <= self.total_pages:
            self.current_page = page
            self.page_changed.emit(page)
            self.update_display()
    
    def on_page_size_changed(self, size_str: str):
        """Handle page size change"""
        try:
            new_size = int(size_str)
            if new_size != self.page_size:
                self.page_size = new_size
                self.calculate_pages()
                self.page_size_changed.emit(new_size)
                self.update_display()
        except ValueError:
            pass
    
    def get_current_page(self) -> int:
        """Get current page number"""
        return self.current_page
    
    def get_page_size(self) -> int:
        """Get page size"""
        return self.page_size
    
    def get_page_range(self) -> tuple:
        """Get start and end indices for current page"""
        start = (self.current_page - 1) * self.page_size
        end = min(start + self.page_size, self.total_items)
        return (start, end)
    
    def refresh_translations(self):
        """Refresh all translations when language changes"""
        # Apply RTL/LTR direction based on current language
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)
        
        # Apply to all child widgets
        for child in self.findChildren(QWidget):
            child.setLayoutDirection(direction)
        
        self.update_display()
