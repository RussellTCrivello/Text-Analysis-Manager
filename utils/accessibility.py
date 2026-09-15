"""
Accessibility Utilities
Provides keyboard navigation, screen reader support, and other accessibility features
"""
from typing import Dict, List, Optional, Callable
from PyQt5.QtWidgets import (
    QWidget, QApplication, QShortcut, QToolTip, QLabel,
    QMainWindow, QPushButton, QLineEdit, QTableWidget,
    QDialog, QMessageBox, QAction
)
from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QScrollArea, QTextEdit
from PyQt5.QtGui import QKeySequence, QPalette, QColor

from config.config_manager import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)


class KeyboardShortcut:
    """Represents a keyboard shortcut"""
    
    def __init__(self, key_sequence: str, action: str, 
                 description: str, callback: Optional[Callable] = None):
        self.key_sequence = key_sequence
        self.action = action
        self.description = description
        self.callback = callback


class AccessibilityManager(QObject):
    """Manages accessibility features for the application"""
    
    _instance: Optional['AccessibilityManager'] = None
    
    # Global keyboard shortcuts
    GLOBAL_SHORTCUTS: List[KeyboardShortcut] = [
        KeyboardShortcut("F1", "help", "Open Help"),
        KeyboardShortcut("Ctrl+Q", "quit", "Quit Application"),
        KeyboardShortcut("Ctrl+S", "save", "Save"),
        KeyboardShortcut("Ctrl+N", "new", "New Record"),
        KeyboardShortcut("Ctrl+E", "edit", "Edit Selected"),
        KeyboardShortcut("Ctrl+D", "delete", "Delete Selected"),
        KeyboardShortcut("Ctrl+F", "search", "Focus Search"),
        KeyboardShortcut("Ctrl+R", "refresh", "Refresh Data"),
        KeyboardShortcut("Ctrl+P", "print", "Print"),
        KeyboardShortcut("Ctrl+1", "tab_sources", "Go to Sources Tab"),
        KeyboardShortcut("Ctrl+2", "tab_contents", "Go to Contents Tab"),
        KeyboardShortcut("Ctrl+3", "tab_analysis", "Go to Analysis Tab"),
        KeyboardShortcut("Ctrl+4", "tab_all_data", "Go to All Data Tab"),
        KeyboardShortcut("Ctrl+5", "tab_timeline", "Go to Timeline Tab"),
        KeyboardShortcut("Ctrl+6", "tab_reports", "Go to Reports Tab"),
        KeyboardShortcut("Escape", "close_dialog", "Close Dialog / Cancel"),
        KeyboardShortcut("Enter", "confirm", "Confirm / OK"),
        KeyboardShortcut("Tab", "next_field", "Next Field"),
        KeyboardShortcut("Shift+Tab", "prev_field", "Previous Field"),
        KeyboardShortcut("Ctrl+Home", "first_record", "Go to First Record"),
        KeyboardShortcut("Ctrl+End", "last_record", "Go to Last Record"),
        KeyboardShortcut("Page Up", "prev_page", "Previous Page"),
        KeyboardShortcut("Page Down", "next_page", "Next Page"),
    ]
    
    # Table navigation shortcuts
    TABLE_SHORTCUTS: List[KeyboardShortcut] = [
        KeyboardShortcut("Up", "prev_row", "Previous Row"),
        KeyboardShortcut("Down", "next_row", "Next Row"),
        KeyboardShortcut("Home", "first_row", "First Row"),
        KeyboardShortcut("End", "last_row", "Last Row"),
        KeyboardShortcut("Space", "select", "Select Row"),
        KeyboardShortcut("Enter", "open", "Open/Edit Row"),
    ]
    
    def __new__(cls, parent=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, parent=None):
        if self._initialized:
            return
        super().__init__(parent)
        self._initialized = True
        
        self.config = ConfigManager()
        self._shortcuts: Dict[str, QShortcut] = {}
        self._registered_widgets: List[QWidget] = []
        
        # Load accessibility settings
        self.keyboard_hints_enabled = self.config.get('Accessibility', 'keyboard_navigation', True)
        self.screen_reader_enabled = self.config.get('Accessibility', 'screen_reader_support', True)
        self.high_contrast_enabled = self.config.get('Accessibility', 'high_contrast', False)
        self.focus_indicator_enabled = self.config.get('Accessibility', 'focus_indicator', True)
    
    def setup_for_window(self, window: QMainWindow, shortcuts_config: Dict[str, Callable] = None):
        """Setup accessibility features for a main window"""
        if shortcuts_config:
            for action, callback in shortcuts_config.items():
                shortcut = next((s for s in self.GLOBAL_SHORTCUTS if s.action == action), None)
                if shortcut:
                    self.register_shortcut(window, shortcut.key_sequence, callback, shortcut.description)
        
        # Apply high contrast if enabled
        if self.high_contrast_enabled:
            self.apply_high_contrast(window)
        
        # Setup focus tracking
        if self.focus_indicator_enabled:
            self._setup_focus_tracking(window)
        
        self._registered_widgets.append(window)
    
    def register_shortcut(self, widget: QWidget, key_sequence: str, 
                         callback: Callable, description: str = ""):
        """Register a keyboard shortcut"""
        try:
            shortcut = QShortcut(QKeySequence(key_sequence), widget)
            shortcut.activated.connect(callback)
            
            # Store for later reference
            key = f"{id(widget)}_{key_sequence}"
            self._shortcuts[key] = shortcut
            
            # Set tooltip if widget supports it
            if hasattr(widget, 'setStatusTip'):
                current_tip = widget.statusTip() or ""
                if key_sequence not in current_tip:
                    widget.setStatusTip(f"{current_tip} ({key_sequence})" if current_tip else key_sequence)
            
            logger.debug(f"Registered shortcut: {key_sequence} -> {description}")
        except Exception as e:
            logger.error(f"Error registering shortcut {key_sequence}: {e}")
    
    def _setup_focus_tracking(self, window: QWidget):
        """Setup focus tracking for accessibility"""
        app = QApplication.instance()
        if app:
            app.focusChanged.connect(self._on_focus_changed)
    
    def _on_focus_changed(self, old: QWidget, new: QWidget):
        """Handle focus change for accessibility"""
        if not new:
            return
        
        # Announce focus change for screen readers
        if self.screen_reader_enabled:
            widget_info = self._get_widget_info(new)
            if widget_info:
                # QAccessible announcement would go here
                logger.debug(f"Focus changed to: {widget_info}")
        
        # Visual focus indicator
        if self.focus_indicator_enabled and new:
            self._apply_focus_style(old, new)
    
    def _get_widget_info(self, widget: QWidget) -> str:
        """Get accessible information about a widget"""
        if not widget:
            return ""
        
        info_parts = []
        
        # Widget type
        widget_type = type(widget).__name__
        info_parts.append(widget_type)
        
        # Accessible name
        if hasattr(widget, 'accessibleName') and widget.accessibleName():
            info_parts.append(widget.accessibleName())
        elif hasattr(widget, 'text'):
            text = widget.text() if callable(widget.text) else str(widget.text)
            if text:
                info_parts.append(text[:50])
        
        # Tool tip
        if hasattr(widget, 'toolTip') and widget.toolTip():
            info_parts.append(f"Hint: {widget.toolTip()}")
        
        return " - ".join(info_parts)
    
    def _apply_focus_style(self, old: QWidget, new: QWidget):
        """Apply visual focus indicator"""
        # Remove focus style from old widget
        if old and hasattr(old, 'setProperty'):
            old.setProperty('focused', False)
            old.style().unpolish(old)
            old.style().polish(old)
        
        # Add focus style to new widget  
        if new and hasattr(new, 'setProperty'):
            new.setProperty('focused', True)
            new.style().unpolish(new)
            new.style().polish(new)
    
    def apply_high_contrast(self, widget: QWidget):
        """Apply high contrast styling"""
        high_contrast_style = """
            QWidget {
                background-color: #000000;
                color: #FFFFFF;
            }
            QWidget:focus {
                border: 3px solid #FFFF00;
            }
            QPushButton {
                background-color: #000080;
                color: #FFFFFF;
                border: 2px solid #FFFFFF;
            }
            QPushButton:hover {
                background-color: #0000FF;
            }
            QPushButton:focus {
                border: 3px solid #FFFF00;
            }
            QLineEdit, QTextEdit {
                background-color: #000000;
                color: #FFFFFF;
                border: 2px solid #FFFFFF;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 3px solid #FFFF00;
            }
            QTableWidget {
                background-color: #000000;
                color: #FFFFFF;
                gridline-color: #FFFFFF;
            }
            QTableWidget::item:selected {
                background-color: #000080;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #000080;
                color: #FFFFFF;
                border: 1px solid #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
            }
            QComboBox {
                background-color: #000000;
                color: #FFFFFF;
                border: 2px solid #FFFFFF;
            }
            QMenu {
                background-color: #000000;
                color: #FFFFFF;
                border: 2px solid #FFFFFF;
            }
            QMenu::item:selected {
                background-color: #000080;
            }
        """
        
        if self.high_contrast_enabled:
            widget.setStyleSheet(widget.styleSheet() + high_contrast_style)
    
    def get_shortcuts_help(self, translator=None) -> str:
        """Get formatted keyboard shortcuts help text, with optional translation"""
        def tr_desc(action_key: str, default: str) -> str:
            if translator and hasattr(translator, 'tr'):
                key = f'shortcut_help_{action_key}'
                result = translator.tr(key)
                return result if result != key else default
            return default
        
        help_text = "<h3>Keyboard Shortcuts</h3>\n"
        help_text += "<table border='1' cellpadding='5'>\n"
        help_text += "<tr><th>Shortcut</th><th>Action</th></tr>\n"
        
        for shortcut in self.GLOBAL_SHORTCUTS:
            desc = tr_desc(shortcut.action, shortcut.description)
            help_text += f"<tr><td><b>{shortcut.key_sequence}</b></td>"
            help_text += f"<td>{desc}</td></tr>\n"
        
        help_text += "</table>\n"
        
        help_text += "\n<h4>Table Navigation</h4>\n"
        help_text += "<table border='1' cellpadding='5'>\n"
        help_text += "<tr><th>Shortcut</th><th>Action</th></tr>\n"
        
        for shortcut in self.TABLE_SHORTCUTS:
            desc = tr_desc(shortcut.action, shortcut.description)
            help_text += f"<tr><td><b>{shortcut.key_sequence}</b></td>"
            help_text += f"<td>{desc}</td></tr>\n"
        
        help_text += "</table>"
        
        return help_text
    
    def show_keyboard_shortcuts_dialog(self, parent: QWidget, translator=None):
        """Show a dialog with keyboard shortcuts"""
        from PyQt5.QtWidgets import QVBoxLayout, QTextEdit, QDialogButtonBox, QScrollArea
        from styles.styles import AppStyles
        
        dialog = QDialog(parent)
        dialog.setWindowTitle(translator.tr('help_shortcuts') if translator else "Keyboard Shortcuts")
        
        # Make dialog resizable with good minimum size
        dialog.setMinimumSize(500, 400)
        dialog.resize(600, 500)
        
        # Apply RTL if Arabic
        if translator and translator.current_language == 'ar':
            dialog.setLayoutDirection(Qt.RightToLeft)
        
        layout = QVBoxLayout(dialog)
        # Use 8px grid spacing
        dialog_margin = AppStyles.get_spacing(2)  # 16px (rounding 15px to 16px)
        dialog_spacing = AppStyles.get_spacing(2)  # 16px (rounding 10px to 16px)
        layout.setContentsMargins(dialog_margin, dialog_margin, dialog_margin, dialog_margin)
        layout.setSpacing(dialog_spacing)
        
        # Scrollable text area for shortcuts
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(self.get_shortcuts_help(translator))
        text_edit.setMinimumHeight(300)
        layout.addWidget(text_edit)
        
        # OK button
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        # Disable autoDefault
        for button in button_box.buttons():
            button.setAutoDefault(False)
            button.setDefault(False)
        layout.addWidget(button_box)
        
        dialog.exec_()
    
    def set_accessible_name(self, widget: QWidget, name: str):
        """Set accessible name for a widget"""
        if hasattr(widget, 'setAccessibleName'):
            widget.setAccessibleName(name)
    
    def set_accessible_description(self, widget: QWidget, description: str):
        """Set accessible description for a widget"""
        if hasattr(widget, 'setAccessibleDescription'):
            widget.setAccessibleDescription(description)
        if hasattr(widget, 'setToolTip'):
            widget.setToolTip(description)
    
    def make_table_accessible(self, table: QTableWidget, translator=None):
        """Make a table widget more accessible"""
        # Set keyboard focus policy
        table.setFocusPolicy(Qt.StrongFocus)
        
        # Enable tab navigation between cells
        table.setTabKeyNavigation(True)
        
        # Set selection behavior
        table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Setup accessible labels for columns
        header = table.horizontalHeader()
        for i in range(table.columnCount()):
            header_item = table.horizontalHeaderItem(i)
            if header_item:
                # Store column name for screen reader
                header_item.setData(Qt.AccessibleTextRole, header_item.text())
    
    def update_settings(self):
        """Reload settings from config"""
        self.keyboard_hints_enabled = self.config.get('Accessibility', 'keyboard_navigation', True)
        self.screen_reader_enabled = self.config.get('Accessibility', 'screen_reader_support', True)
        self.high_contrast_enabled = self.config.get('Accessibility', 'high_contrast', False)
        self.focus_indicator_enabled = self.config.get('Accessibility', 'focus_indicator', True)


# Global instance
_accessibility_manager: Optional[AccessibilityManager] = None


def get_accessibility_manager() -> AccessibilityManager:
    """Get the global accessibility manager instance"""
    global _accessibility_manager
    if _accessibility_manager is None:
        _accessibility_manager = AccessibilityManager()
    return _accessibility_manager


def setup_widget_accessibility(widget: QWidget, name: str = None, 
                               description: str = None):
    """Convenience function to setup accessibility for a widget"""
    manager = get_accessibility_manager()
    
    if name:
        manager.set_accessible_name(widget, name)
    if description:
        manager.set_accessible_description(widget, description)


def add_keyboard_hint(button: QPushButton, shortcut: str):
    """Add keyboard shortcut hint to a button"""
    current_text = button.text()
    if shortcut not in current_text:
        button.setToolTip(f"{button.toolTip()} [{shortcut}]" if button.toolTip() else f"[{shortcut}]")


class ResizableMessageBox(QMessageBox):
    """
    A QMessageBox subclass that allows resizing and has better default sizes.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizeGripEnabled(True)
    
    def event(self, event: QEvent) -> bool:
        result = super().event(event)
        
        # After the dialog is shown, adjust its size
        if event.type() == QEvent.Show:
            # Set minimum size to ensure content is readable
            self.setMinimumWidth(400)
            self.setMinimumHeight(150)
            
            # Get the text label and make it wider
            for child in self.findChildren(QLabel):
                if child.text():
                    child.setMinimumWidth(300)
                    child.setWordWrap(True)
        
        return result
    
    @staticmethod
    def information(parent, title: str, text: str, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
        """Show an information message box"""
        msg = ResizableMessageBox(parent)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(buttons)
        if defaultButton != QMessageBox.NoButton:
            msg.setDefaultButton(defaultButton)
        return msg.exec_()
    
    @staticmethod
    def warning(parent, title: str, text: str, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
        """Show a warning message box"""
        msg = ResizableMessageBox(parent)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(buttons)
        if defaultButton != QMessageBox.NoButton:
            msg.setDefaultButton(defaultButton)
        return msg.exec_()
    
    @staticmethod
    def critical(parent, title: str, text: str, buttons=QMessageBox.Ok, defaultButton=QMessageBox.NoButton):
        """Show a critical/error message box"""
        msg = ResizableMessageBox(parent)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(buttons)
        if defaultButton != QMessageBox.NoButton:
            msg.setDefaultButton(defaultButton)
        return msg.exec_()
    
    @staticmethod
    def question(parent, title: str, text: str, buttons=QMessageBox.Yes | QMessageBox.No, defaultButton=QMessageBox.No):
        """Show a question message box"""
        msg = ResizableMessageBox(parent)
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(buttons)
        if defaultButton != QMessageBox.NoButton:
            msg.setDefaultButton(defaultButton)
        return msg.exec_()
