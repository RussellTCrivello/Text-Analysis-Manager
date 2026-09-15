"""
Enhanced Attachment Manager Widget
Full UI for managing multiple attachments with folder organization
"""
import os
from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QDialog, QMenu, QAction, QSplitter, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QUrl
from PyQt5.QtGui import QIcon, QDragEnterEvent, QDropEvent
from translations.translations import TranslationManager
from utils.attachment_manager import get_attachment_manager, AttachmentManager
from icons.icon_manager import setup_icon_button, get_icon, get_file_type_icon
from utils.logger import get_logger
from styles.styles import AppStyles

logger = get_logger(__name__)


class AttachmentListItem(QListWidgetItem):
    """Custom list item for attachments with file info"""
    
    def __init__(self, file_path: str, attachment_manager: AttachmentManager,
                 translator: TranslationManager = None):
        super().__init__()
        self.file_path = file_path
        self.attachment_manager = attachment_manager
        self.translator = translator

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
            tooltip = (
                f"{self._tr('attachment_path', 'Path')}: {file_path}\n"
                f"{self._tr('attachment_size', 'Size')}: {info['size_str']}\n"
                f"{self._tr('attachment_modified', 'Modified')}: "
                f"{info['modified'].strftime('%Y-%m-%d %H:%M')}"
            )
        else:
            tooltip = (
                f"{self._tr('attachment_path', 'Path')}: {file_path}\n"
                f"{self._tr('attachment_file_not_found', 'File not found')}"
            )
        self.setToolTip(tooltip)

    def _tr(self, key: str, fallback: str) -> str:
        if self.translator and hasattr(self.translator, 'tr'):
            translated = self.translator.tr(key)
            if translated != key:
                return translated
        return fallback
    
    def _get_file_icon(self, extension: str) -> QIcon:
        """Return the graphical asset assigned to a file extension."""
        # FILE_TYPE_ICONS maps unknown extensions to the generic SVG asset, so
        # no text-rendered extension fallback is needed.
        return get_file_type_icon(extension, 32)


