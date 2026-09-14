"""
Full Text Preview Panel Widget
Displays the complete text content of selected records
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QScrollArea, QFrame, QSplitter, QGroupBox,
    QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette
from translations.translations import TranslationManager
from styles.styles import AppStyles


class TextPreviewPanel(QWidget):
    """
    A collapsible panel for displaying full text content of selected records.
    Shows key fields with proper formatting and scrolling.
    """
    
    # Signal emitted when panel is toggled
    toggled = pyqtSignal(bool)
    
    def __init__(self, translator: TranslationManager, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.is_expanded = False  # Collapsed by default
        self.current_data = {}
        
        # Apply RTL/LTR direction based on current language
        from PyQt5.QtCore import Qt
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the preview panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header bar with toggle button
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet(AppStyles.get_component_style('preview_header'))
        header_layout = QHBoxLayout(self.header_frame)
        # Use 8px grid spacing
        header_margin = AppStyles.get_spacing(2)  # 16px horizontal
        header_vertical = AppStyles.get_spacing(1)  # 8px vertical
        header_layout.setContentsMargins(header_margin, header_vertical, header_margin, header_vertical)
        
        # Title label
        self.title_label = QLabel(self.translator.tr('lbl_full_text_preview'))
        self.title_label.setStyleSheet(AppStyles.get_component_style('preview_title'))
        
        # Toggle button
        self.toggle_btn = QPushButton("▼")
        self.toggle_btn.setFixedSize(28, 28)
        self.toggle_btn.setStyleSheet(AppStyles.get_component_style('preview_toggle'))
        self.toggle_btn.clicked.connect(self.toggle_panel)
        self.toggle_btn.setToolTip(self.translator.tr('btn_toggle_preview'))
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.toggle_btn)
        
        layout.addWidget(self.header_frame)
        
        # Content area
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet(AppStyles.get_component_style('preview_content'))
        content_layout = QVBoxLayout(self.content_frame)
        # Use 8px grid spacing
        content_margin = AppStyles.get_spacing(2)  # 16px
        content_spacing = AppStyles.get_spacing(2)  # 16px
        content_layout.setContentsMargins(content_margin, content_margin, content_margin, content_margin)
        content_layout.setSpacing(content_spacing)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(AppStyles.get_component_style('scroll_area_transparent'))
        
        # Content widget inside scroll area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid
        
        # Create field containers
        self.field_widgets = {}
        
        # Primary text field (large display)
        self.primary_group = self.create_text_group(
            self.translator.tr('lbl_content_data'),
            is_primary=True
        )
        self.content_layout.addWidget(self.primary_group)
        
        # Secondary fields in a grid-like layout
        secondary_frame = QFrame()
        secondary_layout = QHBoxLayout(secondary_frame)
        secondary_layout.setContentsMargins(0, 0, 0, 0)
        secondary_layout.setSpacing(AppStyles.get_spacing(2))  # 16px - 8px grid
        
        # Left column
        left_col = QVBoxLayout()
        left_col.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid
        
        self.field_widgets['title'] = self.create_field_widget(self.translator.tr('lbl_title'))
        self.field_widgets['source'] = self.create_field_widget(self.translator.tr('lbl_source'))
        self.field_widgets['type'] = self.create_field_widget(self.translator.tr('lbl_type'))
        self.field_widgets['classification'] = self.create_field_widget(self.translator.tr('lbl_classification'))
        
        left_col.addWidget(self.field_widgets['title'])
        left_col.addWidget(self.field_widgets['source'])
        left_col.addWidget(self.field_widgets['type'])
        left_col.addWidget(self.field_widgets['classification'])
        left_col.addStretch()
        
        # Right column
        right_col = QVBoxLayout()
        right_col.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid
        
        self.field_widgets['importance'] = self.create_field_widget(self.translator.tr('lbl_importance'))
        self.field_widgets['date'] = self.create_field_widget(self.translator.tr('lbl_date'))
        self.field_widgets['people'] = self.create_field_widget(self.translator.tr('lbl_people'))
        self.field_widgets['places'] = self.create_field_widget(self.translator.tr('lbl_places'))
        
        right_col.addWidget(self.field_widgets['importance'])
        right_col.addWidget(self.field_widgets['date'])
        right_col.addWidget(self.field_widgets['people'])
        right_col.addWidget(self.field_widgets['places'])
        right_col.addStretch()
        
        secondary_layout.addLayout(left_col)
        secondary_layout.addLayout(right_col)
        
        self.content_layout.addWidget(secondary_frame)
        
        # Notes section
        self.notes_group = self.create_text_group(
            self.translator.tr('lbl_note'),
            is_primary=False
        )
        self.content_layout.addWidget(self.notes_group)
        
        # Description section
        self.description_group = self.create_text_group(
            self.translator.tr('lbl_description'),
            is_primary=False
        )
        self.content_layout.addWidget(self.description_group)
        
        self.content_layout.addStretch()
        
        scroll.setWidget(self.content_widget)
        content_layout.addWidget(scroll)
        
        layout.addWidget(self.content_frame)
        
        # Set initial size (collapsed by default)
        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        
        # Collapse panel by default
        self.content_frame.setVisible(False)
        self.toggle_btn.setText("▲")
        
        # Show placeholder
        self.show_placeholder()
    
    def create_text_group(self, title: str, is_primary: bool = False) -> QGroupBox:
        """Create a group box for text content"""
        group = QGroupBox(title)
        style_name = 'text_group_primary' if is_primary else 'text_group'
        group.setStyleSheet(AppStyles.get_component_style(style_name))
        
        layout = QVBoxLayout(group)
        # Use 8px grid spacing
        group_margin_h = AppStyles.get_spacing(1)  # 8px horizontal
        group_margin_v = AppStyles.get_spacing(2)  # 16px vertical
        layout.setContentsMargins(group_margin_h, group_margin_v, group_margin_h, group_margin_h)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit_style = 'text_edit_primary' if is_primary else 'text_edit_secondary'
        text_edit.setStyleSheet(AppStyles.get_component_style(text_edit_style))
        text_edit.setMinimumHeight(80 if is_primary else 50)
        text_edit.setMaximumHeight(200 if is_primary else 100)
        layout.addWidget(text_edit)
        
        # Store reference to text edit
        group.text_edit = text_edit
        return group
    
    def create_field_widget(self, label_text: str) -> QWidget:
        """Create a single field display widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(AppStyles.get_spacing(1))  # 8px - 8px grid
        
        label = QLabel(label_text)
        label.setStyleSheet(AppStyles.get_component_style('field_label'))
        
        value = QLabel("-")
        value.setStyleSheet(AppStyles.get_component_style('field_value'))
        value.setWordWrap(True)
        
        layout.addWidget(label)
        layout.addWidget(value)
        
        # Store reference to value label
        widget.value_label = value
        return widget
    
    def toggle_panel(self):
        """Toggle panel expansion"""
        self.is_expanded = not self.is_expanded
        self.content_frame.setVisible(self.is_expanded)
        self.toggle_btn.setText("▼" if self.is_expanded else "▲")
        
        if self.is_expanded:
            self.setMinimumHeight(250)
            self.setMaximumHeight(400)
        else:
            self.setMinimumHeight(40)
            self.setMaximumHeight(40)
        
        self.toggled.emit(self.is_expanded)
    
    def show_placeholder(self):
        """Show placeholder when no data selected"""
        placeholder_text = self.translator.tr('msg_select_record_to_preview')
        
        # Set placeholder in primary text
        self.primary_group.text_edit.setHtml(f"""
            <div style="text-align: center; color: #95A5A6; padding: 20px;">
                <p style="font-size: 12pt;">📋</p>
                <p>{placeholder_text}</p>
            </div>
        """)
        
        # Clear other fields
        for widget in self.field_widgets.values():
            widget.value_label.setText("-")
        
        self.notes_group.text_edit.clear()
        self.description_group.text_edit.clear()
        self.notes_group.setVisible(False)
        self.description_group.setVisible(False)
    
    def update_preview(self, data: dict):
        """Update preview with selected row data"""
        if not data:
            self.show_placeholder()
            return
        
        self.current_data = data
        
        # Map data keys to display
        # Handle different naming conventions from different tables
        content_text = (
            data.get('content_data') or 
            data.get('description') or 
            data.get('note') or 
            ''
        )
        
        # Update primary content
        if content_text:
            self.primary_group.text_edit.setPlainText(str(content_text))
            self.primary_group.setVisible(True)
        else:
            self.primary_group.setVisible(False)
        
        # Update title
        title = data.get('title') or data.get('content_title') or data.get('name') or '-'
        self.field_widgets['title'].value_label.setText(str(title))
        
        # Update source
        source = data.get('source_name') or data.get('source') or '-'
        self.field_widgets['source'].value_label.setText(str(source))
        
        # Update type
        type_val = (
            data.get('type') or 
            data.get('source_type') or 
            data.get('record_type') or 
            '-'
        )
        self.field_widgets['type'].value_label.setText(str(type_val))
        
        # Update classification
        classification = data.get('classification') or '-'
        self.field_widgets['classification'].value_label.setText(str(classification))
        
        # Update importance
        importance = data.get('importance') or data.get('source_importance') or data.get('content_importance')
        if importance is not None:
            try:
                importance_val = f"{float(importance):.1f}%"
            except:
                importance_val = str(importance)
        else:
            importance_val = '-'
        self.field_widgets['importance'].value_label.setText(importance_val)
        
        # Update date
        date_val = (
            data.get('date_content') or 
            data.get('date_creation') or 
            data.get('date_entry') or
            data.get('date_analysis') or
            data.get('source_date_creation') or
            '-'
        )
        if date_val and date_val != '-':
            # Format date if it's a datetime object
            if hasattr(date_val, 'strftime'):
                date_val = date_val.strftime('%Y-%m-%d')
            else:
                date_val = str(date_val)[:10]
        self.field_widgets['date'].value_label.setText(str(date_val))
        
        # Update people
        people = data.get('list_names_people') or '-'
        self.field_widgets['people'].value_label.setText(str(people))
        
        # Update places
        places = data.get('list_names_places') or '-'
        self.field_widgets['places'].value_label.setText(str(places))
        
        # Update notes
        note = data.get('note') or data.get('content_note') or data.get('source_note')
        if note and str(note).strip() and note != content_text:
            self.notes_group.text_edit.setPlainText(str(note))
            self.notes_group.setVisible(True)
        else:
            self.notes_group.setVisible(False)
        
        # Update description (if different from main content)
        description = data.get('description') or data.get('source_description')
        if description and str(description).strip() and description != content_text:
            self.description_group.text_edit.setPlainText(str(description))
            self.description_group.setVisible(True)
        else:
            self.description_group.setVisible(False)
    
    def clear_preview(self):
        """Clear the preview panel"""
        self.current_data = {}
        self.show_placeholder()
    
    def refresh_translations(self):
        """Refresh translations when language changes"""
        # Apply RTL/LTR layout direction
        is_rtl = self.translator.current_language == 'ar'
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight
        self.setLayoutDirection(direction)
        
        # Apply to all child widgets
        from PyQt5.QtWidgets import QWidget as QW
        for child in self.findChildren(QW):
            child.setLayoutDirection(direction)
        
        self.title_label.setText(self.translator.tr('lbl_full_text_preview'))
        self.toggle_btn.setToolTip(self.translator.tr('btn_toggle_preview'))
        
        # Update field labels
        self.primary_group.setTitle(self.translator.tr('lbl_content_data'))
        self.notes_group.setTitle(self.translator.tr('lbl_note'))
        self.description_group.setTitle(self.translator.tr('lbl_description'))
        
        # Update field widget labels
        field_translations = {
            'title': 'lbl_title',
            'source': 'lbl_source',
            'type': 'lbl_type',
            'classification': 'lbl_classification',
            'importance': 'lbl_importance',
            'date': 'lbl_date',
            'people': 'lbl_people',
            'places': 'lbl_places'
        }
        
        for field_key, tr_key in field_translations.items():
            if field_key in self.field_widgets:
                widget = self.field_widgets[field_key]
                # Find the label in the widget's layout
                layout = widget.layout()
                if layout and layout.count() > 0:
                    label_item = layout.itemAt(0)
                    if label_item and label_item.widget():
                        label_item.widget().setText(self.translator.tr(tr_key))
        
        # Refresh placeholder if no data
        if not self.current_data:
            self.show_placeholder()
