"""
Help System
Provides built-in help documentation and tooltips
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QTreeWidget, QTreeWidgetItem, QSplitter,
    QDialog, QTabWidget, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from typing import Dict
from styles.styles import AppStyles
from translations.translations import TranslationManager


class HelpContent:
    """Help content manager"""
    
    def __init__(self, translator: TranslationManager):
        self.translator = translator
        self.content = self.load_help_content()
    
    def load_help_content(self) -> Dict:
        """Load help content"""
        return {
            'getting_started': {
                'title': 'Getting Started',
                'content': """
# Getting Started

Welcome to the Text Analysis Application!

## Overview
This application helps you manage and analyze text data from various sources.

## Main Features
- **Sources Tab**: Manage information sources
- **Contents Tab**: Manage content records
- **Analysis Tab**: Perform content analysis
- **All Data Tab**: Unified view of all data
- **Reports Tab**: Create custom reports and charts

## Quick Start
1. Start by adding sources in the Sources tab
2. Add content linked to sources in the Contents tab
3. Create analysis records in the Analysis tab
4. Use the Reports tab to generate insights

## Keyboard Shortcuts
- Ctrl+1: Sources tab
- Ctrl+2: Contents tab
- Ctrl+3: Analysis tab
- Ctrl+4: All Data tab
- Ctrl+5: Timeline tab
- Ctrl+6: Reports tab
- Ctrl+Q: Exit application
                """
            },
            'sources': {
                'title': 'Sources Management',
                'content': """
# Sources Management

The Sources tab allows you to manage information sources.

## Adding a Source
1. Click the "Add" button
2. Fill in the source details
3. Click "OK" to save

## Fields
- **Name**: Source name (required)
- **Type**: Type of source
- **Link**: URL to source
- **Importance**: Importance level (0-100%)
- **Country/City**: Geographic location
- **Description**: Detailed description
- **Accounts**: Associated accounts
- **Note**: Additional notes

## Operations
- **Import**: Import sources from CSV
- **Duplicate**: Create a copy of a source
- **Statistics**: View source statistics
- **Export**: Export to various formats
                """
            },
            'contents': {
                'title': 'Contents Management',
                'content': """
# Contents Management

The Contents tab manages content records linked to sources.

## Adding Content
1. Click the "Add" button
2. Select a source
3. Enter content details
4. Attach files if needed
5. Click "OK" to save

## Fields
- **Source**: Link to source (required)
- **Title**: Content title (required)
- **Content Data**: Main content text
- **Importance**: Importance level
- **Attachments**: File attachments
- **Note**: Additional notes

## Operations
- **View Attachments**: View attached files
- **Link to Analysis**: Create analysis from content
- **Preview**: Preview full content
- **Export**: Export to various formats
                """
            },
            'analysis': {
                'title': 'Content Analysis',
                'content': """
# Content Analysis

The Analysis tab performs detailed analysis of content.

## Creating Analysis
1. Click the "Add" button
2. Select content to analyze
3. Fill in analysis details
4. Click "OK" to save

## Fields
- **Content**: Link to content (required)
- **Classification**: Content classification
- **People**: List of people mentioned
- **Places**: List of places mentioned
- **Coordinates**: Geographic coordinates
- **Sides**: Involved parties/sides

## Operations
- **View Map**: View coordinates on map
- **Compare**: Compare multiple analyses
- **Summary**: Generate analysis summary
- **Export**: Export to various formats
                """
            },
            'timeline': {
                'title': 'Timeline',
                'content': """
# Timeline

The Timeline tab displays your content and analysis data on a visual timeline.

## Features
- View events chronologically
- Filter by date range, people, places, classification
- Switch between timeline and chart views
- Export timeline data to various formats

## Chart Types
- Timeline Distribution
- Type Distribution
- Day of Week Patterns
- Monthly Aggregation
- Classification Distribution

## Keyboard Shortcuts
- Ctrl+5: Switch to Timeline tab
                """
            },
            'reports': {
                'title': 'Reports and Charts',
                'content': """
# Reports and Charts

The Reports tab allows you to create custom reports and visualizations.

## Creating Reports
1. Use SQL Query Builder to write queries
2. Or use the Report Builder for visual reports
3. Add charts using the Chart Designer
4. Save reports for later use

## Chart Types
- Pie Chart
- Bar Chart
- Line Chart
- Area Chart
- Donut Chart
- Horizontal Bar Chart

## Exporting Reports
Reports can be exported to:
- PDF
- Excel
- Word
- CSV
                """
            },
            'export': {
                'title': 'Export Options',
                'content': """
# Export Options

The application supports multiple export formats.

## Export Formats
- **PDF**: Professional PDF documents
- **Excel**: Spreadsheet format (.xlsx)
- **Word**: Document format (.docx)
- **CSV**: Comma-separated values

## Export Features
- Column selection
- Custom headers/footers
- Page orientation
- Custom formatting
- Export templates

