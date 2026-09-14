"""
Export Templates System
Allows users to create and use custom export templates
"""
import json
import os
from typing import Dict, List, Optional
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class ExportTemplate:
    """Export template definition"""
    
    def __init__(self, name: str, description: str = "", table_name: str = ""):
        self.name = name
        self.description = description
        self.table_name = table_name
        self.format = "excel"  # excel, word, pdf, csv
        self.selected_columns: List[str] = []
        self.column_widths: Dict[str, int] = {}
        self.include_header = True
        self.include_footer = False
        self.header_text = ""
        self.footer_text = ""
        self.page_orientation = "landscape"  # portrait, landscape
        self.custom_styles: Dict = {}
        self.filters: Dict = {}
    
    def to_dict(self) -> Dict:
        """Convert template to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'table_name': self.table_name,
            'format': self.format,
            'selected_columns': self.selected_columns,
            'column_widths': self.column_widths,
            'include_header': self.include_header,
            'include_footer': self.include_footer,
            'header_text': self.header_text,
            'footer_text': self.footer_text,
            'page_orientation': self.page_orientation,
            'custom_styles': self.custom_styles,
            'filters': self.filters
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ExportTemplate':
        """Create template from dictionary"""
        template = cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            table_name=data.get('table_name', '')
        )
        template.format = data.get('format', 'excel')
        template.selected_columns = data.get('selected_columns', [])
        template.column_widths = data.get('column_widths', {})
        template.include_header = data.get('include_header', True)
        template.include_footer = data.get('include_footer', False)
        template.header_text = data.get('header_text', '')
        template.footer_text = data.get('footer_text', '')
        template.page_orientation = data.get('page_orientation', 'landscape')
        template.custom_styles = data.get('custom_styles', {})
        template.filters = data.get('filters', {})
        return template


class TemplateManager:
    """Manages export templates"""
    
    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            # Use path_utils for correct path when installed (AppData)
            from utils.path_utils import get_config_dir
            templates_dir = str(get_config_dir() / 'export_templates')
        
        self.templates_dir = templates_dir
        self.ensure_templates_dir()
    
    def ensure_templates_dir(self):
        """Ensure templates directory exists"""
        os.makedirs(self.templates_dir, exist_ok=True)
    
    def save_template(self, template: ExportTemplate) -> bool:
        """Save template to file"""
        try:
            filename = f"{template.name.replace(' ', '_').lower()}.json"
            filepath = os.path.join(self.templates_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved export template: {template.name}")
            return True
        except Exception as e:
            logger.error(f"Error saving template: {e}")
            return False
    
    def load_template(self, name: str) -> Optional[ExportTemplate]:
        """Load template by name"""
        try:
            filename = f"{name.replace(' ', '_').lower()}.json"
            filepath = os.path.join(self.templates_dir, filename)
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return ExportTemplate.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            return None
    
    def list_templates(self, table_name: str = None) -> List[ExportTemplate]:
        """List all templates, optionally filtered by table"""
        templates = []
        
        try:
            for filename in os.listdir(self.templates_dir):
                if filename.endswith('.json'):
                    try:
                        filepath = os.path.join(self.templates_dir, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        template = ExportTemplate.from_dict(data)
                        if table_name is None or template.table_name == table_name:
                            templates.append(template)
                    except Exception as e:
                        logger.warning(f"Error loading template {filename}: {e}")
        except Exception as e:
            logger.error(f"Error listing templates: {e}")
        
        return templates
    
    def delete_template(self, name: str) -> bool:
        """Delete a template"""
        try:
            filename = f"{name.replace(' ', '_').lower()}.json"
            filepath = os.path.join(self.templates_dir, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Deleted template: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            return False
    
    def get_template_names(self, table_name: str = None) -> List[str]:
        """Get list of template names"""
        templates = self.list_templates(table_name)
        return [t.name for t in templates]


# Global template manager instance
_template_manager = None

def get_template_manager() -> TemplateManager:
    """Get global template manager instance"""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager
