"""
Attachment Manager - Handles file attachments with organized folder structure

Creates a folder structure:
    Source/
        [Source Name]/
            attachment1.pdf
            attachment2.jpg
            ...
"""
import os
import shutil
import re
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class AttachmentManager:
    """
    Manages file attachments with organized folder structure.
    
    Folder Structure:
        [base_path]/
            Source/
                [source_name]/
                    file1.pdf
                    file2.jpg
    """
    
    # Base folder name for all attachments
    BASE_FOLDER = "Source"
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize AttachmentManager.
        
        Args:
            base_path: Base path for attachments. If None, uses AppData when installed.
        """
        if base_path is None:
            # Use path_utils for correct path when installed (AppData for attachments)
            from utils.path_utils import get_app_data_dir, is_frozen
            if is_frozen():
                base_path = str(get_app_data_dir())
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.base_path = base_path
        self.source_folder = os.path.join(base_path, self.BASE_FOLDER)
        
        # Ensure base folder exists
        self._ensure_folder(self.source_folder)
    
    @staticmethod
    def sanitize_folder_name(name: str) -> str:
        """
        Sanitize a string to be used as a folder name.
        
        Args:
            name: The name to sanitize
            
        Returns:
            Sanitized folder name
        """
        if not name:
            return "Unnamed"
        
        # Remove invalid characters for Windows/Linux/Mac
        # Keep letters, numbers, spaces, hyphens, underscores, and common chars
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        
        # Trim whitespace and dots from ends
        sanitized = sanitized.strip('. ')
        
        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        # If empty after sanitization, use default
        if not sanitized:
            sanitized = "Unnamed"
        
        return sanitized
    
    def _ensure_folder(self, folder_path: str) -> bool:
        """
        Ensure a folder exists, create if not.
        
        Args:
            folder_path: Path to the folder
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(folder_path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create folder {folder_path}: {e}")
            return False
    
    def get_source_folder(self, source_name: str) -> str:
        """
        Get the folder path for a specific source.
        
        Args:
            source_name: Name of the source
            
        Returns:
            Full path to the source folder
        """
        sanitized_name = self.sanitize_folder_name(source_name)
        return os.path.join(self.source_folder, sanitized_name)
    
    def _is_managed_path(self, file_path: str) -> bool:
        """Return whether a path resolves inside the managed attachment root."""
        try:
            Path(file_path).resolve().relative_to(Path(self.source_folder).resolve())
            return True
        except (OSError, ValueError):
            return False

    def is_managed_path(self, file_path: str) -> bool:
        """Public path-classification helper for attachment UI workflows."""
        return self._is_managed_path(file_path)

    def create_source_folder(self, source_name: str) -> Tuple[bool, str]:
        """
        Create a folder for a source.
        
        Args:
            source_name: Name of the source
            
        Returns:
            Tuple of (success, folder_path)
        """
        folder_path = self.get_source_folder(source_name)
        success = self._ensure_folder(folder_path)
        return success, folder_path
    
    def add_attachment(self, source_name: str, file_path: str, 
                       copy_file: bool = True) -> Tuple[bool, str]:
        """
        Add an attachment to a source folder.
        
        Args:
            source_name: Name of the source
            file_path: Path to the file to attach
            copy_file: If True, copy the file. If False, just record the path.
            
        Returns:
            Tuple of (success, new_path or error_message)
        """
        if not os.path.isfile(file_path):
            return False, f"File not found or not a regular file: {file_path}"
        
        # Create source folder if needed
        success, folder_path = self.create_source_folder(source_name)
        if not success:
            return False, f"Failed to create folder for: {source_name}"
        
        if copy_file:
            try:
                # Get filename and handle duplicates
                filename = os.path.basename(file_path)
                dest_path = os.path.join(folder_path, filename)
                
                # If file with the same name exists, choose a collision-safe
                # timestamped name without ever overwriting an attachment.
                if os.path.exists(dest_path):
                    name, ext = os.path.splitext(filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    counter = 1
                    while True:
                        candidate = f"{name}_{timestamp}_{counter}{ext}"
                        dest_path = os.path.join(folder_path, candidate)
                        if not os.path.exists(dest_path):
                            filename = candidate
                            break
                        counter += 1
                
                # Copy the file
                shutil.copy2(file_path, dest_path)
                logger.info(f"Copied attachment to: {dest_path}")
                return True, dest_path
            except Exception as e:
                logger.error(f"Failed to copy attachment: {e}")
                return False, str(e)
        else:
            # Just return the original path
            return True, file_path
    
    def add_multiple_attachments(self, source_name: str, file_paths: List[str],
                                 copy_files: bool = True) -> List[Tuple[bool, str]]:
        """
        Add multiple attachments to a source folder.
        
        Args:
            source_name: Name of the source
            file_paths: List of file paths to attach
            copy_files: If True, copy the files
            
        Returns:
            List of (success, new_path or error) tuples
        """
        results = []
        for file_path in file_paths:
            result = self.add_attachment(source_name, file_path, copy_files)
            results.append(result)
        return results
    
    def remove_attachment(self, file_path: str) -> bool:
        """
        Remove an attachment file.
        
        Args:
            file_path: Path to the file to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._is_managed_path(file_path):
                logger.warning(f"Refusing to remove unmanaged attachment path: {file_path}")
                return False
            if os.path.isfile(file_path):
                os.remove(file_path)
                logger.info(f"Removed attachment: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove attachment: {e}")
            return False
    
    def get_attachments(self, source_name: str) -> List[str]:
        """
        Get all attachments for a source.
        
        Args:
            source_name: Name of the source
            
        Returns:
            List of file paths
        """
        folder_path = self.get_source_folder(source_name)
        
        if not os.path.exists(folder_path):
            return []
        
        try:
            files = []
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if self._is_managed_path(file_path) and os.path.isfile(file_path):
                    files.append(file_path)
            return sorted(files)
        except Exception as e:
            logger.error(f"Failed to list attachments: {e}")
            return []
    
    def get_attachment_info(self, file_path: str) -> Dict:
        """
        Get information about an attachment.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        info = {
            'path': file_path,
            'name': os.path.basename(file_path),
            'exists': False,
            'size': 0,
            'size_str': '',
            'modified': None,
            'extension': ''
        }
        
        if os.path.exists(file_path):
            info['exists'] = True
            stat = os.stat(file_path)
            info['size'] = stat.st_size
            info['size_str'] = self.format_size(stat.st_size)
            info['modified'] = datetime.fromtimestamp(stat.st_mtime)
            info['extension'] = os.path.splitext(file_path)[1].lower()
        
        return info
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def rename_source_folder(self, old_name: str, new_name: str) -> bool:
        """
        Rename a source folder.
        
        Args:
            old_name: Current source name
            new_name: New source name
            
        Returns:
            True if successful, False otherwise
        """
        old_path = self.get_source_folder(old_name)
        new_path = self.get_source_folder(new_name)
        
        if not os.path.exists(old_path):
            return False
        
        if os.path.exists(new_path):
            # Merge folders
            try:
                for filename in os.listdir(old_path):
                    src = os.path.join(old_path, filename)
                    dst = os.path.join(new_path, filename)
                    if os.path.exists(dst):
                        name, ext = os.path.splitext(filename)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        dst = os.path.join(new_path, f"{name}_{timestamp}{ext}")
                    shutil.move(src, dst)
                os.rmdir(old_path)
                return True
            except Exception as e:
                logger.error(f"Failed to merge folders: {e}")
                return False
        else:
            try:
                os.rename(old_path, new_path)
                return True
            except Exception as e:
                logger.error(f"Failed to rename folder: {e}")
                return False
    
    def delete_source_folder(self, source_name: str) -> bool:
        """
        Delete a source folder and all its attachments.
        
        Args:
            source_name: Name of the source
            
        Returns:
            True if successful, False otherwise
        """
        folder_path = self.get_source_folder(source_name)
        
        if not os.path.exists(folder_path):
            return True
        
        try:
            shutil.rmtree(folder_path)
            logger.info(f"Deleted source folder: {folder_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete source folder: {e}")
            return False
    
    def get_all_sources(self) -> List[str]:
        """
        Get list of all source folders.
        
        Returns:
            List of source names
        """
        if not os.path.exists(self.source_folder):
            return []
        
        try:
            sources = []
            for name in os.listdir(self.source_folder):
                path = os.path.join(self.source_folder, name)
                if os.path.isdir(path):
                    sources.append(name)
            return sorted(sources)
        except Exception as e:
            logger.error(f"Failed to list sources: {e}")
            return []
    
    def get_total_attachment_count(self) -> int:
        """
        Get total number of attachments across all sources.
        
        Returns:
            Total attachment count
        """
        count = 0
        for source in self.get_all_sources():
            count += len(self.get_attachments(source))
        return count
    
    def get_total_size(self) -> Tuple[int, str]:
        """
        Get total size of all attachments.
        
        Returns:
            Tuple of (size_bytes, formatted_size)
        """
        total = 0
        for source in self.get_all_sources():
            for file_path in self.get_attachments(source):
                if os.path.exists(file_path):
                    total += os.path.getsize(file_path)
        return total, self.format_size(total)
    
    def open_attachment(self, file_path: str) -> bool:
        """
        Open an attachment with the default system application.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(file_path):
            return False
        
        try:
            import subprocess
            import sys
            
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                result = subprocess.run(['open', file_path], check=False)
                if result.returncode != 0:
                    return False
            else:
                result = subprocess.run(['xdg-open', file_path], check=False)
                if result.returncode != 0:
                    return False
            return True
        except Exception as e:
            logger.error(f"Failed to open attachment: {e}")
            return False
    
    def open_source_folder(self, source_name: str) -> bool:
        """
        Open the source folder in file explorer.
        
        Args:
            source_name: Name of the source
            
        Returns:
            True if successful, False otherwise
        """
        folder_path = self.get_source_folder(source_name)
        
        if not os.path.exists(folder_path):
            self._ensure_folder(folder_path)
        
        return self.open_attachment(folder_path)


# Global instance
_attachment_manager = None


def get_attachment_manager() -> AttachmentManager:
    """
    Get the global AttachmentManager instance.
    
    Returns:
        AttachmentManager instance
    """
    global _attachment_manager
    if _attachment_manager is None:
        _attachment_manager = AttachmentManager()
    return _attachment_manager
