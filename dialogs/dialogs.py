"""
Enhanced Dialog Classes with All Fields and Professional UI
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QDateTimeEdit, QLabel, QMessageBox,
    QTabWidget, QWidget, QScrollArea, QGroupBox
)
from PyQt5.QtCore import Qt, QDate, QDateTime
from datetime import datetime
from typing import Optional, Dict, List
from db.db_manager import DatabaseManager
from styles.styles import AppStyles
from translations.translations import TranslationManager
from widgets.widgets import (
    SearchableComboBox, FileAttachmentWidget, PercentageSpinBox,
    CoordinateInputWidget, MultiEmailUrlWidget, AutoCompleteLineEdit,
    AutoCompleteTextEdit
)
from widgets.attachment_manager_widget import AttachmentManagerWidget
from widgets.preview_attachments import AttachmentPreviewDialog
from utils.logger import get_logger
from icons.icon_manager import setup_icon_button

logger = get_logger(__name__)


def _to_datetime(val):
    """Convert various date types to datetime for QDateTimeEdit"""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    from datetime import date
    if isinstance(val, date) and not isinstance(val, datetime):
        return datetime.combine(val, datetime.min.time())
    if isinstance(val, str):
        s = val.strip()[:19]
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
    return None


class SourceDialog(QDialog):
    """Enhanced source dialog with all fields"""
    
    def __init__(self, parent, title: str, source_data: Optional[Dict], translator: TranslationManager):
        super().__init__(parent)
        self.translator = translator
        self.source_data = source_data
        self.result = None
        self.setWindowTitle(title)
        # Apply responsive size
        from styles.styles import AppStyles
        AppStyles.apply_responsive_dialog_size(self, 700, 600)
        # Apply RTL layout if Arabic
        self._apply_rtl_direction()
        self.setup_ui()
        if source_data:
            self.populate_data(source_data)
        # Apply RTL to all children after setup
        self._apply_rtl_direction()
    
    def _apply_rtl_direction(self):
        """Apply RTL/LTR direction based on current language"""
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)
        # Apply to all child widgets
        from PyQt5.QtWidgets import QWidget
        for child in self.findChildren(QWidget):
            child.setLayoutDirection(direction)
    
    def setup_ui(self):
        """Setup enhanced UI with tabs"""
        layout = QVBoxLayout(self)
        is_rtl = self.translator.current_language == 'ar'
        m = AppStyles.get_spacing(3) if is_rtl else AppStyles.get_spacing(2)  # 24px RTL, 16px LTR
        layout.setContentsMargins(m, m, m, m)
        layout.setSpacing(AppStyles.get_spacing(3) if is_rtl else AppStyles.get_spacing(2))
        
        # Scroll area for form with proper content margins
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.NoFrame)
        scroll_widget = QWidget()
        form_layout = QVBoxLayout(scroll_widget)
        scroll_m = AppStyles.get_spacing(3) if is_rtl else AppStyles.get_spacing(2)
        form_layout.setContentsMargins(scroll_m, scroll_m, scroll_m, scroll_m)
        form_layout.setSpacing(AppStyles.get_spacing(3) if is_rtl else AppStyles.get_spacing(2))
        
        # Basic Information Group
        basic_group = QGroupBox(self.translator.tr('lbl_name') + " / " + self.translator.tr('lbl_type'))
        basic_form = QFormLayout(basic_group)
        AppStyles.apply_form_layout_for_language(basic_form, is_rtl)
        
        self.name_edit = QLineEdit()
        basic_form.addRow(self.translator.tr('lbl_name') + " *:", self.name_edit)
        
        # Type field with autocomplete
        type_placeholder = self.translator.tr('msg_type_to_search') if self.translator else "Type to search..."
        self.type_edit = AutoCompleteLineEdit(self, type_placeholder, self.translator)
        self.type_edit.set_suggestions(DatabaseManager.get_distinct_source_types())
        basic_form.addRow(self.translator.tr('lbl_type') + " *:", self.type_edit)
        
        self.link_edit = QLineEdit()
        basic_form.addRow(self.translator.tr('lbl_link_sources') + " *:", self.link_edit)
        
        self.importance_widget = PercentageSpinBox()
        basic_form.addRow(self.translator.tr('lbl_importance_percent') + " *:", self.importance_widget)
        
        form_layout.addWidget(basic_group)
        
        # Location Group
        location_group = QGroupBox(self.translator.tr('lbl_country') + " / " + self.translator.tr('lbl_city'))
        location_form = QFormLayout(location_group)
        AppStyles.apply_form_layout_for_language(location_form, is_rtl)
        
        # Country field with autocomplete
        country_placeholder = self.translator.tr('msg_type_to_search') if self.translator else "Type to search..."
        self.country_edit = AutoCompleteLineEdit(self, country_placeholder, self.translator)
        self.country_edit.set_suggestions(DatabaseManager.get_distinct_countries())
        location_form.addRow(self.translator.tr('lbl_country') + " *:", self.country_edit)
        
        # City field with autocomplete
        city_placeholder = self.translator.tr('msg_type_to_search') if self.translator else "Type to search..."
        self.city_edit = AutoCompleteLineEdit(self, city_placeholder, self.translator)
        self.city_edit.set_suggestions(DatabaseManager.get_distinct_cities())
        location_form.addRow(self.translator.tr('lbl_city') + ":", self.city_edit)
        
        form_layout.addWidget(location_group)
        
        # Details Group
        details_group = QGroupBox(self.translator.tr('lbl_description'))
        details_form = QFormLayout(details_group)
        AppStyles.apply_form_layout_for_language(details_form, is_rtl)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        details_form.addRow(self.translator.tr('lbl_description') + ":", self.description_edit)
        
        self.accounts_widget = MultiEmailUrlWidget(self, separator=';', translator=self.translator)
        self.accounts_widget.text_edit.setMaximumHeight(80)
        details_form.addRow(self.translator.tr('lbl_accounts') + ":", self.accounts_widget)
        
        # Ownership field with autocomplete
        ownership_placeholder = self.translator.tr('msg_type_to_search') if self.translator else "Type to search..."
        self.ownership_edit = AutoCompleteLineEdit(self, ownership_placeholder, self.translator)
        self.ownership_edit.set_suggestions(DatabaseManager.get_distinct_ownership())
        details_form.addRow(self.translator.tr('lbl_ownership') + ":", self.ownership_edit)
        
        self.note_edit = QTextEdit()
        self.note_edit.setMaximumHeight(100)
        details_form.addRow(self.translator.tr('lbl_note') + ":", self.note_edit)
        
        form_layout.addWidget(details_group)
        
        # Dates Group
        dates_group = QGroupBox(self.translator.tr('lbl_date_entry'))
        dates_form = QFormLayout(dates_group)
        AppStyles.apply_form_layout_for_language(dates_form, is_rtl)
        
        self.date_entry_edit = QDateTimeEdit()
        self.date_entry_edit.setCalendarPopup(True)
        self.date_entry_edit.setDateTime(QDateTime.currentDateTime())
        self.date_entry_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        dates_form.addRow(self.translator.tr('lbl_date_entry') + ":", self.date_entry_edit)
        
        form_layout.addWidget(dates_group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons - properly aligned in a single row, extra spacing for RTL
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        btn_spacing = AppStyles.get_spacing(3) if is_rtl else AppStyles.get_spacing(2)  # 24px RTL
        btn_layout.setSpacing(btn_spacing)
        btn_layout.addStretch()
        
        btn_save = QPushButton()
        setup_icon_button(btn_save, 'btn_save', self.translator.tr('btn_save'))
        # Disable autoDefault to prevent Enter key from triggering save unexpectedly
        btn_save.setAutoDefault(False)
        btn_save.setDefault(False)
        btn_save.clicked.connect(self.save)
        
        btn_cancel = QPushButton()
        setup_icon_button(btn_cancel, 'btn_cancel', self.translator.tr('btn_cancel'))
        btn_cancel.setAutoDefault(False)
        btn_cancel.setDefault(False)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save, alignment=Qt.AlignVCenter)
        btn_layout.addWidget(btn_cancel, alignment=Qt.AlignVCenter)
        layout.addLayout(btn_layout)
    
    def populate_data(self, data: Dict):
        """Populate form with existing data"""
        self.name_edit.setText(str(data.get('name', '')))
        self.type_edit.setText(str(data.get('type', '')))
        self.link_edit.setText(str(data.get('link_sources', '')))
        self.importance_widget.set_value(float(data.get('importance', 0.0)))
        self.country_edit.setText(str(data.get('country', '')))
        self.city_edit.setText(str(data.get('city', '')))
        self.description_edit.setPlainText(str(data.get('description', '')))
        self.accounts_widget.set_value(str(data.get('accounts', '')))
        self.ownership_edit.setText(str(data.get('ownership', '')))
        self.note_edit.setPlainText(str(data.get('note', '')))
        
        if data.get('date_entry'):
            date_val = data['date_entry']
            dt = _to_datetime(date_val)
            if dt:
                self.date_entry_edit.setDateTime(QDateTime(dt))
    
    def save(self):
        """Save form data"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, self.translator.tr('msg_validation_error') if hasattr(self.translator, 'tr') else 'Validation Error',
                              self.translator.tr('lbl_name') + ' is required')
            return
        
        if not self.type_edit.text().strip():
            QMessageBox.warning(self, self.translator.tr('msg_validation_error') if hasattr(self.translator, 'tr') else 'Validation Error',
                              self.translator.tr('lbl_type') + ' is required')
            return
        
        if not self.link_edit.text().strip():
            QMessageBox.warning(self, self.translator.tr('msg_validation_error') if hasattr(self.translator, 'tr') else 'Validation Error',
                              self.translator.tr('lbl_link_sources') + ' is required')
            return
        
        if not self.country_edit.text().strip():
            QMessageBox.warning(self, self.translator.tr('msg_validation_error') if hasattr(self.translator, 'tr') else 'Validation Error',
                              self.translator.tr('lbl_country') + ' is required')
            return
        
        try:
            date_val = self.date_entry_edit.dateTime()
            date_entry = date_val.toPyDateTime()
        except:
            date_entry = None
        
        data = {
            'name': self.name_edit.text().strip(),
            'type': self.type_edit.text().strip(),
            'link_sources': self.link_edit.text().strip(),
            'importance': self.importance_widget.get_value(),
            'country': self.country_edit.text().strip(),
            'city': self.city_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip() or None,
            'accounts': self.accounts_widget.get_value() or None,
            'ownership': self.ownership_edit.text().strip() or None,
            'note': self.note_edit.toPlainText().strip() or None,
            'date_entry': date_entry,
            'date_creation': datetime.now() if not self.source_data else None
        }
        
        # Validate using validation system
        from utils.data_validation import get_validator
        validator = get_validator()
        is_valid, errors = validator.validate('sources', data)
        
        if not is_valid:
            QMessageBox.warning(self, 
                              self.translator.tr('validation_error') if hasattr(self.translator, 'tr') else 'Validation Error',
                              '\n'.join(errors))
            return
        
        self.result = data
        self.accept()


