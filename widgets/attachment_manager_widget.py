"""
Enhanced Attachment Manager Widget
Full UI for managing multiple attachments with folder organization
"""
import os
from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QDialog, QFrame, QMenu, QAction, QSplitter, QGroupBox,
    QProgressBar, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QMimeData, QUrl
from PyQt5.QtGui import QIcon, QDragEnterEvent, QDropEvent, QPixmap, QPainter, QColor, QFont, QPen, QBrush
from translations.translations import TranslationManager
from utils.attachment_manager import get_attachment_manager, AttachmentManager
from icons.icon_manager import setup_icon_button, get_icon, get_file_type_icon
from utils.logger import get_logger
from styles.styles import AppStyles

logger = get_logger(__name__)


class AttachmentListItem(QListWidgetItem):
    """Custom list item for attachments with file info"""
    
    def __init__(self, file_path: str, attachment_manager: AttachmentManager):
        super().__init__()
        self.file_path = file_path
        self.attachment_manager = attachment_manager
        
        # Get file info
        info = attachment_manager.get_attachment_info(file_path)
        self.file_info = info
        
        # Set display text
        display_text = f"{info['name']}\n{info['size_str']}"
        self.setText(display_text)
        
        # Set icon based on file type
        self.setIcon(self._get_file_icon(info['extension']))
        
        # Store path as data
        self.setData(Qt.UserRole, file_path)
        
        # Set tooltip
        if info['modified']:
            tooltip = f"Path: {file_path}\nSize: {info['size_str']}\nModified: {info['modified'].strftime('%Y-%m-%d %H:%M')}"
        else:
            tooltip = f"Path: {file_path}\nFile not found"
        self.setToolTip(tooltip)
    
    def _get_file_icon(self, extension: str) -> QIcon:
        """Get icon based on file extension - uses distinctive SVG icons"""
        # Try to get the SVG icon first
        icon = get_file_type_icon(extension, 32)
        if not icon.isNull():
            return icon
        
        # Fallback to programmatic icon with enhanced styling
        size = 32
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Enhanced color palette with gradients
        colors = {
            # PDF - Red
            '.pdf': (QColor('#E74C3C'), QColor('#C0392B')),
            # Word - Blue
            '.doc': (QColor('#2B579A'), QColor('#1E3A5F')),
            '.docx': (QColor('#2B579A'), QColor('#1E3A5F')),
            '.odt': (QColor('#2B579A'), QColor('#1E3A5F')),
            '.rtf': (QColor('#2B579A'), QColor('#1E3A5F')),
            # Excel - Green
            '.xls': (QColor('#217346'), QColor('#165232')),
            '.xlsx': (QColor('#217346'), QColor('#165232')),
            '.ods': (QColor('#217346'), QColor('#165232')),
            '.csv': (QColor('#217346'), QColor('#165232')),
            # PowerPoint - Orange-Red
            '.ppt': (QColor('#D24726'), QColor('#A83B1E')),
            '.pptx': (QColor('#D24726'), QColor('#A83B1E')),
            '.odp': (QColor('#D24726'), QColor('#A83B1E')),
            # Images - Purple
            '.jpg': (QColor('#9B59B6'), QColor('#7D3C98')),
            '.jpeg': (QColor('#9B59B6'), QColor('#7D3C98')),
            '.png': (QColor('#9B59B6'), QColor('#7D3C98')),
            '.gif': (QColor('#9B59B6'), QColor('#7D3C98')),
            '.bmp': (QColor('#9B59B6'), QColor('#7D3C98')),
            '.webp': (QColor('#9B59B6'), QColor('#7D3C98')),
            '.svg': (QColor('#9B59B6'), QColor('#7D3C98')),
            # Videos - Orange
            '.mp4': (QColor('#E67E22'), QColor('#D35400')),
            '.avi': (QColor('#E67E22'), QColor('#D35400')),
            '.mkv': (QColor('#E67E22'), QColor('#D35400')),
            '.mov': (QColor('#E67E22'), QColor('#D35400')),
            '.webm': (QColor('#E67E22'), QColor('#D35400')),
            # Audio - Teal
            '.mp3': (QColor('#1ABC9C'), QColor('#16A085')),
            '.wav': (QColor('#1ABC9C'), QColor('#16A085')),
            '.flac': (QColor('#1ABC9C'), QColor('#16A085')),
            '.aac': (QColor('#1ABC9C'), QColor('#16A085')),
            '.ogg': (QColor('#1ABC9C'), QColor('#16A085')),
            # Archives - Yellow-Orange
            '.zip': (QColor('#F39C12'), QColor('#D68910')),
            '.rar': (QColor('#F39C12'), QColor('#D68910')),
            '.7z': (QColor('#F39C12'), QColor('#D68910')),
            '.tar': (QColor('#F39C12'), QColor('#D68910')),
            '.gz': (QColor('#F39C12'), QColor('#D68910')),
            # Text files - Gray
            '.txt': (QColor('#7F8C8D'), QColor('#5D6D7E')),
            '.log': (QColor('#7F8C8D'), QColor('#5D6D7E')),
            '.md': (QColor('#7F8C8D'), QColor('#5D6D7E')),
            # Code files - Purple
            '.py': (QColor('#8E44AD'), QColor('#6C3483')),
            '.js': (QColor('#F1C40F'), QColor('#D4AC0D')),
            '.html': (QColor('#E44D26'), QColor('#C43D1A')),
            '.css': (QColor('#264DE4'), QColor('#1E3EB8')),
            '.json': (QColor('#5D6D7E'), QColor('#4A5568')),
        }
        
        color_pair = colors.get(extension.lower(), (QColor('#3498DB'), QColor('#2980B9')))
        main_color, darker_color = color_pair
        
        # Draw rounded rectangle with gradient-like effect
        from PyQt5.QtGui import QLinearGradient
        from PyQt5.QtCore import QRectF
        
        rect = QRectF(2, 2, size - 4, size - 4)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, main_color.lighter(110))
        gradient.setColorAt(1, darker_color)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(darker_color.darker(120), 1))
        painter.drawRoundedRect(rect, 6, 6)
        
        # Draw extension text with shadow
        font = QFont('Arial', 7, QFont.Bold)
        painter.setFont(font)
        
        ext_text = extension[1:4].upper() if extension else '?'
        
        # Text shadow
        painter.setPen(QColor(0, 0, 0, 80))
        shadow_rect = pixmap.rect()
        shadow_rect.translate(1, 1)
        painter.drawText(shadow_rect, Qt.AlignCenter, ext_text)
        
        # Main text
        painter.setPen(QColor('#FFFFFF'))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, ext_text)
        
        painter.end()
        return QIcon(pixmap)


