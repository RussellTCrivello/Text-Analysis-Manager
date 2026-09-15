"""
All Data Display Tab - Unified view of all data (Read-Only)
Page-specific buttons: Filter by Type, Quick View, Generate Report
"""
from typing import List, Optional, Dict
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QFileDialog,
    QHeaderView, QDialog, QComboBox, QGroupBox, QSplitter,
    QMenu, QAction, QApplication, QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont

from core.toolbar_factory import ToolbarFactory, ToolbarConfig, ButtonConfig
from db.db_manager import DatabaseManager
from translations.translations import TranslationManager
from styles.styles import AppStyles
from icons.icon_manager import get_icon
from utils.logger import get_logger
from utils.export_safety import sanitize_row

logger = get_logger(__name__)


class AllDataDisplayTab(QWidget):
    """
    All Data unified view - Read-Only display of all tables combined.
    Supports responsive design and RTL/LTR layout directions.
    
    Dedicated Buttons (No CRUD - Read-Only):
    - Page-Specific: Filter by Type, Quick View, Generate Report
    - Export: Print, PDF, CSV, Excel, Word
    - Settings: Header Settings
    """
    
    PAGE_TITLE = "tab_all_data"
    
    def __init__(self, parent, translator: TranslationManager):
        super().__init__(parent)
        self.translator = translator
        self.toolbar_factory = ToolbarFactory(translator)
        self.data = []
        # Keep the complete filtered result separate from the current page so
        # exports, quick reports, and counts are not limited by pagination.
        self.filtered_data = []
        self.page_data = []
        self._select_first_after_render = False
        self.current_type_filter = 'all'
        self._sort_column = None
        self._sort_order = Qt.AscendingOrder
        
        # Apply RTL/LTR layout direction based on language
        self._apply_layout_direction()
        
        # Column mapping: database fields mapped to display columns
        # The unified query returns prefixed fields like 'content_title', 'source_importance', etc.
        self.columns = [
            ('record_type', translator.tr('lbl_record_type'), 100),
            ('source_name', translator.tr('lbl_source'), 180),
            ('content_title', translator.tr('lbl_title'), 200),
            ('content_data', translator.tr('lbl_content_data'), 300),
            ('classification', translator.tr('lbl_classification'), 130),
            ('content_importance', translator.tr('lbl_importance'), 100),
            ('date_content', translator.tr('lbl_date_content'), 150),
            ('content_date_creation', translator.tr('lbl_date_creation'), 150)
        ]
        
        self.setup_ui()
        self._data_loaded = False  # Track if data has been loaded
        # Defer data loading until window is shown to prevent UI flickering
        # Only load if parent window is visible, otherwise wait
        from PyQt5.QtCore import QTimer
        if parent and parent.isVisible():
            QTimer.singleShot(100, self._deferred_load_data)
        else:
            # Window not shown yet, will be loaded when tab becomes visible
            pass
    
    def get_toolbar_config(self) -> ToolbarConfig:
        """Configure toolbar - Read-Only, no CRUD buttons"""
        return ToolbarConfig(
            show_crud=False,  # Read-only view
            show_add=False,
            show_edit=False,
            show_delete=False,
            show_refresh=True,
            show_export=True,
            show_export_unified=True,  # Unified export with preview dialog
            show_print=True,
            # Individual export buttons removed - use unified Export dialog
            show_pdf=False,
            show_csv=False,
            show_excel=False,
            show_word=False,
            show_search=True,
            show_date_filter=True,
            show_header_settings=True,  # Header settings for unified reports
            page_specific_buttons=[
                ButtonConfig(
                    key='column_visibility',
                    icon_key='btn_columns',
                    callback=self.toggle_column_visibility
                )
            ]
        )
    
    def get_callbacks(self) -> Dict[str, callable]:
        """Get callback functions for toolbar buttons"""
        return {
            'search': self.on_search,
            'date_filter_changed': self.on_filter_changed,
            'clear_dates': self.clear_date_filters,
            'refresh': self.load_data,
            'print': self.print_data,
            'export_pdf': self.export_pdf,
            'export_csv': self.export_csv,
            'export_excel': self.export_excel,
            'export_word': self.export_word,
            'export_unified': self.export_unified,
            'set_header': self.set_header,
        }
    
    def setup_ui(self):
        """Setup UI with toolbar and table - with unified scrolling"""
        from PyQt5.QtWidgets import QSizePolicy, QFrame
        
        # Main layout (no margins - scroll area handles it)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create unified scroll area for entire interface
        self.unified_scroll = AppStyles.create_unified_scroll_area()
        
        # Content widget for scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        # Use 8px grid spacing
        tab_margin = AppStyles.get_spacing(1)  # 8px
        tab_spacing = AppStyles.get_spacing(1)  # 8px
        scroll_layout.setContentsMargins(tab_margin, tab_margin, tab_margin, tab_margin)
        scroll_layout.setSpacing(tab_spacing)
        
        # Header with READ-ONLY indicator - fixed height
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel(self.translator.tr('tab_all_data'))
        self.title_label.setStyleSheet(AppStyles.get_component_style('page_title'))
        header_layout.addWidget(self.title_label)
        
        # Read-only badge: graphical icon plus translatable text.
        readonly_container = QWidget()
        readonly_layout = QHBoxLayout(readonly_container)
        readonly_layout.setContentsMargins(0, 0, 0, 0)
        readonly_layout.setSpacing(AppStyles.get_spacing(1))
        self.readonly_icon = QLabel()
        self.readonly_icon.setPixmap(get_icon('preview', 16).pixmap(16, 16))
        self.readonly_icon.setToolTip(self.translator.tr('msg_readonly'))
        self.readonly_badge = QLabel(self.translator.tr('msg_readonly'))
        self.readonly_badge.setStyleSheet(AppStyles.get_component_style('readonly_badge'))
        readonly_layout.addWidget(self.readonly_icon)
        readonly_layout.addWidget(self.readonly_badge)
        header_layout.addWidget(readonly_container)
        header_layout.addStretch()
        
        scroll_layout.addLayout(header_layout, 0)  # stretch factor 0 = fixed
        
        # Toolbar from factory - fixed height
        config = self.get_toolbar_config()
        callbacks = self.get_callbacks()
        self.toolbar = self.toolbar_factory.create_toolbar(self, config, callbacks)
        self.toolbar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        scroll_layout.addWidget(self.toolbar, 0)  # stretch factor 0 = fixed
        
        # Type filter section (Page-Specific for All Data) - fixed height
        type_filter = self._create_type_filter()
        type_filter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        scroll_layout.addWidget(type_filter, 0)  # stretch factor 0 = fixed

        self.result_summary_label = QLabel()
        self.result_summary_label.setObjectName('tableResultSummary')
        self.result_summary_label.setStyleSheet(AppStyles.get_component_style('table_result_summary'))
        self.result_summary_label.setAccessibleName(self.translator.tr(
            'table_result_summary', default='Table result summary'
        ))
        scroll_layout.addWidget(self.result_summary_label, 0)
        
        # Container for table area
        table_container = QFrame()
        table_container.setFrameShape(QFrame.NoFrame)
        table_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        self.table_state_label = QLabel()
        self.table_state_label.setObjectName('tableStateLabel')
        self.table_state_label.setAlignment(Qt.AlignCenter)
        self.table_state_label.setWordWrap(True)
        self.table_state_label.setMinimumHeight(48)
        self.table_state_label.setStyleSheet(AppStyles.get_component_style('table_state'))
        self.table_state_label.setVisible(False)
        table_layout.addWidget(self.table_state_label, 0)
        
        # Splitter for table and preview
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Table with internal scrollbars for table data navigation
        self.data_table = self._create_table()
        # Enable internal scrollbars for table data
        self.data_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.data_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Apply timeline-style scrollbar styling
        self.data_table.setStyleSheet(AppStyles.get_table_scrollbar_style())
        self.splitter.addWidget(self.data_table)
        
        # Preview panel
        from widgets.text_preview_panel import TextPreviewPanel
        self.preview_panel = TextPreviewPanel(self.translator)
        self.preview_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.splitter.addWidget(self.preview_panel)
        
        # Set splitter proportions
        self.splitter.setSizes([400, 150])
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)
        
        table_layout.addWidget(self.splitter)
        
        # Add table container with stretch factor 1 (takes available space)
        scroll_layout.addWidget(table_container, 1)
        
        # Set scroll content (pagination stays OUTSIDE scroll so it's always visible)
        self.unified_scroll.setWidget(scroll_content)
        
        # Add unified scroll to main layout
        layout.addWidget(self.unified_scroll, 1)
        
        # Pagination widget - OUTSIDE scroll area, always visible at bottom
        from widgets.pagination_widget import PaginationWidget
        self.pagination = PaginationWidget(self.translator, self)
        self.pagination.page_changed.connect(self.on_page_changed)
        self.pagination.page_size_changed.connect(self.on_page_size_changed)
        self.pagination.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.pagination, 0)
        
        # Status bar - fixed at bottom, always visible
        self.status_label = QLabel(self.translator.tr('msg_ready'))
        self.status_label.setStyleSheet(AppStyles.get_component_style('status_label'))
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.status_label.setFixedHeight(25)
        layout.addWidget(self.status_label, 0)
        self._update_action_state()
        self._update_result_summary()
    
    def _create_type_filter(self) -> QWidget:
        """Create type filter section with dropdown - Page-Specific for All Data tab"""
        group = QGroupBox(self.translator.tr('lbl_filter_by_type'))
        self.type_filter_group = group  # Store reference for translation refresh
        group.setStyleSheet(AppStyles.get_component_style('type_filter_group'))
        
        layout = QHBoxLayout(group)
        # Use 8px grid spacing
        filter_margin_h = AppStyles.get_spacing(2)  # 16px horizontal
        filter_margin_v = AppStyles.get_spacing(1)  # 8px vertical
        filter_spacing = AppStyles.get_spacing(2)  # 16px
        layout.setContentsMargins(filter_margin_h, filter_margin_v, filter_margin_h, filter_margin_v)
        layout.setSpacing(filter_spacing)
        
        # Type filter label
        type_label = QLabel(self.translator.tr('lbl_record_type') + ":")
        type_label.setStyleSheet(AppStyles.get_component_style('type_label'))
        layout.addWidget(type_label)
        self.type_filter_label = type_label
        
        # Type filter dropdown (combobox)
        self.type_filter_combo = QComboBox()
        self.type_filter_combo.setMinimumWidth(180)
        
        # Define filter options with their internal keys
        # Format: (internal_key, display_text, icon_color)
        self.type_filter_options = [
            ('all', self.translator.tr('btn_all_types'), '#3498DB'),
            ('source', self.translator.tr('tab_sources'), '#27AE60'),
            ('content', self.translator.tr('tab_contents'), '#F39C12'),
            ('analysis', self.translator.tr('tab_analysis'), '#9B59B6'),
        ]
        
        # Populate combobox
        for key, display_text, color in self.type_filter_options:
            self.type_filter_combo.addItem(display_text, key)
        
        # Style the combobox
        self.type_filter_combo.setStyleSheet(AppStyles.get_component_style('type_filter_combo'))
        
        # Connect signal
        self.type_filter_combo.currentIndexChanged.connect(self._on_type_filter_changed)
        layout.addWidget(self.type_filter_combo)
        
        layout.addStretch()
        
        # Quick view is a frequent review action; report generation is the
        # higher-value labeled action for this read-only workspace.
        self.btn_quick_view = self.toolbar_factory._create_labeled_action_button(
            'btn_quick_view', 'btn_quick_view', self.translator.tr('btn_quick_view'),
            icon_only=False
        )
        self.btn_quick_view.clicked.connect(self.quick_view)
        layout.addWidget(self.btn_quick_view)

        self.btn_generate_report = self.toolbar_factory._create_labeled_action_button(
            'btn_generate_report', 'btn_generate_report', self.translator.tr('btn_generate_report'),
            style_class='purple', icon_only=False
        )
        self.btn_generate_report.clicked.connect(self.generate_report)
        layout.addWidget(self.btn_generate_report)
        
        return group
    
    def _create_table(self) -> QTableWidget:
        """Create the data table with scrollbars"""
        from PyQt5.QtWidgets import QSizePolicy
        
        table = QTableWidget()
        table.setColumnCount(len(self.columns) + 1)  # +1 for row number
        table.setHorizontalHeaderLabels(['#'] + [col[1] for col in self.columns])
        
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setFocusPolicy(Qt.StrongFocus)
        table.setTextElideMode(Qt.ElideRight)
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        # Sorting is applied to the complete filtered result before pagination.
        table.setSortingEnabled(False)
        table.verticalHeader().setVisible(False)
        table.setWordWrap(False)
        
        # Enable internal scrollbars for table data navigation
        # These scrollbars allow scrolling within the table data
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Set size policy to allow table to be constrained within container
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setMinimumSectionSize(72)
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        
        table.setColumnWidth(0, 50)
        for i, (_, _, width) in enumerate(self.columns):
            table.setColumnWidth(i + 1, width)
        
        table.itemSelectionChanged.connect(self.on_selection_changed)
        table.customContextMenuRequested.connect(self._show_table_context_menu)
        table.horizontalHeader().sectionClicked.connect(
            self.on_table_sort_requested
        )
        table.itemDoubleClicked.connect(self.quick_view)
        
        return table
    
    def _on_type_filter_changed(self, index: int):
        """Handle type filter dropdown change"""
        if index >= 0:
            record_type = self.type_filter_combo.itemData(index)
            self.filter_by_type(record_type)
    
    def filter_by_type(self, record_type: str):
        """Filter data by record type"""
        self.current_type_filter = record_type
        
        # Update combobox selection if called programmatically
        if hasattr(self, 'type_filter_combo'):
            # Find and select the matching item
            for i in range(self.type_filter_combo.count()):
                if self.type_filter_combo.itemData(i) == record_type:
                    # Block signals to prevent recursive calls
                    self.type_filter_combo.blockSignals(True)
                    self.type_filter_combo.setCurrentIndex(i)
                    self.type_filter_combo.blockSignals(False)
                    break
        
        self.apply_filters()
    
    @staticmethod
    def _sort_value(value):
        """Return a stable key for mixed unified-view values."""
        if value is None:
            return (2, '')
        if isinstance(value, bool):
            return (0, int(value))
        if isinstance(value, (int, float)):
            return (0, float(value))
        if isinstance(value, datetime):
            return (0, value.timestamp())
        return (1, str(value).casefold())

    def _sort_filtered_rows(self, rows):
        """Sort the complete filtered unified-view result."""
        if self._sort_column is None:
            return list(rows)
        if self._sort_column == 0:
            indexed_rows = list(enumerate(rows))
            indexed_rows.sort(
                key=lambda pair: pair[0],
                reverse=self._sort_order == Qt.DescendingOrder
            )
            return [row for _, row in indexed_rows]

        data_column = self._sort_column - 1
        if data_column < 0 or data_column >= len(self.columns):
            return list(rows)
        key_name = self.columns[data_column][0]
        return sorted(
            rows,
            key=lambda row: self._sort_value(row.get(key_name)),
            reverse=self._sort_order == Qt.DescendingOrder
        )

    def on_table_sort_requested(self, column: int):
        """Sort all filtered records when a table header is clicked."""
        if self._sort_column == column:
            self._sort_order = (
                Qt.DescendingOrder
                if self._sort_order == Qt.AscendingOrder
                else Qt.AscendingOrder
            )
        else:
            self._sort_column = column
            self._sort_order = Qt.AscendingOrder

        header = self.data_table.horizontalHeader()
        header.blockSignals(True)
        header.setSortIndicator(self._sort_column, self._sort_order)
        header.blockSignals(False)

        self._full_filtered_data = self._sort_filtered_rows(
            getattr(self, 'filtered_data', [])
        )
        self.filtered_data = list(self._full_filtered_data)
        self.pagination.set_total_items(len(self._full_filtered_data))
        self.apply_pagination()
        self.on_selection_changed()

    def on_selection_changed(self):
        """Update preview and keep read-only review actions stateful."""
        current_row = self.data_table.currentRow()
        if current_row >= 0:
            item = self.data_table.item(current_row, 0)
            row_data = item.data(Qt.UserRole) if item else None
            if not isinstance(row_data, dict) and current_row < len(self.page_data):
                row_data = self.page_data[current_row]
            if isinstance(row_data, dict):
                self.preview_panel.update_preview(row_data)
            else:
                self.preview_panel.clear_preview()
        else:
            self.preview_panel.clear_preview()
        self._update_action_state()
        self._update_result_summary()

    def _update_action_state(self):
        has_selection = bool(self.data_table.selectedItems()) if hasattr(self, 'data_table') else False
        if hasattr(self, 'btn_quick_view'):
            self.btn_quick_view.setEnabled(has_selection)
        if hasattr(self, 'btn_generate_report'):
            self.btn_generate_report.setEnabled(bool(self.filtered_data))

    def _update_result_summary(self):
        if not hasattr(self, 'result_summary_label'):
            return
        filtered = len(self.filtered_data or [])
        total = len(self.data or [])
        selected = len(self.data_table.selectionModel().selectedRows()) if hasattr(self, 'data_table') else 0
        records = self.translator.tr('lbl_records', default='records')
        selected_text = self.translator.tr('table_selected', default='selected')
        total_text = self.translator.tr('table_total', default='total')
        self.result_summary_label.setText(
            f"{filtered} {records}" + (
                f" · {total} {total_text}" if filtered != total else ''
            ) + f" · {selected} {selected_text}"
        )

    def _set_table_state(self, state: str, message: str = '', recoverable: bool = False):
        if not hasattr(self, 'table_state_label'):
            return
        if state == 'ready':
            self.table_state_label.clear()
            self.table_state_label.setVisible(False)
            return
        defaults = {
            'empty': self.translator.tr('table_empty', default='No records match the current view.'),
            'loading': self.translator.tr('table_loading', default='Loading records…'),
            'error': self.translator.tr('table_error', default='Unable to load records.'),
        }
        text = message or defaults.get(state, defaults['error'])
        if recoverable:
            text += '  ' + self.translator.tr('table_recover', default='Use Refresh to try again.')
        self.table_state_label.setText(text)
        self.table_state_label.setProperty('state', state)
        self.table_state_label.setVisible(True)

    def _show_table_context_menu(self, position):
        item = self.data_table.itemAt(position)
        if item is not None:
            self.data_table.setCurrentItem(item)
        menu = QMenu(self.data_table)
        menu.setObjectName('tableContextMenu')
        copy_action = QAction(get_icon('btn_copy', 18), self.translator.tr('btn_copy', default='Copy value'), menu)
        copy_action.setEnabled(bool(self.data_table.currentItem()))
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(
            self.data_table.currentItem().text() if self.data_table.currentItem() else ''
        ))
        menu.addAction(copy_action)
        preview_action = QAction(get_icon('btn_quick_view', 18), self.translator.tr('btn_quick_view'), menu)
        preview_action.setEnabled(bool(self.data_table.currentItem()))
        preview_action.triggered.connect(self.quick_view)
        menu.addAction(preview_action)
        menu.exec_(self.data_table.viewport().mapToGlobal(position))

    def toggle_column_visibility(self):
        from PyQt5.QtWidgets import QCheckBox, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle(self.translator.tr('column_visibility', default='Columns'))
        dialog.setMinimumWidth(320)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(self.translator.tr(
            'column_visibility_hint', default='Choose which columns are visible in this view.'
        )))
        checks = []
        for index, (_, label, _) in enumerate(self.columns, start=1):
            check = QCheckBox(label, dialog)
            check.setChecked(not self.data_table.isColumnHidden(index))
            layout.addWidget(check)
            checks.append((index, check))
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec_() == QDialog.Accepted:
            for index, check in checks:
                self.data_table.setColumnHidden(index, not check.isChecked())
            self.status_label.setText(self.translator.tr(
                'column_visibility_saved', default='Column visibility updated.'
            ))
    
    def on_search(self, text: str = None):
        """Handle search"""
        self.apply_filters()
    
    def on_filter_changed(self):
        """Handle date filter change"""
        self.apply_filters()
    
    def clear_date_filters(self):
        """Clear date filters"""
        date_from = self.toolbar_factory.get_date_from()
        date_to = self.toolbar_factory.get_date_to()
        if date_from:
            date_from.setDate(QDate.currentDate().addYears(-1))
        if date_to:
            date_to.setDate(QDate.currentDate())
        self.apply_filters()
    
    def apply_filters(self):
        """Apply all filters"""
        self._select_first_after_render = True
        search_edit = self.toolbar_factory.get_search_edit()
        date_from = self.toolbar_factory.get_date_from()
        date_to = self.toolbar_factory.get_date_to()
        
        search_term = search_edit.text().lower() if search_edit else ""
        date_from_val = date_from.date().toPyDate() if date_from else None
        date_to_val = date_to.date().toPyDate() if date_to else None
        
        self.filtered_data = []
        
        for row in self.data:
            # Type filter
            if self.current_type_filter != 'all':
                if row.get('record_type', '').lower() != self.current_type_filter:
                    continue
            
            # Search filter
            if search_term:
                found = False
                for val in row.values():
                    if val and search_term in str(val).lower():
                        found = True
                        break
                if not found:
                    continue
            
            # Date filter
            if date_from_val or date_to_val:
                row_date = self.get_row_date(row)
                if row_date:
                    if isinstance(row_date, datetime):
                        row_date_only = row_date.date()
                    else:
                        row_date_only = row_date
                    
                    if date_from_val and row_date_only < date_from_val:
                        continue
                    if date_to_val and row_date_only > date_to_val:
                        continue
            
            self.filtered_data.append(row)
        
        # Store full filtered data for pagination, preserving the active sort.
        self.filtered_data = self._sort_filtered_rows(self.filtered_data)
        self._full_filtered_data = self.filtered_data.copy()
        
        # Update pagination
        self.pagination.current_page = 1
        self.pagination.page_spin.setValue(1)
        self.pagination.set_total_items(len(self._full_filtered_data))
        
        self.apply_pagination()
    
    def apply_pagination(self):
        """Apply pagination to display current page"""
        if not hasattr(self, '_full_filtered_data') or self._full_filtered_data is None:
            self._full_filtered_data = self.filtered_data.copy() if self.filtered_data else []
        if self._sort_column is not None:
            self._full_filtered_data = self._sort_filtered_rows(self._full_filtered_data)
            self.filtered_data = list(self._full_filtered_data)
        
        start, end = self.pagination.get_page_range()
        
        # Get paginated data from full filtered data without replacing the
        # complete result set used by export/report actions.
        self.page_data = self._full_filtered_data[start:end]
        
        self.refresh_display()
        
        # Update status
        page_count = len(self.page_data)
        total_filtered = len(self._full_filtered_data)
        total_count = len(self.data) if self.data else 0
        
        showing_text = self.translator.tr('pagination_showing') if hasattr(self.translator, 'tr') else 'Showing'
        of_text = self.translator.tr('pagination_of') if hasattr(self.translator, 'tr') else 'of'
        records_text = self.translator.tr('lbl_records') if hasattr(self.translator, 'tr') else 'records'
        
        range_text = f"{start + 1}–{start + page_count}" if page_count else "0–0"
        if total_filtered < total_count:
            self.status_label.setText(f"{showing_text} {range_text} {of_text} {total_filtered} ({total_count} {records_text})")
        else:
            self.status_label.setText(f"{showing_text} {range_text} {of_text} {total_count} {records_text}")
        self._set_table_state('empty' if not total_filtered else 'ready')
        self._update_result_summary()
        self._update_action_state()
    
    def on_page_changed(self, page: int):
        """Handle page change"""
        self.apply_pagination()
    
    def on_page_size_changed(self, page_size: int):
        """Handle page size change"""
        self.apply_pagination()
    
    def get_row_date(self, row: Dict) -> Optional[datetime]:
        """Get date from row - checks all possible date fields from unified query"""
        date_fields = [
            'date_content',  # Content date
            'content_date_creation',  # Content creation date
            'source_date_creation',  # Source creation date
            'analysis_date_creation',  # Analysis creation date
            'date_analysis',  # Analysis date
            'source_date_entry',  # Source entry date
        ]
        for field in date_fields:
            if field in row and row[field]:
                if isinstance(row[field], datetime):
                    return row[field]
                try:
                    return datetime.strptime(str(row[field])[:10], '%Y-%m-%d')
                except:
                    pass
        return None
    
    def refresh_display(self):
        """Refresh table display"""
        self.data_table.setSortingEnabled(False)
        self.data_table.setRowCount(0)
        self.data_table.setRowCount(len(self.page_data))
        
        # Row colors that match the filter button colors
        type_colors = {
            'source': '#173B35' if AppStyles.is_dark_theme() else '#E8F8F5',
            'content': '#493A1A' if AppStyles.is_dark_theme() else '#FEF9E7',
            'analysis': '#34254A' if AppStyles.is_dark_theme() else '#F5EEF8'
        }
        
        # Get the starting row number based on pagination
        start_row_num = 1
        if hasattr(self, 'pagination'):
            start, _ = self.pagination.get_page_range()
            start_row_num = start + 1
        
        for row_idx, row_data in enumerate(self.page_data):
            # Row number (reflects actual position in full data)
            actual_row_num = start_row_num + row_idx
            row_num_item = QTableWidgetItem(str(actual_row_num))
            row_num_item.setTextAlignment(Qt.AlignCenter)
            row_num_item.setData(Qt.UserRole, row_data)
            row_num_item.setBackground(QColor(AppStyles.get_color('ROW_NUM_BG')))
            row_num_item.setFont(QFont('Segoe UI', 9, QFont.Bold))
            row_num_item.setToolTip(str(actual_row_num))
            self.data_table.setItem(row_idx, 0, row_num_item)
            
            # Get row color based on type
            record_type = row_data.get('record_type', '').lower()
            row_color = QColor(type_colors.get(record_type, '#FFFFFF'))
            
            # Data columns
            for col_idx, (col_key, _, _) in enumerate(self.columns):
                value = row_data.get(col_key, '')
                display_value = self.format_value(value, col_key)
                
                item = QTableWidgetItem(display_value)
                item.setData(Qt.UserRole, row_data)
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                item.setBackground(row_color)
                item.setToolTip(display_value)
                self.data_table.setItem(row_idx, col_idx + 1, item)

            self.data_table.setRowHeight(row_idx, 38)
        
        # Keep native row sorting disabled; sorting is applied to all filtered
        # records before the page is rendered.
        self.data_table.setSortingEnabled(False)
        
        # Select an initial/reloaded result for preview, not every page change.
        if len(self.page_data) > 0 and self._select_first_after_render:
            from PyQt5.QtCore import QTimer
            self._select_first_after_render = False
            QTimer.singleShot(50, lambda: self._select_first_row())
    
    def _select_first_row(self):
        """Select the first row to trigger preview update"""
        if self.data_table.rowCount() > 0 and not self.data_table.selectionModel().selectedRows():
            self.data_table.selectRow(0)
            # Ensure the selection is visible
            self.data_table.scrollToItem(self.data_table.item(0, 0))
    
    def format_value(self, value, col_key: str = None) -> str:
        """Format value for display"""
        if value is None:
            return ''
        elif isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')
        elif col_key == 'record_type':
            # Translate record type to display value
            type_map = {
                'analysis': self.translator.tr('tab_analysis') if hasattr(self, 'translator') else 'Analysis',
                'content': self.translator.tr('tab_contents') if hasattr(self, 'translator') else 'Content',
                'source': self.translator.tr('tab_sources') if hasattr(self, 'translator') else 'Source'
            }
            return type_map.get(str(value).lower(), str(value))
        elif col_key in ['content_importance', 'source_importance', 'importance'] and isinstance(value, (int, float)):
            return f"{float(value) * 100:.1f}%"
        return str(value)[:200] if len(str(value)) > 200 else str(value)
    
    def _deferred_load_data(self):
        """Deferred data loading to prevent UI flickering during initialization"""
        if not self._data_loaded:
            try:
                self._set_table_state('loading')
                self.load_data()
                if not self.filtered_data:
                    self._set_table_state('empty')
            except Exception as e:
                logger.error(f"Error loading data in AllDataDisplayTab: {e}")
                self._set_table_state('error', str(e), recoverable=True)
    
    def load_data(self):
        """Load all unified data"""
        try:
            self._select_first_after_render = True
            self.data = DatabaseManager.get_all_data_unified()
            logger.info(f"Loaded {len(self.data)} unified records")
            self._data_loaded = True
            self.apply_filters()
        except Exception as e:
            logger.error(f"Error loading unified data: {e}")
            self._set_table_state('error', str(e), recoverable=True)
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    # ==================== Page-Specific Operations ====================
    
    def quick_view(self):
        """Quick view of selected record"""
        current_row = self.data_table.currentRow()
        if current_row < 0 or current_row >= len(self.page_data):
            QMessageBox.warning(self, self.translator.tr('msg_no_selection'),
                              self.translator.tr('msg_select_record'))
            return
        
        item = self.data_table.item(current_row, 0)
        row_data = item.data(Qt.UserRole) if item else None
        if not isinstance(row_data, dict):
            row_data = self.page_data[current_row]
        
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
        from html import escape
        from styles.styles import AppStyles
        
        dialog = QDialog(self)
        dialog.setWindowTitle(self.translator.tr('btn_quick_view'))
        # Apply fixed size to prevent resizing
        AppStyles.apply_fixed_size(dialog, 700, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Record type badge
        record_type = row_data.get('record_type', 'Unknown')
        type_colors = {'source': '#27AE60', 'content': '#F39C12', 'analysis': '#3498DB'}
        badge_color = type_colors.get(record_type.lower(), '#7F8C8D')
        
        type_label = QLabel(f"<span style='background-color: {badge_color}; color: white; "
                          f"padding: 4px 12px; border-radius: 4px;'>{escape(str(record_type).upper())}</span>")
        layout.addWidget(type_label)
        
        # Title/Name. Unified rows expose content titles as content_title.
        title = row_data.get('content_title') or row_data.get('source_name') or 'No Title'
        title_label = QLabel(f"<h2>{escape(str(title))}</h2>")
        layout.addWidget(title_label)
        
        # Content area
        content_edit = QTextEdit()
        content_edit.setReadOnly(True)
        
        # Build content based on type
        content_parts = []
        for key, value in row_data.items():
            if value and key not in ['id', 'record_type']:
                content_parts.append(f"<b>{escape(str(key))}:</b> {escape(str(value))}")
        
        content_edit.setHtml("<br>".join(content_parts))
        layout.addWidget(content_edit)
        
        btn_close = QPushButton(self.translator.tr('btn_close'))
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        
        dialog.exec_()
    
    def generate_report(self):
        """Generate comprehensive report from current data"""
        if not self.filtered_data:
            QMessageBox.warning(self, self.translator.tr('msg_no_data'),
                              self.translator.tr('msg_no_data'))
            return
        
        try:
            from widgets.reports_tab import ReportsTab
            
            # Switch to reports tab with pre-selected data
            parent = self.parent()
            if parent and hasattr(parent, 'tab_widget'):
                # Find reports tab
                for i in range(parent.tab_widget.count()):
                    tab = parent.tab_widget.widget(i)
                    if isinstance(tab, ReportsTab):
                        # Transfer the complete filtered result set, not just
                        # the current page, into the report workspace.
                        columns = [col[0] for col in self.columns]
                        tab.set_data(self.filtered_data, columns=columns,
                                     title=self.translator.tr('tab_all_data'))
                        parent.tab_widget.setCurrentIndex(i)
                        QMessageBox.information(
                            self,
                            self.translator.tr('btn_generate_report'),
                            self.translator.tr('msg_switched_to_reports')
                        )
                        return
            
            QMessageBox.information(
                self,
                self.translator.tr('btn_generate_report'),
                self.translator.tr('msg_ready_to_generate_report', count=len(self.filtered_data))
            )
            
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def set_header(self):
        """Open header settings dialog"""
        try:
            from utils.print_utils import GlobalHeaderSettingsDialog
            dialog = GlobalHeaderSettingsDialog(self, self.translator)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    # ==================== Export Operations ====================
    
    def print_data(self):
        """Print data"""
        if not self.filtered_data:
            QMessageBox.warning(self, self.translator.tr('msg_no_data'),
                              self.translator.tr('msg_no_data'))
            return
        
        column_names = [col[1] for col in self.columns]
        
        from utils.print_utils import ExportColumnDialog, generate_print_html, get_print_settings, print_document_with_page_numbers
        dialog = ExportColumnDialog(self, self.translator, column_names)
        
        if dialog.exec_() != QDialog.Accepted:
            return
        
        selected_cols = dialog.get_selected_columns()
        col_widths = dialog.get_column_widths()
        
        if not selected_cols:
            return
        
        try:
            from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
            from PyQt5.QtGui import QTextDocument
            
            col_name_to_key = {col[1]: col[0] for col in self.columns}
            
            export_data = []
            for row in self.filtered_data:
                export_row = {}
                for col_name in selected_cols:
                    col_key = col_name_to_key.get(col_name, col_name)
                    export_row[col_name] = row.get(col_key)
                export_data.append(export_row)
            
            settings = get_print_settings()
            html = generate_print_html(export_data, selected_cols, col_widths, 
                                      'all_data', self.translator)
            
            printer = QPrinter(QPrinter.HighResolution)
            if settings.page_orientation == 'Landscape':
                printer.setOrientation(QPrinter.Landscape)
            
            print_dialog = QPrintDialog(printer, self)
            if print_dialog.exec_() == QPrintDialog.Accepted:
                doc = QTextDocument()
                doc.setHtml(html)
                print_document_with_page_numbers(doc, printer, settings)
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def export_unified(self):
        """Open unified export dialog with preview, column selection, and format choice"""
        if not self.filtered_data:
            QMessageBox.warning(self, self.translator.tr('msg_no_data'),
                              self.translator.tr('msg_no_data'))
            return
        
        from dialogs.export_preview_dialog import ExportPreviewDialog
        
        dialog = ExportPreviewDialog(
            parent=self,
            data=self.filtered_data,
            columns=[(col[0], col[1]) for col in self.columns],
            translator=self.translator,
            table_name='all_data'
        )
        
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_export_settings()
            self._execute_export(settings)
    
    def _execute_export(self, settings):
        """Execute the export based on settings from ExportPreviewDialog"""
        import csv
        from dialogs.export_preview_dialog import ExportPreviewDialog
        
        export_format = settings.get('format')
        filepath = settings.get('path')
        selected_columns = settings.get('columns')
        column_widths = settings.get('column_widths', {})
        data = settings.get('data')
        open_after = settings.get('open_after', False)
        
        if not filepath or not selected_columns:
            return
        
        try:
            success = False
            if export_format == ExportPreviewDialog.FORMAT_EXCEL:
                from utils.excel_export import export_to_excel
                success = export_to_excel(
                    data,
                    self.columns,
                    filepath,
                    self.translator,
                    'all_data',
                    include_all_fields=False,
                    selected_columns=selected_columns,
                    column_widths=column_widths
                )
            
            elif export_format == ExportPreviewDialog.FORMAT_CSV:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    if data:
                        fieldnames = [col[0] for col in selected_columns]
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        header_row = {col[0]: col[1] for col in selected_columns}
                        writer.writerow(sanitize_row(header_row))
                        for row in data:
                            filtered_row = {key: row.get(key, '') for key in fieldnames}
                            writer.writerow(sanitize_row(filtered_row))
                success = True
            
            elif export_format == ExportPreviewDialog.FORMAT_WORD:
                from utils.word_export import export_to_word
                success = export_to_word(
                    data,
                    self.columns,
                    filepath,
                    self.translator,
                    'all_data',
                    include_all_fields=False,
                    selected_columns=selected_columns,
                    column_widths=column_widths
                )
            
            elif export_format == ExportPreviewDialog.FORMAT_PDF:
                from PyQt5.QtPrintSupport import QPrinter
                from PyQt5.QtGui import QTextDocument
                from utils.print_utils import generate_print_html, get_print_settings, print_document_with_page_numbers, print_document_with_page_numbers
                
                col_names = [col[1] for col in selected_columns]
                col_key_to_name = {col[0]: col[1] for col in selected_columns}
                
                export_data = []
                for row in data:
                    export_row = {}
                    for col_key, col_name in selected_columns:
                        export_row[col_name] = row.get(col_key)
                    export_data.append(export_row)
                
                # Convert column_widths from key-based to name-based for PDF
                pdf_column_widths = {}
                for col_key, col_name in selected_columns:
                    if col_key in column_widths:
                        pdf_column_widths[col_name] = column_widths[col_key]
                
                ps = get_print_settings()
                html = generate_print_html(export_data, col_names, pdf_column_widths, 'all_data', self.translator)
                
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(filepath)
                if ps.page_orientation == 'Landscape':
                    printer.setOrientation(QPrinter.Landscape)
                else:
                    printer.setOrientation(QPrinter.Portrait)
                
                doc = QTextDocument()
                doc.setHtml(html)
                print_document_with_page_numbers(doc, printer, ps)
                success = os.path.isfile(filepath) and os.path.getsize(filepath) > 0
            
            elif export_format == ExportPreviewDialog.FORMAT_JSON:
                from utils.json_xml_export import export_to_json
                # Filter data to selected columns
                filtered_data = []
                for row in data:
                    filtered_row = {}
                    for col_key, _ in selected_columns:
                        if col_key in row:
                            filtered_row[col_key] = row[col_key]
                    filtered_data.append(filtered_row)
                success = export_to_json(filtered_data, filepath)
            
            elif export_format == ExportPreviewDialog.FORMAT_XML:
                from utils.json_xml_export import export_to_xml
                # Filter data to selected columns
                filtered_data = []
                for row in data:
                    filtered_row = {}
                    for col_key, _ in selected_columns:
                        if col_key in row:
                            filtered_row[col_key] = row[col_key]
                    filtered_data.append(filtered_row)
                success = export_to_xml(filtered_data, filepath, root_name='all_data', record_name='record')
            
            elif export_format == ExportPreviewDialog.FORMAT_JSON_LINES:
                from utils.json_xml_export import export_to_json_lines
                # Filter data to selected columns
                filtered_data = []
                for row in data:
                    filtered_row = {}
                    for col_key, _ in selected_columns:
                        if col_key in row:
                            filtered_row[col_key] = row[col_key]
                    filtered_data.append(filtered_row)
                success = export_to_json_lines(filtered_data, filepath)
            else:
                raise ValueError(f"Unsupported export format: {export_format}")

            if not success or not os.path.isfile(filepath) or os.path.getsize(filepath) == 0:
                raise IOError(f"Export did not create a valid output file: {filepath}")
            
            QMessageBox.information(
                self,
                self.translator.tr('msg_success'),
                self.translator.tr('export_success') + f"\n{filepath}"
            )
            
            if open_after:
                ExportPreviewDialog.open_file(filepath)
                
        except ImportError as e:
            QMessageBox.critical(
                self,
                self.translator.tr('msg_error'),
                f"{self.translator.tr('msg_missing_library')}: {str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                self.translator.tr('msg_error'),
                f"{self.translator.tr('export_failed')}: {str(e)}"
            )
    
    def export_pdf(self):
        """Export to PDF"""
        if not self.filtered_data:
            QMessageBox.warning(self, self.translator.tr('msg_no_data'),
                              self.translator.tr('msg_no_data'))
            return
        
        column_names = [col[1] for col in self.columns]
        
        from utils.print_utils import ExportColumnDialog, generate_print_html, get_print_settings, print_document_with_page_numbers
        dialog = ExportColumnDialog(self, self.translator, column_names)
        
        if dialog.exec_() != QDialog.Accepted:
            return
        
        selected_cols = dialog.get_selected_columns()
        col_widths = dialog.get_column_widths()
        
        if not selected_cols:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.translator.tr('btn_export_pdf'),
            f'all_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            'PDF Files (*.pdf)'
        )
        
        if filename:
            try:
                from PyQt5.QtPrintSupport import QPrinter
                from PyQt5.QtGui import QTextDocument
                
                col_name_to_key = {col[1]: col[0] for col in self.columns}
                
                export_data = []
                for row in self.filtered_data:
                    export_row = {}
                    for col_name in selected_cols:
                        col_key = col_name_to_key.get(col_name, col_name)
                        export_row[col_name] = row.get(col_key)
                    export_data.append(export_row)
                
                settings = get_print_settings()
                html = generate_print_html(export_data, selected_cols, col_widths, 
                                          'all_data', self.translator)
                
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(filename)
                if settings.page_orientation == 'Landscape':
                    printer.setOrientation(QPrinter.Landscape)
                else:
                    printer.setOrientation(QPrinter.Portrait)
                
                doc = QTextDocument()
                doc.setHtml(html)
                print_document_with_page_numbers(doc, printer, settings)
                if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
                    raise IOError(f"PDF output was not created: {filename}")
                
                QMessageBox.information(self, self.translator.tr('msg_success'),
                                       f"{self.translator.tr('msg_exported_to')}:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def export_csv(self):
        """Export to CSV"""
        if not self.filtered_data:
            QMessageBox.warning(self, self.translator.tr('msg_no_data'),
                              self.translator.tr('msg_no_data'))
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.translator.tr('btn_export_csv'),
            f'all_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            'CSV Files (*.csv)'
        )
        
        if filename:
            try:
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    if self.filtered_data:
                        fieldnames = list(self.filtered_data[0].keys())
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writerow(sanitize_row({key: key for key in fieldnames}))
                        for row in self.filtered_data:
                            writer.writerow(sanitize_row(row))
                if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
                    raise IOError(f"CSV output was not created: {filename}")
                
                QMessageBox.information(self, self.translator.tr('msg_success'),
                                      f"Exported to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def export_excel(self):
        """Export to Excel"""
        if not self.filtered_data:
            QMessageBox.warning(self, self.translator.tr('msg_no_data'),
                              self.translator.tr('msg_no_data'))
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.translator.tr('btn_export_excel'),
            f'all_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            'Excel Files (*.xlsx)'
        )
        
        if filename:
            try:
                from utils.excel_export import export_to_excel
                success = export_to_excel(
                    self.filtered_data,
                    self.columns,
                    filename,
                    self.translator,
                    'all_data'
                )
                if not success or not os.path.isfile(filename):
                    raise IOError(f"Excel output was not created: {filename}")
                QMessageBox.information(self, self.translator.tr('msg_success'),
                                      f"Exported to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def export_word(self):
        """Export to Word"""
        if not self.filtered_data:
            QMessageBox.warning(self, self.translator.tr('msg_no_data'),
                              self.translator.tr('msg_no_data'))
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.translator.tr('btn_export_word'),
            f'all_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx',
            'Word Documents (*.docx)'
        )
        
        if filename:
            try:
                from utils.word_export import export_to_word
                success = export_to_word(
                    self.filtered_data,
                    self.columns,
                    filename,
                    self.translator,
                    'all_data'
                )
                if not success or not os.path.isfile(filename):
                    raise IOError(f"Word output was not created: {filename}")
                QMessageBox.information(self, self.translator.tr('msg_success'),
                                      f"Exported to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def refresh_columns(self):
        """Refresh column headers when language changes"""
        self.columns = [
            ('record_type', self.translator.tr('lbl_record_type'), 100),
            ('source_name', self.translator.tr('lbl_source'), 180),
            ('content_title', self.translator.tr('lbl_title'), 200),
            ('content_data', self.translator.tr('lbl_content_data'), 300),
            ('classification', self.translator.tr('lbl_classification'), 130),
            ('content_importance', self.translator.tr('lbl_importance'), 100),
            ('date_content', self.translator.tr('lbl_date_content'), 150),
            ('content_date_creation', self.translator.tr('lbl_date_creation'), 150)
        ]
        headers = ['#'] + [col[1] for col in self.columns]
        self.data_table.setHorizontalHeaderLabels(headers)
    
    def _apply_layout_direction(self):
        """Apply RTL/LTR layout direction based on current language"""
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        
        self.setLayoutDirection(direction)
        
        # Update AppStyles global direction
        AppStyles.set_layout_direction('rtl' if is_rtl else 'ltr')
    
    def _apply_direction_to_children(self):
        """Apply current layout direction to all child widgets"""
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        
        # Apply to all child widgets
        from PyQt5.QtWidgets import QWidget
        for child in self.findChildren(QWidget):
            child.setLayoutDirection(direction)
    
    def refresh_translations(self):
        """Refresh all UI translations when language changes"""
        # Apply RTL/LTR layout direction first
        self._apply_layout_direction()
        self._apply_direction_to_children()
        
        # Refresh page title - use instance variable for reliable access
        page_title_key = getattr(self, '_page_title_key', None) or self.PAGE_TITLE
        if hasattr(self, 'title_label') and self.title_label is not None and page_title_key:
            new_title = self.translator.tr(page_title_key)
            self.title_label.setText(new_title)
            # Force widget update to ensure the change is displayed
            self.title_label.update()
        
        # Refresh read-only badge
        if hasattr(self, 'readonly_badge') and self.readonly_badge:
            self.readonly_badge.setText(self.translator.tr('msg_readonly'))
            if hasattr(self, 'readonly_icon'):
                self.readonly_icon.setToolTip(self.translator.tr('msg_readonly'))
        
        # Refresh toolbar translations
        if hasattr(self, 'toolbar_factory'):
            self.toolbar_factory.refresh_translations()
        
        # Apply direction to toolbar widget
        if hasattr(self, 'toolbar'):
            is_rtl = self.translator.current_language == 'ar'
            direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
            self.toolbar.setLayoutDirection(direction)
            # Apply to all toolbar children
            from PyQt5.QtWidgets import QWidget
            for child in self.toolbar.findChildren(QWidget):
                child.setLayoutDirection(direction)
        
        # Refresh pagination widget
        if hasattr(self, 'pagination') and hasattr(self.pagination, 'refresh_translations'):
            self.pagination.refresh_translations()
        
        # Refresh status, review actions, and result context.
        if hasattr(self, 'status_label'):
            self.status_label.setStyleSheet(AppStyles.get_component_style('status_label'))
            self._update_result_summary()
            self.pagination.update_display()
        if hasattr(self, 'btn_quick_view'):
            self.btn_quick_view.setText(self.translator.tr('btn_quick_view'))
            self.btn_quick_view.setToolTip(self.translator.tr('btn_quick_view'))
            self.btn_quick_view.setAccessibleName(self.translator.tr('btn_quick_view'))
        if hasattr(self, 'btn_generate_report'):
            self.btn_generate_report.setText(self.translator.tr('btn_generate_report'))
            self.btn_generate_report.setToolTip(self.translator.tr('btn_generate_report'))
            self.btn_generate_report.setAccessibleName(self.translator.tr('btn_generate_report'))
        if hasattr(self, 'table_state_label'):
            self.table_state_label.setStyleSheet(AppStyles.get_component_style('table_state'))
        
        # Refresh type filter group title
        if hasattr(self, 'type_filter_group'):
            self.type_filter_group.setTitle(self.translator.tr('lbl_filter_by_type'))
        
        # Refresh type filter label
        if hasattr(self, 'type_filter_label'):
            self.type_filter_label.setText(self.translator.tr('lbl_record_type') + ":")
        
        # Refresh type filter dropdown items
        if hasattr(self, 'type_filter_combo'):
            # Store current selection
            current_data = self.type_filter_combo.currentData()
            
            # Update options with new translations
            self.type_filter_options = [
                ('all', self.translator.tr('btn_all_types'), '#3498DB'),
                ('source', self.translator.tr('tab_sources'), '#27AE60'),
                ('content', self.translator.tr('tab_contents'), '#F39C12'),
                ('analysis', self.translator.tr('tab_analysis'), '#9B59B6'),
            ]
            
            # Block signals during update
            self.type_filter_combo.blockSignals(True)
            self.type_filter_combo.clear()
            
            # Repopulate with translated items
            for key, display_text, color in self.type_filter_options:
                self.type_filter_combo.addItem(display_text, key)
            
            # Restore selection
            for i in range(self.type_filter_combo.count()):
                if self.type_filter_combo.itemData(i) == current_data:
                    self.type_filter_combo.setCurrentIndex(i)
                    break
            
            self.type_filter_combo.blockSignals(False)
        
        if hasattr(self, 'data_table'):
            self.data_table.setStyleSheet(AppStyles.get_table_scrollbar_style())
            self.refresh_display()
        # Refresh preview panel
        if hasattr(self, 'preview_panel') and hasattr(self.preview_panel, 'refresh_translations'):
            self.preview_panel.refresh_translations()
