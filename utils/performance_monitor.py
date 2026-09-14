"""
Performance Monitoring System
Provides query optimization indicators, performance tracking, and suggestions
"""
import time
import functools
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict
import threading
import json
from pathlib import Path
import sys

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QProgressBar, QGroupBox, QTextEdit

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QueryMetrics:
    """Stores metrics for a database query"""
    query: str
    table_name: str
    execution_time_ms: float
    row_count: int
    timestamp: datetime
    parameters: Optional[str] = None
    
    @property
    def is_slow(self) -> bool:
        """Check if query is considered slow (>500ms)"""
        return self.execution_time_ms > 500
    
    @property
    def is_very_slow(self) -> bool:
        """Check if query is very slow (>2000ms)"""
        return self.execution_time_ms > 2000


@dataclass
class PerformanceStats:
    """Aggregated performance statistics"""
    total_queries: int = 0
    total_time_ms: float = 0
    slow_queries: int = 0
    very_slow_queries: int = 0
    avg_time_ms: float = 0
    max_time_ms: float = 0
    queries_by_table: Dict[str, int] = field(default_factory=dict)
    time_by_table: Dict[str, float] = field(default_factory=dict)


class PerformanceMonitor(QObject):
    """Monitors application performance and provides optimization suggestions"""
    
    performance_alert = pyqtSignal(str, str)  # (alert_type, message)
    stats_updated = pyqtSignal(object)  # PerformanceStats
    
    _instance: Optional['PerformanceMonitor'] = None
    
    # Performance thresholds (in milliseconds)
    SLOW_QUERY_THRESHOLD = 500
    VERY_SLOW_QUERY_THRESHOLD = 2000
    HIGH_QUERY_COUNT_THRESHOLD = 100  # per minute
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        
        self._metrics: List[QueryMetrics] = []
        self._lock = threading.Lock()
        self._stats = PerformanceStats()
        
        # Setup periodic stats calculation
        self._stats_timer = QTimer()
        self._stats_timer.timeout.connect(self._calculate_stats)
        self._stats_timer.start(30000)  # Every 30 seconds
        
        # Setup log file - use path_utils for correct path when installed
        from utils.path_utils import get_logs_dir
        self._log_dir = get_logs_dir()
        self._perf_log = self._log_dir / "performance.log"
    
    def record_query(self, query: str, table_name: str, 
                    execution_time_ms: float, row_count: int = 0,
                    parameters: Optional[str] = None):
        """Record a query execution"""
        metric = QueryMetrics(
            query=query[:500],  # Truncate long queries
            table_name=table_name,
            execution_time_ms=execution_time_ms,
            row_count=row_count,
            timestamp=datetime.now(),
            parameters=parameters[:200] if parameters else None
        )
        
        with self._lock:
            self._metrics.append(metric)
            
            # Keep only last 1000 metrics
            if len(self._metrics) > 1000:
                self._metrics = self._metrics[-1000:]
        
        # Check for alerts
        if metric.is_very_slow:
            self.performance_alert.emit(
                "slow_query",
                f"Very slow query detected ({execution_time_ms:.0f}ms) on table: {table_name}"
            )
            logger.warning(f"Very slow query: {query[:100]}... ({execution_time_ms:.0f}ms)")
        elif metric.is_slow:
            logger.info(f"Slow query: {query[:100]}... ({execution_time_ms:.0f}ms)")
        
        # Log to file
        self._log_metric(metric)
    
    def _log_metric(self, metric: QueryMetrics):
        """Log metric to file"""
        try:
            log_entry = {
                'timestamp': metric.timestamp.isoformat(),
                'table': metric.table_name,
                'time_ms': metric.execution_time_ms,
                'rows': metric.row_count,
                'query': metric.query[:200]
            }
            with open(self._perf_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Error logging performance metric: {e}")
    
    def _calculate_stats(self):
        """Calculate aggregated statistics"""
        with self._lock:
            if not self._metrics:
                return
            
            # Filter to last 5 minutes
            cutoff = datetime.now().timestamp() - 300
            recent_metrics = [m for m in self._metrics 
                           if m.timestamp.timestamp() > cutoff]
            
            if not recent_metrics:
                return
            
            stats = PerformanceStats()
            stats.total_queries = len(recent_metrics)
            stats.total_time_ms = sum(m.execution_time_ms for m in recent_metrics)
            stats.slow_queries = sum(1 for m in recent_metrics if m.is_slow)
            stats.very_slow_queries = sum(1 for m in recent_metrics if m.is_very_slow)
            stats.avg_time_ms = stats.total_time_ms / stats.total_queries
            stats.max_time_ms = max(m.execution_time_ms for m in recent_metrics)
            
            # Group by table
            for m in recent_metrics:
                stats.queries_by_table[m.table_name] = \
                    stats.queries_by_table.get(m.table_name, 0) + 1
                stats.time_by_table[m.table_name] = \
                    stats.time_by_table.get(m.table_name, 0) + m.execution_time_ms
            
            self._stats = stats
            self.stats_updated.emit(stats)
            
            # Check for high query volume
            if stats.total_queries > self.HIGH_QUERY_COUNT_THRESHOLD:
                self.performance_alert.emit(
                    "high_volume",
                    f"High query volume: {stats.total_queries} queries in last 5 minutes"
                )
    
    def get_stats(self) -> PerformanceStats:
        """Get current performance statistics"""
        return self._stats
    
    def get_recent_slow_queries(self, limit: int = 10) -> List[QueryMetrics]:
        """Get recent slow queries"""
        with self._lock:
            slow = [m for m in self._metrics if m.is_slow]
            return sorted(slow, key=lambda x: x.execution_time_ms, reverse=True)[:limit]
    
    def get_optimization_suggestions(self) -> List[Dict[str, str]]:
        """Generate optimization suggestions based on metrics"""
        suggestions = []
        
        stats = self._stats
        if not stats.total_queries:
            return suggestions
        
        # Check for slow queries
        if stats.slow_queries > 0:
            slow_pct = (stats.slow_queries / stats.total_queries) * 100
            if slow_pct > 10:
                suggestions.append({
                    'severity': 'warning',
                    'title': 'High Percentage of Slow Queries',
                    'description': f'{slow_pct:.1f}% of queries are taking more than {self.SLOW_QUERY_THRESHOLD}ms',
                    'suggestion': 'Consider adding indexes on frequently queried columns'
                })
        
        # Check for very slow queries
        if stats.very_slow_queries > 0:
            suggestions.append({
                'severity': 'error',
                'title': 'Very Slow Queries Detected',
                'description': f'{stats.very_slow_queries} queries took more than {self.VERY_SLOW_QUERY_THRESHOLD}ms',
                'suggestion': 'Review these queries for optimization opportunities'
            })
        
        # Check for high average time
        if stats.avg_time_ms > 200:
            suggestions.append({
                'severity': 'info',
                'title': 'Average Query Time is High',
                'description': f'Average query time: {stats.avg_time_ms:.1f}ms',
                'suggestion': 'Consider implementing caching for frequently accessed data'
            })
        
        # Check tables with high query count
        for table, count in stats.queries_by_table.items():
            if count > 50:  # More than 50 queries in 5 minutes
                avg_time = stats.time_by_table.get(table, 0) / count
                suggestions.append({
                    'severity': 'info',
                    'title': f'High Query Volume on {table}',
                    'description': f'{count} queries with avg time {avg_time:.1f}ms',
                    'suggestion': f'Consider caching {table} data or optimizing access patterns'
                })
        
        # Index suggestions based on slow queries
        slow_queries = self.get_recent_slow_queries(5)
        for query in slow_queries:
            if 'WHERE' in query.query.upper() and 'SELECT' in query.query.upper():
                # Extract potential columns that might need indexes
                suggestions.append({
                    'severity': 'warning',
                    'title': f'Potential Index Needed on {query.table_name}',
                    'description': f'Query taking {query.execution_time_ms:.0f}ms',
                    'suggestion': 'Add index on columns used in WHERE clause'
                })
        
        return suggestions
    
    def clear_metrics(self):
        """Clear all recorded metrics"""
        with self._lock:
            self._metrics.clear()
            self._stats = PerformanceStats()


class PerformanceDialog(QDialog):
    """Dialog showing performance metrics and suggestions"""
    
    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.translator = translator
        self.monitor = get_performance_monitor()
        
        self.setWindowTitle(self._tr('performance_title', 'Performance Monitor'))
        # Apply fixed size to prevent resizing on button clicks or content changes
        from styles.styles import AppStyles
        AppStyles.apply_fixed_size(self, 800, 600)
        self.setup_ui()
        self.refresh_data()
    
    def _tr(self, key: str, default: str) -> str:
        """Translate text"""
        if self.translator and hasattr(self.translator, 'tr'):
            result = self.translator.tr(key)
            return result if result != key else default
        return default
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Stats overview
        stats_group = QGroupBox(self._tr('performance_stats', 'Performance Statistics'))
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel()
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        
        # Performance indicators
        indicators_layout = QHBoxLayout()
        
        self.avg_time_bar = QProgressBar()
        self.avg_time_bar.setMaximum(1000)
        self.avg_time_bar.setFormat("Avg Time: %v ms")
        indicators_layout.addWidget(QLabel(self._tr('perf_avg_query_time', 'Avg Query Time') + ":"))
        indicators_layout.addWidget(self.avg_time_bar)
        
        self.slow_queries_bar = QProgressBar()
        self.slow_queries_bar.setMaximum(100)
        self.slow_queries_bar.setFormat("%v% slow")
        indicators_layout.addWidget(QLabel(self._tr('perf_slow_queries', 'Slow Queries') + ":"))
        indicators_layout.addWidget(self.slow_queries_bar)
        
        stats_layout.addLayout(indicators_layout)
        layout.addWidget(stats_group)
        
        # Slow queries table
        queries_group = QGroupBox(self._tr('performance_slow_queries', 'Recent Slow Queries'))
        queries_layout = QVBoxLayout(queries_group)
        
        self.queries_table = QTableWidget()
        self.queries_table.setColumnCount(4)
        self.queries_table.setHorizontalHeaderLabels([
            self._tr('perf_col_table', 'Table'),
            self._tr('perf_col_time', 'Time (ms)'),
            self._tr('perf_col_rows', 'Rows'),
            self._tr('perf_col_query', 'Query')
        ])
        self.queries_table.horizontalHeader().setStretchLastSection(True)
        queries_layout.addWidget(self.queries_table)
        
        layout.addWidget(queries_group)
        
        # Optimization suggestions
        suggestions_group = QGroupBox(self._tr('performance_suggestions', 'Optimization Suggestions'))
        suggestions_layout = QVBoxLayout(suggestions_group)
        
        self.suggestions_text = QTextEdit()
        self.suggestions_text.setReadOnly(True)
        suggestions_layout.addWidget(self.suggestions_text)
        
        layout.addWidget(suggestions_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_refresh = QPushButton(self._tr('btn_refresh', 'Refresh'))
        btn_refresh.clicked.connect(self.refresh_data)
        btn_layout.addWidget(btn_refresh)
        
        btn_clear = QPushButton(self._tr('btn_clear', 'Clear Metrics'))
        btn_clear.clicked.connect(self.clear_metrics)
        btn_layout.addWidget(btn_clear)
        
        btn_layout.addStretch()
        
        btn_close = QPushButton(self._tr('btn_close', 'Close'))
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
    
    def refresh_data(self):
        """Refresh performance data"""
        stats = self.monitor.get_stats()
        
        # Update stats label
        self.stats_label.setText(f"""
            <b>Total Queries (last 5 min):</b> {stats.total_queries}<br>
            <b>Total Time:</b> {stats.total_time_ms:.0f} ms<br>
            <b>Average Time:</b> {stats.avg_time_ms:.1f} ms<br>
            <b>Max Time:</b> {stats.max_time_ms:.0f} ms<br>
            <b>Slow Queries:</b> {stats.slow_queries}<br>
            <b>Very Slow Queries:</b> {stats.very_slow_queries}
        """)
        
        # Update progress bars
        self.avg_time_bar.setValue(min(int(stats.avg_time_ms), 1000))
        if stats.total_queries > 0:
            slow_pct = int((stats.slow_queries / stats.total_queries) * 100)
            self.slow_queries_bar.setValue(slow_pct)
        else:
            self.slow_queries_bar.setValue(0)
        
        # Update slow queries table
        slow_queries = self.monitor.get_recent_slow_queries(20)
        self.queries_table.setRowCount(len(slow_queries))
        
        for i, q in enumerate(slow_queries):
            self.queries_table.setItem(i, 0, QTableWidgetItem(q.table_name))
            self.queries_table.setItem(i, 1, QTableWidgetItem(f"{q.execution_time_ms:.0f}"))
            self.queries_table.setItem(i, 2, QTableWidgetItem(str(q.row_count)))
            self.queries_table.setItem(i, 3, QTableWidgetItem(q.query[:100]))
        
        # Update suggestions
        suggestions = self.monitor.get_optimization_suggestions()
        suggestions_html = ""
        
        for s in suggestions:
            color = {'error': '#E74C3C', 'warning': '#F39C12', 'info': '#3498DB'}.get(s['severity'], '#333')
            suggestions_html += f"""
                <div style="margin-bottom: 10px; padding: 10px; border-left: 3px solid {color};">
                    <b style="color: {color};">{s['title']}</b><br>
                    {s['description']}<br>
                    <i>Suggestion: {s['suggestion']}</i>
                </div>
            """
        
        if not suggestions_html:
            suggestions_html = "<p style='color: #27AE60;'>✓ No optimization issues detected</p>"
        
        self.suggestions_text.setHtml(suggestions_html)
    
    def clear_metrics(self):
        """Clear performance metrics"""
        self.monitor.clear_metrics()
        self.refresh_data()


def track_performance(table_name: str = "unknown"):
    """Decorator to track function performance"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed_ms = (time.time() - start) * 1000
            
            # Record the metric
            monitor = get_performance_monitor()
            
            # Try to get row count if result is a list
            row_count = len(result) if isinstance(result, (list, tuple)) else 0
            
            monitor.record_query(
                query=func.__name__,
                table_name=table_name,
                execution_time_ms=elapsed_ms,
                row_count=row_count
            )
            
            return result
        return wrapper
    return decorator


# Global instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor
