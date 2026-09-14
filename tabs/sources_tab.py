"""
Sources Tab - Dedicated management for information sources
Page-specific buttons: Import Sources, Duplicate Source, View Statistics
"""
from typing import List
from PyQt5.QtWidgets import QDialog, QMessageBox, QFileDialog

from tabs.base_tab import BaseTableTab
from core.toolbar_factory import ToolbarConfig, ButtonConfig
from db.db_manager import DatabaseManager
from dialogs.dialogs import SourceDialog
from translations.translations import TranslationManager
from utils.logger import get_logger

logger = get_logger(__name__)


class SourcesTab(BaseTableTab):
    """
    Sources table management with dedicated page-specific buttons.
    
    Dedicated Buttons:
    - CRUD: Add, Edit, Delete, Refresh
    - Page-Specific: Import Sources, Duplicate, Statistics
    - Export: Print, PDF, CSV, Excel, Word
    """
    
    PAGE_TITLE = "tab_sources"
    
    def __init__(self, parent, translator: TranslationManager):
        self.translator = translator
        columns = [
            ('id', 'ID', 50),
            ('name', translator.tr('lbl_name'), 180),
            ('type', translator.tr('lbl_type'), 120),
            ('link_sources', translator.tr('lbl_link_sources'), 200),
            ('importance', translator.tr('lbl_importance'), 100),
            ('country', translator.tr('lbl_country'), 120),
            ('city', translator.tr('lbl_city'), 120),
            ('description', translator.tr('lbl_description'), 250),
            ('accounts', translator.tr('lbl_accounts'), 150),
            ('note', translator.tr('lbl_note'), 200),
            ('ownership', translator.tr('lbl_ownership'), 150),
            ('date_entry', translator.tr('lbl_date_entry'), 150),
            ('date_creation', translator.tr('lbl_date_creation'), 150),
            ('date_modified', translator.tr('lbl_date_modified'), 150)
        ]
        super().__init__(parent, 'sources', columns, translator)
    
    def get_toolbar_config(self) -> ToolbarConfig:
        """Configure toolbar with Sources-specific buttons"""
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
        """Sources-specific buttons"""
        return [
            ButtonConfig(
                key='btn_import_sources',
                icon_key='btn_import',
                callback=self.import_sources,
                style_class='primary'
            ),
            ButtonConfig(
                key='btn_duplicate',
                icon_key='btn_duplicate',
                callback=self.duplicate_source,
                style_class=None
            ),
            ButtonConfig(
                key='btn_statistics',
                icon_key='btn_statistics',
                callback=self.show_statistics,
                style_class=None
            ),
        ]
    
    def get_callbacks(self):
        """Get callbacks including page-specific ones"""
        callbacks = super().get_callbacks()
        callbacks.update({
            'btn_import': self.import_sources,
            'btn_duplicate': self.duplicate_source,
            'btn_statistics': self.show_statistics,
        })
        return callbacks
    
    def refresh_columns(self):
        """Refresh column headers when language changes"""
        self.columns = [
            ('id', 'ID', 50),
            ('name', self.translator.tr('lbl_name'), 180),
            ('type', self.translator.tr('lbl_type'), 120),
            ('link_sources', self.translator.tr('lbl_link_sources'), 200),
            ('importance', self.translator.tr('lbl_importance'), 100),
            ('country', self.translator.tr('lbl_country'), 120),
            ('city', self.translator.tr('lbl_city'), 120),
            ('description', self.translator.tr('lbl_description'), 250),
            ('accounts', self.translator.tr('lbl_accounts'), 150),
            ('note', self.translator.tr('lbl_note'), 200),
            ('ownership', self.translator.tr('lbl_ownership'), 150),
            ('date_entry', self.translator.tr('lbl_date_entry'), 150),
            ('date_creation', self.translator.tr('lbl_date_creation'), 150),
            ('date_modified', self.translator.tr('lbl_date_modified'), 150)
        ]
        headers = ['#'] + [col[1] for col in self.columns]
        self.data_table.setHorizontalHeaderLabels(headers)
    
    # ==================== CRUD Operations ====================
    
    def load_data(self):
        """Load sources data"""
        try:
            data = DatabaseManager.get_all_sources()
            self.data_table.load_data(data)
            
            # Initialize pagination with full data
            self._full_filtered_data = data.copy()
            self.pagination.current_page = 1
            self.pagination.set_total_items(len(data))
            self.apply_pagination()
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def add_record(self):
        """Add new source"""
        dialog = SourceDialog(
            self, 
            self.translator.tr('btn_add') + " " + self.translator.tr('tab_sources'), 
            None, 
            self.translator
        )
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            try:
                new_id = DatabaseManager.add_source(dialog.result)
                # Log audit trail
                from utils.audit_trail import AuditTrail
                AuditTrail.log_create('sources', new_id, dialog.result)
                QMessageBox.information(self, self.translator.tr('msg_success'),
                                      self.translator.tr('msg_record_added'))
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def edit_record(self):
        """Edit selected source"""
        selected_id = self.data_table.get_selected_id()
        if not selected_id:
            QMessageBox.warning(self, self.translator.tr('msg_no_selection'),
                              self.translator.tr('msg_select_record'))
            return
        
        try:
            source = DatabaseManager.get_source_by_id(selected_id)
            if source:
                old_data = source.copy()
                dialog = SourceDialog(
                    self, 
                    self.translator.tr('btn_edit') + " " + self.translator.tr('tab_sources'), 
                    source, 
                    self.translator
                )
                if dialog.exec_() == QDialog.Accepted and dialog.result:
                    DatabaseManager.update_source(selected_id, dialog.result)
                    # Log audit trail
                    from utils.audit_trail import AuditTrail
                    AuditTrail.log_update('sources', selected_id, old_data, dialog.result)
                    QMessageBox.information(self, self.translator.tr('msg_success'),
                                          self.translator.tr('msg_record_updated'))
                    self.load_data()
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def delete_from_db(self, record_id: int):
        """Delete source from database"""
        # Get data before deletion for audit trail
        data = DatabaseManager.get_source_by_id(record_id)
        DatabaseManager.delete_source(record_id)
        # Log audit trail
        from utils.audit_trail import AuditTrail
        AuditTrail.log_delete('sources', record_id, data)
    
    # ==================== Page-Specific Operations ====================
    
    def import_sources(self):
        """Import sources from CSV file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            self.translator.tr('btn_import_sources'),
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
                            source_data = {
                                'name': row.get('name', row.get('Name', '')),
                                'type': row.get('type', row.get('Type', '')),
                                'link_sources': row.get('link_sources', row.get('Link', '')),
                                'importance': float(row.get('importance', '0') or '0'),
                                'country': row.get('country', row.get('Country', '')),
                                'city': row.get('city', row.get('City', '')),
                                'description': row.get('description', row.get('Description', '')),
                                'accounts': row.get('accounts', row.get('Accounts', '')),
                                'note': row.get('note', row.get('Note', '')),
                                'ownership': row.get('ownership', row.get('Ownership', '')),
                            }
                            
                            if source_data['name']:
                                DatabaseManager.add_source(source_data)
                                imported_count += 1
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
    
    def duplicate_source(self):
        """Duplicate selected source"""
        selected_id = self.data_table.get_selected_id()
        if not selected_id:
            QMessageBox.warning(self, self.translator.tr('msg_no_selection'),
                              self.translator.tr('msg_select_record'))
            return
        
        try:
            source = DatabaseManager.get_source_by_id(selected_id)
            if source:
                # Modify name to indicate copy
                source['name'] = f"{source['name']} {self.translator.tr('lbl_copy_suffix')}"
                # Remove auto-generated fields
                source.pop('id', None)
                source.pop('date_creation', None)
                source.pop('date_modified', None)
                
                # Open dialog with pre-filled data
                dialog = SourceDialog(
                    self,
                    self.translator.tr('btn_add') + " " + self.translator.tr('tab_sources'),
                    source,
                    self.translator
                )
                if dialog.exec_() == QDialog.Accepted and dialog.result:
                    DatabaseManager.add_source(dialog.result)
                    QMessageBox.information(self, self.translator.tr('msg_success'),
                                          self.translator.tr('msg_record_added'))
                    self.load_data()
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def show_statistics(self):
        """Show statistics about sources"""
        try:
            data = self.data_table.data
            if not data:
                QMessageBox.information(self, self.translator.tr('btn_statistics'),
                                      self.translator.tr('msg_no_data_for_stats'))
                return
            
            # Calculate statistics
            total = len(data)
            
            # Count by type
            types = {}
            unknown_label = self.translator.tr('lbl_unknown_source') if hasattr(self.translator, 'tr') else 'Unknown'
            for row in data:
                t = row.get('type', unknown_label) or unknown_label
                types[t] = types.get(t, 0) + 1
            
            # Count by country
            countries = {}
            for row in data:
                c = row.get('country', unknown_label) or unknown_label
                countries[c] = countries.get(c, 0) + 1
            
            # Average importance
            importances = [float(row.get('importance', 0) or 0) for row in data]
            avg_importance = sum(importances) / len(importances) * 100 if importances else 0
            
            # Build statistics message
            stats = f"""
📊 {self.translator.tr('stats_sources_title')}

{self.translator.tr('stats_total')}: {total}

{self.translator.tr('stats_by_type')}:
{chr(10).join(f'  • {k}: {v} ({v/total*100:.1f}%)' for k, v in sorted(types.items(), key=lambda x: -x[1])[:10])}

{self.translator.tr('stats_by_country')}:
{chr(10).join(f'  • {k}: {v} ({v/total*100:.1f}%)' for k, v in sorted(countries.items(), key=lambda x: -x[1])[:10])}

{self.translator.tr('stats_avg_importance')}: {avg_importance:.1f}%
"""
            
            QMessageBox.information(self, self.translator.tr('btn_statistics'), stats)
            
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
