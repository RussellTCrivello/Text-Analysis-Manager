"""
Frappe-Style Reports Interface
Professional Report Builder with SQL Query Support, Chart Designer, and Full Customization
"""
import sys
import os
import io
import json
import sqlite3
from html import escape
import warnings
from datetime import datetime
from pathlib import Path

# Suppress matplotlib layout warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
from typing import Dict, List, Optional, Any, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QScrollArea, QGridLayout, QGroupBox, QComboBox,
    QDateEdit, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QSplitter, QTextEdit,
    QSizePolicy, QSpacerItem, QProgressBar, QCheckBox, QLineEdit,
    QDialog, QDialogButtonBox, QFormLayout, QSpinBox, QRadioButton,
    QButtonGroup, QColorDialog, QListWidget, QListWidgetItem,
    QPlainTextEdit, QTreeWidget, QTreeWidgetItem, QAbstractItemView,
    QInputDialog, QMenu, QAction, QToolBar, QApplication, QStatusBar,
    QStackedWidget
)
from PyQt5.QtCore import Qt, QDate, QSize, QBuffer, QIODevice, QMarginsF, pyqtSignal, QTimer
from PyQt5.QtGui import (
    QFont, QColor, QPainter, QPixmap, QTextDocument, QPageLayout,
    QPageSize, QFontDatabase, QSyntaxHighlighter, QTextCharFormat
)
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog

from translations.translations import TranslationManager
from db.db_manager import DatabaseManager
from db.db_config import DatabaseConfig
from icons.icon_manager import setup_icon_button, get_icon
from utils.logger import get_logger
from utils.export_safety import sanitize_spreadsheet_value
from utils.table_ui import configure_table, set_item_with_tooltip
from utils.print_utils import PrintSettings, ExportColumnDialog, GlobalHeaderSettingsDialog, generate_print_html, get_print_settings, print_document_with_page_numbers
from dialogs.export_preview_dialog import ExportPreviewDialog
from styles.styles import AppStyles

logger = get_logger(__name__)

# Try to import matplotlib for charts
try:
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available. Charts will be disabled.")

# Try to import Arabic text reshaping libraries
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False
    logger.warning("arabic_reshaper/python-bidi not available. Arabic text in charts may not display correctly.")


def reshape_arabic_text(text: str) -> str:
    """
    Reshape Arabic text for proper display in matplotlib.
    Handles RTL text and character joining.
    """
    if not text or not ARABIC_SUPPORT:
        return text

    # Check if text contains Arabic characters
    has_arabic = any('\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F'
                     for char in text)

    if has_arabic:
        try:
            # Reshape the Arabic text (join characters properly)
            reshaped = arabic_reshaper.reshape(text)
            # Apply bidi algorithm to handle RTL
            bidi_text = get_display(reshaped)
            return bidi_text
        except Exception:
            return text

    return text


def setup_arabic_font_for_matplotlib():
    """Configure matplotlib to use a font that supports Arabic"""
    if not MATPLOTLIB_AVAILABLE:
        return

    # Try to find an Arabic-compatible font
    fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts')
    arabic_fonts = ['NotoSansArabic-Regular.ttf', 'tahoma.ttf', 'arial.ttf']

    font_path = None
    for font_name in arabic_fonts:
        potential_path = os.path.join(fonts_dir, font_name)
        if os.path.exists(potential_path):
            font_path = potential_path
            break

    if font_path:
        try:
            from matplotlib import font_manager
            font_manager.fontManager.addfont(font_path)
            prop = font_manager.FontProperties(fname=font_path)
            plt.rcParams['font.family'] = prop.get_name()
        except Exception as e:
            logger.warning(f"Could not set Arabic font: {e}")

    # Fallback to common fonts that support Arabic
    plt.rcParams['font.family'] = ['Tahoma', 'Arial', 'DejaVu Sans', 'sans-serif']


# Initialize Arabic font support
if MATPLOTLIB_AVAILABLE:
    setup_arabic_font_for_matplotlib()


class SQLHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for SQL queries"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_rules()

    def setup_rules(self):
        self.highlighting_rules = []

        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#0000FF"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'LIKE',
            'ORDER BY', 'GROUP BY', 'HAVING', 'LIMIT', 'OFFSET', 'AS',
            'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'UNION',
            'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER',
            'TABLE', 'INDEX', 'VIEW', 'TRIGGER', 'DISTINCT', 'ALL',
            'ASC', 'DESC', 'NULL', 'IS', 'BETWEEN', 'EXISTS', 'CASE',
            'WHEN', 'THEN', 'ELSE', 'END', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN',
            'COALESCE', 'IFNULL', 'CAST', 'DATE', 'TIME', 'DATETIME'
        ]
        for word in keywords:
            pattern = f'\\b{word}\\b'
            self.highlighting_rules.append((pattern, keyword_format, True))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#008000"))
        self.highlighting_rules.append(("'[^']*'", string_format, False))
        self.highlighting_rules.append(('"[^"]*"', string_format, False))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#FF8C00"))
        self.highlighting_rules.append(('\\b\\d+(\\.\\d+)?\\b', number_format, False))

        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#808080"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append(('--[^\n]*', comment_format, False))
        self.highlighting_rules.append(('/\\*.*\\*/', comment_format, False))

        # Table/Column names
        identifier_format = QTextCharFormat()
        identifier_format.setForeground(QColor("#800080"))
        self.highlighting_rules.append(('\\b(sources|contents|content_analysis)\\b', identifier_format, True))

    def highlightBlock(self, text):
        import re
        for pattern, fmt, case_insensitive in self.highlighting_rules:
            flags = re.IGNORECASE if case_insensitive else 0
            for match in re.finditer(pattern, text, flags):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class SavedReportDialog(QDialog):
    """Dialog to manage saved reports"""

    def __init__(self, parent, translator, reports_dir: str, mode: str = 'load'):
        super().__init__(parent)
        self.translator = translator
        self.reports_dir = reports_dir
        self.mode = mode
        self.selected_report = None

        self.setWindowTitle(translator.tr('report_saved_reports') if mode == 'load' else translator.tr('report_save'))
        # Apply fixed size to prevent resizing on button clicks or content changes
        from styles.styles import AppStyles
        AppStyles.apply_fixed_size(self, 500, 400)

        if translator.current_language == 'ar':
            self.setLayoutDirection(Qt.RightToLeft)

        self.setup_ui()
        self.load_reports_list()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        if self.mode == 'save':
            form_layout = QFormLayout()
            self.name_edit = QLineEdit()
            self.name_edit.setPlaceholderText(self.translator.tr('report_name_hint'))
            form_layout.addRow(self.translator.tr('report_name') + ":", self.name_edit)

            self.desc_edit = QLineEdit()
            form_layout.addRow(self.translator.tr('lbl_description') + ":", self.desc_edit)
            layout.addLayout(form_layout)

        # Reports list
        self.reports_list = QListWidget()
        self.reports_list.itemClicked.connect(self.on_report_selected)
        self.reports_list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.reports_list)

        # Buttons - properly aligned in a single row
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        btn_layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid (rounding 10px to 16px)

        if self.mode == 'load':
            self.btn_delete = QPushButton(self.translator.tr('btn_delete'))
            self.btn_delete.clicked.connect(self.delete_report)
            btn_layout.addWidget(self.btn_delete, alignment=Qt.AlignVCenter)

        btn_layout.addStretch()

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        btn_layout.addWidget(btn_box, alignment=Qt.AlignVCenter)

        layout.addLayout(btn_layout)

    def load_reports_list(self):
        self.reports_list.clear()
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
            return

        for filename in os.listdir(self.reports_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.reports_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    name = data.get('name', filename[:-5])
                    desc = data.get('description', '')
                    item = QListWidgetItem(f"{name} - {desc}" if desc else name)
                    item.setData(Qt.UserRole, filepath)
                    self.reports_list.addItem(item)
                except Exception:
                    pass

    def on_report_selected(self, item):
        self.selected_report = item.data(Qt.UserRole)
        if self.mode == 'save' and hasattr(self, 'name_edit'):
            try:
                with open(self.selected_report, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.name_edit.setText(data.get('name', ''))
                self.desc_edit.setText(data.get('description', ''))
            except Exception:
                pass

    def delete_report(self):
        if not self.selected_report:
            return
        try:
            report_root = Path(self.reports_dir).resolve()
            selected_path = Path(self.selected_report).resolve()
            selected_path.relative_to(report_root)
            if selected_path.suffix.lower() != '.json':
                raise ValueError('Invalid report file')
        except (OSError, ValueError):
            QMessageBox.warning(
                self,
                self.translator.tr('msg_warning'),
                self.translator.tr('report_invalid_file')
            )
            return

        reply = QMessageBox.question(
            self, self.translator.tr('msg_confirm'),
            self.translator.tr('msg_delete_confirm'),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                os.remove(selected_path)
                self.load_reports_list()
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))

    def get_report_name(self) -> str:
        if self.mode == 'save':
            return self.name_edit.text().strip()
        return ''

    def get_report_description(self) -> str:
        if self.mode == 'save':
            return self.desc_edit.text().strip()
        return ''


class ChartDesigner(QWidget):
    """Chart/Graphics Designer Widget"""

    chart_updated = pyqtSignal()

    def __init__(self, parent, translator):
        super().__init__(parent)
        self.translator = translator
        self.is_rtl = translator.current_language == 'ar'
        self.chart_config = {}
        self.chart_data = {}
        self.setup_ui()

    def _create_collapsible_group(self, title: str, expanded: bool = True) -> tuple:
        """Create a collapsible group box with header button and content widget"""
        # Container widget
        container = QWidget()
        container.setObjectName("collapsibleContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, AppStyles.get_spacing(1), AppStyles.get_spacing(1))  # 8px - 8px grid
        container_layout.setSpacing(0)

        # Header button (acts as toggle). Direction-independent graphical
        # chevrons keep the control readable in both LTR and RTL layouts.
        header_btn = QPushButton(title)
        header_btn.setIcon(get_icon('chevron_down' if expanded else 'chevron_right', 18))
        header_btn.setIconSize(QSize(18, 18))
        header_btn.setProperty('expanded', expanded)
        header_btn.setObjectName("collapsibleHeader")
        header_btn.setStyleSheet(AppStyles.get_component_style('report_collapsible_header'))
        header_btn.setCursor(Qt.PointingHandCursor)
        container_layout.addWidget(header_btn)

        # Content widget - Uses centralized styling
        content = QWidget()
        content.setObjectName("collapsibleContent")
        content.setStyleSheet(AppStyles.get_component_style('report_collapsible_content'))
        content.setVisible(expanded)
        container_layout.addWidget(content)

        # Connect toggle
        def toggle_content():
            is_visible = not content.isVisible()
            content.setVisible(is_visible)
            header_btn.setProperty('expanded', is_visible)
            header_btn.setIcon(get_icon('chevron_down' if is_visible else 'chevron_right', 18))
            header_btn.setIconSize(QSize(18, 18))
            header_btn.setText(title)

        header_btn.clicked.connect(toggle_content)

        return container, header_btn, content

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Main splitter for resizable panels
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(6)
        self.main_splitter.setStyleSheet(AppStyles.get_component_style('report_splitter'))

        # Left: Configuration panel (resizable)
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        config_scroll.setMinimumWidth(200)
        config_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)

        # Chart Type - Visual Selector with toggle buttons
        type_container, self.type_header, self.type_content = self._create_collapsible_group(
            self.translator.tr('report_chart_type'), expanded=True)
        self.type_group = type_container  # For compatibility with refresh
        type_layout = QVBoxLayout(self.type_content)
        # Use 8px grid spacing
        type_margin = AppStyles.get_spacing(2)  # 16px (rounding 12px to 16px)
        type_spacing = AppStyles.get_spacing(2)  # 16px (rounding 10px to 16px)
        type_layout.setContentsMargins(type_margin, type_margin, type_margin, type_margin)
        type_layout.setSpacing(type_spacing)

        # View mode toggle (Chart vs Table) - Improved styling
        view_mode_layout = QHBoxLayout()
        view_mode_layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid
        self.btn_chart_view = QPushButton(self.translator.tr('report_chart_view'))
        self.btn_chart_view.setIcon(get_icon('chart', 18))
        self.btn_chart_view.setIconSize(QSize(18, 18))
        self.btn_table_view = QPushButton(self.translator.tr('report_table_view'))
        self.btn_table_view.setIcon(get_icon('table', 18))
        self.btn_table_view.setIconSize(QSize(18, 18))

        view_mode_btn_style = """
            QPushButton {
                background-color: #ECF0F1;
                color: #2C3E50;
                border: 2px solid #BDC3C7;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #D5DBDB;
                border-color: #95A5A6;
            }
            QPushButton:checked {
                background-color: #3498DB;
                color: white;
                border-color: #2980B9;
            }
        """

        for btn in [self.btn_chart_view, self.btn_table_view]:
            btn.setCheckable(True)
            btn.setMinimumHeight(40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(view_mode_btn_style)

        self.btn_chart_view.setChecked(True)
        self.current_view_mode = 'chart'

        self.btn_chart_view.clicked.connect(lambda: self._set_view_mode('chart'))
        self.btn_table_view.clicked.connect(lambda: self._set_view_mode('table'))

        self._update_view_mode_buttons()

        view_mode_layout.addWidget(self.btn_chart_view)
        view_mode_layout.addWidget(self.btn_table_view)
        type_layout.addLayout(view_mode_layout)

        # Separator - Improved styling
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(2)
        separator.setStyleSheet(AppStyles.get_component_style('report_separator'))
        type_layout.addWidget(separator)

        # Chart type dropdown (only shown when chart view is selected)
        self.chart_type_widget = QWidget()
        chart_type_layout = QHBoxLayout(self.chart_type_widget)
        chart_type_layout.setContentsMargins(0, 0, 0, 0)
        chart_type_layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid (rounding 10px to 16px)

        # Label for chart type
        chart_type_label = QLabel(self.translator.tr('report_chart_type') + ":")
        chart_type_label.setStyleSheet(AppStyles.get_component_style('report_chart_type_label'))
        chart_type_layout.addWidget(chart_type_label)
        self.chart_type_label = chart_type_label

        # Chart types data with icons
        self.chart_types_data = [
            ('pie_chart', 'report_pie_chart', 0),
            ('statistics', 'report_bar_chart', 1),
            ('line_chart', 'report_line_chart', 2),
            ('statistics', 'report_horizontal_bar', 3),
            ('area_chart', 'report_area_chart', 4),
            ('donut_chart', 'report_donut_chart', 5),
        ]

        # Styled dropdown for chart types
        self.chart_types = QComboBox()
        self.chart_types.setMinimumWidth(180)
        self.chart_types.setMinimumHeight(36)

        # Populate dropdown with icons
        for icon_name, tr_key, idx in self.chart_types_data:
            self.chart_types.addItem(
                get_icon(icon_name, 18),
                self.translator.tr(tr_key),
                idx
            )

        self.chart_types.setStyleSheet(AppStyles.get_component_style('report_chart_combobox'))

        self.chart_types.currentIndexChanged.connect(self._on_chart_type_changed)
        chart_type_layout.addWidget(self.chart_types)
        chart_type_layout.addStretch()

        self.selected_chart_type = 0

        type_layout.addWidget(self.chart_type_widget)

        config_layout.addWidget(type_container)

        # Title (Collapsible)
        title_container, self.title_header, self.title_content = self._create_collapsible_group(
            self.translator.tr('lbl_title'), expanded=True)
        self.title_group = title_container
        title_layout = QVBoxLayout(self.title_content)
        # Use 8px grid spacing
        title_margin = AppStyles.get_spacing(2)  # 16px (rounding 12px to 16px)
        title_layout.setContentsMargins(title_margin, title_margin, title_margin, title_margin)
        title_layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid

        self.chart_title = QLineEdit()
        self.chart_title.setPlaceholderText(self.translator.tr('report_chart_title_hint'))
        self.chart_title.textChanged.connect(self.on_config_changed)
        title_layout.addWidget(self.chart_title)

        config_layout.addWidget(title_container)

        # Data Configuration (Collapsible)
        data_container, self.data_header, self.data_content = self._create_collapsible_group(
            self.translator.tr('report_data_config'), expanded=True)
        self.data_group = data_container
        data_layout = QFormLayout(self.data_content)
        # Use 8px grid spacing
        data_margin = AppStyles.get_spacing(2)  # 16px (rounding 12px to 16px)
        data_spacing = AppStyles.get_spacing(2)  # 16px (rounding 10px to 16px)
        data_layout.setContentsMargins(data_margin, data_margin, data_margin, data_margin)
        data_layout.setSpacing(data_spacing)
        data_layout.setHorizontalSpacing(AppStyles.get_spacing(2))  # 16px (rounding 12px to 16px)
        data_layout.setVerticalSpacing(AppStyles.get_spacing(2))  # 16px (rounding 12px to 16px)

        self.label_field = QComboBox()
        self.label_field_label = QLabel(self.translator.tr('report_label_field') + ":")
        data_layout.addRow(self.label_field_label, self.label_field)

        self.value_field = QComboBox()
        self.value_field_label = QLabel(self.translator.tr('report_value_field') + ":")
        data_layout.addRow(self.value_field_label, self.value_field)

        self.aggregation = QComboBox()
        self.aggregation.addItems([
            self.translator.tr('report_count'),
            self.translator.tr('report_sum'),
            self.translator.tr('report_average'),
            self.translator.tr('report_max'),
            self.translator.tr('report_min')
        ])
        self.aggregation_label = QLabel(self.translator.tr('report_aggregation') + ":")
        data_layout.addRow(self.aggregation_label, self.aggregation)

        self.label_field.currentIndexChanged.connect(self.on_config_changed)
        self.value_field.currentIndexChanged.connect(self.on_config_changed)
        self.aggregation.currentIndexChanged.connect(self.on_config_changed)

        config_layout.addWidget(data_container)

        # Styling (Collapsible)
        style_container, self.style_header, self.style_content = self._create_collapsible_group(
            self.translator.tr('report_chart_style'), expanded=True)
        self.style_group = style_container
        style_layout = QFormLayout(self.style_content)
        # Use 8px grid spacing
        style_margin = AppStyles.get_spacing(2)  # 16px (rounding 12px to 16px)
        style_spacing = AppStyles.get_spacing(2)  # 16px (rounding 10px to 16px)
        style_layout.setContentsMargins(style_margin, style_margin, style_margin, style_margin)
        style_layout.setSpacing(style_spacing)
        style_layout.setVerticalSpacing(AppStyles.get_spacing(2))  # 16px (rounding 12px to 16px)

        self.show_legend = QCheckBox(self.translator.tr('report_show_legend'))
        self.show_legend.setChecked(True)
        self.show_legend.stateChanged.connect(self.on_config_changed)
        style_layout.addRow(self.show_legend)

        self.show_values = QCheckBox(self.translator.tr('report_show_values'))
        self.show_values.setChecked(True)
        self.show_values.stateChanged.connect(self.on_config_changed)
        style_layout.addRow(self.show_values)

        self.show_grid = QCheckBox(self.translator.tr('report_show_grid'))
        self.show_grid.setChecked(True)
        self.show_grid.stateChanged.connect(self.on_config_changed)
        style_layout.addRow(self.show_grid)

        # Colors
        self.color_scheme = QComboBox()
        self.color_scheme.addItems([
            self.translator.tr('color_scheme_default'),
            self.translator.tr('color_scheme_pastel'),
            self.translator.tr('color_scheme_dark'),
            self.translator.tr('color_scheme_vibrant'),
            self.translator.tr('color_scheme_monochrome')
        ])
        self.color_scheme.currentIndexChanged.connect(self.on_config_changed)
        self.color_scheme_label = QLabel(self.translator.tr('report_color_scheme') + ":")
        style_layout.addRow(self.color_scheme_label, self.color_scheme)

        config_layout.addWidget(style_container)

        # Limit (Collapsible)
        limit_container, self.limit_header, self.limit_content = self._create_collapsible_group(
            self.translator.tr('report_limit'), expanded=True)
        self.limit_group = limit_container
        limit_layout = QHBoxLayout(self.limit_content)
        # Use 8px grid spacing
        limit_margin = AppStyles.get_spacing(2)  # 16px (rounding 12px to 16px)
        limit_spacing = AppStyles.get_spacing(2)  # 16px (rounding 12px to 16px)
        limit_layout.setContentsMargins(limit_margin, limit_margin, limit_margin, limit_margin)
        limit_layout.setSpacing(limit_spacing)

        self.limit_check = QCheckBox(self.translator.tr('report_limit_results'))
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 100)
        self.limit_spin.setValue(10)
        self.limit_check.stateChanged.connect(self.on_config_changed)
        self.limit_spin.valueChanged.connect(self.on_config_changed)

        limit_layout.addWidget(self.limit_check)
        limit_layout.addWidget(self.limit_spin)
        limit_layout.addStretch()

        config_layout.addWidget(limit_container)

        # Generate button - Prominent styling
        self.btn_generate = QPushButton(self.translator.tr('report_generate_chart'))
        self.btn_generate.setIcon(get_icon('refresh', 18))
        self.btn_generate.setIconSize(QSize(18, 18))
        self.btn_generate.setMinimumHeight(45)
        self.btn_generate.setCursor(Qt.PointingHandCursor)
        self.btn_generate.setStyleSheet(AppStyles.get_component_style('report_generate_button'))
        self.btn_generate.clicked.connect(self.generate_chart)
        config_layout.addWidget(self.btn_generate)

        config_layout.addStretch()
        config_scroll.setWidget(config_widget)

        # Right: Chart preview
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)

        self.preview_label = QLabel(self.translator.tr('report_chart_preview'))
        self.preview_label.setStyleSheet(AppStyles.get_component_style('report_preview_label'))
        preview_layout.addWidget(self.preview_label)

        self.chart_frame = QFrame()
        self.chart_frame.setStyleSheet(AppStyles.get_component_style('report_chart_frame'))
        self.chart_frame.setMinimumSize(500, 400)

        chart_frame_layout = QVBoxLayout(self.chart_frame)

        if MATPLOTLIB_AVAILABLE:
            self.figure = Figure(figsize=(6, 5), dpi=100)
            self.figure.patch.set_facecolor('#FFFFFF')
            self.canvas = FigureCanvas(self.figure)
            chart_frame_layout.addWidget(self.canvas)
        else:
            placeholder = QLabel(self.translator.tr('msg_matplotlib_required') if hasattr(self, 'translator') and self.translator else "Charts require matplotlib.\nInstall with: pip install matplotlib")
            placeholder.setAlignment(Qt.AlignCenter)
            chart_frame_layout.addWidget(placeholder)

        preview_layout.addWidget(self.chart_frame)

        # Add panels to splitter
        self.main_splitter.addWidget(config_scroll)
        self.main_splitter.addWidget(preview_widget)

        # Set initial sizes (config panel: 300px, preview: rest)
        self.main_splitter.setSizes([300, 600])
        self.main_splitter.setStretchFactor(0, 0)  # Config panel doesn't stretch
        self.main_splitter.setStretchFactor(1, 1)  # Preview stretches

        layout.addWidget(self.main_splitter)

    def _set_view_mode(self, mode: str):
        """Switch between chart and table view modes"""
        self.current_view_mode = mode
        self.btn_chart_view.setChecked(mode == 'chart')
        self.btn_table_view.setChecked(mode == 'table')
        self._update_view_mode_buttons()

        # Show/hide chart type selector based on mode
        self.chart_type_widget.setVisible(mode == 'chart')

        # Update chart if in chart mode
        if mode == 'chart':
            self.on_config_changed()
        else:
            # Show table view in chart frame
            self._show_table_view()

    def _update_view_mode_buttons(self):
        """Update view mode button styles"""
        active_style = AppStyles.get_component_style('view_mode_active')
        inactive_style = AppStyles.get_component_style('view_mode_inactive')

        self.btn_chart_view.setStyleSheet(active_style if self.current_view_mode == 'chart' else inactive_style)
        self.btn_table_view.setStyleSheet(active_style if self.current_view_mode == 'table' else inactive_style)

    def _on_chart_type_changed(self, index: int):
        """Handle chart type dropdown change"""
        if index >= 0:
            self.selected_chart_type = self.chart_types.itemData(index)
            self.on_config_changed()

    def _select_chart_type(self, index: int):
        """Select a chart type programmatically"""
        self.selected_chart_type = index

        # Update dropdown selection
        self.chart_types.blockSignals(True)
        for i in range(self.chart_types.count()):
            if self.chart_types.itemData(i) == index:
                self.chart_types.setCurrentIndex(i)
                break
        self.chart_types.blockSignals(False)

        # Regenerate chart
        self.on_config_changed()

    def _show_table_view(self):
        """Display data as a table instead of chart"""
        if not MATPLOTLIB_AVAILABLE or not self.chart_data:
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.axis('off')

        if self.chart_data:
            # Get column headers and limit data rows
            columns = list(self.chart_data[0].keys())[:6]  # Limit columns for display
            rows_data = []
            for row in self.chart_data[:15]:  # Limit to 15 rows
                row_values = [
                    ('' if row.get(col, '') is None else str(row.get(col, '')))[:20]
                    for col in columns
                ]  # Truncate values
                rows_data.append(row_values)

            # Create table
            table = ax.table(
                cellText=rows_data,
                colLabels=columns,
                cellLoc='center',
                loc='center',
                colColours=['#2C3E50'] * len(columns)
            )

            # Style the table
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 1.5)

            # Style header cells
            for j in range(len(columns)):
                table[(0, j)].set_text_props(color='white', fontweight='bold')

            # Alternate row colors
            for i in range(len(rows_data)):
                for j in range(len(columns)):
                    if i % 2 == 0:
                        table[(i + 1, j)].set_facecolor('#F8F9FA')
                    else:
                        table[(i + 1, j)].set_facecolor('white')

            ax.set_title(f"{self.translator.tr('report_data_table')} ({len(self.chart_data)} {self.translator.tr('report_rows')})",
                        fontsize=12, fontweight='bold', color='#2C3E50', pad=20)
        else:
            ax.text(0.5, 0.5, self.translator.tr('report_no_data'),
                   ha='center', va='center', fontsize=14, color='#7F8C8D')

        self.canvas.draw()

    def set_available_fields(self, fields: List[str]):
        """Set available fields for chart configuration"""
        self.label_field.clear()
        self.value_field.clear()

        for field in fields:
            self.label_field.addItem(field)
            self.value_field.addItem(field)

    def set_data(self, data: List[Dict]):
        """Set data for chart generation"""
        self.chart_data = data

        # Auto-detect fields
        if data:
            fields = list(data[0].keys())
            self.set_available_fields(fields)

    def on_config_changed(self):
        """Handle configuration changes"""
        self.chart_config = self.get_config()

    def get_config(self) -> dict:
        """Get current chart configuration"""
        # Get chart type from item data (index stored as data)
        chart_type = self.chart_types.currentData()
        if chart_type is None:
            chart_type = self.chart_types.currentIndex()

        return {
            'chart_type': chart_type,
            'title': self.chart_title.text(),
            'label_field': self.label_field.currentText(),
            'value_field': self.value_field.currentText(),
            'aggregation': self.aggregation.currentIndex(),
            'show_legend': self.show_legend.isChecked(),
            'show_values': self.show_values.isChecked(),
            'show_grid': self.show_grid.isChecked(),
            'color_scheme': self.color_scheme.currentIndex(),
            'limit_enabled': self.limit_check.isChecked(),
            'limit_value': self.limit_spin.value()
        }

    def set_config(self, config: dict):
        """Apply configuration"""
        self.chart_types.setCurrentIndex(config.get('chart_type', 0))
        self.chart_title.setText(config.get('title', ''))
        # Set other fields...

    def generate_chart(self):
        """Generate chart from data and config"""
        if not MATPLOTLIB_AVAILABLE or not self.chart_data:
            return

        config = self.get_config()
        label_field = config['label_field']
        value_field = config['value_field']
        aggregation = config['aggregation']

        # Check if data is already aggregated (each label appears only once)
        # This happens when the SQL query already did GROUP BY with COUNT/SUM/etc.
        label_counts = {}
        for row in self.chart_data:
            label = str(row.get(label_field, 'Unknown') or 'Unknown')
            label_counts[label] = label_counts.get(label, 0) + 1

        # If each label appears only once, data is likely pre-aggregated
        is_pre_aggregated = all(count == 1 for count in label_counts.values())

        # Check if value_field contains numeric data that looks like aggregation results
        has_numeric_values = False
        if is_pre_aggregated and value_field:
            for row in self.chart_data:
                val = row.get(value_field)
                if val is not None:
                    try:
                        float(val)
                        has_numeric_values = True
                        break
                    except (ValueError, TypeError):
                        pass

        # If data is pre-aggregated with numeric values, use them directly
        if is_pre_aggregated and has_numeric_values and value_field != label_field:
            aggregated = {}
            for row in self.chart_data:
                label = str(row.get(label_field, 'Unknown') or 'Unknown')
                try:
                    value = float(row.get(value_field, 0) or 0)
                except (ValueError, TypeError):
                    value = 0
                aggregated[label] = value
        else:
            # Standard aggregation for raw data
            aggregated = {}
            for row in self.chart_data:
                label = str(row.get(label_field, 'Unknown') or 'Unknown')

                if aggregation == 0:  # Count
                    aggregated[label] = aggregated.get(label, 0) + 1
                else:
                    try:
                        value = float(row.get(value_field, 0) or 0)
                    except (ValueError, TypeError):
                        value = 0

                    if aggregation == 1:  # Sum
                        aggregated[label] = aggregated.get(label, 0) + value
                    elif aggregation == 2:  # Average
                        if label not in aggregated:
                            aggregated[label] = {'sum': 0, 'count': 0}
                        aggregated[label]['sum'] += value
                        aggregated[label]['count'] += 1
                    elif aggregation == 3:  # Max
                        aggregated[label] = max(aggregated.get(label, float('-inf')), value)
                    elif aggregation == 4:  # Min
                        aggregated[label] = min(aggregated.get(label, float('inf')), value)

            # Calculate averages
            if aggregation == 2:
                aggregated = {k: v['sum'] / v['count'] if isinstance(v, dict) and v['count'] > 0 else 0
                             for k, v in aggregated.items()}

        # Apply limit
        if config['limit_enabled']:
            limit = config['limit_value']
            sorted_items = sorted(aggregated.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0, reverse=True)[:limit]
            aggregated = dict(sorted_items)

        # Draw chart
        self.draw_chart(aggregated, config)
        self.chart_updated.emit()

    def draw_chart(self, data: Dict, config: dict):
        """Draw the chart with proper Arabic text support"""
        if not MATPLOTLIB_AVAILABLE:
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if not data:
            ax.text(0.5, 0.5, reshape_arabic_text(self.translator.tr('report_no_data')),
                   ha='center', va='center')
            self.canvas.draw()
            return

        # Reshape Arabic text in labels
        labels = [reshape_arabic_text(str(k)) for k in data.keys()]
        values = [v if isinstance(v, (int, float)) else 0 for v in data.values()]

        # Validate values - check if all zeros or sum is zero (would cause matplotlib warnings)
        total_sum = sum(abs(v) for v in values)
        if total_sum == 0 or all(v == 0 for v in values):
            ax.text(0.5, 0.5, reshape_arabic_text(self.translator.tr('report_no_valid_data') if hasattr(self.translator, 'tr') else 'No valid data to display'),
                   ha='center', va='center', fontsize=12, color='#7F8C8D')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            self.canvas.draw()
            return

        # Color schemes
        color_schemes = {
            0: ['#3498DB', '#2ECC71', '#E74C3C', '#F39C12', '#9B59B6', '#1ABC9C', '#E67E22', '#34495E'],
            1: ['#FFB6C1', '#87CEEB', '#98FB98', '#DDA0DD', '#F0E68C', '#E0FFFF', '#FFDAB9', '#D8BFD8'],
            2: ['#2C3E50', '#1A252F', '#34495E', '#2E4053', '#283747', '#212F3C', '#1B2631', '#17202A'],
            3: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F'],
            4: ['#2C3E50', '#34495E', '#5D6D7E', '#85929E', '#ABB2B9', '#D5D8DC', '#F2F3F4', '#FDFEFE']
        }
        colors = color_schemes.get(config['color_scheme'], color_schemes[0])
        # Extend colors if needed
        while len(colors) < len(labels):
            colors = colors + colors
        colors = colors[:len(labels)]

        chart_type = config['chart_type']
        title = reshape_arabic_text(config['title'])

        if chart_type == 0:  # Pie
            # Suppress potential division warnings for edge cases
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                wedges, texts, autotexts = ax.pie(
                    values, labels=labels, autopct='%1.1f%%' if config['show_values'] else '',
                    colors=colors, startangle=90
                )
            if config['show_values']:
                for autotext in autotexts:
                    autotext.set_fontsize(9)
                    autotext.set_color('white')
            for text in texts:
                text.set_fontsize(10)
            ax.axis('equal')

        elif chart_type == 1:  # Bar
            x_pos = range(len(labels))
            bars = ax.bar(x_pos, values, color=colors)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
            if config['show_values']:
                for bar, value in zip(bars, values):
                    ax.annotate(f'{value:.0f}' if isinstance(value, float) else str(value),
                               xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                               xytext=(0, 3), textcoords="offset points",
                               ha='center', va='bottom', fontsize=9)
            if config['show_grid']:
                ax.grid(True, alpha=0.3, axis='y')

        elif chart_type == 2:  # Line
            x_pos = range(len(labels))
            ax.plot(x_pos, values, marker='o', color=colors[0], linewidth=2, markersize=8)
            ax.fill_between(x_pos, values, alpha=0.3, color=colors[0])
            ax.set_xticks(x_pos)
            ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
            if config['show_grid']:
                ax.grid(True, alpha=0.3)

        elif chart_type == 3:  # Horizontal Bar
            y_pos = range(len(labels))
            bars = ax.barh(y_pos, values, color=colors)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=9)
            if config['show_values']:
                for bar, value in zip(bars, values):
                    ax.annotate(f'{value:.0f}' if isinstance(value, float) else str(value),
                               xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
                               xytext=(3, 0), textcoords="offset points",
                               ha='left', va='center', fontsize=9)
            if config['show_grid']:
                ax.grid(True, alpha=0.3, axis='x')

        elif chart_type == 4:  # Area
            x_pos = range(len(labels))
            ax.fill_between(x_pos, values, alpha=0.7, color=colors[0])
            ax.plot(x_pos, values, color=colors[0], linewidth=2)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
            if config['show_grid']:
                ax.grid(True, alpha=0.3)

        elif chart_type == 5:  # Donut
            # Suppress potential division warnings for edge cases
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                wedges, texts, autotexts = ax.pie(
                    values, labels=labels, autopct='%1.1f%%' if config['show_values'] else '',
                    colors=colors, startangle=90, pctdistance=0.75
                )
            for text in texts:
                text.set_fontsize(10)
            # Draw center circle
            centre_circle = plt.Circle((0, 0), 0.50, fc='white')
            ax.add_patch(centre_circle)
            ax.axis('equal')

        ax.set_title(title, fontsize=12, fontweight='bold', color='#2C3E50', pad=10)

        # Style
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['left', 'bottom']:
            ax.spines[spine].set_color('#DEE2E6')

        # Handle layout - use try/except to suppress warnings
        try:
            self.figure.tight_layout(pad=1.5)
        except Exception:
            # Fallback: manual adjustment for charts with many labels
            self.figure.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.25)

        self.canvas.draw()

    def get_image_bytes(self) -> bytes:
        """Get chart as image bytes"""
        if not MATPLOTLIB_AVAILABLE:
            return b''

        buffer = io.BytesIO()
        self.figure.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                           facecolor='white', edgecolor='none')
        buffer.seek(0)
        return buffer.getvalue()


