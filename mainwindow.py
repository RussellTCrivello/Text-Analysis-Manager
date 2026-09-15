"""
Enhanced Main Window with Settings and Translations
"""
import sys
import io

# Suppress console window on Windows when running as script (not compiled)
if sys.platform == 'win32' and not getattr(sys, 'frozen', False):
    # Hide console window when running as Python script
    import ctypes
    # SW_HIDE = 0
    SW_HIDE = 0
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    # Get console window handle
    console_window = kernel32.GetConsoleWindow()
    if console_window:
        # Hide the console window immediately
        user32.ShowWindow(console_window, SW_HIDE)

# Set UTF-8 encoding for stdout/stderr on Windows
if sys.platform == 'win32':
    # Check if stdout/stderr exist and have encoding attribute (may be None in compiled executables)
    if sys.stdout is not None and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    elif sys.stdout is not None and not hasattr(sys.stdout, 'encoding'):
        # stdout exists but has no encoding attribute (compiled executable)
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass  # If buffer doesn't exist, skip
    
    if sys.stderr is not None and hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    elif sys.stderr is not None and not hasattr(sys.stderr, 'encoding'):
        # stderr exists but has no encoding attribute (compiled executable)
        try:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass  # If buffer doesn't exist, skip

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMessageBox, QStatusBar, QMenuBar, QMenu, QAction, QDialog,
    QLabel, QPushButton, QLineEdit, QFrame, QSizePolicy, QButtonGroup
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from db.db_config import DatabaseConfig
# Import from new modular tab structure
from tabs.sources_tab import SourcesTab
from tabs.contents_tab import ContentsTab
from tabs.analysis_tab import ContentAnalysisTab
from tabs.all_data_tab import AllDataDisplayTab
from tabs.timeline_tab import TimelineTab
from widgets.reports_tab import ReportsTab
from styles.styles import AppStyles
from translations.translations import TranslationManager
from dialogs.settings_dialog import SettingsDialog
from config.config_manager import ConfigManager
from dialogs.backup_restore_dialog import BackupRestoreDialog
from dialogs.reset_dialog import ResetDialog
from icons.icon_manager import get_icon
from utils.logger import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Persistent application shell for the Text Analysis research platform."""
    
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.translator = TranslationManager(QApplication.instance())
        
        # Initialize AppStyles with saved config (theme + direction)
        # This MUST be called before any stylesheet is generated
        AppStyles.initialize()
        
        # Apply theme to application palette
        app = QApplication.instance()
        if app:
            AppStyles.apply_theme_to_app(app)
        
        # Set application-level direction BEFORE creating widgets
        # This ensures new widgets inherit the correct direction
        self._set_initial_direction()
        
        # Initialize database (create tables if needed)
        success, error_msg = DatabaseConfig.initialize_database()
        if not success:
            error_text = f"{self.translator.tr('msg_db_init_failed')}\n\n"
            if error_msg:
                error_text += f"{self.translator.tr('msg_error_prefix')}: {error_msg}\n\n"
            error_text += f"{self.translator.tr('msg_db_location')}: {DatabaseConfig.get_db_path()}\n\n"
            error_text += f"{self.translator.tr('msg_please_check')}\n"
            error_text += f"1. {self.translator.tr('msg_check_permissions')}\n"
            error_text += f"2. {self.translator.tr('msg_check_disk_space')}\n"
            error_text += f"3. {self.translator.tr('msg_check_antivirus')}"
            
            QMessageBox.critical(
                self,
                self.translator.tr('msg_connection_error'),
                error_text
            )
            sys.exit(1)
        
        self.setup_ui()
        
        # Apply language direction AFTER UI is created to ensure all widgets get the direction
        self.apply_language_direction()
        
        # IMPORTANT: Refresh translations on all tabs to ensure proper icon/button sizing
        # This is needed because setup_icon_button sets fixed sizes during refresh_translations
        # Without this, icons appear large at startup until language is changed
        # Use deferred execution to prevent visual flickering during startup
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self._initial_translations_refresh)
        
        # Enable persisted accessibility settings (focus indicators, high
        # contrast, and screen-reader hooks) for the main window.
        try:
            self._register_accessibility_shortcuts()
        except Exception as e:
            logger.warning(f"Could not initialize accessibility features: {e}")

        # Test database connection
        if not DatabaseConfig.test_connection():
            QMessageBox.critical(
                self,
                self.translator.tr('msg_connection_error'),
                self.translator.tr('msg_connection_failed')
            )
            sys.exit(1)
    
    def _set_application_icon(self):
        """Set the application icon for window title bar and taskbar"""
        from pathlib import Path
        
        # Try multiple possible icon locations
        possible_paths = []
        
        # Use path_utils for correct bundle path when installed
        try:
            from utils.path_utils import get_bundle_dir
            bundle_dir = get_bundle_dir()
            possible_paths.extend([
                bundle_dir / 'app_icon.ico',
                bundle_dir / 'icons' / 'app_icon.ico',
                bundle_dir / 'icons' / 'images' / 'app_logo.svg',
            ])
        except Exception:
            pass
        
        # Development paths
        script_dir = Path(__file__).parent.resolve()
        possible_paths.extend([
            script_dir / 'app_icon.ico',
            script_dir / 'icons' / 'images' / 'app_logo.svg',
        ])
        
        # Try each path
        for icon_path in possible_paths:
            if icon_path.exists():
                icon = QIcon(str(icon_path))
                if not icon.isNull():
                    self.setWindowIcon(icon)
                    # Also set on QApplication for taskbar grouping
                    app = QApplication.instance()
                    if app:
                        app.setWindowIcon(icon)
                    logger.debug(f"Application icon set from: {icon_path}")
                    return
        
        logger.warning("Application icon not found in expected locations")
    
    def _set_initial_direction(self):
        """Set initial direction at application level before widgets are created"""
        current_lang = self.translator.current_language
        is_rtl = current_lang == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        
        # Set application-level direction so new widgets inherit it
        app = QApplication.instance()
        if app:
            app.setLayoutDirection(direction)
        
        # Set on main window
        self.setLayoutDirection(direction)
        
        # Update global direction in AppStyles
        AppStyles.set_layout_direction('rtl' if is_rtl else 'ltr')
    
    def apply_language_direction(self):
        """Apply RTL/LTR based on current language"""
        current_lang = self.translator.current_language
        is_rtl = current_lang == 'ar'
        
        if is_rtl:
            direction = Qt.RightToLeft
        else:
            direction = Qt.LeftToRight
        
        # Update global direction in AppStyles and refresh styles
        AppStyles.refresh_for_language(current_lang)
        
        # Apply to application
        self.setLayoutDirection(direction)
        if QApplication.instance():
            QApplication.instance().setLayoutDirection(direction)
        
        # Apply to menu bar
        menubar = self.menuBar()
        if menubar:
            menubar.setLayoutDirection(direction)
        
        # Apply to status bar
        statusbar = self.statusBar()
        if statusbar:
            statusbar.setLayoutDirection(direction)
        
        # Apply to central widget and all children
        central = self.centralWidget()
        if central:
            central.setLayoutDirection(direction)
            self._apply_direction_recursive(central, direction)
    
    def _apply_direction_recursive(self, widget, direction):
        """Recursively apply layout direction to all child widgets"""
        from PyQt5.QtWidgets import QWidget
        
        for child in widget.findChildren(QWidget):
            child.setLayoutDirection(direction)
    
    def _initial_translations_refresh(self):
        """
        Refresh translations on all tabs after initial setup.
        This ensures proper icon/button sizing at startup.
        
        The issue: setup_icon_button() sets proper fixed sizes during toolbar refresh,
        but this only happens during language change (via refresh_ui -> refresh_translations).
        At startup, the buttons are created but not properly sized until this refresh.
        """
        tabs = [
            getattr(self, 'sources_tab', None),
            getattr(self, 'contents_tab', None),
            getattr(self, 'analysis_tab', None),
            getattr(self, 'all_data_tab', None),
            getattr(self, 'timeline_tab', None),
            getattr(self, 'reports_tab', None),
        ]
        
        for tab in tabs:
            if tab and hasattr(tab, 'refresh_translations'):
                try:
                    tab.refresh_translations()
                except Exception as e:
                    logger.warning(f"Error refreshing translations for tab: {e}")

    def _active_tab(self):
        """Return the currently visible tab, if the UI is ready."""
        return getattr(self, 'tab_widget', None).currentWidget() if hasattr(self, 'tab_widget') else None

    def _run_active_tab_action(self, method_name: str):
        """Invoke a supported action on the active tab without swallowing errors."""
        tab = self._active_tab()
        method = getattr(tab, method_name, None) if tab else None
        if callable(method):
            method()

    def _focus_active_search(self):
        """Focus the active tab's search field."""
        tab = self._active_tab()
        search = getattr(getattr(tab, 'toolbar_factory', None), 'get_search_edit', lambda: None)()
        if search:
            search.setFocus()
            search.selectAll()

    def _select_first_record(self):
        tab = self._active_tab()
        table = getattr(tab, 'data_table', None) if tab else None
        if table and table.rowCount():
            table.setCurrentCell(0, 0)

    def _select_last_record(self):
        tab = self._active_tab()
        table = getattr(tab, 'data_table', None) if tab else None
        if table and table.rowCount():
            table.setCurrentCell(table.rowCount() - 1, 0)

    def _save_active_view(self):
        """Save the active view when it exposes a real save workflow."""
        tab = self._active_tab()
        if tab and callable(getattr(tab, 'save_report', None)):
            tab.save_report()

    def _navigate_active_page(self, method_name: str):
        """Navigate the active tab's pagination control, when present."""
        tab = self._active_tab()
        pagination = getattr(tab, 'pagination', None) if tab else None
        method = getattr(pagination, method_name, None) if pagination else None
        if callable(method):
            method()

    def _close_active_dialog(self):
        """Close the active modal dialog using its normal reject path."""
        from PyQt5.QtWidgets import QDialog
        active = QApplication.activeWindow()
        if isinstance(active, QDialog):
            active.reject()

    def _register_accessibility_shortcuts(self):
        """Register only shortcuts backed by observable application actions."""
        try:
            from utils.accessibility import get_accessibility_manager
            manager = get_accessibility_manager()
            manager.setup_for_window(self, {
                'help': self.show_help,
                'quit': self.close,
                'save': self._save_active_view,
                'new': lambda: self._run_active_tab_action('add_record'),
                'edit': lambda: self._run_active_tab_action('edit_record'),
                'delete': lambda: self._run_active_tab_action('delete_record'),
                'search': self._focus_active_search,
                'refresh': lambda: self._run_active_tab_action('load_data'),
                'print': lambda: self._run_active_tab_action('print_data'),
                'close_dialog': self._close_active_dialog,
                'first_record': self._select_first_record,
                'last_record': self._select_last_record,
                'prev_page': lambda: self._navigate_active_page('go_to_previous'),
                'next_page': lambda: self._navigate_active_page('go_to_next'),
            })
            self.accessibility_manager = manager
        except Exception as e:
            logger.warning(f"Could not register keyboard shortcuts: {e}")

    def setup_ui(self):
        """Build the product shell around the existing functional workspaces.

        The tab pages remain the source of truth for CRUD, import/export, analysis,
        and reporting workflows.  They are presented as workspaces in a persistent
        navigation shell so users can move through the product without losing the
        established workflows or keyboard shortcuts.
        """
        self.setWindowTitle(self.translator.tr('app_title'))
        self.setObjectName('mainWindow')
        self._set_application_icon()
        self.setStyleSheet(AppStyles.get_stylesheet())
        self.setMinimumSize(780, 560)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setDockNestingEnabled(True)
        self.menuBar().setObjectName('mainMenuBar')
        self.menuBar().setNativeMenuBar(False)
        self.create_menu_bar()

        central_widget = QWidget()
        central_widget.setObjectName('appShell')
        self.setCentralWidget(central_widget)
        root = QVBoxLayout(central_widget)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Persistent product header: identity, global search, and global actions.
        header = QFrame()
        header.setObjectName('appHeader')
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 18, 24, 16)
        header_layout.setSpacing(16)

        brand = QFrame()
        brand.setObjectName('brandBlock')
        brand_layout = QHBoxLayout(brand)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(10)
        brand_mark = QLabel()
        brand_mark.setObjectName('brandMark')
        brand_mark.setPixmap(get_icon('app_logo', 30).pixmap(30, 30))
        self.brand_mark = brand_mark
        brand_mark.setFixedSize(34, 34)
        brand_mark.setAccessibleName(self.translator.tr('app_title'))
        brand_layout.addWidget(brand_mark)
        brand_copy_widget = QWidget()
        brand_copy_widget.setObjectName('brandCopy')
        brand_copy = QVBoxLayout(brand_copy_widget)
        brand_copy.setContentsMargins(0, 0, 0, 0)
        brand_copy.setSpacing(1)
        self.brand_title = QLabel(self.translator.tr('app_title'))
        self.brand_title.setObjectName('brandTitle')
        self.brand_subtitle = QLabel(self.translator.tr('shell_subtitle', default='Research workspace'))
        self.brand_subtitle.setObjectName('brandSubtitle')
        brand_copy.addWidget(self.brand_title)
        brand_copy.addWidget(self.brand_subtitle)
        brand_layout.addWidget(brand_copy_widget)
        self.brand_copy_widget = brand_copy_widget
        header_layout.addWidget(brand, 0)

        self.global_search = QLineEdit()
        self.global_search.setObjectName('globalSearch')
        self.global_search.setPlaceholderText(
            self.translator.tr('search_global_placeholder', default='Search the research workspace')
        )
        search_action = self.global_search.addAction(get_icon('search', 18), QLineEdit.LeadingPosition)
        search_action.setProperty('iconName', 'search')
        self.global_search.setClearButtonEnabled(False)
        self.global_search_clear_action = self.global_search.addAction(
            get_icon('clear', 16), QLineEdit.TrailingPosition
        )
        self.global_search_clear_action.setProperty('iconName', 'clear')
        self.global_search_clear_action.setToolTip(self._tr('btn_clear', 'Clear search'))
        self.global_search_clear_action.triggered.connect(self.global_search.clear)
        self.global_search.setMinimumWidth(260)
        self.global_search.setMaximumWidth(560)
        self.global_search.setAccessibleName(
            self.translator.tr('search_global_placeholder', default='Global search')
        )
        self.global_search.setToolTip(
            self.translator.tr('search_global_hint', default='Search the active workspace')
        )
        self.global_search.textChanged.connect(self._on_global_search_changed)
        self.global_search.returnPressed.connect(self._focus_active_search)
        header_layout.addWidget(self.global_search, 1)

        self.quick_add_button = QPushButton(get_icon('add', 18), self.translator.tr('btn_add_new'))
        self.quick_add_button.setObjectName('headerPrimaryAction')
        self.quick_add_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.quick_add_button.setMinimumWidth(128)
        self.quick_add_button.setMaximumWidth(156)
        self.quick_add_button.setToolTip(self.translator.tr('btn_add_new'))
        self.quick_add_button.setAccessibleName(self.translator.tr('btn_add_new'))
        self.quick_add_button.clicked.connect(lambda: self._run_active_tab_action('add_record'))
        header_layout.addWidget(self.quick_add_button, 0)

        self.header_settings_button = self._create_icon_button(
            'settings', self.translator.tr('menu_settings')
        )
        self.header_settings_button.clicked.connect(self.show_settings)
        header_layout.addWidget(self.header_settings_button, 0)
        self.header_help_button = self._create_icon_button(
            'help', self.translator.tr('help_title', default='Help')
        )
        self.header_help_button.clicked.connect(self.show_help)
        header_layout.addWidget(self.header_help_button, 0)
        root.addWidget(header)

        body = QFrame()
        body.setObjectName('shellBody')
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        self.sidebar = self._build_sidebar()
        body_layout.addWidget(self.sidebar, 0)

        workspace = QFrame()
        workspace.setObjectName('workspaceArea')
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(24, 18, 24, 18)
        workspace_layout.setSpacing(14)

        context_header = QFrame()
        context_header.setObjectName('contextHeader')
        context_layout = QHBoxLayout(context_header)
        context_layout.setContentsMargins(0, 0, 0, 0)
        context_layout.setSpacing(12)
        context_copy = QVBoxLayout()
        context_copy.setContentsMargins(0, 0, 0, 0)
        context_copy.setSpacing(3)
        self.breadcrumb_label = QLabel()
        self.breadcrumb_label.setObjectName('breadcrumbLabel')
        self.workspace_title = QLabel()
        self.workspace_title.setObjectName('workspaceTitle')
        self.workspace_subtitle = QLabel()
        self.workspace_subtitle.setObjectName('workspaceSubtitle')
        self.workspace_subtitle.setWordWrap(True)
        context_copy.addWidget(self.breadcrumb_label)
        context_copy.addWidget(self.workspace_title)
        context_copy.addWidget(self.workspace_subtitle)
        context_layout.addLayout(context_copy, 1)
        self.context_refresh_button = self._create_icon_button(
            'refresh', self.translator.tr('btn_refresh', default='Refresh workspace')
        )
        self.context_refresh_button.clicked.connect(lambda: self._run_active_tab_action('load_data'))
        context_layout.addWidget(self.context_refresh_button, 0, Qt.AlignTop)
        workspace_layout.addWidget(context_header)

        # Pages continue to be real, fully functional widgets; the tab strip is
        # hidden because the sidebar is now the primary navigation model.
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName('workspacePages')
        self.tab_widget.tabBar().hide()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setElideMode(Qt.ElideNone)
        self.tab_widget.setUsesScrollButtons(False)
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.sources_tab = SourcesTab(self, self.translator)
        self.tab_widget.addTab(self.sources_tab, self.translator.tr('tab_sources'))
        self.contents_tab = ContentsTab(self, self.translator)
        self.tab_widget.addTab(self.contents_tab, self.translator.tr('tab_contents'))
        self.analysis_tab = ContentAnalysisTab(self, self.translator)
        self.tab_widget.addTab(self.analysis_tab, self.translator.tr('tab_analysis'))
        self.all_data_tab = AllDataDisplayTab(self, self.translator)
        self.tab_widget.addTab(self.all_data_tab, self.translator.tr('tab_all_data'))
        self.timeline_tab = TimelineTab(self, self.translator)
        self.tab_widget.addTab(self.timeline_tab, self.translator.tr('tab_timeline'))
        self.reports_tab = ReportsTab(self, self.translator)
        self.tab_widget.addTab(self.reports_tab, self.translator.tr('tab_reports'))
        self._compact_page_headers()
        workspace_layout.addWidget(self.tab_widget, 1)
        body_layout.addWidget(workspace, 1)
        root.addWidget(body, 1)

        self._create_status_bar()
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self._update_workspace_context(0)
        self.statusBar().showMessage(self.translator.tr('msg_ready'))

    def _tr(self, key: str, default: str) -> str:
        """Translate a shell label while remaining compatible with older catalogs."""
        return self.translator.tr(key, default=default)

    def _create_icon_button(self, icon_name: str, label: str) -> QPushButton:
        """Create an accessible icon-only button using a graphical asset."""
        button = QPushButton()
        button.setObjectName('iconButton')
        button.setIcon(get_icon(icon_name, 18))
        button.setIconSize(button.iconSize())
        button.setFixedSize(38, 38)
        button.setToolTip(label)
        button.setAccessibleName(label)
        button.setProperty('iconName', icon_name)
        return button

    def _create_nav_button(self, index: int, icon_name: str, label: str) -> QPushButton:
        """Create a primary-navigation button with a stable tab target."""
        button = QPushButton()
        button.setObjectName('navButton')
        button.setCheckable(True)
        button.setProperty('navIndex', index)
        button.setIcon(get_icon(icon_name, 19))
        button.setIconSize(button.iconSize())
        button.setText(label)
        button.setToolTip(label)
        button.setAccessibleName(label)
        button.clicked.connect(lambda checked=False, i=index: self._set_active_page(i))
        self._nav_buttons.append(button)
        return button

    def _build_sidebar(self) -> QFrame:
        """Build the persistent workspace navigation rail."""
        self._nav_buttons = []
        self._sidebar_collapsed = False
        self._page_meta = [
            ('tab_sources', 'newspaper', 'Source registry', 'Collect and organize the records that ground your research.'),
            ('tab_contents', 'document', 'Content workspace', 'Review source material, metadata, tags, and attachments together.'),
            ('tab_analysis', 'statistics', 'Analysis workspace', 'Inspect structured findings and relationship context.'),
            ('tab_all_data', 'table', 'Data management', 'Work across tables with validated, exportable records.'),
            ('tab_timeline', 'calendar', 'Chronology', 'Understand events, dates, and research activity over time.'),
            ('tab_reports', 'reports', 'Reporting studio', 'Build, preview, and export analysis reports.'),
        ]
        sidebar = QFrame()
        sidebar.setObjectName('appSidebar')
        sidebar.setMinimumWidth(232)
        sidebar.setMaximumWidth(232)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 16, 14, 16)
        sidebar_layout.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(4, 0, 4, 12)
        top_row.setSpacing(6)
        nav_label = QLabel(self._tr('shell_navigation', 'Workspace'))
        nav_label.setObjectName('sidebarSectionLabel')
        top_row.addWidget(nav_label, 1)
        self.sidebar_collapse_button = self._create_icon_button(
            'chevron_left', self._tr('shell_collapse_sidebar', 'Collapse navigation')
        )
        self.sidebar_collapse_button.setObjectName('sidebarCollapseButton')
        self.sidebar_collapse_button.clicked.connect(self._toggle_sidebar)
        top_row.addWidget(self.sidebar_collapse_button, 0)
        sidebar_layout.addLayout(top_row)

        self.sidebar_section_label = nav_label
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for index, (key, icon_name, _title, _description) in enumerate(self._page_meta):
            button = self._create_nav_button(index, icon_name, self.translator.tr(key))
            self.nav_group.addButton(button, index)
            sidebar_layout.addWidget(button)

        sidebar_layout.addSpacing(18)
        data_label = QLabel(self._tr('shell_tools', 'Operations'))
        data_label.setObjectName('sidebarSectionLabel')
        sidebar_layout.addWidget(data_label)
        self.operations_label = data_label
        self.attachments_nav_button = self._create_sidebar_action(
            'attach_files', self.translator.tr('menu_manage_attachments'), self.show_attachment_manager
        )
        sidebar_layout.addWidget(self.attachments_nav_button)
        self.backup_nav_button = self._create_sidebar_action(
            'create_backup', self.translator.tr('menu_backup_restore'), self.show_backup_restore
        )
        sidebar_layout.addWidget(self.backup_nav_button)
        self.import_nav_button = self._create_sidebar_action(
            'import_data', self._tr('menu_import_data', 'Import data'), self.show_import_dialog
        )
        sidebar_layout.addWidget(self.import_nav_button)
        sidebar_layout.addStretch(1)

        divider = QFrame()
        divider.setObjectName('sidebarDivider')
        divider.setFrameShape(QFrame.HLine)
        divider.setFixedHeight(1)
        sidebar_layout.addWidget(divider)
        self.sidebar_divider = divider
        self.settings_nav_button = self._create_sidebar_action(
            'settings', self.translator.tr('menu_settings'), self.show_settings
        )
        sidebar_layout.addWidget(self.settings_nav_button)
        self.help_nav_button = self._create_sidebar_action(
            'help', self.translator.tr('help_title', default='Help and shortcuts'), self.show_help
        )
        sidebar_layout.addWidget(self.help_nav_button)
        return sidebar

    def _create_sidebar_action(self, icon_name: str, label: str, callback) -> QPushButton:
        button = QPushButton()
        button.setObjectName('sidebarAction')
        button.setIcon(get_icon(icon_name, 18))
        button.setIconSize(button.iconSize())
        button.setText(label)
        button.setToolTip(label)
        button.setAccessibleName(label)
        button.clicked.connect(callback)
        return button

    def _create_status_bar(self):
        """Add a quiet status region without replacing the existing status API."""
        status = self.statusBar()
        status.setObjectName('appStatusBar')
        status.setSizeGripEnabled(False)
        self.status_context = QLabel(self._tr('shell_status_ready', 'Workspace ready'))
        self.status_context.setObjectName('statusContext')
        status.addPermanentWidget(self.status_context)

    def _compact_page_headers(self):
        """Let the shell own page hierarchy while retaining page refresh bindings."""
        for tab in (
            self.sources_tab, self.contents_tab, self.analysis_tab,
            self.all_data_tab, self.timeline_tab, self.reports_tab,
        ):
            title = getattr(tab, 'title_label', None)
            if title is not None:
                title.hide()

    def _set_active_page(self, index: int):
        if not hasattr(self, 'tab_widget') or not 0 <= index < self.tab_widget.count():
            return
        self.tab_widget.setCurrentIndex(index)
        self._update_workspace_context(index)

    def _on_global_search_changed(self, text: str):
        """Route the shell search into the active workspace's real search control."""
        tab = self._active_tab()
        toolbar = getattr(tab, 'toolbar_factory', None) if tab else None
        search = toolbar.get_search_edit() if toolbar and hasattr(toolbar, 'get_search_edit') else None
        if search is not None and search is not self.global_search:
            if search.text() != text:
                search.setText(text)
            self.status_context.setText(
                self._tr('shell_searching', 'Searching active workspace') if text else
                self._tr('shell_status_ready', 'Workspace ready')
            )
            return
        # Timeline and other specialized workspaces expose a named search field.
        specialized_search = getattr(tab, 'search_input', None) if tab else None
        if specialized_search is not None and specialized_search is not self.global_search:
            if specialized_search.text() != text:
                specialized_search.setText(text)
            self.status_context.setText(
                self._tr('shell_searching', 'Searching active workspace') if text else
                self._tr('shell_status_ready', 'Workspace ready')
            )
            return
        self.status_context.setText(
            self._tr('shell_search_unavailable', 'Search is not available in this workspace')
            if text else self._tr('shell_status_ready', 'Workspace ready')
        )

    def _focus_global_search(self):
        self.global_search.setFocus()
        self.global_search.selectAll()

    def _toggle_sidebar(self):
        """Collapse navigation to an icon rail without losing accessible labels."""
        self._sidebar_collapsed = not self._sidebar_collapsed
        collapsed = self._sidebar_collapsed
        self.sidebar.setMinimumWidth(72 if collapsed else 232)
        self.sidebar.setMaximumWidth(72 if collapsed else 232)
        self.sidebar_collapse_button.setIcon(get_icon('chevron_right' if collapsed else 'chevron_left', 18))
        self.sidebar_collapse_button.setToolTip(
            self._tr('shell_expand_sidebar', 'Expand navigation') if collapsed else
            self._tr('shell_collapse_sidebar', 'Collapse navigation')
        )
        self.sidebar_collapse_button.setAccessibleName(self.sidebar_collapse_button.toolTip())
        self.sidebar_section_label.setVisible(not collapsed)
        self.operations_label.setVisible(not collapsed)
        self.sidebar_divider.setVisible(not collapsed)
        for button in self._nav_buttons:
            button.setText('' if collapsed else self.translator.tr(self._page_meta[button.property('navIndex')][0]))
            button.setToolTip(self.translator.tr(self._page_meta[button.property('navIndex')][0]))
        for button in (self.attachments_nav_button, self.backup_nav_button, self.import_nav_button,
                       self.settings_nav_button, self.help_nav_button):
            button.setText('' if collapsed else button.toolTip())
        self._refresh_navigation_icons()

    def _refresh_shell_icons(self):
        """Reload every shell asset after theme changes or language refresh."""
        if hasattr(self, 'brand_mark'):
            self.brand_mark.setPixmap(get_icon('app_logo', 30).pixmap(30, 30))
        if hasattr(self, 'global_search'):
            for action in self.global_search.actions():
                icon_name = action.property('iconName') or 'search'
                action.setIcon(get_icon(icon_name, 16 if icon_name == 'clear' else 18))
        if hasattr(self, 'quick_add_button'):
            self.quick_add_button.setIcon(get_icon('add', 18))
        if hasattr(self, 'header_settings_button'):
            self.header_settings_button.setIcon(get_icon('settings', 18))
        if hasattr(self, 'header_help_button'):
            self.header_help_button.setIcon(get_icon('help', 18))
        if hasattr(self, 'context_refresh_button'):
            self.context_refresh_button.setIcon(get_icon('refresh', 18))
        self._refresh_navigation_icons()

    def _refresh_navigation_icons(self):
        """Reload shell icons after theme or language changes."""
        for button, (_, icon_name, _, _) in zip(self._nav_buttons, self._page_meta):
            button.setIcon(get_icon(icon_name, 19))
        self.sidebar_collapse_button.setIcon(
            get_icon('chevron_right' if self._sidebar_collapsed else 'chevron_left', 18)
        )
        action_icons = (
            (self.attachments_nav_button, 'attach_files'),
            (self.backup_nav_button, 'create_backup'),
            (self.import_nav_button, 'import_data'),
            (self.settings_nav_button, 'settings'),
            (self.help_nav_button, 'help'),
        )
        for button, icon_name in action_icons:
            button.setIcon(get_icon(icon_name, 18))

    def _update_workspace_context(self, index: int):
        if not hasattr(self, 'workspace_title') or not self._page_meta:
            return
        index = max(0, min(index, len(self._page_meta) - 1))
        key, _icon, title, description = self._page_meta[index]
        translated_title = self.translator.tr(key)
        self.breadcrumb_label.setText(
            f"{self._tr('shell_breadcrumb', 'Research workspace')}  /  {translated_title}"
        )
        self.workspace_title.setText(translated_title)
        self.workspace_subtitle.setText(self._tr(f'{key}_description', description))
        if hasattr(self, 'status_context'):
            self.status_context.setText(self._tr('shell_status_ready', 'Workspace ready'))
        if hasattr(self, 'quick_add_button'):
            can_add = callable(getattr(self._active_tab(), 'add_record', None))
            self.quick_add_button.setEnabled(can_add)
            self.quick_add_button.setToolTip(
                self.translator.tr('btn_add_new') if can_add else
                self._tr('shell_action_unavailable', 'Not available in this workspace')
            )
        for i, button in enumerate(getattr(self, '_nav_buttons', [])):
            button.setChecked(i == index)
        self._sync_global_search_from_active_tab()

    def _sync_global_search_from_active_tab(self):
        """Keep the global field and the page search in sync on navigation."""
        tab = self._active_tab()
        toolbar = getattr(tab, 'toolbar_factory', None) if tab else None
        search = toolbar.get_search_edit() if toolbar and hasattr(toolbar, 'get_search_edit') else None
        if search is None:
            search = getattr(tab, 'search_input', None) if tab else None
        if search is not None and self.global_search.text() != search.text():
            self.global_search.blockSignals(True)
            self.global_search.setText(search.text())
            self.global_search.blockSignals(False)

    def _apply_responsive_header(self, width: int):
        """Prioritize search and workspace controls at compact window widths."""
        if not hasattr(self, 'brand_copy_widget'):
            return
        compact = width < 1080
        if compact == getattr(self, '_header_compact', False):
            return
        self._header_compact = compact
        self.brand_copy_widget.setVisible(not compact)
        self.quick_add_button.setText('' if compact else self.translator.tr('btn_add_new'))
        self.quick_add_button.setMinimumWidth(40 if compact else 128)
        self.quick_add_button.setMaximumWidth(44 if compact else 156)
        self.quick_add_button.setToolTip(self.translator.tr('btn_add_new'))
        self.quick_add_button.setAccessibleName(self.translator.tr('btn_add_new'))
        self.global_search.setMinimumWidth(180 if compact else 260)
        self.global_search.setMaximumWidth(420 if compact else 560)

    def resizeEvent(self, event):
        """Keep the shell usable on narrow windows while retaining an explicit toggle."""
        super().resizeEvent(event)
        self._apply_responsive_header(event.size().width())
        if hasattr(self, 'sidebar') and event.size().width() < 980 and not self._sidebar_collapsed:
            self._toggle_sidebar()

    def create_menu_bar(self):
        """Create enhanced menu bar"""
        menubar = self.menuBar()
        menubar.clear()  # Clear existing menus before adding new ones
        
        # File menu
        file_menu = menubar.addMenu(self.translator.tr('menu_file'))
        
        exit_action = QAction(get_icon('close', 18), self.translator.tr('menu_exit'), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu(self.translator.tr('menu_view'))
        
        sources_action = QAction(get_icon('newspaper', 18), self.translator.tr('tab_sources'), self)
        sources_action.setShortcut("Ctrl+1")
        sources_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        view_menu.addAction(sources_action)
        
        contents_action = QAction(get_icon('document', 18), self.translator.tr('tab_contents'), self)
        contents_action.setShortcut("Ctrl+2")
        contents_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        view_menu.addAction(contents_action)
        
        analysis_action = QAction(get_icon('statistics', 18), self.translator.tr('tab_analysis'), self)
        analysis_action.setShortcut("Ctrl+3")
        analysis_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        view_menu.addAction(analysis_action)
        
        all_data_action = QAction(get_icon('table', 18), self.translator.tr('tab_all_data'), self)
        all_data_action.setShortcut("Ctrl+4")
        all_data_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))
        view_menu.addAction(all_data_action)
        
        timeline_action = QAction(get_icon('calendar', 18), self.translator.tr('tab_timeline'), self)
        timeline_action.setShortcut("Ctrl+5")
        timeline_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(4))
        view_menu.addAction(timeline_action)
        
        reports_action = QAction(get_icon('reports', 18), self.translator.tr('tab_reports'), self)
        reports_action.setShortcut("Ctrl+6")
        reports_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(5))
        view_menu.addAction(reports_action)
        
        # Tools menu
        tools_menu = menubar.addMenu(self.translator.tr('menu_tools'))
        
        settings_action = QAction(get_icon('settings', 18), self.translator.tr('menu_settings'), self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        tools_menu.addSeparator()
        
        backup_action = QAction(get_icon('create_backup', 18), self.translator.tr('menu_backup_restore'), self)
        backup_action.triggered.connect(self.show_backup_restore)
        tools_menu.addAction(backup_action)
        
        reset_action = QAction(get_icon('clear', 18), self.translator.tr('menu_reset'), self)
        reset_action.triggered.connect(self.show_reset)
        tools_menu.addAction(reset_action)
        
        tools_menu.addSeparator()
        
        # Print & Export Settings
        print_settings_action = QAction(get_icon('format', 18), self.translator.tr('menu_print_settings'), self)
        print_settings_action.triggered.connect(self.show_print_settings)
        tools_menu.addAction(print_settings_action)
        
        tools_menu.addSeparator()
        
        attachments_action = QAction(get_icon('attach_files', 18), self.translator.tr('menu_manage_attachments'), self)
        attachments_action.triggered.connect(self.show_attachment_manager)
        tools_menu.addAction(attachments_action)
        
        tools_menu.addSeparator()
        
        # Import data action
        import_action = QAction(
            get_icon('import_data', 18),
            self.translator.tr('menu_import_data') if hasattr(self.translator, 'tr') else 'Import Data',
            self
        )
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.show_import_dialog)
        tools_menu.addAction(import_action)
        
        tools_menu.addSeparator()
        
        # Performance monitor action
        performance_action = QAction(
            get_icon('statistics', 18),
            self.translator.tr('menu_performance') if hasattr(self.translator, 'tr') else 'Performance Monitor',
            self
        )
        performance_action.triggered.connect(self.show_performance_monitor)
        tools_menu.addAction(performance_action)
    
        # Help menu
        help_menu = menubar.addMenu(self.translator.tr('menu_help'))
        
        help_action = QAction(
            get_icon('help', 18),
            self.translator.tr('help_title') if hasattr(self.translator, 'tr') else 'Help',
            self
        )
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        shortcuts_action = QAction(
            get_icon('keyboard', 18),
            self.translator.tr('help_shortcuts') if hasattr(self.translator, 'tr') else 'Keyboard Shortcuts',
            self
        )
        shortcuts_action.triggered.connect(self.show_keyboard_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        help_menu.addSeparator()
        
        about_action = QAction(get_icon('app_logo', 18), self.translator.tr('menu_about'), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        self._menu_icon_bindings = [
            (exit_action, 'close'),
            (sources_action, 'newspaper'),
            (contents_action, 'document'),
            (analysis_action, 'statistics'),
            (all_data_action, 'table'),
            (timeline_action, 'calendar'),
            (reports_action, 'reports'),
            (settings_action, 'settings'),
            (backup_action, 'create_backup'),
            (reset_action, 'clear'),
            (print_settings_action, 'format'),
            (attachments_action, 'attach_files'),
            (import_action, 'import_data'),
            (performance_action, 'statistics'),
            (help_action, 'help'),
            (shortcuts_action, 'keyboard'),
            (about_action, 'app_logo'),
        ]

    def refresh_menu_icons(self):
        """Reload menu icons after a theme change."""
        for action, icon_name in getattr(self, '_menu_icon_bindings', []):
            action.setIcon(get_icon(icon_name, 18))
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self, self.translator)
        if dialog.exec_() == QDialog.Accepted:
            # Refresh UI if language changed
            self.refresh_ui()
    
    def show_help(self):
        """Show help dialog"""
        from widgets.help_system import show_help
        show_help(self, self.translator)
    
    def show_keyboard_shortcuts(self):
        """Show keyboard shortcuts dialog"""
        from utils.accessibility import get_accessibility_manager
        manager = get_accessibility_manager()
        manager.show_keyboard_shortcuts_dialog(self, self.translator)
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            self.translator.tr('menu_about'),
            f"{self.translator.tr('app_title')}\n\n{self.translator.tr('app_version')}"
        )
    
    def show_backup_restore(self):
        """Show backup and restore dialog"""
        dialog = BackupRestoreDialog(self, self.translator)
        dialog.exec_()
        # Reload data after backup/restore
        if hasattr(self, 'sources_tab'):
            self.sources_tab.load_data()
        if hasattr(self, 'contents_tab'):
            self.contents_tab.load_data()
        if hasattr(self, 'analysis_tab'):
            self.analysis_tab.load_data()
        if hasattr(self, 'all_data_tab'):
            self.all_data_tab.load_data()
        if hasattr(self, 'reports_tab'):
            self.reports_tab.load_data()
    
    def show_print_settings(self):
        """Show global print and export settings dialog"""
        from utils.print_utils import GlobalHeaderSettingsDialog
        dialog = GlobalHeaderSettingsDialog(self, self.translator)
        dialog.exec_()
    
    def show_attachment_manager(self):
        """Show attachment manager dialog"""
        from widgets.attachment_manager_widget import AttachmentManagerDialog
        dialog = AttachmentManagerDialog(self, self.translator)
        dialog.exec_()
    
    def show_import_dialog(self):
        """Show data import dialog"""
        from dialogs.import_dialog import ImportPreviewDialog
        
        # Ask which table to import to
        from PyQt5.QtWidgets import QInputDialog
        tables = ['sources', 'contents', 'content_analysis']
        table_names = {
            'sources': self.translator.tr('tab_sources'),
            'contents': self.translator.tr('tab_contents'),
            'content_analysis': self.translator.tr('tab_analysis')
        }
        
        table, ok = QInputDialog.getItem(
            self,
            self.translator.tr('menu_import_data') if hasattr(self.translator, 'tr') else 'Import Data',
            self.translator.tr('import_select_table') if hasattr(self.translator, 'tr') else 'Select table to import to:',
            [table_names.get(t, t) for t in tables],
            0,
            False
        )
        
        if ok and table:
            # Get the actual table name
            selected_table = tables[[table_names.get(t, t) for t in tables].index(table)]
            
            dialog = ImportPreviewDialog(self, self.translator, selected_table)
            dialog.import_completed.connect(self._on_import_completed)
            dialog.exec_()
    
    def _on_import_completed(self, success_count: int, error_count: int):
        """Handle import completion"""
        # Reload all data
        self._refresh_all_tabs_data()
        self.statusBar().showMessage(
            self.translator.tr('msg_import_completed', success=success_count, errors=error_count)
        )
    
    def show_performance_monitor(self):
        """Show performance monitor dialog"""
        from utils.performance_monitor import PerformanceDialog
        dialog = PerformanceDialog(self, self.translator)
        dialog.exec_()
    
    def show_reset(self):
        """Show reset dialog"""
        dialog = ResetDialog(self, self.translator)
        if dialog.exec_() == QDialog.Accepted:
            # Reload all data after reset
            if hasattr(self, 'sources_tab'):
                self.sources_tab.load_data()
            if hasattr(self, 'contents_tab'):
                self.contents_tab.load_data()
            if hasattr(self, 'analysis_tab'):
                self.analysis_tab.load_data()
            if hasattr(self, 'all_data_tab'):
                self.all_data_tab.load_data()
            if hasattr(self, 'timeline_tab'):
                self.timeline_tab.load_data()
            if hasattr(self, 'reports_tab'):
                self.reports_tab.load_data()
            self.statusBar().showMessage(self.translator.tr('msg_ready'))
    
    def refresh_ui(self):
        """Refresh UI after language change"""
        # Apply language direction (RTL for Arabic) - this also updates AppStyles
        self.apply_language_direction()
        
        # Regenerate and apply stylesheet with new direction
        self.setStyleSheet(AppStyles.get_stylesheet())
        
        self.setWindowTitle(self.translator.tr('app_title'))
        self.statusBar().showMessage(self.translator.tr('msg_ready'))
        if hasattr(self, 'brand_title'):
            self.brand_title.setText(self.translator.tr('app_title'))
            self.brand_subtitle.setText(self._tr('shell_subtitle', 'Research workspace'))
            self.global_search.setPlaceholderText(
                self._tr('search_global_placeholder', 'Search the research workspace')
            )
            self.global_search.setAccessibleName(
                self._tr('search_global_placeholder', 'Global search')
            )
            self.global_search_clear_action.setToolTip(self._tr('btn_clear', 'Clear search'))
            self.quick_add_button.setText(
                '' if getattr(self, '_header_compact', False) else self.translator.tr('btn_add_new')
            )
            self.quick_add_button.setToolTip(self.translator.tr('btn_add_new'))
            self.quick_add_button.setAccessibleName(self.translator.tr('btn_add_new'))
            self.header_settings_button.setToolTip(self.translator.tr('menu_settings'))
            self.header_settings_button.setAccessibleName(self.translator.tr('menu_settings'))
            self.header_help_button.setToolTip(self.translator.tr('help_title', default='Help'))
            self.header_help_button.setAccessibleName(self.header_help_button.toolTip())
            self.context_refresh_button.setToolTip(
                self.translator.tr('btn_refresh', default='Refresh workspace')
            )
            self.context_refresh_button.setAccessibleName(self.context_refresh_button.toolTip())
            for button, (key, _icon, _title, _description) in zip(self._nav_buttons, self._page_meta):
                label = self.translator.tr(key)
                button.setToolTip(label)
                button.setAccessibleName(label)
                if not self._sidebar_collapsed:
                    button.setText(label)
            action_labels = (
                (self.attachments_nav_button, self.translator.tr('menu_manage_attachments')),
                (self.backup_nav_button, self.translator.tr('menu_backup_restore')),
                (self.import_nav_button, self._tr('menu_import_data', 'Import data')),
                (self.settings_nav_button, self.translator.tr('menu_settings')),
                (self.help_nav_button, self.translator.tr('help_title', default='Help and shortcuts')),
            )
            for button, label in action_labels:
                button.setToolTip(label)
                button.setAccessibleName(label)
                if not self._sidebar_collapsed:
                    button.setText(label)
            self._refresh_shell_icons()
        
        # Refresh menu bar
        self.create_menu_bar()
        
        # Refresh tab labels
        self.tab_widget.setTabText(0, self.translator.tr('tab_sources'))
        self.tab_widget.setTabText(1, self.translator.tr('tab_contents'))
        self.tab_widget.setTabText(2, self.translator.tr('tab_analysis'))
        self.tab_widget.setTabText(3, self.translator.tr('tab_all_data'))
        self.tab_widget.setTabText(4, self.translator.tr('tab_timeline'))
        self.tab_widget.setTabText(5, self.translator.tr('tab_reports'))
        
        # Get direction for current language
        direction = Qt.RightToLeft if self.translator.current_language == 'ar' else Qt.LeftToRight
        
        # Apply direction to tab widget itself
        self.tab_widget.setLayoutDirection(direction)
        
        # Refresh all tabs using their refresh_translations method
        tabs = [self.sources_tab, self.contents_tab, self.analysis_tab, 
                self.all_data_tab, self.timeline_tab, self.reports_tab]
        
        for tab in tabs:
            # Apply language direction to each tab and all its children
            if hasattr(tab, 'setLayoutDirection'):
                tab.setLayoutDirection(direction)
                self._apply_direction_recursive(tab, direction)
            
            # Call the new refresh_translations method if available
            if hasattr(tab, 'refresh_translations'):
                tab.refresh_translations()
            
            # Call refresh_columns for table header updates
            if hasattr(tab, 'refresh_columns'):
                tab.refresh_columns()
        
        # Refresh shell context labels as well as the functional page controls.
        if hasattr(self, 'sidebar'):
            self._update_workspace_context(self.tab_widget.currentIndex())

        # Reload data with deferred loading to prevent flickering
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(200, lambda: self._refresh_all_tabs_data())
    
    def _refresh_all_tabs_data(self):
        """Refresh all tabs data after a delay to prevent UI flickering"""
        if hasattr(self, 'sources_tab'):
            self.sources_tab.load_data()
        if hasattr(self, 'contents_tab'):
            self.contents_tab.load_data()
        if hasattr(self, 'analysis_tab'):
            self.analysis_tab.load_data()
        if hasattr(self, 'all_data_tab'):
            self.all_data_tab.load_data()
        if hasattr(self, 'timeline_tab'):
            self.timeline_tab.load_data()
        if hasattr(self, 'reports_tab') and hasattr(self.reports_tab, 'load_data'):
            self.reports_tab.load_data()
    
    def _on_tab_changed(self, index: int):
        """Handle workspace navigation and lazy-load data for visible pages."""
        if index < 0:
            return
        self._update_workspace_context(index)
        
        tab = self.tab_widget.widget(index)
        if tab:
            # Load data if not already loaded (lazy loading)
            if hasattr(tab, '_data_loaded') and not tab._data_loaded:
                if hasattr(tab, '_deferred_load_data'):
                    tab._deferred_load_data()
                elif hasattr(tab, 'load_data'):
                    try:
                        tab.load_data()
                        tab._data_loaded = True
                    except Exception as e:
                        logger.error(f"Error loading data for tab {index}: {e}")
    
    def closeEvent(self, event):
        """Handle window closing"""
        DatabaseConfig.close_all_connections()
        event.accept()


