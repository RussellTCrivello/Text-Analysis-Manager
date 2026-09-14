"""
Base Table Tab - Foundation for all data management tabs
Provides common functionality while allowing page-specific customization
"""
import csv
import os
from datetime import datetime
from typing import Optional, Dict, List

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QFileDialog,
    QHeaderView, QDialog, QDateEdit, QGroupBox, QSplitter
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont

from core.toolbar_factory import ToolbarFactory, ToolbarConfig, ButtonConfig
from translations.translations import TranslationManager
from styles.styles import AppStyles
from utils.logger import get_logger
from icons.icon_manager import setup_icon_button

logger = get_logger(__name__)


class SimpleTableWidget(QTableWidget):
    """Simple table widget with basic filtering and automatic row numbering"""
    
    def __init__(self, columns: List[tuple], parent=None):
        super().__init__(parent)
        self.original_columns = columns
        # Add row number column at the beginning
        self.columns = [('#', '#', 50)] + list(columns)
        self.data = []
        # ``filtered_data`` is the complete result set after search/date
        # filtering. ``display_data`` is only the current page. Keeping these
        # separate prevents export/report actions from silently exporting one
        # visible page instead of all matching records.
        self.filtered_data = []
        self.display_data = []
        
        self.setup_table()
    
    def setup_table(self):
        """Setup table properties with full text display and scrollbars"""
        self.setColumnCount(len(self.columns))
        self.setHorizontalHeaderLabels([col[1] for col in self.columns])
        
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSortingEnabled(True)
        self.verticalHeader().setVisible(False)
        
        # Enable word wrap for full text display
        self.setWordWrap(True)
        
        # Enable internal scrollbars for table data navigation
        # These scrollbars allow scrolling within the table data
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Set size policy to allow table to be constrained within its container
        from PyQt5.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setDefaultSectionSize(150)
        
        for i, (_, _, width) in enumerate(self.columns):
            self.setColumnWidth(i, width)
    
    def load_data(self, data: List[Dict]):
        """Load data into table"""
        self.data = list(data or [])
        self.filtered_data = self.data.copy()
        self.display_data = self.data.copy()
        self._start_row_num = 1  # Default starting row number
        self.refresh_display()
    
    def set_start_row_num(self, start_row: int):
        """Set the starting row number for pagination display"""
        self._start_row_num = start_row
    
    def refresh_display(self):
        """Refresh table display with full text and row numbers"""
        self.setSortingEnabled(False)
        self.setRowCount(0)
        self.setRowCount(len(self.display_data))
        
        # Get starting row number (for pagination)
        start_row_num = getattr(self, '_start_row_num', 1)
        
        for row_idx, row_data in enumerate(self.display_data):
            # Add row number in first column (reflects actual position in full data)
            actual_row_num = start_row_num + row_idx
            row_num_item = QTableWidgetItem(str(actual_row_num))
            row_num_item.setTextAlignment(Qt.AlignCenter)
            row_num_item.setData(Qt.UserRole, row_data.get('id'))
            row_num_item.setBackground(QColor('#F8F9FA'))
            row_num_item.setFont(QFont('Segoe UI', 9, QFont.Bold))
            self.setItem(row_idx, 0, row_num_item)
            
            # Add data columns (starting from column 1)
            for col_idx, (col_key, _, _) in enumerate(self.original_columns):
                value = row_data.get(col_key, '')
                display_value = self.format_value(value, col_key)
                
                item = QTableWidgetItem(display_value)
                item.setData(Qt.UserRole, row_data.get('id'))
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
                self.setItem(row_idx, col_idx + 1, item)
            
            # Resize row to fit content
            self.resizeRowToContents(row_idx)
        
        self.setSortingEnabled(True)
        
        # Automatically select first row if data exists to show preview by default
        if len(self.display_data) > 0:
            from PyQt5.QtCore import QTimer
            # Use QTimer to select after table is fully rendered
            QTimer.singleShot(50, lambda: self._select_first_row())
    
    def _select_first_row(self):
        """Select the first row to trigger preview update"""
        if self.rowCount() > 0:
            self.selectRow(0)
            # Ensure the selection is visible
            self.scrollToItem(self.item(0, 0))
    
    def format_value(self, value, col_key: str = None) -> str:
        """Format value for display"""
        if value is None:
            return ''
        elif isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')
        elif isinstance(value, (int, float)) and col_key:
            if 'importance' in col_key.lower():
                try:
                    from widgets.widgets import PercentageSpinBox
                    return PercentageSpinBox.format_percentage(float(value))
                except:
                    return f"{float(value):.1f}%"
        elif col_key == 'record_type':
            type_map = {
                'analysis': 'Analysis',
                'content': 'Content',
                'source': 'Source'
            }
            return type_map.get(str(value).lower(), str(value))
        elif col_key in ['coordinates', 'list_coordinates']:
            if value and isinstance(value, str):
                return value.replace('; ', ' | ')
        return str(value)
    
    def get_selected_id(self) -> Optional[int]:
        """Get selected row ID"""
        current_row = self.currentRow()
        if current_row >= 0:
            item = self.item(current_row, 0)
            if item:
                return item.data(Qt.UserRole)
        return None
    
    def filter_data(self, search_term: str = ""):
        """Filter data by search term"""
        if not search_term:
            self.filtered_data = self.data.copy()
        else:
            self.filtered_data = []
            search_lower = search_term.lower()
            for row in self.data:
                if any(str(val).lower().find(search_lower) != -1 
                      for val in row.values() if val is not None):
                    self.filtered_data.append(row)
        
        self.display_data = self.filtered_data.copy()
        self.refresh_display()
    
    def export_to_csv(self, filename: str, selected_columns: Optional[List[tuple]] = None):
        """Export filtered data to CSV with selected columns"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if self.filtered_data:
                if selected_columns:
                    fieldnames = [col[0] for col in selected_columns]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in self.filtered_data:
                        filtered_row = {key: row.get(key, '') for key in fieldnames}
                        writer.writerow(filtered_row)
                else:
                    writer = csv.DictWriter(f, fieldnames=self.filtered_data[0].keys())
                    writer.writeheader()
                    writer.writerows(self.filtered_data)
        return True


class BaseTableTab(QWidget):
    """
    Base class for table management tabs.
    Provides common functionality with page-specific customization.
    Supports responsive design and RTL/LTR layout directions.
    """
    
    # Override in subclasses to customize toolbar
    TOOLBAR_CONFIG = ToolbarConfig()
    PAGE_TITLE = ""
    PAGE_ICON = ""
    
    def __init__(self, parent, table_name: str, columns: List[tuple], 
                 translator: TranslationManager):
        super().__init__(parent)
        self.table_name = table_name
        self.columns = columns
        self.translator = translator
        self.toolbar_factory = ToolbarFactory(translator)
        self._data_loaded = False  # Track if data has been loaded
        
        # Store page title key as instance variable for reliable access during translation refresh
        self._page_title_key = self.PAGE_TITLE
        
        # Apply RTL/LTR layout direction based on language
        self._apply_layout_direction()
        
        self.setup_ui()
        # Defer data loading until window is shown to prevent UI flickering
        # Only load if parent window is visible, otherwise wait
        from PyQt5.QtCore import QTimer
        if parent and parent.isVisible():
            QTimer.singleShot(100, self._deferred_load_data)
        else:
            # Window not shown yet, will be loaded when tab becomes visible
            pass
    
    def get_toolbar_config(self) -> ToolbarConfig:
        """Override in subclasses to provide page-specific toolbar config"""
        buttons = self.get_page_specific_buttons()
        
        # Add bulk operations button
        buttons.append(ButtonConfig(
            key='bulk_operations',
            icon_key='btn_select_all',  # Use existing icon
            callback=self.show_bulk_operations,
            style_class='primary'
        ))
        
        # Add advanced search button
        buttons.append(ButtonConfig(
            key='advanced_search',
            icon_key='btn_search',  # Use existing icon
            callback=self.show_advanced_search,
            style_class=None
        ))
        
        return ToolbarConfig(
            show_crud=True,
            show_export=True,
            show_search=True,
            show_date_filter=True,
            page_specific_buttons=buttons
        )
    
    def get_page_specific_buttons(self) -> List[ButtonConfig]:
        """Override in subclasses to add page-specific buttons"""
        return []
    
    def get_callbacks(self) -> Dict[str, callable]:
        """Get callback functions for toolbar buttons"""
        callbacks = {
            'search': self.on_search,
            'date_filter_changed': self.on_filter_changed,
            'clear_dates': self.clear_date_filters,
            'add': self.add_record,
            'edit': self.edit_record,
            'delete': self.delete_record,
            'refresh': self.load_data,
            'print': self.print_data,
            'export_pdf': self.export_pdf,
            'export_csv': self.export_csv,
            'export_excel': self.export_excel,
            'export_word': self.export_word,
            'export_unified': self.export_unified,
            'bulk_operations': self.show_bulk_operations,
            'advanced_search': self.show_advanced_search,
        }
        return callbacks
    
    def setup_ui(self):
        """Setup UI with toolbar and table - with unified scrolling"""
        from PyQt5.QtWidgets import QSizePolicy, QFrame, QScrollArea
        
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
        
        # Page title (if specified) - fixed, always visible
        self.title_label = None
        if self._page_title_key:
            self.title_label = QLabel(self.translator.tr(self._page_title_key))
            self.title_label.setStyleSheet(AppStyles.get_component_style('page_title'))
            self.title_label.setObjectName("page_title_label")  # For debugging
            scroll_layout.addWidget(self.title_label)
        
        # Toolbar from factory - fixed height, no stretch
        config = self.get_toolbar_config()
        callbacks = self.get_callbacks()
        self.toolbar = self.toolbar_factory.create_toolbar(self, config, callbacks)
        self.toolbar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        scroll_layout.addWidget(self.toolbar, 0)  # stretch factor 0 = don't expand
        
        # Container frame for table area with fixed proportions
        table_container = QFrame()
        table_container.setFrameShape(QFrame.NoFrame)
        table_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        
        # Splitter for table and preview panel
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Table with internal scrollbars for table data navigation
        self.data_table = SimpleTableWidget(self.columns, self)
        self.data_table.itemDoubleClicked.connect(self.edit_record)
        self.data_table.itemSelectionChanged.connect(self.on_selection_changed)
        # Enable internal scrollbars for table data
        self.data_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.data_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Apply timeline-style scrollbar styling
        self.data_table.setStyleSheet(AppStyles.get_table_scrollbar_style())
        self.splitter.addWidget(self.data_table)
        
        # Full Text Preview Panel
        from widgets.text_preview_panel import TextPreviewPanel
        self.preview_panel = TextPreviewPanel(self.translator)
        self.preview_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.splitter.addWidget(self.preview_panel)
        
        # Set splitter proportions - table gets more space
        self.splitter.setSizes([400, 150])
        self.splitter.setStretchFactor(0, 3)  # Table gets 3x stretch
        self.splitter.setStretchFactor(1, 1)  # Preview gets 1x stretch
        
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
    
    def on_selection_changed(self):
        """Handle table selection change to update preview"""
        current_row = self.data_table.currentRow()
        display_data = getattr(self.data_table, 'display_data', self.data_table.filtered_data)
        if current_row >= 0 and current_row < len(display_data):
            row_data = display_data[current_row]
            self.preview_panel.update_preview(row_data)
        else:
            self.preview_panel.clear_preview()
    
    def on_search(self, text: str = None):
        """Handle search"""
        if text is None:
            search_edit = self.toolbar_factory.get_search_edit()
            text = search_edit.text() if search_edit else ""
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
        """Apply all filters (search and date)"""
        search_edit = self.toolbar_factory.get_search_edit()
        date_from = self.toolbar_factory.get_date_from()
        date_to = self.toolbar_factory.get_date_to()
        
        search_term = search_edit.text() if search_edit else ""
        date_from_val = date_from.date().toPyDate() if date_from else None
        date_to_val = date_to.date().toPyDate() if date_to else None
        
        # Filter by search term first
        if search_term:
            self.data_table.filter_data(search_term)
        else:
            self.data_table.filtered_data = self.data_table.data.copy()
        
        # Filter by date range
        if date_from_val or date_to_val:
            filtered = []
            for row in self.data_table.filtered_data:
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
                filtered.append(row)
            self.data_table.filtered_data = filtered
        
        # ``filtered_data`` remains the complete result set. Pagination only
        # changes ``display_data`` so downstream exports and reports see every
        # matching row.
        self.data_table.display_data = self.data_table.filtered_data.copy()
        self._full_filtered_data = self.data_table.filtered_data.copy()
        
        # Update pagination with filtered data count
        self.pagination.set_total_items(len(self._full_filtered_data))
        
        # Reset to first page when filters change
        self.pagination.current_page = 1
        self.pagination.page_spin.setValue(1)
        
        # Apply pagination
        self.apply_pagination()
    
    def apply_pagination(self):
        """Apply pagination to display current page"""
        # Use the stored full filtered data for slicing
        if not hasattr(self, '_full_filtered_data') or self._full_filtered_data is None:
            self._full_filtered_data = self.data_table.filtered_data.copy() if hasattr(self.data_table, 'filtered_data') else []
        
        start, end = self.pagination.get_page_range()
        
        # Get the page of data from the full filtered data (don't overwrite filtered_data)
        paginated_data = self._full_filtered_data[start:end]
        
        # Set starting row number for correct row display
        self.data_table.set_start_row_num(start + 1)
        
        # Keep the complete filtered set intact for export/report actions;
        # only the display set is paginated.
        self.data_table.display_data = paginated_data
        self.data_table.refresh_display()
        
        # Update status with correct counts
        page_count = len(paginated_data)
        total_filtered = len(self._full_filtered_data)
        total_count = len(self.data_table.data) if hasattr(self.data_table, 'data') else 0
        
        # Get translated strings for status
        showing_text = self.translator.tr('pagination_showing') if hasattr(self.translator, 'tr') else 'Showing'
        of_text = self.translator.tr('pagination_of') if hasattr(self.translator, 'tr') else 'of'
        records_text = self.translator.tr('lbl_records') if hasattr(self.translator, 'tr') else 'records'
        
        range_text = f"{start + 1}-{start + page_count}" if page_count else "0-0"
        if total_filtered < total_count:
            # Filtered view
            self.status_label.setText(f"{showing_text} {range_text} {of_text} {total_filtered} ({total_count} {records_text})")
        else:
            self.status_label.setText(f"{showing_text} {range_text} {of_text} {total_count} {records_text}")
    
    def on_page_changed(self, page: int):
        """Handle page change"""
        self.apply_pagination()
    
    def on_page_size_changed(self, page_size: int):
        """Handle page size change"""
        self.apply_pagination()
    
    def get_row_date(self, row: Dict) -> Optional[datetime]:
        """Get date from row for filtering - override in subclasses"""
        date_fields = [
            'date_creation', 'date_content', 'date_entry', 'date_analysis',
            'source_date_creation', 'content_date_creation', 'analysis_date_creation',
            'source_date_entry', 'date_content'
        ]
        for date_field in date_fields:
            if date_field in row and row[date_field]:
                if isinstance(row[date_field], datetime):
                    return row[date_field]
                elif isinstance(row[date_field], str):
                    try:
                        return datetime.strptime(row[date_field][:10], '%Y-%m-%d')
                    except:
                        pass
        return None
    
    # ==================== CRUD Operations ====================
    
    def _deferred_load_data(self):
        """Deferred data loading to prevent UI flickering during initialization"""
        if not self._data_loaded and self.isVisible():
            try:
                self.load_data()
                self._data_loaded = True
            except Exception as e:
                from utils.logger import get_logger
                logger = get_logger(__name__)
                logger.error(f"Error loading data in {self.__class__.__name__}: {e}")
    
    def load_data(self):
        """Load data - override in subclasses"""
        # After loading, update pagination
        if hasattr(self, 'data_table') and hasattr(self.data_table, 'data'):
            # Initialize full filtered data with all data
            self._full_filtered_data = self.data_table.data.copy()
            self.data_table.filtered_data = self.data_table.data.copy()
            self.data_table.display_data = self.data_table.data.copy()
            
            # Reset pagination to first page
            self.pagination.current_page = 1
            self.pagination.set_total_items(len(self.data_table.data))
            
            # Apply pagination to show first page
            self.apply_pagination()
    
    def add_record(self):
        """Add record - override in subclasses"""
        pass
    
    def edit_record(self):
        """Edit record - override in subclasses"""
        pass
    
    def delete_record(self):
        """Delete selected record"""
        selected_id = self.data_table.get_selected_id()
        if not selected_id:
            QMessageBox.warning(self, self.translator.tr('msg_no_selection'),
                              self.translator.tr('msg_select_record'))
            return
        
        reply = QMessageBox.question(
            self,
            self.translator.tr('msg_warning'),
            self.translator.tr('msg_confirm_delete'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.delete_from_db(selected_id)
                QMessageBox.information(self, self.translator.tr('msg_success'),
                                      self.translator.tr('msg_record_deleted'))
                self.load_data()
                self.status_label.setText(self.translator.tr('msg_record_deleted'))
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def delete_from_db(self, record_id: int):
        """Delete from database - override in subclasses"""
        pass
    
    # ==================== Export Operations ====================
    
    def export_unified(self):
        """Open unified export dialog with preview, column selection, and format choice"""
        if not self.data_table.filtered_data:
            QMessageBox.warning(self, self.translator.tr('msg_no_data'),
                              self.translator.tr('msg_no_data'))
            return
        
        from dialogs.export_preview_dialog import ExportPreviewDialog
        
        dialog = ExportPreviewDialog(
            parent=self,
            data=self.data_table.filtered_data,
            columns=[(col[0], col[1]) for col in self.columns],
            translator=self.translator,
            table_name=self.table_name
        )
        
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_export_settings()
            self._execute_export(settings)
    
    def _execute_export(self, settings: Dict):
        """Execute the export based on settings from ExportPreviewDialog"""
        from dialogs.export_preview_dialog import ExportPreviewDialog
        
        export_format = settings.get('format')
        filepath = settings.get('path')
        selected_columns = settings.get('columns')
        column_widths = settings.get('column_widths', {})
        data = settings.get('data')
        open_after = settings.get('open_after', False)
        include_header = settings.get('include_header', True)
        
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
                    self.table_name,
                    include_all_fields=False,
                    selected_columns=selected_columns,
                    column_widths=column_widths
                )
            
            elif export_format == ExportPreviewDialog.FORMAT_CSV:
                success = self._export_csv_data(filepath, data, selected_columns)
            
            elif export_format == ExportPreviewDialog.FORMAT_WORD:
                from utils.word_export import export_table_data_to_word_timeline_style
                success = export_table_data_to_word_timeline_style(
                    data,
                    filepath,
                    self.translator,
                    self.table_name,
                    selected_columns=selected_columns,
                    include_header=include_header
                )
            
            elif export_format == ExportPreviewDialog.FORMAT_PDF:
                success = self._export_pdf_data(filepath, data, selected_columns, column_widths)
            
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
                success = export_to_xml(filtered_data, filepath, root_name=self.table_name, record_name='record')
            
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
            
            # Show success message
            QMessageBox.information(
                self,
                self.translator.tr('msg_success'),
                self.translator.tr('export_success') + f"\n{filepath}"
            )
            
            # Open file if requested
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
            logger.error(f"Export error: {e}")
    
    def _export_csv_data(self, filepath: str, data: List[Dict], columns: List[tuple]):
        """Export data to CSV file"""
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if data:
                fieldnames = [col[0] for col in columns]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                # Write header with display names
                header_row = {col[0]: col[1] for col in columns}
                writer.writerow(header_row)
                # Write data rows
                for row in data:
                    filtered_row = {key: row.get(key, '') for key in fieldnames}
                    writer.writerow(filtered_row)
        return True
    
    def _export_pdf_data(self, filepath: str, data: List[Dict], columns: List[tuple], column_widths: Dict[str, int] = None):
        """Export data to PDF file with Arabic support"""
        from PyQt5.QtPrintSupport import QPrinter
        from PyQt5.QtGui import QTextDocument, QFont
        from utils.print_utils import generate_print_html, get_print_settings, print_document_with_page_numbers
        from styles.styles import AppStyles
        
        # Map column keys to names for HTML generation
        col_names = [col[1] for col in columns]
        
        # Convert column_widths from key-based to name-based for PDF
        pdf_col_widths = {}
        if column_widths:
            for col_key, col_name in columns:
                if col_key in column_widths:
                    pdf_col_widths[col_name] = column_widths[col_key]
        
        # Prepare data with column names as keys
        col_key_to_name = {col[0]: col[1] for col in columns}
        export_data = []
        for row in data:
            export_row = {}
            for col_key, col_name in columns:
                export_row[col_name] = row.get(col_key)
            export_data.append(export_row)
        
        settings = get_print_settings()
        html = generate_print_html(export_data, col_names, pdf_col_widths, 
                                  self.table_name, self.translator)
        
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filepath)
        # Always use landscape orientation for comfortable table display
        printer.setOrientation(QPrinter.Landscape)
        
        # Configure for Arabic if needed
        is_rtl = self.translator.current_language == 'ar'
        
        doc = QTextDocument()
        
        # Set default font for Arabic
        if is_rtl:
            arabic_font = AppStyles.get_arabic_font(10)
            doc.setDefaultFont(arabic_font)
        
        doc.setHtml(html)
        print_document_with_page_numbers(doc, printer, settings)
        if not os.path.isfile(filepath) or os.path.getsize(filepath) == 0:
            raise IOError(f"PDF output was not created: {filepath}")
        return True
    
    def export_word(self):
        """Export to Word in timeline-style format (not table format)"""
        if not self.data_table.filtered_data:
            QMessageBox.warning(self, self.translator.tr('msg_no_data'),
                              self.translator.tr('msg_no_data'))
            return
        
        all_keys = set()
        for row in self.data_table.filtered_data:
            all_keys.update(row.keys())
        
        from dialogs.column_selection_dialog import ColumnSelectionDialog
        dialog = ColumnSelectionDialog(
            self,
            columns=[(col[0], col[1]) for col in self.columns],
            translator=self.translator,
            include_all_fields=True,
            all_available_keys=all_keys
        )
        
        if dialog.exec_() != QDialog.Accepted:
            return
        
        selected_columns = dialog.get_selected_columns()
        if not selected_columns:
            QMessageBox.warning(self, self.translator.tr('msg_warning'),
                              self.translator.tr('msg_select_column_to_export'))
            return
        
        try:
            from utils.word_export import export_table_data_to_word_timeline_style
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                self.translator.tr('btn_export_word'),
                f'{self.table_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx',
                'Word Documents (*.docx);;All Files (*)'
            )
            
            if filename:
                success = export_table_data_to_word_timeline_style(
                    self.data_table.filtered_data,
                    filename,
                    self.translator,
                    self.table_name,
                    selected_columns=selected_columns,
                    include_header=True
                )
                if not success or not os.path.isfile(filename):
                    raise IOError(f"Word output was not created: {filename}")
                QMessageBox.information(
                    self,
                    self.translator.tr('msg_success'),
                    self.translator.tr('msg_word_export_success') + f"\n{filename}"
                )
        except ImportError:
            QMessageBox.critical(
                self,
                self.translator.tr('msg_error'),
                self.translator.tr('msg_python_docx_not_installed')
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                self.translator.tr('msg_error'),
                f"{self.translator.tr('msg_word_export_failed')}: {str(e)}"
            )
            logger.error(f"Error exporting to Word: {e}")
    
    def print_data(self):
        """Print data with professional header"""
        if not self.data_table.filtered_data:
            QMessageBox.warning(self, self.translator.tr('msg_no_data'),
                              self.translator.tr('msg_no_data'))
            return
        
        column_names = [col[1] for col in self.columns]
        
        from utils.print_utils import ExportColumnDialog, generate_print_html, get_print_settings
        dialog = ExportColumnDialog(self, self.translator, column_names)
        
        if dialog.exec_() != QDialog.Accepted:
            return
        
        selected_cols = dialog.get_selected_columns()
        col_widths = dialog.get_column_widths()
        
        if not selected_cols:
            QMessageBox.warning(
                self,
                self.translator.tr('msg_warning'),
                self.translator.tr('msg_select_column_to_print')
            )
            return
        
        try:
            from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
            from PyQt5.QtGui import QTextDocument, QFont
            from styles.styles import AppStyles
            
            col_name_to_key = {col[1]: col[0] for col in self.columns}
            
            export_data = []
            for row in self.data_table.filtered_data:
                export_row = {}
                for col_name in selected_cols:
                    col_key = col_name_to_key.get(col_name, col_name)
                    export_row[col_name] = row.get(col_key)
                export_data.append(export_row)
            
            settings = get_print_settings()
            html = generate_print_html(export_data, selected_cols, col_widths, 
                                      self.table_name, self.translator)
            
            printer = QPrinter(QPrinter.HighResolution)
            if settings.page_orientation == 'Landscape':
                printer.setOrientation(QPrinter.Landscape)
            
            # Configure for Arabic if needed
            is_rtl = self.translator.current_language == 'ar'
            
            print_dialog = QPrintDialog(printer, self)
            if print_dialog.exec_() == QPrintDialog.Accepted:
                doc = QTextDocument()
                
                # Set default font for Arabic
                if is_rtl:
                    arabic_font = AppStyles.get_arabic_font(10)
                    doc.setDefaultFont(arabic_font)
                
                doc.setHtml(html)
                print_document_with_page_numbers(doc, printer, settings)
                QMessageBox.information(self, self.translator.tr('msg_success'),
                                       self.translator.tr('report_print_success'))
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def export_pdf(self):
        """Export to PDF with professional header"""
        if not self.data_table.filtered_data:
            QMessageBox.warning(self, self.translator.tr('msg_no_data'),
                              self.translator.tr('msg_no_data'))
            return
        
        column_names = [col[1] for col in self.columns]
        
        from utils.print_utils import ExportColumnDialog, generate_print_html, get_print_settings
        dialog = ExportColumnDialog(self, self.translator, column_names)
        
        if dialog.exec_() != QDialog.Accepted:
            return
        
        selected_cols = dialog.get_selected_columns()
        col_widths = dialog.get_column_widths()
        
        if not selected_cols:
            QMessageBox.warning(self, self.translator.tr('msg_warning'),
                              self.translator.tr('msg_select_column_to_export'))
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.translator.tr('btn_export_pdf'),
            f'{self.table_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            'PDF Files (*.pdf);;All Files (*)'
        )
        
        if filename:
            try:
                from PyQt5.QtPrintSupport import QPrinter
                from PyQt5.QtGui import QTextDocument, QFont
                from styles.styles import AppStyles
                
                col_name_to_key = {col[1]: col[0] for col in self.columns}
                
                export_data = []
                for row in self.data_table.filtered_data:
                    export_row = {}
                    for col_name in selected_cols:
                        col_key = col_name_to_key.get(col_name, col_name)
                        export_row[col_name] = row.get(col_key)
                    export_data.append(export_row)
                
                settings = get_print_settings()
                html = generate_print_html(export_data, selected_cols, col_widths, 
                                          self.table_name, self.translator)
                
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(filename)
                # Always use landscape orientation for comfortable table display
                printer.setOrientation(QPrinter.Landscape)
                
                # Configure for Arabic if needed
                is_rtl = self.translator.current_language == 'ar'
                
                doc = QTextDocument()
                
                # Set default font for Arabic
                if is_rtl:
                    arabic_font = AppStyles.get_arabic_font(10)
                    doc.setDefaultFont(arabic_font)
                
                doc.setHtml(html)
                print_document_with_page_numbers(doc, printer, settings)
                if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
                    raise IOError(f"PDF output was not created: {filename}")
                
                QMessageBox.information(self, self.translator.tr('msg_success'),
                                       f"{self.translator.tr('report_export_success')}\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def export_csv(self):
        """Export to CSV with column selection"""
        if not self.data_table.filtered_data:
            QMessageBox.warning(self, self.translator.tr('msg_no_data'),
                              self.translator.tr('msg_no_data'))
            return
        
        all_keys = set()
        for row in self.data_table.filtered_data:
            all_keys.update(row.keys())
        
        from dialogs.column_selection_dialog import ColumnSelectionDialog
        dialog = ColumnSelectionDialog(
            self,
            columns=[(col[0], col[1]) for col in self.columns],
            translator=self.translator,
            include_all_fields=True,
            all_available_keys=all_keys
        )
        
        if dialog.exec_() != QDialog.Accepted:
            return
        
        selected_columns = dialog.get_selected_columns()
        if not selected_columns:
            QMessageBox.warning(self, self.translator.tr('msg_warning'),
                              self.translator.tr('msg_select_column_to_export'))
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.translator.tr('btn_export_csv'),
            f'{self.table_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            'CSV Files (*.csv);;All Files (*)'
        )
        
        if filename:
            try:
                success = self.data_table.export_to_csv(filename, selected_columns)
                if not success or not os.path.isfile(filename) or os.path.getsize(filename) == 0:
                    raise IOError(f"CSV output was not created: {filename}")
                QMessageBox.information(self, self.translator.tr('msg_success'),
                                      f"{self.translator.tr('msg_data_exported_to')}:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def export_excel(self):
        """Export to Excel with column selection"""
        if not self.data_table.filtered_data:
            QMessageBox.warning(self, self.translator.tr('msg_no_data'),
                              self.translator.tr('msg_no_data'))
            return
        
        all_keys = set()
        for row in self.data_table.filtered_data:
            all_keys.update(row.keys())
        
        from dialogs.column_selection_dialog import ColumnSelectionDialog
        dialog = ColumnSelectionDialog(
            self,
            columns=[(col[0], col[1]) for col in self.columns],
            translator=self.translator,
            include_all_fields=True,
            all_available_keys=all_keys
        )
        
        if dialog.exec_() != QDialog.Accepted:
            return
        
        selected_columns = dialog.get_selected_columns()
        if not selected_columns:
            QMessageBox.warning(self, self.translator.tr('msg_warning'),
                              self.translator.tr('msg_select_column_to_export'))
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.translator.tr('btn_export_excel'),
            f'{self.table_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            'Excel Files (*.xlsx);;All Files (*)'
        )
        
        if filename:
            try:
                from utils.excel_export import export_to_excel
                success = export_to_excel(
                    self.data_table.filtered_data,
                    self.columns,
                    filename,
                    self.translator,
                    self.table_name,
                    include_all_fields=True,
                    selected_columns=selected_columns
                )
                if not success or not os.path.isfile(filename):
                    raise IOError(f"Excel output was not created: {filename}")
                QMessageBox.information(
                    self,
                    self.translator.tr('msg_success'),
                    self.translator.tr('msg_excel_export_success') + f"\n{filename}"
                )
            except ImportError:
                QMessageBox.critical(
                    self,
                    self.translator.tr('msg_error'),
                    self.translator.tr('msg_openpyxl_not_installed')
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    self.translator.tr('msg_error'),
                    f"{self.translator.tr('msg_excel_export_failed')}: {str(e)}"
                )
                logger.error(f"Error exporting to Excel: {e}")
    
    def refresh_columns(self):
        """Refresh column headers when language changes - override in subclasses"""
        pass
    
    def show_bulk_operations(self):
        """Show bulk operations dialog"""
        from dialogs.bulk_operations_dialog import BulkOperationsDialog
        dialog = BulkOperationsDialog(
            self, self.translator, self.table_name,
            self.data_table.data, self.columns
        )
        dialog.operation_completed.connect(self.on_bulk_operation_completed)
        dialog.exec_()
    
    def on_bulk_operation_completed(self, operation_type: str, count: int):
        """Handle bulk operation completion"""
        self.load_data()
        self.status_label.setText(self.translator.tr('msg_bulk_operation_completed', operation=operation_type, count=count))
    
    def show_advanced_search(self):
        """Show advanced search dialog"""
        from dialogs.advanced_search_dialog import AdvancedSearchDialog
        dialog = AdvancedSearchDialog(self, self.translator, self.table_name)
        if dialog.exec_() == QDialog.Accepted:
            results = dialog.get_results()
            if results:
                # Update data table with search results
                self.data_table.data = list(results)
                self.data_table.filtered_data = list(results)
                self.data_table.display_data = list(results)
                self.pagination.set_total_items(len(results))
                self.apply_pagination()
    
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
        
        # Refresh toolbar translations and apply direction
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
        
        # Refresh status label
        if hasattr(self, 'status_label'):
            count = len(self.data_table.filtered_data) if hasattr(self, 'data_table') else 0
            self.status_label.setText(f"{count} {self.translator.tr('msg_ready').lower()}")
        
        # Refresh preview panel
        if hasattr(self, 'preview_panel') and hasattr(self.preview_panel, 'refresh_translations'):
            self.preview_panel.refresh_translations()
        
        # Refresh pagination widget
        if hasattr(self, 'pagination') and hasattr(self.pagination, 'refresh_translations'):
            self.pagination.refresh_translations()
        
        # Refresh table column headers
        if hasattr(self, 'data_table') and hasattr(self, 'columns'):
            self.refresh_columns()