class QueryBuilder(QWidget):
    """SQL Query Builder Widget with Raw SQL and Visual Builder."""

    # The visual builder only supports these application-owned tables and
    # columns. Keeping this allowlist independent from combo-box text prevents
    # a tampered widget state or a hostile database schema from becoming an SQL
    # identifier injection.
    VISUAL_TABLE_COLUMNS = {
        'sources': {
            'id', 'name', 'type', 'link_sources', 'importance', 'country',
            'city', 'description', 'accounts', 'note', 'ownership',
            'date_entry', 'date_creation', 'date_modified',
        },
        'contents': {
            'id', 'title', 'content_data', 'attachments', 'note', 'importance',
            'date_content', 'date_creation', 'date_modified', 'sources_id',
        },
        'content_analysis': {
            'id', 'content_id', 'list_names_people', 'list_names_places',
            'list_coordinates', 'classification', 'list_sides',
            'date_analysis', 'date_creation', 'date_modified',
        },
    }
    VISUAL_TABLES = frozenset(VISUAL_TABLE_COLUMNS)
    VISUAL_FIELDS = frozenset(
        f'{table}.{column}'
        for table, columns in VISUAL_TABLE_COLUMNS.items()
        for column in columns
    )

    query_executed = pyqtSignal(list, list)  # data, columns
    query_failed = pyqtSignal(str)

    def __init__(self, parent, translator):
        super().__init__(parent)
        self.translator = translator
        self.is_rtl = translator.current_language == 'ar'
        self.db_path = DatabaseConfig.get_db_path()
        self.query_params = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Mode selector - styled as toggle buttons
        mode_layout = QHBoxLayout()
        mode_layout.setContentsMargins(0, 0, 0, AppStyles.get_spacing(2))  # 16px (rounding 10px to 16px)
        self.mode_group = QButtonGroup(self)

        self.sql_mode_btn = QRadioButton(self.translator.tr('report_sql_mode'))
        self.sql_mode_btn.setChecked(True)
        self.visual_mode_btn = QRadioButton(self.translator.tr('report_visual_mode'))

        # Style radio buttons as toggle switches
        mode_btn_style = """
            QRadioButton {
                background-color: #FFFFFF;
                border: 2px solid #3498DB;
                border-radius: 15px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 11px;
                color: #3498DB;
                min-width: 100px;
            }
            QRadioButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498DB, stop:1 #2980B9);
                color: white;
                border-color: #2980B9;
            }
            QRadioButton:hover {
                background-color: #EBF5FB;
            }
            QRadioButton:checked:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5DADE2, stop:1 #3498DB);
            }
            QRadioButton::indicator {
                width: 0px;
                height: 0px;
            }
        """
        self.sql_mode_btn.setStyleSheet(mode_btn_style)
        self.visual_mode_btn.setStyleSheet(mode_btn_style)

        self.mode_group.addButton(self.sql_mode_btn, 0)
        self.mode_group.addButton(self.visual_mode_btn, 1)

        mode_layout.addWidget(self.sql_mode_btn)
        mode_layout.addWidget(self.visual_mode_btn)
        mode_layout.addStretch()

        self.mode_group.buttonClicked.connect(self.on_mode_changed)

        layout.addLayout(mode_layout)

        # Stacked widget for modes
        self.stacked = QStackedWidget()

        # SQL Mode
        sql_widget = self.create_sql_mode()
        self.stacked.addWidget(sql_widget)

        # Visual Mode
        visual_widget = self.create_visual_mode()
        self.stacked.addWidget(visual_widget)

        layout.addWidget(self.stacked)

        # Execute buttons - styled prominently and aligned in a single row
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, AppStyles.get_spacing(2), 0, 0)  # 16px (rounding 10px to 16px)
        btn_layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid (rounding 10px to 16px)
        btn_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment

        self.btn_execute = QPushButton(self.translator.tr('report_execute'))
        self.btn_execute.setIcon(get_icon('play', 18))
        self.btn_execute.setIconSize(QSize(18, 18))
        self.btn_execute.setStyleSheet(AppStyles.get_component_style('report_execute_button'))
        self.btn_execute.clicked.connect(self.execute_query)

        self.btn_clear = QPushButton(self.translator.tr('btn_clear'))
        self.btn_clear.setStyleSheet(AppStyles.get_component_style('report_clear_button'))
        self.btn_clear.clicked.connect(self.clear_query)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_clear, alignment=Qt.AlignVCenter)
        btn_layout.addWidget(self.btn_execute, alignment=Qt.AlignVCenter)

        layout.addLayout(btn_layout)

    def create_sql_mode(self) -> QWidget:
        # Create main scroll area for SQL mode
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_scroll.setFrameShape(QFrame.NoFrame)
        main_scroll.setStyleSheet(AppStyles.get_component_style('report_main_scroll'))

        widget = QWidget()
        layout = QVBoxLayout(widget)
        main_scroll.setWidget(widget)

        # SQL Editor
        editor_label = QLabel(self.translator.tr('report_sql_query'))
        editor_label.setStyleSheet(AppStyles.get_component_style('report_editor_label'))
        layout.addWidget(editor_label)

        self.sql_editor = QPlainTextEdit()
        self.sql_editor.setPlaceholderText(
            "SELECT * FROM sources\n"
            "SELECT s.name, COUNT(c.id) as content_count\n"
            "FROM sources s\n"
            "LEFT JOIN contents c ON s.id = c.sources_id\n"
            "GROUP BY s.id"
        )
        self.sql_editor.setMinimumHeight(200)
        self.sql_editor.setStyleSheet(AppStyles.get_component_style('report_sql_editor'))

        # Syntax highlighting
        self.highlighter = SQLHighlighter(self.sql_editor.document())

        layout.addWidget(self.sql_editor)

        # Quick templates
        self.templates_group = QGroupBox(self.translator.tr('report_query_templates'))
        templates_layout = QGridLayout(self.templates_group)
        # Set column stretch to allow buttons to expand and show full text
        templates_layout.setColumnStretch(0, 1)
        templates_layout.setColumnStretch(1, 1)
        templates_layout.setColumnStretch(2, 1)
        templates_layout.setColumnStretch(3, 1)

        # Store template button references for translation refresh
        self.template_buttons = []

        # Define template keys for translation (translation_key, sql_query)
        template_definitions = [
            # Basic Queries
            ('report_all_sources', "SELECT * FROM sources ORDER BY date_creation DESC"),
            ('report_all_contents', "SELECT c.*, s.name as source_name FROM contents c LEFT JOIN sources s ON c.sources_id = s.id ORDER BY c.date_creation DESC"),
            ('report_all_analysis', "SELECT ca.*, c.content_data, s.name as source_name FROM content_analysis ca LEFT JOIN contents c ON ca.content_id = c.id LEFT JOIN sources s ON c.sources_id = s.id"),
            ('report_sources_by_type', "SELECT type, COUNT(*) as count FROM sources GROUP BY type ORDER BY count DESC"),
            ('report_sources_by_country', "SELECT country, COUNT(*) as count FROM sources WHERE country IS NOT NULL GROUP BY country ORDER BY count DESC"),
            ('report_content_count', "SELECT s.name, COUNT(c.id) as content_count FROM sources s LEFT JOIN contents c ON s.id = c.sources_id GROUP BY s.id ORDER BY content_count DESC"),
            ('report_importance_avg', "SELECT type, AVG(importance) as avg_importance FROM sources GROUP BY type"),
            ('report_full_join', "SELECT s.*, c.*, ca.* FROM sources s LEFT JOIN contents c ON s.id = c.sources_id LEFT JOIN content_analysis ca ON c.id = ca.content_id"),

            # Time-Based Analysis
            ('report_recent_content', "SELECT c.*, s.name as source_name, s.type as source_type FROM contents c LEFT JOIN sources s ON c.sources_id = s.id WHERE c.date_creation >= datetime('now', '-30 days') ORDER BY c.date_creation DESC"),
            ('report_content_by_month', "SELECT strftime('%Y-%m', date_creation) as month, COUNT(*) as count FROM contents GROUP BY month ORDER BY month DESC"),
            ('report_sources_by_date', "SELECT strftime('%Y-%m', date_creation) as month, COUNT(*) as count FROM sources GROUP BY month ORDER BY month DESC"),
            ('report_analysis_trends', "SELECT strftime('%Y-%m', date_analysis) as month, COUNT(*) as count FROM content_analysis WHERE date_analysis IS NOT NULL GROUP BY month ORDER BY month DESC"),

            # Statistical Analysis
            ('report_top_sources_importance', "SELECT name, type, importance, country FROM sources ORDER BY importance DESC LIMIT 20"),
            ('report_importance_distribution', "SELECT CASE WHEN importance >= 0.8 THEN 'Very High' WHEN importance >= 0.6 THEN 'High' WHEN importance >= 0.4 THEN 'Medium' WHEN importance >= 0.2 THEN 'Low' ELSE 'Very Low' END as importance_level, COUNT(*) as count FROM sources GROUP BY importance_level ORDER BY importance DESC"),
            ('report_avg_importance_country', "SELECT country, AVG(importance) as avg_importance, COUNT(*) as source_count FROM sources WHERE country IS NOT NULL GROUP BY country ORDER BY avg_importance DESC"),
            ('report_avg_importance_city', "SELECT city, country, AVG(importance) as avg_importance, COUNT(*) as source_count FROM sources WHERE city IS NOT NULL GROUP BY city, country ORDER BY avg_importance DESC"),
            ('report_content_importance_stats', "SELECT s.name, AVG(c.importance) as avg_content_importance, COUNT(c.id) as content_count FROM sources s LEFT JOIN contents c ON s.id = c.sources_id GROUP BY s.id HAVING content_count > 0 ORDER BY avg_content_importance DESC"),

            # Geographic Analysis
            ('report_sources_by_city', "SELECT city, country, COUNT(*) as count FROM sources WHERE city IS NOT NULL GROUP BY city, country ORDER BY count DESC"),
            ('report_content_by_country', "SELECT s.country, COUNT(c.id) as content_count, AVG(c.importance) as avg_importance FROM sources s LEFT JOIN contents c ON s.id = c.sources_id WHERE s.country IS NOT NULL GROUP BY s.country ORDER BY content_count DESC"),
            ('report_geographic_distribution', "SELECT country, COUNT(DISTINCT s.id) as sources, COUNT(c.id) as contents, AVG(s.importance) as avg_source_importance FROM sources s LEFT JOIN contents c ON s.id = c.sources_id WHERE country IS NOT NULL GROUP BY country ORDER BY sources DESC"),

            # Content Analysis
            ('report_content_with_analysis', "SELECT c.*, s.name as source_name, ca.classification, ca.list_names_people, ca.list_names_places FROM contents c LEFT JOIN sources s ON c.sources_id = s.id INNER JOIN content_analysis ca ON c.id = ca.content_id ORDER BY c.date_creation DESC"),
            ('report_content_without_analysis', "SELECT c.*, s.name as source_name FROM contents c LEFT JOIN sources s ON c.sources_id = s.id LEFT JOIN content_analysis ca ON c.id = ca.content_id WHERE ca.id IS NULL ORDER BY c.date_creation DESC"),
            ('report_classification_distribution', "SELECT classification, COUNT(*) as count FROM content_analysis WHERE classification IS NOT NULL GROUP BY classification ORDER BY count DESC"),
            ('report_content_by_importance', "SELECT CASE WHEN importance >= 0.8 THEN 'Very High' WHEN importance >= 0.6 THEN 'High' WHEN importance >= 0.4 THEN 'Medium' WHEN importance >= 0.2 THEN 'Low' ELSE 'Very Low' END as importance_level, COUNT(*) as count FROM contents GROUP BY importance_level ORDER BY importance DESC"),
            ('report_most_analyzed_content', "SELECT c.id, c.content_data, s.name as source_name, COUNT(ca.id) as analysis_count FROM contents c LEFT JOIN sources s ON c.sources_id = s.id LEFT JOIN content_analysis ca ON c.id = ca.content_id GROUP BY c.id HAVING analysis_count > 0 ORDER BY analysis_count DESC LIMIT 20"),

            # Performance Metrics
            ('report_most_active_sources', "SELECT s.name, s.type, COUNT(c.id) as content_count, MAX(c.date_creation) as last_content_date FROM sources s LEFT JOIN contents c ON s.id = c.sources_id GROUP BY s.id HAVING content_count > 0 ORDER BY content_count DESC LIMIT 20"),
            ('report_sources_without_content', "SELECT s.* FROM sources s LEFT JOIN contents c ON s.id = c.sources_id WHERE c.id IS NULL ORDER BY s.date_creation DESC"),
            ('report_analysis_coverage', "SELECT COUNT(DISTINCT c.id) as total_contents, COUNT(DISTINCT ca.content_id) as analyzed_contents, ROUND(COUNT(DISTINCT ca.content_id) * 100.0 / COUNT(DISTINCT c.id), 2) as coverage_percent FROM contents c LEFT JOIN content_analysis ca ON c.id = ca.content_id"),
            ('report_recent_additions', "SELECT 'Sources' as type, COUNT(*) as count FROM sources WHERE date_creation >= datetime('now', '-7 days') UNION ALL SELECT 'Contents', COUNT(*) FROM contents WHERE date_creation >= datetime('now', '-7 days') UNION ALL SELECT 'Analysis', COUNT(*) FROM content_analysis WHERE date_creation >= datetime('now', '-7 days')"),

            # Advanced Analytics
            ('report_source_statistics', "SELECT s.id, s.name, s.type, s.importance, s.country, COUNT(c.id) as content_count, COUNT(ca.id) as analysis_count, AVG(c.importance) as avg_content_importance, MAX(c.date_creation) as last_content_date FROM sources s LEFT JOIN contents c ON s.id = c.sources_id LEFT JOIN content_analysis ca ON c.id = ca.content_id GROUP BY s.id ORDER BY s.importance DESC"),
            ('report_content_stats_by_type', "SELECT s.type, COUNT(DISTINCT s.id) as source_count, COUNT(c.id) as content_count, AVG(c.importance) as avg_content_importance, COUNT(ca.id) as analysis_count FROM sources s LEFT JOIN contents c ON s.id = c.sources_id LEFT JOIN content_analysis ca ON c.id = ca.content_id GROUP BY s.type ORDER BY content_count DESC"),
            ('report_people_mentioned', "SELECT list_names_people, COUNT(*) as mention_count FROM content_analysis WHERE list_names_people IS NOT NULL AND list_names_people != '' GROUP BY list_names_people ORDER BY mention_count DESC LIMIT 30"),
            ('report_places_mentioned', "SELECT list_names_places, COUNT(*) as mention_count FROM content_analysis WHERE list_names_places IS NOT NULL AND list_names_places != '' GROUP BY list_names_places ORDER BY mention_count DESC LIMIT 30"),
            ('report_data_quality_metrics', "SELECT 'Sources with description' as metric, COUNT(*) as count FROM sources WHERE description IS NOT NULL AND description != '' UNION ALL SELECT 'Sources with city', COUNT(*) FROM sources WHERE city IS NOT NULL UNION ALL SELECT 'Contents with attachments', COUNT(*) FROM contents WHERE attachments IS NOT NULL AND attachments != '' UNION ALL SELECT 'Analysis with classification', COUNT(*) FROM content_analysis WHERE classification IS NOT NULL AND classification != ''"),
            ('report_comprehensive_overview', "SELECT 'Total Sources' as metric, COUNT(*) as value FROM sources UNION ALL SELECT 'Total Contents', COUNT(*) FROM contents UNION ALL SELECT 'Total Analysis', COUNT(*) FROM content_analysis UNION ALL SELECT 'Avg Source Importance', ROUND(AVG(importance), 3) FROM sources UNION ALL SELECT 'Avg Content Importance', ROUND(AVG(importance), 3) FROM contents UNION ALL SELECT 'Sources with Content', COUNT(DISTINCT sources_id) FROM contents UNION ALL SELECT 'Contents with Analysis', COUNT(DISTINCT content_id) FROM content_analysis"),
        ]

        # Build templates list with translated names
        templates = [(self.translator.tr(key), sql) for key, sql in template_definitions]

        # Store definitions for refresh
        self.template_definitions = template_definitions

        for i, (name, sql) in enumerate(templates):
            btn = QPushButton(name)
            # Set size policy to allow full text display and expansion
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            btn.setMinimumHeight(45)  # Ensure enough height for text
            btn.setMinimumWidth(120)  # Minimum width to show more text
            # Set tooltip to show full text on hover
            btn.setToolTip(name)
            btn.setStyleSheet(AppStyles.get_component_style('report_template_button'))
            btn.clicked.connect(lambda checked, q=sql: self.sql_editor.setPlainText(q))
            templates_layout.addWidget(btn, i // 4, i % 4)
            # Store button reference for translation refresh
            self.template_buttons.append(btn)

        layout.addWidget(self.templates_group)

        # Tables structure
        self.structure_group = QGroupBox(self.translator.tr('report_db_structure'))
        structure_layout = QVBoxLayout(self.structure_group)

        self.structure_tree = QTreeWidget()
        self.structure_tree.setHeaderLabels([self.translator.tr('report_table_column'), self.translator.tr('lbl_type')])
        self.structure_tree.setMaximumHeight(200)
        # Ensure columns resize to show full text
        self.structure_tree.header().setStretchLastSection(False)
        self.structure_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.structure_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.load_db_structure()

        structure_layout.addWidget(self.structure_tree)
        layout.addWidget(self.structure_group)

        return main_scroll  # Return scroll area containing the widget

    def create_visual_mode(self) -> QWidget:
        # Create scroll area for visual mode content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(AppStyles.get_component_style('report_scroll_transparent'))

        widget = QWidget()
        layout = QVBoxLayout(widget)
        scroll.setWidget(widget)

        # Common group box styling
        group_style = AppStyles.get_component_style('group_box_full_text')

        # Table selection
        self.table_group = QGroupBox(self.translator.tr('report_select_tables'))
        self.table_group.setStyleSheet(group_style)
        table_layout = QHBoxLayout(self.table_group)
        table_layout.setSpacing(15)
        table_layout.setContentsMargins(15, 15, 15, 10)

        # Checkbox styling
        checkbox_style = AppStyles.get_component_style('report_limit_checkbox')

        self.table_checks = {}
        for table_name in ['sources', 'contents', 'content_analysis']:
            check = QCheckBox(table_name)
            check.setChecked(True)
            check.setStyleSheet(checkbox_style)
            check.stateChanged.connect(self.update_visual_fields)
            self.table_checks[table_name] = check
            table_layout.addWidget(check)

        table_layout.addStretch()
        layout.addWidget(self.table_group)

        # Field selection
        self.fields_group = QGroupBox(self.translator.tr('report_select_fields'))
        self.fields_group.setStyleSheet(group_style)
        fields_layout = QVBoxLayout(self.fields_group)
        fields_layout.setContentsMargins(10, 15, 10, 10)
        fields_layout.setSpacing(8)

        self.fields_list = QListWidget()
        self.fields_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.fields_list.setMinimumHeight(80)
        self.fields_list.setMaximumHeight(120)
        self.fields_list.setStyleSheet(AppStyles.get_component_style('report_fields_list'))
        fields_layout.addWidget(self.fields_list)

        # Select all / Deselect all buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        select_btn_style = AppStyles.get_component_style('report_select_button')

        self.btn_select_all = QPushButton(self.translator.tr('btn_select_all'))
        self.btn_select_all.setStyleSheet(select_btn_style)
        self.btn_select_all.clicked.connect(lambda: self.select_all_fields(True))

        self.btn_deselect_all = QPushButton(self.translator.tr('btn_deselect_all'))
        self.btn_deselect_all.setStyleSheet(select_btn_style)
        self.btn_deselect_all.clicked.connect(lambda: self.select_all_fields(False))

        btn_row.addWidget(self.btn_select_all)
        btn_row.addWidget(self.btn_deselect_all)
        fields_layout.addLayout(btn_row)

        layout.addWidget(self.fields_group)

        # Advanced Filters
        self.filter_group = QGroupBox(self.translator.tr('report_filters'))
        self.filter_group.setStyleSheet(group_style)
        filter_main_layout = QVBoxLayout(self.filter_group)
        filter_main_layout.setContentsMargins(10, 15, 10, 10)
        filter_main_layout.setSpacing(10)

        # Filter toolbar
        filter_toolbar = QHBoxLayout()
        filter_toolbar.setSpacing(8)

        self.btn_add_filter = QPushButton(self.translator.tr('report_add_filter'))
        self.btn_add_filter.setIcon(get_icon('add', 16))
        self.btn_add_filter.setIconSize(QSize(16, 16))
        self.btn_add_filter.setStyleSheet(AppStyles.get_component_style('report_add_filter_button'))
        self.btn_add_filter.clicked.connect(self.add_filter_row)

        self.btn_add_filter_group = QPushButton(self.translator.tr('report_add_group'))
        self.btn_add_filter_group.setIcon(get_icon('add', 16))
        self.btn_add_filter_group.setIconSize(QSize(16, 16))
        self.btn_add_filter_group.setStyleSheet(AppStyles.get_component_style('report_add_group_btn'))
        self.btn_add_filter_group.clicked.connect(self.add_filter_group)

        self.btn_clear_filters = QPushButton(self.translator.tr('btn_clear'))
        self.btn_clear_filters.setStyleSheet(AppStyles.get_component_style('report_clear_filters_btn'))
        self.btn_clear_filters.clicked.connect(self.clear_all_filters)

        filter_toolbar.addWidget(self.btn_add_filter)
        filter_toolbar.addWidget(self.btn_add_filter_group)
        filter_toolbar.addStretch()
        filter_toolbar.addWidget(self.btn_clear_filters)

        filter_main_layout.addLayout(filter_toolbar)

        # Global logic selector
        global_logic_layout = QHBoxLayout()
        global_logic_layout.setSpacing(10)
        self.combine_filters_label = QLabel(self.translator.tr('report_combine_filters') + ":")
        self.combine_filters_label.setStyleSheet(AppStyles.get_component_style('report_combine_label'))
        global_logic_layout.addWidget(self.combine_filters_label)

        self.global_logic_combo = QComboBox()
        self.global_logic_combo.addItems(['AND', 'OR'])
        self.global_logic_combo.setToolTip(self.translator.tr('report_global_logic_hint'))
        self.global_logic_combo.setStyleSheet(AppStyles.get_component_style('report_global_logic_combo'))
        global_logic_layout.addWidget(self.global_logic_combo)
        global_logic_layout.addStretch()
        filter_main_layout.addLayout(global_logic_layout)

        # Scrollable filter container
        self.filter_scroll = QScrollArea()
        self.filter_scroll.setWidgetResizable(True)
        self.filter_scroll.setMaximumHeight(200)
        self.filter_scroll.setStyleSheet(AppStyles.get_component_style('report_filter_scroll'))

        self.filter_container = QWidget()
        self.filter_container_layout = QVBoxLayout(self.filter_container)
        self.filter_container_layout.setSpacing(5)
        self.filter_container_layout.setContentsMargins(5, 5, 5, 5)

        # Initialize with one filter row
        self.filter_rows = []
        self.filter_groups = []
        self.add_filter_row()

        self.filter_container_layout.addStretch()
        self.filter_scroll.setWidget(self.filter_container)
        filter_main_layout.addWidget(self.filter_scroll)

        # Quick filter presets
        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(8)

        self.quick_filters_label = QLabel(self.translator.tr('report_quick_filters') + ":")
        self.quick_filters_label.setStyleSheet(AppStyles.get_component_style('report_quick_filters_label'))
        presets_layout.addWidget(self.quick_filters_label)

        # Quick filter buttons
        quick_filter_style = AppStyles.get_component_style('report_quick_filter_btn')

        self.btn_preset_today = QPushButton(self.translator.tr('report_filter_today'))
        self.btn_preset_today.setStyleSheet(quick_filter_style)
        self.btn_preset_today.clicked.connect(lambda: self.apply_date_preset('today'))

        self.btn_preset_week = QPushButton(self.translator.tr('report_filter_week'))
        self.btn_preset_week.setStyleSheet(quick_filter_style)
        self.btn_preset_week.clicked.connect(lambda: self.apply_date_preset('week'))

        self.btn_preset_month = QPushButton(self.translator.tr('report_filter_month'))
        self.btn_preset_month.setStyleSheet(quick_filter_style)
        self.btn_preset_month.clicked.connect(lambda: self.apply_date_preset('month'))

        self.btn_preset_high_importance = QPushButton(self.translator.tr('report_filter_high_importance'))
        self.btn_preset_high_importance.setStyleSheet(AppStyles.get_component_style('report_importance_filter_btn'))
        self.btn_preset_high_importance.clicked.connect(self.apply_high_importance_filter)

        presets_layout.addWidget(self.btn_preset_today)
        presets_layout.addWidget(self.btn_preset_week)
        presets_layout.addWidget(self.btn_preset_month)
        presets_layout.addWidget(self.btn_preset_high_importance)
        presets_layout.addStretch()

        filter_main_layout.addLayout(presets_layout)
        layout.addWidget(self.filter_group)

        # Ordering
        self.order_group = QGroupBox(self.translator.tr('report_ordering'))
        self.order_group.setStyleSheet(group_style)
        order_layout = QHBoxLayout(self.order_group)
        order_layout.setContentsMargins(15, 15, 15, 10)
        order_layout.setSpacing(12)

        # ComboBox style for ordering
        combo_style = """
            QComboBox {
                background-color: white;
                border: 2px solid #BDC3C7;
                border-radius: 5px;
                padding: 6px 10px;
                font-size: 10px;
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #3498DB;
            }
            QComboBox:focus {
                border-color: #3498DB;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #7F8C8D;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #BDC3C7;
                border-radius: 3px;
                background-color: white;
                selection-background-color: #3498DB;
                padding: 3px;
            }
        """

        self.order_field = QComboBox()
        self.order_field.setStyleSheet(combo_style)
        self.order_direction = QComboBox()
        self.order_direction.addItems(['ASC', 'DESC'])
        self.order_direction.setStyleSheet(combo_style.replace("min-width: 120px", "min-width: 70px"))

        self.order_by_label = QLabel(self.translator.tr('report_order_by') + ":")
        self.order_by_label.setStyleSheet(AppStyles.get_component_style('report_order_label'))
        order_layout.addWidget(self.order_by_label)
        order_layout.addWidget(self.order_field)
        order_layout.addWidget(self.order_direction)
        order_layout.addStretch()

        layout.addWidget(self.order_group)

        # Limit section
        limit_layout = QHBoxLayout()
        limit_layout.setContentsMargins(5, 5, 5, 5)
        limit_layout.setSpacing(10)

        self.limit_check = QCheckBox(self.translator.tr('report_limit_results'))
        self.limit_check.setStyleSheet(AppStyles.get_component_style('report_limit_checkbox'))

        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 10000)
        self.limit_spin.setValue(100)
        self.limit_spin.setStyleSheet(AppStyles.get_component_style('report_limit_spinbox'))

        limit_layout.addWidget(self.limit_check)
        limit_layout.addWidget(self.limit_spin)
        limit_layout.addStretch()

        layout.addLayout(limit_layout)

        # Generated SQL preview
        self.generated_sql = QPlainTextEdit()
        self.generated_sql.setReadOnly(True)
        self.generated_sql.setMaximumHeight(80)
        self.generated_sql.setPlaceholderText(self.translator.tr('report_generated_sql'))
        self.generated_sql.setStyleSheet(AppStyles.get_component_style('report_generated_sql'))
        layout.addWidget(self.generated_sql)

        # Initial load
        self.update_visual_fields()

        return scroll  # Return scroll area containing the widget

    def load_db_structure(self):
        """Load database structure into tree"""
        self.structure_tree.clear()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = cursor.fetchall()

            for (table_name,) in tables:
                table_item = QTreeWidgetItem([table_name, 'TABLE'])
                table_item.setFont(0, QFont('Segoe UI', 10, QFont.Bold))

                # Get columns
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                for col in columns:
                    col_name = col[1]
                    col_type = col[2]
                    col_item = QTreeWidgetItem([col_name, col_type])
                    table_item.addChild(col_item)

                self.structure_tree.addTopLevelItem(table_item)

            conn.close()
            self.structure_tree.expandAll()

        except Exception as e:
            logger.error(f"Error loading DB structure: {e}")

    def update_visual_fields(self):
        """Update available fields based on selected tables"""
        self.fields_list.clear()

        selected_tables = [name for name, check in self.table_checks.items() if check.isChecked()]

        if not selected_tables:
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            self.available_fields = []
            for table in selected_tables:
                if table not in self.VISUAL_TABLES:
                    continue
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                allowed_columns = self.VISUAL_TABLE_COLUMNS[table]
                for col in columns:
                    if col[1] not in allowed_columns:
                        continue
                    field_name = f"{table}.{col[1]}"
                    self.available_fields.append(field_name)
                    item = QListWidgetItem(field_name)
                    item.setSelected(True)
                    self.fields_list.addItem(item)

            # Update filter field combos in all filter rows
            self.update_filter_field_combos()

            # Update order field
            self.order_field.clear()
            self.order_field.addItems(self.available_fields)

            conn.close()

        except Exception as e:
            logger.error(f"Error updating fields: {e}")

    def update_filter_field_combos(self):
        """Update all filter row field combos with current available fields"""
        fields = getattr(self, 'available_fields', [])
        for filter_row in self.filter_rows:
            field_combo = filter_row.get('field_combo')
            if field_combo:
                current_text = field_combo.currentText()
                field_combo.clear()
                field_combo.addItem('')
                field_combo.addItems(fields)
                # Restore selection if possible
                idx = field_combo.findText(current_text)
                if idx >= 0:
                    field_combo.setCurrentIndex(idx)

    def add_filter_row(self, group_widget=None):
        """Add a new filter row"""
        filter_widget = QFrame()
        filter_widget.setFrameStyle(QFrame.StyledPanel)
        filter_widget.setStyleSheet(AppStyles.get_component_style('report_filter_row_frame'))

        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(10, 8, 10, 8)
        filter_layout.setSpacing(8)

        # Common combo style for filter row
        filter_combo_style = AppStyles.get_component_style('report_filter_combo')

        # Field selector
        field_combo = QComboBox()
        field_combo.setMinimumWidth(140)
        field_combo.setStyleSheet(filter_combo_style)
        field_combo.addItem('')
        if hasattr(self, 'available_fields'):
            field_combo.addItems(self.available_fields)
        filter_layout.addWidget(field_combo)

        # Operator selector
        op_combo = QComboBox()
        op_combo.setMinimumWidth(90)
        op_combo.setStyleSheet(filter_combo_style)
        op_combo.addItems([
            '=', '!=', '>', '<', '>=', '<=',
            'LIKE', 'NOT LIKE', 'CONTAINS', 'STARTS WITH', 'ENDS WITH',
            'IS NULL', 'IS NOT NULL', 'IN', 'NOT IN', 'BETWEEN'
        ])
        op_combo.currentTextChanged.connect(lambda text, w=filter_widget: self.on_operator_changed(text, w))
        filter_layout.addWidget(op_combo)

        # Value input style
        value_style = AppStyles.get_component_style('filter_value_input')

        # Value input (can be different widgets based on operator)
        value_widget = QLineEdit()
        value_widget.setPlaceholderText(self.translator.tr('report_enter_value'))
        value_widget.setMinimumWidth(130)
        value_widget.setStyleSheet(value_style)
        filter_layout.addWidget(value_widget)

        # Second value (for BETWEEN operator)
        value2_widget = QLineEdit()
        value2_widget.setPlaceholderText(self.translator.tr('report_to_value'))
        value2_widget.setMinimumWidth(80)
        value2_widget.setStyleSheet(value_style)
        value2_widget.hide()
        filter_layout.addWidget(value2_widget)

        # Logic connector (for next filter)
        logic_combo = QComboBox()
        logic_combo.addItems(['AND', 'OR'])
        logic_combo.setMinimumWidth(60)
        logic_combo.setStyleSheet(filter_combo_style)
        filter_layout.addWidget(logic_combo)

        # Remove button
        btn_remove = QPushButton()
        btn_remove.setIcon(get_icon('close', 16))
        btn_remove.setIconSize(QSize(16, 16))
        btn_remove.setToolTip(self.translator.tr('btn_delete') if hasattr(self.translator, 'tr') else 'Remove filter')
        btn_remove.setAccessibleName(self.translator.tr('btn_delete') if hasattr(self.translator, 'tr') else 'Remove filter')
        btn_remove.setFixedSize(26, 26)
        btn_remove.setStyleSheet(AppStyles.get_component_style('report_remove_btn'))
        btn_remove.clicked.connect(lambda: self.remove_filter_row(filter_widget))
        filter_layout.addWidget(btn_remove)

        # Store reference
        filter_data = {
            'widget': filter_widget,
            'field_combo': field_combo,
            'op_combo': op_combo,
            'value_widget': value_widget,
            'value2_widget': value2_widget,
            'logic_combo': logic_combo,
            'group': group_widget
        }
        self.filter_rows.append(filter_data)

        # Add to container
        if group_widget:
            group_layout = group_widget.layout()
            group_layout.insertWidget(group_layout.count() - 1, filter_widget)
        else:
            self.filter_container_layout.insertWidget(len(self.filter_rows) - 1, filter_widget)

        return filter_data

    def remove_filter_row(self, filter_widget):
        """Remove a filter row"""
        for i, filter_data in enumerate(self.filter_rows):
            if filter_data['widget'] == filter_widget:
                filter_widget.setParent(None)
                filter_widget.deleteLater()
                self.filter_rows.pop(i)
                break

        # Ensure at least one filter row exists
        if not self.filter_rows:
            self.add_filter_row()

    def add_filter_group(self):
        """Add a filter group (nested filters with their own logic)"""
        group_frame = QFrame()
        group_frame.setFrameStyle(QFrame.Box)
        group_frame.setStyleSheet(AppStyles.get_component_style('report_filter_group_frame'))

        group_layout = QVBoxLayout(group_frame)
        group_layout.setContentsMargins(10, 10, 10, 10)

        # Group header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(self.translator.tr('report_filter_group') + ":"))

        group_logic = QComboBox()
        group_logic.addItems(['AND', 'OR'])
        header_layout.addWidget(group_logic)

        btn_add_to_group = QPushButton(self.translator.tr('report_add_filter'))
        btn_add_to_group.setIcon(get_icon('add', 16))
        btn_add_to_group.setIconSize(QSize(16, 16))
        btn_add_to_group.clicked.connect(lambda: self.add_filter_row(group_frame))
        header_layout.addWidget(btn_add_to_group)

        header_layout.addStretch()

        btn_remove_group = QPushButton()
        btn_remove_group.setIcon(get_icon('close', 16))
        btn_remove_group.setIconSize(QSize(16, 16))
        btn_remove_group.setToolTip(self.translator.tr('btn_delete') if hasattr(self.translator, 'tr') else 'Remove filter group')
        btn_remove_group.setAccessibleName(self.translator.tr('btn_delete') if hasattr(self.translator, 'tr') else 'Remove filter group')
        btn_remove_group.setFixedSize(25, 25)
        btn_remove_group.setStyleSheet(AppStyles.get_component_style('report_small_remove_btn'))
        btn_remove_group.clicked.connect(lambda: self.remove_filter_group(group_frame))
        header_layout.addWidget(btn_remove_group)

        group_layout.addLayout(header_layout)
        group_layout.addStretch()

        self.filter_groups.append({
            'widget': group_frame,
            'logic_combo': group_logic
        })

        # Add initial filter to group
        self.add_filter_row(group_frame)

        # Insert before stretch
        self.filter_container_layout.insertWidget(self.filter_container_layout.count() - 1, group_frame)

    def remove_filter_group(self, group_widget):
        """Remove a filter group and all its filters"""
        # Remove all filters in this group
        filters_to_remove = [f for f in self.filter_rows if f.get('group') == group_widget]
        for filter_data in filters_to_remove:
            self.filter_rows.remove(filter_data)

        # Remove group
        for i, group_data in enumerate(self.filter_groups):
            if group_data['widget'] == group_widget:
                group_widget.setParent(None)
                group_widget.deleteLater()
                self.filter_groups.pop(i)
                break

    def clear_all_filters(self):
        """Clear all filters"""
        # Remove all filter rows
        for filter_data in self.filter_rows[:]:
            filter_data['widget'].setParent(None)
            filter_data['widget'].deleteLater()
        self.filter_rows.clear()

        # Remove all groups
        for group_data in self.filter_groups[:]:
            group_data['widget'].setParent(None)
            group_data['widget'].deleteLater()
        self.filter_groups.clear()

        # Add one empty filter
        self.add_filter_row()

    def on_operator_changed(self, operator: str, filter_widget: QFrame):
        """Handle operator change to show/hide value inputs"""
        for filter_data in self.filter_rows:
            if filter_data['widget'] == filter_widget:
                value_widget = filter_data['value_widget']
                value2_widget = filter_data['value2_widget']

                if operator in ['IS NULL', 'IS NOT NULL']:
                    value_widget.hide()
                    value2_widget.hide()
                elif operator == 'BETWEEN':
                    value_widget.show()
                    value2_widget.show()
                else:
                    value_widget.show()
                    value2_widget.hide()
                break

    def apply_date_preset(self, preset: str):
        """Apply a date filter preset"""
        from datetime import datetime, timedelta

        today = datetime.now().strftime('%Y-%m-%d')

        if preset == 'today':
            date_from = today
            date_to = today
        elif preset == 'week':
            date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            date_to = today
        elif preset == 'month':
            date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            date_to = today
        else:
            return

        # Clear and add date filter
        self.clear_all_filters()

        # Find a date field
        date_fields = [f for f in getattr(self, 'available_fields', []) if 'date' in f.lower()]

        if date_fields and self.filter_rows:
            filter_data = self.filter_rows[0]
            filter_data['field_combo'].setCurrentText(date_fields[0])
            filter_data['op_combo'].setCurrentText('BETWEEN')
            filter_data['value_widget'].setText(date_from)
            filter_data['value2_widget'].setText(date_to)
            filter_data['value2_widget'].show()

    def apply_high_importance_filter(self):
        """Apply high importance filter"""
        self.clear_all_filters()

        # Find importance field
        importance_fields = [f for f in getattr(self, 'available_fields', []) if 'importance' in f.lower()]

        if importance_fields and self.filter_rows:
            filter_data = self.filter_rows[0]
            filter_data['field_combo'].setCurrentText(importance_fields[0])
            filter_data['op_combo'].setCurrentText('>=')
            filter_data['value_widget'].setText('0.7')

    def get_filter_clauses(self) -> List[Dict[str, Any]]:
        """Build visual filters with parameterized values.

        Field names and operators come from whitelisted combo-box values;
        user-entered values are always bound parameters rather than interpolated
        into SQL.
        """
        clauses = []
        allowed_fields = set(getattr(self, 'available_fields', [])).intersection(
            self.VISUAL_FIELDS
        )
        allowed_operators = {
            '=', '!=', '>', '<', '>=', '<=', 'LIKE', 'NOT LIKE',
            'IS NULL', 'IS NOT NULL', 'BETWEEN', 'IN', 'NOT IN',
            'CONTAINS', 'STARTS WITH', 'ENDS WITH',
        }
        allowed_logic = {'AND', 'OR'}

        for filter_data in self.filter_rows:
            field = filter_data['field_combo'].currentText()
            operator = filter_data['op_combo'].currentText().upper()
            value = filter_data['value_widget'].text().strip()
            value2 = filter_data['value2_widget'].text().strip()

            if not field or field not in allowed_fields or operator not in allowed_operators:
                continue

            clause = ''
            params = []
            if operator in {'IS NULL', 'IS NOT NULL'}:
                clause = f"{field} {operator}"
            elif operator == 'BETWEEN' and value and value2:
                clause = f"{field} BETWEEN ? AND ?"
                params = [value, value2]
            elif operator in {'IN', 'NOT IN'} and value:
                values = [item.strip() for item in value.split(',') if item.strip()]
                if values:
                    placeholders = ', '.join('?' for _ in values)
                    clause = f"{field} {operator} ({placeholders})"
                    params = values
            elif operator == 'CONTAINS' and value:
                clause = f"{field} LIKE ?"
                params = [f'%{value}%']
            elif operator == 'STARTS WITH' and value:
                clause = f"{field} LIKE ?"
                params = [f'{value}%']
            elif operator == 'ENDS WITH' and value:
                clause = f"{field} LIKE ?"
                params = [f'%{value}']
            elif operator in {'LIKE', 'NOT LIKE'} and value:
                clause = f"{field} {operator} ?"
                params = [f'%{value}%']
            elif value:
                clause = f"{field} {operator} ?"
                params = [value]

            if clause:
                logic = filter_data['logic_combo'].currentText().upper()
                clauses.append({
                    'clause': clause,
                    'params': params,
                    'logic': logic if logic in allowed_logic else 'AND',
                    # Keep the owning group so build_visual_query can honor
                    # the explicit "combine filter groups" control.
                    'group': filter_data.get('group'),
                })

        return clauses

    def select_all_fields(self, select: bool):
        """Select or deselect all fields"""
        for i in range(self.fields_list.count()):
            self.fields_list.item(i).setSelected(select)

    def on_mode_changed(self, button):
        """Handle mode change"""
        mode = self.mode_group.id(button)
        self.stacked.setCurrentIndex(mode)

    def build_visual_query(self) -> str:
        """Build SQL query from visual builder selections"""
        selected_tables = [
            name for name, check in self.table_checks.items()
            if check.isChecked() and name in self.VISUAL_TABLES
        ]

        if not selected_tables:
            self.query_params = []
            return ""

        # Field names are database metadata, not free-form SQL. Keep a second
        # allowlist check here even though the list widget is not editable.
        available_fields = set(getattr(self, 'available_fields', []))
        allowed_fields = available_fields.intersection(self.VISUAL_FIELDS)
        selected_fields = [
            self.fields_list.item(i).text()
            for i in range(self.fields_list.count())
            if self.fields_list.item(i).isSelected()
            and self.fields_list.item(i).text() in allowed_fields
        ]

        if not selected_fields:
            selected_fields = ['*']

        # Build SELECT clause
        fields_str = ', '.join(selected_fields)

        # Build FROM clause with JOINs
        from_clause = selected_tables[0]
        if 'sources' in selected_tables and 'contents' in selected_tables:
            if from_clause == 'sources':
                from_clause += " LEFT JOIN contents ON sources.id = contents.sources_id"
            else:
                from_clause = "contents LEFT JOIN sources ON sources.id = contents.sources_id"

        if 'content_analysis' in selected_tables:
            if 'contents' in selected_tables or 'sources' in selected_tables:
                from_clause += " LEFT JOIN content_analysis ON contents.id = content_analysis.content_id"
            else:
                from_clause = "content_analysis"

        query = f"SELECT {fields_str} FROM {from_clause}"

        # Build WHERE clause from advanced filters. Values are bound below.
        filter_clauses = self.get_filter_clauses()
        self.query_params = []

        if filter_clauses:
            # Parameters are collected in the same order as the final SQL
            # expression below.  This matters when grouped and ungrouped rows
            # are interleaved in the editor.
            where_params = []

            # Flat rows retain their per-row connector.  Rows inside an
            # explicit group are parenthesized and use that group's logic;
            # the global selector then combines each group (and the flat
            # portion) deterministically.  This keeps the visual controls
            # faithful to the generated SQL instead of silently ignoring the
            # group controls.
            grouped = {}
            ungrouped = []
            for clause_data in filter_clauses:
                group = clause_data.get('group')
                if group is None:
                    ungrouped.append(clause_data)
                else:
                    grouped.setdefault(group, []).append(clause_data)

            top_level_parts = []
            if ungrouped:
                flat_expression = ungrouped[0]['clause']
                where_params.extend(ungrouped[0].get('params', []))
                for clause_data, next_clause in zip(ungrouped, ungrouped[1:]):
                    logic = clause_data.get('logic', 'AND')
                    flat_expression += f" {logic} {next_clause['clause']}"
                    where_params.extend(next_clause.get('params', []))
                top_level_parts.append(flat_expression)

            group_logic_by_widget = {
                group_data['widget']: group_data['logic_combo'].currentText().upper()
                for group_data in self.filter_groups
            }
            for group_widget, clauses in grouped.items():
                if not clauses:
                    continue
                logic = group_logic_by_widget.get(group_widget, 'AND')
                if logic not in {'AND', 'OR'}:
                    logic = 'AND'
                group_expression = f"({clauses[0]['clause']}"
                where_params.extend(clauses[0].get('params', []))
                for clause_data in clauses[1:]:
                    group_expression += f" {logic} {clause_data['clause']}"
                    where_params.extend(clause_data.get('params', []))
                group_expression += ")"
                top_level_parts.append(group_expression)

            global_logic = self.global_logic_combo.currentText().upper()
            if global_logic not in {'AND', 'OR'}:
                global_logic = 'AND'
            where_str = f" {global_logic} ".join(top_level_parts)
            self.query_params = where_params
            query += f" WHERE {where_str}"

        # Field/operator values originate from fixed database metadata and
        # combo-box values; validate them again before composing identifiers.
        selected_order_field = self.order_field.currentText()
        allowed_order_fields = set(getattr(self, 'available_fields', [])).intersection(
            self.VISUAL_FIELDS
        )
        if selected_order_field and selected_order_field in allowed_order_fields:
            direction = self.order_direction.currentText().upper()
            if direction not in {'ASC', 'DESC'}:
                direction = 'ASC'
            query += f" ORDER BY {selected_order_field} {direction}"

        if self.limit_check.isChecked():
            # QSpinBox supplies a bounded integer, so this identifier-free
            # clause remains safe and keeps saved visual queries executable
            # when they are loaded in raw SQL mode.
            query += f" LIMIT {int(self.limit_spin.value())}"

        return query

    def get_query(self) -> str:
        """Get the current query (SQL or visual)."""
        if self.mode_group.checkedId() == 0:  # SQL mode
            self.query_params = []
            return self.sql_editor.toPlainText().strip()

        query = self.build_visual_query()
        self.generated_sql.setPlainText(query)
        return query

    def set_query(self, query: str):
        """Set query in SQL mode"""
        self.sql_editor.setPlainText(query)
        self.sql_mode_btn.setChecked(True)
        self.stacked.setCurrentIndex(0)

    def clear_query(self):
        """Clear the query"""
        self.sql_editor.clear()
        self.query_params = []
        # Reset visual builder
        for check in self.table_checks.values():
            check.setChecked(True)
        self.select_all_fields(True)
        # Clear filters using new system
        self.clear_all_filters()

    def execute_query(self):
        """Execute the query"""
        query = self.get_query()

        if not query:
            QMessageBox.warning(self, self.translator.tr('msg_warning'),
                              self.translator.tr('report_empty_query'))
            return

        # Security check - only a single SELECT statement is allowed. Visual
        # queries use bound parameters; raw SQL mode remains intentionally
        # available for advanced users but cannot execute a statement batch.
        query_upper = query.upper().strip()
        if not query_upper.startswith('SELECT') or ';' in query.rstrip().rstrip(';'):
            QMessageBox.warning(self, self.translator.tr('msg_warning'),
                              self.translator.tr('report_only_select'))
            return

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, tuple(getattr(self, 'query_params', [])))

            rows = cursor.fetchall()
            if rows:
                columns = list(rows[0].keys())
                data = [dict(row) for row in rows]
                self.query_executed.emit(data, columns)
            else:
                self.query_executed.emit([], [])
        except Exception as e:
            self.query_failed.emit(str(e))
            QMessageBox.critical(self, self.translator.tr('msg_error'),
                               f"{self.translator.tr('report_query_error')}:\n{str(e)}")
        finally:
            if conn is not None:
                conn.close()


