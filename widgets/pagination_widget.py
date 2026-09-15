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
        self.setAccessibleName(tooltip_text or icon_name.replace('_', ' ').title())
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

    def set_icon_name(self, icon_name: str):
        """Change the directional icon while retaining the button action."""
        self.icon_name = icon_name
        self._setup_icon()


class PageIndicatorLabel(QLabel):
    """Compact page indicator that supplements the numbered page buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pageIndicatorButton")
        self.setAlignment(Qt.AlignCenter)
        self.setAccessibleName("Current page")


class PageNumberButton(QPushButton):
    """Keyboard-accessible page button used in the adaptive page sequence."""

    def __init__(self, page: int, parent=None):
        super().__init__(str(page), parent)
        self.page = page
        self.setObjectName("pageNumberButton")
        self.setCheckable(True)
        self.setFixedSize(36, 36)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAccessibleName(f"Page {page}")
        self.setFocusPolicy(Qt.StrongFocus)


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
        try:
            from config.config_manager import ConfigManager
            configured_size = int(ConfigManager().get('Application', 'page_size', 50))
            if configured_size in {25, 50, 100, 200, 500}:
                self.page_size = configured_size
        except (TypeError, ValueError, OSError):
            pass
        self.total_items = 0
        # Keep a single disabled page visible for the empty state; the range
        # remains the authoritative "Showing 0–0 of 0" count.
        self.total_pages = 1
        
        # Apply RTL/LTR direction based on current language
        self.is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if self.is_rtl else Qt.LeftToRight
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
        self.records_label.setAccessibleName("Result range")
        self.records_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.records_label.setMinimumWidth(150)  # Ensure enough width for full text
        self.records_label.setFixedHeight(36)  # Fixed height for consistent alignment
        container_layout.addWidget(self.records_label, alignment=Qt.AlignVCenter)
        
        container_layout.addStretch()
        
        # CENTER: semantic navigation plus an adaptive page-number sequence
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(AppStyles.get_spacing(1))
        nav_layout.setAlignment(Qt.AlignVCenter)

        # Directional icons follow the semantic action in both LTR and RTL.
        first_icon = 'btn_page_last' if self.is_rtl else 'btn_page_first'
        previous_icon = 'btn_page_next' if self.is_rtl else 'btn_page_prev'
        next_icon = 'btn_page_prev' if self.is_rtl else 'btn_page_next'
        last_icon = 'btn_page_first' if self.is_rtl else 'btn_page_last'

        self.btn_first = CircularNavButton(first_icon)
        self.btn_first.setFixedSize(BTN_SIZE, BTN_SIZE)
        self.btn_first.clicked.connect(self.go_to_first)
        nav_layout.addWidget(self.btn_first, alignment=Qt.AlignVCenter)

        self.btn_prev = CircularNavButton(previous_icon)
        self.btn_prev.setFixedSize(BTN_SIZE, BTN_SIZE)
        self.btn_prev.clicked.connect(self.go_to_previous)
        nav_layout.addWidget(self.btn_prev, alignment=Qt.AlignVCenter)

        self.page_numbers_layout = QHBoxLayout()
        self.page_numbers_layout.setSpacing(4)
        self.page_numbers_layout.setContentsMargins(0, 0, 0, 0)
        self.page_number_buttons = []
        nav_layout.addLayout(self.page_numbers_layout)

        self.page_indicator = PageIndicatorLabel()
        self.page_indicator.setFixedHeight(INDICATOR_HEIGHT)
        self.page_indicator.setMinimumWidth(82)
        self.page_indicator.setMaximumWidth(110)
        self.page_indicator.setToolTip("Current page")
        nav_layout.addWidget(self.page_indicator, alignment=Qt.AlignVCenter)

        self.btn_next = CircularNavButton(next_icon)
        self.btn_next.setFixedSize(BTN_SIZE, BTN_SIZE)
        self.btn_next.clicked.connect(self.go_to_next)
        nav_layout.addWidget(self.btn_next, alignment=Qt.AlignVCenter)

        self.btn_last = CircularNavButton(last_icon)
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
        self.page_spin.setAccessibleName("Page number")
        self.page_spin.setToolTip("Enter page number")
        self.page_spin.setFixedSize(SPIN_WIDTH, BTN_SIZE)
        self.page_spin.valueChanged.connect(self.on_page_changed)
        right_section.addWidget(self.page_spin, alignment=Qt.AlignVCenter)
        
        # Items per page label - ensure full text display
        self.items_per_page_label = QLabel()
        self.items_per_page_label.setObjectName("itemsPerPageLabel")
        self.items_per_page_label.setAccessibleName("Rows per page")
        self.items_per_page_label.setMinimumWidth(100)  # Ensure enough width for translated text
        self.items_per_page_label.setFixedHeight(BTN_SIZE)  # Fixed height for consistent alignment
        right_section.addWidget(self.items_per_page_label, alignment=Qt.AlignVCenter)
        
        # Page size combo
        self.page_size_combo = ModernPageSizeCombo()
        self.page_size_combo.addItems(['25', '50', '100', '200', '500'])
        self.page_size_combo.setCurrentText(str(self.page_size))
        self.page_size_combo.setAccessibleName("Rows per page")
        self.page_size_combo.setToolTip("Rows per page")
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
    
    @staticmethod
    def _build_page_sequence(total_pages: int, current_page: int):
        """Return visible page numbers and ellipsis markers for a large result set."""
        total_pages = max(1, total_pages)
        current_page = max(1, min(current_page, total_pages))
        if total_pages <= 7:
            return list(range(1, total_pages + 1))
        if current_page <= 4:
            return [1, 2, 3, 4, 5, 'ellipsis', total_pages]
        if current_page >= total_pages - 3:
            return [1, 'ellipsis', total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
        return [1, 'ellipsis', current_page - 1, current_page, current_page + 1, 'ellipsis', total_pages]

    def _rebuild_page_buttons(self):
        """Render the adaptive sequence without changing the navigation API."""
        while self.page_numbers_layout.count():
            item = self.page_numbers_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.page_number_buttons = []

        page_label = self.translator.tr('pagination_page', default='Page')
        current_label = self.translator.tr('pagination_current_page', default='Current page')
        for value in self._build_page_sequence(self.total_pages, self.current_page):
            if value == 'ellipsis':
                ellipsis = QLabel('…')
                ellipsis.setObjectName('pageEllipsis')
                ellipsis.setAlignment(Qt.AlignCenter)
                ellipsis.setFixedSize(20, 36)
                ellipsis.setAccessibleName('Additional pages')
                self.page_numbers_layout.addWidget(ellipsis, alignment=Qt.AlignVCenter)
                continue
            button = PageNumberButton(value)
            button.setChecked(value == self.current_page)
            if value == self.current_page:
                button.setAccessibleName(f'{page_label} {value}, {current_label}')
            else:
                button.setAccessibleName(f'{page_label} {value}')
            button.clicked.connect(lambda checked=False, page=value: self.go_to_page(page))
            self.page_numbers_layout.addWidget(button, alignment=Qt.AlignVCenter)
            self.page_number_buttons.append(button)

    def go_to_page(self, page: int):
        """Navigate directly to a visible page-number button."""
        if 1 <= page <= self.total_pages and page != self.current_page:
            self.current_page = page
            self.page_spin.blockSignals(True)
            self.page_spin.setValue(page)
            self.page_spin.blockSignals(False)
            self.page_changed.emit(page)
            self.update_display()

    def update_display(self):
        """Update pagination display with translations"""
        # Get translated strings
        page_text = self.translator.tr('pagination_page') if hasattr(self.translator, 'tr') else 'Page'
        of_text = self.translator.tr('pagination_of') if hasattr(self.translator, 'tr') else 'of'
        showing_text = self.translator.tr('pagination_showing') if hasattr(self.translator, 'tr') else 'Showing'
        items_per_page_text = self.translator.tr('pagination_items_per_page') if hasattr(self.translator, 'tr') else 'Rows per page'
        page_number_text = self.translator.tr('pagination_page_number', default='Page number') if hasattr(self.translator, 'tr') else 'Page number'
        
        # Update the adaptive page-number sequence and current-page indicator.
        self._rebuild_page_buttons()
        self.page_indicator.setText(f"{page_text} {self.current_page} {of_text} {self.total_pages}")
        self.page_indicator.setAccessibleName(
            f"{self.translator.tr('pagination_current_page', default='Current page')} "
            f"{self.current_page} {of_text} {self.total_pages}"
        )
        
        # Update items per page label and semantic names after a language change.
        self.items_per_page_label.setText(items_per_page_text)
        self.items_per_page_label.setAccessibleName(items_per_page_text)
        self.page_size_combo.setAccessibleName(items_per_page_text)
        self.page_size_combo.setToolTip(items_per_page_text)
        self.page_spin.setAccessibleName(page_number_text)
        self.page_spin.setToolTip(page_number_text)
        self.records_label.setAccessibleName(showing_text)
        
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
        
        for button, label in (
            (self.btn_first, first_tip),
            (self.btn_prev, prev_tip),
            (self.btn_next, next_tip),
            (self.btn_last, last_tip),
        ):
            button.setToolTip(label)
            button.setAccessibleName(label)
    
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
                # A new page size changes the result boundaries; restart at
                # page one so the range and table rows remain predictable.
                self.current_page = 1
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
        self.is_rtl = is_rtl
        self.btn_first.set_icon_name('btn_page_last' if is_rtl else 'btn_page_first')
        self.btn_prev.set_icon_name('btn_page_next' if is_rtl else 'btn_page_prev')
        self.btn_next.set_icon_name('btn_page_prev' if is_rtl else 'btn_page_next')
        self.btn_last.set_icon_name('btn_page_first' if is_rtl else 'btn_page_last')
        
        # Apply to all child widgets
        for child in self.findChildren(QWidget):
            child.setLayoutDirection(direction)
        
        self.update_display()
