"""
Professional Print Utilities
Centralized header/footer system for consistent printing and exporting across the entire project
"""
import os
import base64
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QLineEdit, QTextEdit, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QCheckBox, QDialogButtonBox, QTabWidget, QWidget, QComboBox,
    QScrollArea, QFrame, QGridLayout, QMessageBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QSize, QRectF, QRect
from PyQt5.QtGui import QFont, QPixmap, QImage, QColor, QPainter
from styles.styles import AppStyles


# Config file path - use path_utils for correct path when installed
def _get_config_dir():
    from utils.path_utils import get_config_dir
    return str(get_config_dir())

def _get_print_settings_file():
    return os.path.join(_get_config_dir(), 'print_settings.json')

def _get_export_settings_file():
    return os.path.join(_get_config_dir(), 'export_settings.json')


class PrintSettings:
    """Global print settings - Singleton pattern for consistent settings across the app"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Header Left Section
        self.header_left_line1 = ""  # Organization/Company Name
        self.header_left_line2 = ""  # Department/Division
        self.header_left_line3 = ""  # Address or other info
        
        # Header Center Section (Logo)
        self.header_logo_path = ""
        
        # Header Right Section
        self.header_right_prefix = "DOC"  # Document number prefix
        self.header_right_auto_number = True  # Auto-generate number
        self.header_right_number = ""  # Manual number if auto is off
        self.header_right_show_date = True
        self.header_right_date_format = "%Y-%m-%d"
        self.header_right_extra = ""
        
        # Footer settings
        self.footer_left = ""
        self.footer_center = ""
        self.footer_right = ""
        self.show_page_numbers = True
        self.show_print_date = True
        # Page number format: 'page_x_of_y' | 'x_of_y' | 'x_slash_y' | 'x_only'
        self.page_number_format = 'page_x_of_y'
        # Page number position in footer: 'left' | 'center' | 'right'
        self.page_number_position = 'center'
        
        # Column widths (column_name: width_percentage)
        self.column_widths: Dict[str, int] = {}
        
        # Page settings
        self.page_orientation = 'Portrait'
        self.page_size = 'A4'
        self.margin_mm = 15
        
        # Auto-increment counter for document numbers
        self._doc_counter = 0
        
        # Load saved settings
        self.load_settings()
    
    def load_settings(self):
        """Load settings from config file"""
        if os.path.exists(_get_print_settings_file()):
            try:
                with open(_get_print_settings_file(), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.from_dict(data)
            except Exception as e:
                print(f"Error loading print settings: {e}")
    
    def save_settings(self):
        """Save settings to config file"""
        try:
            with open(_get_print_settings_file(), 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving print settings: {e}")
            return False
    
    def generate_doc_number(self) -> str:
        """Generate auto document number"""
        if not self.header_right_auto_number:
            return self.header_right_number
        
        self._doc_counter += 1
        date_part = datetime.now().strftime("%Y%m%d")
        return f"{self.header_right_prefix}-{date_part}-{self._doc_counter:04d}"
    
    def get_formatted_date(self) -> str:
        """Get formatted current date"""
        return datetime.now().strftime(self.header_right_date_format)
    
    def get_logo_base64(self) -> str:
        """Get logo as base64 string for HTML embedding"""
        if not self.header_logo_path or not os.path.exists(self.header_logo_path):
            return ""
        try:
            with open(self.header_logo_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except:
            return ""
    
    def get_logo_mime_type(self) -> str:
        """Get logo MIME type"""
        if not self.header_logo_path:
            return ""
        ext = os.path.splitext(self.header_logo_path)[1].lower()
        mime_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp'
        }
        return mime_map.get(ext, 'image/png')
    
    def to_dict(self) -> Dict:
        """Export settings to dictionary"""
        return {
            'header_left_line1': self.header_left_line1,
            'header_left_line2': self.header_left_line2,
            'header_left_line3': self.header_left_line3,
            'header_logo_path': self.header_logo_path,
            'header_right_prefix': self.header_right_prefix,
            'header_right_auto_number': self.header_right_auto_number,
            'header_right_number': self.header_right_number,
            'header_right_show_date': self.header_right_show_date,
            'header_right_date_format': self.header_right_date_format,
            'header_right_extra': self.header_right_extra,
            'footer_left': self.footer_left,
            'footer_center': self.footer_center,
            'footer_right': self.footer_right,
            'show_page_numbers': self.show_page_numbers,
            'show_print_date': self.show_print_date,
            'page_number_format': self.page_number_format,
            'page_number_position': self.page_number_position,
            'column_widths': self.column_widths,
            'page_orientation': self.page_orientation,
            'page_size': self.page_size,
            'margin_mm': self.margin_mm,
            '_doc_counter': self._doc_counter
        }
    
    def from_dict(self, data: Dict):
        """Import settings from dictionary"""
        self.header_left_line1 = data.get('header_left_line1', '')
        self.header_left_line2 = data.get('header_left_line2', '')
        self.header_left_line3 = data.get('header_left_line3', '')
        self.header_logo_path = data.get('header_logo_path', '')
        self.header_right_prefix = data.get('header_right_prefix', 'DOC')
        self.header_right_auto_number = data.get('header_right_auto_number', True)
        self.header_right_number = data.get('header_right_number', '')
        self.header_right_show_date = data.get('header_right_show_date', True)
        self.header_right_date_format = data.get('header_right_date_format', '%Y-%m-%d')
        self.header_right_extra = data.get('header_right_extra', '')
        self.footer_left = data.get('footer_left', '')
        self.footer_center = data.get('footer_center', '')
        self.footer_right = data.get('footer_right', '')
        self.show_page_numbers = data.get('show_page_numbers', True)
        self.show_print_date = data.get('show_print_date', True)
        self.page_number_format = data.get('page_number_format', 'page_x_of_y')
        self.page_number_position = data.get('page_number_position', 'center')
        self.column_widths = data.get('column_widths', {})
        self.page_orientation = data.get('page_orientation', 'Portrait')
        self.page_size = data.get('page_size', 'A4')
        self.margin_mm = data.get('margin_mm', 15)
        self._doc_counter = data.get('_doc_counter', 0)


class ExportSettings:
    """Global export settings - Singleton pattern for consistent export settings across the app"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Default export format
        self.default_format = 'excel'  # 'excel', 'csv', 'word', 'pdf'
        
        # Open file after export
        self.open_after_export = True
        
        # Include document header in export
        self.include_header = True
        
        # Translate field names based on current language
        self.translate_fields = True
        
        # Column widths (column_name: width_percentage)
        self.column_widths: Dict[str, int] = {}
        
        # Last selected columns (for persistence)
        self.last_selected_columns: List[str] = []
        
        # Load saved settings
        self.load_settings()
    
    def load_settings(self):
        """Load settings from config file"""
        if os.path.exists(_get_export_settings_file()):
            try:
                with open(_get_export_settings_file(), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.from_dict(data)
            except Exception as e:
                print(f"Error loading export settings: {e}")
    
    def save_settings(self):
        """Save settings to config file"""
        try:
            with open(_get_export_settings_file(), 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving export settings: {e}")
            return False
    
    def to_dict(self) -> Dict:
        """Export settings to dictionary"""
        return {
            'default_format': self.default_format,
            'open_after_export': self.open_after_export,
            'include_header': self.include_header,
            'translate_fields': self.translate_fields,
            'column_widths': self.column_widths,
            'last_selected_columns': self.last_selected_columns
        }
    
    def from_dict(self, data: Dict):
        """Import settings from dictionary"""
        self.default_format = data.get('default_format', 'excel')
        self.open_after_export = data.get('open_after_export', True)
        self.include_header = data.get('include_header', True)
        self.translate_fields = data.get('translate_fields', True)
        self.column_widths = data.get('column_widths', {})
        self.last_selected_columns = data.get('last_selected_columns', [])


class GlobalHeaderSettingsDialog(QDialog):
    """Global dialog for configuring print header settings - accessible from main menu"""
    
    def __init__(self, parent, translator):
        super().__init__(parent)
        self.translator = translator
        self.settings = PrintSettings()
        self.is_rtl = translator.current_language == 'ar'
        
        self.setWindowTitle(translator.tr('print_global_settings'))
        # Apply fixed size to prevent resizing on button clicks or content changes
        from styles.styles import AppStyles
        AppStyles.apply_fixed_size(self, 800, 650)
        
        if self.is_rtl:
            self.setLayoutDirection(Qt.RightToLeft)
        
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid (rounding 10px to 16px)
        
        # Header preview at top
        preview_group = QGroupBox(self.translator.tr('print_header_preview'))
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_frame = QFrame()
        self.preview_frame.setMinimumHeight(140)
        self.preview_frame.setStyleSheet(AppStyles.get_component_style('print_preview_frame'))
        preview_layout.addWidget(self.preview_frame)
        self.setup_preview_layout()
        
        layout.addWidget(preview_group)
        
        # Tabs for different settings
        tabs = QTabWidget()
        tabs.setStyleSheet(AppStyles.get_component_style('print_tabs'))
        
        # === LEFT SECTION TAB ===
        left_tab = QWidget()
        left_layout = QVBoxLayout(left_tab)
        
        left_form = QFormLayout()
        left_form.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid (rounding 12px to 16px)
        
        self.line1_edit = QLineEdit()
        self.line1_edit.setPlaceholderText(self.translator.tr('print_org_name'))
        self.line1_edit.textChanged.connect(self.update_preview)
        left_form.addRow(self.translator.tr('print_line1') + " (" + self.translator.tr('print_org_name') + "):", self.line1_edit)
        
        self.line2_edit = QLineEdit()
        self.line2_edit.setPlaceholderText(self.translator.tr('print_department'))
        self.line2_edit.textChanged.connect(self.update_preview)
        left_form.addRow(self.translator.tr('print_line2') + " (" + self.translator.tr('print_department') + "):", self.line2_edit)
        
        self.line3_edit = QLineEdit()
        self.line3_edit.setPlaceholderText(self.translator.tr('print_extra_info'))
        self.line3_edit.textChanged.connect(self.update_preview)
        left_form.addRow(self.translator.tr('print_line3') + " (" + self.translator.tr('print_extra_info') + "):", self.line3_edit)
        
        left_layout.addLayout(left_form)
        left_layout.addStretch()
        tabs.addTab(left_tab, self.translator.tr('print_left_section'))
        
        # === CENTER SECTION TAB (Logo) ===
        center_tab = QWidget()
        center_layout = QVBoxLayout(center_tab)
        
        logo_group = QGroupBox(self.translator.tr('print_logo'))
        logo_inner = QVBoxLayout(logo_group)
        
        self.logo_preview = QLabel()
        self.logo_preview.setFixedSize(200, 120)
        self.logo_preview.setStyleSheet(AppStyles.get_component_style('print_logo_preview'))
        self.logo_preview.setAlignment(Qt.AlignCenter)
        self.logo_preview.setText(self.translator.tr('print_no_logo'))
        logo_inner.addWidget(self.logo_preview, alignment=Qt.AlignCenter)
        
        logo_btn_layout = QHBoxLayout()
        self.btn_select_logo = QPushButton(self.translator.tr('print_select_logo'))
        self.btn_select_logo.setStyleSheet(AppStyles.get_component_style('print_select_logo_btn'))
        self.btn_select_logo.setAutoDefault(False)
        self.btn_select_logo.setDefault(False)
        self.btn_select_logo.clicked.connect(self.select_logo)
        
        self.btn_clear_logo = QPushButton(self.translator.tr('print_clear_logo'))
        self.btn_clear_logo.setAutoDefault(False)
        self.btn_clear_logo.setDefault(False)
        self.btn_clear_logo.clicked.connect(self.clear_logo)
        
        logo_btn_layout.addStretch()
        logo_btn_layout.addWidget(self.btn_select_logo)
        logo_btn_layout.addWidget(self.btn_clear_logo)
        logo_btn_layout.addStretch()
        logo_inner.addLayout(logo_btn_layout)
        
        center_layout.addWidget(logo_group)
        center_layout.addStretch()
        tabs.addTab(center_tab, self.translator.tr('print_center_section'))
        
        # === RIGHT SECTION TAB ===
        right_tab = QWidget()
        right_layout = QVBoxLayout(right_tab)
        
        # Document Number
        num_group = QGroupBox(self.translator.tr('print_doc_number'))
        num_layout = QFormLayout(num_group)
        
        self.auto_number_check = QCheckBox(self.translator.tr('print_auto_number'))
        self.auto_number_check.stateChanged.connect(self.on_auto_number_changed)
        num_layout.addRow("", self.auto_number_check)
        
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText("DOC")
        self.prefix_edit.setMaximumWidth(150)
        self.prefix_edit.textChanged.connect(self.update_preview)
        num_layout.addRow(self.translator.tr('print_prefix') + ":", self.prefix_edit)
        
        self.manual_number_edit = QLineEdit()
        self.manual_number_edit.setPlaceholderText("001")
        self.manual_number_edit.textChanged.connect(self.update_preview)
        num_layout.addRow(self.translator.tr('print_manual_number') + ":", self.manual_number_edit)
        
        right_layout.addWidget(num_group)
        
        # Date
        date_group = QGroupBox(self.translator.tr('print_date'))
        date_layout = QFormLayout(date_group)
        
        self.show_date_check = QCheckBox(self.translator.tr('print_show_date'))
        self.show_date_check.stateChanged.connect(self.update_preview)
        date_layout.addRow("", self.show_date_check)
        
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems([
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%B %d, %Y"
        ])
        self.date_format_combo.currentTextChanged.connect(self.update_preview)
        date_layout.addRow(self.translator.tr('print_date_format') + ":", self.date_format_combo)
        
        right_layout.addWidget(date_group)
        
        # Extra info
        self.extra_right_edit = QLineEdit()
        self.extra_right_edit.setPlaceholderText(self.translator.tr('print_extra_info'))
        self.extra_right_edit.textChanged.connect(self.update_preview)
        right_layout.addWidget(QLabel(self.translator.tr('print_extra_info') + ":"))
        right_layout.addWidget(self.extra_right_edit)
        
        right_layout.addStretch()
        tabs.addTab(right_tab, self.translator.tr('print_right_section'))
        
        # === FOOTER TAB ===
        footer_tab = QWidget()
        footer_layout = QFormLayout(footer_tab)
        footer_layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid (rounding 12px to 16px)
        
        self.footer_left_edit = QLineEdit()
        self.footer_left_edit.setPlaceholderText(self.translator.tr('print_footer_left'))
        footer_layout.addRow(self.translator.tr('print_footer_left') + ":", self.footer_left_edit)
        
        self.footer_center_edit = QLineEdit()
        self.footer_center_edit.setPlaceholderText(self.translator.tr('print_footer_center'))
        footer_layout.addRow(self.translator.tr('print_footer_center') + ":", self.footer_center_edit)
        
        self.footer_right_edit = QLineEdit()
        self.footer_right_edit.setPlaceholderText(self.translator.tr('print_footer_right'))
        footer_layout.addRow(self.translator.tr('print_footer_right') + ":", self.footer_right_edit)
        
        self.page_numbers_check = QCheckBox(self.translator.tr('print_show_page_numbers'))
        footer_layout.addRow("", self.page_numbers_check)
        
        self.page_number_format_combo = QComboBox()
        self.page_number_format_combo.addItems([
            self.translator.tr('print_page_number_format_page_of'),
            self.translator.tr('print_page_number_format_x_of'),
            self.translator.tr('print_page_number_format_slash'),
            self.translator.tr('print_page_number_format_x_only')
        ])
        footer_layout.addRow(self.translator.tr('print_page_number_format') + ":", self.page_number_format_combo)
        
        self.page_number_position_combo = QComboBox()
        self.page_number_position_combo.addItems([
            self.translator.tr('print_page_number_left'),
            self.translator.tr('print_page_number_center'),
            self.translator.tr('print_page_number_right')
        ])
        footer_layout.addRow(self.translator.tr('print_page_number_position') + ":", self.page_number_position_combo)
        
        self.print_date_check = QCheckBox(self.translator.tr('print_show_print_date'))
        footer_layout.addRow("", self.print_date_check)
        
        tabs.addTab(footer_tab, self.translator.tr('print_footer'))
        
        # === PAGE SETTINGS TAB ===
        page_tab = QWidget()
        page_layout = QFormLayout(page_tab)
        page_layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid (rounding 12px to 16px)
        
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItems([
            self.translator.tr('report_portrait'),
            self.translator.tr('report_landscape')
        ])
        page_layout.addRow(self.translator.tr('print_orientation') + ":", self.orientation_combo)
        
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(['A4', 'A3', 'A5', 'Letter', 'Legal'])
        page_layout.addRow(self.translator.tr('print_page_size') + ":", self.page_size_combo)
        
        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(5, 50)
        self.margin_spin.setSuffix(' mm')
        page_layout.addRow(self.translator.tr('print_margins') + ":", self.margin_spin)
        
        tabs.addTab(page_tab, self.translator.tr('print_page_settings'))
        
        layout.addWidget(tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_reset = QPushButton(self.translator.tr('btn_reset'))
        self.btn_reset.setAutoDefault(False)
        self.btn_reset.setDefault(False)
        self.btn_reset.clicked.connect(self.reset_settings)
        btn_layout.addWidget(self.btn_reset)
        
        btn_layout.addStretch()
        
        self.btn_save = QPushButton(self.translator.tr('btn_save'))
        self.btn_save.setStyleSheet(AppStyles.get_component_style('print_save_btn'))
        self.btn_save.setAutoDefault(False)
        self.btn_save.setDefault(False)
        self.btn_save.clicked.connect(self.save_and_close)
        
        self.btn_cancel = QPushButton(self.translator.tr('btn_cancel'))
        self.btn_cancel.setAutoDefault(False)
        self.btn_cancel.setDefault(False)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(btn_layout)
    
    def setup_preview_layout(self):
        """Setup the header preview layout"""
        layout = QHBoxLayout(self.preview_frame)
        # Use 8px grid spacing
        preview_margin_h = AppStyles.get_spacing(3)  # 24px horizontal (rounding 20px to 24px)
        preview_margin_v = AppStyles.get_spacing(2)  # 16px vertical (rounding 15px to 16px)
        preview_spacing = AppStyles.get_spacing(3)  # 24px (rounding 20px to 24px)
        layout.setContentsMargins(preview_margin_h, preview_margin_v, preview_margin_h, preview_margin_v)
        layout.setSpacing(preview_spacing)
        
        # Left section
        self.preview_left = QWidget()
        self.preview_left_layout = QVBoxLayout(self.preview_left)
        self.preview_left_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_left_layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid (rounding 3px to 8px)
        self.preview_left_layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.preview_left, 1)
        
        # Center section (logo)
        self.preview_center = QLabel()
        self.preview_center.setAlignment(Qt.AlignCenter)
        self.preview_center.setFixedWidth(150)
        layout.addWidget(self.preview_center)
        
        # Right section
        self.preview_right = QWidget()
        self.preview_right_layout = QVBoxLayout(self.preview_right)
        self.preview_right_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_right_layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid (rounding 3px to 8px)
        self.preview_right_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)
        layout.addWidget(self.preview_right, 1)
    
    def load_current_settings(self):
        """Load current settings into UI"""
        # Left section
        self.line1_edit.setText(self.settings.header_left_line1)
        self.line2_edit.setText(self.settings.header_left_line2)
        self.line3_edit.setText(self.settings.header_left_line3)
        
        # Logo
        if self.settings.header_logo_path and os.path.exists(self.settings.header_logo_path):
            self.display_logo(self.settings.header_logo_path)
        
        # Right section
        self.auto_number_check.setChecked(self.settings.header_right_auto_number)
        self.prefix_edit.setText(self.settings.header_right_prefix)
        self.manual_number_edit.setText(self.settings.header_right_number)
        self.show_date_check.setChecked(self.settings.header_right_show_date)
        idx = self.date_format_combo.findText(self.settings.header_right_date_format)
        if idx >= 0:
            self.date_format_combo.setCurrentIndex(idx)
        self.extra_right_edit.setText(self.settings.header_right_extra)
        
        # Footer
        self.footer_left_edit.setText(self.settings.footer_left)
        self.footer_center_edit.setText(self.settings.footer_center)
        self.footer_right_edit.setText(self.settings.footer_right)
        self.page_numbers_check.setChecked(self.settings.show_page_numbers)
        format_map = {'page_x_of_y': 0, 'x_of_y': 1, 'x_slash_y': 2, 'x_only': 3}
        self.page_number_format_combo.setCurrentIndex(format_map.get(self.settings.page_number_format, 0))
        pos_map = {'left': 0, 'center': 1, 'right': 2}
        self.page_number_position_combo.setCurrentIndex(pos_map.get(self.settings.page_number_position, 1))
        self.print_date_check.setChecked(self.settings.show_print_date)
        
        # Page settings
        self.orientation_combo.setCurrentText(self.settings.page_orientation)
        self.page_size_combo.setCurrentText(self.settings.page_size)
        self.margin_spin.setValue(self.settings.margin_mm)
        
        self.on_auto_number_changed()
        self.update_preview()
    
    def save_settings_to_object(self):
        """Save UI values to settings object"""
        self.settings.header_left_line1 = self.line1_edit.text()
        self.settings.header_left_line2 = self.line2_edit.text()
        self.settings.header_left_line3 = self.line3_edit.text()
        self.settings.header_right_prefix = self.prefix_edit.text()
        self.settings.header_right_auto_number = self.auto_number_check.isChecked()
        self.settings.header_right_number = self.manual_number_edit.text()
        self.settings.header_right_show_date = self.show_date_check.isChecked()
        self.settings.header_right_date_format = self.date_format_combo.currentText()
        self.settings.header_right_extra = self.extra_right_edit.text()
        self.settings.footer_left = self.footer_left_edit.text()
        self.settings.footer_center = self.footer_center_edit.text()
        self.settings.footer_right = self.footer_right_edit.text()
        self.settings.show_page_numbers = self.page_numbers_check.isChecked()
        format_values = ['page_x_of_y', 'x_of_y', 'x_slash_y', 'x_only']
        self.settings.page_number_format = format_values[self.page_number_format_combo.currentIndex()]
        pos_values = ['left', 'center', 'right']
        self.settings.page_number_position = pos_values[self.page_number_position_combo.currentIndex()]
        self.settings.show_print_date = self.print_date_check.isChecked()
        self.settings.page_orientation = self.orientation_combo.currentText()
        self.settings.page_size = self.page_size_combo.currentText()
        self.settings.margin_mm = self.margin_spin.value()
    
    def on_auto_number_changed(self):
        """Handle auto number checkbox change"""
        is_auto = self.auto_number_check.isChecked()
        self.prefix_edit.setEnabled(is_auto)
        self.manual_number_edit.setEnabled(not is_auto)
        self.update_preview()
    
    def select_logo(self):
        """Select logo image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            self.translator.tr('print_select_logo'),
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.settings.header_logo_path = file_path
            self.display_logo(file_path)
            self.update_preview()
    
    def clear_logo(self):
        """Clear logo"""
        self.settings.header_logo_path = ""
        self.logo_preview.setPixmap(QPixmap())
        self.logo_preview.setText(self.translator.tr('print_no_logo'))
        self.preview_center.setPixmap(QPixmap())
        self.update_preview()
    
    def display_logo(self, path: str):
        """Display logo in preview"""
        if os.path.exists(path):
            pixmap = QPixmap(path)
            # Dialog preview
            scaled = pixmap.scaled(180, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_preview.setPixmap(scaled)
            self.logo_preview.setText("")
            # Header preview
            header_scaled = pixmap.scaled(100, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_center.setPixmap(header_scaled)
    
    def update_preview(self):
        """Update header preview"""
        # Clear left section
        while self.preview_left_layout.count():
            item = self.preview_left_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear right section
        while self.preview_right_layout.count():
            item = self.preview_right_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Left section
        if self.line1_edit.text():
            lbl = QLabel(self.line1_edit.text())
            lbl.setFont(QFont('Arial', 14, QFont.Bold))
            lbl.setStyleSheet(AppStyles.get_component_style('print_preview_label_primary'))
            self.preview_left_layout.addWidget(lbl)
        
        if self.line2_edit.text():
            lbl = QLabel(self.line2_edit.text())
            lbl.setFont(QFont('Arial', 11))
            lbl.setStyleSheet(AppStyles.get_component_style('print_preview_label_secondary'))
            self.preview_left_layout.addWidget(lbl)
        
        if self.line3_edit.text():
            lbl = QLabel(self.line3_edit.text())
            lbl.setFont(QFont('Arial', 9))
            lbl.setStyleSheet(AppStyles.get_component_style('print_preview_label_muted'))
            self.preview_left_layout.addWidget(lbl)
        
        self.preview_left_layout.addStretch()
        
        # Right section
        if self.auto_number_check.isChecked():
            prefix = self.prefix_edit.text() or "DOC"
            doc_num = f"{prefix}-{datetime.now().strftime('%Y%m%d')}-0001"
        else:
            doc_num = self.manual_number_edit.text()
        
        if doc_num:
            lbl = QLabel(f"#{doc_num}")
            lbl.setFont(QFont('Arial', 12, QFont.Bold))
            lbl.setStyleSheet(AppStyles.get_component_style('print_preview_label_primary'))
            lbl.setAlignment(Qt.AlignRight)
            self.preview_right_layout.addWidget(lbl)
        
        if self.show_date_check.isChecked():
            date_str = datetime.now().strftime(self.date_format_combo.currentText())
            lbl = QLabel(date_str)
            lbl.setFont(QFont('Arial', 10))
            lbl.setStyleSheet(AppStyles.get_component_style('print_preview_label_secondary'))
            lbl.setAlignment(Qt.AlignRight)
            self.preview_right_layout.addWidget(lbl)
        
        if self.extra_right_edit.text():
            lbl = QLabel(self.extra_right_edit.text())
            lbl.setFont(QFont('Arial', 9))
            lbl.setStyleSheet(AppStyles.get_component_style('print_preview_label_muted'))
            lbl.setAlignment(Qt.AlignRight)
            self.preview_right_layout.addWidget(lbl)
        
        self.preview_right_layout.addStretch()
    
    def reset_settings(self):
        """Reset all settings to default"""
        reply = QMessageBox.question(
            self, 
            self.translator.tr('msg_confirm'),
            self.translator.tr('print_reset_confirm'),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.line1_edit.clear()
            self.line2_edit.clear()
            self.line3_edit.clear()
            self.clear_logo()
            self.auto_number_check.setChecked(True)
            self.prefix_edit.setText("DOC")
            self.manual_number_edit.clear()
            self.show_date_check.setChecked(True)
            self.date_format_combo.setCurrentIndex(0)
            self.extra_right_edit.clear()
            self.footer_left_edit.clear()
            self.footer_center_edit.clear()
            self.footer_right_edit.clear()
            self.page_numbers_check.setChecked(True)
            self.page_number_format_combo.setCurrentIndex(0)
            self.page_number_position_combo.setCurrentIndex(1)
            self.print_date_check.setChecked(True)
            self.orientation_combo.setCurrentIndex(0)
            self.page_size_combo.setCurrentIndex(0)
            self.margin_spin.setValue(15)
    
    def save_and_close(self):
        """Save settings and close dialog"""
        self.save_settings_to_object()
        if self.settings.save_settings():
            QMessageBox.information(
                self,
                self.translator.tr('msg_success'),
                self.translator.tr('print_settings_saved')
            )
            self.accept()
        else:
            QMessageBox.warning(
                self,
                self.translator.tr('msg_error'),
                self.translator.tr('print_settings_save_error')
            )


class ExportColumnDialog(QDialog):
    """Dialog for selecting columns and setting widths for export"""
    
    def __init__(self, parent, translator, columns: List[str], 
                 current_widths: Dict[str, int] = None):
        super().__init__(parent)
        self.translator = translator
        self.columns = columns
        self.settings = PrintSettings()
        self.current_widths = current_widths or self.settings.column_widths
        self.is_rtl = translator.current_language == 'ar'
        
        self.setWindowTitle(translator.tr('print_column_config'))
        # Apply fixed size to prevent resizing on button clicks or content changes
        from styles.styles import AppStyles
        AppStyles.apply_fixed_size(self, 550, 500)
        
        if self.is_rtl:
            self.setLayoutDirection(Qt.RightToLeft)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Info
        info = QLabel(self.translator.tr('print_column_width_info'))
        info.setWordWrap(True)
        info.setStyleSheet(AppStyles.get_component_style('print_info_box'))
        layout.addWidget(info)
        
        # Total indicator
        self.total_label = QLabel()
        self.total_label.setStyleSheet(AppStyles.get_component_style('print_total_label'))
        layout.addWidget(self.total_label)
        
        # Scrollable column list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        scroll_widget = QWidget()
        self.columns_layout = QVBoxLayout(scroll_widget)
        self.columns_layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid
        
        self.column_widgets = {}
        
        for col in self.columns:
            frame = QFrame()
            frame.setStyleSheet(AppStyles.get_component_style('print_column_frame'))
            row_layout = QHBoxLayout(frame)
            # Use 8px grid spacing
            row_margin_h = AppStyles.get_spacing(1)  # 8px horizontal (rounding 10px to 8px)
            row_margin_v = AppStyles.get_spacing(1)  # 8px vertical
            row_layout.setContentsMargins(row_margin_h, row_margin_v, row_margin_h, row_margin_v)
            
            # Checkbox
            cb = QCheckBox()
            cb.setChecked(True)
            cb.stateChanged.connect(self.update_total)
            row_layout.addWidget(cb)
            
            # Column name
            name_lbl = QLabel(col)
            name_lbl.setMinimumWidth(180)
            name_lbl.setFont(QFont('Segoe UI', 10))
            row_layout.addWidget(name_lbl, 1)
            
            # Width
            row_layout.addWidget(QLabel(self.translator.tr('print_width') + ":"))
            
            width_spin = QSpinBox()
            width_spin.setRange(5, 60)
            width_spin.setSuffix('%')
            width_spin.setValue(self.current_widths.get(col, 100 // max(len(self.columns), 1)))
            width_spin.valueChanged.connect(self.update_total)
            row_layout.addWidget(width_spin)
            
            # Auto checkbox
            auto_cb = QCheckBox(self.translator.tr('print_auto_width'))
            auto_cb.stateChanged.connect(lambda state, s=width_spin: s.setEnabled(not state))
            row_layout.addWidget(auto_cb)
            
            self.column_widgets[col] = {
                'checkbox': cb,
                'width': width_spin,
                'auto': auto_cb
            }
            
            self.columns_layout.addWidget(frame)
        
        self.columns_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Quick actions
        actions = QHBoxLayout()
        
        btn_all = QPushButton(self.translator.tr('btn_select_all'))
        btn_all.setAutoDefault(False)
        btn_all.setDefault(False)
        btn_all.clicked.connect(self.select_all)
        
        btn_none = QPushButton(self.translator.tr('btn_deselect_all'))
        btn_none.setAutoDefault(False)
        btn_none.setDefault(False)
        btn_none.clicked.connect(self.deselect_all)
        
        btn_equal = QPushButton(self.translator.tr('print_equal_widths'))
        btn_equal.setStyleSheet(AppStyles.get_component_style('print_equal_btn'))
        btn_equal.setAutoDefault(False)
        btn_equal.setDefault(False)
        btn_equal.clicked.connect(self.set_equal_widths)
        
        btn_auto = QPushButton(self.translator.tr('print_auto_all'))
        btn_auto.setAutoDefault(False)
        btn_auto.setDefault(False)
        btn_auto.clicked.connect(self.set_auto_all)
        
        actions.addWidget(btn_all)
        actions.addWidget(btn_none)
        actions.addWidget(btn_equal)
        actions.addWidget(btn_auto)
        actions.addStretch()
        
        layout.addLayout(actions)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_ok = QPushButton(self.translator.tr('btn_ok'))
        btn_ok.setStyleSheet(AppStyles.get_component_style('print_ok_btn'))
        btn_ok.setAutoDefault(False)
        btn_ok.setDefault(False)
        btn_ok.clicked.connect(self.accept)
        
        btn_cancel = QPushButton(self.translator.tr('btn_cancel'))
        btn_cancel.setAutoDefault(False)
        btn_cancel.setDefault(False)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        
        self.update_total()
    
    def update_total(self):
        """Update total width display"""
        total = 0
        auto_count = 0
        
        for widgets in self.column_widgets.values():
            if widgets['checkbox'].isChecked():
                if widgets['auto'].isChecked():
                    auto_count += 1
                else:
                    total += widgets['width'].value()
        
        if auto_count > 0:
            remaining = max(0, 100 - total)
            auto_width = remaining / auto_count
            self.total_label.setText(
                f"{self.translator.tr('print_total_width')}: {total}% + {auto_count} × {auto_width:.1f}% (auto) = ~100%"
            )
            self.total_label.setStyleSheet(AppStyles.get_component_style('print_total_valid'))
        else:
            if 95 <= total <= 105:
                style_key = 'print_total_valid'
            elif total > 105:
                style_key = 'print_total_error'
            else:
                style_key = 'print_total_warning'
            self.total_label.setText(f"{self.translator.tr('print_total_width')}: {total}%")
            self.total_label.setStyleSheet(AppStyles.get_component_style(style_key))
    
    def select_all(self):
        for w in self.column_widgets.values():
            w['checkbox'].setChecked(True)
    
    def deselect_all(self):
        for w in self.column_widgets.values():
            w['checkbox'].setChecked(False)
    
    def set_equal_widths(self):
        selected = [c for c, w in self.column_widgets.items() if w['checkbox'].isChecked()]
        if selected:
            width = 100 // len(selected)
            for col in selected:
                self.column_widgets[col]['width'].setValue(width)
                self.column_widgets[col]['auto'].setChecked(False)
                self.column_widgets[col]['width'].setEnabled(True)
    
    def set_auto_all(self):
        for w in self.column_widgets.values():
            w['auto'].setChecked(True)
    
    def get_selected_columns(self) -> List[str]:
        return [c for c, w in self.column_widgets.items() if w['checkbox'].isChecked()]
    
    def get_column_widths(self) -> Dict[str, int]:
        widths = {}
        for col, w in self.column_widgets.items():
            if w['checkbox'].isChecked() and not w['auto'].isChecked():
                widths[col] = w['width'].value()
        return widths


def generate_print_html(data: List[Dict], columns: List[str], 
                       column_widths: Dict[str, int] = None,
                       title: str = "",
                       translator = None) -> str:
    """Generate professional HTML document with consistent header for printing/export"""
    
    settings = PrintSettings()
    column_widths = column_widths or {}
    
    is_rtl = translator.current_language == 'ar' if translator else False
    direction = 'rtl' if is_rtl else 'ltr'
    text_align = 'right' if is_rtl else 'left'
    opposite_align = 'left' if is_rtl else 'right'
    
    # Arabic-specific font family for proper rendering
    if is_rtl:
        font_family = "'Noto Sans Arabic', 'Segoe UI', 'Tahoma', 'Arial', 'Traditional Arabic', 'Simplified Arabic', sans-serif"
        title_font = "'Noto Sans Arabic', 'Traditional Arabic', 'Segoe UI', sans-serif"
    else:
        font_family = "'Segoe UI', 'Tahoma', 'Arial', sans-serif"
        title_font = "'Segoe UI', 'Arial', sans-serif"
    
    # Calculate column widths
    # Create a copy to avoid modifying the original
    normalized_widths = column_widths.copy() if column_widths else {}
    
    # Normalize percentages if they don't sum to 100%
    total_specified = sum(normalized_widths.get(col, 0) for col in columns)
    if total_specified > 0 and total_specified != 100:
        # Normalize all specified widths to sum to 100%
        for col in columns:
            if col in normalized_widths:
                normalized_widths[col] = (normalized_widths[col] / total_specified) * 100
    
    auto_cols = [col for col in columns if col not in normalized_widths]
    remaining_percentage = 100 - sum(normalized_widths.get(col, 0) for col in columns)
    auto_width = (remaining_percentage / len(auto_cols)) if auto_cols and remaining_percentage > 0 else (100 / len(columns)) if columns else 10
    
    # Generate document number
    doc_number = settings.generate_doc_number()
    current_date = settings.get_formatted_date() if settings.header_right_show_date else ""
    
    # Logo HTML
    logo_html = ""
    if settings.header_logo_path and os.path.exists(settings.header_logo_path):
        logo_b64 = settings.get_logo_base64()
        mime_type = settings.get_logo_mime_type()
        logo_html = f'<img src="data:{mime_type};base64,{logo_b64}" style="max-height: 70px; max-width: 140px;">'
    
    # Print date for footer
    print_date = datetime.now().strftime("%Y-%m-%d %H:%M") if settings.show_print_date else ""
    
    # Get fonts directory path for embedded fonts
    fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts')
    
    # Build @font-face declarations for Arabic fonts
    font_face_css = ""
    if is_rtl:
        noto_arabic_regular = os.path.join(fonts_dir, 'NotoSansArabic-Regular.ttf')
        noto_arabic_bold = os.path.join(fonts_dir, 'NotoSansArabic-Bold.ttf')
        
        if os.path.exists(noto_arabic_regular):
            try:
                with open(noto_arabic_regular, 'rb') as f:
                    font_b64 = base64.b64encode(f.read()).decode('utf-8')
                    font_face_css += f"""
        @font-face {{
            font-family: 'Noto Sans Arabic';
            src: url('data:font/truetype;base64,{font_b64}') format('truetype');
            font-weight: normal;
            font-style: normal;
        }}
"""
            except:
                pass
        
        if os.path.exists(noto_arabic_bold):
            try:
                with open(noto_arabic_bold, 'rb') as f:
                    font_b64 = base64.b64encode(f.read()).decode('utf-8')
                    font_face_css += f"""
        @font-face {{
            font-family: 'Noto Sans Arabic';
            src: url('data:font/truetype;base64,{font_b64}') format('truetype');
            font-weight: bold;
            font-style: normal;
        }}
"""
            except:
                pass
    
    html = f'''<!DOCTYPE html>
<html dir="{direction}" lang="{'ar' if is_rtl else 'en'}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title or 'Report'}</title>
    <style>
        {font_face_css}
        
        @page {{
            size: {settings.page_size} {settings.page_orientation.lower()};
            margin: {settings.margin_mm}mm;
        }}
        
        * {{
            box-sizing: border-box;
        }}
        
        html {{
            direction: {direction};
        }}
        
        body {{
            font-family: {font_family};
            font-size: 10pt;
            direction: {direction};
            text-align: {text_align};
            margin: 0;
            padding: 0;
            color: #333;
            unicode-bidi: embed;
            line-height: 1.6;
        }}
        
        /* Arabic text improvements */
        {'p, td, th, span, div, label { unicode-bidi: embed; }' if is_rtl else ''}
        
        /* Header Styles */
        .header-container {{
            display: table;
            width: 100%;
            border-bottom: 3px solid #2C3E50;
            padding-bottom: 12px;
            margin-bottom: 20px;
            direction: {direction};
        }}
        
        .header-section {{
            display: table-cell;
            vertical-align: middle;
            width: 33.33%;
        }}
        
        .header-left {{
            text-align: {text_align};
        }}
        
        .header-center {{
            text-align: center;
        }}
        
        .header-right {{
            text-align: {opposite_align};
        }}
        
        .header-line1 {{
            font-family: {title_font};
            font-size: 16pt;
            font-weight: bold;
            color: #2C3E50;
            margin: 0 0 4px 0;
            line-height: 1.4;
        }}
        
        .header-line2 {{
            font-family: {font_family};
            font-size: 12pt;
            color: #34495E;
            margin: 0 0 3px 0;
            line-height: 1.4;
        }}
        
        .header-line3 {{
            font-family: {font_family};
            font-size: 10pt;
            color: #7F8C8D;
            margin: 0;
            line-height: 1.4;
        }}
        
        .doc-number {{
            font-size: 13pt;
            font-weight: bold;
            color: #2C3E50;
            margin: 0 0 4px 0;
            direction: ltr;
            unicode-bidi: isolate;
        }}
        
        .doc-date {{
            font-size: 11pt;
            color: #34495E;
            margin: 0 0 3px 0;
            direction: ltr;
            unicode-bidi: isolate;
        }}
        
        .doc-extra {{
            font-size: 10pt;
            color: #7F8C8D;
            margin: 0;
        }}
        
        /* Report Title */
        .report-title {{
            font-family: {title_font};
            font-size: 14pt;
            font-weight: bold;
            text-align: center;
            margin: 15px 0 20px 0;
            padding: 12px 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 6px;
            line-height: 1.5;
        }}
        
        /* Table Styles */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            direction: {direction};
        }}
        
        thead {{
            display: table-header-group;
        }}
        
        th {{
            font-family: {font_family};
            background: linear-gradient(180deg, #2C3E50 0%, #1a252f 100%);
            color: white;
            padding: 12px 10px;
            text-align: {text_align};
            font-weight: 600;
            font-size: 10pt;
            border: 1px solid #1a252f;
            line-height: 1.4;
        }}
        
        th:first-child {{
            border-radius: {'0 4px 0 0' if is_rtl else '4px 0 0 0'};
        }}
        
        th:last-child {{
            border-radius: {'4px 0 0 0' if is_rtl else '0 4px 0 0'};
        }}
        
        td {{
            font-family: {font_family};
            padding: 10px;
            border: 1px solid #DEE2E6;
            text-align: {text_align};
            font-size: 9pt;
            vertical-align: top;
            line-height: 1.5;
            word-wrap: break-word;
        }}
        
        tbody tr:nth-child(even) {{
            background-color: #F8F9FA;
        }}
        
        tbody tr:hover {{
            background-color: #E3F2FD;
        }}
        
        .row-number {{
            text-align: center;
            font-weight: bold;
            color: #7F8C8D;
            background-color: #ECEFF1;
            width: 5%;
            direction: ltr;
        }}
        
        .null-value {{
            color: #BDC3C7;
            font-style: italic;
        }}
        
        /* Footer Styles */
        .footer {{
            margin-top: 25px;
            padding-top: 12px;
            border-top: 2px solid #DEE2E6;
            display: table;
            width: 100%;
            font-size: 9pt;
            color: #7F8C8D;
            direction: {direction};
        }}
        
        .footer-section {{
            display: table-cell;
            width: 33.33%;
        }}
        
        .footer-left {{
            text-align: {text_align};
        }}
        
        .footer-center {{
            text-align: center;
        }}
        
        .footer-right {{
            text-align: {opposite_align};
        }}
        
        /* Print-specific styles */
        @media print {{
            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            
            .header-container {{
                position: running(header);
            }}
            
            @page {{
                @top-center {{
                    content: element(header);
                }}
            }}
            
            table {{
                page-break-inside: auto;
            }}
            
            tr {{
                page-break-inside: avoid;
                page-break-after: auto;
            }}
        }}
    </style>
</head>
<body>
    <!-- Professional Header -->
    <div class="header-container">
        <div class="header-section header-left">
            {'<p class="header-line1">' + settings.header_left_line1 + '</p>' if settings.header_left_line1 else ''}
            {'<p class="header-line2">' + settings.header_left_line2 + '</p>' if settings.header_left_line2 else ''}
            {'<p class="header-line3">' + settings.header_left_line3 + '</p>' if settings.header_left_line3 else ''}
        </div>
        <div class="header-section header-center">
            {logo_html}
        </div>
        <div class="header-section header-right">
            {'<p class="doc-number">#' + doc_number + '</p>' if doc_number else ''}
            {'<p class="doc-date">' + current_date + '</p>' if current_date else ''}
            {'<p class="doc-extra">' + settings.header_right_extra + '</p>' if settings.header_right_extra else ''}
        </div>
    </div>
'''
    
    # Report title
    if title:
        html += f'<div class="report-title">{title}</div>'
    
    # Data table
    html += '<table><thead><tr>'
    html += '<th class="row-number">#</th>'
    
    for col in columns:
        width = normalized_widths.get(col, auto_width)
        html += f'<th style="width: {width}%;">{col}</th>'
    
    html += '</tr></thead><tbody>'
    
    for idx, row in enumerate(data, 1):
        html += f'<tr><td class="row-number">{idx}</td>'
        for col in columns:
            value = row.get(col)
            formatted_value = format_value_for_html(value, col)
            if formatted_value == '-':
                html += '<td class="null-value">-</td>'
            else:
                html += f'<td>{formatted_value}</td>'
        html += '</tr>'
    
    html += '</tbody></table>'
    
    # Footer
    html += '''
    <div class="footer">
        <div class="footer-section footer-left">'''
    
    if settings.footer_left:
        html += settings.footer_left
    
    html += '''</div>
        <div class="footer-section footer-center">'''
    
    # Page numbers are drawn by print_document_with_page_numbers, not in HTML
    if settings.footer_center:
        html += settings.footer_center
    
    html += '''</div>
        <div class="footer-section footer-right">'''
    
    footer_right_parts = []
    if settings.footer_right:
        footer_right_parts.append(settings.footer_right)
    if print_date:
        footer_right_parts.append(print_date)
    
    html += ' | '.join(footer_right_parts) if footer_right_parts else ''
    
    html += '''</div>
    </div>
</body>
</html>'''
    
    # Save document number increment
    settings.save_settings()
    
    return html


def format_value_for_html(value, col_name: str = None) -> str:
    """Format value for HTML display - handles None and special values"""
    if value is None:
        return '-'
    if value == '':
        return '-'
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(value, (int, float)):
        # Check if importance column
        if col_name and 'importance' in col_name.lower():
            try:
                return f"{float(value) * 100:.0f}%"
            except:
                pass
        return str(value)
    
    # Convert to string and escape HTML
    str_val = str(value)
    if not str_val.strip():
        return '-'
    
    # Escape HTML characters
    str_val = str_val.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return str_val


def get_field_translation_map() -> Dict[str, str]:
    """
    Get comprehensive field translation mapping for all database columns.
    Maps field/column names to translation keys.
    """
    return {
        # Common fields
        'id': 'lbl_id',
        'name': 'lbl_name',
        'title': 'lbl_title',
        'type': 'lbl_type',
        'note': 'lbl_note',
        'description': 'lbl_description',
        'importance': 'lbl_importance',
        
        # Sources table fields
        'source': 'lbl_source',
        'source_name': 'lbl_source',
        'sources_id': 'lbl_source',
        'source_id': 'lbl_source',
        'link': 'lbl_link_sources',
        'link_sources': 'lbl_link_sources',
        'country': 'lbl_country',
        'city': 'lbl_city',
        'accounts': 'lbl_accounts',
        'ownership': 'lbl_ownership',
        
        # Contents table fields
        'content': 'lbl_content_data',
        'content_data': 'lbl_content_data',
        'attachments': 'lbl_attachments',
        
        # Content Analysis table fields
        'content_id': 'lbl_content_id',
        'classification': 'lbl_classification',
        'list_names_people': 'lbl_people',
        'list_names_places': 'lbl_places',
        'list_coordinates': 'lbl_coordinates',
        'list_sides': 'lbl_sides',
        'people': 'lbl_people',
        'people_names': 'lbl_people',
        'places': 'lbl_places',
        'place_names': 'lbl_places',
        'coordinates': 'lbl_coordinates',
        'sides': 'lbl_sides',
        
        # Date fields
        'date': 'lbl_date',
        'date_entry': 'lbl_date_entry',
        'date_creation': 'lbl_date_creation',
        'date_modified': 'lbl_date_modified',
        'date_content': 'lbl_date_content',
        'date_analysis': 'lbl_date_analysis',
        
        # All Data tab combined fields
        'record_type': 'lbl_record_type',
        'content_title': 'lbl_title',
        'content_importance': 'lbl_importance',
        'content_date_creation': 'lbl_date_creation',
        'source_date_creation': 'lbl_date_creation',
        'source_date_entry': 'lbl_date_entry',
        'analysis_date_creation': 'lbl_date_creation',
        
        # Report/Statistics fields
        'count': 'report_count',
        'sum': 'report_sum',
        'average': 'report_average',
        'avg': 'report_average',
        'max': 'report_max',
        'min': 'report_min',
        'total': 'report_total',
        'percentage': 'report_percentage',
        'category': 'report_category',
        
        # Size and file fields
        'size': 'lbl_size',
        'filename': 'lbl_filename',
        'actions': 'lbl_actions',
    }


def translate_field_name(field_name: str, translator) -> str:
    """
    Translate a field/column name based on current language.
    
    Args:
        field_name: The field/column name to translate
        translator: TranslationManager instance
        
    Returns:
        Translated field name or formatted original if no translation exists
    """
    if not translator:
        return field_name.replace('_', ' ').title()
    
    field_map = get_field_translation_map()
    field_lower = field_name.lower().strip()
    
    # Try exact match
    if field_lower in field_map:
        tr_key = field_map[field_lower]
        translated = translator.tr(tr_key)
        if translated != tr_key:
            return translated
    
    # Try partial match for compound names
    for key, tr_key in field_map.items():
        if key in field_lower or field_lower in key:
            translated = translator.tr(tr_key)
            if translated != tr_key:
                return translated
    
    # Fallback to formatted field name
    return field_name.replace('_', ' ').title()


def get_print_settings() -> PrintSettings:
    """Get the global print settings instance"""
    return PrintSettings()


def _format_page_number(page: int, total: int, fmt: str) -> str:
    """Format page number string based on format setting"""
    if fmt == 'page_x_of_y':
        return f"Page {page} of {total}"
    if fmt == 'x_of_y':
        return f"{page} of {total}"
    if fmt == 'x_slash_y':
        return f"{page} / {total}"
    if fmt == 'x_only':
        return str(page)
    return f"Page {page} of {total}"


def print_document_with_page_numbers(doc, printer, settings: PrintSettings = None):
    """
    Print QTextDocument with proper page numbers on every page.
    Uses manual pagination to draw page numbers in footer on each page.
    """
    from PyQt5.QtGui import QTextDocument
    from PyQt5.QtPrintSupport import QPrinter
    
    if settings is None:
        settings = get_print_settings()
    
    # Use device pixels for accurate layout (QPrinter uses 72 DPI for points)
    margin_pt = settings.margin_mm * 2.83465  # mm to points
    page_rect = printer.pageRect(QPrinter.Point)
    
    content_rect = QRectF(
        page_rect.left() + margin_pt,
        page_rect.top() + margin_pt,
        page_rect.width() - 2 * margin_pt,
        page_rect.height() - 2 * margin_pt
    )
    
    footer_height = 36
    page_content_height = content_rect.height() - footer_height
    
    # Document page size = content area per printed page
    doc.setPageSize(QRectF(0, 0, content_rect.width(), page_content_height).size())
    page_count = max(1, doc.pageCount())
    
    painter = QPainter(printer)
    
    for page in range(page_count):
        if page > 0:
            printer.newPage()
        
        # Draw document content for this page
        # Page N content is at y from N*pageHeight to (N+1)*pageHeight in document coords
        clip_rect = QRectF(0, page * page_content_height, content_rect.width(), page_content_height)
        painter.save()
        painter.translate(content_rect.left(), content_rect.top() - page * page_content_height)
        painter.setClipRect(QRectF(0, 0, content_rect.width(), page_content_height))
        doc.drawContents(painter, clip_rect)
        painter.restore()
        
        # Draw page number in footer
        if settings.show_page_numbers:
            page_text = _format_page_number(page + 1, page_count, settings.page_number_format)
            painter.setFont(QFont("Arial", 9))
            painter.setPen(QColor(100, 100, 100))
            
            footer_y = content_rect.bottom() - footer_height + 22
            
            if settings.page_number_position == 'left':
                painter.drawText(int(content_rect.left()), int(footer_y), page_text)
            elif settings.page_number_position == 'right':
                fm = painter.fontMetrics()
                text_width = fm.horizontalAdvance(page_text)
                painter.drawText(int(content_rect.right() - text_width), int(footer_y), page_text)
            else:  # center
                fm = painter.fontMetrics()
                text_width = fm.horizontalAdvance(page_text)
                x = content_rect.left() + (content_rect.width() - text_width) / 2
                painter.drawText(int(x), int(footer_y), page_text)
    
    painter.end()


def generate_timeline_print_html(events: List[Dict], translator, density_mode: str = 'comfortable') -> str:
    """Generate HTML for printing timeline events with preserved formatting"""
    from widgets.timeline_widget import TimelineEventWidget, TimelineDesignSystem
    
    settings = PrintSettings()
    is_rtl = translator.current_language == 'ar' if translator else False
    direction = 'rtl' if is_rtl else 'ltr'
    text_align = 'right' if is_rtl else 'left'
    opposite_align = 'left' if is_rtl else 'right'
    
    # Arabic-specific font family
    if is_rtl:
        font_family = "'Noto Sans Arabic', 'Segoe UI', 'Tahoma', 'Arial', sans-serif"
    else:
        font_family = "'Segoe UI', 'Tahoma', 'Arial', sans-serif"
    
    # Generate document number
    doc_number = settings.generate_doc_number()
    current_date = settings.get_formatted_date() if settings.header_right_show_date else ""
    print_date = datetime.now().strftime('%Y-%m-%d %H:%M') if settings.show_print_date else ""
    
    # Logo HTML
    logo_html = ""
    if settings.header_logo_path and os.path.exists(settings.header_logo_path):
        logo_b64 = settings.get_logo_base64()
        mime_type = settings.get_logo_mime_type()
        logo_html = f'<img src="data:{mime_type};base64,{logo_b64}" style="max-height: 70px; max-width: 140px;">'
    
    # Get density config for spacing
    config = TimelineDesignSystem.get_density_config(density_mode)
    
    html = f'''<!DOCTYPE html>
<html dir="{direction}" lang="{'ar' if is_rtl else 'en'}">
<head>
    <meta charset="UTF-8">
    <title>Timeline Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: {font_family};
            font-size: 11pt;
            line-height: 1.6;
            color: #2C3E50;
            direction: {direction};
            padding: 20px;
        }}
        
        .header-container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid #3498DB;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        
        .header-section {{
            flex: 1;
        }}
        
        .header-left {{
            text-align: {text_align};
        }}
        
        .header-center {{
            text-align: center;
        }}
        
        .header-right {{
            text-align: {opposite_align};
        }}
        
        .header-line1 {{
            font-size: 14pt;
            font-weight: bold;
            margin: 2px 0;
        }}
        
        .header-line2, .header-line3 {{
            font-size: 10pt;
            margin: 2px 0;
            color: #555;
        }}
        
        .doc-number {{
            font-size: 12pt;
            font-weight: bold;
            margin: 2px 0;
        }}
        
        .doc-date {{
            font-size: 10pt;
            margin: 2px 0;
            color: #555;
        }}
        
        .report-title {{
            font-size: 18pt;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
            color: #2C3E50;
        }}
        
        .timeline-event {{
            margin-bottom: {config['card_spacing']}px;
            padding: {config['card_padding']}px;
            border: 2px solid #E0E0E0;
            border-radius: 8px;
            background: linear-gradient(to bottom, #FFFFFF, #F8F9FA);
            page-break-inside: avoid;
        }}
        
        .event-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
        }}
        
        .event-date {{
            font-size: {config['font_date']}pt;
            font-weight: bold;
            color: #2C3E50;
            min-width: 160px;
        }}
        
        .event-title {{
            font-size: {config['font_title']}pt;
            font-weight: bold;
            color: #2C3E50;
            flex: 1;
            margin-{text_align}: 16px;
        }}
        
        .event-description {{
            font-size: {config['font_desc']}pt;
            color: #555555;
            margin: 10px 0;
            line-height: 1.5;
        }}
        
        .event-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }}
        
        .event-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: {config['font_meta']}pt;
            font-weight: bold;
        }}
        
        .badge-people {{
            background-color: #3498DB20;
            border: 1px solid #3498DB60;
            color: #3498DB;
        }}
        
        .badge-places {{
            background-color: #E74C3C20;
            border: 1px solid #E74C3C60;
            color: #E74C3C;
        }}
        
        .badge-classification {{
            background-color: #9B59B620;
            border: 1px solid #9B59B660;
            color: #9B59B6;
        }}
        
        .event-source {{
            font-size: {config['font_meta']}pt;
            color: #95A5A6;
            font-style: italic;
            margin-top: 8px;
        }}
        
        .footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 2px solid #DEE2E6;
            padding-top: 15px;
            margin-top: 30px;
            font-size: 9pt;
            color: #7F8C8D;
        }}
        
        .footer-left {{
            text-align: {text_align};
        }}
        
        .footer-center {{
            text-align: center;
        }}
        
        .footer-right {{
            text-align: {opposite_align};
        }}
        
        @media print {{
            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            
            .timeline-event {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <!-- Professional Header -->
    <div class="header-container">
        <div class="header-section header-left">
            {'<p class="header-line1">' + settings.header_left_line1 + '</p>' if settings.header_left_line1 else ''}
            {'<p class="header-line2">' + settings.header_left_line2 + '</p>' if settings.header_left_line2 else ''}
            {'<p class="header-line3">' + settings.header_left_line3 + '</p>' if settings.header_left_line3 else ''}
        </div>
        <div class="header-section header-center">
            {logo_html}
        </div>
        <div class="header-section header-right">
            {'<p class="doc-number">#' + doc_number + '</p>' if doc_number else ''}
            {'<p class="doc-date">' + current_date + '</p>' if current_date else ''}
            {'<p class="doc-extra">' + settings.header_right_extra + '</p>' if settings.header_right_extra else ''}
        </div>
    </div>
    
    <div class="report-title">Timeline Events Report</div>
'''
    
    # Add events
    for idx, event in enumerate(events, 1):
        # Get event date
        event_date = None
        date_fields = ['date_content', 'date_analysis', 'date_entry', 
                      'date_creation', 'source_date_entry', 'content_date_creation']
        for field in date_fields:
            if field in event and event[field]:
                date_val = event[field]
                if isinstance(date_val, datetime):
                    event_date = date_val
                elif isinstance(date_val, str):
                    try:
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']:
                            try:
                                event_date = datetime.strptime(date_val[:19], fmt)
                                break
                            except:
                                continue
                    except:
                        pass
                if event_date:
                    break
        
        date_str = event_date.strftime('%Y-%m-%d %H:%M') if event_date else 'No Date'
        
        # Get title
        title = ""
        if 'content_title' in event and event['content_title']:
            title = str(event['content_title'])
        elif 'classification' in event and event['classification']:
            title = str(event['classification'])
        elif 'source_name' in event and event['source_name']:
            title = str(event['source_name'])
        else:
            title = translator.tr('timeline_event', default='Event') if translator else 'Event'
        
        # Get description
        description = ""
        if 'content_data' in event and event['content_data']:
            content = str(event['content_data'])
            description = content[:500] + "..." if len(content) > 500 else content
        
        # Get metadata
        people = event.get('list_names_people', '')
        places = event.get('list_names_places', '')
        classification = event.get('classification', '')
        source = event.get('source_name', '')
        
        html += f'''
    <div class="timeline-event">
        <div class="event-header">
            <div class="event-date">{date_str}</div>
            <div class="event-title">{format_value_for_html(title)}</div>
        </div>
'''
        
        if description:
            html += f'        <div class="event-description">{format_value_for_html(description)}</div>\n'
        
        if people or places or classification:
            html += '        <div class="event-meta">\n'
            if people:
                html += f'            <span class="event-badge badge-people">👤 {format_value_for_html(str(people)[:50])}</span>\n'
            if places:
                html += f'            <span class="event-badge badge-places">📍 {format_value_for_html(str(places)[:50])}</span>\n'
            if classification:
                html += f'            <span class="event-badge badge-classification">🏷️ {format_value_for_html(classification)}</span>\n'
            html += '        </div>\n'
        
        if source:
            html += f'        <div class="event-source">📰 {format_value_for_html(source)}</div>\n'
        
        html += '    </div>\n'
    
    # Footer
    html += f'''
    <div class="footer">
        <div class="footer-section footer-left">
            {settings.footer_left if settings.footer_left else ''}
        </div>
        <div class="footer-section footer-center">
            {settings.footer_center if settings.footer_center else ''}
        </div>
        <div class="footer-section footer-right">
            {settings.footer_right if settings.footer_right else ''}
            {' | ' if settings.footer_right and print_date else ''}
            {print_date if print_date else ''}
        </div>
    </div>
</body>
</html>'''
    
    settings.save_settings()
    return html