## Using Export Templates
1. Create a template with your preferred settings
2. Save the template
3. Use the template for future exports
                """
            },
            'search': {
                'title': 'Search and Filter',
                'content': """
# Search and Filter

The application provides powerful search and filtering capabilities.

## Basic Search
- Use the search box to find records
- Search across all fields
- Real-time filtering

## Date Filtering
- Filter by date range
- Use date pickers for easy selection
- Clear filters with one click

## Advanced Search
- Use Advanced Search for complex queries
- Build queries with multiple conditions
- Save searches for reuse
                """
            },
            'bulk_operations': {
                'title': 'Bulk Operations',
                'content': """
# Bulk Operations

Perform operations on multiple records at once.

## Bulk Delete
1. Select multiple records
2. Choose Bulk Delete
3. Confirm deletion

## Bulk Edit
1. Select records to edit
2. Choose Bulk Edit
3. Enter new values for fields
4. Apply changes

## Bulk Import
1. Prepare CSV file
2. Choose Bulk Import
3. Select file
4. Preview and import
                """
            }
        }
    
    def get_content(self, key: str) -> Dict:
        """Get help content by key"""
        not_found = {
            'title': self.translator.tr('help_title') if hasattr(self.translator, 'tr') else 'Help',
            'content': self.translator.tr('help_content_not_found') if hasattr(self.translator, 'tr') else 'Content not found'
        }
        return self.content.get(key, not_found)


class HelpDialog(QDialog):
    """Help dialog"""
    
    def __init__(self, parent, translator: TranslationManager):
        super().__init__(parent)
        self.translator = translator
        self.help_content = HelpContent(translator)
        
        self.setWindowTitle(translator.tr('help_title') if hasattr(translator, 'tr') else 'Help')
        # Apply fixed size to prevent resizing on button clicks or content changes
        from styles.styles import AppStyles
        AppStyles.apply_fixed_size(self, 900, 700)
        
        if translator.current_language == 'ar':
            self.setLayoutDirection(Qt.RightToLeft)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        
        # Splitter for navigation and content
        splitter = QSplitter(Qt.Horizontal)
        
        # Navigation tree
        nav_tree = QTreeWidget()
        nav_tree.setHeaderLabel(self.translator.tr('help_topics') if hasattr(self.translator, 'tr') else 'Topics')
        nav_tree.setMaximumWidth(250)
        nav_tree.itemClicked.connect(self.on_topic_selected)
        
        # Add topics - use translation keys
        tr = self.translator.tr if hasattr(self.translator, 'tr') else lambda k: k
        topics = [
            ('getting_started', tr('help_getting_started')),
            ('sources', tr('help_sources')),
            ('contents', tr('help_contents')),
            ('analysis', tr('help_analysis')),
            ('timeline', tr('help_timeline')),
            ('reports', tr('help_reports')),
            ('export', tr('help_export')),
            ('search', tr('help_search_filter')),
            ('bulk_operations', tr('help_bulk_operations'))
        ]
        
        for key, title in topics:
            item = QTreeWidgetItem(nav_tree, [title])
            item.setData(0, Qt.UserRole, key)
        
        nav_tree.expandAll()
        splitter.addWidget(nav_tree)
        
        # Content area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        
        self.content_title = QLabel()
        self.content_title.setFont(QFont('Arial', 14, QFont.Bold))
        content_layout.addWidget(self.content_title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setFont(QFont('Arial', 10))
        scroll.setWidget(self.content_text)
        
        content_layout.addWidget(scroll)
        splitter.addWidget(content_area)
        
        splitter.setSizes([250, 650])
        layout.addWidget(splitter)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_close = QPushButton(self.translator.tr('btn_close') if hasattr(self.translator, 'tr') else 'Close')
        btn_close.setStyleSheet(AppStyles.get_button_style('default'))
        btn_close.setAutoDefault(False)
        btn_close.setDefault(False)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
        # Show first topic
        if nav_tree.topLevelItemCount() > 0:
            nav_tree.setCurrentItem(nav_tree.topLevelItem(0))
            self.on_topic_selected(nav_tree.topLevelItem(0), 0)
    
    def on_topic_selected(self, item: QTreeWidgetItem, column: int):
        """Handle topic selection"""
        key = item.data(0, Qt.UserRole)
        content = self.help_content.get_content(key)
        
        self.content_title.setText(content['title'])
        
        # Convert markdown-like content to HTML
        html_content = content['content'].replace('\n# ', '\n<h2>').replace('\n## ', '\n<h3>')
        html_content = html_content.replace('\n- ', '\n<li>')
        html_content = f"<html><body>{html_content}</body></html>"
        
        self.content_text.setHtml(html_content)


def show_help(parent, translator: TranslationManager):
    """Show help dialog"""
    dialog = HelpDialog(parent, translator)
    dialog.exec_()
