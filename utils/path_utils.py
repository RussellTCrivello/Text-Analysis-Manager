"""
Path Utilities for Installable Application
==========================================
Centralized path resolution for both development and installed (frozen) modes.

When installed (PyInstaller):
- User data (config, logs, backups, etc.) goes to %APPDATA%\\TextAnalysisManager\\
- Bundled resources (icons, default config) are read from exe folder or _MEIPASS

This ensures the app works correctly when installed in Program Files (read-only).
"""
import os
import sys
from pathlib import Path
from typing import Optional

# App data folder name
APP_DATA_FOLDER = "TextAnalysisManager"


def is_frozen() -> bool:
    """Check if running as compiled executable (PyInstaller)"""
    return getattr(sys, 'frozen', False)


def is_single_file_build() -> bool:
    """Check if running as single-file PyInstaller build (has _MEIPASS)"""
    return is_frozen() and hasattr(sys, '_MEIPASS')


def get_app_data_dir() -> Path:
    """
    Get the user data directory (writable).
    Use for: config, logs, backups, search history, attachments, etc.
    
    Windows: %APPDATA%\\TextAnalysisManager
    Linux/Mac: ~/.TextAnalysisManager
    """
    if sys.platform == 'win32':
        appdata = os.environ.get('APPDATA', '')
        if not appdata:
            appdata = os.path.expanduser('~')
        base = Path(appdata) / APP_DATA_FOLDER
    else:
        base = Path.home() / f'.{APP_DATA_FOLDER}'
    
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_bundle_dir() -> Path:
    """
    Get the directory containing bundled application resources (read-only for single-file).
    Use for: reading default config, icons, translations, styles.
    
    - Single-file build: sys._MEIPASS (extracted temp folder)
    - Folder build: directory containing the executable
    - Development: project root
    """
    if is_frozen():
        if is_single_file_build():
            return Path(sys._MEIPASS)
        else:
            return Path(sys.executable).parent
    else:
        # Development: project root (parent of utils/)
        return Path(__file__).resolve().parent.parent


def get_config_dir() -> Path:
    """
    Get config directory for reading/writing user configuration.
    Always uses AppData when frozen to allow writes from Program Files.
    """
    if is_frozen():
        config_dir = get_app_data_dir() / 'config'
    else:
        config_dir = get_bundle_dir() / 'config'
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_logs_dir() -> Path:
    """Get logs directory. Uses AppData when frozen."""
    if is_frozen():
        logs_dir = get_app_data_dir() / 'logs'
    else:
        logs_dir = get_bundle_dir() / 'logs'
    
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_data_dir() -> Path:
    """Get general data directory (search history, etc.). Uses AppData when frozen."""
    if is_frozen():
        data_dir = get_app_data_dir() / 'data'
    else:
        data_dir = get_bundle_dir() / 'data'
    
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_backups_dir() -> Path:
    """Get backups directory. Uses AppData when frozen."""
    if is_frozen():
        backups_dir = get_app_data_dir() / 'backups'
    else:
        backups_dir = get_bundle_dir() / 'backups'
    
    backups_dir.mkdir(parents=True, exist_ok=True)
    return backups_dir


def get_icons_dir() -> Path:
    """
    Get icons directory for loading icon files.
    Uses bundle dir (resources are bundled with the app).
    """
    bundle = get_bundle_dir()
    # Try icons/images (standard structure)
    icons_dir = bundle / 'icons' / 'images'
    if icons_dir.exists():
        return icons_dir
    # Fallback
    return bundle / 'icons' / 'images'


def get_default_config_path() -> Optional[Path]:
    """
    Get path to default/bundled config (for first-run copy).
    Returns None if no bundled config exists.
    """
    bundle_config = get_bundle_dir() / 'config' / 'config.ini'
    if bundle_config.exists():
        return bundle_config
    return None