class ReportsTab(QWidget):
    """Frappe-Style Reports Interface with Query Builder, Report Creator, and Chart Designer"""

    def __init__(self, parent, translator: TranslationManager):
        super().__init__(parent)
        self.translator = translator
        self.is_rtl = translator.current_language == 'ar'
        self.current_data = []
        self.current_columns = []
        self.report_config = {}

        # Apply RTL/LTR direction at initialization
        direction = Qt.RightToLeft if self.is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)

        # Reports directory
        self.reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'saved_reports')
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)

        self.setup_fonts()
        self.setup_ui()

    def setup_fonts(self):
        """Load and setup fonts for better printing"""
        fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts')

        if os.path.exists(fonts_dir):
            for font_file in os.listdir(fonts_dir):
                if font_file.endswith(('.ttf', '.otf')):
                    font_path = os.path.join(fonts_dir, font_file)
                    QFontDatabase.addApplicationFont(font_path)

    def setup_ui(self):
        # Main layout (no margins - scroll area handles it)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if self.is_rtl:
            self.setLayoutDirection(Qt.RightToLeft)

        # Create unified scroll area for entire interface
        self.unified_scroll = AppStyles.create_unified_scroll_area()

        # Content widget for scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        # Use 8px grid spacing system
        AppStyles.apply_layout_spacing(scroll_layout, margin_units=1, spacing_units=1)

        # Main toolbar
        self.create_toolbar(scroll_layout)

        # Main content - Splitter
        main_splitter = QSplitter(Qt.Horizontal)

        # Left panel - Query Builder & Chart Designer
        self.left_panel_tabs = QTabWidget()
        self.left_panel_tabs.setMinimumWidth(480)  # Wider to accommodate full text
        # Fix tab text truncation - set elide mode to None so full text is shown
        self.left_panel_tabs.setElideMode(Qt.ElideNone)
        self.left_panel_tabs.setUsesScrollButtons(True)
        # Access tab bar to ensure full text display
        left_tab_bar = self.left_panel_tabs.tabBar()
        left_tab_bar.setElideMode(Qt.ElideNone)
        left_tab_bar.setExpanding(True)  # Allow tabs to expand to show full text
        left_tab_bar.setStyleSheet(AppStyles.get_component_style('report_tab_bar'))

        # Query Builder Tab
        self.query_builder = QueryBuilder(self, self.translator)
        self.query_builder.query_executed.connect(self.on_query_executed)
        self.query_builder.query_failed.connect(self.on_query_failed)
        self.left_panel_tabs.addTab(self.query_builder, self.translator.tr('report_query_builder'))

        # Chart Designer Tab
        self.chart_designer = ChartDesigner(self, self.translator)
        self.left_panel_tabs.addTab(self.chart_designer, self.translator.tr('report_chart_designer'))

        main_splitter.addWidget(self.left_panel_tabs)

        # Right panel - Results & Report
        self.right_panel_tabs = QTabWidget()
        # Fix tab text truncation - set elide mode to None so full text is shown
        self.right_panel_tabs.setElideMode(Qt.ElideNone)
        self.right_panel_tabs.setUsesScrollButtons(True)
        # Access tab bar to ensure full text display
        right_tab_bar = self.right_panel_tabs.tabBar()
        right_tab_bar.setElideMode(Qt.ElideNone)
        right_tab_bar.setExpanding(True)  # Allow tabs to expand to show full text
        right_tab_bar.setStyleSheet(AppStyles.get_component_style('report_tab_bar'))

        # Results Tab
        results_widget = self.create_results_tab()
        self.right_panel_tabs.addTab(results_widget, self.translator.tr('report_results'))

        # Report Preview Tab
        report_widget = self.create_report_tab()
        self.right_panel_tabs.addTab(report_widget, self.translator.tr('report_preview'))

        main_splitter.addWidget(self.right_panel_tabs)
        main_splitter.setSizes([450, 700])

        scroll_layout.addWidget(main_splitter, 1)  # Stretch factor 1 to take available space

        # Status bar
        self.status_label = QLabel(self.translator.tr('msg_ready'))
        scroll_layout.addWidget(self.status_label, 0)  # Fixed height

        # Set scroll content
        self.unified_scroll.setWidget(scroll_content)

        # Add unified scroll to main layout
        layout.addWidget(self.unified_scroll)

    def load_data(self):
        """Load/refresh data - called when tab is activated or language changes"""
        # Update query builder fields
        if hasattr(self, 'query_builder'):
            self.query_builder.load_db_structure()
            self.query_builder.update_visual_fields()

        # Update status
        if hasattr(self, 'status_label'):
            self.status_label.setText(self.translator.tr('msg_ready'))

    def set_data(self, data: List[Dict], columns: Optional[List[str]] = None,
                 title: str = None):
        """Load externally supplied rows into the report workspace.

        The All Data tab uses this to hand its filtered selection to Reports.
        Keeping the operation here avoids faking a SQL query and makes the
        report preview, result table, chart designer, and export actions all
        operate on the same data.
        """
        rows = list(data or [])
        if columns is None:
            columns = list(rows[0].keys()) if rows else []
        self.on_query_executed(rows, list(columns))
        if title:
            self.report_title_edit.setText(title)
        self.right_panel_tabs.setCurrentIndex(1)
        self.update_report_preview()

    def _configure_report_action(self, button: QPushButton, icon_key: str,
                                 label: str, *, style_class: str = None,
                                 icon_only: bool = False):
        """Configure a report action with the same focus and label rules as tables."""
        button.setObjectName('reportToolbarAction')
        button.setProperty('toolbarVariant', style_class or '')
        button.setProperty('iconOnly', bool(icon_only))
        icon = get_icon(icon_key, 18, use_white=bool(style_class))
        if not icon.isNull():
            button.setIcon(icon)
            button.setIconSize(QSize(18, 18))
        if icon_only:
            button.setText('')
            button.setFixedSize(38, 36)
        else:
            button.setText(label)
            # Leave room for the icon, label spacing, and focus border so
            # action names never lose their final character on high-DPI
            # or translated layouts. The toolbar itself can scroll.
            button.setMinimumWidth(max(112, len(label) * 9 + 62))
            button.setFixedHeight(36)
        button.setToolTip(label)
        button.setAccessibleName(label)
        action_width = max(112, len(label) * 9 + 62) if not icon_only else None
        button.setStyleSheet(AppStyles.get_table_toolbar_action_style(
            style_class, icon_only, object_name='reportToolbarAction',
            fixed_width=action_width
        ))
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # Reapply geometry after the compact stylesheet is polished; Qt adds
        # stylesheet padding to minimum dimensions.
        if icon_only:
            button.setFixedSize(40, 38)
        else:
            button.setFixedWidth(max(112, len(label) * 9 + 62))
            button.setFixedHeight(38)
        return button

    def create_toolbar(self, parent_layout):
        """Create grouped report actions in a responsive horizontal scroller."""
        scroll = QScrollArea()
        scroll.setObjectName('reportToolbarScroller')
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        # A two-tier action surface preserves the existing capabilities while
        # making the report workspace hierarchy explicit on narrow windows.
        scroll.setFixedHeight(76)

        content = QWidget()
        content.setObjectName('reportToolbar')
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)
        self.report_toolbar_heading = QLabel(
            self.translator.tr('report_workspace', default='Report workspace')
        )
        self.report_toolbar_heading.setObjectName('reportToolbarHeading')
        content_layout.addWidget(self.report_toolbar_heading)
        action_row = QWidget(content)
        toolbar = QHBoxLayout(action_row)
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(AppStyles.get_spacing(1))
        toolbar.setAlignment(Qt.AlignVCenter)
        content_layout.addWidget(action_row)

        def group_label(text):
            label = QLabel(text)
            label.setObjectName('toolbarGroupLabel')
            label.setStyleSheet(AppStyles.get_component_style('toolbar_label'))
            return label

        toolbar.addWidget(group_label(self.translator.tr('report_management', default='Report')))
        self.btn_new = self._configure_report_action(
            QPushButton(), 'btn_add', self.translator.tr('report_new'), style_class='primary'
        )
        self.btn_new.clicked.connect(self.new_report)
        self.btn_save = self._configure_report_action(
            QPushButton(), 'save', self.translator.tr('report_save')
        )
        self.btn_save.clicked.connect(self.save_report)
        self.btn_load = self._configure_report_action(
            QPushButton(), 'file_text', self.translator.tr('report_load'), icon_only=True
        )
        self.btn_load.clicked.connect(self.load_report)
        toolbar.addWidget(self.btn_new)
        toolbar.addWidget(self.btn_save)
        toolbar.addWidget(self.btn_load)

        toolbar.addWidget(self.create_separator())
        toolbar.addWidget(group_label(self.translator.tr('report_output', default='Output')))

        self.btn_print = self._configure_report_action(
            QPushButton(), 'btn_print', self.translator.tr('btn_print'), icon_only=True
        )
        self.btn_print.clicked.connect(self.print_report)
        self.btn_print_preview = self._configure_report_action(
            QPushButton(), 'btn_print_preview', self.translator.tr('btn_print_preview'), icon_only=True
        )
        self.btn_print_preview.clicked.connect(self.print_preview)
        self.btn_export_pdf = self._configure_report_action(
            QPushButton(), 'btn_export_pdf', self.translator.tr('btn_export_pdf'), icon_only=True
        )
        self.btn_export_pdf.clicked.connect(self.export_pdf)
        self.btn_export_excel = self._configure_report_action(
            QPushButton(), 'btn_export_excel', self.translator.tr('btn_export_excel'), icon_only=True
        )
        self.btn_export_excel.clicked.connect(self.export_excel)
        self.btn_export_csv = self._configure_report_action(
            QPushButton(), 'btn_export_csv', self.translator.tr('btn_export_csv')
        )
        self.btn_export_csv.clicked.connect(self.export_csv)
        for button in (self.btn_print, self.btn_print_preview, self.btn_export_pdf,
                       self.btn_export_excel, self.btn_export_csv):
            toolbar.addWidget(button)

        toolbar.addWidget(self.create_separator())
        toolbar.addWidget(group_label(self.translator.tr('report_page_settings', default='Page')))
        self.orientation_label = QLabel(self.translator.tr('report_orientation') + ':')
        self.orientation_label.setObjectName('toolbarGroupLabel')
        self.orientation_combo = QComboBox()
        self.orientation_combo.setAccessibleName(self.translator.tr('report_orientation'))
        self.orientation_combo.addItems([
            self.translator.tr('report_portrait'),
            self.translator.tr('report_landscape')
        ])
        self.page_size_label = QLabel(self.translator.tr('report_page_size') + ':')
        self.page_size_label.setObjectName('toolbarGroupLabel')
        self.page_size_combo = QComboBox()
        self.page_size_combo.setAccessibleName(self.translator.tr('report_page_size'))
        self.page_size_combo.addItems(['A4', 'Letter', 'A3', 'Legal'])
        toolbar.addWidget(self.orientation_label)
        toolbar.addWidget(self.orientation_combo)
        toolbar.addWidget(self.page_size_label)
        toolbar.addWidget(self.page_size_combo)
        toolbar.addStretch()

        scroll.setWidget(content)
        parent_layout.addWidget(scroll, 0)

    def create_separator(self) -> QFrame:
        """Create vertical separator"""
        sep = QFrame()
        sep.setObjectName('toolbarGroupSeparator')
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Plain)
        sep.setFixedHeight(24)
        return sep

    def create_results_tab(self) -> QWidget:
        """Create results display tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Results info
        self.results_info = QLabel(self.translator.tr('report_no_results'))
        self.results_info.setStyleSheet(AppStyles.get_component_style('report_results_info'))
        layout.addWidget(self.results_info)
        self.results_state_label = QLabel(self.translator.tr(
            'table_empty', default='Run a report query to view results.'
        ))
        self.results_state_label.setObjectName('tableStateLabel')
        self.results_state_label.setAlignment(Qt.AlignCenter)
        self.results_state_label.setWordWrap(True)
        self.results_state_label.setStyleSheet(AppStyles.get_component_style('table_state'))
        self.results_state_label.setVisible(True)
        layout.addWidget(self.results_state_label, 0)

        # Results table with scrollbars and keyboard-friendly row selection.
        self.results_table = QTableWidget()
        self.results_table.setObjectName('reportResultsTable')
        configure_table(self.results_table, multi_select=True)
        self.results_table.setAccessibleName(self.translator.tr(
            'report_results', default='Report results'
        ))
        self.results_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self._show_results_context_menu)
        self.results_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.results_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.results_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.results_table.setStyleSheet(AppStyles.get_component_style('report_results_table'))
        layout.addWidget(self.results_table, 1)

        from widgets.pagination_widget import PaginationWidget
        self.results_pagination = PaginationWidget(self.translator, self)
        self.results_pagination.page_changed.connect(self._render_results_page)
        self.results_pagination.page_size_changed.connect(self._render_results_page)
        layout.addWidget(self.results_pagination, 0)

        # Quick stats
        stats_layout = QHBoxLayout()
        self.stat_total = QLabel(f"{self.translator.tr('report_total')}: 0")
        self.stat_columns = QLabel(f"{self.translator.tr('report_columns')}: 0")
        stats_layout.addWidget(self.stat_total)
        stats_layout.addWidget(self.stat_columns)
        stats_layout.addStretch()

        # Generate chart from results
        self.btn_chart_from_data = self._configure_report_action(
            QPushButton(), 'chart', self.translator.tr('report_create_chart')
        )
        self.btn_chart_from_data.clicked.connect(self.create_chart_from_results)
        self.btn_chart_from_data.setEnabled(False)
        stats_layout.addWidget(self.btn_chart_from_data)

        layout.addLayout(stats_layout)

        return widget

    def create_report_tab(self) -> QWidget:
        """Create report preview tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Report header settings
        header_layout = QHBoxLayout()

        header_layout.addWidget(QLabel(self.translator.tr('report_title') + ":"))
        self.report_title_edit = QLineEdit()
        self.report_title_edit.setPlaceholderText(self.translator.tr('report_title_hint'))
        self.report_title_edit.textChanged.connect(self.update_report_preview)
        header_layout.addWidget(self.report_title_edit)

        self.include_chart_check = QCheckBox(self.translator.tr('report_include_chart'))
        self.include_chart_check.setChecked(True)
        self.include_chart_check.stateChanged.connect(self.update_report_preview)
        header_layout.addWidget(self.include_chart_check)

        self.btn_refresh_report = QPushButton(self.translator.tr('btn_refresh'))
        self.btn_refresh_report.clicked.connect(self.update_report_preview)
        header_layout.addWidget(self.btn_refresh_report)

        layout.addLayout(header_layout)

        # Report preview
        self.report_preview = QTextEdit()
        self.report_preview.setReadOnly(True)
        self.report_preview.setStyleSheet(AppStyles.get_component_style('report_preview_editor'))
        layout.addWidget(self.report_preview)

        return widget

    def _translate_column_name(self, col_name: str) -> str:
        """Translate column name to current language"""
        # Comprehensive map of all database column names to translation keys
        column_translations = {
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

        # Try exact match first
        col_lower = col_name.lower().strip()
        if col_lower in column_translations:
            return self.translator.tr(column_translations[col_lower])

        # Try partial match for common patterns
        for key, tr_key in column_translations.items():
            if key in col_lower or col_lower in key:
                return self.translator.tr(tr_key)

        # Return original if no translation found
        return col_name

    def on_query_failed(self, message: str):
        """Clear stale results and expose a recoverable report-query state."""
        self.current_data = []
        self.current_columns = []
        self.results_table.clear()
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)
        self.results_pagination.current_page = 1
        self.results_pagination.set_total_items(0)
        self.results_state_label.setText(
            f"{self.translator.tr('table_error', default='Unable to load records.')} "
            f"{self.translator.tr('table_recover', default='Run the query again after correcting it.')}"
        )
        self.results_state_label.setVisible(True)
        self.btn_chart_from_data.setEnabled(False)
        if hasattr(self, 'status_label'):
            self.status_label.setText(self.translator.tr(
                'table_error', default='Report query failed.'
            ))

    def on_query_executed(self, data: List[Dict], columns: List[str]):
        """Handle query execution results"""
        self.current_data = data
        self.current_columns = columns
        if hasattr(self, 'btn_chart_from_data'):
            self.btn_chart_from_data.setEnabled(bool(data))
        if hasattr(self, 'results_state_label'):
            self.results_state_label.setText(self.translator.tr(
                'table_empty', default='No records returned by this query.'
            ))
            self.results_state_label.setVisible(not bool(data))

        # Update results table headers; rows are rendered through the reusable
        # paginator so large report outputs stay navigable.
        translated_columns = [self._translate_column_name(col) for col in columns]
        self.results_table.clear()
        all_columns = ['#'] + translated_columns
        self.results_table.setColumnCount(len(all_columns))
        self.results_table.setHorizontalHeaderLabels(all_columns)
        self.results_table.setColumnWidth(0, 50)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.horizontalHeader().setMinimumSectionSize(72)
        self.results_pagination.current_page = 1
        self.results_pagination.set_total_items(len(data))
        self._render_results_page()

        # Update stats
        self.results_info.setText(
            f"{self.translator.tr('report_results')}: {len(data)} "
            f"{self.translator.tr('report_rows')}"
        )
        self.stat_total.setText(f"{self.translator.tr('report_total')}: {len(data)}")
        self.stat_columns.setText(f"{self.translator.tr('report_columns')}: {len(columns)}")

        # Update chart designer with data
        self.chart_designer.set_data(data)

        # Update report preview
        self.update_report_preview()

        self.status_label.setText(f"{self.translator.tr('report_query_success')} - {len(data)} {self.translator.tr('report_rows')}")

    def _render_results_page(self, _page=None):
        """Render only the active report-result page with accurate numbering."""
        if not hasattr(self, 'results_table') or not hasattr(self, 'results_pagination'):
            return
        data = list(getattr(self, 'current_data', []) or [])
        columns = list(getattr(self, 'current_columns', []) or [])
        start, end = self.results_pagination.get_page_range()
        page_data = data[start:end]
        self.results_table.setRowCount(len(page_data))

        for row_idx, row_data in enumerate(page_data):
            row_num_item = set_item_with_tooltip(
                self.results_table, row_idx, 0, str(start + row_idx + 1),
                alignment=Qt.AlignCenter
            )
            row_num_item.setBackground(QColor(AppStyles.get_color('ROW_NUM_BG')))
            row_num_item.setFont(QFont('Segoe UI', 9, QFont.Bold))
            for col_idx, col_name in enumerate(columns):
                raw_value = row_data.get(col_name)
                if raw_value is None:
                    value = '-'
                elif isinstance(raw_value, float):
                    if 0 <= raw_value <= 1 and 'importance' in col_name.lower():
                        value = f"{raw_value * 100:.0f}%"
                    else:
                        value = f"{raw_value:.2f}" if raw_value != int(raw_value) else str(int(raw_value))
                else:
                    value = str(raw_value)
                item = set_item_with_tooltip(self.results_table, row_idx, col_idx + 1, value)
                if raw_value is None:
                    item.setForeground(QColor(AppStyles.get_color('TEXT_MUTED')))
            self.results_table.setRowHeight(row_idx, 38)

        self.results_table.resizeColumnsToContents()
        self.results_table.setColumnWidth(0, 50)
        showing = self.translator.tr('pagination_showing', default='Showing')
        of_text = self.translator.tr('pagination_of', default='of')
        if data:
            self.results_info.setText(
                f"{showing} {start + 1}–{end} {of_text} {len(data)} "
                f"· {self.translator.tr('report_rows')}"
            )
        else:
            self.results_info.setText(self.translator.tr('report_no_results'))

    def _show_results_context_menu(self, position):
        """Offer copy access without adding another permanent toolbar row."""
        item = self.results_table.itemAt(position)
        if item is not None:
            self.results_table.setCurrentItem(item)
        menu = QMenu(self.results_table)
        menu.setObjectName('tableContextMenu')
        copy_action = QAction(
            get_icon('btn_copy', 18),
            self.translator.tr('btn_copy', default='Copy value'), menu
        )
        copy_action.setEnabled(bool(self.results_table.currentItem()))
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(
            self.results_table.currentItem().text() if self.results_table.currentItem() else ''
        ))
        menu.addAction(copy_action)
        menu.exec_(self.results_table.viewport().mapToGlobal(position))

    def create_chart_from_results(self):
        """Switch to chart designer with current data"""
        if self.current_data:
            # Set data to chart designer
            self.chart_designer.set_data(self.current_data)

            # Switch to Chart Designer tab (index 1 in left_panel_tabs)
            self.left_panel_tabs.setCurrentIndex(1)

            # Auto-generate the chart if data is available
            if hasattr(self.chart_designer, 'generate_chart'):
                self.chart_designer.generate_chart()

    def update_report_preview(self):
        """Update the report preview"""
        direction = 'rtl' if self.is_rtl else 'ltr'
        text_align = 'right' if self.is_rtl else 'left'

        title = self.report_title_edit.text() or self.translator.tr('report_default_title')

        html = f"""
        <!DOCTYPE html>
        <html dir="{direction}">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #2C3E50; direction: {direction}; text-align: {text_align}; padding: 20px; }}
                h1 {{ color: #2C3E50; border-bottom: 3px solid #3498DB; padding-bottom: 10px; text-align: center; }}
                .info {{ color: #7F8C8D; font-size: 12px; text-align: center; margin-bottom: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; direction: {direction}; }}
                th, td {{ border: 1px solid #DEE2E6; padding: 10px; text-align: {text_align}; }}
                th {{ background-color: #2C3E50; color: white; }}
                tr:nth-child(even) {{ background-color: #F8F9FA; }}
                .stats {{ background-color: #E8F4FD; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                .chart-placeholder {{ text-align: center; padding: 20px; background: #F8F9FA; border: 1px dashed #DEE2E6; margin: 20px 0; }}
                .footer {{ margin-top: 30px; padding-top: 15px; border-top: 1px solid #DEE2E6; color: #7F8C8D; font-size: 11px; text-align: center; }}
            </style>
        </head>
        <body>
            <h1>{escape(str(title))}</h1>
            <p class="info">{self.translator.tr('report_generated')}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """

        # Stats section
        if self.current_data:
            html += f"""
            <div class="stats">
                <strong>{self.translator.tr('report_summary')}:</strong><br>
                {self.translator.tr('report_total_rows')}: {len(self.current_data)}<br>
                {self.translator.tr('report_columns')}: {len(self.current_columns)}
            </div>
            """

        # Chart section
        if self.include_chart_check.isChecked() and MATPLOTLIB_AVAILABLE:
            chart_bytes = self.chart_designer.get_image_bytes()
            if chart_bytes:
                import base64
                chart_b64 = base64.b64encode(chart_bytes).decode('utf-8')
                html += f'<div style="text-align:center;"><img src="data:image/png;base64,{chart_b64}" style="max-width:100%;"></div>'
            else:
                html += f'<div class="chart-placeholder">{self.translator.tr("report_no_chart")}</div>'

        # Data table (limited rows for preview)
        if self.current_data:
            html += f"<h3>{self.translator.tr('report_data_table')}</h3>"
            html += "<table><tr>"
            for col in self.current_columns:
                html += f"<th>{escape(str(col))}</th>"
            html += "</tr>"

            for row in self.current_data[:50]:  # Limit to 50 rows in preview
                html += "<tr>"
                for col in self.current_columns:
                    raw_value = row.get(col, '')
                    value = '' if raw_value is None else str(raw_value)
                    value = value[:100]  # Truncate long values
                    html += f"<td>{escape(value)}</td>"
                html += "</tr>"

            if len(self.current_data) > 50:
                html += f'<tr><td colspan="{len(self.current_columns)}" style="text-align:center;color:#7F8C8D;">... {self.translator.tr("report_and_more", count=len(self.current_data)-50)}</td></tr>'

            html += "</table>"

        html += f"""
            <div class="footer">
                <p>{self.translator.tr('report_footer')}</p>
            </div>
        </body>
        </html>
        """

        self.report_preview.setHtml(html)

    def new_report(self):
        """Create new report"""
        reply = QMessageBox.question(
            self, self.translator.tr('report_new'),
            self.translator.tr('report_new_confirm'),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.query_builder.clear_query()
            self.current_data = []
            self.current_columns = []
            if hasattr(self, 'btn_chart_from_data'):
                self.btn_chart_from_data.setEnabled(False)
            if hasattr(self, 'results_state_label'):
                self.results_state_label.setText(self.translator.tr(
                    'table_empty', default='Run a report query to view results.'
                ))
                self.results_state_label.setVisible(True)
            self.results_table.clear()
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
            if hasattr(self, 'results_pagination'):
                self.results_pagination.current_page = 1
                self.results_pagination.set_total_items(0)
            self.report_title_edit.clear()
            self.update_report_preview()
            self.status_label.setText(self.translator.tr('report_new_created'))

    def save_report(self):
        """Save current report"""
        dialog = SavedReportDialog(self, self.translator, self.reports_dir, 'save')

        if dialog.exec_() == QDialog.Accepted:
            name = dialog.get_report_name()
            if not name:
                QMessageBox.warning(self, self.translator.tr('msg_warning'),
                                  self.translator.tr('report_name_required'))
                return

            report_data = {
                'name': name,
                'description': dialog.get_report_description(),
                'query': self.query_builder.get_query(),
                'query_params': list(getattr(self.query_builder, 'query_params', [])),
                'title': self.report_title_edit.text(),
                'chart_config': self.chart_designer.get_config(),
                'orientation': self.orientation_combo.currentIndex(),
                'page_size': self.page_size_combo.currentText(),
                'include_chart': self.include_chart_check.isChecked(),
                'created': datetime.now().isoformat(),
            }

            safe_name = ''.join(
                char if (char.isalnum() or char in {' ', '-', '_'}) else '_'
                for char in name
            ).strip().replace(' ', '_')[:120] or 'report'
            filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            filepath = os.path.join(self.reports_dir, filename)

            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)

                self.status_label.setText(f"{self.translator.tr('report_saved')}: {name}")
                QMessageBox.information(self, self.translator.tr('msg_success'),
                                       self.translator.tr('report_save_success'))
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))

    def load_report(self):
        """Load saved report"""
        dialog = SavedReportDialog(self, self.translator, self.reports_dir, 'load')

        if dialog.exec_() == QDialog.Accepted and dialog.selected_report:
            try:
                with open(dialog.selected_report, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)

                # Apply report settings. Visual-builder placeholders are kept
                # as data so loading a saved report never reintroduces value
                # interpolation into SQL.
                self.query_builder.set_query(report_data.get('query', ''))
                saved_params = report_data.get('query_params', [])
                if isinstance(saved_params, list) and len(saved_params) <= 1000:
                    self.query_builder.query_params = saved_params
                self.report_title_edit.setText(report_data.get('title', ''))
                self.orientation_combo.setCurrentIndex(report_data.get('orientation', 0))

                page_size = report_data.get('page_size', 'A4')
                idx = self.page_size_combo.findText(page_size)
                if idx >= 0:
                    self.page_size_combo.setCurrentIndex(idx)

                self.include_chart_check.setChecked(report_data.get('include_chart', True))

                # Apply chart config
                chart_config = report_data.get('chart_config', {})
                if chart_config:
                    self.chart_designer.set_config(chart_config)

                # Execute query
                self.query_builder.execute_query()

                self.status_label.setText(f"{self.translator.tr('report_loaded')}: {report_data.get('name', '')}")

            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))

    def get_printer_with_settings(self) -> QPrinter:
        """Get printer with current settings"""
        printer = QPrinter(QPrinter.HighResolution)

        if self.orientation_combo.currentIndex() == 1:
            printer.setPageOrientation(QPageLayout.Landscape)
        else:
            printer.setPageOrientation(QPageLayout.Portrait)

        page_size_map = {'A4': QPageSize.A4, 'Letter': QPageSize.Letter, 'A3': QPageSize.A3, 'Legal': QPageSize.Legal}
        page_size = page_size_map.get(self.page_size_combo.currentText(), QPageSize.A4)
        printer.setPageSize(QPageSize(page_size))

        printer.setPageMargins(15, 15, 15, 15, QPrinter.Millimeter)

        return printer

    def print_report(self):
        """Print the report with professional header and column configuration"""
        if not self.current_data:
            QMessageBox.warning(self, self.translator.tr('msg_warning'),
                              self.translator.tr('report_no_data'))
            return

        # Show column selection dialog
        dialog = ExportColumnDialog(self, self.translator, self.current_columns)
        if dialog.exec_() != QDialog.Accepted:
            return

        selected_cols = dialog.get_selected_columns()
        col_widths = dialog.get_column_widths()

        # Get global print settings
        settings = get_print_settings()

        # Generate HTML with professional header
        title = self.report_title_edit.text() if hasattr(self, 'report_title_edit') else ""
        html = generate_print_html(self.current_data, selected_cols, col_widths, title, self.translator)

        # Setup printer
        printer = self.get_printer_with_settings()
        if settings.page_orientation == 'Landscape':
            printer.setOrientation(QPrinter.Landscape)

        # Print
        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec_() == QPrintDialog.Accepted:
            doc = QTextDocument()
            doc.setHtml(html)
            print_document_with_page_numbers(doc, printer, settings)
            QMessageBox.information(self, self.translator.tr('msg_success'),
                                   self.translator.tr('report_print_success'))

    def print_preview(self):
        """Show print preview with professional header"""
        if not self.current_data:
            QMessageBox.warning(self, self.translator.tr('msg_warning'),
                              self.translator.tr('report_no_data'))
            return

        # Show column selection dialog
        dialog = ExportColumnDialog(self, self.translator, self.current_columns)
        if dialog.exec_() != QDialog.Accepted:
            return

        selected_cols = dialog.get_selected_columns()
        col_widths = dialog.get_column_widths()

        # Get global print settings
        settings = get_print_settings()

        # Generate HTML
        title = self.report_title_edit.text() if hasattr(self, 'report_title_edit') else ""
        html = generate_print_html(self.current_data, selected_cols, col_widths, title, self.translator)

        # Setup printer
        printer = self.get_printer_with_settings()
        if settings.page_orientation == 'Landscape':
            printer.setOrientation(QPrinter.Landscape)

        # Create document
        doc = QTextDocument()
        doc.setHtml(html)

        # Show preview
        preview = QPrintPreviewDialog(printer, self)
        preview.setWindowTitle(self.translator.tr('btn_print_preview'))
        preview.paintRequested.connect(lambda p: print_document_with_page_numbers(doc, p, settings))
        preview.exec_()

    def _export_unified(self, default_format: str = ExportPreviewDialog.FORMAT_EXCEL):
        """Unified export method using ExportPreviewDialog"""
        try:
            if not self.current_data:
                QMessageBox.warning(self, self.translator.tr('msg_warning'),
                                  self.translator.tr('report_no_data'))
                return

            # Convert current_columns (list of strings) to format expected by ExportPreviewDialog (list of tuples)
            # If no columns specified, extract from data
            if not self.current_columns and self.current_data:
                # Extract column names from first data row
                first_row = self.current_data[0]
                columns = [(key, key) for key in first_row.keys()]
            else:
                columns = [(col, col) for col in self.current_columns]

            # Create export dialog
            dialog = ExportPreviewDialog(
                parent=self,
                data=self.current_data,
                columns=columns,
                translator=self.translator,
                table_name="report",
                default_format=default_format
            )

            if dialog.exec_() == QDialog.Accepted:
                settings = dialog.get_export_settings()
                self._execute_export(settings)
        except Exception as e:
            logger.error(f"Error in export_unified: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                self.translator.tr('msg_error'),
                f"{self.translator.tr('msg_error')}: {str(e)}"
            )

    def _execute_export(self, settings: Dict):
        """Execute the export based on settings from ExportPreviewDialog"""
        export_format = settings.get('format')
        filepath = settings.get('path')
        selected_columns = settings.get('columns')  # List of (key, header) tuples
        column_widths = settings.get('column_widths', {})
        data = settings.get('data')
        open_after = settings.get('open_after', False)
        include_header = settings.get('include_header', False)

        if not filepath or not selected_columns:
            return

        # Extract column keys from tuples
        selected_col_keys = [col[0] for col in selected_columns]

        # Get print settings for header information
        print_settings = get_print_settings() if include_header else None

        try:
            success = False
            if export_format == ExportPreviewDialog.FORMAT_EXCEL:
                from openpyxl import Workbook
                from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
                from openpyxl.utils import get_column_letter

                wb = Workbook()
                ws = wb.active
                ws.title = self.translator.tr('report_data_sheet')

                if self.is_rtl:
                    ws.sheet_view.rightToLeft = True

                # Styles
                header_font = Font(bold=True, color='FFFFFF')
                header_fill = PatternFill(start_color='2C3E50', end_color='2C3E50', fill_type='solid')
                title_font = Font(bold=True, size=14, color='2C3E50')
                subtitle_font = Font(bold=True, size=11, color='7F8C8D')
                border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )

                start_row = 1

                # Add document header if enabled
                if include_header and print_settings:
                    total_cols = len(selected_columns) + 1  # +1 for row number column

                    # Organization name (Line 1)
                    if print_settings.header_left_line1:
                        cell = ws.cell(row=start_row, column=1, value=print_settings.header_left_line1)
                        cell.font = title_font
                        ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row, end_column=total_cols)
                        cell.alignment = Alignment(horizontal='center')
                        start_row += 1

                    # Department (Line 2)
                    if print_settings.header_left_line2:
                        cell = ws.cell(row=start_row, column=1, value=print_settings.header_left_line2)
                        cell.font = subtitle_font
                        ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row, end_column=total_cols)
                        cell.alignment = Alignment(horizontal='center')
                        start_row += 1

                    # Document number and date
                    from datetime import datetime
                    doc_info = []
                    if print_settings.header_right_auto_number or print_settings.header_right_number:
                        doc_num = print_settings.generate_doc_number()
                        doc_info.append(f"{self.translator.tr('print_doc_number')}: {doc_num}")
                    if print_settings.header_right_show_date:
                        doc_info.append(f"{self.translator.tr('lbl_date')}: {print_settings.get_formatted_date()}")

                    if doc_info:
                        cell = ws.cell(row=start_row, column=1, value=" | ".join(doc_info))
                        cell.font = Font(size=10, color='7F8C8D')
                        ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row, end_column=total_cols)
                        cell.alignment = Alignment(horizontal='center')
                        start_row += 1

                    # Empty row before data
                    start_row += 1

                # Add row number header
                cell = ws.cell(row=start_row, column=1, value='#')
                cell.font = header_font
                cell.fill = header_fill
                cell.border = border
                cell.alignment = Alignment(horizontal='center')
                ws.column_dimensions['A'].width = 8

                # Header row with selected columns
                for col_idx, (col_key, col_header) in enumerate(selected_columns, 2):
                    cell = ws.cell(row=start_row, column=col_idx, value=col_header)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.border = border

                    # Set column width based on configuration
                    if col_key in column_widths:
                        ws.column_dimensions[get_column_letter(col_idx)].width = column_widths[col_key] * 0.8

                # Data rows
                data_start_row = start_row + 1
                for row_idx, row_data in enumerate(data, data_start_row):
                    # Row number
                    cell = ws.cell(row=row_idx, column=1, value=row_idx - data_start_row + 1)
                    cell.border = border
                    cell.alignment = Alignment(horizontal='center')

                    for col_idx, (col_key, _) in enumerate(selected_columns, 2):
                        value = row_data.get(col_key)
                        if value is None:
                            value = '-'
                        cell = ws.cell(
                            row=row_idx,
                            column=col_idx,
                            value=sanitize_spreadsheet_value(value)
                        )
                        cell.border = border

                # Auto-size columns without specified width
                for col_idx, (col_key, _) in enumerate(selected_columns, 2):
                    if col_key not in column_widths:
                        max_length = len(str(selected_columns[col_idx - 2][1]))
                        for row in range(data_start_row, len(data) + data_start_row):
                            cell_value = ws.cell(row=row, column=col_idx).value
                            if cell_value:
                                max_length = max(max_length, min(len(str(cell_value)), 50))
                        ws.column_dimensions[get_column_letter(col_idx)].width = max_length + 2

                wb.save(filepath)
                success = True

            elif export_format == ExportPreviewDialog.FORMAT_CSV:
                import csv
                from datetime import datetime

                with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)

                    # Add document header if enabled
                    if include_header and print_settings:
                        if print_settings.header_left_line1:
                            writer.writerow([sanitize_spreadsheet_value(print_settings.header_left_line1)])
                        if print_settings.header_left_line2:
                            writer.writerow([sanitize_spreadsheet_value(print_settings.header_left_line2)])

                        # Document number and date
                        doc_info = []
                        if print_settings.header_right_auto_number or print_settings.header_right_number:
                            doc_num = print_settings.generate_doc_number()
                            doc_info.append(f"{self.translator.tr('print_doc_number')}: {doc_num}")
                        if print_settings.header_right_show_date:
                            doc_info.append(f"{self.translator.tr('lbl_date')}: {print_settings.get_formatted_date()}")

                        if doc_info:
                            writer.writerow([sanitize_spreadsheet_value(" | ".join(doc_info))])

                        # Empty row before data
                        writer.writerow([])

                    # Add row number column
                    headers = ['#'] + [col[1] for col in selected_columns]
                    writer.writerow([sanitize_spreadsheet_value(value) for value in headers])

                    for idx, row_data in enumerate(data, 1):
                        row = [idx]
                        for col_key, _ in selected_columns:
                            value = row_data.get(col_key)
                            row.append(sanitize_spreadsheet_value('-' if value is None else value))
                        writer.writerow(row)
                success = True

            elif export_format == ExportPreviewDialog.FORMAT_WORD:
                from utils.word_export import export_to_word
                success = export_to_word(
                    data,
                    selected_columns,
                    filepath,
                    self.translator,
                    "report",
                    include_all_fields=False,
                    selected_columns=selected_columns,
                    column_widths=column_widths
                )

            elif export_format == ExportPreviewDialog.FORMAT_PDF:
                # Filter data to only include selected columns
                export_data = []
                for row in data:
                    export_row = {}
                    for col_key, _ in selected_columns:
                        export_row[col_key] = row.get(col_key)
                    export_data.append(export_row)

                # Get global print settings
                settings_obj = get_print_settings()

                # Generate HTML
                title = self.report_title_edit.text() if hasattr(self, 'report_title_edit') else ""
                html = generate_print_html(export_data, selected_col_keys, column_widths, title, self.translator)

                # Setup printer
                printer = self.get_printer_with_settings()
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(filepath)
                printer.setOrientation(QPrinter.Landscape)

                # Configure for Arabic if needed
                is_rtl = self.translator.current_language == 'ar'

                # Print to PDF
                doc = QTextDocument()

                # Set default font for Arabic
                if is_rtl:
                    from PyQt5.QtGui import QFont
                    from styles.styles import AppStyles
                    arabic_font = AppStyles.get_arabic_font(10)
                    doc.setDefaultFont(arabic_font)

                doc.setHtml(html)
                print_document_with_page_numbers(doc, printer, settings_obj)
                success = os.path.isfile(filepath) and os.path.getsize(filepath) > 0
            else:
                raise ValueError(f"Unsupported export format: {export_format}")

            if not success or not os.path.isfile(filepath) or os.path.getsize(filepath) == 0:
                raise IOError(f"Export did not create a valid output file: {filepath}")

            # Show success message
            QMessageBox.information(
                self,
                self.translator.tr('msg_success'),
                f"{self.translator.tr('report_export_success')}\n{filepath}"
            )

            # Open file if requested
            if open_after:
                ExportPreviewDialog.open_file(filepath)

        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))

    def export_pdf(self):
        """Export report to PDF - uses unified export dialog"""
        self._export_unified(default_format=ExportPreviewDialog.FORMAT_PDF)

    def export_excel(self):
        """Export data to Excel - uses unified export dialog"""
        self._export_unified(default_format=ExportPreviewDialog.FORMAT_EXCEL)

    def export_csv(self):
        """Export data to CSV - uses unified export dialog"""
        self._export_unified(default_format=ExportPreviewDialog.FORMAT_CSV)

    def refresh_columns(self):
        """Refresh for language change - alias for refresh_translations"""
        self.refresh_translations()

    def refresh_translations(self):
        """Comprehensive refresh of all UI elements when language changes"""
        self.is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if self.is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)

        # Update AppStyles global direction
        from styles.styles import AppStyles
        AppStyles.set_layout_direction('rtl' if self.is_rtl else 'ltr')

        # Apply direction to all child widgets
        for child in self.findChildren(QWidget):
            child.setLayoutDirection(direction)

        # Refresh toolbar buttons
        if hasattr(self, 'btn_new'):
            self.btn_new.setText(self.translator.tr('report_new'))
        if hasattr(self, 'btn_save'):
            self.btn_save.setText(self.translator.tr('report_save'))
        if hasattr(self, 'btn_load'):
            self.btn_load.setText(self.translator.tr('report_load'))
        if hasattr(self, 'btn_export_csv'):
            self.btn_export_csv.setText(self.translator.tr('btn_export_csv'))

        # Refresh report toolbar actions without discarding their hierarchy.
        if hasattr(self, 'btn_new'):
            self._configure_report_action(
                self.btn_new, 'btn_add', self.translator.tr('report_new'), style_class='primary'
            )
        if hasattr(self, 'btn_save'):
            self._configure_report_action(self.btn_save, 'save', self.translator.tr('report_save'))
        if hasattr(self, 'btn_load'):
            self._configure_report_action(
                self.btn_load, 'file_text', self.translator.tr('report_load'), icon_only=True
            )
        if hasattr(self, 'btn_print'):
            self._configure_report_action(
                self.btn_print, 'btn_print', self.translator.tr('btn_print'), icon_only=True
            )
        if hasattr(self, 'btn_print_preview'):
            self._configure_report_action(
                self.btn_print_preview, 'btn_print_preview', self.translator.tr('btn_print_preview'), icon_only=True
            )
        if hasattr(self, 'btn_export_pdf'):
            self._configure_report_action(
                self.btn_export_pdf, 'btn_export_pdf', self.translator.tr('btn_export_pdf'), icon_only=True
            )
        if hasattr(self, 'btn_export_excel'):
            self._configure_report_action(
                self.btn_export_excel, 'btn_export_excel', self.translator.tr('btn_export_excel'), icon_only=True
            )
        if hasattr(self, 'btn_export_csv'):
            self._configure_report_action(
                self.btn_export_csv, 'btn_export_csv', self.translator.tr('btn_export_csv')
            )

        # Refresh status label
        if hasattr(self, 'status_label'):
            self.status_label.setText(self.translator.tr('msg_ready'))

        # Refresh results info
        if hasattr(self, 'results_info'):
            if self.current_data:
                self.results_info.setText(f"{self.translator.tr('report_results')}: {len(self.current_data)} {self.translator.tr('report_rows')}")
            else:
                self.results_info.setText(self.translator.tr('report_no_results'))
        if hasattr(self, 'results_state_label'):
            self.results_state_label.setStyleSheet(AppStyles.get_component_style('table_state'))
            self.results_state_label.setText(self.translator.tr(
                'table_empty', default='Run a report query to view results.'
            ))

        if hasattr(self, 'results_pagination'):
            self.results_pagination.refresh_translations()
            self._render_results_page()

        # Refresh stats labels
        if hasattr(self, 'stat_total'):
            self.stat_total.setText(f"{self.translator.tr('report_total')}: {len(self.current_data) if self.current_data else 0}")
        if hasattr(self, 'stat_columns'):
            self.stat_columns.setText(f"{self.translator.tr('report_columns')}: {len(self.current_columns) if self.current_columns else 0}")

        # Refresh chart from data button
        if hasattr(self, 'btn_chart_from_data'):
            self.btn_chart_from_data.setText(self.translator.tr('report_create_chart'))

        # Refresh report preview elements
        if hasattr(self, 'include_chart_check'):
            self.include_chart_check.setText(self.translator.tr('report_include_chart'))
        if hasattr(self, 'btn_refresh_report'):
            self.btn_refresh_report.setText(self.translator.tr('btn_refresh'))
        if hasattr(self, 'report_title_edit'):
            self.report_title_edit.setPlaceholderText(self.translator.tr('report_title_hint'))

        # Refresh orientation and page size combo labels
        if hasattr(self, 'orientation_label'):
            self.orientation_label.setText(self.translator.tr('report_orientation') + ':')
        if hasattr(self, 'page_size_label'):
            self.page_size_label.setText(self.translator.tr('report_page_size') + ':')
        if hasattr(self, 'orientation_combo'):
            current_idx = self.orientation_combo.currentIndex()
            self.orientation_combo.clear()
            self.orientation_combo.addItems([
                self.translator.tr('report_portrait'),
                self.translator.tr('report_landscape')
            ])
            self.orientation_combo.setCurrentIndex(current_idx)

        # Refresh left panel tab titles (Query Builder, Chart Designer)
        if hasattr(self, 'left_panel_tabs'):
            self.left_panel_tabs.setTabText(0, self.translator.tr('report_query_builder'))
            self.left_panel_tabs.setTabText(1, self.translator.tr('report_chart_designer'))

        # Refresh right panel tab titles (Results, Report Preview)
        if hasattr(self, 'right_panel_tabs'):
            self.right_panel_tabs.setTabText(0, self.translator.tr('report_results'))
            self.right_panel_tabs.setTabText(1, self.translator.tr('report_preview'))

        # Refresh query builder if exists
        if hasattr(self, 'query_builder'):
            self.refresh_query_builder_translations()

        # Refresh chart designer if exists
        if hasattr(self, 'chart_designer'):
            self.refresh_chart_designer_translations()

        # Update report preview
        self.update_report_preview()

    def refresh_query_builder_translations(self):
        """Refresh query builder translations"""
        qb = self.query_builder

        # Mode buttons
        if hasattr(qb, 'sql_mode_btn'):
            qb.sql_mode_btn.setText(self.translator.tr('report_sql_mode'))
        if hasattr(qb, 'visual_mode_btn'):
            qb.visual_mode_btn.setText(self.translator.tr('report_visual_mode'))

        # Execute button
        if hasattr(qb, 'btn_execute'):
            qb.btn_execute.setText(self.translator.tr('report_execute'))
        if hasattr(qb, 'btn_clear'):
            qb.btn_clear.setText(self.translator.tr('btn_clear'))

        # Visual mode buttons
        if hasattr(qb, 'btn_select_all'):
            qb.btn_select_all.setText(self.translator.tr('btn_select_all'))
        if hasattr(qb, 'btn_deselect_all'):
            qb.btn_deselect_all.setText(self.translator.tr('btn_deselect_all'))
        if hasattr(qb, 'btn_add_filter'):
            qb.btn_add_filter.setText(self.translator.tr('report_add_filter'))
            qb.btn_add_filter.setIcon(get_icon('add', 16))
        if hasattr(qb, 'btn_clear_filters'):
            qb.btn_clear_filters.setText(self.translator.tr('btn_clear'))
        if hasattr(qb, 'btn_add_filter_group'):
            qb.btn_add_filter_group.setText(self.translator.tr('report_add_group'))
            qb.btn_add_filter_group.setIcon(get_icon('add', 16))

        # Quick filter buttons
        if hasattr(qb, 'btn_preset_today'):
            qb.btn_preset_today.setText(self.translator.tr('report_filter_today'))
        if hasattr(qb, 'btn_preset_week'):
            qb.btn_preset_week.setText(self.translator.tr('report_filter_week'))
        if hasattr(qb, 'btn_preset_month'):
            qb.btn_preset_month.setText(self.translator.tr('report_filter_month'))
        if hasattr(qb, 'btn_preset_high_importance'):
            qb.btn_preset_high_importance.setText(self.translator.tr('report_filter_high_importance'))

        # Limit checkbox
        if hasattr(qb, 'limit_check'):
            qb.limit_check.setText(self.translator.tr('report_limit_results'))

        # Refresh group boxes in visual mode
        if hasattr(qb, 'table_group'):
            qb.table_group.setTitle(self.translator.tr('report_select_tables'))
        if hasattr(qb, 'fields_group'):
            qb.fields_group.setTitle(self.translator.tr('report_select_fields'))
        if hasattr(qb, 'filter_group'):
            qb.filter_group.setTitle(self.translator.tr('report_filters'))
        if hasattr(qb, 'order_group'):
            qb.order_group.setTitle(self.translator.tr('report_ordering'))

        # Refresh labels
        if hasattr(qb, 'combine_filters_label'):
            qb.combine_filters_label.setText(self.translator.tr('report_combine_filters') + ":")
        if hasattr(qb, 'quick_filters_label'):
            qb.quick_filters_label.setText(self.translator.tr('report_quick_filters') + ":")
        if hasattr(qb, 'order_by_label'):
            qb.order_by_label.setText(self.translator.tr('report_order_by') + ":")

        # Refresh SQL mode template buttons and groups (these are on query_builder)
        if hasattr(qb, 'templates_group'):
            qb.templates_group.setTitle(self.translator.tr('report_query_templates'))

        if hasattr(qb, 'structure_group'):
            qb.structure_group.setTitle(self.translator.tr('report_db_structure'))

        # Refresh structure tree headers
        if hasattr(qb, 'structure_tree'):
            qb.structure_tree.setHeaderLabels([
                self.translator.tr('report_table_column'),
                self.translator.tr('lbl_type')
            ])

        # Refresh template buttons
        if hasattr(qb, 'template_buttons') and hasattr(qb, 'template_definitions'):
            for i, btn in enumerate(qb.template_buttons):
                if i < len(qb.template_definitions):
                    tr_key, _ = qb.template_definitions[i]
                    translated_text = self.translator.tr(tr_key)
                    btn.setText(translated_text)
                    btn.setToolTip(translated_text)

    def refresh_chart_designer_translations(self):
        """Refresh chart designer translations"""
        cd = self.chart_designer

        # Collapsible section headers
        for header_attr, content_attr, title_key in (
            ('type_header', 'type_content', 'report_chart_type'),
            ('title_header', 'title_content', 'lbl_title'),
            ('data_header', 'data_content', 'report_data_config'),
            ('style_header', 'style_content', 'report_chart_style'),
            ('limit_header', 'limit_content', 'report_limit'),
        ):
            if hasattr(cd, header_attr) and hasattr(cd, content_attr):
                header = getattr(cd, header_attr)
                expanded = getattr(cd, content_attr).isVisible()
                header.setText(self.translator.tr(title_key))
                header.setIcon(get_icon('chevron_down' if expanded else 'chevron_right', 18))
                header.setIconSize(QSize(18, 18))

        # View mode buttons
        if hasattr(cd, 'btn_chart_view'):
            cd.btn_chart_view.setText(self.translator.tr('report_chart_view'))
            cd.btn_chart_view.setIcon(get_icon('chart', 18))
        if hasattr(cd, 'btn_table_view'):
            cd.btn_table_view.setText(self.translator.tr('report_table_view'))
            cd.btn_table_view.setIcon(get_icon('table', 18))

        # Chart type label
        if hasattr(cd, 'chart_type_label'):
            cd.chart_type_label.setText(self.translator.tr('report_chart_type') + ":")

        # Chart type dropdown
        if hasattr(cd, 'chart_types') and hasattr(cd, 'chart_types_data'):
            current_idx = cd.chart_types.currentIndex()
            cd.chart_types.blockSignals(True)
            cd.chart_types.clear()

            # Repopulate with translated labels and graphical icons.
            icon_names = ['pie_chart', 'statistics', 'line_chart', 'statistics', 'area_chart', 'donut_chart']
            chart_types_tr = [
                'report_pie_chart', 'report_bar_chart', 'report_line_chart',
                'report_horizontal_bar', 'report_area_chart', 'report_donut_chart'
            ]
            for i, tr_key in enumerate(chart_types_tr):
                cd.chart_types.addItem(
                    get_icon(icon_names[i], 18),
                    self.translator.tr(tr_key),
                    i
                )

            cd.chart_types.setCurrentIndex(current_idx)
            cd.chart_types.blockSignals(False)

        # Title placeholder
        if hasattr(cd, 'chart_title'):
            cd.chart_title.setPlaceholderText(self.translator.tr('report_chart_title_hint'))

        # Data config labels
        if hasattr(cd, 'label_field_label'):
            cd.label_field_label.setText(self.translator.tr('report_label_field') + ":")
        if hasattr(cd, 'value_field_label'):
            cd.value_field_label.setText(self.translator.tr('report_value_field') + ":")
        if hasattr(cd, 'aggregation_label'):
            cd.aggregation_label.setText(self.translator.tr('report_aggregation') + ":")

        # Aggregation combo
        if hasattr(cd, 'aggregation'):
            current_idx = cd.aggregation.currentIndex()
            cd.aggregation.clear()
            cd.aggregation.addItems([
                self.translator.tr('report_count'),
                self.translator.tr('report_sum'),
                self.translator.tr('report_average'),
                self.translator.tr('report_max'),
                self.translator.tr('report_min')
            ])
            cd.aggregation.setCurrentIndex(current_idx)

        # Checkboxes
        if hasattr(cd, 'show_legend'):
            cd.show_legend.setText(self.translator.tr('report_show_legend'))
        if hasattr(cd, 'show_values'):
            cd.show_values.setText(self.translator.tr('report_show_values'))
        if hasattr(cd, 'show_grid'):
            cd.show_grid.setText(self.translator.tr('report_show_grid'))
        if hasattr(cd, 'limit_check'):
            cd.limit_check.setText(self.translator.tr('report_limit_results'))

        # Color scheme label
        if hasattr(cd, 'color_scheme_label'):
            cd.color_scheme_label.setText(self.translator.tr('report_color_scheme') + ":")

        # Color scheme dropdown
        if hasattr(cd, 'color_scheme'):
            current_idx = cd.color_scheme.currentIndex()
            cd.color_scheme.clear()
            cd.color_scheme.addItems([
                self.translator.tr('color_scheme_default'),
                self.translator.tr('color_scheme_pastel'),
                self.translator.tr('color_scheme_dark'),
                self.translator.tr('color_scheme_vibrant'),
                self.translator.tr('color_scheme_monochrome')
            ])
            cd.color_scheme.setCurrentIndex(current_idx)

        # Generate button
        if hasattr(cd, 'btn_generate'):
            cd.btn_generate.setText(self.translator.tr('report_generate_chart'))

        # Preview label
        if hasattr(cd, 'preview_label'):
            cd.preview_label.setText(self.translator.tr('report_chart_preview'))
