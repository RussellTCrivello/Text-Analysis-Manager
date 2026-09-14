"""
Build Script for Text Analysis Manager
Creates a standalone executable and Windows installer

Usage:
    python build.py              # Build everything (exe + installer)
    python build.py --exe        # Build only the executable
    python build.py --installer  # Build installer (requires exe first)
    python build.py --portable   # Build portable single-file exe
    python build.py --clean      # Clean build artifacts
    python build.py --icons      # Generate application icons
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path
import argparse


# Build configuration
APP_NAME = "TextAnalysisManager"
VERSION = "2.1.0"


def get_base_path():
    """Get the base path of the project"""
    return Path(__file__).parent.resolve()


def print_header(message: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {message}")
    print("=" * 60 + "\n")


def print_step(message: str):
    """Print a step message"""
    print(f">>> {message}")


def check_python_dependencies():
    """Check and install required Python dependencies"""
    print_step("Checking Python dependencies...")
    
    required = [
        'PyQt5',
        'pyinstaller', 
        'Pillow',
        'python-docx',
        'openpyxl',
        'matplotlib',
        'arabic_reshaper',
        'python-bidi'
    ]
    
    missing = []
    for package in required:
        package_name = package.replace('-', '_').lower()
        # Special cases
        if package == 'python-docx':
            package_name = 'docx'
        elif package == 'python-bidi':
            package_name = 'bidi'
        
        try:
            __import__(package_name)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"  Missing dependencies: {', '.join(missing)}")
        print("  Installing missing dependencies...")
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install'] + missing,
            check=True
        )
        print("  Dependencies installed successfully!")
    else:
        print("  All dependencies are installed.")


def check_inno_setup():
    """Check if Inno Setup is installed"""
    print_step("Checking for Inno Setup Compiler...")
    
    # Common installation paths for Inno Setup
    possible_paths = [
        Path(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')) / 'Inno Setup 6' / 'ISCC.exe',
        Path(os.environ.get('ProgramFiles', 'C:\\Program Files')) / 'Inno Setup 6' / 'ISCC.exe',
        Path(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')) / 'Inno Setup 5' / 'ISCC.exe',
        Path('C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe'),
        Path('C:\\Program Files\\Inno Setup 6\\ISCC.exe'),
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"  Found: {path}")
            return str(path)
    
    # Try to find in PATH
    try:
        result = subprocess.run(
            ['where', 'ISCC.exe'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            iscc_path = result.stdout.strip().split('\n')[0]
            print(f"  Found in PATH: {iscc_path}")
            return iscc_path
    except Exception:
        pass
    
    print("  WARNING: Inno Setup not found!")
    print("  Please install Inno Setup from: https://jrsoftware.org/isinfo.php")
    return None


def create_directories():
    """Create required directories"""
    print_step("Creating required directories...")
    
    base_path = get_base_path()
    dirs = ['data', 'logs', 'config', 'backups', 'installer_output']
    
    for dir_name in dirs:
        dir_path = base_path / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"  Ensured: {dir_path}")


# def generate_icons():
#     """Generate application icons"""
#     print_header("Generating Application Icons")
    
#     base_path = get_base_path()
#     icon_path = base_path / 'app_icon.ico'
    
#     if icon_path.exists():
#         print_step("Icons already exist. Skipping generation.")
#         return True
    
#     print_step("Running icon generator...")
    
#     try:
#         # Import and run the distinctive icon generator
#         sys.path.insert(0, str(base_path))
#         from create_distinctive_icon import main as generate_distinctive_icons
#         generate_distinctive_icons()
        
#         print("  Distinctive icons generated successfully!")
#         return True
        
#     except Exception as e:
#         print(f"  ERROR: Failed to generate icons: {e}")
#         print("  You can create icons manually or continue without them.")
#         return False


def build_executable(single_file: bool = False):
    """Build the executable using PyInstaller"""
    print_header("Building Executable with PyInstaller")
    
    base_path = get_base_path()
    spec_file = base_path / 'build_exe.spec'
    
    if not spec_file.exists():
        print(f"ERROR: Spec file not found: {spec_file}")
        return False
    
    # Clean previous build
    print_step("Cleaning previous build...")
    for dir_name in ['build', 'dist']:
        dir_path = base_path / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed: {dir_path}")
    
    print_step("Running PyInstaller...")
    
    try:
        cmd = [sys.executable, '-m', 'PyInstaller', str(spec_file), '--clean']
        if not single_file:
            cmd.append('--noconfirm')
        
        result = subprocess.run(
            cmd,
            cwd=str(base_path),
            check=True
        )
        
        # Check output
        if single_file:
            exe_path = base_path / 'dist' / f'{APP_NAME}.exe'
        else:
            exe_path = base_path / 'dist' / APP_NAME / f'{APP_NAME}.exe'
        
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n  Executable created: {exe_path}")
            print(f"  Size: {size_mb:.2f} MB")
            return True
        else:
            print(f"\n  ERROR: Executable not found at expected location: {exe_path}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\n  ERROR: PyInstaller failed: {e}")
        return False


def build_installer():
    """Build the Windows installer using Inno Setup"""
    print_header("Building Windows Installer")
    
    base_path = get_base_path()
    
    # Check if executable exists
    exe_path = base_path / 'dist' / APP_NAME / f'{APP_NAME}.exe'
    if not exe_path.exists():
        print("  ERROR: Executable not found. Run --exe first.")
        return False
    
    # Check for Inno Setup
    iscc_path = check_inno_setup()
    if not iscc_path:
        print("\n  Cannot build installer without Inno Setup.")
        print("  Download from: https://jrsoftware.org/isinfo.php")
        return False
    
    # Check for installer script
    iss_file = base_path / 'installer.iss'
    if not iss_file.exists():
        print(f"  ERROR: Installer script not found: {iss_file}")
        return False
    
    print_step("Running Inno Setup Compiler...")
    
    try:
        result = subprocess.run(
            [iscc_path, str(iss_file)],
            cwd=str(base_path),
            check=True
        )
        
        # Check output
        output_dir = base_path / 'installer_output'
        installers = list(output_dir.glob('*.exe'))
        
        if installers:
            installer_path = installers[0]
            size_mb = installer_path.stat().st_size / (1024 * 1024)
            print(f"\n  Installer created: {installer_path}")
            print(f"  Size: {size_mb:.2f} MB")
            return True
        else:
            print("\n  ERROR: Installer not found in output directory")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\n  ERROR: Inno Setup failed: {e}")
        return False


def build_portable():
    """Build a portable single-file executable"""
    print_header("Building Portable Executable")
    
    base_path = get_base_path()
    
    print_step("Creating single-file executable...")
    
    # Use a modified approach - build with onefile option
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name', APP_NAME,
        '--clean',
        '--noconfirm',
    ]
    
    # Add icon if exists
    icon_path = base_path / 'app_icon.ico'
    if icon_path.exists():
        cmd.extend(['--icon', str(icon_path)])
    
    # Add version file if exists
    version_file = base_path / 'file_version_info.txt'
    if version_file.exists():
        cmd.extend(['--version-file', str(version_file)])
    
    # Add data files
    data_dirs = ['config', 'styles', 'translations', 'widgets', 'dialogs', 
                 'db', 'utils', 'tabs', 'icons', 'core', 'fonts']
    for dir_name in data_dirs:
        dir_path = base_path / dir_name
        if dir_path.exists():
            cmd.extend(['--add-data', f'{dir_name};{dir_name}'])
    
    # Add icons/images specifically
    if (base_path / 'icons' / 'images').exists():
        cmd.extend(['--add-data', 'icons/images;icons/images'])
    
    # Add hidden imports
    hidden_imports = [
        'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.QtPrintSupport',
        'PyQt5.QtSvg', 'sqlite3', 'configparser', 'json', 'csv',
        'matplotlib', 'matplotlib.pyplot', 'matplotlib.backends.backend_qt5agg',
        'openpyxl', 'docx', 'PIL', 'arabic_reshaper', 'bidi', 'bidi.algorithm',
    ]
    for imp in hidden_imports:
        cmd.extend(['--hidden-import', imp])
    
    # Main script
    cmd.append('mainwindow.py')
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(base_path),
            check=True
        )
        
        exe_path = base_path / 'dist' / f'{APP_NAME}.exe'
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n  Portable executable created: {exe_path}")
            print(f"  Size: {size_mb:.2f} MB")
            
            # Copy to a 'portable' folder
            portable_dir = base_path / 'portable'
            portable_dir.mkdir(exist_ok=True)
            portable_exe = portable_dir / f'{APP_NAME}_Portable_{VERSION}.exe'
            shutil.copy2(exe_path, portable_exe)
            print(f"  Copied to: {portable_exe}")
            
            return True
        else:
            print("\n  ERROR: Portable executable not found")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\n  ERROR: Build failed: {e}")
        return False


def clean_build():
    """Clean all build artifacts"""
    print_header("Cleaning Build Artifacts")
    
    base_path = get_base_path()
    
    dirs_to_clean = ['build', 'dist', 'portable', 'installer_output', '__pycache__']
    
    for dir_name in dirs_to_clean:
        dir_path = base_path / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed: {dir_path}")
    
    # Clean __pycache__ in subdirectories
    for pycache in base_path.rglob('__pycache__'):
        shutil.rmtree(pycache)
        print(f"  Removed: {pycache}")
    
    # Clean .pyc files
    for pyc_file in base_path.rglob('*.pyc'):
        pyc_file.unlink()
        print(f"  Removed: {pyc_file}")
    
    # Clean .pyo files
    for pyo_file in base_path.rglob('*.pyo'):
        pyo_file.unlink()
        print(f"  Removed: {pyo_file}")
    
    # Clean .spec backup files
    for spec_backup in base_path.glob('*.spec.bak'):
        spec_backup.unlink()
        print(f"  Removed: {spec_backup}")
    
    print("\n  Clean completed!")


def build_all():
    """Build everything: icons, executable, and installer"""
    print_header(f"Building {APP_NAME} v{VERSION}")
    print("This will create a complete Windows installer.\n")
    
    # Step 1: Check dependencies
    check_python_dependencies()
    
    # Step 2: Create directories
    create_directories()
    
    # Step 3: Generate icons
    # generate_icons()
    
    # Step 4: Build executable
    if not build_executable(single_file=False):
        print("\n" + "=" * 60)
        print("  BUILD FAILED: Could not create executable")
        print("=" * 60)
        return False
    
    # Step 5: Build installer
    if not build_installer():
        print("\n" + "=" * 60)
        print("  INSTALLER CREATION FAILED")
        print("  The executable was created successfully.")
        print("  Install Inno Setup to create the installer.")
        print("=" * 60)
        return False
    
    # Success
    print("\n" + "=" * 60)
    print("  BUILD COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    base_path = get_base_path()
    print(f"\n  Executable: {base_path / 'dist' / APP_NAME / f'{APP_NAME}.exe'}")
    
    installer_files = list((base_path / 'installer_output').glob('*.exe'))
    if installer_files:
        print(f"  Installer:  {installer_files[0]}")
    
    print("\n  You can now distribute the installer to users!")
    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Build Text Analysis Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py              Build everything (exe + installer)
  python build.py --exe        Build only the executable
  python build.py --installer  Build installer (requires exe)
  python build.py --portable   Build portable single-file exe
  python build.py --clean      Clean build artifacts
  python build.py --icons      Generate application icons
        """
    )
    
    parser.add_argument('--exe', action='store_true',
                        help='Build only the executable')
    parser.add_argument('--installer', action='store_true',
                        help='Build only the installer (requires exe)')
    parser.add_argument('--portable', action='store_true',
                        help='Build portable single-file executable')
    parser.add_argument('--clean', action='store_true',
                        help='Clean build artifacts')
    parser.add_argument('--icons', action='store_true',
                        help='Generate application icons')
    
    args = parser.parse_args()
    
    # Handle specific commands
    if args.clean:
        clean_build()
        return 0
    
    # if args.icons:
    #     check_python_dependencies()
    #     generate_icons()
    #     return 0
    
    # if args.portable:
    #     check_python_dependencies()
    #     create_directories()
    #     generate_icons()
    #     success = build_portable()
    #     return 0 if success else 1
    
    if args.exe:
        check_python_dependencies()
        create_directories()
        success = build_executable(single_file=False)
        return 0 if success else 1
    
    if args.installer:
        success = build_installer()
        return 0 if success else 1
    
    # Default: build everything
    success = build_all()
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
