# Build Instructions for Text Analysis Manager

This document explains how to build the Text Analysis Manager application into a distributable Windows installer.

## Prerequisites

### 1. Python Environment
- Python 3.8 or later (Python 3.11 recommended)
- pip (Python package manager)

### 2. Required Python Packages
Install all dependencies:
```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 3. Inno Setup (for creating the installer)
Download and install Inno Setup from: https://jrsoftware.org/isinfo.php

**Important:** Install to the default location (`C:\Program Files (x86)\Inno Setup 6\`)

## Build Commands

### Quick Build (Everything)
To build the complete installer package:
```bash
python build.py
```

This will:
1. Check and install dependencies
2. Generate application icons
3. Build the executable with PyInstaller
4. Create the Windows installer with Inno Setup

### Individual Build Steps

#### Generate Icons Only
```bash
python build.py --icons
```

#### Build Executable Only
```bash
python build.py --exe
```

#### Build Installer Only (requires exe first)
```bash
python build.py --installer
```

#### Build Portable Version
Creates a single-file portable executable:
```bash
python build.py --portable
```

#### Clean Build Artifacts
```bash
python build.py --clean
```

## Output Files

After a successful build, you'll find:

| File | Location | Description |
|------|----------|-------------|
| Executable | `dist/TextAnalysisManager/TextAnalysisManager.exe` | Main application (folder-based) |
| Installer | `installer_output/TextAnalysisManager_Setup_2.1.0.exe` | Windows installer |
| Portable | `portable/TextAnalysisManager_Portable_2.1.0.exe` | Single-file portable version |

## Project Structure

```
txt_analysis/
├── build.py                 # Main build script
├── build_exe.spec          # PyInstaller configuration
├── installer.iss           # Inno Setup script
├── create_icon.py          # Icon generator
├── version_info.py         # Version constants
├── file_version_info.txt   # Windows version resource
├── app_icon.ico           # Application icon (generated)
├── uninstall_icon.ico     # Uninstall icon (generated)
├── LICENSE.txt            # License file
├── README.txt             # User readme
├── requirements.txt       # Python dependencies
├── mainwindow.py          # Main application entry point
├── config/                # Configuration modules
├── core/                  # Core functionality
├── db/                    # Database modules
├── dialogs/               # Dialog windows
├── fonts/                 # Font files
├── icons/                 # Icon resources
├── logs/                  # Log files
├── styles/                # Style definitions
├── tabs/                  # Tab widgets
├── translations/          # Language translations
├── utils/                 # Utility modules
└── widgets/               # Custom widgets
```

## Customization

### Changing Version Number
Edit `version_info.py` and `installer.iss`:
- `version_info.py`: Update `VERSION_MAJOR`, `VERSION_MINOR`, `VERSION_PATCH`
- `installer.iss`: Update `#define MyAppVersion`
- `file_version_info.txt`: Update version numbers

### Changing Application Name
Edit these files:
- `version_info.py`: `APP_NAME` and related constants
- `installer.iss`: `#define MyAppName`
- `build.py`: `APP_NAME` constant
- `build_exe.spec`: `name` parameter in EXE()

### Customizing the Installer
The installer (`installer.iss`) is a full-featured installation program with:

**Installation Features:**
- **License Agreement**: Users must accept the license before installation
- **Installation Types**: Full, Compact, and Custom installation options
- **Component Selection**: Choose which components to install (core files, documentation, shortcuts)
- **Task Selection**: Optional desktop shortcut, Quick Launch icon, startup entry
- **Previous Version Detection**: Automatically detects and offers to uninstall previous versions
- **Disk Space Check**: Warns if insufficient disk space is available
- **Progress Tracking**: Visual progress indicators during installation and uninstallation

**Windows Integration:**
- **Registry Entries**: Proper Windows registry integration for uninstaller
- **Start Menu Integration**: Creates Start Menu shortcuts with uninstall option
- **User Data Management**: Separates application files from user data
- **Uninstaller**: Full-featured uninstaller with data preservation options

**User Experience:**
- **Modern Wizard Interface**: Modern, professional installer appearance
- **Post-Installation Options**: Option to launch application after installation
- **Data Preservation**: Prompts to preserve user data during uninstallation
- **Installation Logging**: Creates installation logs for troubleshooting

Edit `installer.iss` to:
- Change installation directory
- Add/remove shortcuts
- Modify installer appearance
- Add file associations
- Change compression settings
- Customize installation types and components

### Customizing the Icon
Either:
1. Replace `app_icon.ico` with your own icon
2. Or modify `create_icon.py` to generate a different design

## Troubleshooting

### PyInstaller Errors

**"ModuleNotFoundError"**
Add the missing module to `hiddenimports` in `build_exe.spec`:
```python
hiddenimports=[
    ...
    'missing_module',
],
```

**Large executable size**
Add unused modules to `excludes` in `build_exe.spec`:
```python
excludes=[
    'tkinter',
    'test',
    ...
],
```

### Inno Setup Errors

**"ISCC not found"**
- Install Inno Setup from https://jrsoftware.org/isinfo.php
- Or add ISCC.exe to your PATH

**"Source file not found"**
- Ensure the executable was built first (`python build.py --exe`)
- Check that `dist/TextAnalysisManager/` exists

### Runtime Errors

**Application won't start**
1. Run from command line to see error messages:
   ```bash
   cd dist\TextAnalysisManager
   TextAnalysisManager.exe
   ```
2. Check logs in `%APPDATA%\TextAnalysisManager\logs\`

**Missing DLL errors**
- Ensure all Visual C++ Redistributables are installed
- PyInstaller should include necessary DLLs automatically

## Distribution

### For End Users
Distribute the installer file:
```
installer_output/TextAnalysisManager_Setup_2.1.0.exe
```

### For Portable Use
Distribute the portable executable:
```
portable/TextAnalysisManager_Portable_2.1.0.exe
```

### Testing the Installer
1. Build the installer
2. Test on a clean Windows VM or machine
3. Verify:
   - License agreement is displayed and accepted
   - Installation type selection works (Full/Compact/Custom)
   - Component selection works correctly
   - Task selection (desktop icon, startup) works
   - Previous version detection and uninstallation works
   - Installation completes successfully
   - Application launches correctly
   - All features work
   - Registry entries are created correctly
   - Uninstallation is clean
   - Data preservation option works during uninstall
   - Installation info file is created in user data directory

## Signing the Installer (Optional)

For distribution outside your organization, consider code signing:

1. Obtain a code signing certificate
2. Sign the executable:
   ```bash
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\TextAnalysisManager\TextAnalysisManager.exe
   ```
3. Sign the installer:
   ```bash
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com installer_output\TextAnalysisManager_Setup_2.1.0.exe
   ```

## Support

For issues or questions, refer to:
- This document
- The project repository
- Log files in `%APPDATA%\TextAnalysisManager\logs\`
