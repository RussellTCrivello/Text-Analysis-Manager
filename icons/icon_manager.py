"""
Modern Icon Manager - Supports both file-based icons and programmatic fallback
Uses real SVG/PNG icons when available, falls back to programmatic drawing
"""
import sys
import os
from pathlib import Path
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath, QFont
from PyQt5.QtWidgets import QStyle, QApplication
from PyQt5.QtCore import Qt, QSize, QRect, QRectF, QPointF, QFileInfo, QByteArray

# Try to import QSvgRenderer, fall back if not available
try:
    from PyQt5.QtSvg import QSvgRenderer
    SVG_SUPPORT = True
except ImportError:
    SVG_SUPPORT = False
    QSvgRenderer = None


class IconFileManager:
    """Manages loading icons from files"""
    
    def __init__(self):
        # Get the icons directory - handle both development and packaged scenarios
        self.icons_dir = self._get_icons_directory()
        if self.icons_dir:
            self.icons_dir.mkdir(exist_ok=True)
    
    def _get_icons_directory(self) -> Path:
        """Get the icons directory path, handling packaged apps (single-file and folder)"""
        # Use path_utils for correct bundle path (handles _MEIPASS for single-file)
        try:
            from utils.path_utils import get_bundle_dir
            bundle_dir = get_bundle_dir()
            icons_dir = bundle_dir / "icons" / "images"
            if icons_dir.exists():
                return icons_dir
            # Fallback for different bundle structure
            alt_dir = bundle_dir / "images"
            if alt_dir.exists():
                return alt_dir
        except Exception:
            pass
        
        # Development: relative to this file
        local_dir = Path(__file__).resolve().parent / "images"
        if local_dir.exists():
            return local_dir
        
        # Last resort: cwd
        cwd_dir = Path.cwd() / "icons" / "images"
        if cwd_dir.exists():
            return cwd_dir
        
        return local_dir  # Default fallback
    
    def get_icon_path(self, icon_name: str) -> Path:
        """Get the path to an icon file"""
        if not self.icons_dir:
            return None
            
        # Try SVG first (vector, scalable)
        svg_path = self.icons_dir / f"{icon_name}.svg"
        if svg_path.exists():
            return svg_path
        
        # Try PNG
        png_path = self.icons_dir / f"{icon_name}.png"
        if png_path.exists():
            return png_path
        
        return None
    
    def load_icon_from_file(self, icon_name: str, size: int = 24, icon_color: str = '#2c3e50') -> QIcon:
        """Load an icon from file (SVG or PNG)
        
        Args:
            icon_name: Name of the icon file (without extension)
            size: Icon size in pixels
            icon_color: Color for SVG strokes (default dark blue-gray)
        """
        icon_path = self.get_icon_path(icon_name)
        
        if not icon_path:
            return QIcon()  # Return null icon
        
        file_path = str(icon_path)
        
        # Try SVG first (if SVG support is available)
        if icon_path.suffix.lower() == '.svg' and SVG_SUPPORT and QSvgRenderer:
            try:
                # Read SVG content and replace currentColor with actual color
                with open(file_path, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
                
                # Replace currentColor with the specified icon color
                svg_content = svg_content.replace('currentColor', icon_color)
                svg_content = svg_content.replace('stroke="none"', f'stroke="{icon_color}"')
                
                # Create renderer from modified SVG content
                svg_bytes = QByteArray(svg_content.encode('utf-8'))
                renderer = QSvgRenderer(svg_bytes)
                
                if renderer.isValid():
                    # Use device pixel ratio for high DPI displays
                    dpr = QApplication.instance().devicePixelRatio() if QApplication.instance() else 1.0
                    actual_size = int(size * dpr)
                    
                    pixmap = QPixmap(actual_size, actual_size)
                    pixmap.setDevicePixelRatio(dpr)
                    pixmap.fill(Qt.transparent)
                    
                    painter = QPainter(pixmap)
                    painter.setRenderHint(QPainter.Antialiasing, True)
                    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
                    renderer.render(painter)
                    painter.end()
                    
                    if not pixmap.isNull():
                        return QIcon(pixmap)
            except Exception as e:
                print(f"SVG loading error for {icon_name}: {e}")
        
        # Try PNG or other image formats
        try:
            icon = QIcon(file_path)
            if not icon.isNull():
                return icon
        except Exception as e:
            print(f"Image loading error for {icon_name}: {e}")
        
        return QIcon()  # Return null icon if loading failed


class ModernIconPainter:
    """Draws modern, professional icons programmatically (fallback)"""
    
    # Modern color palette
    COLORS = {
        'primary': QColor('#3498DB'),      # Blue
        'success': QColor('#27AE60'),      # Green
        'danger': QColor('#E74C3C'),       # Red
        'warning': QColor('#F39C12'),      # Orange
        'info': QColor('#9B59B6'),         # Purple
        'dark': QColor('#2C3E50'),         # Dark blue
        'white': QColor('#FFFFFF'),        # White
        'light': QColor('#95A5A6'),        # Light gray
        'excel': QColor('#217346'),        # Excel green
        'word': QColor('#2B579A'),         # Word blue
        'csv': QColor('#FF6F00'),          # CSV orange
    }
    
    # Thread-local storage for current drawing color
    _use_white = False
    
    @classmethod
    def get_color(cls, color_key: str = 'primary') -> QColor:
        """Get the appropriate color based on current icon mode
        
        For primary/default colors, returns white when use_white is set.
        For specific colors like danger, success, excel, word, etc., 
        returns the original color to maintain visual distinction.
        """
        # Colors that should stay the same regardless of background
        preserve_colors = {'danger', 'success', 'warning', 'excel', 'word', 'csv', 'info'}
        
        if cls._use_white and color_key not in preserve_colors:
            return cls.COLORS['white']
        return cls.COLORS.get(color_key, cls.COLORS['primary'])
    
    @classmethod
    def create_icon(cls, icon_name: str, size: int = 24, use_white: bool = False) -> QIcon:
        """Create a modern icon by name (fallback method)
        
        Args:
            icon_name: Name of the icon to draw
            size: Icon size in pixels
            use_white: If True, use white color for the icon
        """
        # Set the color mode for this icon
        cls._use_white = use_white
        
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        # Draw the appropriate icon
        draw_method = getattr(cls, f'draw_{icon_name}', None)
        if draw_method:
            draw_method(painter, size)
        
        painter.end()
        
        # Reset color mode
        cls._use_white = False
        
        return QIcon(pixmap)
    
    # Keep all the existing draw methods as fallback
    @staticmethod
    def draw_add(painter: QPainter, size: int):
        """Draw modern plus/add icon"""
        color = ModernIconPainter.COLORS['success']
        margin = size * 0.15
        center = size / 2
        line_length = size * 0.5
        thickness = size * 0.12
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QRectF(margin, margin, size - 2*margin, size - 2*margin))
        
        painter.setPen(QPen(ModernIconPainter.COLORS['white'], thickness, Qt.SolidLine, Qt.RoundCap))
        half_len = line_length / 2
        painter.drawLine(QPointF(center - half_len, center), QPointF(center + half_len, center))
        painter.drawLine(QPointF(center, center - half_len), QPointF(center, center + half_len))
    
    @staticmethod
    def draw_edit(painter: QPainter, size: int):
        """Draw modern pencil/edit icon - highly visible and prominent"""
        color = ModernIconPainter.get_color('primary')
        margin = size * 0.08
        center = size / 2
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        tip_x = margin + size * 0.12
        tip_y = size - margin - size * 0.1
        body_top_x = size - margin - size * 0.05
        body_top_y = margin + size * 0.12
        
        path = QPainterPath()
        path.moveTo(tip_x, tip_y)
        path.lineTo(tip_x + size * 0.22, tip_y - size * 0.22)
        path.lineTo(body_top_x, body_top_y)
        path.lineTo(body_top_x - size * 0.1, body_top_y - size * 0.1)
        path.lineTo(tip_x + size * 0.12, tip_y - size * 0.12)
        path.closeSubpath()
        
        painter.setPen(QPen(color.darker(110), size * 0.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(color.lighter(120)))
        painter.drawPath(path)
        
        tip_path = QPainterPath()
        tip_path.moveTo(tip_x, tip_y)
        tip_path.lineTo(tip_x + size * 0.2, tip_y - size * 0.02)
        tip_path.lineTo(tip_x + size * 0.04, tip_y - size * 0.2)
        tip_path.closeSubpath()
        
        tip_color = QColor('#FF8C00')
        painter.setPen(QPen(tip_color, size * 0.08, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(tip_color))
        painter.drawPath(tip_path)
    
    @staticmethod
    def draw_delete(painter: QPainter, size: int):
        """Draw modern trash/delete icon"""
        color = ModernIconPainter.get_color('danger')
        margin = size * 0.08
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(color, size * 0.08, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        body_top = size * 0.25
        body_bottom = size - margin
        body_left = margin + size * 0.08
        body_right = size - margin - size * 0.08
        
        path = QPainterPath()
        path.moveTo(body_left, body_top)
        path.lineTo(body_left + size * 0.08, body_bottom - size * 0.12)
        path.quadTo(body_left + size * 0.08, body_bottom, (body_left + body_right) / 2, body_bottom)
        path.quadTo(body_right - size * 0.08, body_bottom, body_right - size * 0.08, body_bottom - size * 0.12)
        path.lineTo(body_right, body_top)
        path.closeSubpath()
        
        painter.setPen(QPen(color.darker(120), size * 0.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(color.lighter(130)))
        painter.drawPath(path)
        
        lid_y = body_top - size * 0.02
        lid_thickness = size * 0.08
        painter.setBrush(QBrush(color))
        painter.drawRect(QRectF(margin, lid_y - lid_thickness/2, size - 2*margin, lid_thickness))
        
        handle_width = size * 0.32
        handle_center = size / 2
        handle_top = lid_y - size * 0.18
        
        handle_path = QPainterPath()
        handle_path.moveTo(handle_center - handle_width/2, lid_y)
        handle_path.lineTo(handle_center - handle_width/2, handle_top)
        handle_path.quadTo(handle_center - handle_width/2, handle_top - size * 0.04, handle_center, handle_top - size * 0.04)
        handle_path.quadTo(handle_center + handle_width/2, handle_top - size * 0.04, handle_center + handle_width/2, handle_top)
        handle_path.lineTo(handle_center + handle_width/2, lid_y)
        handle_path.closeSubpath()
        
        painter.setPen(QPen(color.darker(140), size * 0.08, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(color.darker(120)))
        painter.drawPath(handle_path)
    
    @staticmethod
    def draw_refresh(painter: QPainter, size: int):
        """Draw modern refresh/update icon"""
        color = ModernIconPainter.get_color('primary')
        margin = size * 0.12
        center = size / 2
        radius = (size - 2 * margin) / 2
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(color.darker(110), size * 0.15, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        
        rect = QRectF(margin, margin, size - 2*margin, size - 2*margin)
        painter.drawArc(rect, 25 * 16, 280 * 16)
        
        arrow_x = center + radius * 0.6
        arrow_y = margin + size * 0.1
        arrow_size = size * 0.25
        
        painter.setPen(QPen(color.darker(120), size * 0.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(color.darker(120)))
        arrow = QPainterPath()
        arrow.moveTo(arrow_x, arrow_y)
        arrow.lineTo(arrow_x + arrow_size * 0.8, arrow_y - arrow_size * 0.6)
        arrow.lineTo(arrow_x - arrow_size * 0.2, arrow_y - arrow_size * 0.6)
        arrow.closeSubpath()
        painter.drawPath(arrow)
    
    @staticmethod
    def draw_clear(painter: QPainter, size: int):
        """Draw modern clear icon"""
        color = ModernIconPainter.COLORS['warning']
        margin = size * 0.08
        center = size / 2
        radius = size * 0.42
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(color.darker(120), size * 0.08, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(center, center), radius, radius)
        
        x_size = radius * 0.7
        x_thickness = size * 0.16
        painter.setPen(QPen(ModernIconPainter.COLORS['white'], x_thickness, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(center - x_size, center - x_size), QPointF(center + x_size, center + x_size))
        painter.drawLine(QPointF(center + x_size, center - x_size), QPointF(center - x_size, center + x_size))
    
    @staticmethod
    def draw_export(painter: QPainter, size: int):
        """Draw modern unified export icon"""
        color = ModernIconPainter.COLORS['info']
        margin = size * 0.08
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        box_width = size * 0.75
        box_height = size * 0.55
        box_x = (size - box_width) / 2
        box_y = size - margin - box_height
        
        painter.setPen(QPen(color.darker(120), size * 0.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(color.lighter(140)))
        
        path = QPainterPath()
        path.moveTo(box_x, box_y + size * 0.15)
        path.lineTo(box_x, box_y + box_height)
        path.lineTo(box_x + box_width, box_y + box_height)
        path.lineTo(box_x + box_width, box_y + size * 0.15)
        path.closeSubpath()
        painter.drawPath(path)
        
        arrow_center = size / 2
        arrow_base = box_y + size * 0.12
        arrow_top = margin + size * 0.06
        arrow_width = size * 0.3
        
        painter.setPen(QPen(color.darker(140), size * 0.12, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(arrow_center, arrow_base), QPointF(arrow_center, arrow_top + size * 0.15))
        
        painter.setBrush(QBrush(color.darker(140)))
        arrow_head = QPainterPath()
        arrow_head.moveTo(arrow_center, arrow_top)
        arrow_head.lineTo(arrow_center - arrow_width, arrow_top + size * 0.22)
        arrow_head.lineTo(arrow_center + arrow_width, arrow_top + size * 0.22)
        arrow_head.closeSubpath()
        painter.drawPath(arrow_head)
    
    # Add stub methods for other icons (can be expanded)
    @staticmethod
    def draw_save(painter: QPainter, size: int):
        ModernIconPainter.draw_add(painter, size)  # Fallback
    
    @staticmethod
    def draw_cancel(painter: QPainter, size: int):
        ModernIconPainter.draw_clear(painter, size)
    
    @staticmethod
    def draw_ok(painter: QPainter, size: int):
        color = ModernIconPainter.COLORS['success']
        margin = size * 0.15
        center = size / 2
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QRectF(margin, margin, size - 2*margin, size - 2*margin))
        painter.setPen(QPen(ModernIconPainter.COLORS['white'], size * 0.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        check_start = QPointF(center - size * 0.2, center)
        check_mid = QPointF(center - size * 0.05, center + size * 0.15)
        check_end = QPointF(center + size * 0.22, center - size * 0.15)
        path = QPainterPath()
        path.moveTo(check_start)
        path.lineTo(check_mid)
        path.lineTo(check_end)
        painter.drawPath(path)
    
    # Export format-specific icons
    @staticmethod
    def draw_export_csv(painter: QPainter, size: int):
        """Draw CSV icon - table/grid representation"""
        color = ModernIconPainter.COLORS['csv']  # Orange
        margin = size * 0.12
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw table/grid
        box_width = size * 0.7
        box_height = size * 0.6
        box_x = (size - box_width) / 2
        box_y = margin
        
        # Table border
        painter.setPen(QPen(color.darker(120), size * 0.08, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(color.lighter(150)))
        painter.drawRect(QRectF(box_x, box_y, box_width, box_height))
        
        # Grid lines (rows)
        line_spacing = box_height / 3
        painter.setPen(QPen(color.darker(140), size * 0.06, Qt.SolidLine))
        for i in range(1, 3):
            y = box_y + line_spacing * i
            painter.drawLine(QPointF(box_x, y), QPointF(box_x + box_width, y))
        
        # Grid lines (columns)
        col_spacing = box_width / 3
        for i in range(1, 3):
            x = box_x + col_spacing * i
            painter.drawLine(QPointF(x, box_y), QPointF(x, box_y + box_height))
    
    @staticmethod
    def draw_export_excel(painter: QPainter, size: int):
        """Draw Excel icon - spreadsheet with cells"""
        color = ModernIconPainter.COLORS['excel']  # Excel green
        margin = size * 0.12
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw spreadsheet
        box_width = size * 0.7
        box_height = size * 0.6
        box_x = (size - box_width) / 2
        box_y = margin
        
        # Spreadsheet border
        painter.setPen(QPen(color.darker(120), size * 0.08, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(color.lighter(150)))
        painter.drawRect(QRectF(box_x, box_y, box_width, box_height))
        
        # Grid lines (more cells for spreadsheet look)
        row_spacing = box_height / 4
        col_spacing = box_width / 4
        painter.setPen(QPen(color.darker(140), size * 0.05, Qt.SolidLine))
        
        # Rows
        for i in range(1, 4):
            y = box_y + row_spacing * i
            painter.drawLine(QPointF(box_x, y), QPointF(box_x + box_width, y))
        
        # Columns
        for i in range(1, 4):
            x = box_x + col_spacing * i
            painter.drawLine(QPointF(x, box_y), QPointF(x, box_y + box_height))
    
    @staticmethod
    def draw_export_word(painter: QPainter, size: int):
        """Draw Word icon - document with text lines"""
        color = ModernIconPainter.COLORS['word']  # Word blue
        margin = size * 0.12
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw document
        box_width = size * 0.65
        box_height = size * 0.7
        box_x = (size - box_width) / 2
        box_y = margin
        
        # Document border
        painter.setPen(QPen(color.darker(120), size * 0.08, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(color.lighter(150)))
        painter.drawRect(QRectF(box_x, box_y, box_width, box_height))
        
        # Text lines
        line_spacing = box_height / 5
        line_width = box_width * 0.7
        line_x = box_x + (box_width - line_width) / 2
        painter.setPen(QPen(color.darker(140), size * 0.08, Qt.SolidLine, Qt.RoundCap))
        
        for i in range(3):
            y = box_y + line_spacing * (i + 1.5)
            painter.drawLine(QPointF(line_x, y), QPointF(line_x + line_width, y))
    
    @staticmethod
    def draw_export_pdf(painter: QPainter, size: int):
        """Draw PDF icon - document file"""
        color = ModernIconPainter.get_color('danger')  # Red for PDF
        margin = size * 0.12
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw document
        box_width = size * 0.65
        box_height = size * 0.7
        box_x = (size - box_width) / 2
        box_y = margin
        
        # Document border
        painter.setPen(QPen(color.darker(120), size * 0.08, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(color.lighter(150)))
        painter.drawRect(QRectF(box_x, box_y, box_width, box_height))
        
        # PDF text indicator (simplified "PDF" representation)
        # Draw a small rectangle in corner to represent PDF badge
        badge_size = size * 0.2
        badge_x = box_x + box_width - badge_size - size * 0.05
        badge_y = box_y + size * 0.05
        
        painter.setPen(QPen(color.darker(150), size * 0.06, Qt.SolidLine))
        painter.setBrush(QBrush(color))
        painter.drawRect(QRectF(badge_x, badge_y, badge_size, badge_size * 0.6))
        
        # Small lines to represent text
        line_spacing = box_height / 6
        line_width = box_width * 0.5
        line_x = box_x + (box_width - line_width) / 2
        painter.setPen(QPen(color.darker(140), size * 0.06, Qt.SolidLine, Qt.RoundCap))
        
        for i in range(2):
            y = box_y + line_spacing * (i + 2)
            painter.drawLine(QPointF(line_x, y), QPointF(line_x + line_width, y))
    
    @staticmethod
    def draw_print(painter: QPainter, size: int):
        ModernIconPainter.draw_export(painter, size)
    
    @staticmethod
    def draw_preview(painter: QPainter, size: int):
        ModernIconPainter.draw_export(painter, size)
    
    @staticmethod
    def draw_close(painter: QPainter, size: int):
        ModernIconPainter.draw_clear(painter, size)
    
    @staticmethod
    def draw_remove(painter: QPainter, size: int):
        ModernIconPainter.draw_delete(painter, size)
    
    @staticmethod
    def draw_delete_backup(painter: QPainter, size: int):
        ModernIconPainter.draw_delete(painter, size)
    
    @staticmethod
    def draw_reset(painter: QPainter, size: int):
        ModernIconPainter.draw_clear(painter, size)
    
    @staticmethod
    def draw_add_new(painter: QPainter, size: int):
        ModernIconPainter.draw_add(painter, size)
    
    @staticmethod
    def draw_restore(painter: QPainter, size: int):
        ModernIconPainter.draw_refresh(painter, size)
    
    @staticmethod
    def draw_restore_from_file(painter: QPainter, size: int):
        ModernIconPainter.draw_refresh(painter, size)
    
    @staticmethod
    def draw_set_header(painter: QPainter, size: int):
        ModernIconPainter.draw_export(painter, size)
    
    @staticmethod
    def draw_format(painter: QPainter, size: int):
        ModernIconPainter.draw_export(painter, size)
    
    @staticmethod
    def draw_validate(painter: QPainter, size: int):
        ModernIconPainter.draw_ok(painter, size)
    
    @staticmethod
    def draw_reports(painter: QPainter, size: int):
        ModernIconPainter.draw_export(painter, size)
    
    @classmethod
    def draw_import_data(cls, painter: QPainter, size: int):
        """Draw import/download icon - arrow pointing down into tray"""
        color = cls.get_color('primary')
        margin = size * 0.15
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(color, size * 0.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        center_x = size / 2
        
        # Draw down arrow
        arrow_top = margin
        arrow_bottom = size * 0.6
        arrow_width = size * 0.25
        
        # Arrow shaft
        painter.drawLine(QPointF(center_x, arrow_top), QPointF(center_x, arrow_bottom))
        # Arrow head
        painter.drawLine(QPointF(center_x - arrow_width, arrow_bottom - arrow_width), 
                        QPointF(center_x, arrow_bottom))
        painter.drawLine(QPointF(center_x + arrow_width, arrow_bottom - arrow_width), 
                        QPointF(center_x, arrow_bottom))
        
        # Draw tray/container at bottom
        tray_top = size * 0.7
        tray_bottom = size - margin
        painter.drawLine(QPointF(margin, tray_top), QPointF(margin, tray_bottom))
        painter.drawLine(QPointF(margin, tray_bottom), QPointF(size - margin, tray_bottom))
        painter.drawLine(QPointF(size - margin, tray_bottom), QPointF(size - margin, tray_top))
    
    @staticmethod
    def draw_duplicate(painter: QPainter, size: int):
        ModernIconPainter.draw_add(painter, size)
    
    @staticmethod
    def draw_statistics(painter: QPainter, size: int):
        ModernIconPainter.draw_export(painter, size)
    
    @classmethod
    def draw_attach_files(cls, painter: QPainter, size: int):
        """Draw paperclip/attachment icon"""
        color = cls.get_color('primary')
        margin = size * 0.15
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(color, size * 0.08, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Draw a simple paperclip using lines (more reliable than QPainterPath arcs)
        center_x = size / 2
        
        # Outer loop
        x1, y1 = center_x - size * 0.15, size * 0.75
        x2, y2 = center_x - size * 0.15, size * 0.25
        x3, y3 = center_x + size * 0.15, size * 0.25
        x4, y4 = center_x + size * 0.15, size * 0.65
        x5, y5 = center_x - size * 0.05, size * 0.65
        x6, y6 = center_x - size * 0.05, size * 0.35
        
        # Draw the paperclip shape
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        painter.drawLine(QPointF(x2, y2), QPointF(x3, y3))
        painter.drawLine(QPointF(x3, y3), QPointF(x4, y4))
        painter.drawLine(QPointF(x4, y4), QPointF(x5, y5))
        painter.drawLine(QPointF(x5, y5), QPointF(x6, y6))
    
    @staticmethod
    def draw_select_all(painter: QPainter, size: int):
        ModernIconPainter.draw_add(painter, size)
    
    @staticmethod
    def draw_deselect_all(painter: QPainter, size: int):
        ModernIconPainter.draw_clear(painter, size)
    
    @staticmethod
    def draw_create_backup(painter: QPainter, size: int):
        ModernIconPainter.draw_save(painter, size)
    
    @staticmethod
    def draw_link_analysis(painter: QPainter, size: int):
        ModernIconPainter.draw_export(painter, size)
    
    @staticmethod
    def draw_map(painter: QPainter, size: int):
        ModernIconPainter.draw_export(painter, size)
    
    @staticmethod
    def draw_compare(painter: QPainter, size: int):
        ModernIconPainter.draw_refresh(painter, size)
    
    @staticmethod
    def draw_summary(painter: QPainter, size: int):
        ModernIconPainter.draw_export(painter, size)
    
    @staticmethod
    def draw_quick_view(painter: QPainter, size: int):
        ModernIconPainter.draw_preview(painter, size)
    
    @staticmethod
    def draw_generate_report(painter: QPainter, size: int):
        ModernIconPainter.draw_export(painter, size)
    
    @staticmethod
    def draw_print_preview(painter: QPainter, size: int):
        ModernIconPainter.draw_preview(painter, size)
    
    # Pagination navigation icons
    @staticmethod
    def draw_page_first(painter: QPainter, size: int):
        """Draw first page icon (double left arrow)"""
        color = ModernIconPainter.get_color('primary')
        margin = size * 0.2
        center_y = size / 2
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(color, size * 0.12, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        # First arrow
        arrow1_x = margin + size * 0.15
        painter.drawLine(QPointF(arrow1_x + size * 0.2, margin + size * 0.1), 
                        QPointF(arrow1_x, center_y))
        painter.drawLine(QPointF(arrow1_x, center_y), 
                        QPointF(arrow1_x + size * 0.2, size - margin - size * 0.1))
        
        # Second arrow
        arrow2_x = margin + size * 0.4
        painter.drawLine(QPointF(arrow2_x + size * 0.2, margin + size * 0.1), 
                        QPointF(arrow2_x, center_y))
        painter.drawLine(QPointF(arrow2_x, center_y), 
                        QPointF(arrow2_x + size * 0.2, size - margin - size * 0.1))
    
    @staticmethod
    def draw_page_prev(painter: QPainter, size: int):
        """Draw previous page icon (single left arrow)"""
        color = ModernIconPainter.get_color('primary')
        margin = size * 0.25
        center_x = size / 2
        center_y = size / 2
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(color, size * 0.12, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        # Single arrow pointing left
        arrow_width = size * 0.25
        painter.drawLine(QPointF(center_x + arrow_width * 0.5, margin), 
                        QPointF(center_x - arrow_width * 0.5, center_y))
        painter.drawLine(QPointF(center_x - arrow_width * 0.5, center_y), 
                        QPointF(center_x + arrow_width * 0.5, size - margin))
    
    @staticmethod
    def draw_page_next(painter: QPainter, size: int):
        """Draw next page icon (single right arrow)"""
        color = ModernIconPainter.get_color('primary')
        margin = size * 0.25
        center_x = size / 2
        center_y = size / 2
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(color, size * 0.12, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        # Single arrow pointing right
        arrow_width = size * 0.25
        painter.drawLine(QPointF(center_x - arrow_width * 0.5, margin), 
                        QPointF(center_x + arrow_width * 0.5, center_y))
        painter.drawLine(QPointF(center_x + arrow_width * 0.5, center_y), 
                        QPointF(center_x - arrow_width * 0.5, size - margin))
    
    @staticmethod
    def draw_page_last(painter: QPainter, size: int):
        """Draw last page icon (double right arrow)"""
        color = ModernIconPainter.get_color('primary')
        margin = size * 0.2
        center_y = size / 2
        
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(color, size * 0.12, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        # First arrow
        arrow1_x = margin + size * 0.15
        painter.drawLine(QPointF(arrow1_x, margin + size * 0.1), 
                        QPointF(arrow1_x + size * 0.2, center_y))
        painter.drawLine(QPointF(arrow1_x + size * 0.2, center_y), 
                        QPointF(arrow1_x, size - margin - size * 0.1))
        
        # Second arrow
        arrow2_x = margin + size * 0.4
        painter.drawLine(QPointF(arrow2_x, margin + size * 0.1), 
                        QPointF(arrow2_x + size * 0.2, center_y))
        painter.drawLine(QPointF(arrow2_x + size * 0.2, center_y), 
                        QPointF(arrow2_x, size - margin - size * 0.1))


# Icon name to draw method mapping
# Maps button names to icon file names (without extension)
# Icons will be loaded from icons/images/ folder first, then fall back to programmatic drawing
ICON_NAME_MAP = {
    # CRUD buttons
    'btn_add': 'add',
    'btn_add_new': 'add',  # Use 'add' icon (add_new.svg doesn't exist)
    'btn_edit': 'edit',
    'btn_delete': 'delete',
    'btn_remove': 'delete',  # Use 'delete' icon (remove.svg doesn't exist)
    'btn_delete_backup': 'delete',  # Use 'delete' icon
    'btn_refresh': 'refresh',
    
    # Export buttons
    'btn_export': 'export',
    'btn_export_csv': 'export_csv',
    'btn_export_excel': 'export_excel',
    'btn_export_word': 'export_word',
    'btn_export_pdf': 'export_pdf',
    
    # Action buttons
    'btn_clear': 'clear',
    'btn_reset': 'clear',  # Use 'clear' icon (reset.svg doesn't exist)
    'btn_save': 'save',
    'btn_cancel': 'cancel',
    'btn_ok': 'ok',
    'btn_close': 'close',
    'btn_preview': 'preview',
    'btn_print': 'print',
    'btn_print_preview': 'print_preview',
    
    # File/Attachment buttons - Now with distinctive icons
    'btn_attach_files': 'attach_files',
    'btn_attachments': 'attach_files',
    'btn_attachment_add': 'attachment_add',
    'btn_attachment_remove': 'attachment_remove',
    'btn_attachment_open': 'attachment_open',
    'btn_attachment_folder': 'attachment_folder',
    'btn_attachment_download': 'attachment_download',
    
    # File type icons
    'file_pdf': 'file_pdf',
    'file_word': 'file_word',
    'file_excel': 'file_excel',
    'file_powerpoint': 'file_powerpoint',
    'file_image': 'file_image',
    'file_video': 'file_video',
    'file_audio': 'file_audio',
    'file_archive': 'file_archive',
    'file_text': 'file_text',
    'file_code': 'file_code',
    'file_generic': 'file_generic',
    
    # Selection buttons
    'btn_select_all': 'select_all',
    'btn_deselect_all': 'deselect_all',
    
    # Backup/Restore buttons
    'btn_create_backup': 'create_backup',
    'btn_restore': 'restore',
    'btn_merge': 'import_data',  # Use import icon for merge (adding data)
    'btn_restore_from_file': 'restore',  # Use 'restore' icon
    
    # Settings/Format buttons
    'btn_set_header': 'set_header',
    'btn_format': 'format',
    'btn_validate': 'validate',
    
    # Report/Data buttons
    'btn_reports': 'reports',
    'btn_import': 'import_data',
    'btn_duplicate': 'duplicate',
    'btn_statistics': 'statistics',
    'btn_link_analysis': 'link_analysis',
    'btn_map': 'map',
    'btn_compare': 'compare',
    'btn_summary': 'summary',
    'btn_quick_view': 'quick_view',
    'btn_generate_report': 'generate_report',
    
    # Pagination navigation icons
    'btn_page_first': 'page_first',
    'btn_page_prev': 'page_prev',
    'btn_page_next': 'page_next',
    'btn_page_last': 'page_last',
    
    # Additional common button names (aliases)
    'btn_browse': 'import_data',
    'btn_next': 'page_next',
    'btn_back': 'page_prev',
    'btn_import_contents': 'import_data',
    'btn_import_sources': 'import_data',
    'btn_import_analysis': 'import_data',
    'btn_duplicate_content': 'duplicate',
    'btn_duplicate_analysis': 'duplicate',
    'btn_view_attachments': 'attach_files',
    'btn_preview_content': 'preview',
    'btn_view_map': 'map',
    'btn_execute': 'ok',
}

# File extension to icon mapping for attachment display
FILE_TYPE_ICONS = {
    # PDF
    '.pdf': 'file_pdf',
    
    # Microsoft Word
    '.doc': 'file_word',
    '.docx': 'file_word',
    '.odt': 'file_word',
    '.rtf': 'file_word',
    
    # Microsoft Excel
    '.xls': 'file_excel',
    '.xlsx': 'file_excel',
    '.ods': 'file_excel',
    '.csv': 'file_excel',
    
    # Microsoft PowerPoint
    '.ppt': 'file_powerpoint',
    '.pptx': 'file_powerpoint',
    '.odp': 'file_powerpoint',
    
    # Images
    '.jpg': 'file_image',
    '.jpeg': 'file_image',
    '.png': 'file_image',
    '.gif': 'file_image',
    '.bmp': 'file_image',
    '.webp': 'file_image',
    '.svg': 'file_image',
    '.ico': 'file_image',
    '.tiff': 'file_image',
    '.tif': 'file_image',
    
    # Videos
    '.mp4': 'file_video',
    '.avi': 'file_video',
    '.mkv': 'file_video',
    '.mov': 'file_video',
    '.wmv': 'file_video',
    '.flv': 'file_video',
    '.webm': 'file_video',
    '.m4v': 'file_video',
    
    # Audio
    '.mp3': 'file_audio',
    '.wav': 'file_audio',
    '.flac': 'file_audio',
    '.aac': 'file_audio',
    '.ogg': 'file_audio',
    '.wma': 'file_audio',
    '.m4a': 'file_audio',
    
    # Archives
    '.zip': 'file_archive',
    '.rar': 'file_archive',
    '.7z': 'file_archive',
    '.tar': 'file_archive',
    '.gz': 'file_archive',
    '.bz2': 'file_archive',
    
    # Text files
    '.txt': 'file_text',
    '.log': 'file_text',
    '.md': 'file_text',
    '.ini': 'file_text',
    '.cfg': 'file_text',
    
    # Code files
    '.py': 'file_code',
    '.js': 'file_code',
    '.ts': 'file_code',
    '.html': 'file_code',
    '.css': 'file_code',
    '.json': 'file_code',
    '.xml': 'file_code',
    '.sql': 'file_code',
    '.java': 'file_code',
    '.cpp': 'file_code',
    '.c': 'file_code',
    '.h': 'file_code',
    '.go': 'file_code',
    '.rs': 'file_code',
    '.php': 'file_code',
    '.rb': 'file_code',
    '.swift': 'file_code',
    '.kt': 'file_code',
}


def get_file_type_icon(extension: str, size: int = 32) -> QIcon:
    """
    Get an icon for a file type based on its extension.
    
    Args:
        extension: File extension (e.g., '.pdf', '.docx')
        size: Icon size in pixels
        
    Returns:
        QIcon for the file type
    """
    ext_lower = extension.lower()
    icon_name = FILE_TYPE_ICONS.get(ext_lower, 'file_generic')
    
    # Try to load from file first
    file_icon = _file_manager.load_icon_from_file(icon_name, size)
    if not file_icon.isNull():
        return file_icon
    
    # Fall back to programmatic icon
    return ModernIconPainter.create_icon(icon_name, size)

# Global file manager instance
_file_manager = IconFileManager()


def get_icon(button_name: str, size: int = 24, use_white: bool = False) -> QIcon:
    """
    Get icon for a button name - tries file-based icons first, falls back to programmatic
    
    Args:
        button_name: Name of the button (e.g., 'btn_add')
        size: Icon size in pixels
        use_white: If True, use white colored icons (for colored backgrounds)
        
    Returns:
        QIcon object
    """
    icon_name = ICON_NAME_MAP.get(button_name, button_name.replace('btn_', ''))
    
    # Determine icon color
    icon_color = '#FFFFFF' if use_white else '#2c3e50'
    
    # Try to load from file first
    file_icon = _file_manager.load_icon_from_file(icon_name, size, icon_color)
    if not file_icon.isNull():
        return file_icon
    
    # Fall back to programmatic drawing
    prog_icon = ModernIconPainter.create_icon(icon_name, size, use_white)
    if not prog_icon.isNull():
        return prog_icon
    
    # Ultimate fallback: try generic icon based on action type
    fallback_map = {
        'add': 'add', 'new': 'add', 'create': 'add',
        'edit': 'edit', 'update': 'edit', 'modify': 'edit',
        'delete': 'delete', 'remove': 'delete', 'trash': 'delete',
        'refresh': 'refresh', 'reload': 'refresh', 'sync': 'refresh',
        'save': 'ok', 'confirm': 'ok', 'apply': 'ok',
        'cancel': 'clear', 'close': 'clear', 'reset': 'clear',
        'export': 'export', 'download': 'export',
        'import': 'export', 'upload': 'export',
        'print': 'export', 'preview': 'export',
    }
    
    for keyword, fallback_icon in fallback_map.items():
        if keyword in icon_name.lower():
            return ModernIconPainter.create_icon(fallback_icon, size, use_white)
    
    # Default: return a generic icon
    return ModernIconPainter.create_icon('export', size, use_white)


def setup_icon_button(button, button_name: str, tooltip_text: str, size: int = 26, use_white_icon: bool = False):
    """
    Setup a QPushButton with modern icon and tooltip
    
    Args:
        button: QPushButton instance to configure
        button_name: Name of the button (e.g., 'btn_add')
        tooltip_text: Tooltip text to show on hover
        size: Icon size in pixels (default 26 for better visibility)
        use_white_icon: If True, use white colored icons (for colored backgrounds)
    """
    from PyQt5.QtWidgets import QSizePolicy
    
    # Check if button has a colored background style that needs white icons
    style_sheet = button.styleSheet()
    needs_white = use_white_icon or any(color in style_sheet.lower() for color in 
                                        ['#3498db', '#2ecc71', '#e74c3c', '#9b59b6', '#e67e22',
                                         'background-color: rgb', 'background: rgb'])
    
    icon = get_icon(button_name, size, use_white=needs_white)
    
    if not icon.isNull():
        button.setIcon(icon)
        button.setIconSize(QSize(size, size))
        button.setText("")  # Remove text for minimal icon-only design
        button.setProperty("iconOnly", True)  # For margin styling to prevent overlap
        button.setVisible(True)
    else:
        # If no icon, keep text as fallback
        if not button.text():
            button.setText(tooltip_text)
        button.setVisible(True)
    
    button.setToolTip(tooltip_text)
    
    # Set size policy to Fixed to prevent buttons from causing layout changes
    button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    
    # Set fixed size for consistent button appearance - extra padding prevents icon cropping
    button_size = size + 14  # Padding around icon (7px each side) to prevent cropping/overlap
    button.setFixedSize(button_size, button_size)
