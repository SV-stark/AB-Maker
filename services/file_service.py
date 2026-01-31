"""
File Service
Handles file operations, validation, and management
"""
from typing import List, Optional, Tuple, Set
from pathlib import Path
import os
import logging
import mimetypes

from models.domain import RecentFile, ConversionStatus
from config.constants import get_config

logger = logging.getLogger(__name__)


class FileService:
    """Service for file operations and management."""
    
    def __init__(self, config_manager):
        """
        Initialize file service.
        
        Args:
            config_manager: ConfigManager instance
        """
        self._config_manager = config_manager
        self._app_config = get_config()
        self._recent_files: List[RecentFile] = []
        self._load_recent_files()
    
    def _load_recent_files(self):
        """Load recent files from config."""
        paths = self._config_manager.get_recent_files()
        self._recent_files = []
        
        for path_str in paths:
            path = Path(path_str)
            if path.exists():
                status_str = self._config_manager.get_file_status(str(path))
                status = ConversionStatus(status_str) if status_str else ConversionStatus.PENDING
                
                recent_file = RecentFile(
                    path=path,
                    title=path.stem,
                    status=status
                )
                self._recent_files.append(recent_file)
    
    def get_supported_audio_formats(self) -> List[str]:
        """Get list of supported audio output formats."""
        return self._app_config.audio.supported_formats.copy()
    
    def get_supported_cover_formats(self) -> List[str]:
        """Get list of supported cover image formats."""
        return self._app_config.audio.supported_cover_formats.copy()
    
    def validate_epub_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate an EPUB file.
        
        Args:
            file_path: Path to EPUB file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        
        if not file_path.is_file():
            return False, f"Not a file: {file_path}"
        
        if file_path.suffix.lower() != '.epub':
            return False, f"Not an EPUB file: {file_path.suffix}"
        
        # Check if file is readable
        try:
            with open(file_path, 'rb') as f:
                f.read(1)
        except Exception as e:
            return False, f"Cannot read file: {e}"
        
        return True, None
    
    def validate_cover_image(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate a cover image file.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        
        if not file_path.is_file():
            return False, f"Not a file: {file_path}"
        
        ext = file_path.suffix.lower()
        if ext not in self._app_config.audio.supported_cover_formats:
            return False, f"Unsupported image format: {ext}"
        
        return True, None
    
    def validate_output_directory(self, dir_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate an output directory.
        
        Args:
            dir_path: Path to directory
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Cannot create directory: {e}"
        
        if not dir_path.is_dir():
            return False, f"Not a directory: {dir_path}"
        
        # Check write permissions
        try:
            test_file = dir_path / ".write_test"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            return False, f"Cannot write to directory: {e}"
        
        return True, None
    
    def add_recent_file(self, file_path: Path, title: str = "") -> None:
        """
        Add a file to recent files list.
        
        Args:
            file_path: Path to file
            title: Book title
        """
        # Remove if already exists
        self._recent_files = [f for f in self._recent_files if f.path != file_path]
        
        # Add to front
        recent_file = RecentFile(
            path=file_path,
            title=title or file_path.stem
        )
        self._recent_files.insert(0, recent_file)
        
        # Trim to max
        max_files = self._app_config.ui.max_recent_files
        self._recent_files = self._recent_files[:max_files]
        
        # Save to config
        self._config_manager.add_recent_file(str(file_path))
        
        logger.debug(f"Added recent file: {file_path}")
    
    def get_recent_files(self) -> List[RecentFile]:
        """Get list of recent files."""
        return self._recent_files.copy()
    
    def update_file_status(self, file_path: Path, status: ConversionStatus) -> None:
        """
        Update conversion status for a file.
        
        Args:
            file_path: Path to file
            status: New status
        """
        self._config_manager.set_file_status(str(file_path), status.value)
        
        # Update in memory
        for recent_file in self._recent_files:
            if recent_file.path == file_path:
                recent_file.status = status
                break
        
        logger.debug(f"Updated file status: {file_path} -> {status.value}")
    
    def clear_file_status(self, file_path: Path) -> None:
        """Clear conversion status for a file."""
        self._config_manager.clear_file_status(str(file_path))
        
        for recent_file in self._recent_files:
            if recent_file.path == file_path:
                recent_file.status = ConversionStatus.PENDING
                break
    
    def remove_from_recent(self, file_path: Path) -> None:
        """Remove a file from recent files list."""
        self._recent_files = [f for f in self._recent_files if f.path != file_path]
        
        # Update config
        paths = [str(f.path) for f in self._recent_files]
        self._config_manager.set("recent_files", paths)
    
    def get_file_dialog_filters(self, dialog_type: str) -> List[Tuple[str, str]]:
        """
        Get file dialog filters.
        
        Args:
            dialog_type: Type of dialog ('epub', 'image', 'all')
            
        Returns:
            List of (description, pattern) tuples
        """
        if dialog_type == 'epub':
            return [("EPUB files", "*.epub"), ("All files", "*.*")]
        elif dialog_type == 'image':
            return [
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("All files", "*.*")
            ]
        else:
            return [("All files", "*.*")]
    
    def suggest_output_path(self, input_path: Path, output_format: str, 
                          output_dir: Optional[Path] = None) -> Path:
        """
        Suggest an output file path.
        
        Args:
            input_path: Input EPUB path
            output_format: Output format (m4b, mp3)
            output_dir: Optional output directory
            
        Returns:
            Suggested output path
        """
        if output_dir:
            base_dir = output_dir
        else:
            base_dir = input_path.parent
        
        base_name = input_path.stem
        output_name = f"{base_name}_audiobook.{output_format}"
        
        return base_dir / output_name
    
    def check_disk_space(self, path: Path, required_mb: float) -> Tuple[bool, float]:
        """
        Check if there's enough disk space.
        
        Args:
            path: Path to check
            required_mb: Required space in MB
            
        Returns:
            Tuple of (has_space, available_mb)
        """
        try:
            stat = os.statvfs(path)
            available_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
            return available_mb >= required_mb, available_mb
        except Exception as e:
            logger.warning(f"Cannot check disk space: {e}")
            return True, 0  # Assume OK if can't check
