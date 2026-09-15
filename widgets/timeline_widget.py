"""
Timeline Widget - Professional Design with Charts, Graphs, and Analysis
Complete redesign with statistics dashboard, visualizations, and clear interface
Scientifically-sound UX principles: 8px grid, density modes, WCAG AA compliance
"""
import sys
from html import escape
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict, Counter
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QPushButton, QComboBox, QDateEdit, QGroupBox, QGridLayout, QSizePolicy,
    QButtonGroup, QSplitter, QMessageBox, QLineEdit
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QSize, QRect, QPoint, QTimer
from PyQt5.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QPalette, QLinearGradient,
    QRadialGradient, QFontMetrics
)
from styles.styles import AppStyles
from translations.translations import TranslationManager
from config.config_manager import ConfigManager
from utils.logger import get_logger
from widgets.pagination_widget import PaginationWidget
from icons.icon_manager import setup_icon_button, get_icon

# Try to import matplotlib for charts
try:
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

logger = get_logger(__name__)


class TimelineDesignSystem:
    """
    Design system for timeline widget following scientific UX principles:
    - 8-pixel grid spacing
    - WCAG 2.1 AA compliance (4.5:1 contrast ratio)
    - Three density modes (Compact, Comfortable, Expansive)
    - F-pattern reading layout
    - Gestalt principles (proximity, similarity, continuity)
    """
    
    # 8-pixel grid system
    GRID_UNIT = 8
    
    # Density mode configurations
    DENSITY_MODES = {
        'compact': {
            'card_padding': 8,      # 1x grid
            'card_spacing': 16,     # 2x grid
            'section_margin': 16,    # 2x grid
            'font_date': 18,         # Event date
            'font_title': 14,        # Event title
            'font_desc': 10,         # Event description
            'font_meta': 9,          # Metadata/tags
            'font_stats_value': 20,  # Statistics value
            'font_stats_label': 10,  # Statistics label
            'card_min_height': 120,
        },
        'comfortable': {
            'card_padding': 16,      # 2x grid
            'card_spacing': 24,      # 3x grid
            'section_margin': 24,     # 3x grid
            'font_date': 20,         # Event date
            'font_title': 16,         # Event title
            'font_desc': 12,         # Event description
            'font_meta': 10,          # Metadata/tags
            'font_stats_value': 24,   # Statistics value
            'font_stats_label': 12,   # Statistics label
            'card_min_height': 160,
        },
        'expansive': {
            'card_padding': 24,      # 3x grid
            'card_spacing': 32,       # 4x grid
            'section_margin': 32,     # 4x grid
            'font_date': 24,          # Event date
            'font_title': 18,         # Event title
            'font_desc': 14,          # Event description
            'font_meta': 12,          # Metadata/tags
            'font_stats_value': 28,   # Statistics value
            'font_stats_label': 14,   # Statistics label
            'card_min_height': 200,
        }
    }
    
    @classmethod
    def get_density_config(cls, mode: str) -> Dict:
        """Get configuration for a density mode"""
        return cls.DENSITY_MODES.get(mode, cls.DENSITY_MODES['comfortable'])
    
    @classmethod
    def get_color_with_contrast(cls, base_color: str, is_text: bool = True) -> str:
        """
        Get color ensuring WCAG AA compliance (4.5:1 for text, 3:1 for UI)
        Uses AppStyles colors which are already WCAG compliant
        """
        colors = AppStyles.get_colors()
        # Map common colors to AppStyles palette
        color_map = {
            '#3498DB': colors.get('ACCENT', '#3498DB'),
            '#27AE60': colors.get('SUCCESS', '#27AE60'),
            '#E74C3C': colors.get('DANGER', '#E74C3C'),
            '#9B59B6': colors.get('PURPLE', '#9B59B6'),
            '#2C3E50': colors.get('TEXT_PRIMARY', '#2C3E50'),
            '#7F8C8D': colors.get('TEXT_SECONDARY', '#7F8C8D'),
        }
        return color_map.get(base_color, base_color)
    
    @classmethod
    def get_spacing(cls, units: int) -> int:
        """Get spacing value in pixels (multiples of 8px)"""
        return cls.GRID_UNIT * units