class AttachmentManagerWidget(QWidget):
    """
    Enhanced widget for managing file attachments.
    Supports drag-and-drop, multiple selection, and organized folder structure.
    """
    
    # Signals
    attachments_changed = pyqtSignal(list)  # Emits list of file paths
    attachment_opened = pyqtSignal(str)     # Emits path of opened file
    
    def __init__(self, parent=None, translator: TranslationManager = None,
                 source_name: str = "", allow_multiple: bool = True,
                 defer_file_changes: bool = False):
        super().__init__(parent)
        self.translator = translator
        self.source_name = source_name
        self.allow_multiple = allow_multiple
        self.defer_file_changes = defer_file_changes
        self.attachment_manager = get_attachment_manager()
        self.file_paths = []
        # Dialogs can defer physical file mutations until their database write
        # succeeds. This makes Cancel and failed CRUD operations reversible.
        self._initial_file_paths = []
        self._pending_added_paths = set()
        self._pending_removed_paths = set()
        
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
        setup_icon_button(self.btn_add, 'btn_attachment_add', self._tr('btn_add_attachment'), use_white_icon=True)
        self.btn_add.clicked.connect(self.add_attachments)
        self.btn_add.setStyleSheet(self._get_attachment_button_style('add'))
        
        self.btn_remove = QPushButton()
        setup_icon_button(self.btn_remove, 'btn_attachment_remove', self._tr('btn_remove_attachment'), use_white_icon=True)
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_remove.setEnabled(False)
        self.btn_remove.setStyleSheet(self._get_attachment_button_style('remove'))
        
        self.btn_open = QPushButton()
        setup_icon_button(self.btn_open, 'btn_attachment_open', self._tr('btn_open_attachment'), use_white_icon=True)
        self.btn_open.clicked.connect(self.open_selected)
        self.btn_open.setEnabled(False)
        self.btn_open.setStyleSheet(self._get_attachment_button_style('open'))
        
        self.btn_folder = QPushButton()
        setup_icon_button(self.btn_folder, 'btn_attachment_folder', self._tr('btn_open_folder'), use_white_icon=True)
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
        layout.addWidget(self.drop_hint)
        
        # Status bar
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(AppStyles.get_component_style('status_label_muted'))
        layout.addWidget(self.status_label)
        
        # Show drop hint initially
        self.update_display()
    
    def _tr(self, key: str, fallback: str = None) -> str:
        """Get a translation, using an optional local fallback."""
        if self.translator:
            translated = self.translator.tr(key)
            if translated != key:
                return translated
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
            'attachment_copy_failed': 'Could not copy attachment: {error}',
            'attachment_open_failed': 'Could not open the attachment.',
            'attachment_folder_open_failed': 'Could not open the attachment folder.',
            'attachment_delete_failed': 'Could not delete attachment: {error}',
            'msg_no_selection': 'No file selected',
        }
        return fallbacks.get(key, fallback if fallback is not None else key)
    
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
        failures = []
        
        for file_path in file_paths:
            if not os.path.isfile(file_path):
                failures.append(file_path)
                continue
            
            if copy_to_folder and self.source_name:
                # Copy to organized folder
                success, new_path = self.attachment_manager.add_attachment(
                    self.source_name, file_path, copy_file=True
                )
                if success:
                    added_paths.append(new_path)
                    if self.defer_file_changes:
                        self._pending_added_paths.add(new_path)
                else:
                    logger.warning(f"Failed to copy attachment: {new_path}")
                    failures.append(new_path)
            else:
                # Use original path
                added_paths.append(file_path)
        
        # Add to file paths (avoid duplicates)
        for path in added_paths:
            if path not in self.file_paths:
                self.file_paths.append(path)
        
        self.update_display()
        self.attachments_changed.emit(self.file_paths)
        if failures:
            self.status_label.setText(
                self._tr('attachment_copy_failed').format(error=failures[0])
            )
            self.status_label.setStyleSheet(AppStyles.get_component_style('status_label_error'))
    
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
        
        failures = []
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            if file_path not in self.file_paths:
                continue

            # Managed copies are deleted from disk; unmanaged paths are only
            # detached from this record. Dialog-owned widgets defer deleting
            # existing files until the database write has succeeded.
            if self.attachment_manager.is_managed_path(file_path):
                if self.defer_file_changes and file_path not in self._pending_added_paths:
                    self._pending_removed_paths.add(file_path)
                elif not self.attachment_manager.remove_attachment(file_path):
                    failures.append(file_path)
                    continue
                else:
                    self._pending_added_paths.discard(file_path)
            self.file_paths.remove(file_path)

        self.update_display()
        self.attachments_changed.emit(self.file_paths)
        if failures:
            self.status_label.setText(
                self._tr('attachment_delete_failed').format(error=failures[0])
            )
            self.status_label.setStyleSheet(AppStyles.get_component_style('status_label_error'))
    
    def open_selected(self):
        """Open selected attachment"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
        
        file_path = selected_items[0].data(Qt.UserRole)
        if self.attachment_manager.open_attachment(file_path):
            self.attachment_opened.emit(file_path)
        else:
            QMessageBox.warning(
                self,
                self._tr('msg_warning'),
                self._tr('attachment_open_failed')
            )
    
    def open_folder(self):
        """Open the source folder in file explorer"""
        if self.source_name:
            if not self.attachment_manager.open_source_folder(self.source_name):
                QMessageBox.warning(
                    self,
                    self._tr('msg_warning'),
                    self._tr('attachment_folder_open_failed')
                )
        else:
            # Open the base Source folder through the manager's guarded
            # platform launcher. This keeps missing desktop helpers (for
            # example xdg-open in a headless Linux environment) from
            # escaping as an unhandled button-click exception.
            folder = self.attachment_manager.source_folder
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
            if not self.attachment_manager.open_attachment(folder):
                QMessageBox.warning(
                    self,
                    self._tr('msg_warning'),
                    self._tr('attachment_folder_open_failed')
                )
    
    def on_selection_changed(self):
        """Handle selection change"""
        has_selection = len(self.list_widget.selectedItems()) > 0
        self.btn_remove.setEnabled(has_selection)
        self.btn_open.setEnabled(has_selection)
    
    def on_item_double_clicked(self, item: QListWidgetItem):
        """Handle double click on item"""
        file_path = item.data(Qt.UserRole)
        if self.attachment_manager.open_attachment(file_path):
            self.attachment_opened.emit(file_path)
        else:
            QMessageBox.warning(
                self,
                self._tr('msg_warning'),
                self._tr('attachment_open_failed')
            )
    
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
            item = AttachmentListItem(file_path, self.attachment_manager, self.translator)
            self.list_widget.addItem(item)
        
        # Update count and the empty-state hint.
        count = len(self.file_paths)
        self.count_label.setText(f"({count})")
        self.drop_hint.setVisible(count == 0)
        
        # Update status
        self.status_label.setStyleSheet(AppStyles.get_component_style('status_label_muted'))
        if count > 0:
            total_size = 0
            for file_path in self.file_paths:
                try:
                    total_size += os.path.getsize(file_path)
                except OSError:
                    logger.warning(f"Could not read attachment size: {file_path}")
            size_str = self.attachment_manager.format_size(total_size)
            self.status_label.setText(
                self._tr('msg_files_attached', '{count} file(s) attached').format(
                    count=count
                ) + f" ({size_str})"
            )
        else:
            self.status_label.setText("")
    
    def set_files(self, file_paths: List[str]):
        """Set file paths (from database) and start a new change set."""
        self.file_paths = [f for f in file_paths if f] if file_paths else []
        self._initial_file_paths = list(self.file_paths)
        self._pending_added_paths.clear()
        self._pending_removed_paths.clear()
        self.update_display()

    def commit_file_changes(self) -> List[str]:
        """Finalize deferred attachment deletions after a successful save.

        Returns paths that could not be removed. Newly copied files are kept;
        callers can surface the cleanup warning without losing the database
        update that already succeeded.
        """
        failures = []
        if self.defer_file_changes:
            for file_path in list(self._pending_removed_paths):
                if os.path.exists(file_path) and not self.attachment_manager.remove_attachment(file_path):
                    failures.append(file_path)
        self._initial_file_paths = list(self.file_paths)
        self._pending_added_paths.clear()
        self._pending_removed_paths.clear()
        self.update_display()
        return failures

    def rollback_file_changes(self):
        """Undo deferred physical changes after Cancel or a failed save."""
        if self.defer_file_changes:
            for file_path in list(self._pending_added_paths):
                if os.path.exists(file_path):
                    self.attachment_manager.remove_attachment(file_path)
            self.file_paths = list(self._initial_file_paths)
            self._pending_added_paths.clear()
            self._pending_removed_paths.clear()
            self.update_display()

    def get_files(self) -> List[str]:
        """Get list of file paths"""
        return self.file_paths
    
    def get_files_string(self) -> str:
        """Get files as semicolon-separated string for database"""
        return "; ".join(self.file_paths) if self.file_paths else ""
    
    def clear(self):
        """Clear all attachments, deferring managed deletes when requested."""
        if self.defer_file_changes:
            for file_path in self.file_paths:
                if self.attachment_manager.is_managed_path(file_path):
                    if file_path in self._pending_added_paths:
                        if self.attachment_manager.remove_attachment(file_path):
                            self._pending_added_paths.discard(file_path)
                    else:
                        self._pending_removed_paths.add(file_path)
        else:
            for file_path in list(self.file_paths):
                if self.attachment_manager.is_managed_path(file_path):
                    self.attachment_manager.remove_attachment(file_path)
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
            'msg_warning': 'Warning',
            'attachment_open_failed': 'Could not open the attachment.',
            'attachment_folder_open_failed': 'Could not open the attachment folder.',
            'attachment_delete_failed': 'Could not delete attachment: {error}',
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
        setup_icon_button(self.btn_open_source_folder, 'btn_attachment_folder', self._tr('btn_open_folder'), use_white_icon=True)
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
        setup_icon_button(self.btn_open_attachment, 'btn_attachment_open', self._tr('btn_open_attachment') if self.translator else 'Open', use_white_icon=True)
        self.btn_open_attachment.clicked.connect(self.open_selected_attachment)
        self.btn_open_attachment.setEnabled(False)
        self.btn_open_attachment.setStyleSheet(self._get_dialog_button_style('open'))
        
        self.btn_delete_attachment = QPushButton()
        setup_icon_button(self.btn_delete_attachment, 'btn_attachment_remove', self._tr('btn_delete'), use_white_icon=True)
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
            item = AttachmentListItem(file_path, self.attachment_manager, self.translator)
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
            if not self.attachment_manager.open_source_folder(source_name):
                QMessageBox.warning(
                    self,
                    self._tr('msg_warning') if self.translator else 'Warning',
                    self._tr('attachment_folder_open_failed')
                )

    def open_attachment(self, item: QListWidgetItem):
        """Open attachment"""
        file_path = item.data(Qt.UserRole)
        if not self.attachment_manager.open_attachment(file_path):
            QMessageBox.warning(
                self,
                self._tr('msg_warning') if self.translator else 'Warning',
                self._tr('attachment_open_failed')
            )
    
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
        
        failures = []
        for item in selected:
            file_path = item.data(Qt.UserRole)
            if not self.attachment_manager.remove_attachment(file_path):
                failures.append(file_path)

        # Reload current source
        source_selected = self.sources_list.selectedItems()
        if source_selected:
            source_name = source_selected[0].data(Qt.UserRole)
            self.load_attachments(source_name)
        
        # Update sources list counts
        self.load_data()
        if failures:
            self.status_label.setText(
                self._tr('attachment_delete_failed').format(error=failures[0])
            )
            self.status_label.setStyleSheet(AppStyles.get_component_style('status_label_error'))
