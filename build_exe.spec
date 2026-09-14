# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building Text Analysis Management System executable
Configured for Windows Installer distribution
"""

import sys
from pathlib import Path
import os

block_cipher = None

# Get the base path - handle both SPECPATH (PyInstaller) and direct execution
try:
    base_path = Path(SPECPATH)
except NameError:
    base_path = Path(os.path.dirname(os.path.abspath(__file__)))

# Check if icon exists
icon_path = base_path / 'app_icon.ico'
icon_file = str(icon_path) if icon_path.exists() else None

# Check if version info exists
version_file = base_path / 'file_version_info.txt'
version_info_path = str(version_file) if version_file.exists() else None

a = Analysis(
    ['mainwindow.py'],
    pathex=[str(base_path)],
    binaries=[],
    datas=(
        [('app_icon.ico', '.')] if (base_path / 'app_icon.ico').exists() else []
    ) + [
        ('config', 'config'),
        ('styles', 'styles'),
        ('translations', 'translations'),
        ('widgets', 'widgets'),
        ('dialogs', 'dialogs'),
        ('db', 'db'),
        ('utils', 'utils'),
        ('tabs', 'tabs'),
        ('icons', 'icons'),
        ('icons/images', 'icons/images'),
        ('core', 'core'),
        ('fonts', 'fonts'),
    ],
    hiddenimports=[
        # PyQt5 modules
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtPrintSupport',
        'PyQt5.QtSvg',
        
        # Standard library
        'sqlite3',
        'configparser',
        'json',
        'csv',
        'datetime',
        'decimal',
        'io',
        'pathlib',
        'traceback',
        'threading',
        'functools',
        'dataclasses',
        'enum',
        'typing',
        'collections',
        'shutil',
        'tempfile',
        'uuid',
        'hashlib',
        'base64',
        'xml.etree.ElementTree',
        
        # Database modules
        'db.db_config',
        'db.db_manager',
        
        # Dialog modules
        'dialogs.dialogs',
        'dialogs.settings_dialog',
        'dialogs.advanced_search_dialog',
        'dialogs.backup_restore_dialog',
        'dialogs.bulk_operations_dialog',
        'dialogs.column_selection_dialog',
        'dialogs.export_preview_dialog',
        'dialogs.reset_dialog',
        'dialogs.import_dialog',
        
        # Widget modules
        'widgets.widgets',
        'widgets.preview_attachments',
        'widgets.pagination_widget',
        'widgets.text_preview_panel',
        'widgets.reports_tab',
        'widgets.attachment_manager_widget',
        'widgets.help_system',
        
        # Style modules
        'styles.styles',
        
        # Translation modules
        'translations.translations',
        
        # Utility modules
        'utils.logger',
        'utils.search_history',
        'utils.error_handler',
        'utils.accessibility',
        'utils.performance_monitor',
        'utils.data_validation',
        'utils.backup_restore',
        'utils.attachment_manager',
        'utils.audit_trail',
        'utils.excel_export',
        'utils.word_export',
        'utils.json_xml_export',
        'utils.print_utils',
        'utils.export_templates',
        'utils.path_utils',
        
        # Config modules
        'config.config_manager',
        
        # Tab modules
        'tabs.base_tab',
        'tabs.sources_tab',
        'tabs.contents_tab',
        'tabs.analysis_tab',
        'tabs.all_data_tab',
        'tabs.timeline_tab',
        'dialogs.timeline_export_dialog',
        
        # Icon modules
        'icons.icon_manager',
        
        # Core modules
        'core.toolbar_factory',
        
        # Third-party libraries
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.figure',
        'matplotlib.axes',
        'matplotlib.colors',
        'matplotlib.patches',
        'matplotlib.lines',
        'matplotlib.text',
        'matplotlib.font_manager',
        'matplotlib.backends.backend_qt5agg',
        
        'openpyxl',
        'openpyxl.workbook',
        'openpyxl.styles',
        'openpyxl.utils',
        
        'docx',
        'docx.shared',
        'docx.enum.text',
        'docx.enum.table',
        
        'PIL',
        'PIL.Image',
        
        'arabic_reshaper',
        'bidi',
        'bidi.algorithm',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'test',
        'tests',
        '_pytest',
        'pytest',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Single-file executable (for portable use)
exe_onefile = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TextAnalysisManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
    version=version_info_path,
)

# Folder-based distribution (for installer - faster startup)
exe_folder = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TextAnalysisManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
    version=version_info_path,
)

coll = COLLECT(
    exe_folder,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TextAnalysisManager',
)
