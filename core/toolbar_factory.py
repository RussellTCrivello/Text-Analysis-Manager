"""
Toolbar Factory - Creates consistent, page-specific toolbars
Ensures each page has dedicated buttons while maintaining design consistency
"""
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Dict
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, 
    QLabel, QGroupBox, QDateEdit, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate
from icons.icon_manager import setup_icon_button
from translations.translations import TranslationManager
from styles.styles import AppStyles


@dataclass
class ButtonConfig:
    """Configuration for a single button"""
    key: str  # Translation key for tooltip/text
    icon_key: str  # Icon key for setup_icon_button
    callback: Optional[Callable] = None
    style_class: Optional[str] = None  # 'danger', 'success', 'primary'
    enabled: bool = True
    visible: bool = True


@dataclass
class ToolbarConfig:
    """Configuration for toolbar sections"""
    # CRUD Section (Add, Edit, Delete, Refresh)
    show_crud: bool = True
    show_add: bool = True
    show_edit: bool = True
    show_delete: bool = True
    show_refresh: bool = True
    
    # Export Section - Simplified: Only Print and Unified Export
    # Individual format buttons (PDF, CSV, Excel, Word) are disabled by default
    # Users should use the unified Export Preview dialog for all export needs
    show_export: bool = True
    show_print: bool = True
    show_pdf: bool = False  # Use unified export instead
    show_csv: bool = False  # Use unified export instead
    show_excel: bool = False  # Use unified export instead
    show_word: bool = False  # Use unified export instead
    show_export_unified: bool = True  # Main export button with preview dialog
    
    # Search & Filter Section
    show_search: bool = True
    show_date_filter: bool = True
    
    # Page-specific buttons
    page_specific_buttons: List[ButtonConfig] = field(default_factory=list)
    
    # Settings buttons
    show_header_settings: bool = True
    
    # Custom labels
    page_title: str = ""
    page_icon: str = ""


class ToolbarFactory:
    """
    Factory class for creating consistent toolbars across all tabs.
    Each page gets dedicated buttons appropriate for its function.
    """
    
    def __init__(self, translator: TranslationManager):
        self.translator = translator
        self.buttons: Dict[str, QPushButton] = {}
    
    def create_toolbar(self, parent: QWidget, config: ToolbarConfig, 
                      callbacks: Dict[str, Callable]) -> QWidget:
        """
        Create a complete toolbar widget with all sections.
        
        Args:
            parent: Parent widget
            config: Toolbar configuration
            callbacks: Dictionary of callback functions keyed by action name
        
        Returns:
            QWidget containing the complete toolbar
        """
        toolbar_widget = QWidget(parent)
        toolbar_widget.setObjectName('workspaceToolbar')
        
        # Apply RTL/LTR direction based on current language
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        toolbar_widget.setLayoutDirection(direction)
        
        main_layout = QVBoxLayout(toolbar_widget)
        # Use 8px grid spacing
        main_layout.setContentsMargins(0, 0, 0, AppStyles.get_spacing(1))  # 8px bottom
        main_layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid
        
        # Top row: Search and Date Filter
        if config.show_search or config.show_date_filter:
            filter_row = self._create_filter_row(toolbar_widget, config, callbacks)
            main_layout.addWidget(filter_row)
        
        # Bottom row: Action buttons
        action_row = self._create_action_row(toolbar_widget, config, callbacks)
        main_layout.addWidget(action_row)
        
        return toolbar_widget
    
    def _create_filter_row(self, parent: QWidget, config: ToolbarConfig,
                          callbacks: Dict[str, Callable]) -> QWidget:
        """Create the search and date filter row"""
        row = QWidget(parent)
        row.setObjectName('workspaceFilterRow')
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid (rounding 12px to 16px)
        layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        
        # Search Section
        if config.show_search:
            search_widget = self._create_search_section(row, callbacks)
            layout.addWidget(search_widget)
        
        # Date Filter Section
        if config.show_date_filter:
            date_widget = self._create_date_filter_section(row, callbacks)
            layout.addWidget(date_widget)
        
        layout.addStretch()

        # The filter row contains date controls with deliberate minimum widths.
        # Keep it usable on compact windows by allowing horizontal scrolling
        # instead of clipping labels or calendar fields.
        from PyQt5.QtWidgets import QScrollArea
        filter_scroll = QScrollArea(parent)
        filter_scroll.setObjectName('workspaceFilterScroller')
        filter_scroll.setWidgetResizable(False)
        filter_scroll.setFrameShape(QFrame.NoFrame)
        filter_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        filter_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        filter_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        filter_scroll.setMinimumHeight(66)
        filter_scroll.setMaximumHeight(82)
        filter_scroll.setWidget(row)
        return filter_scroll
    
    def _create_search_section(self, parent: QWidget, 
                               callbacks: Dict[str, Callable]) -> QWidget:
        """Create search input section"""
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid
        layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        
        # Search label - ensure full text display
        label = QLabel(self.translator.tr('lbl_search') + ":")
        label.setMinimumWidth(60)  # Ensure enough width for label text
        label.setStyleSheet(AppStyles.get_component_style('toolbar_label'))
        layout.addWidget(label)
        self.buttons['search_label'] = label
        
        # Search input
        search_edit = QLineEdit()
        search_edit.setPlaceholderText(self.translator.tr('msg_type_to_search'))
        search_edit.setMinimumWidth(200)
        search_edit.setStyleSheet(AppStyles.get_component_style('search_input'))
        if 'search' in callbacks:
            search_edit.textChanged.connect(callbacks['search'])
        layout.addWidget(search_edit)
        self.buttons['search_edit'] = search_edit
        
        return widget
    
    def _create_date_filter_section(self, parent: QWidget,
                                    callbacks: Dict[str, Callable]) -> QWidget:
        """Create date filter section"""
        group = QGroupBox(self.translator.tr('lbl_date_filter'))
        group.setStyleSheet(AppStyles.get_component_style('date_filter_group'))
        group.setMinimumWidth(350)  # Ensure enough width for full text
        self.buttons['date_filter_group'] = group
        layout = QHBoxLayout(group)
        # Use 8px grid spacing
        date_margin_h = AppStyles.get_spacing(1)  # 8px horizontal (rounding 10px to 8px)
        date_margin_v = AppStyles.get_spacing(1)  # 8px vertical (rounding 6px to 8px)
        layout.setContentsMargins(date_margin_h, date_margin_v, date_margin_h, date_margin_v)
        layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid (rounding 10px to 8px)
        layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        
        # From date - ensure full text display
        from_label = QLabel(self.translator.tr('lbl_date_from') + ":")
        from_label.setMinimumWidth(50)
        from_label.setStyleSheet(AppStyles.get_component_style('toolbar_label'))
        layout.addWidget(from_label)
        self.buttons['date_from_label'] = from_label
        
        from_date = QDateEdit()
        from_date.setCalendarPopup(True)
        from_date.setDate(QDate.currentDate().addYears(-1))
        from_date.setDisplayFormat("yyyy-MM-dd")
        from_date.setMinimumWidth(110)
        if 'date_filter_changed' in callbacks:
            from_date.dateChanged.connect(callbacks['date_filter_changed'])
        layout.addWidget(from_date)
        self.buttons['date_from_edit'] = from_date
        
        # To date - ensure full text display
        to_label = QLabel(self.translator.tr('lbl_date_to') + ":")
        to_label.setMinimumWidth(40)
        to_label.setStyleSheet(AppStyles.get_component_style('toolbar_label'))
        layout.addWidget(to_label)
        self.buttons['date_to_label'] = to_label
        
        to_date = QDateEdit()
        to_date.setCalendarPopup(True)
        to_date.setDate(QDate.currentDate())
        to_date.setDisplayFormat("yyyy-MM-dd")
        to_date.setMinimumWidth(110)
        if 'date_filter_changed' in callbacks:
            to_date.dateChanged.connect(callbacks['date_filter_changed'])
        layout.addWidget(to_date)
        self.buttons['date_to_edit'] = to_date
        
        # Clear button
        btn_clear = QPushButton()
        setup_icon_button(btn_clear, 'btn_clear', self.translator.tr('btn_clear'))
        if 'clear_dates' in callbacks:
            btn_clear.clicked.connect(callbacks['clear_dates'])
        layout.addWidget(btn_clear)
        self.buttons['btn_clear_dates'] = btn_clear
        
        return group
    
    def _create_action_row(self, parent: QWidget, config: ToolbarConfig,
                          callbacks: Dict[str, Callable]) -> QWidget:
        """Create the action buttons row with horizontal scrolling for smaller screens"""
        from PyQt5.QtWidgets import QScrollArea
        from PyQt5.QtCore import Qt
        
        # Create scroll area for horizontal scrolling on smaller screens
        scroll_area = QScrollArea(parent)
        scroll_area.setObjectName('workspaceActionScroller')
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setFixedHeight(50)  # Fixed height for toolbar row
        scroll_area.setStyleSheet(AppStyles.get_component_style('toolbar_scroll'))
        
        # Content widget inside scroll area
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid
        layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment for all items
        
        # CRUD Section
        if config.show_crud:
            crud_widget = self._create_crud_section(row, config, callbacks)
            layout.addWidget(crud_widget)
            layout.addWidget(self._create_separator())
        
        # Page-specific buttons
        if config.page_specific_buttons:
            specific_widget = self._create_page_specific_section(
                row, config.page_specific_buttons, callbacks
            )
            layout.addWidget(specific_widget)
            layout.addWidget(self._create_separator())
        
        layout.addStretch()
        
        # Export Section
        if config.show_export:
            export_widget = self._create_export_section(row, config, callbacks)
            layout.addWidget(export_widget)
        
        # Settings buttons
        if config.show_header_settings:
            layout.addWidget(self._create_separator())
            btn_header = QPushButton()
            setup_icon_button(btn_header, 'btn_set_header', 
                            self.translator.tr('btn_set_header'))
            if 'set_header' in callbacks:
                btn_header.clicked.connect(callbacks['set_header'])
            layout.addWidget(btn_header)
            self.buttons['btn_set_header'] = btn_header
        
        scroll_area.setWidget(row)
        return scroll_area
    
    def _create_crud_section(self, parent: QWidget, config: ToolbarConfig,
                            callbacks: Dict[str, Callable]) -> QWidget:
        """Create CRUD buttons section"""
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid (rounding 6px to 8px)
        layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        
        # Add button
        if config.show_add:
            btn_add = QPushButton()
            btn_add.setStyleSheet(AppStyles.get_button_style('success'))
            setup_icon_button(btn_add, 'btn_add', self.translator.tr('btn_add'))
            if 'add' in callbacks:
                btn_add.clicked.connect(callbacks['add'])
            layout.addWidget(btn_add)
            self.buttons['btn_add'] = btn_add
        
        # Edit button
        if config.show_edit:
            btn_edit = QPushButton()
            setup_icon_button(btn_edit, 'btn_edit', self.translator.tr('btn_edit'))
            if 'edit' in callbacks:
                btn_edit.clicked.connect(callbacks['edit'])
            layout.addWidget(btn_edit)
            self.buttons['btn_edit'] = btn_edit
        
        # Delete button
        if config.show_delete:
            btn_delete = QPushButton()
            btn_delete.setProperty('class', 'danger')
            btn_delete.setStyleSheet(AppStyles.get_button_style('danger'))
            setup_icon_button(btn_delete, 'btn_delete', self.translator.tr('btn_delete'))
            if 'delete' in callbacks:
                btn_delete.clicked.connect(callbacks['delete'])
            layout.addWidget(btn_delete)
            self.buttons['btn_delete'] = btn_delete
        
        # Refresh button
        if config.show_refresh:
            btn_refresh = QPushButton()
            setup_icon_button(btn_refresh, 'btn_refresh', self.translator.tr('btn_refresh'))
            if 'refresh' in callbacks:
                btn_refresh.clicked.connect(callbacks['refresh'])
            layout.addWidget(btn_refresh)
            self.buttons['btn_refresh'] = btn_refresh
        
        return widget
    
    def _create_page_specific_section(self, parent: QWidget, 
                                      buttons: List[ButtonConfig],
                                      callbacks: Dict[str, Callable]) -> QWidget:
        """Create page-specific buttons section"""
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid (rounding 6px to 8px)
        layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        
        for btn_config in buttons:
            if not btn_config.visible:
                continue
            
            btn = QPushButton()
            
            # Apply style BEFORE setting up icon so we can detect if white icon is needed
            if btn_config.style_class:
                btn.setStyleSheet(AppStyles.get_button_style(btn_config.style_class))
            
            # Now setup icon (will detect colored background and use appropriate icon color)
            setup_icon_button(btn, btn_config.icon_key, 
                            self.translator.tr(btn_config.key))
            
            btn.setEnabled(btn_config.enabled)
            
            if btn_config.callback:
                btn.clicked.connect(btn_config.callback)
            elif btn_config.icon_key in callbacks:
                btn.clicked.connect(callbacks[btn_config.icon_key])
            
            layout.addWidget(btn)
            # Store button using the key from config (already has btn_ prefix in icon_key)
            self.buttons[btn_config.icon_key] = btn
        
        return widget
    
    def _create_export_section(self, parent: QWidget, config: ToolbarConfig,
                              callbacks: Dict[str, Callable]) -> QWidget:
        """Create export buttons section"""
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid (rounding 6px to 8px)
        layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        
        # Unified export button (with preview dialog)
        if config.show_export_unified:
            btn_export = QPushButton()
            btn_export.setStyleSheet(AppStyles.get_button_style('purple'))
            setup_icon_button(btn_export, 'btn_export', self.translator.tr('btn_export'))
            if 'export_unified' in callbacks:
                btn_export.clicked.connect(callbacks['export_unified'])
            layout.addWidget(btn_export)
            self.buttons['btn_export_unified'] = btn_export
        
        # Print button
        if config.show_print:
            btn_print = QPushButton()
            setup_icon_button(btn_print, 'btn_print', self.translator.tr('btn_print'))
            if 'print' in callbacks:
                btn_print.clicked.connect(callbacks['print'])
            layout.addWidget(btn_print)
            self.buttons['btn_print'] = btn_print
        
        # PDF button
        if config.show_pdf:
            btn_pdf = QPushButton()
            setup_icon_button(btn_pdf, 'btn_export_pdf', self.translator.tr('btn_export_pdf'))
            if 'export_pdf' in callbacks:
                btn_pdf.clicked.connect(callbacks['export_pdf'])
            layout.addWidget(btn_pdf)
            self.buttons['btn_export_pdf'] = btn_pdf
        
        # CSV button
        if config.show_csv:
            btn_csv = QPushButton()
            setup_icon_button(btn_csv, 'btn_export_csv', self.translator.tr('btn_export_csv'))
            if 'export_csv' in callbacks:
                btn_csv.clicked.connect(callbacks['export_csv'])
            layout.addWidget(btn_csv)
            self.buttons['btn_export_csv'] = btn_csv
        
        # Excel button
        if config.show_excel:
            btn_excel = QPushButton()
            setup_icon_button(btn_excel, 'btn_export_excel', self.translator.tr('btn_export_excel'))
            if 'export_excel' in callbacks:
                btn_excel.clicked.connect(callbacks['export_excel'])
            layout.addWidget(btn_excel)
            self.buttons['btn_export_excel'] = btn_excel
        
        # Word button
        if config.show_word:
            btn_word = QPushButton()
            setup_icon_button(btn_word, 'btn_export_word', self.translator.tr('btn_export_word'))
            if 'export_word' in callbacks:
                btn_word.clicked.connect(callbacks['export_word'])
            layout.addWidget(btn_word)
            self.buttons['btn_export_word'] = btn_word
        
        return widget
    
    def _create_separator(self) -> QFrame:
        """Create a vertical separator line"""
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet(f"color: {AppStyles.get_color('BORDER')};")
        return sep
    
    def get_button(self, key: str) -> Optional[QPushButton]:
        """Get a button by its key"""
        return self.buttons.get(key)
    
    def get_search_edit(self) -> Optional[QLineEdit]:
        """Get the search input field"""
        return self.buttons.get('search_edit')
    
    def get_date_from(self) -> Optional[QDateEdit]:
        """Get the from date picker"""
        return self.buttons.get('date_from_edit')
    
    def get_date_to(self) -> Optional[QDateEdit]:
        """Get the to date picker"""
        return self.buttons.get('date_to_edit')
    
    def refresh_translations(self):
        """Refresh all button translations when language changes"""
        from icons.icon_manager import setup_icon_button
        
        # Refresh button texts and tooltips using the original setup function
        # This ensures consistent icon loading and button configuration
        button_configs = {
            'btn_add': 'btn_add',
            'btn_edit': 'btn_edit',
            'btn_delete': 'btn_delete',
            'btn_refresh': 'btn_refresh',
            'btn_print': 'btn_print',
            'btn_print_preview': 'btn_print_preview',
            'btn_export_pdf': 'btn_export_pdf',
            'btn_export_csv': 'btn_export_csv',
            'btn_export_excel': 'btn_export_excel',
            'btn_export_word': 'btn_export_word',
            'btn_export': 'btn_export',
            'btn_export_unified': 'btn_export',
            'btn_clear_dates': 'btn_clear',
            'btn_clear': 'btn_clear',
            'btn_set_header': 'btn_set_header',
        }
        
        for btn_key, icon_key in button_configs.items():
            btn = self.buttons.get(btn_key)
            if btn and isinstance(btn, QPushButton):
                # Use setup_icon_button for consistent icon and tooltip refresh
                translated_tooltip = self.translator.tr(icon_key)
                setup_icon_button(btn, icon_key, translated_tooltip)
        
        # Refresh page-specific buttons that have custom configs
        for btn_key, btn in self.buttons.items():
            if btn_key.startswith('btn_') and btn_key not in button_configs:
                if isinstance(btn, QPushButton):
                    # Extract the icon key from button key
                    icon_key = btn_key.replace('btn_', '')
                    # Try to get translation for this button
                    tr_key = f'btn_{icon_key}'
                    tooltip = self.translator.tr(tr_key) if self.translator.tr(tr_key) != tr_key else btn.toolTip()
                    if tooltip:
                        setup_icon_button(btn, btn_key, tooltip)
        
        # Refresh labels
        search_label = self.buttons.get('search_label')
        if search_label:
            search_label.setText(self.translator.tr('lbl_search') + ":")
            search_label.setVisible(True)
        
        search_edit = self.buttons.get('search_edit')
        if search_edit:
            search_edit.setPlaceholderText(self.translator.tr('msg_type_to_search'))
            search_edit.setVisible(True)
        
        date_from_label = self.buttons.get('date_from_label')
        if date_from_label:
            date_from_label.setText(self.translator.tr('lbl_date_from') + ":")
            date_from_label.setVisible(True)
        
        date_to_label = self.buttons.get('date_to_label')
        if date_to_label:
            date_to_label.setText(self.translator.tr('lbl_date_to') + ":")
            date_to_label.setVisible(True)
        
        # Refresh date filter group title
        date_filter_group = self.buttons.get('date_filter_group')
        if date_filter_group:
            date_filter_group.setVisible(True)
            date_filter_group.setTitle(self.translator.tr('lbl_date_filter'))
        
        # Apply RTL/LTR direction to all widgets
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        
        for widget in self.buttons.values():
            if hasattr(widget, 'setLayoutDirection'):
                widget.setLayoutDirection(direction)