class AttachmentManagerWidget(QWidget):
    """
    Enhanced widget for managing file attachments.
    Supports drag-and-drop, multiple selection, and organized folder structure.
    """
    
    # Signals
    attachments_changed = pyqtSignal(list)  # Emits list of file paths
    attachment_opened = pyqtSignal(str)     # Emits path of opened file
    
    def __init__(self, parent=None, translator: TranslationManager = None,
                 source_name: str = "", allow_multiple: bool = True):
        super().__init__(parent)
        self.translator = translator
        self.source_name = source_name
        self.allow_multiple = allow_multiple
        self.attachment_manager = get_attachment_manager()
        self.file_paths = []
        
        self.setAcceptDrops(True)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the attachment manager UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Header with count
        header_layout = QHBoxLayout()
        btn_spacing = AppStyles.get_spacing(3) if (self.translator and self.translator.current_language == 'ar') else AppStyles.get_spacing(1)
        header_layout.setSpacing(btn_spacing)
        
        self.title_label = QLabel(self._tr('lbl_attachments'))
        self.title_label.setStyleSheet(AppStyles.get_component_style('attachment_manager_title'))
        
        self.count_label = QLabel("(0)")
        self.count_label.setStyleSheet(AppStyles.get_component_style('attachment_manager_count'))
        
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.count_label)
        header_layout.addStretch()
        
        # Action buttons with distinctive attachment-specific icons
        self.btn_add = QPushButton()
        setup_icon_button(self.btn_add, 'btn_attachment_add', self._tr('btn_add_attachment'))
        self.btn_add.clicked.connect(self.add_attachments)
        self.btn_add.setStyleSheet(self._get_attachment_button_style('add'))
        
        self.btn_remove = QPushButton()
        setup_icon_button(self.btn_remove, 'btn_attachment_remove', self._tr('btn_remove_attachment'))
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_remove.setEnabled(False)
        self.btn_remove.setStyleSheet(self._get_attachment_button_style('remove'))
        
        self.btn_open = QPushButton()
        setup_icon_button(self.btn_open, 'btn_attachment_open', self._tr('btn_open_attachment'))
        self.btn_open.clicked.connect(self.open_selected)
        self.btn_open.setEnabled(False)
        self.btn_open.setStyleSheet(self._get_attachment_button_style('open'))
        
        self.btn_folder = QPushButton()
        setup_icon_button(self.btn_folder, 'btn_attachment_folder', self._tr('btn_open_folder'))
        self.btn_folder.clicked.connect(self.open_folder)
        self.btn_folder.setStyleSheet(self._get_attachment_button_style('folder'))
        
        header_layout.addWidget(self.btn_add)
        header_layout.addWidget(self.btn_remove)
        header_layout.addWidget(self.btn_open)
        header_layout.addWidget(self.btn_folder)
        
        layout.addLayout(header_layout)
        
        # Attachment list
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(
            QListWidget.ExtendedSelection if self.allow_multiple else QListWidget.SingleSelection
        )
        self.list_widget.setIconSize(QSize(32, 32))
        self.list_widget.setSpacing(2)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        # Drag and drop hint
        self.list_widget.setStyleSheet(AppStyles.get_component_style('attachment_list'))
        
        layout.addWidget(self.list_widget)
        
        # Drop hint label (shown when empty)
        self.drop_hint = QLabel(self._tr('msg_drop_files_here'))
        self.drop_hint.setAlignment(Qt.AlignCenter)
        self.drop_hint.setStyleSheet(AppStyles.get_component_style('drop_hint'))
        
        # Status bar
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(AppStyles.get_component_style('status_label_muted'))
        layout.addWidget(self.status_label)
        
        # Show drop hint initially
        self.update_display()
    
    def _tr(self, key: str) -> str:
        """Get translation"""
        if self.translator:
            return self.translator.tr(key)
        # Fallback translations
        fallbacks = {
            'lbl_attachments': 'Attachments',
            'btn_add_attachment': 'Add Files',
            'btn_remove_attachment': 'Remove',
            'btn_open_attachment': 'Open',
            'btn_open_folder': 'Open Folder',
            'msg_drop_files_here': 'Drag and drop files here or click Add',
            'msg_files_attached': '{count} file(s) attached',
            'msg_confirm_remove': 'Remove selected attachment(s)?',
            'msg_warning': 'Warning',
            'msg_error': 'Error',
            'msg_no_selection': 'No file selected',
        }
        return fallbacks.get(key, key)
    
    def _get_attachment_button_style(self, button_type: str) -> str:
        """Get distinctive button style based on button type"""
        colors = {
            'add': {'bg': '#27AE60', 'hover': '#2ECC71', 'pressed': '#1E8449'},
            'remove': {'bg': '#E74C3C', 'hover': '#EC7063', 'pressed': '#C0392B'},
            'open': {'bg': '#3498DB', 'hover': '#5DADE2', 'pressed': '#2980B9'},
            'folder': {'bg': '#F39C12', 'hover': '#F5B041', 'pressed': '#D68910'},
            'download': {'bg': '#9B59B6', 'hover': '#AF7AC5', 'pressed': '#7D3C98'},
        }
        
        c = colors.get(button_type, colors['open'])
        
        return f"""
            QPushButton {{
                background-color: {c['bg']};
                border: none;
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {c['hover']};
            }}
            QPushButton:pressed {{
                background-color: {c['pressed']};
            }}
            QPushButton:disabled {{
                background-color: #BDC3C7;
                opacity: 0.6;
            }}
        """
    
    def set_source_name(self, source_name: str):
        """Set the source name for folder organization"""
        self.source_name = source_name
    
    def add_attachments(self):
        """Open file dialog to add attachments"""
        title = self._tr('btn_add_attachment')
        
        if self.allow_multiple:
            files, _ = QFileDialog.getOpenFileNames(
                self, title, "", "All Files (*.*)"
            )
        else:
            file, _ = QFileDialog.getOpenFileName(
                self, title, "", "All Files (*.*)"
            )
            files = [file] if file else []
        
        if files:
            self.add_files(files)
    
    def add_files(self, file_paths: List[str], copy_to_folder: bool = True):
        """
        Add files to the attachment list.
        
        Args:
            file_paths: List of file paths to add
            copy_to_folder: If True, copy files to the organized folder structure
        """
        if not file_paths:
            return
        
        added_paths = []
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue
            
            if copy_to_folder and self.source_name:
                # Copy to organized folder
                success, new_path = self.attachment_manager.add_attachment(
                    self.source_name, file_path, copy_file=True
                )
                if success:
                    added_paths.append(new_path)
                else:
                    logger.warning(f"Failed to copy attachment: {new_path}")
                    # Use original path as fallback
                    added_paths.append(file_path)
            else:
                # Use original path
                added_paths.append(file_path)
        
        # Add to file paths (avoid duplicates)
        for path in added_paths:
            if path not in self.file_paths:
                self.file_paths.append(path)
        
        self.update_display()
        self.attachments_changed.emit(self.file_paths)
    
    def remove_selected(self):
        """Remove selected attachments"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
        
        reply = QMessageBox.question(
            self,
            self._tr('msg_warning'),
            self._tr('msg_confirm_remove'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            if file_path in self.file_paths:
                self.file_paths.remove(file_path)
                
                # Optionally remove the actual file if it's in our managed folder
                if self.source_name and self.attachment_manager.source_folder in file_path:
                    self.attachment_manager.remove_attachment(file_path)
        
        self.update_display()
        self.attachments_changed.emit(self.file_paths)
    
    def open_selected(self):
        """Open selected attachment"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
        
        file_path = selected_items[0].data(Qt.UserRole)
        self.attachment_manager.open_attachment(file_path)
        self.attachment_opened.emit(file_path)
    
    def open_folder(self):
        """Open the source folder in file explorer"""
        if self.source_name:
            self.attachment_manager.open_source_folder(self.source_name)
        else:
            # Open the base Source folder
            import subprocess
            import sys
            folder = self.attachment_manager.source_folder
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
            
            if sys.platform == 'win32':
                os.startfile(folder)
            elif sys.platform == 'darwin':
                subprocess.run(['open', folder])
            else:
                subprocess.run(['xdg-open', folder])
    
    def on_selection_changed(self):
        """Handle selection change"""
        has_selection = len(self.list_widget.selectedItems()) > 0
        self.btn_remove.setEnabled(has_selection)
        self.btn_open.setEnabled(has_selection)
    
    def on_item_double_clicked(self, item: QListWidgetItem):
        """Handle double click on item"""
        file_path = item.data(Qt.UserRole)
        self.attachment_manager.open_attachment(file_path)
        self.attachment_opened.emit(file_path)
    
    def show_context_menu(self, pos):
        """Show context menu for attachments"""
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        
        menu = QMenu(self)
        
        open_action = QAction(self._tr('btn_open_attachment'), self)
        open_action.triggered.connect(self.open_selected)
        menu.addAction(open_action)
        
        menu.addSeparator()
        
        remove_action = QAction(self._tr('btn_remove_attachment'), self)
        remove_action.triggered.connect(self.remove_selected)
        menu.addAction(remove_action)
        
        menu.exec_(self.list_widget.mapToGlobal(pos))
    
    def update_display(self):
        """Update the list display"""
        self.list_widget.clear()
        
        for file_path in self.file_paths:
            item = AttachmentListItem(file_path, self.attachment_manager)
            self.list_widget.addItem(item)
        
        # Update count
        count = len(self.file_paths)
        self.count_label.setText(f"({count})")
        
        # Update status
        if count > 0:
            total_size = sum(
                os.path.getsize(f) for f in self.file_paths if os.path.exists(f)
            )
            size_str = self.attachment_manager.format_size(total_size)
            self.status_label.setText(f"{count} files, {size_str}")
        else:
            self.status_label.setText("")
    
    def set_files(self, file_paths: List[str]):
        """Set file paths (from database)"""
        self.file_paths = [f for f in file_paths if f] if file_paths else []
        self.update_display()
    
    def get_files(self) -> List[str]:
        """Get list of file paths"""
        return self.file_paths
    
    def get_files_string(self) -> str:
        """Get files as semicolon-separated string for database"""
        return "; ".join(self.file_paths) if self.file_paths else ""
    
    def clear(self):
        """Clear all attachments"""
        self.file_paths = []
        self.update_display()
        self.attachments_changed.emit(self.file_paths)
    
    # Drag and Drop support
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """Handle drag move event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_paths.append(url.toLocalFile())
            
            if file_paths:
                self.add_files(file_paths)
            
            event.acceptProposedAction()


class AttachmentManagerDialog(QDialog):
    """
    Dialog for comprehensive attachment management.
    Shows all sources and their attachments.
    """
    
    def __init__(self, parent=None, translator: TranslationManager = None):
        super().__init__(parent)
        self.translator = translator
        self.attachment_manager = get_attachment_manager()
        
        self.setWindowTitle(self._tr('dlg_manage_attachments'))
        # Apply fixed size to prevent resizing on button clicks or content changes
        from styles.styles import AppStyles
        AppStyles.apply_fixed_size(self, 800, 600)
        
        if translator and translator.current_language == 'ar':
            self.setLayoutDirection(Qt.RightToLeft)
        
        self.setup_ui()
        self.load_data()
    
    def _tr(self, key: str) -> str:
        """Get translation"""
        if self.translator:
            return self.translator.tr(key)
        fallbacks = {
            'dlg_manage_attachments': 'Manage All Attachments',
            'lbl_sources': 'Sources',
            'lbl_attachments': 'Attachments',
            'btn_refresh': 'Refresh',
            'btn_close': 'Close',
            'btn_open_folder': 'Open Folder',
            'btn_delete': 'Delete',
            'msg_total_attachments': 'Total: {count} attachments ({size})',
        }
        return fallbacks.get(key, key)
    
    def _get_dialog_button_style(self, button_type: str) -> str:
        """Get distinctive button style based on button type (8px grid system)"""
        from styles.styles import AppStyles
        colors_map = {
            'add': AppStyles.get_color('SUCCESS'),
            'remove': AppStyles.get_color('DANGER'),
            'open': AppStyles.get_color('ACCENT'),
            'folder': AppStyles.get_color('WARNING'),
            'refresh': AppStyles.get_color('ACCENT'),
            'close': AppStyles.get_color('TEXT_SECONDARY'),
        }
        hover_map = {
            'add': AppStyles.get_color('SUCCESS_HOVER'),
            'remove': AppStyles.get_color('DANGER_HOVER'),
            'open': AppStyles.get_color('ACCENT_HOVER'),
            'folder': '#F5B041',
            'refresh': AppStyles.get_color('ACCENT_HOVER'),
            'close': '#95A5A6',
        }
        
        bg_color = colors_map.get(button_type, AppStyles.get_color('ACCENT'))
        hover_color = hover_map.get(button_type, AppStyles.get_color('ACCENT_HOVER'))
        border_color = AppStyles.get_color('BORDER')
        
        return f"""
            QPushButton {{
                background-color: {bg_color};
                border: none;
                border-radius: 8px;
                padding: 10px 14px;
                font-weight: 500;
                min-width: 40px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {bg_color};
                opacity: 0.9;
            }}
            QPushButton:disabled {{
                background-color: {border_color};
                color: {AppStyles.get_color('TEXT_SECONDARY')};
                opacity: 0.6;
            }}
        """
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Splitter for sources and attachments
        splitter = QSplitter(Qt.Horizontal)
        
        # Sources panel
        sources_group = QGroupBox(self._tr('lbl_sources'))
        sources_layout = QVBoxLayout(sources_group)
        
        self.sources_list = QListWidget()
        self.sources_list.itemSelectionChanged.connect(self.on_source_selected)
        sources_layout.addWidget(self.sources_list)
        
        # Source actions - spacing for icon buttons to prevent cropping
        source_btn_layout = QHBoxLayout()
        is_rtl = self.translator and self.translator.current_language == 'ar'
        btn_spacing = AppStyles.get_spacing(3) if is_rtl else AppStyles.get_spacing(2)
        source_btn_layout.setSpacing(btn_spacing)
        
        self.btn_open_source_folder = QPushButton()
        setup_icon_button(self.btn_open_source_folder, 'btn_attachment_folder', self._tr('btn_open_folder'))
        self.btn_open_source_folder.clicked.connect(self.open_source_folder)
        self.btn_open_source_folder.setEnabled(False)
        self.btn_open_source_folder.setStyleSheet(self._get_dialog_button_style('folder'))
        
        source_btn_layout.addWidget(self.btn_open_source_folder)
        source_btn_layout.addStretch()
        sources_layout.addLayout(source_btn_layout)
        
        splitter.addWidget(sources_group)
        
        # Attachments panel
        attachments_group = QGroupBox(self._tr('lbl_attachments'))
        attachments_layout = QVBoxLayout(attachments_group)
        
        self.attachments_list = QListWidget()
        self.attachments_list.setIconSize(QSize(32, 32))
        self.attachments_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.attachments_list.itemDoubleClicked.connect(self.open_attachment)
        attachments_layout.addWidget(self.attachments_list)
        
        # Attachment actions with distinctive icons - spacing to prevent overlap
        attach_btn_layout = QHBoxLayout()
        attach_btn_layout.setSpacing(btn_spacing)
        
        self.btn_open_attachment = QPushButton()
        setup_icon_button(self.btn_open_attachment, 'btn_attachment_open', self._tr('btn_open_attachment') if self.translator else 'Open')
        self.btn_open_attachment.clicked.connect(self.open_selected_attachment)
        self.btn_open_attachment.setEnabled(False)
        self.btn_open_attachment.setStyleSheet(self._get_dialog_button_style('open'))
        
        self.btn_delete_attachment = QPushButton()
        setup_icon_button(self.btn_delete_attachment, 'btn_attachment_remove', self._tr('btn_delete'))
        self.btn_delete_attachment.clicked.connect(self.delete_selected_attachment)
        self.btn_delete_attachment.setEnabled(False)
        self.btn_delete_attachment.setStyleSheet(self._get_dialog_button_style('remove'))
        
        self.attachments_list.itemSelectionChanged.connect(self.on_attachment_selected)
        
        attach_btn_layout.addWidget(self.btn_open_attachment)
        attach_btn_layout.addWidget(self.btn_delete_attachment)
        attach_btn_layout.addStretch()
        attachments_layout.addLayout(attach_btn_layout)
        
        splitter.addWidget(attachments_group)
        
        # Set splitter proportions
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
        
        # Status bar - spacing between icon buttons
        status_layout = QHBoxLayout()
        status_layout.setSpacing(btn_spacing)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(AppStyles.get_component_style('status_label_muted'))
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.btn_refresh = QPushButton()
        setup_icon_button(self.btn_refresh, 'btn_refresh', self._tr('btn_refresh'))
        self.btn_refresh.clicked.connect(self.load_data)
        
        self.btn_close = QPushButton()
        setup_icon_button(self.btn_close, 'btn_close', self._tr('btn_close'))
        self.btn_close.clicked.connect(self.accept)
        
        status_layout.addWidget(self.btn_refresh)
        status_layout.addWidget(self.btn_close)
        
        layout.addLayout(status_layout)
    
    def load_data(self):
        """Load sources and attachments data"""
        self.sources_list.clear()
        self.attachments_list.clear()
        
        # Load sources
        sources = self.attachment_manager.get_all_sources()
        for source in sources:
            attachments = self.attachment_manager.get_attachments(source)
            item = QListWidgetItem(f"{source} ({len(attachments)})")
            item.setData(Qt.UserRole, source)
            self.sources_list.addItem(item)
        
        # Update status
        total_count = self.attachment_manager.get_total_attachment_count()
        _, total_size = self.attachment_manager.get_total_size()
        self.status_label.setText(
            self._tr('msg_total_attachments').format(count=total_count, size=total_size) if self.translator else f"Total: {total_count} attachments ({total_size})"
        )
    
    def on_source_selected(self):
        """Handle source selection"""
        selected = self.sources_list.selectedItems()
        self.btn_open_source_folder.setEnabled(len(selected) > 0)
        
        if selected:
            source_name = selected[0].data(Qt.UserRole)
            self.load_attachments(source_name)
        else:
            self.attachments_list.clear()
    
    def load_attachments(self, source_name: str):
        """Load attachments for a source"""
        self.attachments_list.clear()
        
        attachments = self.attachment_manager.get_attachments(source_name)
        for file_path in attachments:
            item = AttachmentListItem(file_path, self.attachment_manager)
            self.attachments_list.addItem(item)
    
    def on_attachment_selected(self):
        """Handle attachment selection"""
        selected = self.attachments_list.selectedItems()
        has_selection = len(selected) > 0
        self.btn_open_attachment.setEnabled(has_selection)
        self.btn_delete_attachment.setEnabled(has_selection)
    
    def open_source_folder(self):
        """Open selected source folder"""
        selected = self.sources_list.selectedItems()
        if selected:
            source_name = selected[0].data(Qt.UserRole)
            self.attachment_manager.open_source_folder(source_name)
    
    def open_attachment(self, item: QListWidgetItem):
        """Open attachment"""
        file_path = item.data(Qt.UserRole)
        self.attachment_manager.open_attachment(file_path)
    
    def open_selected_attachment(self):
        """Open selected attachment"""
        selected = self.attachments_list.selectedItems()
        if selected:
            self.open_attachment(selected[0])
    
    def delete_selected_attachment(self):
        """Delete selected attachment(s)"""
        selected = self.attachments_list.selectedItems()
        if not selected:
            return
        
        reply = QMessageBox.question(
            self,
            self._tr('msg_warning') if self.translator else 'Warning',
            self._tr('attachment_delete_confirm').format(count=len(selected)) if self.translator else f"Delete {len(selected)} attachment(s)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        for item in selected:
            file_path = item.data(Qt.UserRole)
            self.attachment_manager.remove_attachment(file_path)
        
        # Reload current source
        source_selected = self.sources_list.selectedItems()
        if source_selected:
            source_name = source_selected[0].data(Qt.UserRole)
            self.load_attachments(source_name)
        
        # Update sources list counts
        self.load_data()
