"""
Toolbar Factory - Creates consistent, page-specific toolbars
Ensures each page has dedicated buttons while maintaining design consistency
"""
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Dict
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit,
    QLabel, QGroupBox, QDateEdit, QFrame, QSizePolicy,
    QToolButton, QMenu, QAction
)
from PyQt5.QtCore import Qt, QDate, QSize
from icons.icon_manager import get_icon
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

    # Actions that are useful but should not compete with the table's primary
    # workflow. They remain available in the overflow menu and keep their
    # original callbacks, tooltips, and accessibility text.
    TERTIARY_ACTION_KEYS = {
        'bulk_operations', 'advanced_search', 'btn_duplicate',
        'btn_duplicate_content', 'btn_duplicate_analysis', 'btn_statistics',
        'btn_link_analysis', 'btn_view_map', 'btn_compare', 'btn_summary',
        'column_visibility',
    }

    def __init__(self, translator: TranslationManager):
        self.translator = translator
        self.buttons: Dict[str, QPushButton] = {}
        self.menu_actions: Dict[str, QAction] = {}
        self.more_button: Optional[QToolButton] = None
        self.more_menu: Optional[QMenu] = None

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

        clear_search = self._create_labeled_action_button(
            'btn_clear', 'btn_clear_search', self.translator.tr('btn_clear'), icon_only=True
        )
        clear_search.setEnabled(False)
        search_edit.textChanged.connect(clear_search.setEnabled)
        clear_search.clicked.connect(search_edit.clear)
        layout.addWidget(clear_search)
        self.buttons['btn_clear_search'] = clear_search

        return widget

    def _create_date_filter_section(self, parent: QWidget,
                                    callbacks: Dict[str, Callable]) -> QWidget:
        """Create date filter section"""
        group = QGroupBox(self.translator.tr('lbl_date_filter'))
        group.setStyleSheet(AppStyles.get_component_style('date_filter_group'))
        group.setMinimumWidth(420)  # Keep labels and both date values readable
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
        from_label.setMinimumWidth(64)
        from_label.setStyleSheet(AppStyles.get_component_style('toolbar_label'))
        layout.addWidget(from_label)
        self.buttons['date_from_label'] = from_label

        from_date = QDateEdit()
        from_date.setCalendarPopup(True)
        from_date.setDate(QDate.currentDate().addYears(-1))
        from_date.setDisplayFormat("yyyy-MM-dd")
        from_date.setMinimumWidth(160)
        if 'date_filter_changed' in callbacks:
            from_date.dateChanged.connect(callbacks['date_filter_changed'])
        layout.addWidget(from_date)
        self.buttons['date_from_edit'] = from_date

        # To date - ensure full text display
        to_label = QLabel(self.translator.tr('lbl_date_to') + ":")
        to_label.setMinimumWidth(64)
        to_label.setStyleSheet(AppStyles.get_component_style('toolbar_label'))
        layout.addWidget(to_label)
        self.buttons['date_to_label'] = to_label

        to_date = QDateEdit()
        to_date.setCalendarPopup(True)
        to_date.setDate(QDate.currentDate())
        to_date.setDisplayFormat("yyyy-MM-dd")
        to_date.setMinimumWidth(160)
        if 'date_filter_changed' in callbacks:
            to_date.dateChanged.connect(callbacks['date_filter_changed'])
        layout.addWidget(to_date)
        self.buttons['date_to_edit'] = to_date

        # Clear button
        btn_clear = self._create_labeled_action_button(
            'btn_clear', 'btn_clear_dates', self.translator.tr('btn_clear'), icon_only=True
        )
        if 'clear_dates' in callbacks:
            btn_clear.clicked.connect(callbacks['clear_dates'])
        layout.addWidget(btn_clear)
        self.buttons['btn_clear_dates'] = btn_clear

        return group

    def _create_action_row(self, parent: QWidget, config: ToolbarConfig,
                           callbacks: Dict[str, Callable]) -> QWidget:
        """Create grouped table actions with an overflow for tertiary work."""
        from PyQt5.QtWidgets import QScrollArea

        scroll_area = QScrollArea(parent)
        scroll_area.setObjectName('workspaceActionScroller')
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.NoFrame)
        # Two visual tiers (group caption + actions) keep the toolbar legible
        # without turning every operation into a loud labeled button.
        scroll_area.setFixedHeight(76)
        scroll_area.setStyleSheet(AppStyles.get_component_style('toolbar_scroll'))

        row = QWidget()
        row.setObjectName('workspaceActionRow')
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(AppStyles.get_spacing(1))
        layout.setAlignment(Qt.AlignVCenter)

        # Build the overflow first so page-specific controls can contribute
        # actions without creating a second, unrelated button row.
        self.more_menu = QMenu(row)
        self.more_menu.setObjectName('tableMoreMenu')
        self.menu_actions = {}

        if config.show_crud:
            crud_widget = self._create_crud_section(row, config, callbacks)
            layout.addWidget(crud_widget)
            layout.addWidget(self._create_group_separator())

        if config.page_specific_buttons:
            specific_widget = self._create_page_specific_section(
                row, config.page_specific_buttons, callbacks
            )
            if specific_widget.layout() and specific_widget.layout().count():
                layout.addWidget(specific_widget)
                layout.addWidget(self._create_group_separator())

        # Output belongs to its own visual group and stays immediately
        # accessible without competing with record manipulation.
        if config.show_export:
            export_widget = self._create_export_section(row, config, callbacks)
            layout.addWidget(export_widget)

        if config.show_header_settings:
            layout.addWidget(self._create_group_separator())
            view_group = QWidget(row)
            view_layout = QVBoxLayout(view_group)
            view_layout.setContentsMargins(0, 0, 0, 0)
            view_layout.setSpacing(2)
            view_caption = QLabel(self.translator.tr('toolbar_view', default='View'))
            view_caption.setObjectName('toolbarGroupLabel')
            self.buttons['toolbar_view_label'] = view_caption
            view_layout.addWidget(view_caption)
            view_actions = QWidget(view_group)
            view_actions_layout = QHBoxLayout(view_actions)
            view_actions_layout.setContentsMargins(0, 0, 0, 0)
            btn_header = self._create_labeled_action_button(
                'btn_set_header', 'btn_set_header', self.translator.tr('btn_set_header'),
                style_class=None, icon_only=True
            )
            if 'set_header' in callbacks:
                btn_header.clicked.connect(callbacks['set_header'])
            view_actions_layout.addWidget(btn_header)
            view_layout.addWidget(view_actions)
            layout.addWidget(view_group)
            self.buttons['btn_set_header'] = btn_header

        if self.more_menu.actions():
            layout.addWidget(self._create_group_separator())
            more_button = QToolButton(row)
            more_button.setObjectName('toolbarMoreButton')
            more_button.setIcon(get_icon('more', 18))
            more_button.setIconSize(QSize(18, 18))
            more_button.setText(self.translator.tr('toolbar_more', default='More'))
            more_button.setToolTip(self.translator.tr('toolbar_more_hint', default='More table actions'))
            more_button.setAccessibleName(more_button.toolTip())
            more_button.setPopupMode(QToolButton.InstantPopup)
            more_button.setMenu(self.more_menu)
            self.more_button = more_button
            layout.addWidget(more_button)

        layout.addStretch(1)
        scroll_area.setWidget(row)
        return scroll_area

    def _create_crud_section(self, parent: QWidget, config: ToolbarConfig,
                             callbacks: Dict[str, Callable]) -> QWidget:
        """Create the high-frequency record actions as a compact group."""
        widget = QWidget(parent)
        widget.setObjectName('toolbarCrudGroup')
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        caption = QLabel(self.translator.tr('toolbar_records', default='Records'))
        caption.setObjectName('toolbarGroupLabel')
        self.buttons['toolbar_records_label'] = caption
        layout.addWidget(caption)
        action_row = QWidget(widget)
        action_layout = QHBoxLayout(action_row)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(AppStyles.get_spacing(1))
        action_layout.setAlignment(Qt.AlignVCenter)
        layout.addWidget(action_row)

        if config.show_add:
            btn_add = self._create_labeled_action_button(
                'btn_add', 'btn_add', self.translator.tr('btn_add'),
                style_class='success', icon_only=False
            )
            if 'add' in callbacks:
                btn_add.clicked.connect(callbacks['add'])
            action_layout.addWidget(btn_add)
            self.buttons['btn_add'] = btn_add

        if config.show_edit:
            btn_edit = self._create_labeled_action_button(
                'btn_edit', 'btn_edit', self.translator.tr('btn_edit'), icon_only=True
            )
            if 'edit' in callbacks:
                btn_edit.clicked.connect(callbacks['edit'])
            action_layout.addWidget(btn_edit)
            self.buttons['btn_edit'] = btn_edit

        if config.show_delete:
            btn_delete = self._create_labeled_action_button(
                'btn_delete', 'btn_delete', self.translator.tr('btn_delete'),
                style_class='danger', icon_only=True
            )
            if 'delete' in callbacks:
                btn_delete.clicked.connect(callbacks['delete'])
            action_layout.addWidget(btn_delete)
            self.buttons['btn_delete'] = btn_delete

        if config.show_refresh:
            btn_refresh = self._create_labeled_action_button(
                'btn_refresh', 'btn_refresh', self.translator.tr('btn_refresh'), icon_only=True
            )
            if 'refresh' in callbacks:
                btn_refresh.clicked.connect(callbacks['refresh'])
            action_layout.addWidget(btn_refresh)
            self.buttons['btn_refresh'] = btn_refresh

        return widget

    def _create_page_specific_section(self, parent: QWidget,
                                      buttons: List[ButtonConfig],
                                      callbacks: Dict[str, Callable]) -> QWidget:
        """Create frequent page actions and route advanced work to More."""
        widget = QWidget(parent)
        widget.setObjectName('toolbarContextGroup')
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        caption = QLabel(self.translator.tr('toolbar_workspace', default='Workspace'))
        caption.setObjectName('toolbarGroupLabel')
        self.buttons['toolbar_workspace_label'] = caption
        layout.addWidget(caption)
        action_row = QWidget(widget)
        action_layout = QHBoxLayout(action_row)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(AppStyles.get_spacing(1))
        action_layout.setAlignment(Qt.AlignVCenter)
        layout.addWidget(action_row)

        for btn_config in buttons:
            if not btn_config.visible:
                continue
            label = self.translator.tr(btn_config.key)
            callback = btn_config.callback or callbacks.get(btn_config.icon_key)
            if btn_config.key in self.TERTIARY_ACTION_KEYS:
                if self.more_menu is None:
                    continue
                action = QAction(get_icon(btn_config.icon_key, 18), label, self.more_menu)
                action.setToolTip(label)
                action.setProperty('actionKey', btn_config.key)
                action.setProperty('iconName', btn_config.icon_key)
                action.setEnabled(btn_config.enabled)
                if callback:
                    action.triggered.connect(callback)
                self.more_menu.addAction(action)
                self.menu_actions[btn_config.key] = action
                continue

            show_label = bool(btn_config.style_class == 'primary' or
                              btn_config.key in {'btn_view_attachments', 'btn_preview_content'})
            btn = self._create_labeled_action_button(
                btn_config.icon_key, btn_config.key, label,
                style_class=btn_config.style_class, icon_only=not show_label
            )
            btn.setEnabled(btn_config.enabled)
            if callback:
                btn.clicked.connect(callback)
            action_layout.addWidget(btn)
            self.buttons[btn_config.icon_key] = btn

        return widget

    def _create_labeled_action_button(self, icon_key: str, action_key: str,
                                      label: str, style_class: Optional[str] = None,
                                      icon_only: bool = True) -> QPushButton:
        """Create a consistent toolbar action with an optional visible label."""
        button = QPushButton()
        button.setObjectName('toolbarActionButton')
        button.setProperty('actionKey', action_key)
        button.setProperty('iconName', icon_key)
        button.setProperty('toolbarRole', 'primary' if style_class in {'primary', 'success'} else 'secondary')
        if style_class:
            # Keep the toolbar on the shared stylesheet path. Applying the
            # legacy dialog button stylesheet inline adds large padding and
            # overrides the compact toolbar geometry.
            button.setProperty('toolbarVariant', style_class)
        icon = get_icon(icon_key, 18, use_white=style_class in {
            'primary', 'success', 'danger', 'purple', 'warning'
        })
        if not icon.isNull():
            button.setIcon(icon)
            button.setIconSize(QSize(18, 18))
        if not icon_only:
            button.setText(label)
            button.setProperty('iconOnly', False)
            button.setFixedWidth(max(96, len(label) * 8 + 50))
            button.setFixedHeight(38)
        else:
            button.setProperty('iconOnly', True)
            button.setFixedSize(40, 38)
        button.setToolTip(label)
        button.setAccessibleName(label)
        button.setStyleSheet(AppStyles.get_table_toolbar_action_style(
            style_class, icon_only, object_name='toolbarActionButton'
        ))
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # Dynamic-property selectors need a repolish before the widget is
        # measured; otherwise the generic QPushButton padding wins at startup.
        button.style().unpolish(button)
        button.style().polish(button)
        # Apply geometry after stylesheet polish; Qt style rules can otherwise
        # replace fixed dimensions with the generic QPushButton size hint.
        if icon_only:
            button.setFixedSize(40, 38)
        else:
            button.setFixedWidth(max(96, len(label) * 8 + 50))
            button.setFixedHeight(38)
        return button

    def _create_export_section(self, parent: QWidget, config: ToolbarConfig,
                              callbacks: Dict[str, Callable]) -> QWidget:
        """Create export buttons section"""
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        caption = QLabel(self.translator.tr('toolbar_output', default='Output'))
        caption.setObjectName('toolbarGroupLabel')
        self.buttons['toolbar_output_label'] = caption
        layout.addWidget(caption)
        action_row = QWidget(widget)
        action_layout = QHBoxLayout(action_row)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(AppStyles.get_spacing(1))
        action_layout.setAlignment(Qt.AlignVCenter)
        layout.addWidget(action_row)

        # Unified export button (with preview dialog)
        if config.show_export_unified:
            btn_export = self._create_labeled_action_button(
                'btn_export', 'btn_export', self.translator.tr('btn_export'),
                style_class='purple', icon_only=False
            )
            if 'export_unified' in callbacks:
                btn_export.clicked.connect(callbacks['export_unified'])
            action_layout.addWidget(btn_export)
            self.buttons['btn_export_unified'] = btn_export

        # Output actions share the same compact icon-only dimensions. The
        # unified export action remains the labeled primary output control.
        output_actions = [
            ('btn_print', 'print', 'print'),
            ('btn_export_pdf', 'export_pdf', 'export_pdf'),
            ('btn_export_csv', 'export_csv', 'export_csv'),
            ('btn_export_excel', 'export_excel', 'export_excel'),
            ('btn_export_word', 'export_word', 'export_word'),
        ]
        visibility = {
            'print': config.show_print,
            'export_pdf': config.show_pdf,
            'export_csv': config.show_csv,
            'export_excel': config.show_excel,
            'export_word': config.show_word,
        }
        for button_key, icon_key, callback_key in output_actions:
            if not visibility[callback_key]:
                continue
            button = self._create_labeled_action_button(
                icon_key, button_key, self.translator.tr(button_key), icon_only=True
            )
            if callback_key in callbacks:
                button.clicked.connect(callbacks[callback_key])
            action_layout.addWidget(button)
            self.buttons[button_key] = button

        return widget

    def _create_group_separator(self) -> QFrame:
        """Create a quiet separator between action priority groups."""
        sep = QFrame()
        sep.setObjectName('toolbarGroupSeparator')
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Plain)
        sep.setFixedHeight(24)
        sep.setStyleSheet(f"color: {AppStyles.get_color('BORDER')};")
        return sep

    def _create_separator(self) -> QFrame:
        """Backward-compatible separator helper used by older callers."""
        return self._create_group_separator()

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

    def _refresh_toolbar_button(self, button: QPushButton, icon_key: str, label: str):
        """Refresh an action without losing its label/priority treatment."""
        if not button:
            return
        variant = button.property('toolbarVariant')
        use_white = variant in {'primary', 'success', 'danger', 'purple', 'warning'}
        icon = get_icon(icon_key, 18, use_white=use_white)
        if not icon.isNull():
            button.setIcon(icon)
            button.setIconSize(QSize(18, 18))
        if button.property('iconOnly') is False:
            button.setText(label)
            button.setToolTip(label)
            button.setAccessibleName(label)
            button.setFixedWidth(max(96, len(label) * 8 + 50))
            button.setFixedHeight(38)
        else:
            button.setText('')
            button.setProperty('iconOnly', True)
            button.setToolTip(label)
            button.setAccessibleName(label)
            button.setFixedSize(40, 38)
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.setStyleSheet(AppStyles.get_table_toolbar_action_style(
            variant, button.property('iconOnly') is True,
            object_name='toolbarActionButton'
        ))
        button.style().unpolish(button)
        button.style().polish(button)
        if button.property('iconOnly') is True:
            button.setFixedSize(40, 38)
        else:
            button.setFixedWidth(max(96, len(label) * 8 + 50))
            button.setFixedHeight(38)

    def refresh_translations(self):
        """Refresh labels, menu actions, direction, and icons after language changes."""
        group_labels = {
            'toolbar_records_label': ('toolbar_records', 'Records'),
            'toolbar_workspace_label': ('toolbar_workspace', 'Workspace'),
            'toolbar_output_label': ('toolbar_output', 'Output'),
            'toolbar_view_label': ('toolbar_view', 'View'),
        }
        for label_key, (translation_key, fallback) in group_labels.items():
            label_widget = self.buttons.get(label_key)
            if label_widget:
                label_widget.setText(self.translator.tr(translation_key, default=fallback))

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
            'btn_clear_search': 'btn_clear',
            'btn_clear': 'btn_clear',
            'btn_set_header': 'btn_set_header',
        }

        for btn_key, icon_key in button_configs.items():
            btn = self.buttons.get(btn_key)
            if btn and isinstance(btn, QPushButton):
                self._refresh_toolbar_button(
                    btn, icon_key, self.translator.tr(icon_key, default=btn.toolTip())
                )

        # Refresh visible page-specific actions by their semantic action key.
        for btn_key, btn in self.buttons.items():
            if not isinstance(btn, QPushButton) or btn_key in button_configs:
                continue
            action_key = btn.property('actionKey') or btn_key
            icon_key = btn.property('iconName') or btn_key
            label = self.translator.tr(action_key, default=btn.toolTip())
            self._refresh_toolbar_button(btn, icon_key, label)

        for action_key, action in self.menu_actions.items():
            label = self.translator.tr(action_key, default=action.text())
            action.setText(label)
            action.setToolTip(label)
            action.setIcon(get_icon(action.property('iconName') or 'more', 18))

        if self.more_button:
            self.more_button.setText(self.translator.tr('toolbar_more', default='More'))
            self.more_button.setToolTip(
                self.translator.tr('toolbar_more_hint', default='More table actions')
            )
            self.more_button.setAccessibleName(self.more_button.toolTip())
            self.more_button.setIcon(get_icon('more', 18))

        search_label = self.buttons.get('search_label')
        if search_label:
            search_label.setText(self.translator.tr('lbl_search') + ':')
        search_edit = self.buttons.get('search_edit')
        if search_edit:
            search_edit.setPlaceholderText(self.translator.tr('msg_type_to_search'))
        date_from_label = self.buttons.get('date_from_label')
        if date_from_label:
            date_from_label.setText(self.translator.tr('lbl_date_from') + ':')
        date_to_label = self.buttons.get('date_to_label')
        if date_to_label:
            date_to_label.setText(self.translator.tr('lbl_date_to') + ':')
        date_filter_group = self.buttons.get('date_filter_group')
        if date_filter_group:
            date_filter_group.setTitle(self.translator.tr('lbl_date_filter'))

        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        for widget in self.buttons.values():
            if hasattr(widget, 'setLayoutDirection'):
                widget.setLayoutDirection(direction)
        if self.more_button:
            self.more_button.setLayoutDirection(direction)
