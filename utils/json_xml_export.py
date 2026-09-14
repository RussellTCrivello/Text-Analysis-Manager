"""
JSON and XML Export Utilities
Provides export functionality for JSON and XML formats
"""
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


def export_to_json(data: List[Dict], filepath: str, indent: int = 2, 
                   pretty: bool = True) -> bool:
    """
    Export data to JSON format
    
    Args:
        data: List of dictionaries to export
        filepath: Output file path
        indent: JSON indentation level
        pretty: Whether to format JSON nicely
    
    Returns:
        True if successful, False otherwise
    """
    try:
        export_data = {
            'export_date': datetime.now().isoformat(),
            'record_count': len(data),
            'records': data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(export_data, f, indent=indent, ensure_ascii=False, default=str)
            else:
                json.dump(export_data, f, ensure_ascii=False, default=str)
        
        logger.info(f"Exported {len(data)} records to JSON: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        return False


def export_to_xml(data: List[Dict], filepath: str, root_name: str = 'records',
                  record_name: str = 'record', pretty: bool = True) -> bool:
    """
    Export data to XML format
    
    Args:
        data: List of dictionaries to export
        filepath: Output file path
        root_name: Root element name
        record_name: Individual record element name
        pretty: Whether to format XML nicely
    
    Returns:
        True if successful, False otherwise
    """
    try:
        root = ET.Element(root_name)
        root.set('export_date', datetime.now().isoformat())
        root.set('record_count', str(len(data)))
        
        for record in data:
            record_elem = ET.SubElement(root, record_name)
            for key, value in record.items():
                if value is not None:
                    field_elem = ET.SubElement(record_elem, str(key))
                    field_elem.text = str(value)
        
        tree = ET.ElementTree(root)
        
        if pretty:
            # Pretty print XML
            from xml.dom import minidom
            xml_str = ET.tostring(root, encoding='unicode')
            dom = minidom.parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent="  ")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
        else:
            tree.write(filepath, encoding='utf-8', xml_declaration=True)
        
        logger.info(f"Exported {len(data)} records to XML: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error exporting to XML: {e}")
        return False


def export_to_json_lines(data: List[Dict], filepath: str) -> bool:
    """
    Export data to JSON Lines format (one JSON object per line)
    
    Args:
        data: List of dictionaries to export
        filepath: Output file path
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            for record in data:
                json_line = json.dumps(record, ensure_ascii=False, default=str)
                f.write(json_line + '\n')
        
        logger.info(f"Exported {len(data)} records to JSON Lines: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error exporting to JSON Lines: {e}")
        return False
