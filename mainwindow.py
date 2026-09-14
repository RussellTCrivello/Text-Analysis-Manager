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
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QMessageBox, QStatusBar, QMenuBar, QMenu, QAction, QDialog, QLabel
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
    """Simple main application window"""
    
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
            from utils.accessibility import get_accessibility_manager
            self.accessibility_manager = get_accessibility_manager()
            self.accessibility_manager.setup_for_window(self)
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
    
    def setup_ui(self):
        """Setup enhanced UI"""
        self.setWindowTitle(self.translator.tr('app_title'))
        
        # Set application icon (for window title bar and taskbar)
        self._set_application_icon()
        
        self.setStyleSheet(AppStyles.get_stylesheet())
        
        # Set responsive minimum size based on screen
        min_width, min_height = AppStyles.get_min_dialog_size(1200, 800)
        self.setMinimumSize(min_width, min_height)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        # Use 8px grid spacing
        margin = AppStyles.get_spacing(1)  # 8px
        spacing = AppStyles.get_spacing(1)  # 8px
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        # Set size constraint to prevent child widgets from changing parent size
        layout.setSizeConstraint(QVBoxLayout.SetMinAndMaxSize)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Configure tab bar for full text display
        tab_bar = self.tab_widget.tabBar()
        tab_bar.setExpanding(True)  # Expand tabs to fill available space
        tab_bar.setElideMode(Qt.ElideNone)  # Don't truncate tab text
        tab_bar.setUsesScrollButtons(True)  # Allow scroll buttons if tabs don't fit
        tab_bar.setDocumentMode(False)  # Standard tab appearance
        tab_bar.setStyleSheet(AppStyles.get_component_style('tab_bar'))
        
        # Set tab widget to use scroll mode if tabs don't fit
        self.tab_widget.setElideMode(Qt.ElideNone)
        self.tab_widget.setUsesScrollButtons(True)
        
        # Add tabs
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
        
        layout.addWidget(self.tab_widget)
        
        # Connect tab change signal to lazy load data for tabs
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Status bar
        self.statusBar().showMessage(self.translator.tr('msg_ready'))
    
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
        """Handle tab change - ensure data is loaded for visible tab"""
        if index < 0:
            return
        
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