class ContentDialog(QDialog):
    """Enhanced content dialog with all fields and file attachments"""
    
    def __init__(self, parent, title: str, content_data: Optional[Dict], translator: TranslationManager):
        super().__init__(parent)
        self.translator = translator
        self.content_data = content_data
        self.result = None
        self.setWindowTitle(title)
        # Apply responsive size
        from styles.styles import AppStyles
        AppStyles.apply_responsive_dialog_size(self, 700, 600)
        # Apply RTL layout direction
        self._apply_rtl_direction()
        self.setup_ui()
        if content_data:
            self.populate_data(content_data)
        # Apply RTL to all children after setup
        self._apply_rtl_direction()
    
    def _apply_rtl_direction(self):
        """Apply RTL/LTR direction based on current language"""
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)
        # Apply to all child widgets
        from PyQt5.QtWidgets import QWidget
        for child in self.findChildren(QWidget):
            child.setLayoutDirection(direction)
    
    def setup_ui(self):
        """Setup enhanced UI"""
        layout = QVBoxLayout(self)
        is_rtl = self.translator.current_language == 'ar'
        m = AppStyles.get_spacing(3) if is_rtl else AppStyles.get_spacing(2)  # 24px RTL, 16px LTR
        layout.setContentsMargins(m, m, m, m)
        layout.setSpacing(AppStyles.get_spacing(3) if is_rtl else AppStyles.get_spacing(2))
        
        # Scroll area with proper content margins
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.NoFrame)
        scroll_widget = QWidget()
        form_layout = QVBoxLayout(scroll_widget)
        form_layout.setContentsMargins(m, m, m, m)
        form_layout.setSpacing(AppStyles.get_spacing(2))
        
        # Source Selection Group
        source_group = QGroupBox(self.translator.tr('lbl_source'))
        source_form = QFormLayout(source_group)
        AppStyles.apply_form_layout_for_language(source_form, is_rtl)
        
        def add_new_source():
            dialog = SourceDialog(self, self.translator.tr('btn_add') + " " + self.translator.tr('tab_sources'), None, self.translator)
            if dialog.exec_() == QDialog.Accepted and dialog.result:
                try:
                    new_id = DatabaseManager.add_source(dialog.result)
                    QMessageBox.information(self, self.translator.tr('msg_success'),
                                          self.translator.tr('msg_record_added'))
                    self.refresh_source_combo()
                    self.source_combo.set_selected_id(new_id)
                    return new_id
                except Exception as e:
                    QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
            return None
        
        self.source_combo = SearchableComboBox(self, allow_add_new=True, add_callback=add_new_source, translator=self.translator)
        self.refresh_source_combo()
        source_form.addRow(self.translator.tr('lbl_source') + " *:", self.source_combo)
        
        # Update attachment folder when source changes
        self.source_combo.selection_changed.connect(self.on_source_selected)
        
        form_layout.addWidget(source_group)
        
        # Content Group
        content_group = QGroupBox(self.translator.tr('lbl_content_data'))
        content_form = QFormLayout(content_group)
        AppStyles.apply_form_layout_for_language(content_form, is_rtl)
        
        self.title_edit = QLineEdit()
        content_form.addRow(self.translator.tr('lbl_title') + ":", self.title_edit)
        
        self.content_edit = QTextEdit()
        self.content_edit.setMinimumHeight(150)
        content_form.addRow(self.translator.tr('lbl_content_data') + " *:", self.content_edit)
        
        self.importance_widget = PercentageSpinBox()
        content_form.addRow(self.translator.tr('lbl_importance_percent') + " *:", self.importance_widget)
        
        self.date_content_edit = QDateTimeEdit()
        self.date_content_edit.setCalendarPopup(True)
        self.date_content_edit.setDateTime(QDateTime.currentDateTime())
        self.date_content_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        content_form.addRow(self.translator.tr('lbl_date_content') + ":", self.date_content_edit)
        
        # Enhanced File Attachments with folder organization
        self.attachment_widget = AttachmentManagerWidget(
            self, 
            translator=self.translator,
            source_name=self.get_current_source_name(),
            allow_multiple=True
        )
        content_form.addRow(self.translator.tr('lbl_attachments') + ":", self.attachment_widget)
        
        self.note_edit = QTextEdit()
        self.note_edit.setMaximumHeight(100)
        content_form.addRow(self.translator.tr('lbl_note') + ":", self.note_edit)
        
        form_layout.addWidget(content_group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons - properly aligned in a single row, extra spacing for RTL
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        btn_spacing = AppStyles.get_spacing(3) if is_rtl else AppStyles.get_spacing(2)  # 24px RTL
        btn_layout.setSpacing(btn_spacing)
        btn_layout.addStretch()
        
        btn_save = QPushButton()
        setup_icon_button(btn_save, 'btn_save', self.translator.tr('btn_save'))
        # Disable autoDefault to prevent Enter key from triggering save unexpectedly
        btn_save.setAutoDefault(False)
        btn_save.setDefault(False)
        btn_save.clicked.connect(self.save)
        
        btn_cancel = QPushButton()
        setup_icon_button(btn_cancel, 'btn_cancel', self.translator.tr('btn_cancel'))
        btn_cancel.setAutoDefault(False)
        btn_cancel.setDefault(False)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save, alignment=Qt.AlignVCenter)
        btn_layout.addWidget(btn_cancel, alignment=Qt.AlignVCenter)
        layout.addLayout(btn_layout)
    
    def refresh_source_combo(self):
        """Refresh source combo box"""
        sources = DatabaseManager.get_all_sources()
        items = [{'id': s['id'], 'text': s['name'], 'name': s['name']} for s in sources]
        self.source_combo.set_items(items)
    
    def get_current_source_name(self) -> str:
        """Get the currently selected source name for folder organization"""
        if self.content_data:
            # If editing, use the source name from the data
            return self.content_data.get('source_name', '') or ''
        return ''
    
    def on_source_selected(self, source_id: int, source_text: str):
        """Handle source selection change to update attachment folder"""
        # Update the attachment widget's source name for folder organization
        if hasattr(self, 'attachment_widget'):
            self.attachment_widget.set_source_name(source_text)
    
    def preview_attachments(self):
        """Preview attachments"""
        files = self.attachment_widget.get_files()
        if not files:
            QMessageBox.information(self, self.translator.tr('msg_warning'),
                                  self.translator.tr('msg_no_files'))
            return
        
        # Create preview dialog with fixed size
        from styles.styles import AppStyles
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle(self.translator.tr('lbl_preview_attachments'))
        AppStyles.apply_fixed_size(preview_dialog, 800, 600)
        preview_layout = QVBoxLayout(preview_dialog)
        
        preview_widget = AttachmentPreviewDialog(preview_dialog, self.translator)
        preview_layout.addWidget(preview_widget)
        
        # Load first file
        if files:
            preview_widget.preview_file(files[0])
        
        preview_dialog.exec_()
    
    def populate_data(self, data: Dict):
        """Populate form with existing data"""
        source_id = data.get('sources_id')
        self.refresh_source_combo()
        if source_id:
            self.source_combo.set_selected_id(source_id)
        
        # Set source name for attachment organization
        source_name = data.get('source_name', '')
        if source_name:
            self.attachment_widget.set_source_name(source_name)
        
        self.title_edit.setText(str(data.get('title', '')))
        self.content_edit.setPlainText(str(data.get('content_data', '')))
        self.importance_widget.set_value(float(data.get('importance', 0.0)))
        
        if data.get('date_content'):
            date_val = data['date_content']
            dt = _to_datetime(date_val)
            if dt:
                self.date_content_edit.setDateTime(QDateTime(dt))
        
        # Load attachments
        attachments_str = data.get('attachments', '')
        if attachments_str:
            attachments = [f.strip() for f in attachments_str.split(';') if f.strip()]
            self.attachment_widget.set_files(attachments)
        
        self.note_edit.setPlainText(str(data.get('note', '')))
    
    def save(self):
        """Save form data"""
        source_id = self.source_combo.get_selected_id()
        if not source_id:
            QMessageBox.warning(self, self.translator.tr('msg_validation_error') if hasattr(self.translator, 'tr') else 'Validation Error',
                              self.translator.tr('lbl_source') + ' is required')
            return
        
        if not self.content_edit.toPlainText().strip():
            QMessageBox.warning(self, self.translator.tr('msg_validation_error') if hasattr(self.translator, 'tr') else 'Validation Error',
                              self.translator.tr('lbl_content_data') + ' is required')
            return
        
        try:
            date_val = self.date_content_edit.dateTime()
            date_content = date_val.toPyDateTime()
        except:
            date_content = None
        
        # Get attachments as semicolon-separated string
        attachments_str = self.attachment_widget.get_files_string()
        
        data = {
            'sources_id': source_id,
            'title': self.title_edit.text().strip() or None,
            'content_data': self.content_edit.toPlainText().strip(),
            'importance': self.importance_widget.get_value(),
            'date_content': date_content,
            'attachments': attachments_str if attachments_str else None,
            'note': self.note_edit.toPlainText().strip() or None,
            'date_creation': datetime.now() if not self.content_data else None
        }
        
        # Validate using validation system
        from utils.data_validation import get_validator
        validator = get_validator()
        is_valid, errors = validator.validate('contents', data)
        
        if not is_valid:
            QMessageBox.warning(self,
                              self.translator.tr('validation_error') if hasattr(self.translator, 'tr') else 'Validation Error',
                              '\n'.join(errors))
            return
        
        self.result = data
        self.accept()


