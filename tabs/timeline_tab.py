"""
Timeline Tab - Chronological view of events and news
"""
from typing import List, Dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from widgets.timeline_widget import TimelineWidget
from widgets.text_preview_panel import TextPreviewPanel
from db.db_manager import DatabaseManager
from translations.translations import TranslationManager
from styles.styles import AppStyles
from utils.logger import get_logger

logger = get_logger(__name__)


class TimelineTab(QWidget):
    """
    Timeline tab displaying chronological events and news
    """
    
    PAGE_TITLE = "tab_timeline"
    
    def __init__(self, parent, translator: TranslationManager):
        super().__init__(parent)
        self.translator = translator
        self._data_loaded = False
        
        # Apply RTL/LTR layout direction
        self._apply_layout_direction()
        
        self.setup_ui()
    
    def _apply_layout_direction(self):
        """Apply RTL/LTR layout direction based on current language"""
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)
        AppStyles.set_layout_direction('rtl' if is_rtl else 'ltr')
    
    def setup_ui(self):
        """Setup timeline tab UI with unified scrolling"""
        from PyQt5.QtWidgets import QScrollArea
        
        # Main layout (no margins - scroll area handles it)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create unified scroll area for entire interface
        self.unified_scroll = AppStyles.create_unified_scroll_area()
        
        # Content widget for scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        # Use 8px grid spacing system
        AppStyles.apply_layout_spacing(scroll_layout, margin_units=1, spacing_units=1)
        
        # Page title
        self.title_label = QLabel(self.translator.tr('tab_timeline'))
        self.title_label.setStyleSheet(AppStyles.get_component_style('page_title'))
        scroll_layout.addWidget(self.title_label)
        
        # Splitter for timeline and preview
        splitter = QSplitter(Qt.Horizontal)
        
        # Timeline widget (left/top) - remove internal scroll, use unified scroll
        # Pass internal_scroll_enabled=False to disable internal scroll
        self.timeline_widget = TimelineWidget(self.translator, self, internal_scroll_enabled=False)
        self.timeline_widget.event_selected.connect(self.on_event_selected)
        splitter.addWidget(self.timeline_widget)
        
        # Preview panel (right/bottom)
        self.preview_panel = TextPreviewPanel(self.translator)
        splitter.addWidget(self.preview_panel)
        
        # Set splitter proportions
        splitter.setSizes([600, 300])
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        scroll_layout.addWidget(splitter, 1)  # Stretch factor 1 to take available space
        
        # Status label
        self.status_label = QLabel(self.translator.tr('msg_ready'))
        self.status_label.setStyleSheet(AppStyles.get_component_style('status_label'))
        scroll_layout.addWidget(self.status_label)
        
        # Set scroll content
        self.unified_scroll.setWidget(scroll_content)
        
        # Add unified scroll to main layout
        layout.addWidget(self.unified_scroll)
    
    def load_data(self):
        """Load timeline data from database"""
        try:
            # Get all data with dates
            events = DatabaseManager.get_timeline_events()
            
            if not events:
                self.status_label.setText(
                    self.translator.tr('timeline_no_events')
                )
                self.timeline_widget.load_events([])
                self._data_loaded = True
                return
            
            # Load events into timeline widget
            self.timeline_widget.load_events(events)
            
            # Update status
            self.status_label.setText(
                self.translator.tr('timeline_loaded', count=len(events))
            )
            
            self._data_loaded = True
            
            # Force refresh to ensure all sections are visible
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.timeline_widget.refresh_display())
            
        except Exception as e:
            logger.error(f"Error loading timeline data: {e}")
            QMessageBox.critical(
                self,
                self.translator.tr('msg_error'),
                self.translator.tr('timeline_load_error', error=str(e))
            )
            self.status_label.setText(self.translator.tr('msg_error'))
    
    def on_event_selected(self, event_data: Dict):
        """Handle event selection"""
        # Update preview panel with event data
        self.preview_panel.update_preview(event_data)
    
    def refresh_translations(self):
        """Refresh translations when language changes"""
        # Apply layout direction
        self._apply_layout_direction()
        
        # Update title
        if hasattr(self, 'title_label'):
            self.title_label.setText(self.translator.tr('tab_timeline'))
        
        # Refresh timeline widget
        if hasattr(self, 'timeline_widget'):
            self.timeline_widget.refresh_translations()
        
        # Refresh preview panel
        if hasattr(self, 'preview_panel') and hasattr(self.preview_panel, 'refresh_translations'):
            self.preview_panel.refresh_translations()
        
        # Update status
        if hasattr(self, 'status_label'):
            self.status_label.setText(self.translator.tr('msg_ready'))
