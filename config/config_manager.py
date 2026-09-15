"""
Configuration Management System
Handles application and database configuration
Supports both INI and JSON formats
"""
import os
import json
import configparser
import sys
import io
from typing import Any, Dict, Optional
from pathlib import Path

# Set UTF-8 encoding for stdout/stderr on Windows
if sys.platform == 'win32':
    # Check if stdout/stderr exist and have encoding attribute (may be None in compiled executables)
    if sys.stdout is not None and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    elif sys.stdout is not None and not hasattr(sys.stdout, 'encoding'):
        # stdout exists but has no encoding attribute (compiled executable)
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass  # If buffer doesn't exist, skip
    
    if sys.stderr is not None and hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    elif sys.stderr is not None and not hasattr(sys.stderr, 'encoding'):
        # stderr exists but has no encoding attribute (compiled executable)
        try:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass  # If buffer doesn't exist, skip


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_file: str = "config.ini"):
        """Initialize configuration manager"""
        # Use path_utils for correct paths when installed (AppData for user data)
        from utils.path_utils import get_config_dir, get_default_config_path
        
        self.config_dir = get_config_dir()
        self.config_file = self.config_dir / config_file
        self.json_config_file = self.config_dir / "config.json"
        self._default_config_path = get_default_config_path()
        self.config = configparser.ConfigParser()
        self.json_config = {}
        
        # Load configuration (copy from bundled default if first run)
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        # Load INI config - copy from bundled default if first run (installed app)
        if self.config_file.exists():
            self.config.read(self.config_file, encoding='utf-8')
        elif self._default_config_path and self._default_config_path.exists():
            # First run: copy bundled config to user config dir
            import shutil
            try:
                shutil.copy2(self._default_config_path, self.config_file)
                self.config.read(self.config_file, encoding='utf-8')
            except Exception:
                self.create_default_config()
        else:
            self.create_default_config()
        
        # Load JSON config if exists
        if self.json_config_file.exists():
            try:
                with open(self.json_config_file, 'r', encoding='utf-8') as f:
                    self.json_config = json.load(f)
            except Exception:
                self.json_config = {}
    
    def create_default_config(self):
        """Create default configuration file"""
        # Database section
        self.config['Database'] = {
            'host': 'localhost',
            'port': '5432',
            'name': 'research_db',
            'user': 'postgres',
            'password': 'eggarf123',
            'pool_min': '1',
            'pool_max': '10',
            'timeout': '30'
        }
        
        # Application section
        self.config['Application'] = {
            'language': 'en',
            'theme': 'light',
            'font_size': '10',
            'font_family': 'Segoe UI',
            'auto_save': 'true',
            'auto_save_interval': '300',  # seconds
            'page_size': '50',
            'max_undo_history': '50'
        }
        
        # Window section
        self.config['Window'] = {
            'width': '1400',
            'height': '900',
            'x': '50',
            'y': '50',
            'maximized': 'false'
        }
        
        # Logging section
        self.config['Logging'] = {
            'enabled': 'true',
            'level': 'INFO',
            'file_path': 'logs/app.log',
            'max_file_size': '10485760',  # 10MB
            'backup_count': '5',
            'log_database_queries': 'true',
            'log_errors': 'true',
            'log_user_actions': 'true'
        }
        
        # Backup section
        self.config['Backup'] = {
            'enabled': 'true',
            'auto_backup': 'true',
            'auto_backup_interval': '24',  # hours
            'backup_path': 'backups',
            'encryption': 'false',
            'encryption_key': '',
            'max_backups': '30',
            'incremental': 'true'
        }
        
        # Search section
        self.config['Search'] = {
            'max_history': '50',
            'save_filters': 'true',
            'full_text_search': 'true',
            'fuzzy_search': 'true'
        }
        
        # Export section
        self.config['Export'] = {
            'default_format': 'CSV',
            'include_headers': 'true',
            'date_format': 'YYYY-MM-DD HH:MM:SS',
            'number_format': 'standard'
        }
        
        # Accessibility section
        self.config['Accessibility'] = {
            'high_contrast': 'false',
            'font_size_multiplier': '1.0',
            'screen_reader_support': 'true',
            'keyboard_navigation': 'true',
            'focus_indicator': 'true',
            'color_blind_mode': 'none'
        }
        
        # Save default config
        self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
        except Exception as e:
            error_msg = f"Error saving config: {e}"
            try:
                print(error_msg)
            except UnicodeEncodeError:
                # Fallback for console encoding issues
                print(error_msg.encode('ascii', errors='replace').decode('ascii'))
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        try:
            if self.config.has_section(section) and self.config.has_option(section, key):
                value = self.config.get(section, key)
                # Try to convert to appropriate type
                if value.lower() in ('true', 'false'):
                    return value.lower() == 'true'
                try:
                    return int(value)
                except ValueError:
                    try:
                        return float(value)
                    except ValueError:
                        return value
            return default
        except Exception:
            return default
    
    def set(self, section: str, key: str, value: Any):
        """Set configuration value"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        self.save_config()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire section as dictionary"""
        result = {}
        if self.config.has_section(section):
            for key in self.config.options(section):
                result[key] = self.get(section, key)
        return result
    
    def set_section(self, section: str, values: Dict[str, Any]):
        """Set entire section"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        for key, value in values.items():
            self.config.set(section, key, str(value))
        self.save_config()
    
    def get_json(self, key: str, default: Any = None) -> Any:
        """Get value from JSON config"""
        keys = key.split('.')
        value = self.json_config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set_json(self, key: str, value: Any):
        """Set value in JSON config"""
        keys = key.split('.')
        config = self.json_config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        
        # Save JSON config
        self.save_json_config()
    
    def save_json_config(self):
        """Save JSON config to file"""
        try:
            with open(self.json_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.json_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            error_msg = f"Error saving JSON config: {e}"
            try:
                print(error_msg)
            except UnicodeEncodeError:
                # Fallback for console encoding issues
                print(error_msg.encode('ascii', errors='replace').decode('ascii'))
    
    def save_all_to_json(self):
        """Save all INI settings to JSON file"""
        try:
            # Convert all INI sections to JSON
            json_data = {}
            for section in self.config.sections():
                json_data[section] = {}
                for key in self.config.options(section):
                    value = self.get(section, key)
                    json_data[section][key] = value
            
            # Also include existing JSON config
            json_data.update(self.json_config)
            
            # Save to JSON file
            with open(self.json_config_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            
            self.json_config = json_data
            return True
        except Exception as e:
            error_msg = f"Error saving all settings to JSON: {e}"
            try:
                print(error_msg)
            except UnicodeEncodeError:
                # Fallback for console encoding issues
                print(error_msg.encode('ascii', errors='replace').decode('ascii'))
            return False
    
    def get_timeline_density_mode(self) -> str:
        """Get timeline density mode preference"""
        return self.get('Timeline', 'density_mode', 'comfortable')
    
    def set_timeline_density_mode(self, mode: str):
        """Set timeline density mode preference"""
        if mode not in ['compact', 'comfortable', 'expansive']:
            mode = 'comfortable'
        self.set('Timeline', 'density_mode', mode)


# Global config instance
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