def main():
    """Main entry point"""
    import logging
    import os
    
    # Enable high DPI scaling BEFORE creating QApplication
    # This is critical for proper scaling on Windows high DPI displays
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Set environment variable for better scaling on Windows
    os.environ.setdefault('QT_AUTO_SCREEN_SCALE_FACTOR', '1')
    os.environ.setdefault('QT_ENABLE_HIGHDPI_SCALING', '1')
    
    # Suppress Qt geometry warnings
    logging.getLogger('PyQt5.QtCore').setLevel(logging.CRITICAL)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application-wide high DPI policy if available (Qt 5.14+)
    try:
        if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
    except:
        pass
    
    # Suppress Qt debug messages about geometry
    from PyQt5.QtCore import qInstallMessageHandler, QtMsgType
    
    def message_handler(msg_type, context, message):
        # Suppress geometry-related warnings and other noise
        if 'setGeometry' in message or 'Unable to set geometry' in message:
            return
        # Only log critical messages
        if msg_type == QtMsgType.QtCriticalMsg:
            print(f"Qt Critical: {message}")
    
    qInstallMessageHandler(message_handler)
    
    # Create and show main window directly - no hide/show cycle
    window = MainWindow()
    window.showMaximized()
    
    # Load initial data after a short delay to ensure UI is ready
    from PyQt5.QtCore import QTimer
    QTimer.singleShot(100, lambda: window._on_tab_changed(window.tab_widget.currentIndex()))
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
