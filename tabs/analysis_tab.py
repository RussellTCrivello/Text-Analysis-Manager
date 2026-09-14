"""
Content Analysis Tab - Dedicated management for analysis records
Page-specific buttons: View Map, Compare Analysis, Generate Summary
"""
from typing import List
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox

from tabs.base_tab import BaseTableTab
from core.toolbar_factory import ToolbarConfig, ButtonConfig
from db.db_manager import DatabaseManager
from dialogs.dialogs import ContentAnalysisDialog
from translations.translations import TranslationManager
from utils.logger import get_logger

logger = get_logger(__name__)


class ContentAnalysisTab(BaseTableTab):
    """
    Content Analysis table management with dedicated page-specific buttons.
    
    Dedicated Buttons:
    - CRUD: Add, Edit, Delete, Refresh
    - Page-Specific: View Map, Compare, Summary
    - Export: Print, PDF, CSV, Excel, Word
    """
    
    PAGE_TITLE = "tab_analysis"
    
    def __init__(self, parent, translator: TranslationManager):
        self.translator = translator
        columns = [
            ('id', 'ID', 50),
            ('content_id', translator.tr('lbl_content_id'), 80),
            ('source_name', translator.tr('lbl_source'), 150),
            ('classification', translator.tr('lbl_classification'), 130),
            ('list_names_people', translator.tr('lbl_people'), 200),
            ('list_names_places', translator.tr('lbl_places'), 200),
            ('coordinates', translator.tr('lbl_coordinates'), 200),
            ('list_sides', translator.tr('lbl_sides'), 200),
            ('date_analysis', translator.tr('lbl_date_analysis'), 150),
            ('date_creation', translator.tr('lbl_date_creation'), 150),
            ('date_modified', translator.tr('lbl_date_modified'), 150)
        ]
        super().__init__(parent, 'content_analysis', columns, translator)
    
    def get_toolbar_config(self) -> ToolbarConfig:
        """Configure toolbar with Analysis-specific buttons"""
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
        """Analysis-specific buttons"""
        return [
            ButtonConfig(
                key='btn_import_analysis',
                icon_key='btn_import',
                callback=self.import_analysis,
                style_class='primary'
            ),
            ButtonConfig(
                key='btn_duplicate_analysis',
                icon_key='btn_duplicate',
                callback=self.duplicate_analysis,
                style_class=None
            ),
            ButtonConfig(
                key='btn_view_map',
                icon_key='btn_map',
                callback=self.view_on_map,
                style_class='primary'
            ),
            ButtonConfig(
                key='btn_compare',
                icon_key='btn_compare',
                callback=self.compare_analysis,
                style_class=None
            ),
            ButtonConfig(
                key='btn_summary',
                icon_key='btn_summary',
                callback=self.generate_summary,
                style_class=None
            ),
        ]
    
    def get_callbacks(self):
        """Get callbacks including page-specific ones"""
        callbacks = super().get_callbacks()
        callbacks.update({
            'btn_import_analysis': self.import_analysis,
            'btn_duplicate_analysis': self.duplicate_analysis,
            'btn_map': self.view_on_map,
            'btn_compare': self.compare_analysis,
            'btn_summary': self.generate_summary,
        })
        return callbacks
    
    def refresh_columns(self):
        """Refresh column headers when language changes"""
        self.columns = [
            ('id', 'ID', 50),
            ('content_id', self.translator.tr('lbl_content_id'), 80),
            ('source_name', self.translator.tr('lbl_source'), 150),
            ('classification', self.translator.tr('lbl_classification'), 130),
            ('list_names_people', self.translator.tr('lbl_people'), 200),
            ('list_names_places', self.translator.tr('lbl_places'), 200),
            ('coordinates', self.translator.tr('lbl_coordinates'), 200),
            ('list_sides', self.translator.tr('lbl_sides'), 200),
            ('date_analysis', self.translator.tr('lbl_date_analysis'), 150),
            ('date_creation', self.translator.tr('lbl_date_creation'), 150),
            ('date_modified', self.translator.tr('lbl_date_modified'), 150)
        ]
        headers = ['#'] + [col[1] for col in self.columns]
        self.data_table.setHorizontalHeaderLabels(headers)
    
    # ==================== CRUD Operations ====================
    
    def load_data(self):
        """Load content analysis data"""
        try:
            data = DatabaseManager.get_all_content_analysis()
            self.data_table.load_data(data)
            
            # Initialize pagination with full data
            self._full_filtered_data = data.copy()
            self.pagination.current_page = 1
            self.pagination.set_total_items(len(data))
            self.apply_pagination()
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def add_record(self):
        """Add new content analysis"""
        dialog = ContentAnalysisDialog(
            self, 
            self.translator.tr('btn_add') + " " + self.translator.tr('tab_analysis'), 
            None, 
            self.translator
        )
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            try:
                new_id = DatabaseManager.add_content_analysis(dialog.result)
                # Log audit trail
                from utils.audit_trail import AuditTrail
                AuditTrail.log_create('content_analysis', new_id, dialog.result)
                QMessageBox.information(self, self.translator.tr('msg_success'),
                                      self.translator.tr('msg_record_added'))
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def edit_record(self):
        """Edit selected content analysis"""
        selected_id = self.data_table.get_selected_id()
        if not selected_id:
            QMessageBox.warning(self, self.translator.tr('msg_no_selection'),
                              self.translator.tr('msg_select_record'))
            return
        
        try:
            analysis = DatabaseManager.get_analysis_by_id(selected_id)
            if analysis:
                old_data = analysis.copy()
                dialog = ContentAnalysisDialog(
                    self, 
                    self.translator.tr('btn_edit') + " " + self.translator.tr('tab_analysis'), 
                    analysis, 
                    self.translator
                )
                if dialog.exec_() == QDialog.Accepted and dialog.result:
                    DatabaseManager.update_content_analysis(selected_id, dialog.result)
                    # Log audit trail
                    from utils.audit_trail import AuditTrail
                    AuditTrail.log_update('content_analysis', selected_id, old_data, dialog.result)
                    QMessageBox.information(self, self.translator.tr('msg_success'),
                                          self.translator.tr('msg_record_updated'))
                    self.load_data()
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def delete_from_db(self, record_id: int):
        """Delete content analysis from database"""
        # Get data before deletion for audit trail
        data = DatabaseManager.get_analysis_by_id(record_id)
        DatabaseManager.delete_content_analysis(record_id)
        # Log audit trail
        from utils.audit_trail import AuditTrail
        AuditTrail.log_delete('content_analysis', record_id, data)
    
    # ==================== Page-Specific Operations ====================

    def import_analysis(self):
        """Import analysis from CSV file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            self.translator.tr('btn_import_analysis'),
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
                            analysis_data = {
                                'content_id': row.get('content_id', row.get('Content ID', '')),
                                'list_names_people': row.get('list_names_people', row.get('List Names People', '')),
                                'list_names_places': row.get('list_names_places', row.get('List Names Places', '')),
                                'coordinates': row.get('coordinates', row.get('Coordinates', '')),
                                'classification': row.get('classification', row.get('Classification', '')),
                                'list_sides': row.get('list_sides', row.get('List Sides', '')),
                                'date_analysis': row.get('date_analysis', row.get('Date Analysis', '')),
                                'date_creation': row.get('date_creation', row.get('Date Creation', '')),
                                'date_modified': row.get('date_modified', row.get('Date Modified', '')),
                            }
                            
                            if analysis_data['content_id']:
                                DatabaseManager.add_content_analysis(analysis_data)
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
    
    def duplicate_analysis(self):
        """Duplicate selected analysis"""
        selected_id = self.data_table.get_selected_id()
        if not selected_id:
            QMessageBox.warning(self, self.translator.tr('msg_no_selection'),
                              self.translator.tr('msg_select_record'))
            return
        
        try:
            analysis = DatabaseManager.get_analysis_by_id(selected_id)
            if analysis:
                # Modify content_id to indicate copy (note: this is a number, keep it)
                # Don't modify content_id as it's a foreign key reference
                # Remove auto-generated fields
                analysis.pop('id', None)
                analysis.pop('date_creation', None)
                analysis.pop('date_modified', None)
                
                # Open dialog with pre-filled data
                dialog = ContentAnalysisDialog(
                    self,
                    self.translator.tr('btn_add') + " " + self.translator.tr('tab_analysis'),
                    analysis,
                    self.translator
                )
                if dialog.exec_() == QDialog.Accepted and dialog.result:
                    DatabaseManager.add_content_analysis(dialog.result)
                    QMessageBox.information(self, self.translator.tr('msg_success'),
                                          self.translator.tr('msg_record_added'))
                    self.load_data()
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))

    def view_on_map(self):
        """View coordinates on map (opens browser with Google Maps)"""
        selected_id = self.data_table.get_selected_id()
        if not selected_id:
            QMessageBox.warning(self, self.translator.tr('msg_no_selection'),
                              self.translator.tr('msg_select_record'))
            return
        
        try:
            analysis = DatabaseManager.get_analysis_by_id(selected_id)
            if analysis:
                coords = analysis.get('coordinates', '')
                if not coords:
                    QMessageBox.information(self, self.translator.tr('btn_view_map'),
                                          self.translator.tr('msg_no_coordinates'))
                    return
                
                # Parse first coordinate
                first_coord = coords.split(';')[0].strip()
                if ',' in first_coord:
                    parts = first_coord.split(',')
                    lat = parts[0].strip()
                    lon = parts[1].strip()
                    
                    # Open in browser
                    import webbrowser
                    url = f"https://www.google.com/maps?q={lat},{lon}"
                    webbrowser.open(url)
                    
                    self.status_label.setText(f"{self.translator.tr('msg_map_opened')}: {lat}, {lon}")
                else:
                    QMessageBox.warning(self, self.translator.tr('btn_view_map'),
                                      self.translator.tr('msg_invalid_coordinate_format'))
                
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def compare_analysis(self):
        """Compare multiple analysis records"""
        # Get all selected or filtered data
        data = self.data_table.filtered_data
        if len(data) < 2:
            QMessageBox.information(self, self.translator.tr('btn_compare'),
                                  self.translator.tr('msg_need_records_to_compare'))
            return
        
        try:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton
            from styles.styles import AppStyles
            
            dialog = QDialog(self)
            dialog.setWindowTitle(self.translator.tr('btn_compare'))
            # Apply fixed size to prevent resizing
            AppStyles.apply_fixed_size(dialog, 900, 600)
            
            layout = QVBoxLayout(dialog)
            
            # Create comparison table
            table = QTableWidget()
            fields = [
                self.translator.tr('lbl_id'),
                self.translator.tr('lbl_classification'),
                self.translator.tr('lbl_people'),
                self.translator.tr('lbl_places'),
                self.translator.tr('lbl_coordinates'),
                self.translator.tr('lbl_sides')
            ]
            table.setColumnCount(len(fields))
            table.setHorizontalHeaderLabels(fields)
            table.setRowCount(min(len(data), 10))  # Limit to 10 for comparison
            
            for row_idx, row_data in enumerate(data[:10]):
                table.setItem(row_idx, 0, QTableWidgetItem(str(row_data.get('id', ''))))
                table.setItem(row_idx, 1, QTableWidgetItem(str(row_data.get('classification', ''))))
                table.setItem(row_idx, 2, QTableWidgetItem(str(row_data.get('list_names_people', ''))[:50]))
                table.setItem(row_idx, 3, QTableWidgetItem(str(row_data.get('list_names_places', ''))[:50]))
                table.setItem(row_idx, 4, QTableWidgetItem(str(row_data.get('coordinates', ''))[:30]))
                table.setItem(row_idx, 5, QTableWidgetItem(str(row_data.get('list_sides', ''))[:50]))
            
            table.resizeColumnsToContents()
            layout.addWidget(table)
            
            btn_close = QPushButton(self.translator.tr('btn_close'))
            btn_close.clicked.connect(dialog.accept)
            layout.addWidget(btn_close)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
    
    def generate_summary(self):
        """Generate summary of analysis data"""
        try:
            data = self.data_table.filtered_data
            if not data:
                QMessageBox.information(self, self.translator.tr('btn_summary'),
                                      self.translator.tr('msg_no_data_for_summary'))
                return
            
            # Calculate statistics
            total = len(data)
            
            # Count by classification
            classifications = {}
            unclassified_label = self.translator.tr('lbl_classification') if hasattr(self.translator, 'tr') else 'Unclassified'
            for row in data:
                c = row.get('classification', unclassified_label) or unclassified_label
                classifications[c] = classifications.get(c, 0) + 1
            
            # Count unique people
            all_people = set()
            for row in data:
                people_str = row.get('list_names_people', '') or ''
                for p in people_str.split(','):
                    p = p.strip()
                    if p:
                        all_people.add(p)
            
            # Count unique places
            all_places = set()
            for row in data:
                places_str = row.get('list_names_places', '') or ''
                for p in places_str.split(','):
                    p = p.strip()
                    if p:
                        all_places.add(p)
            
            # Count coordinates
            coord_count = sum(1 for row in data if row.get('coordinates'))
            
            # Build summary
            summary = f"""
{self.translator.tr('stats_analysis_title')}

{self.translator.tr('stats_total_records')}: {total}

{self.translator.tr('stats_classifications')}:
{chr(10).join(f'  {k}: {v} ({v/total*100:.1f}%)' for k, v in sorted(classifications.items(), key=lambda x: -x[1]))}

{self.translator.tr('stats_unique_people')}: {len(all_people)}
{self.translator.tr('stats_top_people')}: {', '.join(list(all_people)[:5])}{'...' if len(all_people) > 5 else ''}

{self.translator.tr('stats_unique_places')}: {len(all_places)}
{self.translator.tr('stats_top_places')}: {', '.join(list(all_places)[:5])}{'...' if len(all_places) > 5 else ''}

{self.translator.tr('stats_with_coordinates')}: {coord_count} ({coord_count/total*100:.1f}%)
"""
            
            QMessageBox.information(self, self.translator.tr('btn_summary'), summary)
            
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