class ContentAnalysisDialog(QDialog):
    """Enhanced content analysis dialog with all fields"""
    
    def __init__(self, parent, title: str, analysis_data: Optional[Dict], translator: TranslationManager):
        super().__init__(parent)
        self.translator = translator
        self.analysis_data = analysis_data
        self.result = None
        self.selected_content_id = None
        self.setWindowTitle(title)
        # Apply responsive size
        from styles.styles import AppStyles
        AppStyles.apply_responsive_dialog_size(self, 800, 700)
        # Apply RTL layout direction
        self._apply_rtl_direction()
        self.setup_ui()
        if analysis_data:
            self.populate_data(analysis_data)
        # Apply RTL to all children after setup
        self._apply_rtl_direction()
    
    def _apply_rtl_direction(self):
        """Apply RTL/LTR direction based on current language"""
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)
        # Apply to all child widgets
        from PyQt5.QtWidgets import QWidget
        for child in self.findChildren(QWidget):
            child.setLayoutDirection(direction)
    
    def setup_ui(self):
        """Setup enhanced UI"""
        layout = QVBoxLayout(self)
        is_rtl = self.translator.current_language == 'ar'
        m = AppStyles.get_spacing(3) if is_rtl else AppStyles.get_spacing(2)  # 24px RTL, 16px LTR
        layout.setContentsMargins(m, m, m, m)
        layout.setSpacing(AppStyles.get_spacing(3) if is_rtl else AppStyles.get_spacing(2))
        
        # Scroll area with proper content margins
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.NoFrame)
        scroll_widget = QWidget()
        form_layout = QVBoxLayout(scroll_widget)
        form_layout.setContentsMargins(m, m, m, m)
        form_layout.setSpacing(AppStyles.get_spacing(2))
        
        # Content Selection Group
        content_group = QGroupBox(self.translator.tr('lbl_content_id'))
        content_form = QFormLayout(content_group)
        AppStyles.apply_form_layout_for_language(content_form, is_rtl)
        
        def add_new_content():
            dialog = ContentDialog(self, self.translator.tr('btn_add') + " " + self.translator.tr('tab_contents'), None, self.translator)
            if dialog.exec_() == QDialog.Accepted and dialog.result:
                try:
                    new_id = DatabaseManager.add_content(dialog.result)
                    QMessageBox.information(self, self.translator.tr('msg_success'),
                                          self.translator.tr('msg_record_added'))
                    self.refresh_content_combo()
                    self.content_combo.set_selected_id(new_id)
                    return new_id
                except Exception as e:
                    QMessageBox.critical(self, self.translator.tr('msg_error'), str(e))
            return None
        
        self.content_combo = SearchableComboBox(self, allow_add_new=True, add_callback=add_new_content, translator=self.translator)
        self.refresh_content_combo()
        content_form.addRow(self.translator.tr('lbl_content_id') + " *:", self.content_combo)
        
        # Update source name when content is selected for attachment organization
        self.content_combo.selection_changed.connect(self.on_content_selected)
        
        form_layout.addWidget(content_group)
        
        # Analysis Group
        analysis_group = QGroupBox(self.translator.tr('tab_analysis'))
        analysis_form = QFormLayout(analysis_group)
        AppStyles.apply_form_layout_for_language(analysis_form, is_rtl)
        
        # Classification field with autocomplete
        classification_placeholder = self.translator.tr('msg_type_to_search') if self.translator else "Type to search..."
        self.classification_edit = AutoCompleteLineEdit(self, classification_placeholder, self.translator)
        self.classification_edit.set_suggestions(DatabaseManager.get_distinct_classifications())
        analysis_form.addRow(self.translator.tr('lbl_classification') + ":", self.classification_edit)
        
        # People field with autocomplete suggestions
        self.people_edit = AutoCompleteTextEdit(
            self, 
            separator=',', 
            placeholder=self.translator.tr('msg_type_to_search') if self.translator else "Type to search...",
            translator=self.translator
        )
        self.people_edit.set_suggestions(DatabaseManager.get_distinct_people())
        analysis_form.addRow(self.translator.tr('lbl_people') + ":", self.people_edit)
        
        # Places field with autocomplete suggestions
        self.places_edit = AutoCompleteTextEdit(
            self, 
            separator=',', 
            placeholder=self.translator.tr('msg_type_to_search') if self.translator else "Type to search...",
            translator=self.translator
        )
        self.places_edit.set_suggestions(DatabaseManager.get_distinct_places())
        analysis_form.addRow(self.translator.tr('lbl_places') + ":", self.places_edit)
        
        self.coordinates_widget = CoordinateInputWidget(self, translator=self.translator)
        analysis_form.addRow(self.translator.tr('lbl_coordinates') + ":", self.coordinates_widget)
        
        # Sides field with autocomplete suggestions
        self.sides_edit = AutoCompleteTextEdit(
            self, 
            separator=',', 
            placeholder=self.translator.tr('msg_type_to_search') if self.translator else "Type to search...",
            translator=self.translator
        )
        self.sides_edit.set_suggestions(DatabaseManager.get_distinct_sides())
        analysis_form.addRow(self.translator.tr('lbl_sides') + ":", self.sides_edit)
        
        form_layout.addWidget(analysis_group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons - properly aligned in a single row, extra spacing for RTL
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignVCenter)  # Vertical center alignment
        btn_spacing = AppStyles.get_spacing(3) if is_rtl else AppStyles.get_spacing(2)  # 24px RTL
        btn_layout.setSpacing(btn_spacing)
        btn_layout.addStretch()
        
        btn_save = QPushButton()
        setup_icon_button(btn_save, 'btn_save', self.translator.tr('btn_save'))
        # Disable autoDefault to prevent Enter key from triggering save unexpectedly
        btn_save.setAutoDefault(False)
        btn_save.setDefault(False)
        btn_save.clicked.connect(self.save)
        
        btn_cancel = QPushButton()
        setup_icon_button(btn_cancel, 'btn_cancel', self.translator.tr('btn_cancel'))
        btn_cancel.setAutoDefault(False)
        btn_cancel.setDefault(False)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save, alignment=Qt.AlignVCenter)
        btn_layout.addWidget(btn_cancel, alignment=Qt.AlignVCenter)
        layout.addLayout(btn_layout)
    
    def on_content_selected(self, content_id):
        """Track the content currently associated with the analysis form."""
        self.selected_content_id = content_id
        # Keeping this state explicit makes the selection available to future
        # attachment/link actions without performing an implicit database write.
        self.content_combo.setToolTip(
            self.translator.tr('lbl_content_id') + f": {content_id}"
            if content_id else self.translator.tr('lbl_content_id')
        )
    
    def refresh_content_combo(self):
        """Refresh content combo box"""
        contents = DatabaseManager.get_all_contents()
        items = []
        for c in contents:
            content_text = c.get('content_data', '')[:50] + '...' if len(c.get('content_data', '')) > 50 else c.get('content_data', '')
            items.append({'id': c['id'], 'text': f"ID {c['id']}: {content_text}", 'name': content_text})
        self.content_combo.set_items(items)
    
    def populate_data(self, data: Dict):
        """Populate form with existing data"""
        content_id = data.get('content_id')
        self.refresh_content_combo()
        if content_id:
            self.content_combo.set_selected_id(content_id)
        
        self.classification_edit.setText(str(data.get('classification', '')))
        self.people_edit.set_value(str(data.get('list_names_people', '')))
        self.places_edit.set_value(str(data.get('list_names_places', '')))
        # Try both 'coordinates' (aliased) and 'list_coordinates' (database field) for backward compatibility
        coord_value = data.get('coordinates') or data.get('list_coordinates') or ''
        self.coordinates_widget.set_value(str(coord_value))
        self.sides_edit.set_value(str(data.get('list_sides', '')))
    
    def save(self):
        """Save form data"""
        content_id = self.content_combo.get_selected_id()
        if not content_id:
            QMessageBox.warning(self, self.translator.tr('msg_validation_error') if hasattr(self.translator, 'tr') else 'Validation Error',
                              self.translator.tr('lbl_content_id') + ' is required')
            return
        
        data = {
            'content_id': content_id,
            'classification': self.classification_edit.text().strip() or None,
            'list_names_people': self.people_edit.get_value() or None,
            'list_names_places': self.places_edit.get_value() or None,
            'coordinates': self.coordinates_widget.get_value() or None,
            'list_sides': self.sides_edit.get_value() or None,
            'date_creation': datetime.now() if not self.analysis_data else None
        }
        
        # Validate using validation system
        from utils.data_validation import get_validator
        validator = get_validator()
        is_valid, errors = validator.validate('content_analysis', data)
        
        if not is_valid:
            QMessageBox.warning(self,
                              self.translator.tr('validation_error') if hasattr(self.translator, 'tr') else 'Validation Error',
                              '\n'.join(errors))
            return
        
        self.result = data
        self.accept()
