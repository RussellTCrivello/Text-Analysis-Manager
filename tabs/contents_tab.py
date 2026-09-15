"""
Contents Tab - Dedicated management for content records
Page-specific buttons: View Attachments, Link to Analysis, Preview Content
"""
from typing import List
from html import escape
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox

from tabs.base_tab import BaseTableTab
from core.toolbar_factory import ToolbarConfig, ButtonConfig
from db.db_manager import DatabaseManager
from dialogs.dialogs import ContentDialog, _show_attachment_cleanup_warning
from translations.translations import TranslationManager
from utils.logger import get_logger

logger = get_logger(__name__)


class ContentsTab(BaseTableTab):
    """
    Contents table management with dedicated page-specific buttons.
    
    Dedicated Buttons:
    - CRUD: Add, Edit, Delete, Refresh
    - Page-Specific: View Attachments, Link Analysis, Preview Content
    - Export: Print, PDF, CSV, Excel, Word
    """
    
    PAGE_TITLE = "tab_contents"
    
    def __init__(self, parent, translator: TranslationManager):
        self.translator = translator
        columns = [
            ('id', 'ID', 50),
            ('sources_id', 'Source ID', 80),
            ('source_name', translator.tr('lbl_source'), 180),
            ('title', translator.tr('lbl_title'), 200),
            ('content_data', translator.tr('lbl_content_data'), 350),
            ('importance', translator.tr('lbl_importance'), 100),
            ('attachments', translator.tr('lbl_attachments'), 200),
            ('note', translator.tr('lbl_note'), 200),
            ('date_content', translator.tr('lbl_date_content'), 150),
            ('date_creation', translator.tr('lbl_date_creation'), 150),
            ('date_modified', translator.tr('lbl_date_modified'), 150)
        ]
        super().__init__(parent, 'contents', columns, translator)
    
    def get_toolbar_config(self) -> ToolbarConfig:
        """Configure toolbar with Contents-specific buttons"""
        return ToolbarConfig(
            show_crud=True,
            show_add=True,
            show_edit=True,
            show_delete=True,
            show_refresh=True,
            show_export=True,
            show_export_unified=True,  # Unified export with preview dialog
            show_print=True,
            # Individual export buttons removed - use unified Export dialog
            show_pdf=False,
            show_csv=False,
            show_excel=False,
            show_word=False,
            show_search=True,
            show_date_filter=True,
            page_specific_buttons=self.get_page_specific_buttons()
        )
    
    def get_page_specific_buttons(self) -> List[ButtonConfig]:
        """Contents-specific buttons"""
        return [
            ButtonConfig(
                key='btn_import_contents',
                icon_key='btn_import',
                callback=self.import_contents,
                style_class='primary'
            ),
            ButtonConfig(
                key='btn_duplicate_content',
                icon_key='btn_duplicate',
                callback=self.duplicate_content,
                style_class=None
            ),
            
            ButtonConfig(
                key='btn_view_attachments',
                icon_key='btn_attachments',
                callback=self.view_attachments,
                style_class='primary'
            ),
            ButtonConfig(
                key='btn_link_analysis',
                icon_key='btn_link_analysis',
                callback=self.link_to_analysis,
                style_class=None
            ),
            ButtonConfig(
                key='btn_preview_content',
                icon_key='btn_preview',
                callback=self.preview_content,
                style_class=None
            ),
        ]
    
    def get_callbacks(self):
        """Get callbacks including page-specific ones"""
        callbacks = super().get_callbacks()
        callbacks.update({
            'btn_import_contents': self.import_contents,
            'btn_duplicate_content': self.duplicate_content,
            'btn_attachments': self.view_attachments,
            'btn_link_analysis': self.link_to_analysis,
            'btn_preview': self.preview_content,
        })
        return callbacks
    
    def refresh_columns(self):
        """Refresh column headers when language changes"""
        self.columns = [
            ('id', 'ID', 50),
            ('sources_id', 'Source ID', 80),
            ('source_name', self.translator.tr('lbl_source'), 180),
            ('title', self.translator.tr('lbl_title'), 200),
            ('content_data', self.translator.tr('lbl_content_data'), 350),
            ('importance', self.translator.tr('lbl_importance'), 100),
            ('attachments', self.translator.tr('lbl_attachments'), 200),
            ('note', self.translator.tr('lbl_note'), 200),
            ('date_content', self.translator.tr('lbl_date_content'), 150),
            ('date_creation', self.translator.tr('lbl_date_creation'), 150),
            ('date_modified', self.translator.tr('lbl_date_modified'), 150)
        ]
        headers = ['#'] + [col[1] for col in self.columns]
        self.data_table.setHorizontalHeaderLabels(headers)
    
    # ==================== CRUD Operations ====================
    
    def load_data(self):
        """Load contents data"""
        try:
            data = DatabaseManager.get_all_contents()
            self.data_table.load_data(data)
            
            # Initialize pagination with full data
            self._full_filtered_data = data.copy()
            self.pagination.current_page = 1
            self.pagination.set_total_items(len(data))
            self.apply_pagination()
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def add_record(self):
        """Add new content"""
        dialog = ContentDialog(
            self, 
            self.translator.tr('btn_add') + " " + self.translator.tr('tab_contents'), 
            None, 
            self.translator
        )
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            try:
                new_id = DatabaseManager.add_content(dialog.result)
                cleanup_failures = dialog.commit_attachment_changes()
                # Log audit trail
                from utils.audit_trail import AuditTrail
                AuditTrail.log_create('contents', new_id, dialog.result)
                QMessageBox.information(self, self.translator.tr('msg_success'),
                                      self.translator.tr('msg_record_added'))
                _show_attachment_cleanup_warning(self, self.translator, cleanup_failures)
                self.load_data()
            except Exception as e:
                dialog.rollback_attachment_changes()
                QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def edit_record(self):
        """Edit selected content"""
        selected_id = self.data_table.get_selected_id()
        if not selected_id:
            QMessageBox.warning(self, self.translator.tr('msg_no_selection'),
                              self.translator.tr('msg_select_record'))
            return
        
        dialog = None
        try:
            content = DatabaseManager.get_content_by_id(selected_id)
            if content:
                old_data = content.copy()
                dialog = ContentDialog(
                    self, 
                    self.translator.tr('btn_edit') + " " + self.translator.tr('tab_contents'), 
                    content, 
                    self.translator
                )
                if dialog.exec_() == QDialog.Accepted and dialog.result:
                    DatabaseManager.update_content(selected_id, dialog.result)
                    cleanup_failures = dialog.commit_attachment_changes()
                    # Log audit trail
                    from utils.audit_trail import AuditTrail
                    AuditTrail.log_update('contents', selected_id, old_data, dialog.result)
                    QMessageBox.information(self, self.translator.tr('msg_success'),
                                          self.translator.tr('msg_record_updated'))
                    _show_attachment_cleanup_warning(self, self.translator, cleanup_failures)
                    self.load_data()
        except Exception as e:
            if dialog is not None:
                dialog.rollback_attachment_changes()
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def delete_from_db(self, record_id: int):
        """Delete content from database"""
        # Get data before deletion for audit trail
        data = DatabaseManager.get_content_by_id(record_id)
        DatabaseManager.delete_content(record_id)
        # Log audit trail
        from utils.audit_trail import AuditTrail
        AuditTrail.log_delete('contents', record_id, data)
    
        # ==================== Page-Specific Operations ====================
    
    def import_contents(self):
        """Import contents from CSV file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            self.translator.tr('btn_import_contents'),
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if filename:
            try:
                import csv
                imported_count = 0
                errors = []
                
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row_num, row in enumerate(reader, 1):
                        try:
                            # Map CSV columns to database fields
                            content_data = {
                                'title': row.get('title', row.get('Title', '')) or None,
                                'content_data': row.get('content_data', row.get('Content', '')) or '',
                                'attachments': row.get('attachments', row.get('Attachments', '')) or None,
                                'note': row.get('note', row.get('Note', '')) or None,
                                'importance': float(row.get('importance', '0') or '0'),
                                'date_content': row.get('date_content', row.get('Date Content', '')) or None,
                                'date_creation': row.get('date_creation', row.get('Date Creation', '')) or None,
                                'sources_id': row.get('sources_id', row.get('Sources ID', '')) or None,
                            }
                            
                            if content_data['content_data'].strip():
                                DatabaseManager.add_content(content_data)
                                imported_count += 1
                            else:
                                errors.append(f"Row {row_num}: Content data is required")
                        except Exception as e:
                            errors.append(f"Row {row_num}: {str(e)}")
                
                msg = self.translator.tr('msg_import_success', count=imported_count)
                if errors:
                    msg += f"\n\n{self.translator.tr('msg_import_errors', count=len(errors))}\n" + "\n".join(errors[:5])
                    if len(errors) > 5:
                        msg += f"\n{self.translator.tr('msg_more_errors', count=len(errors) - 5)}"
                
                QMessageBox.information(self, self.translator.tr('msg_success'), msg)
                self.load_data()
                
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('msg_error'), 
                                   f"{self.translator.tr('msg_import_failed')}: {str(e)}")
    
    def duplicate_content(self):
        """Duplicate selected content"""
        selected_id = self.data_table.get_selected_id()
        if not selected_id:
            QMessageBox.warning(self, self.translator.tr('msg_no_selection'),
                              self.translator.tr('msg_select_record'))
            return
        
        dialog = None
        try:
            content = DatabaseManager.get_content_by_id(selected_id)
            if content:
                # Modify name to indicate copy
                content['title'] = f"{content['title']} {self.translator.tr('lbl_copy_suffix')}"
                # Remove auto-generated fields
                content.pop('id', None)
                content.pop('date_creation', None)
                content.pop('date_modified', None)
                
                # Open dialog with pre-filled data
                dialog = ContentDialog(
                    self,
                    self.translator.tr('btn_add') + " " + self.translator.tr('tab_contents'),
                    content,
                    self.translator
                )
                if dialog.exec_() == QDialog.Accepted and dialog.result:
                    DatabaseManager.add_content(dialog.result)
                    cleanup_failures = dialog.commit_attachment_changes()
                    QMessageBox.information(self, self.translator.tr('msg_success'),
                                          self.translator.tr('msg_record_added'))
                    _show_attachment_cleanup_warning(self, self.translator, cleanup_failures)
                    self.load_data()
        except Exception as e:
            if dialog is not None:
                dialog.rollback_attachment_changes()
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))


    def view_attachments(self):
        """View attachments for selected content"""
        selected_id = self.data_table.get_selected_id()
        if not selected_id:
            QMessageBox.warning(self, self.translator.tr('msg_no_selection'),
                              self.translator.tr('msg_select_record'))
            return
        
        try:
            content = DatabaseManager.get_content_by_id(selected_id)
            if content:
                attachments_str = content.get('attachments', '')
                if not attachments_str:
                    QMessageBox.information(self, self.translator.tr('lbl_attachments'),
                                          self.translator.tr('msg_no_files'))
                    return
                
                # Parse attachments
                attachments = [f.strip() for f in attachments_str.split(';') if f.strip()]
                
                from widgets.preview_attachments import AttachmentPreviewDialog
                dialog = AttachmentPreviewDialog(self, self.translator)
                if attachments:
                    dialog.preview_file(attachments[0])
                dialog.exec_()
                
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def link_to_analysis(self):
        """Create analysis linked to selected content"""
        selected_id = self.data_table.get_selected_id()
        if not selected_id:
            QMessageBox.warning(self, self.translator.tr('msg_no_selection'),
                              self.translator.tr('msg_select_record'))
            return
        
        try:
            from dialogs.dialogs import ContentAnalysisDialog
            
            # Pre-populate with selected content ID
            analysis_data = {'content_id': selected_id}
            
            dialog = ContentAnalysisDialog(
                self,
                self.translator.tr('btn_add') + " " + self.translator.tr('tab_analysis'),
                analysis_data,
                self.translator
            )
            
            if dialog.exec_() == QDialog.Accepted and dialog.result:
                DatabaseManager.add_content_analysis(dialog.result)
                QMessageBox.information(self, self.translator.tr('msg_success'),
                                      self.translator.tr('msg_record_added'))
                
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def preview_content(self):
        """Show full content preview in popup"""
        selected_id = self.data_table.get_selected_id()
        if not selected_id:
            QMessageBox.warning(self, self.translator.tr('msg_no_selection'),
                              self.translator.tr('msg_select_record'))
            return
        
        try:
            content = DatabaseManager.get_content_by_id(selected_id)
            if content:
                from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
                from styles.styles import AppStyles
                
                dialog = QDialog(self)
                dialog.setWindowTitle(self.translator.tr('btn_preview_content'))
                # Apply fixed size to prevent resizing
                AppStyles.apply_fixed_size(dialog, 700, 500)
                
                layout = QVBoxLayout(dialog)
                
                # Title and source values come from the database; escape them
                # before embedding them in the small rich-text presentation.
                title = content.get('title') or self.translator.tr('lbl_no_title')
                title_label = QLabel(f"<h2>{escape(str(title))}</h2>")
                layout.addWidget(title_label)
                
                # Source info
                source = content.get('source_name') or self.translator.tr('lbl_unknown_source')
                date = content.get('date_content') or ''
                info_label = QLabel(
                    f"<b>{escape(self.translator.tr('lbl_source_prefix'))}:</b> "
                    f"{escape(str(source))} | "
                    f"<b>{escape(self.translator.tr('lbl_date_prefix'))}:</b> "
                    f"{escape(str(date))}"
                )
                layout.addWidget(info_label)
                
                # Content
                content_edit = QTextEdit()
                content_edit.setPlainText(content.get('content_data') or '')
                content_edit.setReadOnly(True)
                layout.addWidget(content_edit)
                
                # Note
                note = content.get('note', '')
                if note:
                    note_label = QLabel(
                        f"<b>{escape(self.translator.tr('lbl_note_prefix'))}:</b> "
                        f"{escape(str(note))}"
                    )
                    note_label.setWordWrap(True)
                    layout.addWidget(note_label)
                
                # Close button
                btn_close = QPushButton(self.translator.tr('btn_close'))
                btn_close.clicked.connect(dialog.accept)
                layout.addWidget(btn_close)
                
                dialog.exec_()
                
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
