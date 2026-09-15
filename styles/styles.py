"""
Centralized Styling System for the Application
================================================
All UI formatting MUST be defined in this file only.
Do NOT create inline styles in any other file.

This provides:
- Theme support (Light and Dark)
- Component-specific stylesheets
- Consistent color palette
- Font management
- Style retrieval methods
- RTL/LTR direction support (auto-loaded from config)

Usage in other files:
    from styles.styles import AppStyles
    
    # Apply global stylesheet
    widget.setStyleSheet(AppStyles.get_stylesheet())
    
    # Get component-specific style
    button.setStyleSheet(AppStyles.get_button_style('primary'))
    panel.setStyleSheet(AppStyles.get_component_style('preview_header'))

IMPORTANT: This module auto-initializes direction from saved config.
Call AppStyles.initialize() at application startup to ensure proper RTL/LTR.
"""
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtWidgets import QApplication
from typing import Optional, Dict


class AppStyles:
    """
    Centralized application styles with theme support.
    ALL formatting definitions must be placed in this class.
    """
    
    # ==================== FONT FAMILIES ====================
    
    # Standard font family for LTR languages
    FONT_FAMILY = "Segoe UI"
    
    # Arabic font family for RTL languages
    FONT_FAMILY_ARABIC = "'Noto Sans Arabic', 'Segoe UI', 'Tahoma', 'Traditional Arabic', 'Simplified Arabic', sans-serif"
    
    # Combined font family that works for both
    FONT_FAMILY_COMBINED = "'Segoe UI', 'Noto Sans Arabic', 'Tahoma', 'Arial', 'Traditional Arabic', sans-serif"
    
    # ==================== COLOR PALETTES ====================
    
    # Light Theme Colors
    LIGHT = {
        'PRIMARY': "#14283D",
        'SECONDARY': "#25405B",
        'ACCENT': "#2F6FED",
        'ACCENT_HOVER': "#2558C5",
        'SUCCESS': "#1B9C85",
        'SUCCESS_HOVER': "#157A68",
        'DANGER': "#D9534F",
        'DANGER_HOVER': "#B83D3A",
        'WARNING': "#C9832B",
        'INFO': "#2F6FED",
        'WHITE': "#FFFFFF",
        'LIGHT_BG': "#F4F7FB",
        'DARK_BG': "#0E1B2A",
        'TEXT_PRIMARY': "#172B4D",
        'TEXT_SECONDARY': "#60738A",
        'TEXT_MUTED': "#8393A7",
        'BORDER': "#D7E0EC",
        'BORDER_FOCUS': "#2F6FED",
        'TABLE_HEADER': "#1D3553",
        'TABLE_ALT_ROW': "#F4F7FB",
        'INPUT_BG': "#FFFFFF",
        'DIALOG_BG': "#FFFFFF",
        'MENU_BG': "#FFFFFF",
        'PURPLE': "#7657D6",
        'PURPLE_HOVER': "#5E43B5",
        'GRADIENT_START': "#2F6FED",
        'GRADIENT_END': "#1B9C85",
        'PANEL_BG': "#F9FBFE",
        'PANEL_HEADER': "#1D3553",
        'ROW_NUM_BG': "#F4F7FB",
    }
    
    # Dark Theme Colors
    DARK = {
        'PRIMARY': "#101B2A",
        'SECONDARY': "#1B2D42",
        'ACCENT': "#6E9CFF",
        'ACCENT_HOVER': "#8CACFF",
        'SUCCESS': "#4BC7A8",
        'SUCCESS_HOVER': "#35A98D",
        'DANGER': "#F27873",
        'DANGER_HOVER': "#D95D58",
        'WARNING': "#F0B563",
        'INFO': "#6E9CFF",
        'WHITE': "#182536",
        'LIGHT_BG': "#101A28",
        'DARK_BG': "#0B1420",
        'TEXT_PRIMARY': "#E7EEF8",
        'TEXT_SECONDARY': "#A6B5C8",
        'TEXT_MUTED': "#73869D",
        'BORDER': "#34475E",
        'BORDER_FOCUS': "#6E9CFF",
        'TABLE_HEADER': "#20344D",
        'TABLE_ALT_ROW': "#142235",
        'INPUT_BG': "#182536",
        'DIALOG_BG': "#142235",
        'MENU_BG': "#182536",
        'PURPLE': "#A78BFA",
        'PURPLE_HOVER': "#8B70DD",
        'GRADIENT_START': "#6E9CFF",
        'GRADIENT_END': "#4BC7A8",
        'PANEL_BG': "#142235",
        'PANEL_HEADER': "#20344D",
        'ROW_NUM_BG': "#182536",
    }
    
    # ==================== THEME STATE ====================
    
    _current_theme = 'light'
    _colors = LIGHT
    _initialized = False
    
    # ==================== FONT SETTINGS ====================
    
    # Note: FONT_FAMILY is defined above in the FONT FAMILIES section
    FONT_SIZE = 10
    FONT_SIZE_LARGE = 12
    FONT_SIZE_SMALL = 9
    FONT_SIZE_TITLE = 16
    FONT_SIZE_HEADER = 14
    
    # ==================== 8-PIXEL GRID SYSTEM ====================
    # All spacing, margins, and padding should use multiples of 8px
    GRID_UNIT = 8
    
    @classmethod
    def get_spacing(cls, units: int) -> int:
        """Get spacing value in pixels (multiples of 8px grid)"""
        return cls.GRID_UNIT * units
    
    @classmethod
    def get_padding(cls, units: int = 2) -> int:
        """Get standard padding (default 16px = 2 units)"""
        return cls.GRID_UNIT * units
    
    @classmethod
    def get_margin(cls, units: int = 2) -> int:
        """Get standard margin (default 16px = 2 units)"""
        return cls.GRID_UNIT * units
    
    @staticmethod
    def apply_layout_spacing(layout, margin_units: int = 1, spacing_units: int = 2):
        """
        Apply consistent 8px grid spacing to a layout.
        
        Args:
            layout: QVBoxLayout, QHBoxLayout, QGridLayout, or QFormLayout
            margin_units: Margin in 8px units (default 1 = 8px)
            spacing_units: Spacing between items in 8px units (default 2 = 16px)
        """
        margin = AppStyles.get_spacing(margin_units)
        spacing = AppStyles.get_spacing(spacing_units)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
    
    @staticmethod
    def apply_form_layout_for_language(form_layout, is_rtl: bool):
        """
        Apply RTL/LTR-aware alignment and spacing to QFormLayout for data entry forms.
        Ensures proper label alignment and field layout for both Arabic and English.
        
        Args:
            form_layout: QFormLayout to configure
            is_rtl: True for Arabic (RTL), False for English (LTR)
        """
        from PyQt5.QtCore import Qt
        
        # Apply 8px grid spacing; use larger margins for RTL (Arabic) for better visual separation
        margin = AppStyles.get_spacing(2) if is_rtl else AppStyles.get_spacing(1)  # 16px RTL, 8px LTR
        spacing = AppStyles.get_spacing(2) if is_rtl else AppStyles.get_spacing(2)  # 16px between rows
        form_layout.setContentsMargins(margin, margin, margin, margin)
        form_layout.setSpacing(spacing)
        
        # Label alignment: right-aligned for RTL (labels on right side), left for LTR
        label_align = Qt.AlignRight | Qt.AlignVCenter if is_rtl else Qt.AlignLeft | Qt.AlignVCenter
        form_layout.setLabelAlignment(label_align)
        
        # Allow fields to expand to use available space
        from PyQt5.QtWidgets import QFormLayout
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
    
    @staticmethod
    def get_dialog_content_margins():
        """Get standard content margins for dialog scroll areas (16px all sides)."""
        m = AppStyles.get_spacing(2)
        return (m, m, m, m)
    
    # ==================== INITIALIZATION ====================
    
    @classmethod
    def initialize(cls):
        """
        Initialize AppStyles with saved settings from config.
        This method loads theme and direction from saved configuration
        and should be called at application startup BEFORE creating any widgets.
        """
        if cls._initialized:
            return
        
        try:
            from config.config_manager import ConfigManager
            config = ConfigManager()
            
            # Load theme from config
            saved_theme = config.get('Application', 'theme', 'light')
            cls._current_theme = saved_theme.lower()
            cls._colors = cls.DARK if cls._current_theme == 'dark' else cls.LIGHT
            
            # Load language and set direction
            saved_language = config.get('Application', 'language', 'en')
            cls._current_direction = 'rtl' if saved_language == 'ar' else 'ltr'
            
            cls._initialized = True
        except Exception:
            # Fallback to defaults if config loading fails
            cls._current_theme = 'light'
            cls._colors = cls.LIGHT
            cls._current_direction = 'ltr'
            cls._initialized = True
    
    @classmethod
    def ensure_initialized(cls):
        """Ensure AppStyles is initialized before use"""
        if not cls._initialized:
            cls.initialize()
    
    @classmethod
    def refresh_for_language(cls, language: str):
        """
        Refresh styles for a new language. Call this when language changes.
        This updates the direction and invalidates cached styles.
        
        Args:
            language: Language code ('ar' for RTL, 'en' for LTR, etc.)
        """
        cls._current_direction = 'rtl' if language == 'ar' else 'ltr'
        # Mark as initialized to prevent reload from config
        cls._initialized = True
    
    @classmethod
    def get_all_colors(cls) -> Dict[str, str]:
        """Get all theme colors - useful for debugging"""
        cls.ensure_initialized()
        return cls._colors.copy()
    
    # ==================== THEME MANAGEMENT ====================
    
    @classmethod
    def set_theme(cls, theme: str):
        """Set the current theme ('light' or 'dark')"""
        cls.ensure_initialized()
        cls._current_theme = theme.lower()
        cls._colors = cls.DARK if cls._current_theme == 'dark' else cls.LIGHT
    
    @classmethod
    def get_current_theme(cls) -> str:
        """Get current theme name"""
        cls.ensure_initialized()
        return cls._current_theme
    
    @classmethod
    def is_dark_theme(cls) -> bool:
        """Check if dark theme is active"""
        cls.ensure_initialized()
        return cls._current_theme == 'dark'
    
    @classmethod
    def get_color(cls, color_name: str) -> str:
        """Get color value for current theme"""
        cls.ensure_initialized()
        return cls._colors.get(color_name, '#000000')
    
    @classmethod
    def get_colors(cls) -> Dict[str, str]:
        """Get all colors for current theme"""
        cls.ensure_initialized()
        return cls._colors.copy()
    
    # ==================== FONT HELPERS ====================
    
    @staticmethod
    def get_font(size: Optional[int] = None, bold: bool = False) -> QFont:
        """Get QFont with specified settings"""
        font = QFont(AppStyles.FONT_FAMILY, size or AppStyles.FONT_SIZE)
        font.setBold(bold)
        return font
    
    @classmethod
    def get_current_font_family(cls) -> str:
        """Get the appropriate font family based on current language direction"""
        if cls.is_rtl():
            return cls.FONT_FAMILY_ARABIC
        return f"'{cls.FONT_FAMILY}', sans-serif"
    
    @classmethod
    def get_arabic_font(cls, size: Optional[int] = None, bold: bool = False) -> QFont:
        """Get QFont configured for Arabic text"""
        # Try Noto Sans Arabic first, fall back to system Arabic fonts
        font = QFont('Noto Sans Arabic', size or cls.FONT_SIZE)
        if not font.exactMatch():
            font = QFont('Traditional Arabic', size or cls.FONT_SIZE)
        if not font.exactMatch():
            font = QFont('Segoe UI', size or cls.FONT_SIZE)
        font.setBold(bold)
        return font
    
    # ==================== APPLICATION PALETTE ====================
    
    @classmethod
    def apply_theme_to_app(cls, app: QApplication):
        """Apply theme palette to the application"""
        if cls._current_theme == 'dark':
            palette = QPalette()
            
            # Window colors
            palette.setColor(QPalette.Window, QColor(cls._colors['LIGHT_BG']))
            palette.setColor(QPalette.WindowText, QColor(cls._colors['TEXT_PRIMARY']))
            
            # Base colors (input fields, etc.)
            palette.setColor(QPalette.Base, QColor(cls._colors['INPUT_BG']))
            palette.setColor(QPalette.AlternateBase, QColor(cls._colors['LIGHT_BG']))
            
            # Text colors
            palette.setColor(QPalette.Text, QColor(cls._colors['TEXT_PRIMARY']))
            palette.setColor(QPalette.BrightText, QColor('#FFFFFF'))
            palette.setColor(QPalette.PlaceholderText, QColor(cls._colors['TEXT_SECONDARY']))
            
            # Button colors
            palette.setColor(QPalette.Button, QColor(cls._colors['SECONDARY']))
            palette.setColor(QPalette.ButtonText, QColor(cls._colors['TEXT_PRIMARY']))
            
            # Highlight colors
            palette.setColor(QPalette.Highlight, QColor(cls._colors['ACCENT']))
            palette.setColor(QPalette.HighlightedText, QColor('#FFFFFF'))
            
            # Disabled colors
            palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(cls._colors['TEXT_SECONDARY']))
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(cls._colors['TEXT_SECONDARY']))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(cls._colors['TEXT_SECONDARY']))
            
            # Link colors
            palette.setColor(QPalette.Link, QColor(cls._colors['ACCENT']))
            palette.setColor(QPalette.LinkVisited, QColor(cls._colors['ACCENT_HOVER']))
            
            # Tooltip
            palette.setColor(QPalette.ToolTipBase, QColor(cls._colors['SECONDARY']))
            palette.setColor(QPalette.ToolTipText, QColor(cls._colors['TEXT_PRIMARY']))
            
            app.setPalette(palette)
    
    # ==================== GLOBAL STYLESHEET ====================
    
    @classmethod
    def _get_checkmark_image_path(cls) -> str:
        """Get path to checkmark icon for checkbox (works in dev and frozen)"""
        return cls._get_icon_image_path('checkmark')

    @classmethod
    def _get_icon_image_path(cls, icon_name: str) -> str:
        """Get a packaged graphical asset path for stylesheet image properties."""
        try:
            from utils.path_utils import get_bundle_dir
            path = get_bundle_dir() / 'icons' / 'images' / f'{icon_name}.svg'
            if path.exists():
                return str(path).replace('\\', '/')
        except Exception:
            pass
        return ''
    
    @classmethod
    def get_stylesheet(cls) -> str:
        """Get the complete application stylesheet"""
        cls.ensure_initialized()
        c = cls._colors
        
        # Use Arabic font family for RTL direction
        font_family = cls.get_current_font_family()
        
        # Checkmark image for checkbox (empty if not found)
        checkmark_url = cls._get_checkmark_image_path()
        checkmark_style = f'\n            image: url({checkmark_url});' if checkmark_url else ''
        chevron_down_url = cls._get_icon_image_path('chevron_down')
        chevron_down_style = f'image: url({chevron_down_url});' if chevron_down_url else ''
        
        return f"""
        /* ==================== Main Window ==================== */
        QMainWindow {{
            background-color: {c['WHITE']};
            color: {c['TEXT_PRIMARY']};
            font-family: {font_family};
        }}
        
        /* ==================== Menu Bar ==================== */
        QMenuBar {{
            background-color: {c['PRIMARY']};
            color: {c['TEXT_PRIMARY'] if cls._current_theme == 'dark' else '#FFFFFF'};
            padding: 6px;
            border: none;
            font-family: {font_family};
            font-size: {cls.FONT_SIZE}pt;
            font-weight: 500;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 8px 16px;
            border-radius: 4px;
            margin: 2px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {c['ACCENT']};
        }}
        
        QMenuBar::item:pressed {{
            background-color: {c['ACCENT_HOVER']};
        }}
        
        QMenuBar[layoutDirection="1"]::item {{
            padding: 8px 16px;
        }}
        
        /* ==================== Menu ==================== */
        QMenu {{
            background-color: {c['MENU_BG']};
            color: {c['TEXT_PRIMARY']};
            border: 1px solid {c['BORDER']};
            padding: 4px;
            border-radius: 4px;
            font-family: {font_family};
        }}
        
        QMenu::item {{
            padding: 8px 30px 8px 20px;
            border-radius: 3px;
        }}
        
        QMenu::item:selected {{
            background-color: {c['ACCENT']};
            color: #FFFFFF;
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {c['BORDER']};
            margin: 4px 8px;
        }}
        
        /* ==================== Buttons (8px Grid System) ==================== */
        QPushButton {{
            background-color: {c['ACCENT']};
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-family: {font_family};
            font-size: {cls.FONT_SIZE}pt;
            font-weight: 500;
            min-width: 32px;
            min-height: 32px;
        }}
        
        QPushButton:hover {{
            background-color: {c['ACCENT_HOVER']};
        }}
        
        QPushButton:pressed {{
            background-color: {c['PRIMARY']};
        }}
        
        QPushButton:disabled {{
            background-color: {c['BORDER']};
            color: {c['TEXT_SECONDARY']};
            opacity: 0.6;
        }}
        
        QPushButton[class="danger"] {{
            background-color: {c['DANGER']};
        }}
        
        QPushButton[class="danger"]:hover {{
            background-color: {c['DANGER_HOVER']};
        }}
        
        QPushButton[class="success"] {{
            background-color: {c['SUCCESS']};
        }}
        
        QPushButton[class="success"]:hover {{
            background-color: {c['SUCCESS_HOVER']};
        }}
        
        /* ==================== Tab Widget ==================== */
        QTabWidget::pane {{
            border: 1px solid {c['BORDER']};
            background-color: {c['WHITE']};
            border-radius: 4px;
            top: -1px;
        }}
        
        QTabBar {{
            font-family: {font_family};
            font-size: {cls.FONT_SIZE + 1}pt;
        }}
        
        QTabBar::tab {{
            background-color: {c['LIGHT_BG']};
            color: {c['TEXT_PRIMARY']};
            border: 1px solid {c['BORDER']};
            padding: 10px 20px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            font-family: {font_family};
            font-size: {cls.FONT_SIZE + 1}pt;
            font-weight: 500;
            min-width: 100px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {c['WHITE']};
            color: {c['ACCENT']};
            border-bottom: 2px solid {c['ACCENT']};
            font-weight: 600;
        }}
        
        QTabBar::tab:hover {{
            background-color: {c['WHITE']};
        }}
        
        /* ==================== Table Widget ==================== */
        QTableWidget {{
            background-color: {c['WHITE']};
            alternate-background-color: {c['TABLE_ALT_ROW']};
            gridline-color: {c['BORDER']};
            border: 1px solid {c['BORDER']};
            border-radius: 4px;
            selection-background-color: {c['ACCENT']};
            selection-color: #FFFFFF;
            font-family: {font_family};
            font-size: {cls.FONT_SIZE}pt;
            color: {c['TEXT_PRIMARY']};
        }}
        
        QTableWidget::item {{
            padding: 6px 8px;
            border: none;
            line-height: 1.4;
        }}
        
        QTableWidget::item:selected {{
            background-color: {c['ACCENT']};
            color: #FFFFFF;
        }}
        
        QHeaderView::section {{
            background-color: {c['TABLE_HEADER']};
            color: #FFFFFF;
            padding: 8px 10px;
            border: none;
            font-family: {font_family};
            font-weight: 600;
            font-size: {cls.FONT_SIZE}pt;
        }}
        
        /* ==================== Input Fields (8px Grid System) ==================== */
        QLineEdit, QTextEdit, QDoubleSpinBox, QSpinBox, QPlainTextEdit {{
            background-color: {c['INPUT_BG']};
            border: 2px solid {c['BORDER']};
            border-radius: 8px;
            padding: 8px 16px;
            font-family: {font_family};
            font-size: {cls.FONT_SIZE}pt;
            color: {c['TEXT_PRIMARY']};
            selection-background-color: {c['ACCENT']};
            selection-color: #FFFFFF;
            line-height: 1.5;
            min-height: 32px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QPlainTextEdit:focus {{
            border: 2px solid {c['BORDER_FOCUS']};
            background-color: {c['INPUT_BG']};
            padding: 8px 16px;
        }}
        
        QLineEdit:disabled, QTextEdit:disabled, QDoubleSpinBox:disabled, QSpinBox:disabled, QPlainTextEdit:disabled {{
            background-color: {c['LIGHT_BG']};
            color: {c['TEXT_SECONDARY']};
            border-color: {c['BORDER']};
            opacity: 0.6;
        }}
        
        /* ==================== ComboBox (8px Grid System) ==================== */
        QComboBox {{
            background-color: {c['INPUT_BG']};
            border: 2px solid {c['BORDER']};
            border-radius: 8px;
            padding: 8px 16px;
            font-family: {font_family};
            font-size: {cls.FONT_SIZE}pt;
            color: {c['TEXT_PRIMARY']};
            min-height: 32px;
        }}
        
        QComboBox:hover {{
            border-color: {c['ACCENT']};
            background-color: {c['INPUT_BG']};
        }}
        
        QComboBox:focus {{
            border: 2px solid {c['BORDER_FOCUS']};
            background-color: {c['INPUT_BG']};
            padding: 9px 13px;
        }}
        
        QComboBox:disabled {{
            background-color: {c['LIGHT_BG']};
            color: {c['TEXT_SECONDARY']};
            border-color: {c['BORDER']};
        }}
        
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 32px;
            border-left: 1px solid {c['BORDER']};
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
            background-color: {c['LIGHT_BG']};
        }}
        
        QComboBox[layoutDirection="1"]::drop-down {{
            subcontrol-position: top left;
            border-left: none;
            border-right: 1px solid {c['BORDER']};
            border-top-left-radius: 6px;
            border-bottom-left-radius: 6px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
        }}
        
        QComboBox::drop-down:hover {{
            background-color: {c['BORDER']};
        }}
        
        QComboBox::down-arrow {{
            {chevron_down_style}
            width: 16px;
            height: 16px;
            margin-right: 8px;
        }}
        
        QComboBox[layoutDirection="1"]::down-arrow {{
            margin-right: 0px;
            margin-left: 8px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {c['INPUT_BG']};
            border: 1.5px solid {c['BORDER']};
            border-radius: 6px;
            selection-background-color: {c['ACCENT']};
            selection-color: #FFFFFF;
            padding: 4px;
            outline: none;
            min-width: 150px;
        }}
        
        QComboBox QAbstractItemView::item {{
            padding: 8px 12px;
            border-radius: 4px;
            margin: 2px;
            color: {c['TEXT_PRIMARY']};
        }}
        
        QComboBox QAbstractItemView::item:hover {{
            background-color: {c['LIGHT_BG']};
        }}
        
        QComboBox QAbstractItemView::item:selected {{
            background-color: {c['ACCENT']};
            color: #FFFFFF;
        }}
        
        /* ==================== DateEdit / DateTimeEdit ==================== */
        QDateEdit, QDateTimeEdit {{
            background-color: {c['INPUT_BG']};
            border: 1.5px solid {c['BORDER']};
            border-radius: 6px;
            padding: 10px 14px;
            font-size: {cls.FONT_SIZE}pt;
            color: {c['TEXT_PRIMARY']};
            min-height: 20px;
        }}
        
        QDateEdit:hover, QDateTimeEdit:hover {{
            border-color: {c['ACCENT']};
            background-color: {c['INPUT_BG']};
        }}
        
        QDateEdit:focus, QDateTimeEdit:focus {{
            border: 2px solid {c['BORDER_FOCUS']};
            background-color: {c['INPUT_BG']};
            padding: 9px 13px;
        }}
        
        QDateEdit:disabled, QDateTimeEdit:disabled {{
            background-color: {c['LIGHT_BG']};
            color: {c['TEXT_SECONDARY']};
            border-color: {c['BORDER']};
        }}
        
        QDateEdit::drop-down, QDateTimeEdit::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 32px;
            border-left: 1px solid {c['BORDER']};
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
            background-color: {c['LIGHT_BG']};
        }}
        
        QDateEdit[layoutDirection="1"]::drop-down, QDateTimeEdit[layoutDirection="1"]::drop-down {{
            subcontrol-position: top left;
            border-left: none;
            border-right: 1px solid {c['BORDER']};
            border-top-left-radius: 6px;
            border-bottom-left-radius: 6px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
        }}
        
        QDateEdit::drop-down:hover, QDateTimeEdit::drop-down:hover {{
            background-color: {c['BORDER']};
        }}
        
        QDateEdit::down-arrow, QDateTimeEdit::down-arrow {{
            {chevron_down_style}
            width: 16px;
            height: 16px;
            margin-right: 8px;
        }}
        
        QDateEdit[layoutDirection="1"]::down-arrow, QDateTimeEdit[layoutDirection="1"]::down-arrow {{
            margin-right: 0px;
            margin-left: 8px;
        }}
        
        QCalendarWidget {{
            background-color: {c['INPUT_BG']};
            border: 1.5px solid {c['BORDER']};
            border-radius: 8px;
            font-size: {cls.FONT_SIZE}pt;
        }}
        
        QCalendarWidget QTableView {{
            selection-background-color: {c['ACCENT']};
            selection-color: #FFFFFF;
            border: none;
            background-color: {c['INPUT_BG']};
            color: {c['TEXT_PRIMARY']};
        }}
        
        QCalendarWidget QTableView::item:hover {{
            background-color: {c['LIGHT_BG']};
        }}
        
        /* ==================== Labels ==================== */
        QLabel {{
            color: {c['TEXT_PRIMARY']};
            font-family: {font_family};
            font-size: {cls.FONT_SIZE}pt;
            padding: 2px 4px;
            min-width: 50px;
            line-height: 1.5;
        }}
        
        /* ==================== Status Bar ==================== */
        QStatusBar {{
            background-color: {c['LIGHT_BG']};
            color: {c['TEXT_PRIMARY']};
            border-top: 1px solid {c['BORDER']};
            padding: 4px;
        }}
        
        QStatusBar[layoutDirection="1"] QLabel {{
            text-align: right;
        }}
        
        /* ==================== Scroll Bar ==================== */
        QScrollBar:vertical {{
            background-color: {c['LIGHT_BG']};
            width: 14px;
            border: none;
            border-radius: 7px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {c['BORDER']};
            min-height: 30px;
            border-radius: 7px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {c['TEXT_SECONDARY']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        
        QScrollBar:horizontal {{
            background-color: {c['LIGHT_BG']};
            height: 14px;
            border: none;
            border-radius: 7px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {c['BORDER']};
            min-width: 30px;
            border-radius: 7px;
            margin: 2px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {c['TEXT_SECONDARY']};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
        
        /* ==================== Dialog ==================== */
        QDialog {{
            background-color: {c['DIALOG_BG']};
            color: {c['TEXT_PRIMARY']};
        }}
        
        /* ==================== Group Box ==================== */
        QGroupBox {{
            border: 1px solid {c['BORDER']};
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 12px;
            font-family: {font_family};
            font-weight: bold;
            font-size: {cls.FONT_SIZE}pt;
            color: {c['TEXT_PRIMARY']};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top {'right' if cls.is_rtl() else 'left'};
            padding: 4px 12px;
            background-color: {c['ACCENT']};
            color: white;
            border-radius: 4px;
            {'margin-right' if cls.is_rtl() else 'margin-left'}: 8px;
            font-family: {font_family};
            font-size: {cls.FONT_SIZE}pt;
        }}
        
        /* ==================== Progress Bar ==================== */
        QProgressBar {{
            border: 1px solid {c['BORDER']};
            border-radius: 4px;
            text-align: center;
            background-color: {c['LIGHT_BG']};
            color: {c['TEXT_PRIMARY']};
            height: 20px;
        }}
        
        QProgressBar::chunk {{
            background-color: {c['ACCENT']};
            border-radius: 3px;
        }}
        
        /* ==================== Tooltip ==================== */
        QToolTip {{
            background-color: {c['PRIMARY']};
            color: #FFFFFF;
            border: 1px solid {c['SECONDARY']};
            padding: 6px;
            border-radius: 4px;
            font-size: {cls.FONT_SIZE_SMALL}pt;
        }}
        
        /* ==================== List Widget ==================== */
        QListWidget {{
            background-color: {c['INPUT_BG']};
            border: 1px solid {c['BORDER']};
            border-radius: 4px;
            color: {c['TEXT_PRIMARY']};
        }}
        
        QListWidget::item {{
            padding: 6px;
            border-radius: 2px;
        }}
        
        QListWidget::item:selected {{
            background-color: {c['ACCENT']};
            color: #FFFFFF;
        }}
        
        QListWidget::item:hover {{
            background-color: {c['LIGHT_BG']};
        }}
        
        /* ==================== Check Box ==================== */
        QCheckBox {{
            color: {c['TEXT_PRIMARY']};
            spacing: 8px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {c['BORDER']};
            border-radius: 4px;
            background-color: {c['INPUT_BG']};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {c['ACCENT']};
            border-color: {c['ACCENT']};{checkmark_style}
        }}
        
        QCheckBox::indicator:hover {{
            border-color: {c['ACCENT']};
        }}
        
        /* ==================== Radio Button ==================== */
        QRadioButton {{
            color: {c['TEXT_PRIMARY']};
            spacing: 8px;
        }}
        
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {c['BORDER']};
            border-radius: 9px;
            background-color: {c['INPUT_BG']};
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {c['ACCENT']};
            border-color: {c['ACCENT']};
        }}
        
        QRadioButton::indicator:hover {{
            border-color: {c['ACCENT']};
        }}
        
        /* ==================== Splitter ==================== */
        QSplitter::handle {{
            background-color: {c['BORDER']};
        }}
        
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        
        QSplitter::handle:vertical {{
            height: 2px;
        }}
        
        /* ==================== Message Box ==================== */
        QMessageBox {{
            background-color: {c['DIALOG_BG']};
            color: {c['TEXT_PRIMARY']};
            min-width: 400px;
            min-height: 150px;
        }}
        
        QMessageBox QLabel {{
            color: {c['TEXT_PRIMARY']};
            min-width: 300px;
            padding: 10px;
            font-size: {cls.FONT_SIZE}pt;
        }}
        
        QMessageBox QPushButton {{
            min-width: 80px;
            min-height: 28px;
            padding: 6px 16px;
        }}
        
        /* ==================== Tool Button ==================== */
        QToolButton {{
            background-color: {c['ACCENT']};
            color: #FFFFFF;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
        }}
        
        QToolButton:hover {{
            background-color: {c['ACCENT_HOVER']};
        }}
        
        QToolButton::menu-indicator {{
            image: none;
        }}
        
        /* ==================== Slider ==================== */
        QSlider::groove:horizontal {{
            border: 1px solid {c['BORDER']};
            height: 8px;
            background: {c['LIGHT_BG']};
            margin: 2px 0;
            border-radius: 4px;
        }}
        
        QSlider::handle:horizontal {{
            background: {c['ACCENT']};
            border: 1px solid {c['ACCENT']};
            width: 18px;
            margin: -5px 0;
            border-radius: 9px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background: {c['ACCENT_HOVER']};
        }}
        
        /* ==================== Frame ==================== */
        QFrame {{
            color: {c['TEXT_PRIMARY']};
        }}

        /* ==================== Product Shell ==================== */
        QMainWindow#mainWindow {{
            background-color: {c['LIGHT_BG']};
        }}
        QFrame#appShell {{
            background-color: {c['LIGHT_BG']};
        }}
        QFrame#appHeader {{
            background-color: {c['WHITE']};
            border-bottom: 1px solid {c['BORDER']};
        }}
        QLabel#brandMark {{
            background-color: {c['LIGHT_BG']};
            border: 1px solid {c['BORDER']};
            border-radius: 10px;
        }}
        QLabel#brandTitle {{
            color: {c['TEXT_PRIMARY']};
            font-size: 13pt;
            font-weight: 700;
        }}
        QLabel#brandSubtitle {{
            color: {c['TEXT_SECONDARY']};
            font-size: 9pt;
        }}
        QLineEdit#globalSearch {{
            background-color: {c['LIGHT_BG']};
            border: 1px solid {c['BORDER']};
            border-radius: 9px;
            color: {c['TEXT_PRIMARY']};
            padding: 9px 14px 9px 36px;
            min-height: 36px;
            font-size: 10pt;
        }}
        QLineEdit#globalSearch:focus {{
            background-color: {c['WHITE']};
            border: 2px solid {c['BORDER_FOCUS']};
            padding: 8px 13px 8px 35px;
        }}
        QPushButton#headerPrimaryAction {{
            background-color: {c['ACCENT']};
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            padding: 9px 16px;
            min-height: 36px;
            font-weight: 600;
        }}
        QPushButton#headerPrimaryAction:hover {{
            background-color: {c['ACCENT_HOVER']};
        }}
        QPushButton#headerPrimaryAction:pressed {{
            background-color: {c['PRIMARY']};
        }}
        QPushButton#iconButton, QPushButton#sidebarCollapseButton {{
            background-color: transparent;
            color: {c['TEXT_PRIMARY']};
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 6px;
            min-width: 0;
            min-height: 0;
        }}
        QPushButton#iconButton:hover, QPushButton#sidebarCollapseButton:hover {{
            background-color: {c['LIGHT_BG']};
            border-color: {c['BORDER']};
        }}
        QPushButton#iconButton:pressed, QPushButton#sidebarCollapseButton:pressed {{
            background-color: {c['BORDER']};
        }}
        QFrame#appSidebar {{
            background-color: {c['WHITE']};
            border-right: 1px solid {c['BORDER']};
        }}
        QLabel#sidebarSectionLabel {{
            color: {c['TEXT_MUTED']};
            font-size: 8pt;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}
        QPushButton#navButton, QPushButton#sidebarAction {{
            background-color: transparent;
            color: {c['TEXT_SECONDARY']};
            border: 1px solid transparent;
            border-radius: 8px;
            text-align: left;
            padding: 9px 10px;
            min-height: 38px;
            font-size: 10pt;
            font-weight: 500;
        }}
        QPushButton#navButton:hover, QPushButton#sidebarAction:hover {{
            background-color: {c['LIGHT_BG']};
            color: {c['TEXT_PRIMARY']};
            border-color: {c['BORDER']};
        }}
        QPushButton#navButton:checked {{
            background-color: {c['ACCENT']};
            color: #FFFFFF;
            border-color: {c['ACCENT']};
            font-weight: 650;
        }}
        QPushButton#navButton:checked:hover {{
            background-color: {c['ACCENT_HOVER']};
            color: #FFFFFF;
        }}
        QPushButton#sidebarAction {{
            min-height: 34px;
            padding-top: 7px;
            padding-bottom: 7px;
        }}
        QFrame#sidebarDivider {{
            background-color: {c['BORDER']};
            color: {c['BORDER']};
        }}
        QFrame#workspaceArea {{
            background-color: {c['LIGHT_BG']};
        }}
        QFrame#contextHeader {{
            background-color: transparent;
        }}
        QLabel#breadcrumbLabel {{
            color: {c['TEXT_MUTED']};
            font-size: 9pt;
            font-weight: 600;
        }}
        QLabel#workspaceTitle {{
            color: {c['TEXT_PRIMARY']};
            font-size: 20pt;
            font-weight: 700;
        }}
        QLabel#workspaceSubtitle {{
            color: {c['TEXT_SECONDARY']};
            font-size: 10pt;
        }}
        QTabWidget#workspacePages::pane {{
            background-color: {c['WHITE']};
            border: 1px solid {c['BORDER']};
            border-radius: 10px;
            top: 0;
        }}
        QTabWidget#workspacePages QScrollArea, QTabWidget#workspacePages QWidget {{
            background-color: {c['WHITE']};
        }}
        QWidget#workspaceToolbar {{
            background-color: {c['WHITE']};
            border: 1px solid {c['BORDER']};
            border-radius: 10px;
            padding: 8px 10px;
        }}
        QWidget#workspaceFilterRow {{
            background-color: transparent;
        }}
        QScrollArea#workspaceActionScroller, QScrollArea#workspaceFilterScroller {{
            background-color: transparent;
            border: none;
        }}
        QScrollArea#workspaceFilterScroller QScrollBar:horizontal {{
            height: 6px;
            background-color: {c['LIGHT_BG']};
        }}
        QScrollArea#workspaceFilterScroller QScrollBar::handle:horizontal {{
            background-color: {c['BORDER']};
            border-radius: 3px;
            min-width: 24px;
        }}
        QFrame#tableWorkspace {{
            background-color: {c['WHITE']};
            border-radius: 8px;
        }}
        QSplitter#dataSplitter::handle {{
            background-color: {c['BORDER']};
        }}
        QSplitter#dataSplitter::handle:vertical {{
            height: 6px;
            margin: 2px 24px;
            border-radius: 3px;
        }}
        QStatusBar#appStatusBar {{
            background-color: {c['WHITE']};
            color: {c['TEXT_SECONDARY']};
            border-top: 1px solid {c['BORDER']};
            padding: 3px 12px;
        }}
        QLabel#statusContext {{
            color: {c['TEXT_MUTED']};
            padding: 2px 6px;
        }}
        """
    
    # ==================== BUTTON STYLES ====================
    
    @classmethod
    def get_button_style(cls, style_type: str = 'default') -> str:
        """
        Get button stylesheet by type.
        
        Types: 'default', 'primary', 'success', 'danger', 'warning', 'purple', 
               'gradient_primary', 'gradient_success', 'transparent', 'icon_only',
               'nav_button', 'remove_button'
        """
        cls.ensure_initialized()
        c = cls._colors
        
        styles = {
            'default': f"""
                QPushButton {{
                    background-color: {c['ACCENT']};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-size: {cls.FONT_SIZE}pt;
                    font-weight: 500;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: {c['ACCENT_HOVER']};
                }}
                QPushButton:pressed {{
                    background-color: {c['PRIMARY']};
                }}
                QPushButton:disabled {{
                    background-color: {c['BORDER']};
                    color: {c['TEXT_SECONDARY']};
                    opacity: 0.6;
                }}
            """,
            
            'primary': f"""
                QPushButton {{
                    background-color: {c['ACCENT']};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: 500;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: {c['ACCENT_HOVER']};
                }}
                QPushButton:disabled {{
                    background-color: {c['BORDER']};
                    color: {c['TEXT_SECONDARY']};
                    opacity: 0.6;
                }}
            """,
            
            'success': f"""
                QPushButton {{
                    background-color: {c['SUCCESS']};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: 500;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: {c['SUCCESS_HOVER']};
                }}
                QPushButton:disabled {{
                    background-color: {c['BORDER']};
                    color: {c['TEXT_SECONDARY']};
                    opacity: 0.6;
                }}
            """,
            
            'danger': f"""
                QPushButton {{
                    background-color: {c['DANGER']};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: 500;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: {c['DANGER_HOVER']};
                }}
                QPushButton:disabled {{
                    background-color: {c['BORDER']};
                    color: {c['TEXT_SECONDARY']};
                    opacity: 0.6;
                }}
            """,
            
            'warning': f"""
                QPushButton {{
                    background-color: {c['WARNING']};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: 500;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: #E67E22;
                }}
                QPushButton:disabled {{
                    background-color: {c['BORDER']};
                    color: {c['TEXT_SECONDARY']};
                    opacity: 0.6;
                }}
            """,
            
            'purple': f"""
                QPushButton {{
                    background-color: {c['PURPLE']};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: 500;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: {c['PURPLE_HOVER']};
                }}
                QPushButton:disabled {{
                    background-color: {c['BORDER']};
                    color: {c['TEXT_SECONDARY']};
                    opacity: 0.6;
                }}
            """,
            
            'gradient_primary': f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['ACCENT']}, stop:1 {c['ACCENT_HOVER']});
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: 600;
                    font-size: {cls.FONT_SIZE}pt;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['ACCENT_HOVER']}, stop:1 {c['PRIMARY']});
                }}
                QPushButton:pressed {{
                    background-color: {c['PRIMARY']};
                }}
                QPushButton:disabled {{
                    background-color: {c['BORDER']};
                    color: {c['TEXT_SECONDARY']};
                    opacity: 0.6;
                }}
            """,
            
            'gradient_success': f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['SUCCESS']}, stop:1 {c['SUCCESS_HOVER']});
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: 600;
                    font-size: {cls.FONT_SIZE}pt;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['SUCCESS_HOVER']}, stop:1 #1E8449);
                }}
                QPushButton:disabled {{
                    background-color: {c['BORDER']};
                    color: {c['TEXT_SECONDARY']};
                    opacity: 0.6;
                }}
            """,
            
            'transparent': f"""
                QPushButton {{
                    background-color: transparent;
                    color: {c['TEXT_PRIMARY']};
                    border: 2px solid {c['BORDER']};
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: 500;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: {c['LIGHT_BG']};
                    border-color: {c['ACCENT']};
                }}
                QPushButton:disabled {{
                    background-color: transparent;
                    color: {c['TEXT_SECONDARY']};
                    border-color: {c['BORDER']};
                    opacity: 0.6;
                }}
            """,
            
            'icon_only': f"""
                QPushButton {{
                    background-color: transparent;
                    color: #FFFFFF;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                    border-radius: 8px;
                    font-size: {cls.FONT_SIZE}pt;
                    font-weight: 500;
                    min-width: 32px;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.1);
                    border-color: rgba(255, 255, 255, 0.5);
                }}
            """,
            
            'nav_button': f"""
                QPushButton {{
                    background-color: {c['WHITE']};
                    border: 2px solid {c['BORDER']};
                    border-radius: 8px;
                    font-size: {cls.FONT_SIZE}pt;
                    font-weight: 500;
                    color: {c['TEXT_PRIMARY']};
                    padding: 8px 16px;
                    min-height: 32px;
                }}
                QPushButton:hover:enabled {{
                    background-color: {c['ACCENT']};
                    border-color: {c['ACCENT']};
                    color: white;
                }}
                QPushButton:pressed:enabled {{
                    background-color: {c['ACCENT_HOVER']};
                }}
                QPushButton:disabled {{
                    background-color: {c['LIGHT_BG']};
                    border-color: {c['BORDER']};
                    color: {c['TEXT_SECONDARY']};
                    opacity: 0.6;
                }}
            """,
            
            'remove_button': f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['DANGER']}, stop:1 {c['DANGER_HOVER']});
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: {cls.FONT_SIZE}pt;
                    padding: 8px 16px;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['DANGER_HOVER']}, stop:1 #A93226);
                }}
                QPushButton:disabled {{
                    background-color: {c['BORDER']};
                    color: {c['TEXT_SECONDARY']};
                    opacity: 0.6;
                }}
            """,
            
            'table_button': f"""
                QPushButton {{
                    text-align: center;
                    background-color: {c['LIGHT_BG']};
                    border: 2px solid {c['BORDER']};
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-size: {cls.FONT_SIZE_SMALL}pt;
                    font-weight: 500;
                    color: {c['TEXT_PRIMARY']};
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: {c['ACCENT']};
                    color: white;
                    border-color: {c['ACCENT']};
                }}
            """,
            
            'filter_preset': f"""
                QPushButton {{
                    background-color: {c['WHITE']};
                    border: 2px solid {c['BORDER']};
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: 500;
                    color: {c['TEXT_PRIMARY']};
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: {c['ACCENT']};
                    color: white;
                    border-color: {c['ACCENT']};
                }}
            """,
            
            'clear_button': f"""
                QPushButton {{
                    background-color: {c['TEXT_SECONDARY']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: 500;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: #7F8C8D;
                }}
                QPushButton:disabled {{
                    background-color: {c['BORDER']};
                    color: {c['TEXT_SECONDARY']};
                    opacity: 0.6;
                }}
            """,
        }
        
        return styles.get(style_type, styles['default'])
    
    # ==================== COMPONENT STYLES ====================
    
    @classmethod
    def get_component_style(cls, component: str) -> str:
        """
        Get stylesheet for specific UI components.
        
        Components: 'page_title', 'status_label', 'readonly_badge', 'section_header',
                   'preview_header', 'preview_content', 'preview_title', 'preview_toggle',
                   'field_label', 'field_value', 'text_group', 'text_edit_primary',
                   'text_edit_secondary', 'scroll_area_transparent', 'collapsible_header',
                   'collapsible_content', 'splitter', 'separator', 'chart_type_label',
                   'chart_combobox', 'chart_frame', 'sql_editor', 'fields_list',
                   'filter_frame', 'filter_group_frame', 'filter_scroll', 'results_info',
                   'results_table', 'report_preview', 'validation_summary', 'search_input',
                   'date_filter_group', 'type_filter_group', 'generated_sql',
                   'report_*' (all report builder styles), 'toolbar_*' (toolbar styles)
        """
        cls.ensure_initialized()
        c = cls._colors
        font_family = cls.get_current_font_family()
        checkmark_url = cls._get_checkmark_image_path()
        checkmark_style = f'\n                    image: url({checkmark_url});' if checkmark_url else ''
        chevron_down_url = cls._get_icon_image_path('chevron_down')
        chevron_down_style = f'image: url({chevron_down_url});' if chevron_down_url else ''
        chevron_up_url = cls._get_icon_image_path('chevron_up')
        chevron_up_style = f'image: url({chevron_up_url});' if chevron_up_url else ''
        
        components = {
            'page_title': f"""
                QLabel {{
                    font-size: {cls.FONT_SIZE_TITLE}pt;
                    font-weight: bold;
                    color: {c['TEXT_PRIMARY']};
                    padding: 8px 0;
                }}
            """,
            
            'status_label': f"""
                QLabel {{
                    color: {c['TEXT_SECONDARY']};
                    padding: 4px;
                    border-top: 1px solid {c['BORDER']};
                }}
            """,
            
            'readonly_badge': f"""
                QLabel {{
                    background-color: {c['WARNING']};
                    color: white;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-weight: bold;
                    font-size: {cls.FONT_SIZE_SMALL}pt;
                }}
            """,
            
            'section_header': f"""
                QLabel {{
                    font-size: {cls.FONT_SIZE_HEADER}pt;
                    font-weight: bold;
                    color: {c['TEXT_PRIMARY']};
                }}
            """,
            
            'preview_header': f"""
                QFrame {{
                    background-color: {c['PANEL_HEADER']};
                    border-radius: 6px 6px 0 0;
                    padding: 2px;
                }}
            """,
            
            'preview_content': f"""
                QFrame {{
                    background-color: {c['PANEL_BG']};
                    border: 1px solid {c['BORDER']};
                    border-top: none;
                    border-radius: 0 0 6px 6px;
                }}
            """,
            
            'preview_title': f"""
                QLabel {{
                    color: #FFFFFF;
                    font-size: 11pt;
                    font-weight: 600;
                }}
            """,
            
            'preview_toggle': f"""
                QPushButton {{
                    background-color: transparent;
                    color: #FFFFFF;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 4px;
                    font-size: 10pt;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.1);
                    border-color: rgba(255, 255, 255, 0.5);
                }}
            """,
            
            'field_label': f"""
                QLabel {{
                    color: {c['TEXT_SECONDARY']};
                    font-size: 9pt;
                    font-weight: 500;
                }}
            """,
            
            'field_value': f"""
                QLabel {{
                    color: {c['TEXT_PRIMARY']};
                    font-size: 10pt;
                    font-weight: 400;
                    background-color: {c['WHITE']};
                    padding: 6px 10px;
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                }}
            """,
            
            'text_group': f"""
                QGroupBox {{
                    font-weight: 600;
                    font-size: 10pt;
                    color: {c['TEXT_PRIMARY']};
                    border: 1px solid #E0E0E0;
                    border-radius: 6px;
                    margin-top: 12px;
                    padding-top: 8px;
                    background-color: {c['WHITE']};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 8px;
                    background-color: {c['WHITE']};
                    color: {c['ACCENT']};
                }}
            """,
            
            'text_group_primary': f"""
                QGroupBox {{
                    font-weight: 600;
                    font-size: 11pt;
                    color: {c['TEXT_PRIMARY']};
                    border: 1px solid #E0E0E0;
                    border-radius: 6px;
                    margin-top: 12px;
                    padding-top: 8px;
                    background-color: {c['WHITE']};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 8px;
                    background-color: {c['WHITE']};
                    color: {c['ACCENT']};
                }}
            """,
            
            'text_edit_primary': f"""
                QTextEdit {{
                    border: none;
                    background-color: transparent;
                    font-size: 11pt;
                    color: {c['TEXT_PRIMARY']};
                    line-height: 1.5;
                }}
            """,
            
            'text_edit_secondary': f"""
                QTextEdit {{
                    border: none;
                    background-color: transparent;
                    font-size: 10pt;
                    color: {c['TEXT_PRIMARY']};
                    line-height: 1.5;
                }}
            """,
            
            'scroll_area_transparent': f"""
                QScrollArea {{
                    border: none;
                    background-color: transparent;
                }}
                QScrollArea > QWidget > QWidget {{
                    background-color: transparent;
                }}
            """,
            
            'collapsible_header': f"""
                QPushButton#collapsibleHeader {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['ACCENT']}, stop:1 {c['ACCENT_HOVER']});
                    color: white;
                    border: none;
                    border-radius: 6px 6px 0 0;
                    padding: 12px 16px;
                    text-align: left;
                    font-weight: bold;
                    font-size: 12px;
                }}
                QPushButton#collapsibleHeader:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['ACCENT_HOVER']}, stop:1 {c['PRIMARY']});
                }}
            """,
            
            'collapsible_content': f"""
                QWidget#collapsibleContent {{
                    border: 2px solid {c['ACCENT']};
                    border-top: none;
                    border-radius: 0 0 6px 6px;
                    background-color: {c['WHITE']};
                    padding: 8px;
                }}
            """,
            
            'splitter': f"""
                QSplitter::handle {{
                    background-color: {c['BORDER']};
                    margin: 0 6px;
                }}
                QSplitter::handle:hover {{
                    background-color: {c['ACCENT']};
                }}
            """,
            
            'separator': f"""
                background-color: #E0E0E0;
                margin: 10px 0;
                border: none;
            """,
            
            'chart_type_label': f"""
                QLabel {{
                    color: {c['TEXT_PRIMARY']};
                    font-size: 11px;
                    font-weight: bold;
                    padding: 4px;
                }}
            """,
            
            'chart_combobox': f"""
                QComboBox {{
                    padding: 8px 14px;
                    font-size: 11px;
                    min-width: 180px;
                    border: 2px solid {c['BORDER']};
                    border-radius: 6px;
                    background-color: white;
                }}
                QComboBox:hover {{
                    border-color: {c['ACCENT']};
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 24px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: white;
                    selection-background-color: {c['ACCENT']};
                    selection-color: white;
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                }}
            """,
            
            'chart_frame': f"""
                background-color: white;
                border: 1px solid {c['BORDER']};
                border-radius: 4px;
            """,
            
            'sql_editor': f"""
                QPlainTextEdit {{
                    font-family: Consolas, Monaco, monospace;
                    font-size: 11px;
                    background-color: #2D2D2D;
                    color: #F8F8F2;
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    padding: 8px;
                    selection-background-color: #44475A;
                }}
            """,
            
            'fields_list': f"""
                QListWidget {{
                    border: 1px solid #BDC3C7;
                    border-radius: 4px;
                    background-color: white;
                    font-size: 10px;
                }}
                QListWidget::item {{
                    padding: 4px 8px;
                    border-radius: 3px;
                }}
                QListWidget::item:selected {{
                    background-color: {c['ACCENT']};
                    color: white;
                }}
                QListWidget::item:hover {{
                    background-color: #EBF5FB;
                }}
            """,
            
            'filter_frame': f"""
                QFrame {{
                    background-color: {c['WHITE']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 6px;
                    margin: 2px;
                }}
            """,
            
            'filter_group_frame': f"""
                QFrame {{
                    background-color: #EBF5FB;
                    border: 2px solid {c['ACCENT']};
                    border-radius: 6px;
                    margin: 4px;
                    padding: 8px;
                }}
            """,
            
            'filter_scroll': f"""
                QScrollArea {{
                    border: 1px solid #BDC3C7;
                    border-radius: 6px;
                    background-color: #FAFAFA;
                }}
            """,
            
            'results_info': f"""
                font-size: 12px;
                color: {c['TEXT_SECONDARY']};
                padding: 5px;
            """,
            
            'results_table': f"""
                QTableWidget {{
                    background-color: white;
                    gridline-color: {c['BORDER']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    font-size: 10px;
                }}
                QTableWidget::item {{
                    padding: 6px;
                }}
                QTableWidget::item:selected {{
                    background-color: {c['ACCENT']};
                    color: white;
                }}
                QHeaderView::section {{
                    background-color: {c['TABLE_HEADER']};
                    color: white;
                    padding: 8px;
                    border: none;
                    font-weight: bold;
                }}
            """,
            
            'report_preview': f"""
                QTextEdit {{
                    background-color: white;
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 11px;
                }}
            """,
            
            'validation_summary': f"""
                QLabel {{
                    padding: 10px;
                    background-color: {c['LIGHT_BG']};
                    border-radius: 4px;
                }}
            """,
            
            'search_input': f"""
                QLineEdit {{
                    padding: 8px 12px;
                    border: 1.5px solid {c['BORDER']};
                    border-radius: 6px;
                    font-size: {cls.FONT_SIZE}pt;
                    background-color: {c['INPUT_BG']};
                    color: {c['TEXT_PRIMARY']};
                }}
                QLineEdit:focus {{
                    border-color: {c['ACCENT']};
                    border-width: 2px;
                    padding: 7px 11px;
                }}
            """,
            
            'date_filter_group': f"""
                QGroupBox {{
                    font-weight: bold;
                    font-size: {cls.FONT_SIZE}pt;
                    color: {c['ACCENT']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    margin-top: 8px;
                    padding-top: 4px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 8px;
                    background-color: {c['WHITE']};
                }}
            """,
            
            'type_filter_group': f"""
                QGroupBox {{
                    font-weight: bold;
                    font-size: {cls.FONT_SIZE}pt;
                    color: {c['ACCENT']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 6px;
                    margin-top: 8px;
                    padding: 12px;
                    background-color: {c['WHITE']};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 8px;
                    background-color: {c['WHITE']};
                }}
            """,
            
            'type_label': f"""
                QLabel {{
                    font-weight: bold;
                    color: {c['TEXT_PRIMARY']};
                    font-size: {cls.FONT_SIZE}pt;
                }}
            """,
            
            'type_filter_combo': f"""
                QComboBox {{
                    padding: 8px 12px;
                    border: 1.5px solid {c['BORDER']};
                    border-radius: 6px;
                    background-color: {c['WHITE']};
                    min-width: 180px;
                    font-size: {cls.FONT_SIZE}pt;
                }}
                QComboBox:hover {{
                    border-color: {c['ACCENT']};
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 24px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: white;
                    selection-background-color: {c['ACCENT']};
                    selection-color: white;
                }}
            """,
            
            'generated_sql': f"""
                QPlainTextEdit {{
                    font-family: Consolas, Monaco, monospace;
                    font-size: 10px;
                    background-color: #FAFAFA;
                    color: {c['TEXT_PRIMARY']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    padding: 6px;
                }}
            """,
            
            'limit_checkbox': f"""
                QCheckBox {{
                    font-size: 10px;
                    color: {c['TEXT_PRIMARY']};
                }}
            """,
            
            'limit_spinbox': f"""
                QSpinBox {{
                    background-color: white;
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 10px;
                }}
            """,
            
            'global_logic_combo': f"""
                QComboBox {{
                    background-color: white;
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 10px;
                    font-weight: bold;
                }}
            """,
            
            'quick_filters_label': f"""
                font-size: 10px;
                color: {c['TEXT_PRIMARY']};
                font-weight: bold;
            """,
            
            'tab_bar': f"""
                QTabBar {{
                    font-size: 12px;
                    font-weight: bold;
                }}
                QTabBar::tab {{
                    min-width: 120px;
                    max-width: 300px;
                    padding: 10px 20px;
                    margin: 2px 1px;
                    border: 1px solid {c['BORDER']};
                    border-bottom: none;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                    background-color: {c['LIGHT_BG']};
                    color: {c['TEXT_PRIMARY']};
                }}
                QTabBar::tab:selected {{
                    background-color: {c['WHITE']};
                    border-bottom: 2px solid {c['ACCENT']};
                    font-weight: bold;
                    color: {c['ACCENT']};
                }}
                QTabBar::tab:hover:!selected {{
                    background-color: {c['WHITE']};
                }}
            """,
            
            'label_full_text': f"""
                QLabel {{
                    min-width: 80px;
                    padding: 2px 4px;
                    font-size: 11px;
                    color: {c['TEXT_PRIMARY']};
                }}
            """,
            
            'group_box_full_text': f"""
                QGroupBox {{
                    font-weight: bold;
                    font-size: 11px;
                    color: {c['TEXT_PRIMARY']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 6px;
                    margin-top: 12px;
                    padding-top: 10px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 4px 10px;
                    background-color: {c['ACCENT']};
                    color: white;
                    border-radius: 4px;
                    margin-left: 10px;
                }}
            """,
            
            # ==================== REPORT BUILDER STYLES ====================
            
            'report_collapsible_header': f"""
                QPushButton#collapsibleHeader {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['ACCENT']}, stop:1 {c['ACCENT_HOVER']});
                    color: white;
                    border: none;
                    border-radius: 6px 6px 0 0;
                    padding: 12px 16px;
                    text-align: {'right' if cls.is_rtl() else 'left'};
                    font-weight: bold;
                    font-size: 12px;
                    font-family: {font_family};
                }}
                QPushButton#collapsibleHeader:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['ACCENT_HOVER']}, stop:1 {c['PRIMARY']});
                }}
            """,
            
            'report_collapsible_content': f"""
                QWidget#collapsibleContent {{
                    border: 2px solid {c['ACCENT']};
                    border-top: none;
                    border-radius: 0 0 6px 6px;
                    background-color: {c['WHITE']};
                }}
                QWidget#collapsibleContent QLabel {{
                    color: {c['TEXT_PRIMARY']};
                    font-size: 11px;
                    font-weight: 500;
                    padding: 2px 0;
                    background: transparent;
                    border: none;
                    font-family: {font_family};
                }}
                QWidget#collapsibleContent QComboBox {{
                    padding: 8px 12px;
                    border: 1.5px solid {c['BORDER']};
                    border-radius: 6px;
                    background-color: {c['WHITE']};
                    color: {c['TEXT_PRIMARY']};
                    font-size: 11px;
                    min-height: 18px;
                    font-family: {font_family};
                }}
                QWidget#collapsibleContent QComboBox:hover {{
                    border-color: {c['ACCENT']};
                }}
                QWidget#collapsibleContent QComboBox:focus {{
                    border-color: {c['ACCENT']};
                    border-width: 2px;
                }}
                QWidget#collapsibleContent QComboBox::drop-down {{
                    border: none;
                    width: 28px;
                    background-color: {c['LIGHT_BG']};
                    border-top-{'left' if cls.is_rtl() else 'right'}-radius: 6px;
                    border-bottom-{'left' if cls.is_rtl() else 'right'}-radius: 6px;
                    subcontrol-position: {'left' if cls.is_rtl() else 'right'};
                }}
                QWidget#collapsibleContent QComboBox::down-arrow {{
                    {chevron_down_style}
                    width: 16px;
                    height: 16px;
                }}
                QWidget#collapsibleContent QLineEdit {{
                    padding: 8px 12px;
                    border: 1.5px solid {c['BORDER']};
                    border-radius: 6px;
                    background-color: {c['WHITE']};
                    color: {c['TEXT_PRIMARY']};
                    font-size: 11px;
                    font-family: {font_family};
                }}
                QWidget#collapsibleContent QLineEdit:hover {{
                    border-color: {c['ACCENT']};
                }}
                QWidget#collapsibleContent QLineEdit:focus {{
                    border-color: {c['ACCENT']};
                    border-width: 2px;
                }}
                QWidget#collapsibleContent QCheckBox {{
                    color: {c['TEXT_PRIMARY']};
                    font-size: 11px;
                    font-weight: 500;
                    spacing: 8px;
                    padding: 4px 0;
                    background: transparent;
                    border: none;
                    font-family: {font_family};
                }}
                QWidget#collapsibleContent QCheckBox::indicator {{
                    width: 20px;
                    height: 20px;
                    border: 2px solid {c['BORDER']};
                    border-radius: 4px;
                    background-color: {c['WHITE']};
                }}
                QWidget#collapsibleContent QCheckBox::indicator:hover {{
                    border-color: {c['ACCENT']};
                }}
                QWidget#collapsibleContent QCheckBox::indicator:checked {{
                    background-color: {c['ACCENT']};
                    border-color: {c['ACCENT']};{checkmark_style}
                }}
                QWidget#collapsibleContent QSpinBox {{
                    padding: 6px 10px;
                    border: 1.5px solid {c['BORDER']};
                    border-radius: 6px;
                    background-color: {c['WHITE']};
                    color: {c['TEXT_PRIMARY']};
                    font-size: 11px;
                    min-width: 70px;
                    font-family: {font_family};
                }}
                QWidget#collapsibleContent QSpinBox:hover {{
                    border-color: {c['ACCENT']};
                }}
                QWidget#collapsibleContent QSpinBox:focus {{
                    border-color: {c['ACCENT']};
                    border-width: 2px;
                }}
            """,
            
            'report_splitter': f"""
                QSplitter::handle {{
                    background-color: {c['BORDER']};
                    margin: 0 6px;
                }}
                QSplitter::handle:hover {{
                    background-color: {c['ACCENT']};
                }}
            """,
            
            'report_separator': f"""
                background-color: {c['BORDER']};
                margin: 10px 0;
                border: none;
            """,
            
            'report_chart_type_label': f"""
                QLabel {{
                    color: {c['TEXT_PRIMARY']};
                    font-size: 11px;
                    font-weight: bold;
                    padding: 4px;
                    font-family: {font_family};
                }}
            """,
            
            'report_chart_combobox': f"""
                QComboBox {{
                    padding: 8px 14px;
                    font-size: 11px;
                    min-width: 180px;
                    border: 2px solid {c['BORDER']};
                    border-radius: 6px;
                    background-color: {c['WHITE']};
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
                QComboBox:hover {{
                    border-color: {c['ACCENT']};
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 24px;
                    subcontrol-position: {'left' if cls.is_rtl() else 'right'};
                }}
                QComboBox QAbstractItemView {{
                    background-color: {c['WHITE']};
                    selection-background-color: {c['ACCENT']};
                    selection-color: white;
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                }}
            """,
            
            'report_generate_button': f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['SUCCESS']}, stop:1 {c['SUCCESS_HOVER']});
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: bold;
                    font-size: 13px;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['SUCCESS_HOVER']}, stop:1 #1E8449);
                }}
                QPushButton:pressed {{
                    background-color: #1E8449;
                }}
            """,
            
            'report_preview_label': f"""
                QLabel {{
                    font-size: 14px;
                    font-weight: bold;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
            """,
            
            'report_chart_frame': f"""
                QFrame {{
                    background-color: {c['WHITE']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                }}
            """,
            
            'report_execute_button': f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['ACCENT']}, stop:1 {c['ACCENT_HOVER']});
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 12px;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['ACCENT_HOVER']}, stop:1 {c['PRIMARY']});
                }}
                QPushButton:pressed {{
                    background-color: {c['PRIMARY']};
                }}
            """,
            
            'report_clear_button': f"""
                QPushButton {{
                    background-color: {c['TEXT_SECONDARY']};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background-color: {c['TEXT_MUTED']};
                }}
            """,
            
            'report_scroll_transparent': f"""
                QScrollArea {{
                    background-color: transparent;
                    border: none;
                }}
                QScrollArea > QWidget > QWidget {{
                    background-color: transparent;
                }}
            """,
            
            'report_editor_label': f"""
                QLabel {{
                    font-weight: bold;
                    font-size: 12px;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
            """,
            
            'report_sql_editor': f"""
                QPlainTextEdit {{
                    font-family: Consolas, Monaco, monospace;
                    font-size: 11px;
                    background-color: #2D2D2D;
                    color: #F8F8F2;
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    padding: 8px;
                    selection-background-color: #44475A;
                }}
            """,
            
            'report_template_button': f"""
                QPushButton {{
                    text-align: center;
                    background-color: {c['LIGHT_BG']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    padding: 6px 8px;
                    font-size: 9px;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background-color: {c['ACCENT']};
                    color: white;
                    border-color: {c['ACCENT']};
                }}
            """,
            
            'report_fields_list': f"""
                QListWidget {{
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    background-color: {c['WHITE']};
                    font-size: 10px;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
                QListWidget::item {{
                    padding: 4px 8px;
                    border-radius: 3px;
                }}
                QListWidget::item:selected {{
                    background-color: {c['ACCENT']};
                    color: white;
                }}
                QListWidget::item:hover {{
                    background-color: {c['LIGHT_BG']};
                }}
            """,
            
            'report_add_filter_button': f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['ACCENT']}, stop:1 {c['ACCENT_HOVER']});
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: 600;
                    font-size: 11px;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['ACCENT_HOVER']}, stop:1 {c['PRIMARY']});
                }}
            """,
            
            'report_add_group_button': f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['SUCCESS']}, stop:1 {c['SUCCESS_HOVER']});
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: 600;
                    font-size: 11px;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['SUCCESS_HOVER']}, stop:1 #1E8449);
                }}
            """,
            
            'report_clear_filters_button': f"""
                QPushButton {{
                    background-color: {c['DANGER']};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: 600;
                    font-size: 11px;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background-color: {c['DANGER_HOVER']};
                }}
            """,
            
            'report_combine_label': f"""
                QLabel {{
                    font-size: 10px;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
            """,
            
            'report_global_logic_combo': f"""
                QComboBox {{
                    background-color: {c['WHITE']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 10px;
                    font-weight: bold;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
                QComboBox::drop-down {{
                    subcontrol-position: {'left' if cls.is_rtl() else 'right'};
                }}
            """,
            
            'report_filter_scroll': f"""
                QScrollArea {{
                    border: 1px solid {c['BORDER']};
                    border-radius: 6px;
                    background-color: {c['LIGHT_BG']};
                }}
            """,
            
            'report_quick_filters_label': f"""
                QLabel {{
                    font-size: 10px;
                    color: {c['TEXT_PRIMARY']};
                    font-weight: bold;
                    font-family: {font_family};
                }}
            """,
            
            'report_preset_button': f"""
                QPushButton {{
                    background-color: {c['WHITE']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    padding: 6px 12px;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background-color: {c['ACCENT']};
                    color: white;
                    border-color: {c['ACCENT']};
                }}
            """,
            
            'report_order_label': f"""
                QLabel {{
                    font-size: 10px;
                    color: {c['TEXT_PRIMARY']};
                    font-weight: bold;
                    font-family: {font_family};
                }}
            """,
            
            'report_limit_checkbox': f"""
                QCheckBox {{
                    font-size: 10px;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
            """,
            
            'report_limit_spinbox': f"""
                QSpinBox {{
                    background-color: {c['WHITE']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 10px;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
            """,
            
            'report_generated_sql': f"""
                QPlainTextEdit {{
                    font-family: Consolas, Monaco, monospace;
                    font-size: 10px;
                    background-color: {c['LIGHT_BG']};
                    color: {c['TEXT_PRIMARY']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    padding: 6px;
                }}
            """,
            
            'report_filter_widget': f"""
                QFrame {{
                    background-color: {c['WHITE']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 6px;
                    margin: 2px;
                }}
            """,
            
            'report_filter_combo': f"""
                QComboBox {{
                    background-color: {c['WHITE']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 10px;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
                QComboBox:hover {{
                    border-color: {c['ACCENT']};
                }}
                QComboBox::drop-down {{
                    subcontrol-position: {'left' if cls.is_rtl() else 'right'};
                }}
            """,
            
            'report_remove_button': f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['DANGER']}, stop:1 {c['DANGER_HOVER']});
                    color: white;
                    border: none;
                    border-radius: 13px;
                    font-weight: bold;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['DANGER_HOVER']}, stop:1 #A93226);
                }}
            """,
            
            'report_filter_group': f"""
                QFrame {{
                    background-color: #EBF5FB;
                    border: 2px solid {c['ACCENT']};
                    border-radius: 6px;
                    margin: 4px;
                    padding: 8px;
                }}
            """,
            
            'report_remove_group_button': f"""
                QPushButton {{
                    background-color: {c['DANGER']};
                    color: white;
                    border-radius: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {c['DANGER_HOVER']};
                }}
            """,
            
            'report_tab_bar': f"""
                QTabBar::tab {{
                    min-width: 120px;
                    max-width: 200px;
                    padding: 10px 16px;
                    margin: 2px;
                    font-family: {font_family};
                    font-size: 11px;
                }}
            """,
            
            'report_results_info': f"""
                QLabel {{
                    font-size: 12px;
                    color: {c['TEXT_SECONDARY']};
                    padding: 5px;
                    font-family: {font_family};
                }}
            """,
            
            'report_results_table': f"""
                QTableWidget {{
                    background-color: {c['WHITE']};
                    gridline-color: {c['BORDER']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    font-size: 10px;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
                QTableWidget::item {{
                    padding: 6px;
                }}
                QTableWidget::item:selected {{
                    background-color: {c['ACCENT']};
                    color: white;
                }}
                QHeaderView::section {{
                    background-color: {c['TABLE_HEADER']};
                    color: white;
                    padding: 8px;
                    border: none;
                    font-weight: bold;
                    font-family: {font_family};
                }}
            """,
            
            # ==================== TOOLBAR STYLES ====================
            
            'toolbar_label': f"""
                QLabel {{
                    font-weight: bold;
                    font-size: 11px;
                    padding: 0 4px;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
            """,
            
            'toolbar_scroll': f"""
                QScrollArea {{
                    background-color: transparent;
                    border: none;
                }}
                QScrollArea > QWidget > QWidget {{
                    background-color: transparent;
                }}
                QScrollBar:horizontal {{
                    background: {c['LIGHT_BG']};
                    height: 8px;
                    border-radius: 4px;
                    margin: 0px;
                }}
                QScrollBar::handle:horizontal {{
                    background: {c['BORDER']};
                    border-radius: 3px;
                    min-width: 20px;
                }}
                QScrollBar::handle:horizontal:hover {{
                    background: {c['TEXT_SECONDARY']};
                }}
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                    width: 0px;
                }}
            """,
            
            'toolbar_separator': f"""
                color: {c['BORDER']};
            """,
            
            # ==================== FILTER INPUT STYLES ====================
            
            'filter_value_input': f"""
                QLineEdit {{
                    background-color: {c['INPUT_BG']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 10px;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
                QLineEdit:focus {{
                    border-color: {c['ACCENT']};
                }}
            """,
            
            'view_mode_active': f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['ACCENT']}, stop:1 {c['ACCENT_HOVER']});
                    color: white;
                    border: 2px solid {c['ACCENT_HOVER']};
                    border-radius: 8px;
                    padding: 10px 16px;
                    font-weight: bold;
                    font-size: 12px;
                    font-family: {font_family};
                }}
            """,
            
            'view_mode_inactive': f"""
                QPushButton {{
                    background-color: {c['WHITE']};
                    color: {c['TEXT_PRIMARY']};
                    border: 2px solid {c['BORDER']};
                    border-radius: 8px;
                    padding: 10px 16px;
                    font-weight: 500;
                    font-size: 12px;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background-color: {c['LIGHT_BG']};
                    border-color: {c['ACCENT']};
                    color: {c['ACCENT_HOVER']};
                }}
            """,
            
            'report_execute_button': f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['SUCCESS']}, stop:1 {c['SUCCESS_HOVER']});
                    color: white;
                    font-weight: bold;
                    font-size: 12px;
                    padding: 12px 30px;
                    border: none;
                    border-radius: 6px;
                    min-height: 20px;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #58D68D, stop:1 {c['SUCCESS']});
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #1E8449, stop:1 #196F3D);
                }}
            """,
            
            'report_clear_button': f"""
                QPushButton {{
                    background-color: {c['TEXT_SECONDARY']};
                    color: white;
                    font-weight: bold;
                    padding: 12px 20px;
                    border: none;
                    border-radius: 6px;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background-color: {c['TEXT_MUTED']};
                }}
                QPushButton:pressed {{
                    background-color: #616A6B;
                }}
            """,
            
            'report_main_scroll': f"""
                QScrollArea {{
                    background-color: transparent;
                    border: none;
                }}
                QScrollBar:vertical {{
                    background: {c['LIGHT_BG']};
                    width: 10px;
                    border-radius: 5px;
                }}
                QScrollBar::handle:vertical {{
                    background: {c['BORDER']};
                    border-radius: 4px;
                    min-height: 30px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {c['TEXT_SECONDARY']};
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
            """,
            
            'report_editor_label': f"""
                QLabel {{
                    font-weight: bold;
                    font-size: 12px;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
            """,
            
            'report_sql_editor': f"""
                QPlainTextEdit {{
                    font-family: Consolas, Monaco, monospace;
                    font-size: 13px;
                    background-color: #1E1E1E;
                    color: #D4D4D4;
                    border: 1px solid #3C3C3C;
                    border-radius: 4px;
                    padding: 8px;
                }}
            """,
            
            'report_template_button': f"""
                QPushButton {{
                    text-align: center;
                    padding: 8px 4px;
                    border: 1px solid {c['ACCENT']};
                    border-radius: 4px;
                    background-color: {c['LIGHT_BG']};
                    color: {c['TEXT_PRIMARY']};
                    font-size: 9pt;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background-color: {c['ACCENT']};
                    color: white;
                }}
            """,
            
            'report_fields_list': f"""
                QListWidget {{
                    border: 1px solid {c['BORDER']};
                    border-radius: 6px;
                    background-color: {c['LIGHT_BG']};
                    padding: 5px;
                    font-size: 10px;
                    font-family: {font_family};
                }}
                QListWidget::item {{
                    padding: 4px 8px;
                    border-radius: 3px;
                    margin: 1px 0;
                }}
                QListWidget::item:selected {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['ACCENT']}, stop:1 {c['ACCENT_HOVER']});
                    color: white;
                }}
                QListWidget::item:hover {{
                    background-color: {c['WHITE']};
                }}
            """,
            
            'report_visual_fields_list': f"""
                QListWidget {{
                    border: 1px solid {c['BORDER']};
                    border-radius: 6px;
                    background-color: {c['LIGHT_BG']};
                    padding: 5px;
                    font-size: 10px;
                    font-family: {font_family};
                }}
                QListWidget::item {{
                    padding: 4px 8px;
                    border-radius: 3px;
                    margin: 1px 0;
                }}
                QListWidget::item:selected {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['ACCENT']}, stop:1 {c['ACCENT_HOVER']});
                    color: white;
                }}
                QListWidget::item:hover {{
                    background-color: {c['WHITE']};
                }}
            """,
            
            'report_add_filter_btn': f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['SUCCESS']}, stop:1 #1E8449);
                    color: white;
                    font-weight: bold;
                    font-size: 10px;
                    padding: 8px 14px;
                    border: none;
                    border-radius: 5px;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2ECC71, stop:1 {c['SUCCESS']});
                }}
            """,
            
            'report_add_group_btn': f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['ACCENT']}, stop:1 {c['ACCENT_HOVER']});
                    color: white;
                    font-weight: bold;
                    font-size: 10px;
                    padding: 8px 14px;
                    border: none;
                    border-radius: 5px;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #5DADE2, stop:1 {c['ACCENT']});
                }}
            """,
            
            'report_clear_filters_btn': f"""
                QPushButton {{
                    background-color: {c['DANGER']};
                    color: white;
                    font-weight: bold;
                    font-size: 10px;
                    padding: 8px 14px;
                    border: none;
                    border-radius: 5px;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background-color: #C0392B;
                }}
            """,
            
            'report_combine_label': f"""
                QLabel {{
                    font-size: 10px;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
            """,
            
            'report_global_logic_combo': f"""
                QComboBox {{
                    background-color: {c['WHITE']};
                    border: 2px solid {c['ACCENT']};
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-weight: bold;
                    font-size: 10px;
                    min-width: 70px;
                    font-family: {font_family};
                }}
                QComboBox:hover {{
                    border-color: {c['ACCENT_HOVER']};
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 25px;
                }}
                QComboBox::down-arrow {{
                    {chevron_down_style}
                    width: 16px;
                    height: 16px;
                }}
            """,
            
            'report_filter_scroll': f"""
                QScrollArea {{
                    border: 1px solid {c['BORDER']};
                    border-radius: 6px;
                    background-color: {c['LIGHT_BG']};
                }}
            """,
            
            'report_quick_filters_label': f"""
                QLabel {{
                    font-size: 10px;
                    color: {c['TEXT_PRIMARY']};
                    font-weight: bold;
                    font-family: {font_family};
                }}
            """,
            
            'report_quick_filter_btn': f"""
                QPushButton {{
                    background-color: {c['WHITE']};
                    color: {c['ACCENT']};
                    font-size: 10px;
                    font-weight: bold;
                    padding: 6px 12px;
                    border: 2px solid {c['ACCENT']};
                    border-radius: 15px;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background-color: {c['ACCENT']};
                    color: white;
                }}
                QPushButton:pressed {{
                    background-color: {c['ACCENT_HOVER']};
                }}
            """,
            
            'report_importance_filter_btn': f"""
                QPushButton {{
                    background-color: {c['WHITE']};
                    color: #E67E22;
                    font-size: 10px;
                    font-weight: bold;
                    padding: 6px 12px;
                    border: 2px solid #E67E22;
                    border-radius: 15px;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background-color: #E67E22;
                    color: white;
                }}
                QPushButton:pressed {{
                    background-color: #D35400;
                }}
            """,
            
            'report_order_label': f"""
                QLabel {{
                    font-size: 10px;
                    color: {c['TEXT_PRIMARY']};
                    font-weight: bold;
                    font-family: {font_family};
                }}
            """,
            
            'report_generate_button': f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['SUCCESS']}, stop:1 {c['SUCCESS_HOVER']});
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 20px;
                    font-weight: bold;
                    font-size: 13px;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2ECC71, stop:1 {c['SUCCESS']});
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #1E8449, stop:1 #196F3D);
                }}
            """,
            
            'report_preview_label': f"""
                QLabel {{
                    font-size: 14px;
                    font-weight: bold;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
            """,
            
            'report_chart_frame': f"""
                QFrame {{
                    background-color: {c['WHITE']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                }}
            """,
            
            'report_visual_group': f"""
                QGroupBox {{
                    font-weight: bold;
                    font-size: 11px;
                    color: {c['TEXT_PRIMARY']};
                    border: 2px solid {c['ACCENT']};
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 10px;
                    background-color: {c['WHITE']};
                    font-family: {font_family};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top {cls.get_opposite_align()};
                    padding: 4px 12px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['ACCENT']}, stop:1 {c['ACCENT_HOVER']});
                    color: white;
                    border-radius: 4px;
                }}
            """,
            
            'report_limit_checkbox': f"""
                QCheckBox {{
                    font-size: 10px;
                    color: {c['TEXT_PRIMARY']};
                    font-weight: bold;
                    spacing: 8px;
                    font-family: {font_family};
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border-radius: 4px;
                    border: 2px solid {c['BORDER']};
                    background-color: {c['WHITE']};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {c['ACCENT']};
                    border-color: {c['ACCENT']};{checkmark_style}
                }}
                QCheckBox::indicator:hover {{
                    border-color: {c['ACCENT']};
                }}
            """,
            
            'report_limit_spinbox': f"""
                QSpinBox {{
                    background-color: {c['WHITE']};
                    border: 2px solid {c['BORDER']};
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-size: 10px;
                    min-width: 80px;
                    font-family: {font_family};
                }}
                QSpinBox:hover {{
                    border-color: {c['ACCENT']};
                }}
                QSpinBox:focus {{
                    border-color: {c['ACCENT']};
                }}
                QSpinBox::up-button, QSpinBox::down-button {{
                    width: 20px;
                    border: none;
                    background-color: {c['LIGHT_BG']};
                }}
                QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                    background-color: {c['ACCENT']};
                }}
            """,
            
            'report_generated_sql': f"""
                QPlainTextEdit {{
                    font-family: Consolas, Monaco, monospace;
                    font-size: 10px;
                    background-color: #2C3E50;
                    color: #ECF0F1;
                    border: 2px solid #34495E;
                    border-radius: 6px;
                    padding: 8px;
                }}
            """,
            
            'report_filter_row_frame': f"""
                QFrame {{ 
                    background-color: {c['WHITE']}; 
                    border: 1px solid {c['BORDER']}; 
                    border-radius: 6px;
                    border-left: 4px solid {c['ACCENT']};
                }}
            """,
            
            'report_filter_combo': f"""
                QComboBox {{
                    background-color: {c['WHITE']};
                    border: 1px solid {c['BORDER']};
                    border-radius: 4px;
                    padding: 5px 8px;
                    font-size: 10px;
                    font-family: {font_family};
                }}
                QComboBox:hover {{
                    border-color: {c['ACCENT']};
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 20px;
                }}
                QComboBox::down-arrow {{
                    {chevron_down_style}
                    width: 16px;
                    height: 16px;
                }}
            """,
            
            'report_remove_btn': f"""
                QPushButton {{ 
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {c['DANGER']}, stop:1 #C0392B);
                    color: white; 
                    border-radius: 13px; 
                    font-weight: bold;
                    font-size: 14px;
                    border: none;
                }}
                QPushButton:hover {{ 
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #FF6B6B, stop:1 {c['DANGER']});
                }}
            """,
            
            'report_filter_group_frame': f"""
                QFrame {{ 
                    background-color: {c['LIGHT_BG']}; 
                    border: 2px solid {c['ACCENT']}; 
                    border-radius: 6px; 
                    margin: 5px;
                }}
            """,
            
            'report_small_remove_btn': f"""
                QPushButton {{ 
                    background-color: {c['DANGER']}; 
                    color: white; 
                    border-radius: 12px; 
                    font-weight: bold; 
                }}
                QPushButton:hover {{ 
                    background-color: #C0392B; 
                }}
            """,
            
            'report_tab_bar': f"""
                QTabBar::tab {{
                    min-width: 120px;
                    padding: 8px 16px;
                    font-size: 11px;
                    font-weight: bold;
                    font-family: {font_family};
                }}
            """,
            
            'report_results_info': f"""
                QLabel {{
                    font-size: 12px;
                    color: {c['TEXT_SECONDARY']};
                    padding: 5px;
                    font-family: {font_family};
                }}
            """,
            
            'report_results_table': f"""
                QTableWidget {{
                    background-color: {c['WHITE']};
                    border: 1px solid {c['BORDER']};
                    gridline-color: {c['LIGHT_BG']};
                    font-family: {font_family};
                }}
                QHeaderView::section {{
                    background-color: {c['TABLE_HEADER']};
                    color: white;
                    padding: 8px;
                    border: none;
                    font-weight: bold;
                }}
            """,
            
            'report_preview_editor': f"""
                QTextEdit {{
                    background-color: {c['WHITE']};
                    border: 1px solid {c['BORDER']};
                    padding: 20px;
                    font-family: {font_family};
                }}
            """,
            
            'autocomplete_popup': f"""
                QListView {{
                    background-color: {c['WHITE']};
                    border: 1px solid {c['ACCENT']};
                    border-radius: 4px;
                    padding: 4px;
                    font-size: 12px;
                    font-family: {font_family};
                }}
                QListView::item {{
                    padding: 6px 10px;
                    border-radius: 2px;
                }}
                QListView::item:hover {{
                    background-color: {c['LIGHT_BG']};
                }}
                QListView::item:selected {{
                    background-color: {c['ACCENT']};
                    color: white;
                }}
            """,
            
            'new_entry_highlight': f"""
                QLineEdit {{
                    border: 2px solid {c['SUCCESS']};
                    border-radius: 4px;
                    padding: 6px;
                    background-color: #E8F8F5;
                    font-family: {font_family};
                }}
            """,
            
            'status_label_muted': f"""
                QLabel {{
                    color: {c['TEXT_SECONDARY']};
                    font-size: 10px;
                    font-family: {font_family};
                }}
            """,
            
            'attachment_label_empty': f"""
                QLabel {{
                    color: {c['TEXT_SECONDARY']};
                    font-style: italic;
                    font-family: {font_family};
                }}
            """,
            
            'attachment_label_filled': f"""
                QLabel {{
                    color: {c['TEXT_PRIMARY']};
                    font-style: normal;
                    font-family: {font_family};
                }}
            """,
            
            'status_label_error': f"""
                QLabel {{
                    color: {c['DANGER']};
                    font-size: 10px;
                    font-family: {font_family};
                }}
            """,
            
            'status_label_success': f"""
                QLabel {{
                    color: {c['SUCCESS']};
                    font-size: 10px;
                    font-family: {font_family};
                }}
            """,
            
            'input_error': f"""
                QLineEdit {{
                    border: 2px solid {c['DANGER']};
                    font-family: {font_family};
                }}
            """,
            
            'attachment_manager_title': f"""
                QLabel {{
                    font-weight: 700;
                    font-size: 12pt;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                    padding: 4px 0px;
                }}
            """,
            
            'attachment_manager_count': f"""
                QLabel {{
                    color: {c['ACCENT']};
                    font-size: 11pt;
                    font-weight: 600;
                    font-family: {font_family};
                    padding: 2px 8px;
                    background-color: {c['LIGHT_BG']};
                    border-radius: 10px;
                }}
            """,
            
            'attachment_list': f"""
                QListWidget {{
                    border: 2px dashed {c['BORDER']};
                    border-radius: 10px;
                    background-color: {c['LIGHT_BG']};
                    background-image: none;
                    min-height: 150px;
                    font-family: {font_family};
                    padding: 8px;
                }}
                QListWidget:focus {{
                    border-color: {c['ACCENT']};
                    border-style: solid;
                }}
                QListWidget::item {{
                    padding: 10px 12px;
                    border-radius: 8px;
                    margin: 4px 2px;
                    background-color: {c['WHITE']};
                    border: 1px solid {c['BORDER']};
                }}
                QListWidget::item:selected {{
                    background-color: {c['ACCENT']};
                    color: white;
                    border: 1px solid {c['ACCENT']};
                }}
                QListWidget::item:hover:!selected {{
                    background-color: {c['WHITE']};
                    border: 1px solid {c['ACCENT']};
                }}
            """,
            
            'drop_hint': f"""
                QLabel {{
                    color: {c['TEXT_SECONDARY']};
                    font-size: 11pt;
                    font-style: italic;
                    padding: 30px;
                    font-family: {font_family};
                    background-color: transparent;
                    border: none;
                    qproperty-alignment: AlignCenter;
                }}
            """,
            
            'preview_placeholder': f"""
                QLabel {{
                    background-color: {c['LIGHT_BG']};
                    border: 1px solid {c['BORDER']};
                    font-family: {font_family};
                }}
            """,
            
            'pdf_preview_placeholder': f"""
                QLabel {{
                    background-color: {c['LIGHT_BG']}; 
                    border: 1px solid {c['BORDER']};
                    min-height: 400px;
                    font-size: 14pt;
                    color: {c['TEXT_MUTED']};
                    font-family: {font_family};
                }}
            """,
            
            'document_preview': f"""
                QTextEdit {{
                    background-color: {c['WHITE']};
                    border: 1px solid {c['BORDER']};
                    font-family: 'Courier New', monospace;
                    font-size: 10pt;
                }}
            """,
            
            'preview_title': f"""
                QLabel {{
                    font-size: 16pt;
                    font-weight: bold;
                    padding: 10px;
                    font-family: {font_family};
                }}
            """,
            
            'print_preview_frame': f"""
                QFrame {{
                    background-color: {c['WHITE']};
                    border: 2px solid {c['TEXT_PRIMARY']};
                    border-radius: 8px;
                }}
            """,
            
            'print_tabs': f"""
                QTabWidget::pane {{ border: 1px solid {c['BORDER']}; border-radius: 4px; }}
                QTabBar::tab {{ padding: 8px 16px; font-family: {font_family}; }}
                QTabBar::tab:selected {{ background: {c['ACCENT']}; color: white; }}
            """,
            
            'print_logo_preview': f"""
                QLabel {{
                    border: 2px dashed {c['BORDER']};
                    background: {c['LIGHT_BG']};
                    border-radius: 8px;
                    font-family: {font_family};
                }}
            """,
            
            'print_select_logo_btn': f"""
                QPushButton {{
                    background: {c['ACCENT']};
                    color: white;
                    padding: 8px 16px;
                    font-family: {font_family};
                }}
            """,
            
            'print_save_btn': f"""
                QPushButton {{
                    background: {c['SUCCESS']};
                    color: white;
                    padding: 10px 25px;
                    font-weight: bold;
                    font-family: {font_family};
                }}
            """,
            
            'print_preview_label_primary': f"""
                QLabel {{
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
            """,
            
            'print_preview_label_secondary': f"""
                QLabel {{
                    color: {c['TEXT_SECONDARY']};
                    font-family: {font_family};
                }}
            """,
            
            'print_preview_label_muted': f"""
                QLabel {{
                    color: {c['TEXT_MUTED']};
                    font-family: {font_family};
                }}
            """,
            
            'print_info_box': f"""
                QLabel {{
                    background: {c['LIGHT_BG']};
                    padding: 10px;
                    border-radius: 4px;
                    color: {c['ACCENT_HOVER']};
                    font-family: {font_family};
                }}
            """,
            
            'print_total_label': f"""
                QLabel {{
                    font-weight: bold;
                    padding: 8px;
                    font-size: 12pt;
                    font-family: {font_family};
                }}
            """,
            
            'print_column_frame': f"""
                QFrame {{ 
                    background: {c['LIGHT_BG']}; 
                    border: 1px solid {c['BORDER']}; 
                    border-radius: 6px; 
                    padding: 8px;
                }}
                QFrame:hover {{
                    background: #F0F0F0;
                    border-color: {c['ACCENT']};
                }}
            """,
            
            'print_equal_btn': f"""
                QPushButton {{
                    background: {c['ACCENT']};
                    color: white;
                    font-family: {font_family};
                }}
            """,
            
            'print_ok_btn': f"""
                QPushButton {{
                    background: {c['SUCCESS']};
                    color: white;
                    padding: 10px 25px;
                    font-family: {font_family};
                }}
            """,
            
            'print_total_valid': f"""
                QLabel {{
                    color: {c['SUCCESS']};
                    font-weight: bold;
                    padding: 8px;
                    font-family: {font_family};
                }}
            """,
            
            'print_total_error': f"""
                QLabel {{
                    color: {c['DANGER']};
                    font-weight: bold;
                    padding: 8px;
                    font-family: {font_family};
                }}
            """,
            
            'print_total_warning': f"""
                QLabel {{
                    color: {c['WARNING']};
                    font-weight: bold;
                    padding: 8px;
                    font-family: {font_family};
                }}
            """,
            
            'export_stats_frame': f"""
                QFrame {{
                    background-color: {c['LIGHT_BG']};
                    border: 1px solid {c['ACCENT']};
                    border-radius: 6px;
                    padding: 10px;
                }}
            """,
            
            'export_stats_label': f"""
                QLabel {{
                    font-weight: bold;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
            """,
            
            'export_stats_count': f"""
                QLabel {{
                    font-weight: bold;
                    color: {c['ACCENT']};
                    font-size: 16px;
                    font-family: {font_family};
                }}
            """,
            
            'export_stats_count_green': f"""
                QLabel {{
                    font-weight: bold;
                    color: {c['SUCCESS']};
                    font-size: 16px;
                    font-family: {font_family};
                }}
            """,
            
            'export_preview_table': f"""
                QTableWidget {{
                    gridline-color: {c['BORDER']};
                    font-size: 11px;
                    font-family: {font_family};
                }}
                QTableWidget::item {{
                    padding: 5px;
                }}
                QHeaderView::section {{
                    background-color: {c['ACCENT']};
                    color: white;
                    padding: 6px;
                    border: none;
                    font-weight: bold;
                }}
            """,
            
            'export_format_label': f"""
                QLabel {{
                    font-weight: bold;
                    font-family: {font_family};
                }}
            """,
            
            'export_separator': f"""
                QFrame {{
                    background-color: {c['BORDER']};
                }}
            """,
            
            'export_checkbox_bold': f"""
                QCheckBox {{
                    font-weight: bold;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
            """,
            
            'export_checkbox_green': f"""
                QCheckBox {{
                    font-weight: bold;
                    color: {c['SUCCESS']};
                    font-family: {font_family};
                }}
            """,
            
            'export_btn': f"""
                QPushButton {{
                    background-color: {c['SUCCESS']};
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 12px 30px;
                    border-radius: 6px;
                    font-family: {font_family};
                }}
                QPushButton:hover {{
                    background-color: #2ECC71;
                }}
            """,
            
            'export_cancel_btn': f"""
                QPushButton {{
                    padding: 10px 20px;
                    font-family: {font_family};
                }}
            """,
            
            'export_checkbox_primary': f"""
                QCheckBox {{
                    font-weight: bold;
                    color: {c['TEXT_PRIMARY']};
                    font-family: {font_family};
                }}
            """,
            
            'export_checkbox_secondary': f"""
                QCheckBox {{
                    color: {c['TEXT_SECONDARY']};
                    font-family: {font_family};
                }}
            """,
            
            'export_width_label': f"""
                QLabel {{
                    color: {c['TEXT_SECONDARY']};
                    font-size: 10px;
                    font-family: {font_family};
                }}
            """,
            
            'export_width_spin': f"""
                QSpinBox {{
                    padding: 3px;
                    border: 1px solid {c['BORDER']};
                    border-radius: 3px;
                    background: {c['WHITE']};
                    font-family: {font_family};
                }}
                QSpinBox:focus {{
                    border-color: {c['ACCENT']};
                }}
            """,
            
            'settings_scroll': f"""
                QScrollArea {{
                    background-color: transparent;
                    border: none;
                }}
                QScrollBar:vertical {{
                    background: {c['LIGHT_BG']};
                    width: 10px;
                    border-radius: 5px;
                }}
                QScrollBar::handle:vertical {{
                    background: {c['BORDER']};
                    border-radius: 4px;
                    min-height: 30px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {c['TEXT_SECONDARY']};
                }}
            """,
        }
        
        return components.get(component, "")
    
    # ==================== PAGINATION WIDGET STYLES ====================
    
    @classmethod
    def get_pagination_style(cls, scale_factor: float = 1.0) -> str:
        """Get pagination widget stylesheet - Premium Modern Design"""
        c = cls._colors
        base_font = max(11, int(11 * scale_factor))
        small_font = max(10, int(10 * scale_factor))
        
        return f"""
            #paginationWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {c['LIGHT_BG']}, stop:1 #EDF2F7);
                border: 1px solid {c['BORDER']};
                border-radius: 6px;
            }}
            
            #paginationScroll {{
                background: transparent;
                border: none;
            }}
            
            #paginationContent {{
                background: transparent;
            }}
            
            QScrollBar:horizontal {{
                height: 6px;
                background: transparent;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: {c['BORDER']};
                border-radius: 3px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {c['TEXT_MUTED']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
            
            #navFrame {{
                background-color: white;
                border: 1px solid {c['BORDER']};
                border-radius: 6px;
            }}
            
            QPushButton {{
                background-color: white;
                border: 1px solid {c['BORDER']};
                border-radius: 4px;
                font-size: {base_font}px;
                font-weight: bold;
                color: {c['TEXT_PRIMARY']};
                padding: 4px;
            }}
            QPushButton:hover:enabled {{
                background-color: {c['ACCENT']};
                border-color: {c['ACCENT']};
                color: white;
            }}
            QPushButton:pressed:enabled {{
                background-color: {c['ACCENT_HOVER']};
            }}
            QPushButton:disabled {{
                background-color: #F1F5F9;
                border-color: #E2E8F0;
                color: #CBD5E1;
            }}
            
            #pageFrame {{
                background-color: #EBF5FB;
                border: 1px solid {c['ACCENT']};
                border-radius: 4px;
            }}
            
            #pageLabel {{
                color: {c['ACCENT']};
                font-weight: 600;
                font-size: {small_font}px;
            }}
            
            #totalPagesLabel {{
                color: {c['TEXT_MUTED']};
                font-weight: 500;
                font-size: {small_font}px;
            }}
            
            #pageSpin {{
                background-color: white;
                border: 1px solid {c['ACCENT']};
                border-radius: 4px;
                padding: 2px;
                font-weight: bold;
                font-size: {small_font}px;
                color: {c['ACCENT']};
            }}
            #pageSpin:focus {{
                border-color: {c['ACCENT_HOVER']};
                border-width: 2px;
            }}
            #pageSpin::up-button, #pageSpin::down-button {{
                width: 16px;
                border: none;
                background-color: {c['ACCENT']};
            }}
            #pageSpin::up-button:hover, #pageSpin::down-button:hover {{
                background-color: {c['ACCENT_HOVER']};
            }}
            #pageSpin::up-arrow {{
                {chevron_up_style}
                width: 14px;
                height: 14px;
            }}
            #pageSpin::down-arrow {{
                {chevron_down_style}
                width: 14px;
                height: 14px;
            }}
            
            #sizeFrame {{
                background-color: white;
                border: 1px solid {c['BORDER']};
                border-radius: 6px;
            }}
            
            #pageSizeLabel {{
                color: {c['TEXT_MUTED']};
                font-size: {small_font}px;
                font-weight: 500;
            }}
            
            #pageSizeCombo {{
                background-color: {c['LIGHT_BG']};
                border: 1px solid {c['BORDER']};
                border-radius: 4px;
                padding: 3px 6px;
                font-weight: 600;
                font-size: {small_font}px;
                color: {c['TEXT_PRIMARY']};
            }}
            #pageSizeCombo:hover {{
                border-color: {c['ACCENT']};
            }}
            #pageSizeCombo::drop-down {{
                border: none;
                width: 16px;
            }}
            #pageSizeCombo::down-arrow {{
                {chevron_down_style}
                width: 14px;
                height: 14px;
            }}
            #pageSizeCombo QAbstractItemView {{
                background-color: white;
                border: 1px solid {c['BORDER']};
                border-radius: 4px;
                selection-background-color: {c['ACCENT']};
                selection-color: white;
            }}
            
            #infoFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {c['SUCCESS']}, stop:1 #2ECC71);
                border: none;
                border-radius: 6px;
            }}
            
            #itemsLabel {{
                color: white;
                font-weight: 600;
                font-size: {small_font}px;
            }}
        """
    
    @classmethod
    def get_premium_pagination_style(cls, scale_factor: float = 1.0) -> str:
        """Get premium pagination widget stylesheet with modern compact design"""
        c = cls._colors
        # Compact font sizes
        base_font = max(12, int(12 * scale_factor))
        small_font = max(11, int(11 * scale_factor))
        # Smaller button size for compact design
        btn_size = max(36, int(36 * scale_factor))
        indicator_height = max(36, int(36 * scale_factor))
        
        # Modern blue accent colors (matching app theme)
        accent_color = c['ACCENT']
        accent_hover = c['ACCENT_HOVER']
        chevron_down_url = cls._get_icon_image_path('chevron_down')
        chevron_down_style = f'image: url({chevron_down_url});' if chevron_down_url else ''
        
        return f"""
            /* Main Container */
            #premiumPaginationContainer {{
                background-color: {c['LIGHT_BG']};
                border: 1px solid {c['BORDER']};
                border-radius: 8px;
            }}
            
            /* Records Info Label */
            #recordsInfoLabel {{
                color: {c['TEXT_PRIMARY']};
                font-size: {base_font}px;
                font-weight: 600;
                background-color: {c['LIGHT_BG']};
                padding: 8px 16px;
                border-radius: 8px;
            }}
            
            /* Circular Navigation Buttons - Compact */
            #circularNavButton {{
                background-color: {c['WHITE']};
                color: {c['TEXT_SECONDARY']};
                border: 1px solid {c['BORDER']};
                border-radius: {btn_size // 2}px;
                min-width: {btn_size}px;
                min-height: {btn_size}px;
                max-width: {btn_size}px;
                max-height: {btn_size}px;
            }}
            #circularNavButton:hover:enabled {{
                background-color: {accent_color};
                color: white;
                border: 1px solid {accent_color};
            }}
            #circularNavButton:pressed:enabled {{
                background-color: {accent_hover};
            }}
            #circularNavButton:disabled {{
                background-color: {c['LIGHT_BG']};
                color: {c['TEXT_MUTED']};
                border: 1px solid {c['BORDER']};
            }}
            
            /* Page Indicator Label - Compact Pill */
            #pageIndicatorButton {{
                background-color: {accent_color};
                color: white;
                border: none;
                border-radius: {indicator_height // 2}px;
                font-size: {base_font}px;
                font-weight: 600;
                padding: 0px 20px;
                min-height: {indicator_height}px;
                min-width: 120px;
            }}
            
            /* Modern SpinBox - Compact */
            #modernPageSpinBox {{
                background-color: {c['WHITE']};
                border: 1px solid {c['BORDER']};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: {base_font}px;
                font-weight: 600;
                color: {c['TEXT_PRIMARY']};
                min-height: {btn_size}px;
                min-width: 60px;
                max-width: 70px;
            }}
            #modernPageSpinBox:hover {{
                border: 1px solid {accent_color};
            }}
            #modernPageSpinBox:focus {{
                border: 2px solid {accent_color};
                padding: 3px 7px;
            }}
            #modernPageSpinBox::up-button, #modernPageSpinBox::down-button {{
                width: 0px;
            }}
            
            /* Modern ComboBox - Compact */
            #modernPageSizeCombo {{
                background-color: {c['WHITE']};
                border: 1px solid {c['BORDER']};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: {base_font}px;
                font-weight: 600;
                color: {c['TEXT_PRIMARY']};
                min-height: {btn_size}px;
                min-width: 65px;
                max-width: 75px;
            }}
            #modernPageSizeCombo:hover {{
                border: 1px solid {accent_color};
            }}
            #modernPageSizeCombo::drop-down {{
                border: none;
                width: 20px;
            }}
            #modernPageSizeCombo::down-arrow {{
                {chevron_down_style}
                width: 16px;
                height: 16px;
                margin-right: 4px;
            }}
            #modernPageSizeCombo QAbstractItemView {{
                background-color: {c['WHITE']};
                border: 1px solid {c['BORDER']};
                border-radius: 6px;
                selection-background-color: {accent_color};
                selection-color: white;
                padding: 4px;
                font-weight: 600;
                outline: none;
            }}
            
            /* Items Per Page Label */
            #itemsPerPageLabel {{
                color: {c['TEXT_SECONDARY']};
                font-size: {small_font}px;
                font-weight: 500;
            }}
        """
    
    # ==================== WINDOW SIZE UTILITIES ====================
    
    @staticmethod
    def apply_fixed_size(dialog, width: int, height: int):
        """
        Apply initial size to a dialog/window while allowing user to resize.
        Sets minimum size based on content and allows expansion.
        
        Args:
            dialog: QDialog or QWidget to apply size to
            width: Initial/minimum width in pixels
            height: Initial/minimum height in pixels
        """
        from PyQt5.QtWidgets import QSizePolicy
        from PyQt5.QtCore import QSize
        
        # Set minimum size to ensure content is readable
        dialog.setMinimumSize(int(width * 0.7), int(height * 0.7))
        
        # Set initial size (resize to this)
        dialog.resize(width, height)
        
        # Allow resizing - set size policy to Preferred
        dialog.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
        # Adjust to content if possible
        if hasattr(dialog, 'adjustSize'):
            dialog.adjustSize()
            # Ensure we don't go smaller than content requires
            content_size = dialog.sizeHint()
            if content_size.isValid():
                final_width = max(width, content_size.width())
                final_height = max(height, content_size.height())
                dialog.resize(final_width, final_height)
    
    @staticmethod
    def apply_fixed_width(widget, width: int):
        """
        Apply fixed width to a widget to prevent horizontal resizing.
        
        Args:
            widget: QWidget to apply fixed width to
            width: Fixed width in pixels
        """
        from PyQt5.QtWidgets import QSizePolicy
        
        widget.setFixedWidth(width)
        widget.setSizePolicy(QSizePolicy.Fixed, widget.sizePolicy().verticalPolicy())
    
    @staticmethod
    def apply_fixed_height(widget, height: int):
        """
        Apply fixed height to a widget to prevent vertical resizing.
        
        Args:
            widget: QWidget to apply fixed height to
            height: Fixed height in pixels
        """
        from PyQt5.QtWidgets import QSizePolicy
        
        widget.setFixedHeight(height)
        widget.setSizePolicy(widget.sizePolicy().horizontalPolicy(), QSizePolicy.Fixed)
    
    @staticmethod
    def prevent_layout_resize(widget):
        """
        Prevent a widget from causing its parent layout to resize.
        Useful for widgets with dynamic content like autocomplete dropdowns.
        
        Args:
            widget: QWidget to prevent from affecting parent layout
        """
        from PyQt5.QtWidgets import QSizePolicy
        
        # Set size policy to Ignored so the widget doesn't affect layout sizing
        widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # Prevent size hint changes from propagating
        widget.setProperty("no_resize_propagation", True)
    
    # ==================== RESPONSIVE DESIGN UTILITIES ====================
    
    # Base reference sizes (designed for 1920x1080 at 100% scaling)
    _BASE_SCREEN_WIDTH = 1920
    _BASE_SCREEN_HEIGHT = 1080
    _BASE_DPI = 96
    
    @classmethod
    def get_screen_scale_factor(cls) -> float:
        """
        Get the current screen scale factor based on DPI and screen size.
        Returns a multiplier to scale UI elements appropriately.
        """
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QScreen
        
        app = QApplication.instance()
        if not app:
            return 1.0
        
        screen = app.primaryScreen()
        if not screen:
            return 1.0
        
        # Get logical DPI (accounts for system scaling)
        dpi = screen.logicalDotsPerInch()
        dpi_scale = dpi / cls._BASE_DPI
        
        # Get screen size
        geometry = screen.availableGeometry()
        width_scale = geometry.width() / cls._BASE_SCREEN_WIDTH
        height_scale = geometry.height() / cls._BASE_SCREEN_HEIGHT
        
        # Use the smaller scale to ensure UI fits on screen
        size_scale = min(width_scale, height_scale)
        
        # Combine DPI and size scaling (weighted average)
        # DPI scaling is more important for text readability
        combined_scale = (dpi_scale * 0.6) + (size_scale * 0.4)
        
        # Clamp to reasonable range (0.75 to 2.0)
        return max(0.75, min(2.0, combined_scale))
    
    @classmethod
    def scale_size(cls, base_size: int) -> int:
        """
        Scale a size value based on current screen scale factor.
        
        Args:
            base_size: Base size in pixels (designed for 1080p at 100% scaling)
            
        Returns:
            Scaled size appropriate for current screen
        """
        return int(base_size * cls.get_screen_scale_factor())
    
    @classmethod
    def get_responsive_font_size(cls, base_size: int = None) -> int:
        """
        Get responsive font size based on screen scale.
        
        Args:
            base_size: Base font size (defaults to FONT_SIZE)
            
        Returns:
            Scaled font size
        """
        if base_size is None:
            base_size = cls.FONT_SIZE
        return max(8, cls.scale_size(base_size))
    
    @classmethod
    def get_responsive_spacing(cls, base_spacing: int = 8) -> int:
        """
        Get responsive spacing/margin value.
        
        Args:
            base_spacing: Base spacing in pixels
            
        Returns:
            Scaled spacing value
        """
        return max(4, cls.scale_size(base_spacing))
    
    @classmethod
    def get_responsive_button_size(cls, base_size: int = 36) -> int:
        """
        Get responsive button size.
        
        Args:
            base_size: Base button size in pixels
            
        Returns:
            Scaled button size
        """
        return max(28, cls.scale_size(base_size))
    
    @classmethod
    def get_min_dialog_size(cls, base_width: int, base_height: int) -> tuple:
        """
        Get minimum dialog size that works across screen sizes.
        
        Args:
            base_width: Base dialog width
            base_height: Base dialog height
            
        Returns:
            Tuple of (width, height) scaled for current screen
        """
        from PyQt5.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen:
                available = screen.availableGeometry()
                # Ensure dialog doesn't exceed 90% of available screen
                max_width = int(available.width() * 0.9)
                max_height = int(available.height() * 0.9)
                
                scaled_width = cls.scale_size(base_width)
                scaled_height = cls.scale_size(base_height)
                
                return (
                    min(scaled_width, max_width),
                    min(scaled_height, max_height)
                )
        
        return (base_width, base_height)
    
    # ==================== RTL/LTR LAYOUT UTILITIES ====================
    
    _current_direction = 'ltr'
    
    @classmethod
    def set_layout_direction(cls, direction: str):
        """
        Set the current layout direction globally.
        
        Args:
            direction: 'rtl' for right-to-left (Arabic), 'ltr' for left-to-right
        """
        cls.ensure_initialized()
        cls._current_direction = direction.lower()
    
    @classmethod
    def get_layout_direction(cls) -> str:
        """Get current layout direction ('rtl' or 'ltr')"""
        cls.ensure_initialized()
        return cls._current_direction
    
    @classmethod
    def is_rtl(cls) -> bool:
        """Check if current direction is RTL"""
        cls.ensure_initialized()
        return cls._current_direction == 'rtl'
    
    @classmethod
    def get_direction_aware_margin(cls, left: int, top: int, right: int, bottom: int) -> str:
        """
        Get margin string that respects current layout direction.
        Swaps left and right margins for RTL layouts.
        
        Args:
            left, top, right, bottom: Margin values in pixels
            
        Returns:
            CSS margin string
        """
        if cls.is_rtl():
            return f"{top}px {left}px {bottom}px {right}px"
        return f"{top}px {right}px {bottom}px {left}px"
    
    @classmethod
    def get_direction_aware_padding(cls, left: int, top: int, right: int, bottom: int) -> str:
        """
        Get padding string that respects current layout direction.
        Swaps left and right padding for RTL layouts.
        """
        if cls.is_rtl():
            return f"{top}px {left}px {bottom}px {right}px"
        return f"{top}px {right}px {bottom}px {left}px"
    
    @classmethod
    def get_text_align(cls) -> str:
        """Get appropriate text alignment for current direction"""
        return 'right' if cls.is_rtl() else 'left'
    
    @classmethod
    def get_opposite_align(cls) -> str:
        """Get opposite text alignment for current direction"""
        return 'left' if cls.is_rtl() else 'right'
    
    @staticmethod
    def get_rtl_aware_button_style(base_style: str = None) -> str:
        """
        Get button style that maintains consistent size regardless of RTL/LTR.
        
        Args:
            base_style: Optional base style to extend
            
        Returns:
            CSS stylesheet string for buttons
        """
        style = """
            QPushButton {
                min-width: 36px;
                min-height: 36px;
                max-width: 36px;
                max-height: 36px;
                padding: 4px;
                margin: 2px;
                border-radius: 4px;
                background-color: #FFFFFF;
                border: 1px solid #BDC3C7;
            }
            QPushButton:hover {
                background-color: #EBF5FB;
                border-color: #3498DB;
            }
            QPushButton:pressed {
                background-color: #D4E6F1;
            }
            QPushButton:disabled {
                background-color: #F5F5F5;
                border-color: #E0E0E0;
            }
        """
        if base_style:
            return base_style + style
        return style
    
    @staticmethod
    def apply_rtl_to_layout(layout, is_rtl: bool):
        """
        Apply RTL/LTR direction to a layout and its contents.
        
        Args:
            layout: QLayout to apply direction to
            is_rtl: True for RTL (Arabic), False for LTR
        """
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
        
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        
        # Apply to all widgets in the layout
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget():
                item.widget().setLayoutDirection(direction)
            elif item.layout():
                AppStyles.apply_rtl_to_layout(item.layout(), is_rtl)
    
    @staticmethod
    def get_fixed_button_size(size: int = 36) -> tuple:
        """
        Get fixed button dimensions for consistent sizing.
        
        Args:
            size: Base button size
            
        Returns:
            Tuple of (width, height)
        """
        return (size, size)
    
    @staticmethod
    def apply_fixed_button_style(button, size: int = 36, style_type: str = None):
        """
        Apply fixed size styling to a button for consistent appearance.
        
        Args:
            button: QPushButton to style
            size: Button size in pixels
            style_type: Optional style type ('success', 'danger', 'primary')
        """
        from PyQt5.QtWidgets import QSizePolicy
        from PyQt5.QtCore import QSize
        
        # Set fixed size
        button.setFixedSize(size, size)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Base style
        base_style = f"""
            QPushButton {{
                min-width: {size}px;
                min-height: {size}px;
                max-width: {size}px;
                max-height: {size}px;
                padding: 4px;
                margin: 2px;
                border-radius: 4px;
            }}
        """
        
        # Add type-specific colors
        if style_type == 'success':
            base_style += """
                QPushButton {
                    background-color: #27AE60;
                    border: 1px solid #229954;
                }
                QPushButton:hover {
                    background-color: #2ECC71;
                }
            """
        elif style_type == 'danger':
            base_style += """
                QPushButton {
                    background-color: #E74C3C;
                    border: 1px solid #C0392B;
                }
                QPushButton:hover {
                    background-color: #EC7063;
                }
            """
        elif style_type == 'primary':
            base_style += """
                QPushButton {
                    background-color: #3498DB;
                    border: 1px solid #2980B9;
                }
                QPushButton:hover {
                    background-color: #5DADE2;
                }
            """
        else:
            base_style += """
                QPushButton {
                    background-color: #FFFFFF;
                    border: 1px solid #BDC3C7;
                }
                QPushButton:hover {
                    background-color: #EBF5FB;
                    border-color: #3498DB;
                }
            """
        
        button.setStyleSheet(base_style)
    
    @classmethod
    def apply_direction_to_widget(cls, widget, language: str = None):
        """
        Apply appropriate layout direction to a widget based on language.
        
        Args:
            widget: QWidget to apply direction to
            language: Language code ('ar' for RTL, others for LTR)
        """
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QWidget as QW
        
        if language is None:
            is_rtl = cls.is_rtl()
        else:
            is_rtl = language == 'ar'
        
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        widget.setLayoutDirection(direction)
        
        # Apply to all child widgets recursively
        for child in widget.findChildren(QW):
            if hasattr(child, 'setLayoutDirection'):
                child.setLayoutDirection(direction)
    
    @classmethod
    def apply_rtl_to_dialog(cls, dialog, translator):
        """
        Apply complete RTL/LTR direction support to a dialog.
        Ensures all buttons maintain their sizes and positions.
        
        Args:
            dialog: QDialog to apply direction to
            translator: TranslationManager instance
        """
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QWidget, QPushButton, QSizePolicy
        
        is_rtl = translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        
        # Apply direction to dialog
        dialog.setLayoutDirection(direction)
        
        # Apply direction to all child widgets
        for child in dialog.findChildren(QWidget):
            child.setLayoutDirection(direction)
            
            # Ensure buttons maintain fixed size
            if isinstance(child, QPushButton):
                # Get current fixed size if set
                current_size = child.size()
                if child.sizePolicy().horizontalPolicy() == QSizePolicy.Fixed:
                    # Re-apply fixed size to ensure it's maintained
                    child.setFixedSize(current_size)
        
        # Update global direction
        cls.set_layout_direction('rtl' if is_rtl else 'ltr')
    
    @staticmethod
    def ensure_button_fixed_size(button, size: int = 36):
        """
        Ensure a button maintains fixed size regardless of RTL/LTR changes.
        
        Args:
            button: QPushButton to fix size for
            size: Button size in pixels
        """
        from PyQt5.QtWidgets import QSizePolicy
        
        button.setFixedSize(size, size)
        button.setMinimumSize(size, size)
        button.setMaximumSize(size, size)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    
    @classmethod
    def apply_responsive_dialog_size(cls, dialog, base_width: int, base_height: int):
        """
        Apply responsive sizing to a dialog that works across all screen sizes.
        Dialog is resizable by the user with appropriate minimum size.
        
        Args:
            dialog: QDialog to apply sizing to
            base_width: Base width for 1080p screens
            base_height: Base height for 1080p screens
        """
        from PyQt5.QtWidgets import QSizePolicy
        from PyQt5.QtWidgets import QApplication
        
        # Get screen-appropriate size
        width, height = cls.get_min_dialog_size(base_width, base_height)
        
        # Set minimum size (70% of base to allow some shrinking)
        min_width = int(width * 0.7)
        min_height = int(height * 0.7)
        dialog.setMinimumSize(min_width, min_height)
        
        # Set initial size
        dialog.resize(width, height)
        
        # Allow resizing - always use Preferred policy
        dialog.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
        # For smaller screens, limit max size to screen
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen:
                available = screen.availableGeometry()
                max_width = int(available.width() * 0.95)
                max_height = int(available.height() * 0.95)
                dialog.setMaximumSize(max_width, max_height)
        
        # Adjust to content size if larger than base
        if hasattr(dialog, 'sizeHint'):
            content_size = dialog.sizeHint()
            if content_size.isValid():
                final_width = max(width, min(content_size.width(), dialog.maximumWidth()))
                final_height = max(height, min(content_size.height(), dialog.maximumHeight()))
                dialog.resize(final_width, final_height)
    
    @classmethod
    def get_responsive_stylesheet(cls) -> str:
        """
        Get the main stylesheet with responsive font sizes and spacing.
        """
        # Get scaled values
        font_size = cls.get_responsive_font_size()
        large_font = cls.get_responsive_font_size(cls.FONT_SIZE_LARGE)
        small_font = cls.get_responsive_font_size(cls.FONT_SIZE_SMALL)
        spacing = cls.get_responsive_spacing()
        
        # Generate stylesheet with scaled values
        return cls.get_stylesheet()
    
    # ==================== SCROLLING UTILITIES ====================
    
    @classmethod
    def get_unified_scroll_area_style(cls) -> str:
        """Return the theme-aware style used by unified workspace scrolling."""
        colors = cls.get_colors()
        scroll_bg = colors.get('WHITE', '#FFFFFF')
        border_color = colors.get('BORDER', '#DEE2E6')
        muted_color = colors.get('TEXT_SECONDARY', '#64748B')
        return f"""
            QScrollArea {{
                background-color: {scroll_bg};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {scroll_bg};
                width: 14px;
                border-radius: 7px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {border_color};
                border-radius: 6px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {muted_color};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                background: {scroll_bg};
                height: 14px;
                border-radius: 7px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {border_color};
                border-radius: 6px;
                min-width: 40px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {muted_color};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """

    @classmethod
    def create_unified_scroll_area(cls, content_widget=None):
        """Create one theme-aware scroll area for a complete workspace."""
        from PyQt5.QtWidgets import QScrollArea, QFrame
        from PyQt5.QtCore import Qt

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(cls.get_unified_scroll_area_style())
        if content_widget:
            scroll.setWidget(content_widget)
        return scroll
    
    @staticmethod
    def get_table_scrollbar_style():
        """
        Get scrollbar styling for tables that matches timeline interface style.
        Returns stylesheet string for QTableWidget scrollbars.
        """
        colors = AppStyles.get_colors()
        accent_color = colors.get('ACCENT', '#3498DB')
        accent_hover = colors.get('ACCENT_HOVER', '#2980B9')
        light_bg = colors.get('LIGHT_BG', '#F0F0F0')
        border_color = colors.get('BORDER', '#DEE2E6')
        
        return f"""
            QTableWidget {{
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
            QScrollBar:vertical {{
                border: none;
                background: {light_bg};
                width: 16px;
                margin: 0px;
                border-radius: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: {accent_color};
                min-height: 30px;
                border-radius: 8px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {accent_hover};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
            QScrollBar:horizontal {{
                border: none;
                background: {light_bg};
                height: 16px;
                margin: 0px;
                border-radius: 8px;
            }}
            QScrollBar::handle:horizontal {{
                background: {accent_color};
                min-width: 30px;
                border-radius: 8px;
                margin: 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {accent_hover};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: transparent;
            }}
        """
    
    @staticmethod
    def create_scroll_area(content_widget=None, horizontal_policy='as_needed', 
                           vertical_policy='as_needed', frame_shape='no_frame'):
        """
        Create a configured scroll area for responsive layouts.
        
        Args:
            content_widget: Optional widget to set as scroll area content
            horizontal_policy: 'always', 'never', 'as_needed'
            vertical_policy: 'always', 'never', 'as_needed'
            frame_shape: 'no_frame', 'box', 'panel', 'styled_panel'
            
        Returns:
            Configured QScrollArea
        """
        from PyQt5.QtWidgets import QScrollArea, QFrame
        from PyQt5.QtCore import Qt
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # Set horizontal scroll policy
        h_policies = {
            'always': Qt.ScrollBarAlwaysOn,
            'never': Qt.ScrollBarAlwaysOff,
            'as_needed': Qt.ScrollBarAsNeeded
        }
        scroll.setHorizontalScrollBarPolicy(h_policies.get(horizontal_policy, Qt.ScrollBarAsNeeded))
        
        # Set vertical scroll policy
        v_policies = {
            'always': Qt.ScrollBarAlwaysOn,
            'never': Qt.ScrollBarAlwaysOff,
            'as_needed': Qt.ScrollBarAsNeeded
        }
        scroll.setVerticalScrollBarPolicy(v_policies.get(vertical_policy, Qt.ScrollBarAsNeeded))
        
        # Set frame shape
        frames = {
            'no_frame': QFrame.NoFrame,
            'box': QFrame.Box,
            'panel': QFrame.Panel,
            'styled_panel': QFrame.StyledPanel
        }
        scroll.setFrameShape(frames.get(frame_shape, QFrame.NoFrame))
        
        # Apply styling
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #F0F0F0;
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #C0C0C0;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #A0A0A0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background: #F0F0F0;
                height: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal {
                background: #C0C0C0;
                border-radius: 5px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #A0A0A0;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        if content_widget:
            scroll.setWidget(content_widget)
        
        return scroll
    
    @staticmethod
    def wrap_in_scroll_area(widget, min_width=None, min_height=None,
                            horizontal_policy='as_needed', vertical_policy='as_needed'):
        """
        Wrap an existing widget in a scroll area for responsive layouts.
        
        Args:
            widget: The widget to wrap
            min_width: Optional minimum width for the scroll area
            min_height: Optional minimum height for the scroll area
            horizontal_policy: 'always', 'never', 'as_needed'
            vertical_policy: 'always', 'never', 'as_needed'
            
        Returns:
            QScrollArea containing the widget
        """
        from PyQt5.QtWidgets import QSizePolicy
        
        scroll = AppStyles.create_scroll_area(
            content_widget=widget,
            horizontal_policy=horizontal_policy,
            vertical_policy=vertical_policy
        )
        
        if min_width:
            scroll.setMinimumWidth(min_width)
        if min_height:
            scroll.setMinimumHeight(min_height)
        
        # Allow scroll area to expand
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        return scroll
    
    @staticmethod
    def apply_scroll_to_widget(widget, enable_horizontal=True, enable_vertical=True):
        """
        Apply scroll behavior to widgets that support it (like QTextEdit, QTableWidget).
        
        Args:
            widget: Widget to apply scroll behavior to
            enable_horizontal: Enable horizontal scrollbar
            enable_vertical: Enable vertical scrollbar
        """
        from PyQt5.QtCore import Qt
        
        if hasattr(widget, 'setVerticalScrollBarPolicy'):
            widget.setVerticalScrollBarPolicy(
                Qt.ScrollBarAsNeeded if enable_vertical else Qt.ScrollBarAlwaysOff
            )
        
        if hasattr(widget, 'setHorizontalScrollBarPolicy'):
            widget.setHorizontalScrollBarPolicy(
                Qt.ScrollBarAsNeeded if enable_horizontal else Qt.ScrollBarAlwaysOff
            )
        
        # Apply modern scrollbar styling
        widget.setStyleSheet(widget.styleSheet() + """
            QScrollBar:vertical {
                background: #F0F0F0;
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #C0C0C0;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #A0A0A0;
            }
            QScrollBar:horizontal {
                background: #F0F0F0;
                height: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal {
                background: #C0C0C0;
                border-radius: 5px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #A0A0A0;
            }
        """)
    
    @staticmethod
    def create_scrollable_form_container(parent=None):
        """
        Create a scrollable container ideal for forms and dialogs.
        
        Args:
            parent: Optional parent widget
            
        Returns:
            Tuple of (scroll_area, content_widget, content_layout)
        """
        from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
        
        # Create content widget
        content_widget = QWidget(parent)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(10)
        
        # Create scroll area
        scroll = AppStyles.create_scroll_area(
            content_widget=content_widget,
            horizontal_policy='as_needed',
            vertical_policy='as_needed'
        )
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        return scroll, content_widget, content_layout
    
    @staticmethod
    def create_scrollable_panel(title=None, parent=None):
        """
        Create a scrollable panel with optional title, ideal for sidebar sections.
        
        Args:
            title: Optional title for the panel
            parent: Optional parent widget
            
        Returns:
            Tuple of (container_widget, scroll_area, content_widget, content_layout)
        """
        from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QSizePolicy
        
        # Container
        container = QFrame(parent)
        container.setFrameShape(QFrame.StyledPanel)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Title if provided
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                QLabel {
                    background-color: #2C3E50;
                    color: white;
                    padding: 8px 12px;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
            container_layout.addWidget(title_label)
        
        # Scrollable content
        scroll, content_widget, content_layout = AppStyles.create_scrollable_form_container()
        container_layout.addWidget(scroll)
        
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        return container, scroll, content_widget, content_layout
    
    # ==================== LEGACY COMPATIBILITY ====================
    
    # Legacy color properties for backward compatibility
    PRIMARY = LIGHT['PRIMARY']
    SECONDARY = LIGHT['SECONDARY']
    ACCENT = LIGHT['ACCENT']
    ACCENT_HOVER = LIGHT['ACCENT_HOVER']
    SUCCESS = LIGHT['SUCCESS']
    SUCCESS_HOVER = LIGHT['SUCCESS_HOVER']
    DANGER = LIGHT['DANGER']
    DANGER_HOVER = LIGHT['DANGER_HOVER']
    WARNING = LIGHT['WARNING']
    INFO = LIGHT['INFO']
    WHITE = LIGHT['WHITE']
    LIGHT_BG = LIGHT['LIGHT_BG']
    DARK_BG = LIGHT['DARK_BG']
    TEXT_PRIMARY = LIGHT['TEXT_PRIMARY']
    TEXT_SECONDARY = LIGHT['TEXT_SECONDARY']
    BORDER = LIGHT['BORDER']
    BORDER_FOCUS = LIGHT['BORDER_FOCUS']