class StatisticsCard(QFrame):
    """
    Individual statistics card widget
    Enhanced with 8px grid spacing, WCAG AA compliance, and density mode support
    """
    
    def __init__(self, title: str, value: str, icon: str = "", color: str = "#3498DB", 
                 density_mode: str = 'comfortable', parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.icon = icon
        self.color = color
        self.density_mode = density_mode
        self.setObjectName('timelineStatisticsCard')
        self.setup_ui()
    
    def setup_ui(self):
        """Setup statistics card UI with design system"""
        config = TimelineDesignSystem.get_density_config(self.density_mode)
        colors = AppStyles.get_colors()
        
        layout = QVBoxLayout(self)
        # Use 8px grid spacing
        padding = TimelineDesignSystem.get_spacing(2)  # 16px
        spacing = TimelineDesignSystem.get_spacing(1)  # 8px
        layout.setContentsMargins(padding, padding, padding, padding)
        layout.setSpacing(spacing)
        
        # Icon and title
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(spacing)
        
        if self.icon:
            icon_label = QLabel()
            icon_label.setPixmap(get_icon(self.icon, 18).pixmap(18, 18))
            icon_label.setToolTip(self.title)
            header_layout.addWidget(icon_label)
        
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont(AppStyles.FONT_FAMILY, config['font_stats_label']))
        # WCAG AA compliant text color
        text_secondary = TimelineDesignSystem.get_color_with_contrast('#7F8C8D')
        self.title_label.setStyleSheet(f"color: {text_secondary};")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Value
        self.value_label = QLabel(self.value)
        self.value_label.setFont(QFont(AppStyles.FONT_FAMILY, config['font_stats_value'], QFont.Bold))
        # WCAG AA compliant accent color
        accent_color = TimelineDesignSystem.get_color_with_contrast(self.color)
        self.value_label.setStyleSheet(f"color: {accent_color};")
        layout.addWidget(self.value_label)
        
        # Style with WCAG AA compliance and subtle shadow
        bg_color = colors.get('WHITE', '#FFFFFF')
        bg_light = colors.get('LIGHT_BG', '#F8F9FA')
        border_color = f"{accent_color}40"  # 40 = 25% opacity
        
        self.setStyleSheet(f"""
            QFrame#timelineStatisticsCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {bg_color}, stop:1 {bg_light});
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
            QFrame#timelineStatisticsCard:hover {{
                border: 2px solid {accent_color};
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {bg_color}, stop:1 {bg_light});
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)
    
    def update_value(self, value: str):
        """Update the displayed value"""
        self.value = value
        if hasattr(self, 'value_label'):
            self.value_label.setText(value)
    
    def set_title(self, title: str):
        """Update the title"""
        self.title = title
        if hasattr(self, 'title_label'):
            self.title_label.setText(title)
    
    def set_density_mode(self, mode: str):
        """Update density mode"""
        self.density_mode = mode
        config = TimelineDesignSystem.get_density_config(mode)
        padding = TimelineDesignSystem.get_spacing(2)
        self.layout().setContentsMargins(padding, padding, padding, padding)
        if hasattr(self, 'value_label'):
            self.value_label.setFont(QFont(AppStyles.FONT_FAMILY, config['font_stats_value'], QFont.Bold))


class TimelineChartWidget(QWidget):
    """Chart widget showing event distribution over time"""
    
    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.translator = translator
        self.events = []
        self.setMinimumHeight(250)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup chart widget with design system"""
        colors = AppStyles.get_colors()
        layout = QVBoxLayout(self)
        padding = TimelineDesignSystem.get_spacing(1)  # 8px
        layout.setContentsMargins(padding, padding, padding, padding)
        
        # Title (dynamic, will be updated based on chart type)
        default_title = self.translator.tr('timeline_chart_title_default') if self.translator else "Event Distribution Over Time"
        self.title_label = QLabel(default_title)
        self.title_label.setFont(QFont(AppStyles.FONT_FAMILY, 12, QFont.Bold))
        text_primary = colors.get('TEXT_PRIMARY', '#2C3E50')
        self.title_label.setStyleSheet(f"color: {text_primary}; padding: {padding}px;")
        layout.addWidget(self.title_label)
        
        # Chart frame
        self.chart_frame = QFrame()
        bg_color = colors.get('WHITE', '#FFFFFF')
        border_color = colors.get('BORDER', '#DEE2E6')
        self.chart_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)
        chart_layout = QVBoxLayout(self.chart_frame)
        chart_layout.setContentsMargins(padding, padding, padding, padding)
        
        if MATPLOTLIB_AVAILABLE:
            self.figure = Figure(
                figsize=(8, 3),
                facecolor=colors.get('PANEL_BG', colors.get('WHITE', '#FFFFFF'))
            )
            self.canvas = FigureCanvas(self.figure)
            chart_layout.addWidget(self.canvas)
        else:
            msg = self.translator.tr('timeline_chart_matplotlib_required') if self.translator else "Charts require matplotlib.\nInstall with: pip install matplotlib"
            no_chart_label = QLabel(msg)
            no_chart_label.setAlignment(Qt.AlignCenter)
            text_secondary = colors.get('TEXT_SECONDARY', '#7F8C8D')
            no_chart_label.setStyleSheet(f"color: {text_secondary}; padding: 20px;")
            chart_layout.addWidget(no_chart_label)
        
        layout.addWidget(self.chart_frame)
    
    def update_chart(self, events: List[Dict], chart_type: str = 'timeline'):
        """Update chart with events and chart type"""
        self.events = events
        self.chart_type = chart_type
        if not MATPLOTLIB_AVAILABLE or not events:
            return
        
        try:
            self.figure.clear()
            colors = AppStyles.get_colors()
            accent_color = TimelineDesignSystem.get_color_with_contrast('#3498DB')
            
            if chart_type == 'timeline':
                self._draw_timeline_chart(events, accent_color)
            elif chart_type == 'type_sort':
                self._draw_type_sort_chart(events, colors)
            elif chart_type == 'day_of_week':
                self._draw_day_of_week_chart(events, accent_color)
            elif chart_type == 'monthly':
                self._draw_monthly_chart(events, accent_color)
            elif chart_type == 'classification':
                self._draw_classification_chart(events, colors)
            else:
                self._draw_timeline_chart(events, accent_color)

            # Repaint matplotlib surfaces with the active Qt theme rather than
            # leaving black labels on a dark workspace.
            panel_bg = colors.get('PANEL_BG', colors.get('WHITE', '#FFFFFF'))
            text_color = colors.get('TEXT_PRIMARY', '#2C3E50')
            self.figure.set_facecolor(panel_bg)
            for axis in self.figure.axes:
                axis.set_facecolor(panel_bg)
                axis.tick_params(colors=text_color)
                axis.xaxis.label.set_color(text_color)
                axis.yaxis.label.set_color(text_color)
                for spine in axis.spines.values():
                    spine.set_color(colors.get('BORDER', '#D7E0EC'))
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"Error updating chart: {e}")
    
    def _draw_timeline_chart(self, events: List[Dict], accent_color: str):
        """Draw timeline distribution chart"""
        ax = self.figure.add_subplot(111)
        title = self.translator.tr('timeline_chart_title_timeline') if self.translator else "Timeline Event Distribution"
        self.title_label.setText(title)
        
        # Group events by date
        date_counts = defaultdict(int)
        for event in events:
            event_date = self.get_event_date(event)
            if event_date:
                date_key = event_date.strftime('%Y-%m-%d')
                date_counts[date_key] += 1
        
        if not date_counts:
            return
        
        sorted_dates = sorted(date_counts.items())
        dates = [d[0] for d in sorted_dates]
        counts = [d[1] for d in sorted_dates]
        
        plot_label = self.translator.tr('timeline_chart_plot_label') if self.translator else 'Events'
        ax.plot(range(len(dates)), counts, marker='o', color=accent_color, 
               linewidth=2.5, markersize=6, label=plot_label)
        ax.fill_between(range(len(dates)), counts, alpha=0.3, color=accent_color)
        
        step = max(1, len(dates) // 10)
        ax.set_xticks(range(0, len(dates), step))
        ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)], 
                          rotation=45, ha='right', fontsize=8)
        
        ylabel = self.translator.tr('timeline_chart_label_events') if self.translator else 'Number of Events'
        ax.set_ylabel(ylabel, fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
    
    def _draw_type_sort_chart(self, events: List[Dict], colors: Dict):
        """Draw type distribution chart (bar/pie)"""
        ax = self.figure.add_subplot(111)
        title = self.translator.tr('timeline_chart_title_type') if self.translator else "Event Distribution by Type"
        self.title_label.setText(title)
        
        type_counts = Counter()
        for event in events:
            record_type = event.get('record_type', 'unknown')
            type_counts[record_type] += 1
        
        if not type_counts:
            return
        
        types = list(type_counts.keys())
        counts = list(type_counts.values())
        
        # Color mapping
        color_map = {
            'analysis': TimelineDesignSystem.get_color_with_contrast('#9B59B6'),
            'content': TimelineDesignSystem.get_color_with_contrast('#3498DB'),
            'source': TimelineDesignSystem.get_color_with_contrast('#27AE60'),
        }
        bar_colors = [color_map.get(t, '#95A5A6') for t in types]
        
        ax.bar(types, counts, color=bar_colors, alpha=0.8)
        ylabel = self.translator.tr('timeline_chart_label_events') if self.translator else 'Number of Events'
        xlabel = self.translator.tr('timeline_chart_label_type') if self.translator else 'Event Type'
        ax.set_ylabel(ylabel, fontsize=10, fontweight='bold')
        ax.set_xlabel(xlabel, fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
    
    def _draw_day_of_week_chart(self, events: List[Dict], accent_color: str):
        """Draw day of week patterns chart"""
        ax = self.figure.add_subplot(111)
        title = self.translator.tr('timeline_chart_title_day') if self.translator else "Activity by Day of Week"
        self.title_label.setText(title)
        
        day_counts = defaultdict(int)
        if self.translator:
            day_names = [
                self.translator.tr('timeline_day_mon'),
                self.translator.tr('timeline_day_tue'),
                self.translator.tr('timeline_day_wed'),
                self.translator.tr('timeline_day_thu'),
                self.translator.tr('timeline_day_fri'),
                self.translator.tr('timeline_day_sat'),
                self.translator.tr('timeline_day_sun')
            ]
        else:
            day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        for event in events:
            event_date = self.get_event_date(event)
            if event_date:
                day_idx = event_date.weekday()  # 0=Monday, 6=Sunday
                day_counts[day_idx] += 1
        
        if not day_counts:
            return
        
        counts = [day_counts.get(i, 0) for i in range(7)]
        
        ax.bar(day_names, counts, color=accent_color, alpha=0.8)
        ylabel = self.translator.tr('timeline_chart_label_events') if self.translator else 'Number of Events'
        xlabel = self.translator.tr('timeline_chart_label_day') if self.translator else 'Day of Week'
        ax.set_ylabel(ylabel, fontsize=10, fontweight='bold')
        ax.set_xlabel(xlabel, fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
    
    def _draw_monthly_chart(self, events: List[Dict], accent_color: str):
        """Draw monthly aggregation chart"""
        ax = self.figure.add_subplot(111)
        title = self.translator.tr('timeline_chart_title_monthly') if self.translator else "Monthly Event Aggregation"
        self.title_label.setText(title)
        
        monthly_counts = defaultdict(int)
        for event in events:
            event_date = self.get_event_date(event)
            if event_date:
                month_key = event_date.strftime('%Y-%m')
                monthly_counts[month_key] += 1
        
        if not monthly_counts:
            return
        
        sorted_months = sorted(monthly_counts.items())
        months = [m[0] for m in sorted_months]
        counts = [m[1] for m in sorted_months]
        
        ax.bar(range(len(months)), counts, color=accent_color, alpha=0.8)
        step = max(1, len(months) // 10)
        ax.set_xticks(range(0, len(months), step))
        ax.set_xticklabels([months[i] for i in range(0, len(months), step)], 
                          rotation=45, ha='right', fontsize=8)
        ylabel = self.translator.tr('timeline_chart_label_events') if self.translator else 'Number of Events'
        ax.set_ylabel(ylabel, fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
    
    def _draw_classification_chart(self, events: List[Dict], colors: Dict):
        """Draw classification distribution chart"""
        ax = self.figure.add_subplot(111)
        title = self.translator.tr('timeline_chart_title_classification') if self.translator else "Classification Distribution"
        self.title_label.setText(title)
        
        classification_counts = Counter()
        for event in events:
            classification = event.get('classification')
            if classification:
                classification_counts[classification] += 1
        
        if not classification_counts:
            return
        
        # Get top 10 classifications
        top_classifications = classification_counts.most_common(10)
        classifications = [c[0][:20] + '...' if len(c[0]) > 20 else c[0] for c in top_classifications]
        counts = [c[1] for c in top_classifications]
        
        accent_color = TimelineDesignSystem.get_color_with_contrast('#3498DB')
        ax.barh(classifications, counts, color=accent_color, alpha=0.8)
        xlabel = self.translator.tr('timeline_chart_label_events') if self.translator else 'Number of Events'
        ax.set_xlabel(xlabel, fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='x')
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
    
    def get_event_date(self, event: Dict) -> Optional[datetime]:
        """Get event date"""
        date_fields = ['date_content', 'date_analysis', 'date_entry', 
                      'date_creation', 'source_date_entry', 'content_date_creation']
        for field in date_fields:
            if field in event and event[field]:
                date_val = event[field]
                if isinstance(date_val, datetime):
                    return date_val
                elif isinstance(date_val, str):
                    try:
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']:
                            try:
                                return datetime.strptime(date_val[:19], fmt)
                            except:
                                continue
                    except:
                        pass
        return None


class AnalysisPanel(QFrame):
    """Analysis panel showing key insights"""
    
    def __init__(self, translator: TranslationManager, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.setObjectName('timelineAnalysisPanel')
        self.setup_ui()
    
    def setup_ui(self):
        """Setup analysis panel"""
        colors = AppStyles.get_colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title_text = self.translator.tr('timeline_analysis_title') if self.translator else "Timeline Analysis"
        title = QLabel(title_text)
        title.setFont(QFont('Segoe UI', 12, QFont.Bold))
        title.setStyleSheet(
            f"color: {colors.get('TEXT_PRIMARY', '#2C3E50')}; padding: 5px;"
        )
        layout.addWidget(title)
        
        # Analysis content
        no_data_text = self.translator.tr('timeline_analysis_no_data') if self.translator else "No analysis available"
        self.analysis_label = QLabel(no_data_text)
        self.analysis_label.setWordWrap(True)
        self.analysis_label.setStyleSheet(
            f"color: {colors.get('TEXT_SECONDARY', '#555')}; padding: 10px;"
        )
        layout.addWidget(self.analysis_label)
        
        # Style
        colors = AppStyles.get_colors()
        self.setStyleSheet(f"""
            QFrame#timelineAnalysisPanel {{
                background-color: {colors.get('LIGHT_BG', '#F8F9FA')};
                border: 1px solid {colors.get('BORDER', '#DEE2EC')};
                border-radius: 8px;
            }}
        """)
    
    def update_analysis(self, events: List[Dict]):
        """Update analysis with events"""
        if not events:
            no_events_text = self.translator.tr('timeline_analysis_no_events') if self.translator else "No events to analyze"
            self.analysis_label.setText(no_events_text)
            return
        
        try:
            # Calculate statistics
            total = len(events)
            
            # Count by type
            type_counts = Counter()
            for event in events:
                record_type = event.get('record_type', 'unknown')
                type_counts[record_type] += 1
            
            # Count classifications
            classifications = Counter()
            for event in events:
                if event.get('classification'):
                    classifications[event['classification']] += 1
            
            # Find most active period
            monthly_counts = defaultdict(int)
            for event in events:
                event_date = self.get_event_date(event)
                if event_date:
                    month_key = event_date.strftime('%Y-%m')
                    monthly_counts[month_key] += 1
            
            most_active_month = max(monthly_counts.items(), key=lambda x: x[1]) if monthly_counts else None
            
            # Build analysis text
            total_label = self.translator.tr('timeline_analysis_total') if self.translator else "Total Events:"
            by_type_label = self.translator.tr('timeline_analysis_by_type') if self.translator else "By Type:"
            analysis_parts = [
                f"<b>{total_label}</b> {total:,}",
                "",
                f"<b>{by_type_label}</b>",
            ]
            
            for event_type, count in type_counts.most_common():
                percentage = (count / total * 100) if total > 0 else 0
                type_name = event_type.title()
                analysis_parts.append(f"  {type_name}: {count} ({percentage:.1f}%)")
            
            if classifications:
                top_class_label = self.translator.tr('timeline_analysis_top_classifications') if self.translator else "Top Classifications:"
                analysis_parts.append("")
                analysis_parts.append(f"<b>{top_class_label}</b>")
                for classification, count in classifications.most_common(5):
                    percentage = (count / total * 100) if total > 0 else 0
                    analysis_parts.append(
                        f"  {escape(str(classification))}: {count} ({percentage:.1f}%)"
                    )
            
            if most_active_month:
                most_active_label = self.translator.tr('timeline_analysis_most_active') if self.translator else "Most Active Period:"
                events_word = self.translator.tr('timeline_event') if self.translator else "events"
                analysis_parts.append("")
                analysis_parts.append(f"<b>{most_active_label}</b> {most_active_month[0]} ({most_active_month[1]} {events_word})")
            
            self.analysis_label.setText("<br>".join(analysis_parts))
            
        except Exception as e:
            logger.error(f"Error updating analysis: {e}")
            error_text = self.translator.tr('timeline_analysis_error', error=str(e)) if self.translator else f"Error analyzing data: {e}"
            self.analysis_label.setText(error_text)
    
    def get_event_date(self, event: Dict) -> Optional[datetime]:
        """Get event date"""
        date_fields = ['date_content', 'date_analysis', 'date_entry', 
                      'date_creation', 'source_date_entry', 'content_date_creation']
        for field in date_fields:
            if field in event and event[field]:
                date_val = event[field]
                if isinstance(date_val, datetime):
                    return date_val
                elif isinstance(date_val, str):
                    try:
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']:
                            try:
                                return datetime.strptime(date_val[:19], fmt)
                            except:
                                continue
                    except:
                        pass
        return None


class TimelineAxisWidget(QWidget):
    """Visual timeline axis with vertical line and nodes"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(80)
        self.node_positions = []
        self.setMinimumHeight(100)
    
    def set_node_positions(self, positions: List[tuple]):
        """Set node positions: [(y_pos, color, size), ...]"""
        self.node_positions = positions
        self.update()
    
    def paintEvent(self, event):
        """Paint the timeline axis"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        center_x = width // 2
        
        # Draw main timeline line (vertical)
        line_pen = QPen(QColor("#3498DB"), 4)
        painter.setPen(line_pen)
        painter.drawLine(center_x, 0, center_x, self.height())
        
        # Draw gradient glow effect
        gradient = QLinearGradient(center_x - 20, 0, center_x + 20, 0)
        gradient.setColorAt(0, QColor("#3498DB00"))
        gradient.setColorAt(0.5, QColor("#3498DB40"))
        gradient.setColorAt(1, QColor("#3498DB00"))
        
        glow_pen = QPen(QBrush(gradient), 30)
        painter.setPen(glow_pen)
        painter.drawLine(center_x, 0, center_x, self.height())
        
        # Draw nodes
        for y_pos, color, size in self.node_positions:
            if 0 <= y_pos <= self.height():
                # Outer glow
                radial_gradient = QRadialGradient(center_x, y_pos, size + 5)
                radial_gradient.setColorAt(0, QColor(color).lighter(150))
                radial_gradient.setColorAt(1, QColor("#00000000"))
                painter.setBrush(QBrush(radial_gradient))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPoint(center_x, y_pos), size + 5, size + 5)
                
                # Main node
                painter.setBrush(QBrush(QColor(color)))
                painter.setPen(QPen(QColor("#FFFFFF"), 2))
                painter.drawEllipse(QPoint(center_x, y_pos), size, size)
                
                # Inner highlight
                painter.setBrush(QBrush(QColor("#FFFFFF")))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPoint(center_x - size//4, y_pos - size//4), size//3, size//3)


class TimelineEventWidget(QFrame):
    """
    Enhanced event widget with F-pattern layout and design system
    Follows F-pattern reading: Date, title, description, and tags
    """
    
    clicked = pyqtSignal(dict)
    
    def __init__(self, event_data: Dict, translator: TranslationManager, 
                 density_mode: str = 'comfortable', parent=None):
        super().__init__(parent)
        self.event_data = event_data
        self.translator = translator
        self.is_selected = False
        self.density_mode = density_mode
        self.setObjectName('timelineEventCard')
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        """Setup event widget UI with F-pattern layout and design system"""
        config = TimelineDesignSystem.get_density_config(self.density_mode)
        colors = AppStyles.get_colors()
        
        # Set minimum height based on density mode
        self.setMinimumHeight(config['card_min_height'])
        
        layout = QHBoxLayout(self)
        # Use 8px grid spacing
        padding = config['card_padding']
        spacing = TimelineDesignSystem.get_spacing(2)  # 16px between date and content
        layout.setContentsMargins(padding, padding, padding, padding)
        layout.setSpacing(spacing)
        
        # F-Pattern Layout: Date Section (left, prominent)
        date_widget = QWidget()
        date_widget.setFixedWidth(200)  # Preserve full dates at comfortable density
        date_layout = QVBoxLayout(date_widget)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(TimelineDesignSystem.get_spacing(1))  # 8px
        
        event_date = self.get_event_date()
        if event_date:
            date_str = self.format_date(event_date)
            time_str = self.format_time(event_date)
            day_name = event_date.strftime('%A')[:3].upper()
        else:
            date_str = self.translator.tr('timeline_no_date')
            time_str = ""
            day_name = ""
        
        # Day name (top)
        if day_name:
            day_label = QLabel(day_name)
            accent_color = TimelineDesignSystem.get_color_with_contrast('#3498DB')
            day_label.setFont(QFont(AppStyles.FONT_FAMILY, config['font_meta'], QFont.Bold))
            day_label.setStyleSheet(f"color: {accent_color};")
            date_layout.addWidget(day_label)
        
        # Date (prominent)
        self.date_label = QLabel(date_str)
        text_primary = TimelineDesignSystem.get_color_with_contrast('#2C3E50')
        self.date_label.setFont(QFont(AppStyles.FONT_FAMILY, config['font_date'], QFont.Bold))
        self.date_label.setStyleSheet(f"color: {text_primary};")
        date_layout.addWidget(self.date_label)
        
        # Time (secondary)
        if time_str:
            self.time_label = QLabel(time_str)
            text_secondary = TimelineDesignSystem.get_color_with_contrast('#7F8C8D')
            self.time_label.setFont(QFont(AppStyles.FONT_FAMILY, config['font_meta']))
            self.time_label.setStyleSheet(f"color: {text_secondary};")
            date_layout.addWidget(self.time_label)
        
        date_layout.addStretch()
        layout.addWidget(date_widget)
        
        # Content section (F-pattern: title, description, tags)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(TimelineDesignSystem.get_spacing(1))  # 8px
        
        # Title (F-pattern: below date, bold, larger font)
        title = self.get_event_title()
        if title:
            self.title_label = QLabel(title)
            self.title_label.setTextFormat(Qt.PlainText)
            self.title_label.setFont(QFont(AppStyles.FONT_FAMILY, config['font_title'], QFont.Bold))
            self.title_label.setStyleSheet(f"color: {text_primary};")
            self.title_label.setWordWrap(True)
            content_layout.addWidget(self.title_label)
        
        # Description (F-pattern: below title, secondary text)
        description = self.get_event_description()
        if description:
            self.desc_label = QLabel(description)
            self.desc_label.setFont(QFont(AppStyles.FONT_FAMILY, config['font_desc']))
            desc_color = colors.get('TEXT_SECONDARY', '#555555')
            self.desc_label.setStyleSheet(f"color: {desc_color}; line-height: 1.5;")
            self.desc_label.setWordWrap(True)
            self.desc_label.setTextFormat(Qt.RichText)
            content_layout.addWidget(self.desc_label)
        
        # Tags/Metadata badges (F-pattern: bottom, badges)
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(TimelineDesignSystem.get_spacing(1))  # 8px
        self._meta_badges = []
        
        people = self.get_event_people()
        places = self.get_event_places()
        classification = self.event_data.get('classification')
        
        if people:
            badge = self.create_badge("user", people, "#3498DB", config)
            self._meta_badges.append(badge)
            meta_layout.addWidget(badge)
        
        if places:
            badge = self.create_badge("location", places, "#E74C3C", config)
            self._meta_badges.append(badge)
            meta_layout.addWidget(badge)
        
        if classification:
            badge = self.create_badge("tag", classification, "#9B59B6", config)
            self._meta_badges.append(badge)
            meta_layout.addWidget(badge)
        
        meta_layout.addStretch()
        content_layout.addLayout(meta_layout)
        
        # Source (optional, below tags)
        source = self.get_event_source()
        if source:
            source_row = QHBoxLayout()
            source_icon = QLabel()
            source_icon.setPixmap(get_icon('newspaper', 16).pixmap(16, 16))
            source_icon.setToolTip(self.translator.tr('lbl_source'))
            source_label = QLabel(source)
            source_label.setTextFormat(Qt.PlainText)
            source_label.setFont(QFont(AppStyles.FONT_FAMILY, config['font_meta']))
            muted_color = colors.get('TEXT_MUTED', '#95A5A6')
            source_label.setStyleSheet(f"color: {muted_color}; font-style: italic;")
            source_row.addWidget(source_icon)
            source_row.addWidget(source_label)
            source_row.addStretch()
            content_layout.addLayout(source_row)
        
        layout.addLayout(content_layout, 1)
        self.setCursor(Qt.PointingHandCursor)
    
    def create_badge(self, icon: str, text: str, color: str, config: Dict) -> QFrame:
        """Create a badge widget with design system"""
        badge = QFrame()
        accent_color = TimelineDesignSystem.get_color_with_contrast(color)
        badge_padding = TimelineDesignSystem.get_spacing(1)  # 8px
        
        badge.setStyleSheet(f"""
            QFrame {{
                background-color: {accent_color}20;
                border: 1px solid {accent_color}60;
                border-radius: 6px;
                padding: {badge_padding//2}px {badge_padding}px;
            }}
        """)
        badge_layout = QHBoxLayout(badge)
        badge_layout.setContentsMargins(badge_padding//2, badge_padding//2, 
                                       badge_padding//2, badge_padding//2)
        badge_layout.setSpacing(badge_padding//2)
        
        icon_label = QLabel()
        icon_label.setPixmap(get_icon(icon, 16).pixmap(16, 16))
        icon_label.setToolTip(icon.replace('_', ' ').title())
        text_label = QLabel(text)
        text_label.setTextFormat(Qt.PlainText)
        text_label.setFont(QFont(AppStyles.FONT_FAMILY, config['font_meta'], QFont.Bold))
        text_label.setStyleSheet(f"color: {accent_color};")
        text_label.setToolTip(str(text))
        text_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        badge.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        badge.setProperty('fullBadgeText', str(text))
        badge.badge_text_label = text_label
        
        badge_layout.addWidget(icon_label)
        badge_layout.addWidget(text_label, 1)
        
        return badge

    def resizeEvent(self, event):
        """Keep metadata badges readable when the card becomes narrow."""
        super().resizeEvent(event)
        badges = getattr(self, '_meta_badges', [])
        if not badges:
            return
        date_widget = self.layout().itemAt(0).widget() if self.layout() else None
        date_width = date_widget.width() if date_widget else 0
        available = max(180, self.width() - date_width - 96)
        gap_total = max(0, len(badges) - 1) * 8
        badge_width = max(96, (available - gap_total) // len(badges))
        for badge in badges:
            badge.setMaximumWidth(badge_width)
            text_label = getattr(badge, 'badge_text_label', None)
            if text_label is not None:
                text_width = max(40, badge_width - 48)
                full_text = badge.property('fullBadgeText') or ''
                metrics = QFontMetrics(text_label.font())
                text_label.setText(metrics.elidedText(str(full_text), Qt.ElideRight, text_width))
    
    def setup_styles(self):
        """Setup widget styles with WCAG AA compliance"""
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(0)
        self.update_style()
    
    def update_style(self):
        """Update widget style with design system colors"""
        colors = AppStyles.get_colors()
        bg_color = colors.get('WHITE', '#FFFFFF')
        bg_hover = colors.get('LIGHT_BG', '#F8F9FA')
        border_color = colors.get('BORDER', '#E0E0E0')
        accent_color = TimelineDesignSystem.get_color_with_contrast('#3498DB')
        
        if self.is_selected:
            selected_bg = colors.get('LIGHT_BG', '#EBF5FB')
            self.setStyleSheet(f"""
                QFrame#timelineEventCard {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {selected_bg}, stop:1 {bg_hover});
                    border: 3px solid {accent_color};
                    border-radius: 8px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#timelineEventCard {{
                    background-color: {bg_color};
                    border: 2px solid {border_color};
                    border-radius: 8px;
                }}
                QFrame#timelineEventCard:hover {{
                    border: 2px solid {accent_color};
                    background-color: {bg_hover};
                }}
            """)
    
    def set_density_mode(self, mode: str):
        """Update density mode"""
        self.density_mode = mode
        config = TimelineDesignSystem.get_density_config(mode)
        self.setMinimumHeight(config['card_min_height'])
        padding = config['card_padding']
        self.layout().setContentsMargins(padding, padding, padding, padding)
    
    def apply_zoom(self, zoom_factor: float):
        """Apply zoom factor to make text and fields clearer"""
        config = TimelineDesignSystem.get_density_config(self.density_mode)
        
        # Apply zoom to fonts for all labels
        if hasattr(self, 'date_label'):
            base_font_size = config['font_date']
            self.date_label.setFont(QFont(AppStyles.FONT_FAMILY, int(base_font_size * zoom_factor), QFont.Bold))
        
        if hasattr(self, 'time_label'):
            base_font_size = config['font_meta']
            self.time_label.setFont(QFont(AppStyles.FONT_FAMILY, int(base_font_size * zoom_factor)))
        
        if hasattr(self, 'title_label'):
            base_font_size = config['font_title']
            self.title_label.setFont(QFont(AppStyles.FONT_FAMILY, int(base_font_size * zoom_factor), QFont.Bold))
        
        if hasattr(self, 'desc_label'):
            base_font_size = config['font_desc']
            self.desc_label.setFont(QFont(AppStyles.FONT_FAMILY, int(base_font_size * zoom_factor)))
        
        # Badge/source labels already use the active density font. Do not
        # multiply the primary labels a second time; doing so clipped dates
        # and made comfortable cards unnecessarily tall.
        
        # Apply zoom to padding for better spacing
        base_padding = config['card_padding']
        zoomed_padding = int(base_padding * zoom_factor)
        self.layout().setContentsMargins(zoomed_padding, zoomed_padding, 
                                        zoomed_padding, zoomed_padding)
        
        # Update minimum height
        base_height = config['card_min_height']
        self.setMinimumHeight(int(base_height * zoom_factor))
        
        # Keep the formatted date readable at every zoom level. The original
        # fixed column became too narrow once the date font was enlarged,
        # which clipped the day portion even though the card itself had room.
        date_widget = self.layout().itemAt(0).widget()
        if date_widget:
            base_width = 200
            required_width = 0
            if hasattr(self, 'date_label'):
                required_width = self.date_label.sizeHint().width() + (zoomed_padding * 2) + 8
            date_widget.setFixedWidth(max(int(base_width * zoom_factor), required_width))
    
    def mousePressEvent(self, event):
        """Handle mouse click"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.event_data)
        super().mousePressEvent(event)
    
    def set_selected(self, selected: bool):
        """Set selection state"""
        self.is_selected = selected
        self.update_style()
    
    def get_event_date(self) -> Optional[datetime]:
        """Get event date"""
        date_fields = ['date_content', 'date_analysis', 'date_entry', 
                      'date_creation', 'source_date_entry', 'content_date_creation']
        for field in date_fields:
            if field in self.event_data and self.event_data[field]:
                date_val = self.event_data[field]
                if isinstance(date_val, datetime):
                    return date_val
                elif isinstance(date_val, str):
                    try:
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']:
                            try:
                                return datetime.strptime(date_val[:19], fmt)
                            except:
                                continue
                    except:
                        pass
        return None
    
    def format_date(self, dt: datetime) -> str:
        """Format date"""
        return dt.strftime('%Y-%m-%d')
    
    def format_time(self, dt: datetime) -> str:
        """Format time"""
        return dt.strftime('%H:%M')
    
    def get_event_title(self) -> str:
        """Get event title"""
        if 'content_title' in self.event_data and self.event_data['content_title']:
            return str(self.event_data['content_title'])
        if 'classification' in self.event_data and self.event_data['classification']:
            return str(self.event_data['classification'])
        if 'source_name' in self.event_data and self.event_data['source_name']:
            return str(self.event_data['source_name'])
        if 'content_data' in self.event_data and self.event_data['content_data']:
            content = str(self.event_data['content_data'])
            title = content[:100].strip()
            if len(content) > 100:
                title += "..."
            return title
        return self.translator.tr('timeline_event')
    
    def get_event_description(self) -> str:
        """Get event description"""
        parts = []
        if 'content_data' in self.event_data and self.event_data['content_data']:
            content = str(self.event_data['content_data'])
            if 'content_title' in self.event_data and self.event_data['content_title']:
                parts.append(escape(content))
            elif len(content) > 100:
                parts.append(escape(content))
        if 'note' in self.event_data and self.event_data['note']:
            parts.append(f"<i>Note: {escape(str(self.event_data['note']))}</i>")
        if 'content_note' in self.event_data and self.event_data['content_note']:
            parts.append(f"<i>Note: {escape(str(self.event_data['content_note']))}</i>")
        return "<br>".join(parts) if parts else ""
    
    def get_event_people(self) -> str:
        """Get people names"""
        if 'list_names_people' in self.event_data and self.event_data['list_names_people']:
            people = str(self.event_data['list_names_people'])
            # Truncate if too long
            if len(people) > 50:
                return people[:47] + "..."
            return people
        return ""
    
    def get_event_places(self) -> str:
        """Get place names"""
        places = []
        if 'list_names_places' in self.event_data and self.event_data['list_names_places']:
            places.append(str(self.event_data['list_names_places']))
        if 'source_city' in self.event_data and self.event_data['source_city']:
            places.append(str(self.event_data['source_city']))
        if 'source_country' in self.event_data and self.event_data['source_country']:
            places.append(str(self.event_data['source_country']))
        result = ", ".join(places)
        if len(result) > 50:
            return result[:47] + "..."
        return result
    
    def get_event_source(self) -> str:
        """Get source information"""
        source_parts = []
        if 'source_name' in self.event_data and self.event_data['source_name']:
            source_parts.append(str(self.event_data['source_name']))
        if 'source_type' in self.event_data and self.event_data['source_type']:
            source_parts.append(f"({self.event_data['source_type']})")
        return " - ".join(source_parts) if source_parts else ""


class TimelineWidget(QWidget):
    """
    Professional timeline widget with statistics, charts, and analysis
    Enhanced with design system, density modes, and WCAG AA compliance
    """
    
    event_selected = pyqtSignal(dict)
    
    def __init__(self, translator: TranslationManager, parent=None, internal_scroll_enabled: bool = True):
        super().__init__(parent)
        self.translator = translator
        self.config = ConfigManager()
        self.events = []
        self.filtered_events = []
        self.selected_event = None
        self.sort_order = 'desc'
        self.is_rtl = translator.current_language == 'ar'
        
        # Load density mode from config
        self.density_mode = self.config.get_timeline_density_mode()
        if self.density_mode not in ['compact', 'comfortable', 'expansive']:
            self.density_mode = 'comfortable'
        
        # Chart type
        self.current_chart_type = 'timeline'
        
        # Internal scroll enabled by default (can be disabled for unified scroll)
        self._internal_scroll_enabled = internal_scroll_enabled
        
        # Pagination support
        self._full_filtered_events = []  # Store all filtered events for pagination
        self.pagination = None
        
        # Zoom support for data section (1.0 = 100%, higher = zoomed in for clarity)
        self.zoom_factor = 1.15  # 15% zoom for better readability
        
        # Search and filter support
        self.search_text = ""
        self.search_fields = ['content_title', 'content_data', 'classification', 
                             'list_names_people', 'list_names_places', 'source_name']
        
        # Enhanced filter criteria
        self.filter_people = ""  # Selected person name
        self.filter_places = ""  # Selected place name
        self.filter_classification = ""  # Selected classification
        self.sort_by = 'date'  # Sort by: date, people, places, classification, source
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup professional timeline UI with design system"""
        colors = AppStyles.get_colors()
        config = TimelineDesignSystem.get_density_config(self.density_mode)
        
        layout = QVBoxLayout(self)
        # Use 8px grid spacing
        margin = TimelineDesignSystem.get_spacing(1)  # 8px
        spacing = TimelineDesignSystem.get_spacing(2)  # 16px
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Statistics Dashboard with design system
        stats_frame = QFrame()
        stats_frame.setObjectName('timelineOverview')
        stats_padding = TimelineDesignSystem.get_spacing(2)  # 16px
        
        # The overview is a quiet summary surface; the cards carry emphasis
        # individually instead of putting the whole page on a dark banner.
        stats_frame.setStyleSheet(f"""
            QFrame#timelineOverview {{
                background-color: {colors.get('WHITE', '#FFFFFF')};
                border: 1px solid {colors.get('BORDER', '#D7E0EC')};
                border-radius: 10px;
                padding: {stats_padding}px;
            }}
        """)
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(TimelineDesignSystem.get_spacing(2))  # 16px
        
        total_label = self.translator.tr('timeline_stats_total')
        filtered_label = self.translator.tr('timeline_stats_filtered')
        sources_label = self.translator.tr('timeline_stats_sources')
        analyses_label = self.translator.tr('timeline_stats_analyses')
        self.total_card = StatisticsCard(total_label, "0", "calendar", "#3498DB", self.density_mode)
        self.filtered_card = StatisticsCard(filtered_label, "0", "preview", "#27AE60", self.density_mode)
        self.sources_card = StatisticsCard(sources_label, "0", "newspaper", "#E74C3C", self.density_mode)
        self.analyses_card = StatisticsCard(analyses_label, "0", "statistics", "#9B59B6", self.density_mode)
        
        stats_layout.addWidget(self.total_card, 0, 0)
        stats_layout.addWidget(self.filtered_card, 0, 1)
        stats_layout.addWidget(self.sources_card, 0, 2)
        stats_layout.addWidget(self.analyses_card, 0, 3)
        
        layout.addWidget(stats_frame)
        
        # Controls bar with design system
        controls_frame = QFrame()
        bg_color = colors.get('LIGHT_BG', '#F8F9FA')
        border_color = colors.get('BORDER', '#DEE2E6')
        controls_padding = TimelineDesignSystem.get_spacing(2)  # 16px
        
        controls_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: {controls_padding}px;
            }}
        """)
        controls_outer = QVBoxLayout(controls_frame)
        controls_outer.setContentsMargins(12, 10, 12, 10)
        controls_outer.setSpacing(8)
        self.controls_heading = QLabel(
            self.translator.tr('timeline_controls_title', default='View controls')
        )
        self.controls_heading.setObjectName('timelineControlsTitle')
        controls_outer.addWidget(self.controls_heading)
        controls_scroll = QScrollArea(controls_frame)
        controls_scroll.setObjectName('timelineControlsScroller')
        controls_scroll.setWidgetResizable(False)
        controls_scroll.setFrameShape(QFrame.NoFrame)
        controls_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        controls_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        controls_content = QWidget()
        controls_row_layout = QHBoxLayout(controls_content)
        controls_row_layout.setContentsMargins(0, 0, 0, 0)
        controls_row_layout.setSpacing(TimelineDesignSystem.get_spacing(2))
        controls_scroll.setWidget(controls_content)
        controls_outer.addWidget(controls_scroll)

        # Sort control is kept together as one task group.
        self.order_group = QGroupBox(
            self.translator.tr('timeline_order_group', default='Order')
        )
        order_group = self.order_group
        order_group.setObjectName('timelineControlGroup')
        order_layout = QHBoxLayout(order_group)
        order_layout.setContentsMargins(10, 8, 10, 8)
        order_layout.setSpacing(8)
        controls_row_layout.addWidget(order_group)
        controls_layout = order_layout
        self.sort_label = QLabel(self.translator.tr('timeline_sort'))
        self.sort_label.setFont(QFont(AppStyles.FONT_FAMILY, 10, QFont.Bold))
        controls_layout.addWidget(self.sort_label)
        
        self.sort_by_combo = QComboBox()
        self.sort_by_combo.setFont(QFont(AppStyles.FONT_FAMILY, 10))
        self.sort_by_combo.setMinimumWidth(150)
        self.sort_by_combo.setMinimumHeight(32)
        self.sort_by_combo.addItem(self.translator.tr('timeline_sort_by_date', default='Date'), 'date')
        self.sort_by_combo.addItem(self.translator.tr('timeline_sort_by_people', default='People'), 'people')
        self.sort_by_combo.addItem(self.translator.tr('timeline_sort_by_places', default='Places'), 'places')
        self.sort_by_combo.addItem(self.translator.tr('timeline_sort_by_classification', default='Classification'), 'classification')
        self.sort_by_combo.addItem(self.translator.tr('timeline_sort_by_source', default='Source'), 'source')
        accent_color = TimelineDesignSystem.get_color_with_contrast('#3498DB')
        input_bg = colors.get('INPUT_BG', '#FFFFFF')
        self.sort_by_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {input_bg};
                border: 2px solid {border_color};
                border-radius: 6px;
                padding: 4px 8px;
            }}
            QComboBox:hover {{
                border: 2px solid {accent_color};
            }}
        """)
        self.sort_by_combo.currentIndexChanged.connect(self.on_sort_by_changed)
        controls_layout.addWidget(self.sort_by_combo)
        
        # Sort order (asc/desc)
        self.sort_order_combo = QComboBox()
        self.sort_order_combo.setFont(QFont(AppStyles.FONT_FAMILY, 10))
        self.sort_order_combo.setMinimumWidth(150)
        self.sort_order_combo.setMinimumHeight(32)
        self.sort_order_combo.addItem(self.translator.tr('timeline_latest_first'), 'desc')
        self.sort_order_combo.addItem(self.translator.tr('timeline_chronological'), 'asc')
        self.sort_order_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {input_bg};
                border: 2px solid {border_color};
                border-radius: 6px;
                padding: 4px 8px;
            }}
            QComboBox:hover {{
                border: 2px solid {accent_color};
            }}
        """)
        self.sort_order_combo.currentIndexChanged.connect(self.on_sort_order_changed)
        controls_layout.addWidget(self.sort_order_combo)

        # Density is a separate decision group, not a continuation of sort.
        self.density_group = QGroupBox(
            self.translator.tr('timeline_density_group', default='Density')
        )
        density_group = self.density_group
        density_group.setObjectName('timelineControlGroup')
        density_layout_outer = QHBoxLayout(density_group)
        density_layout_outer.setContentsMargins(10, 8, 10, 8)
        density_layout_outer.setSpacing(8)
        controls_row_layout.addWidget(density_group)
        controls_layout = density_layout_outer
        self.density_label = QLabel(self.translator.tr('timeline_density_mode'))
        self.density_label.setFont(QFont(AppStyles.FONT_FAMILY, 10, QFont.Bold))
        controls_layout.addWidget(self.density_label)
        
        self.density_button_group = QButtonGroup(self)
        density_container = QWidget()
        density_layout = QHBoxLayout(density_container)
        density_layout.setContentsMargins(0, 0, 0, 0)
        density_layout.setSpacing(0)
        
        density_modes = ['compact', 'comfortable', 'expansive']
        self.density_buttons = []
        for mode in density_modes:
            btn = QPushButton(self.translator.tr(f'timeline_density_{mode}'))
            btn.setCheckable(True)
            btn.setMinimumWidth(100)
            btn.setMinimumHeight(32)
            btn.setFont(QFont(AppStyles.FONT_FAMILY, 10))
            if mode == self.density_mode:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, m=mode: self.on_density_changed(m))
            self.density_button_group.addButton(btn)
            self.density_buttons.append(btn)
            density_layout.addWidget(btn)
        
        # Style density buttons
        self.update_density_button_styles()
        controls_layout.addWidget(density_container)

        self.date_group = QGroupBox(
            self.translator.tr('timeline_date_group', default='Date range')
        )
        date_group = self.date_group
        date_group.setObjectName('timelineControlGroup')
        date_layout = QHBoxLayout(date_group)
        date_layout.setContentsMargins(10, 8, 10, 8)
        date_layout.setSpacing(8)
        controls_row_layout.addWidget(date_group)
        controls_layout = date_layout

        # Date filters with design system
        self.from_label = QLabel(self.translator.tr('timeline_from'))
        self.from_label.setFont(QFont(AppStyles.FONT_FAMILY, 10))
        controls_layout.addWidget(self.from_label)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addYears(-1))
        self.date_from.setMinimumHeight(32)
        self.date_from.setMinimumWidth(140)
        self.date_from.setStyleSheet(f"""
            QDateEdit {{
                background-color: {input_bg};
                border: 2px solid {border_color};
                border-radius: 6px;
                padding: 4px;
            }}
            QDateEdit:hover {{
                border: 2px solid {accent_color};
            }}
        """)
        self.date_from.dateChanged.connect(self.apply_filters)
        controls_layout.addWidget(self.date_from)
        
        self.to_label = QLabel(self.translator.tr('timeline_to'))
        self.to_label.setFont(QFont(AppStyles.FONT_FAMILY, 10))
        controls_layout.addWidget(self.to_label)
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setMinimumHeight(32)
        self.date_to.setMinimumWidth(140)
        self.date_to.setStyleSheet(f"""
            QDateEdit {{
                background-color: {input_bg};
                border: 2px solid {border_color};
                border-radius: 6px;
                padding: 4px;
            }}
            QDateEdit:hover {{
                border: 2px solid {accent_color};
            }}
        """)
        self.date_to.dateChanged.connect(self.apply_filters)
        controls_layout.addWidget(self.date_to)
        
        clear_btn = QPushButton(self.translator.tr('btn_clear'))
        clear_btn.setFont(QFont(AppStyles.FONT_FAMILY, 10, QFont.Bold))
        clear_btn.setMinimumHeight(32)
        clear_btn.setMinimumWidth(80)
        danger_color = TimelineDesignSystem.get_color_with_contrast('#E74C3C')
        danger_hover = colors.get('DANGER_HOVER', '#C0392B')
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {danger_color};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {danger_hover};
            }}
        """)
        clear_btn.clicked.connect(self.clear_filters)
        controls_layout.addWidget(clear_btn)
        controls_row_layout.addStretch()
        controls_content.adjustSize()
        # Reserve room for the group controls plus the horizontal scrollbar;
        # otherwise the scrollbar covers the combobox/date controls.
        controls_scroll.setFixedHeight(120)
        
        layout.addWidget(controls_frame)
        
        # Use QSplitter to separate Charts section from Data section
        main_splitter = QSplitter(Qt.Vertical)
        
        # ========== CHARTS SECTION (Top) ==========
        charts_section = QWidget()
        charts_section_layout = QVBoxLayout(charts_section)
        charts_section_layout.setContentsMargins(0, 0, 0, 0)
        charts_section_layout.setSpacing(TimelineDesignSystem.get_spacing(1))
        
        # Chart type selector
        chart_controls_frame = QFrame()
        chart_controls_frame.setObjectName('timelineChartControls')
        chart_controls_layout = QHBoxLayout(chart_controls_frame)
        chart_controls_layout.setContentsMargins(TimelineDesignSystem.get_spacing(2), 
                                                 TimelineDesignSystem.get_spacing(1),
                                                 TimelineDesignSystem.get_spacing(2),
                                                 TimelineDesignSystem.get_spacing(1))
        chart_controls_layout.setSpacing(TimelineDesignSystem.get_spacing(2))
        
        self.chart_type_label = QLabel(self.translator.tr('timeline_chart_select'))
        self.chart_type_label.setFont(QFont(AppStyles.FONT_FAMILY, 10, QFont.Bold))
        chart_controls_layout.addWidget(self.chart_type_label)
        
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.setFont(QFont(AppStyles.FONT_FAMILY, 10))
        self.chart_type_combo.setMinimumWidth(200)
        self.chart_type_combo.setMinimumHeight(32)
        self.chart_type_combo.addItem(self.translator.tr('timeline_chart_timeline'), 'timeline')
        self.chart_type_combo.addItem(self.translator.tr('timeline_chart_type_sort'), 'type_sort')
        self.chart_type_combo.addItem(self.translator.tr('timeline_chart_day_of_week'), 'day_of_week')
        self.chart_type_combo.addItem(self.translator.tr('timeline_chart_monthly'), 'monthly')
        self.chart_type_combo.addItem(self.translator.tr('timeline_chart_classification'), 'classification')
        self.chart_type_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {input_bg};
                border: 2px solid {border_color};
                border-radius: 6px;
                padding: 4px 8px;
            }}
            QComboBox:hover {{
                border: 2px solid {accent_color};
            }}
        """)
        self.chart_type_combo.currentIndexChanged.connect(self.on_chart_type_changed)
        chart_controls_layout.addWidget(self.chart_type_combo)
        chart_controls_layout.addStretch()
        
        charts_section_layout.addWidget(chart_controls_frame)
        
        # Charts and Analysis Row
        charts_row = QHBoxLayout()
        charts_row.setSpacing(TimelineDesignSystem.get_spacing(2))  # 16px
        
        # Chart widget (enhanced with multiple chart types)
        self.chart_widget = TimelineChartWidget(translator=self.translator)
        charts_row.addWidget(self.chart_widget, 2)
        
        # Analysis panel
        self.analysis_panel = AnalysisPanel(self.translator)
        charts_row.addWidget(self.analysis_panel, 1)
        
        charts_section_layout.addLayout(charts_row)
        main_splitter.addWidget(charts_section)
        
        # ========== DATA SECTION (Bottom) ==========
        data_section = QWidget()
        data_section_layout = QVBoxLayout(data_section)
        data_section_layout.setContentsMargins(0, 0, 0, 0)
        data_section_layout.setSpacing(TimelineDesignSystem.get_spacing(1))
        
        # Data section header with print/export buttons
        data_header_frame = QFrame()
        data_header_frame.setObjectName('timelineDataHeader')
        data_header_layout = QVBoxLayout(data_header_frame)
        data_header_layout.setContentsMargins(12, 10, 12, 10)
        data_header_layout.setSpacing(8)
        data_top_layout = QHBoxLayout()
        data_top_layout.setContentsMargins(0, 0, 0, 0)
        data_top_layout.setSpacing(8)
        data_header_layout.addLayout(data_top_layout)
        data_filter_content = QWidget()
        filter_layout = QHBoxLayout(data_filter_content)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(8)
        self.data_title = QLabel(self.translator.tr('timeline_data_section'))
        self.data_title.setFont(QFont(AppStyles.FONT_FAMILY, 12, QFont.Bold))
        text_primary = colors.get('TEXT_PRIMARY', '#2C3E50')
        self.data_title.setStyleSheet(f"color: {text_primary};")
        data_top_layout.addWidget(self.data_title)
        data_top_layout.addStretch()
        
        # Enhanced search and filter controls
        # General search
        self.search_label = QLabel(self.translator.tr('search'))
        self.search_label.setFont(QFont(AppStyles.FONT_FAMILY, 10))
        filter_layout.addWidget(self.search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translator.tr('search_placeholder'))
        self.search_input.setMinimumWidth(200)
        self.search_input.setMinimumHeight(32)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {input_bg};
                border: 2px solid {border_color};
                border-radius: 6px;
                padding: 4px 8px;
            }}
            QLineEdit:focus {{
                border: 2px solid {accent_color};
            }}
        """)
        self.search_input.textChanged.connect(self.on_search_changed)
        filter_layout.addWidget(self.search_input)
        
        # People filter
        self.people_label = QLabel(self.translator.tr('lbl_people', default='People:'))
        self.people_label.setFont(QFont(AppStyles.FONT_FAMILY, 10))
        filter_layout.addWidget(self.people_label)
        
        self.people_filter_combo = QComboBox()
        self.people_filter_combo.setEditable(True)
        self.people_filter_combo.setInsertPolicy(QComboBox.NoInsert)
        self.people_filter_combo.setMinimumWidth(180)
        self.people_filter_combo.setMinimumHeight(32)
        self.people_filter_combo.lineEdit().setPlaceholderText(self.translator.tr('filter_people_placeholder', default='All People'))
        self.people_filter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {input_bg};
                border: 2px solid {border_color};
                border-radius: 6px;
                padding: 4px 8px;
            }}
            QComboBox:hover {{
                border: 2px solid {accent_color};
            }}
        """)
        self.people_filter_combo.currentTextChanged.connect(self.on_people_filter_changed)
        filter_layout.addWidget(self.people_filter_combo)
        
        # Places filter
        self.places_label = QLabel(self.translator.tr('lbl_places', default='Places:'))
        self.places_label.setFont(QFont(AppStyles.FONT_FAMILY, 10))
        filter_layout.addWidget(self.places_label)
        
        self.places_filter_combo = QComboBox()
        self.places_filter_combo.setEditable(True)
        self.places_filter_combo.setInsertPolicy(QComboBox.NoInsert)
        self.places_filter_combo.setMinimumWidth(180)
        self.places_filter_combo.setMinimumHeight(32)
        self.places_filter_combo.lineEdit().setPlaceholderText(self.translator.tr('filter_places_placeholder', default='All Places'))
        self.places_filter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {input_bg};
                border: 2px solid {border_color};
                border-radius: 6px;
                padding: 4px 8px;
            }}
            QComboBox:hover {{
                border: 2px solid {accent_color};
            }}
        """)
        self.places_filter_combo.currentTextChanged.connect(self.on_places_filter_changed)
        filter_layout.addWidget(self.places_filter_combo)
        
        # Classification filter
        self.classification_label = QLabel(self.translator.tr('lbl_classification', default='Classification:'))
        self.classification_label.setFont(QFont(AppStyles.FONT_FAMILY, 10))
        filter_layout.addWidget(self.classification_label)
        
        self.classification_filter_combo = QComboBox()
        self.classification_filter_combo.setEditable(True)
        self.classification_filter_combo.setInsertPolicy(QComboBox.NoInsert)
        self.classification_filter_combo.setMinimumWidth(180)
        self.classification_filter_combo.setMinimumHeight(32)
        self.classification_filter_combo.lineEdit().setPlaceholderText(self.translator.tr('filter_classification_placeholder', default='All Classifications'))
        self.classification_filter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {input_bg};
                border: 2px solid {border_color};
                border-radius: 6px;
                padding: 4px 8px;
            }}
            QComboBox:hover {{
                border: 2px solid {accent_color};
            }}
        """)
        self.classification_filter_combo.currentTextChanged.connect(self.on_classification_filter_changed)
        filter_layout.addWidget(self.classification_filter_combo)
        
        # Clear filters button
        self.clear_search_btn = QPushButton()
        clear_search_btn = self.clear_search_btn
        clear_search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors.get('LIGHT_BG', '#F8F9FA')};
                border: 2px solid {border_color};
                border-radius: 6px;
                padding: 6px;
            }}
            QPushButton:hover {{
                background-color: {colors.get('BORDER', '#DEE2E6')};
            }}
        """)
        setup_icon_button(clear_search_btn, 'btn_clear',
                         self.translator.tr('btn_clear', default='Clear Filters'),
                         size=18)
        clear_search_btn.clicked.connect(self.clear_all_filters)
        filter_layout.addWidget(clear_search_btn)
        filter_layout.addStretch()
        
        self.filters_heading = QLabel(
            self.translator.tr('timeline_filters', default='Filters')
        )
        self.filters_heading.setObjectName('timelineFiltersHeading')
        data_header_layout.addWidget(self.filters_heading)
        filter_scroll = QScrollArea(data_header_frame)
        filter_scroll.setObjectName('timelineFilterScroller')
        filter_scroll.setWidgetResizable(False)
        filter_scroll.setFrameShape(QFrame.NoFrame)
        filter_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        filter_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        filter_scroll.setWidget(data_filter_content)
        filter_scroll.setMinimumHeight(54)
        filter_scroll.setMaximumHeight(72)
        data_header_layout.addWidget(filter_scroll)
        
        # Load filter options after UI is set up
        QTimer.singleShot(100, self.load_filter_options)
        
        # Print button (icon only)
        self.print_btn = QPushButton()
        self.print_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent_color};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {colors.get('ACCENT_HOVER', '#2980B9')};
            }}
        """)
        setup_icon_button(self.print_btn, 'btn_print', 
                        self.translator.tr('btn_print', default='Print'),
                        size=24, use_white_icon=True)
        self.print_btn.clicked.connect(self.print_timeline)
        data_top_layout.addWidget(self.print_btn)
        
        # Export button (icon only)
        self.export_btn = QPushButton()
        export_color = TimelineDesignSystem.get_color_with_contrast('#27AE60')
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {export_color};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {colors.get('SUCCESS_HOVER', '#229954')};
            }}
        """)
        setup_icon_button(self.export_btn, 'btn_export',
                        self.translator.tr('btn_export', default='Export'),
                        size=24, use_white_icon=True)
        self.export_btn.clicked.connect(self.export_timeline)
        data_top_layout.addWidget(self.export_btn)
        
        data_section_layout.addWidget(data_header_frame)
        
        # Timeline container with axis (8px grid spacing)
        self.timeline_wrapper = QWidget()
        timeline_wrapper = self.timeline_wrapper
        timeline_wrapper.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        timeline_wrapper_layout = QHBoxLayout(timeline_wrapper)
        timeline_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        timeline_wrapper_layout.setSpacing(0)
        
        self.timeline_axis = TimelineAxisWidget()
        timeline_wrapper_layout.addWidget(self.timeline_axis)
        
        scroll_bg = colors.get('LIGHT_BG', '#F5F6FA')
        self.timeline_container = QWidget()
        self.timeline_container.setStyleSheet(f"background-color: {scroll_bg};")
        self.timeline_layout = QVBoxLayout(self.timeline_container)
        # Use design system spacing
        timeline_margin = config['section_margin']
        timeline_spacing = config['card_spacing']
        self.timeline_layout.setContentsMargins(timeline_margin, timeline_margin,
                                               timeline_margin, timeline_margin)
        self.timeline_layout.setSpacing(timeline_spacing)
        self.empty_state_label = QLabel(self.translator.tr(
            'table_empty', default='No events match the current view.'
        ))
        self.empty_state_label.setObjectName('timelineEmptyState')
        self.empty_state_label.setAlignment(Qt.AlignCenter)
        self.empty_state_label.setWordWrap(True)
        self.empty_state_label.setMinimumHeight(64)
        self.empty_state_label.setStyleSheet(AppStyles.get_component_style('table_state'))
        self.empty_state_label.setVisible(False)
        self.timeline_layout.addWidget(self.empty_state_label)
        self.timeline_layout.addStretch()
        
        timeline_wrapper_layout.addWidget(self.timeline_container, 1)
        
        # Always use dedicated internal scroll area for data section with zoom support
        self.timeline_scroll = QScrollArea()
        self.timeline_scroll.setWidgetResizable(True)
        self.timeline_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.timeline_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Enhanced scrollbar styling for better visibility
        scrollbar_style = f"""
            QScrollArea {{
                border: 1px solid {border_color};
                border-radius: 8px;
                background-color: {scroll_bg};
            }}
            QScrollBar:vertical {{
                border: none;
                background: {colors.get('LIGHT_BG', '#F0F0F0')};
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
                background: {colors.get('ACCENT_HOVER', '#2980B9')};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """
        self.timeline_scroll.setStyleSheet(scrollbar_style)
        self.timeline_scroll.setWidget(timeline_wrapper)
        
        # Set minimum height for scroll area to ensure it's visible
        self.timeline_scroll.setMinimumHeight(400)
        
        data_section_layout.addWidget(self.timeline_scroll, 1)
        
        # Pagination widget for data section
        self.pagination = PaginationWidget(self.translator, self)
        self.pagination.page_changed.connect(self.on_page_changed)
        self.pagination.page_size_changed.connect(self.on_page_size_changed)
        data_section_layout.addWidget(self.pagination)
        
        # Status label with design system
        self.status_label = QLabel()
        self.status_label.setFont(QFont(AppStyles.FONT_FAMILY, 10, QFont.Bold))
        status_bg = colors.get('LIGHT_BG', '#ECF0F1')
        text_primary = colors.get('TEXT_PRIMARY', '#2C3E50')
        status_padding = TimelineDesignSystem.get_spacing(1)  # 8px
        self.status_label.setStyleSheet(f"""
            color: {text_primary};
            padding: {status_padding}px;
            background-color: {status_bg};
            border-radius: 6px;
        """)
        self.status_label.setObjectName('timelineStatusMessage')
        self.status_label.setVisible(False)
        data_section_layout.addWidget(self.status_label)
        
        # Add data section to splitter
        main_splitter.addWidget(data_section)
        
        # Set splitter proportions (charts: 40%, data: 60%)
        main_splitter.setSizes([400, 600])
        main_splitter.setStretchFactor(0, 0)  # Charts section fixed
        main_splitter.setStretchFactor(1, 1)  # Data section stretches
        
        layout.addWidget(main_splitter, 1)
    
    def load_events(self, events: List[Dict]):
        """Load events into timeline"""
        self.events = events
        # Reload filter options when new events are loaded
        self.load_filter_options()
        self.apply_filters()
    
    def apply_filters(self):
        """Apply date filters, search, people, places, classification filters, and sort order"""
        date_from = self.date_from.date().toPyDate() if self.date_from else None
        date_to = self.date_to.date().toPyDate() if self.date_to else None
        
        self._full_filtered_events = []
        for event in self.events:
            # Apply date filter
            event_date = self.get_event_date(event)
            if event_date:
                event_date_only = event_date.date() if isinstance(event_date, datetime) else event_date
                if date_from and event_date_only < date_from:
                    continue
                if date_to and event_date_only > date_to:
                    continue
            
            # Apply general search filter
            if self.search_text:
                if not self.matches_search(event, self.search_text):
                    continue
            
            # Apply people filter (handle comma-separated lists)
            if self.filter_people:
                people = event.get('list_names_people', '')
                if people:
                    # Split by comma and check each name
                    people_list = [p.strip().lower() for p in str(people).split(',')]
                    filter_lower = self.filter_people.lower()
                    if not any(filter_lower in person for person in people_list):
                        continue
                else:
                    continue
            
            # Apply places filter (handle comma-separated lists and source location)
            if self.filter_places:
                places = event.get('list_names_places', '')
                source_city = event.get('source_city', '')
                source_country = event.get('source_country', '')
                
                # Combine all place-related fields
                all_places = []
                if places:
                    all_places.extend([p.strip().lower() for p in str(places).split(',')])
                if source_city:
                    all_places.append(str(source_city).lower())
                if source_country:
                    all_places.append(str(source_country).lower())
                
                filter_lower = self.filter_places.lower()
                if not all_places or not any(filter_lower in place for place in all_places):
                    continue
            
            # Apply classification filter
            if self.filter_classification:
                classification = event.get('classification', '')
                if not classification or self.filter_classification.lower() not in str(classification).lower():
                    continue
            
            self._full_filtered_events.append(event)
        
        self.sort_events_full()
        
        # Update pagination
        if self.pagination:
            self.pagination.set_total_items(len(self._full_filtered_events))
            self.pagination.page_spin.setValue(1)
        
        # Apply pagination to get current page
        self.apply_pagination()
        
        # Update statistics and charts with ALL filtered events (independent from pagination)
        self.update_statistics()
        self.chart_widget.update_chart(self._full_filtered_events, self.current_chart_type)
        self.analysis_panel.update_analysis(self._full_filtered_events)
    
    def matches_search(self, event: Dict, search_text: str) -> bool:
        """Check if event matches search text"""
        if not search_text:
            return True
        
        search_lower = search_text.lower().strip()
        if not search_lower:
            return True
        
        # Search in specified fields
        for field in self.search_fields:
            value = event.get(field)
            if value:
                if search_lower in str(value).lower():
                    return True
        
        # Also search in source name and type
        if event.get('source_name'):
            if search_lower in str(event.get('source_name')).lower():
                return True
        
        return False
    
    def on_search_changed(self, text: str):
        """Handle search text change"""
        self.search_text = text
        # Debounce search with a timer
        if hasattr(self, '_search_timer'):
            self._search_timer.stop()
        else:
            self._search_timer = QTimer()
            self._search_timer.setSingleShot(True)
            self._search_timer.timeout.connect(self.apply_filters)
        
        # Wait 300ms after user stops typing before applying search
        self._search_timer.start(300)
    
    def clear_search(self):
        """Clear search input"""
        self.search_input.clear()
        self.search_text = ""
        self.apply_filters()
    
    def clear_all_filters(self):
        """Clear all search, date, and categorical filter inputs."""
        # Block intermediate signals so resetting several controls results in
        # one deterministic refresh rather than a cascade of partial queries.
        for control in (
            getattr(self, 'search_input', None),
            getattr(self, 'people_filter_combo', None),
            getattr(self, 'places_filter_combo', None),
            getattr(self, 'classification_filter_combo', None),
            getattr(self, 'date_from', None),
            getattr(self, 'date_to', None),
        ):
            if control is not None:
                control.blockSignals(True)

        try:
            self.search_input.clear()
            self.search_text = ""
            self.filter_people = ""
            self.filter_places = ""
            self.filter_classification = ""

            # Restore the same broad default date range used when the widget
            # is created.  This makes both clear-filter controls consistent.
            self.date_from.setDate(QDate.currentDate().addYears(-1))
            self.date_to.setDate(QDate.currentDate())

            for combo in (
                getattr(self, 'people_filter_combo', None),
                getattr(self, 'places_filter_combo', None),
                getattr(self, 'classification_filter_combo', None),
            ):
                if combo is not None:
                    combo.setCurrentIndex(0)
                    if combo.isEditable() and combo.lineEdit():
                        combo.lineEdit().clear()
        finally:
            for control in (
                getattr(self, 'search_input', None),
                getattr(self, 'people_filter_combo', None),
                getattr(self, 'places_filter_combo', None),
                getattr(self, 'classification_filter_combo', None),
                getattr(self, 'date_from', None),
                getattr(self, 'date_to', None),
            ):
                if control is not None:
                    control.blockSignals(False)

        self.apply_filters()
    
    def load_filter_options(self):
        """Load distinct values for filter combos from database"""
        try:
            from db.db_manager import DatabaseManager
            
            # Load people
            people_list = DatabaseManager.get_distinct_people()
            if hasattr(self, 'people_filter_combo'):
                self.people_filter_combo.clear()
                self.people_filter_combo.addItem("", "")  # Empty option for "All"
                for person in people_list:
                    self.people_filter_combo.addItem(person, person)
            
            # Load places
            places_list = DatabaseManager.get_distinct_places()
            if hasattr(self, 'places_filter_combo'):
                self.places_filter_combo.clear()
                self.places_filter_combo.addItem("", "")  # Empty option for "All"
                for place in places_list:
                    self.places_filter_combo.addItem(place, place)
            
            # Load classifications
            classifications_list = DatabaseManager.get_distinct_classifications()
            if hasattr(self, 'classification_filter_combo'):
                self.classification_filter_combo.clear()
                self.classification_filter_combo.addItem("", "")  # Empty option for "All"
                for classification in classifications_list:
                    self.classification_filter_combo.addItem(classification, classification)
        
        except Exception as e:
            logger.error(f"Error loading filter options: {e}")
    
    def on_people_filter_changed(self, text: str):
        """Handle people filter change"""
        self.filter_people = text.strip() if text else ""
        # Debounce with timer
        if hasattr(self, '_people_filter_timer'):
            self._people_filter_timer.stop()
        else:
            self._people_filter_timer = QTimer()
            self._people_filter_timer.setSingleShot(True)
            self._people_filter_timer.timeout.connect(self.apply_filters)
        self._people_filter_timer.start(300)
    
    def on_places_filter_changed(self, text: str):
        """Handle places filter change"""
        self.filter_places = text.strip() if text else ""
        # Debounce with timer
        if hasattr(self, '_places_filter_timer'):
            self._places_filter_timer.stop()
        else:
            self._places_filter_timer = QTimer()
            self._places_filter_timer.setSingleShot(True)
            self._places_filter_timer.timeout.connect(self.apply_filters)
        self._places_filter_timer.start(300)
    
    def on_classification_filter_changed(self, text: str):
        """Handle classification filter change"""
        self.filter_classification = text.strip() if text else ""
        # Debounce with timer
        if hasattr(self, '_classification_filter_timer'):
            self._classification_filter_timer.stop()
        else:
            self._classification_filter_timer = QTimer()
            self._classification_filter_timer.setSingleShot(True)
            self._classification_filter_timer.timeout.connect(self.apply_filters)
        self._classification_filter_timer.start(300)
    
    def on_sort_by_changed(self, index: int):
        """Handle sort by field change"""
        self.sort_by = self.sort_by_combo.currentData()
        self.sort_events_full()
        
        # Reset pagination to first page
        if self.pagination:
            self.pagination.page_spin.setValue(1)
        
        self.apply_pagination()
    
    def on_sort_order_changed(self, index: int):
        """Handle sort order change"""
        self.sort_order = self.sort_order_combo.currentData()
        self.sort_events_full()
        
        # Reset pagination to first page
        if self.pagination:
            self.pagination.page_spin.setValue(1)
        
        self.apply_pagination()
    
    def update_statistics(self):
        """Update statistics cards"""
        total = len(self.events)
        # Statistics describe the full filtered set, not only the visible
        # pagination page.
        statistics_events = self._full_filtered_events
        filtered = len(statistics_events)
        
        # Count sources and analyses
        sources_count = len(set(e.get('source_id') for e in statistics_events if e.get('source_id')))
        analyses_count = len([e for e in statistics_events if e.get('analysis_id')])
        
        # Update using the new update_value method
        self.total_card.update_value(f"{total:,}")
        self.filtered_card.update_value(f"{filtered:,}")
        self.sources_card.update_value(f"{sources_count:,}")
        self.analyses_card.update_value(f"{analyses_count:,}")
    
    def sort_events_full(self):
        """Sort all filtered events by selected criteria"""
        reverse = (self.sort_order == 'desc')
        
        if self.sort_by == 'date':
            def get_sort_key(event):
                event_date = self.get_event_date(event)
                if event_date:
                    return event_date if isinstance(event_date, datetime) else datetime.min
                return datetime.min
            self._full_filtered_events.sort(key=get_sort_key, reverse=reverse)
        
        elif self.sort_by == 'people':
            def get_sort_key(event):
                people = event.get('list_names_people', '')
                return str(people).lower() if people else 'zzz'
            self._full_filtered_events.sort(key=get_sort_key, reverse=reverse)
        
        elif self.sort_by == 'places':
            def get_sort_key(event):
                places = event.get('list_names_places', '')
                source_city = event.get('source_city', '')
                source_country = event.get('source_country', '')
                place_text = f"{places} {source_city} {source_country}".strip()
                return place_text.lower() if place_text else 'zzz'
            self._full_filtered_events.sort(key=get_sort_key, reverse=reverse)
        
        elif self.sort_by == 'classification':
            def get_sort_key(event):
                classification = event.get('classification', '')
                return str(classification).lower() if classification else 'zzz'
            self._full_filtered_events.sort(key=get_sort_key, reverse=reverse)
        
        elif self.sort_by == 'source':
            def get_sort_key(event):
                source_name = event.get('source_name', '')
                return str(source_name).lower() if source_name else 'zzz'
            self._full_filtered_events.sort(key=get_sort_key, reverse=reverse)
        
        else:
            # Default to date sorting
            def get_sort_key(event):
                event_date = self.get_event_date(event)
                if event_date:
                    return event_date if isinstance(event_date, datetime) else datetime.min
                return datetime.min
            self._full_filtered_events.sort(key=get_sort_key, reverse=reverse)
    
    def apply_pagination(self):
        """Apply pagination to display current page"""
        if not hasattr(self, '_full_filtered_events') or not self._full_filtered_events:
            self.filtered_events = []
            self.refresh_display()
            if hasattr(self, 'status_label'):
                self.status_label.setText(self.translator.tr('msg_ready', default='Ready'))
                self.status_label.setVisible(False)
            return
        
        if not self.pagination:
            # No pagination widget yet, show all
            self.filtered_events = self._full_filtered_events.copy()
            self.refresh_display()
            return
        
        start, end = self.pagination.get_page_range()
        self.filtered_events = self._full_filtered_events[start:end]
        self.refresh_display()
        
        # Pagination owns the result range. Keep the legacy status channel
        # available for future recoverable errors but quiet for normal pages.
        self.status_label.setText(self.translator.tr('msg_ready', default='Ready'))
        self.status_label.setVisible(False)
    
    def on_page_changed(self, page: int):
        """Handle page change"""
        self.apply_pagination()
    
    def on_page_size_changed(self, page_size: int):
        """Handle page size change"""
        self.pagination.page_spin.setValue(1)
        self.apply_pagination()
    
    def get_event_date(self, event: Dict) -> Optional[datetime]:
        """Get event date"""
        date_fields = ['date_content', 'date_analysis', 'date_entry', 
                      'date_creation', 'source_date_entry', 'content_date_creation']
        for field in date_fields:
            if field in event and event[field]:
                date_val = event[field]
                if isinstance(date_val, datetime):
                    return date_val
                elif isinstance(date_val, str):
                    try:
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']:
                            try:
                                return datetime.strptime(date_val[:19], fmt)
                            except:
                                continue
                    except:
                        pass
        return None
    
    def refresh_display(self):
        """Refresh timeline display with density mode - using pagination to prevent freezing"""
        config = TimelineDesignSystem.get_density_config(self.density_mode)
        
        # Apply zoom factor to spacing for better clarity
        zoomed_margin = int(config['section_margin'] * self.zoom_factor)
        zoomed_spacing = int(config['card_spacing'] * self.zoom_factor)
        
        # Update timeline container spacing with zoom
        self.timeline_layout.setContentsMargins(zoomed_margin, zoomed_margin,
                                               zoomed_margin, zoomed_margin)
        self.timeline_layout.setSpacing(zoomed_spacing)
        
        # Clear existing event cards while retaining the state label as the
        # first item. Rebuild the spacer after the page cards so it does not
        # push cards below an empty stretch on every refresh.
        while self.timeline_layout.count() > 1:
            item = self.timeline_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        if hasattr(self, 'empty_state_label'):
            self.empty_state_label.setVisible(not bool(self.filtered_events))
            self.empty_state_label.setText(self.translator.tr(
                'table_empty', default='No events match the current view.'
            ))
        self.timeline_layout.addStretch()
        
        # Create widgets only for current page (pagination prevents freezing)
        for event in self.filtered_events:
            event_widget = TimelineEventWidget(event, self.translator, self.density_mode, self)
            # Apply zoom to event widget for clearer display
            event_widget.apply_zoom(self.zoom_factor)
            event_widget.clicked.connect(self.on_event_clicked)
            self.timeline_layout.insertWidget(self.timeline_layout.count() - 1, event_widget)
        
        # Reflow after the page cards exist. Without an explicit content-size
        # pass, a resizable scroll area can squeeze every card into the
        # viewport and make a populated timeline look like empty rules.
        QTimer.singleShot(0, self._resize_timeline_content)
        QTimer.singleShot(100, self.update_axis_nodes)
    
    def _resize_timeline_content(self):
        """Give the internal scroll area enough height for the active page."""
        if not hasattr(self, 'timeline_layout') or not hasattr(self, 'timeline_container'):
            return
        self.timeline_layout.activate()
        desired_height = max(
            self.timeline_layout.sizeHint().height(),
            self.timeline_scroll.viewport().height() if hasattr(self, 'timeline_scroll') else 0,
        )
        self.timeline_container.setMinimumHeight(desired_height)
        self.timeline_container.updateGeometry()
        if hasattr(self, 'timeline_wrapper'):
            self.timeline_wrapper.setMinimumHeight(desired_height)
            self.timeline_wrapper.updateGeometry()
            self.timeline_wrapper.adjustSize()
        self.timeline_layout.activate()

    def update_axis_nodes(self):
        """Update visual axis nodes"""
        node_positions = []
        for i in range(self.timeline_layout.count() - 1):
            widget = self.timeline_layout.itemAt(i).widget()
            if isinstance(widget, TimelineEventWidget):
                widget_y = widget.y() + widget.height() // 2
                record_type = widget.event_data.get('record_type', 'content')
                if record_type == 'analysis':
                    node_color = "#9B59B6"
                    node_size = 12
                elif record_type == 'content':
                    node_color = "#3498DB"
                    node_size = 10
                else:
                    node_color = "#27AE60"
                    node_size = 8
                node_positions.append((widget_y, node_color, node_size))
        self.timeline_axis.set_node_positions(node_positions)
    
    def on_event_clicked(self, event_data: Dict):
        """Handle event click"""
        if self.selected_event:
            for i in range(self.timeline_layout.count() - 1):
                widget = self.timeline_layout.itemAt(i).widget()
                if isinstance(widget, TimelineEventWidget):
                    widget.set_selected(False)
        
        self.selected_event = event_data
        for i in range(self.timeline_layout.count() - 1):
            widget = self.timeline_layout.itemAt(i).widget()
            if isinstance(widget, TimelineEventWidget):
                if widget.event_data == event_data:
                    widget.set_selected(True)
                    break
        
        self.event_selected.emit(event_data)
    
    
    def clear_filters(self):
        """Clear all timeline filters."""
        self.clear_all_filters()
    
    def on_density_changed(self, mode: str):
        """Handle density mode change"""
        self.density_mode = mode
        self.config.set_timeline_density_mode(mode)
        
        # Update statistics cards
        for card in [self.total_card, self.filtered_card, self.sources_card, self.analyses_card]:
            card.set_density_mode(mode)
        
        # Update button styles
        self.update_density_button_styles()
        
        # Refresh display with new density
        self.refresh_display()
    
    def update_density_button_styles(self):
        """Update density button styles based on current mode"""
        colors = AppStyles.get_colors()
        accent_color = TimelineDesignSystem.get_color_with_contrast('#3498DB')
        input_bg = colors.get('INPUT_BG', '#FFFFFF')
        border_color = colors.get('BORDER', '#DEE2E6')
        text_primary = colors.get('TEXT_PRIMARY', '#2C3E50')
        
        density_modes = ['compact', 'comfortable', 'expansive']
        for i, btn in enumerate(self.density_buttons):
            mode_key = density_modes[i] if i < len(density_modes) else 'comfortable'
            is_active = mode_key == self.density_mode
            
            if is_active:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {accent_color};
                        color: #FFFFFF;
                        border: 2px solid {accent_color};
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {colors.get('ACCENT_HOVER', '#2980B9')};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {input_bg};
                        color: {text_primary};
                        border: 2px solid {border_color};
                        border-radius: 6px;
                        padding: 6px 12px;
                    }}
                    QPushButton:hover {{
                        border: 2px solid {accent_color};
                        background-color: {colors.get('LIGHT_BG', '#F8F9FA')};
                    }}
                """)
    
    def on_chart_type_changed(self, index: int):
        """Handle chart type change"""
        self.current_chart_type = self.chart_type_combo.currentData()
        if hasattr(self, 'chart_widget'):
            self.chart_widget.update_chart(self._full_filtered_events, self.current_chart_type)
    
    def set_scroll_enabled(self, enabled: bool):
        """Enable or disable internal scroll area (for unified scroll)"""
        self._internal_scroll_enabled = enabled
    
    def print_timeline(self):
        """Print timeline data with current formatting"""
        if not self._full_filtered_events:
            QMessageBox.warning(self, self.translator.tr('msg_no_data', default='No Data'),
                              self.translator.tr('msg_no_data', default='No data to print'))
            return
        
        try:
            from utils.print_utils import generate_timeline_print_html, get_print_settings, print_document_with_page_numbers
            from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
            
            # Get print settings
            settings = get_print_settings()
            
            # Generate HTML with timeline formatting
            html = generate_timeline_print_html(
                self._full_filtered_events, 
                self.translator,
                self.density_mode
            )
            
            # Setup printer
            printer = QPrinter(QPrinter.HighResolution)
            if settings.page_orientation == 'Landscape':
                printer.setOrientation(QPrinter.Landscape)
            else:
                printer.setOrientation(QPrinter.Portrait)
            
            # Print dialog
            print_dialog = QPrintDialog(printer, self)
            if print_dialog.exec_() == QPrintDialog.Accepted:
                from PyQt5.QtGui import QTextDocument
                doc = QTextDocument()
                doc.setHtml(html)
                print_document_with_page_numbers(doc, printer, settings)
                
        except Exception as e:
            logger.error(f"Error printing timeline: {e}")
            QMessageBox.critical(self, self.translator.tr('msg_error', default='Error'),
                               f"Error printing timeline: {str(e)}")
    
    def export_timeline(self):
        """Export timeline data with comprehensive export dialog"""
        from dialogs.timeline_export_dialog import TimelineExportDialog
        from utils.word_export import export_timeline_to_word
        from utils.excel_export import export_timeline_to_excel
        import subprocess
        import os
        
        # Open export dialog
        dialog = TimelineExportDialog(
            self,
            events=self.events,
            filtered_events=self._full_filtered_events,
            current_page_events=self.filtered_events,
            translator=self.translator
        )
        
        if dialog.exec_() != QDialog.Accepted:
            return
        
        # Get export settings
        settings = dialog.get_export_settings()
        events_to_export = settings['events']
        file_path = settings['file_path']
        export_format = settings['format']
        include_header = settings['include_header']
        preserve_format = settings['preserve_format']
        open_after = settings['open_after_export']
        
        if not events_to_export:
            QMessageBox.warning(
                self,
                self.translator.tr('msg_warning', default='Warning'),
                self.translator.tr('export_no_data', default='No data selected for export.')
            )
            return
        
        try:
            # Export based on format
            if export_format == TimelineExportDialog.FORMAT_WORD:
                export_timeline_to_word(
                    events_to_export,
                    file_path,
                    self.translator,
                    self.density_mode,
                    include_header=include_header,
                    preserve_format=preserve_format
                )
            elif export_format == TimelineExportDialog.FORMAT_EXCEL:
                export_timeline_to_excel(
                    events_to_export,
                    file_path,
                    self.translator,
                    self.density_mode,
                    include_header=include_header,
                    preserve_format=preserve_format
                )
            elif export_format == TimelineExportDialog.FORMAT_PDF:
                # PDF export using print HTML
                from utils.print_utils import generate_timeline_print_html, get_print_settings, print_document_with_page_numbers
                from PyQt5.QtPrintSupport import QPrinter
                from PyQt5.QtGui import QTextDocument
                
                html = generate_timeline_print_html(
                    events_to_export,
                    self.translator,
                    self.density_mode
                )
                
                settings = get_print_settings()
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)
                if settings.page_orientation == 'Landscape':
                    printer.setOrientation(QPrinter.Landscape)
                else:
                    printer.setOrientation(QPrinter.Portrait)
                
                doc = QTextDocument()
                doc.setHtml(html)
                print_document_with_page_numbers(doc, printer, settings)
            
            if not os.path.isfile(file_path) or os.path.getsize(file_path) == 0:
                raise IOError(f"Export did not create a valid output file: {file_path}")

            # Opening the exported file is optional; a viewer failure must not
            # be confused with an export failure.
            if open_after:
                try:
                    if sys.platform == 'win32':
                        os.startfile(file_path)
                    elif sys.platform == 'darwin':
                        subprocess.run(['open', file_path], check=True)
                    else:
                        subprocess.run(['xdg-open', file_path], check=True)
                except Exception as e:
                    logger.warning(f"Could not open file: {e}")
            
            QMessageBox.information(
                self,
                self.translator.tr('msg_success', default='Success'),
                self.translator.tr('export_success', default='Export completed successfully')
            )
            
        except Exception as e:
            logger.error(f"Error exporting timeline: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                self.translator.tr('msg_error', default='Error'),
                f"Error exporting timeline: {str(e)}"
            )
    
    def refresh_translations(self):
        """Refresh translations"""
        if hasattr(self, 'controls_heading'):
            self.controls_heading.setText(
                self.translator.tr('timeline_controls_title', default='View controls')
            )
        if hasattr(self, 'order_group'):
            self.order_group.setTitle(
                self.translator.tr('timeline_order_group', default='Order')
            )
        if hasattr(self, 'density_group'):
            self.density_group.setTitle(
                self.translator.tr('timeline_density_group', default='Density')
            )
        if hasattr(self, 'date_group'):
            self.date_group.setTitle(
                self.translator.tr('timeline_date_group', default='Date range')
            )
        if hasattr(self, 'sort_label'):
            self.sort_label.setText(self.translator.tr('timeline_sort'))
        if hasattr(self, 'density_label'):
            self.density_label.setText(self.translator.tr('timeline_density_mode'))
        if hasattr(self, 'from_label'):
            self.from_label.setText(self.translator.tr('timeline_from'))
        if hasattr(self, 'to_label'):
            self.to_label.setText(self.translator.tr('timeline_to'))
        if hasattr(self, 'chart_type_label'):
            self.chart_type_label.setText(self.translator.tr('timeline_chart_select'))
        if hasattr(self, 'data_title'):
            self.data_title.setText(self.translator.tr('timeline_data_section'))
        if hasattr(self, 'search_label'):
            self.search_label.setText(self.translator.tr('search'))
        if hasattr(self, 'people_label'):
            self.people_label.setText(self.translator.tr('lbl_people', default='People:'))
        if hasattr(self, 'places_label'):
            self.places_label.setText(self.translator.tr('lbl_places', default='Places:'))
        if hasattr(self, 'classification_label'):
            self.classification_label.setText(
                self.translator.tr('lbl_classification', default='Classification:')
            )
        if hasattr(self, 'filters_heading'):
            self.filters_heading.setText(
                self.translator.tr('timeline_filters', default='Filters')
            )
        for button_attr, translation_key, fallback in (
            ('clear_search_btn', 'btn_clear', 'Clear filters'),
            ('print_btn', 'btn_print', 'Print'),
            ('export_btn', 'btn_export', 'Export'),
        ):
            button = getattr(self, button_attr, None)
            if button:
                label = self.translator.tr(translation_key, default=fallback)
                button.setToolTip(label)
                button.setAccessibleName(label)
        if hasattr(self, 'sort_by_combo'):
            self.sort_by_combo.clear()
            self.sort_by_combo.addItem(self.translator.tr('timeline_sort_by_date', default='Date'), 'date')
            self.sort_by_combo.addItem(self.translator.tr('timeline_sort_by_people', default='People'), 'people')
            self.sort_by_combo.addItem(self.translator.tr('timeline_sort_by_places', default='Places'), 'places')
            self.sort_by_combo.addItem(self.translator.tr('timeline_sort_by_classification', default='Classification'), 'classification')
            self.sort_by_combo.addItem(self.translator.tr('timeline_sort_by_source', default='Source'), 'source')
        
        if hasattr(self, 'sort_order_combo'):
            self.sort_order_combo.clear()
            self.sort_order_combo.addItem(self.translator.tr('timeline_latest_first'), 'desc')
            self.sort_order_combo.addItem(self.translator.tr('timeline_chronological'), 'asc')
        
        # Update chart type combo
        if hasattr(self, 'chart_type_combo'):
            self.chart_type_combo.clear()
            self.chart_type_combo.addItem(self.translator.tr('timeline_chart_timeline'), 'timeline')
            self.chart_type_combo.addItem(self.translator.tr('timeline_chart_type_sort'), 'type_sort')
            self.chart_type_combo.addItem(self.translator.tr('timeline_chart_day_of_week'), 'day_of_week')
            self.chart_type_combo.addItem(self.translator.tr('timeline_chart_monthly'), 'monthly')
            self.chart_type_combo.addItem(self.translator.tr('timeline_chart_classification'), 'classification')
        
        # Update density button labels
        if hasattr(self, 'density_buttons'):
            density_modes = ['compact', 'comfortable', 'expansive']
            for i, btn in enumerate(self.density_buttons):
                if i < len(density_modes):
                    btn.setText(self.translator.tr(f'timeline_density_{density_modes[i]}'))
            self.update_density_button_styles()
        
        # Update statistics cards
        if hasattr(self, 'total_card'):
            self.total_card.set_title(self.translator.tr('timeline_stats_total'))
        if hasattr(self, 'filtered_card'):
            self.filtered_card.set_title(self.translator.tr('timeline_stats_filtered'))
        if hasattr(self, 'sources_card'):
            self.sources_card.set_title(self.translator.tr('timeline_stats_sources'))
        if hasattr(self, 'analyses_card'):
            self.analyses_card.set_title(self.translator.tr('timeline_stats_analyses'))
        
        # Update pagination translations
        if self.pagination:
            self.pagination.refresh_translations()
        
        # Refresh chart widget by updating current chart
        if hasattr(self, 'chart_widget') and hasattr(self, 'current_chart_type'):
            self.chart_widget.update_chart(self._full_filtered_events, self.current_chart_type)
        
        # Refresh analysis panel
        if hasattr(self, 'analysis_panel'):
            self.analysis_panel.update_analysis(self.filtered_events)
        
        self.refresh_display()
