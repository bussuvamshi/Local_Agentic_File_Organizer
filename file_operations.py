"""
File Operations Module for LAFO
Handles file moving, renaming, and duplicate detection.
"""
import logging
import shutil
import hashlib
from pathlib import Path
from typing import Optional, Tuple

from config import TARGET_ROOT, UNSORTED_FOLDER

logger = logging.getLogger(__name__)

class FileOperations:
    """Manages file operations including moving, renaming, and duplicate detection."""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize a filename to remove invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Invalid characters for Windows filenames
        invalid_chars = '<>:"|?*\\/'
        sanitized = filename
        
        for char in invalid_chars:
            sanitized = sanitized.replace(char, "_")
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip('. ')
        
        # Limit length (Windows has 255 char limit)
        if len(sanitized) > 200:
            name, ext = sanitized.rsplit(".", 1) if "." in sanitized else (sanitized, "")
            name = name[:195]
            sanitized = f"{name}.{ext}" if ext else name
        
        return sanitized
    
    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """
        Calculate SHA256 hash of a file for duplicate detection.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA256 hash string
        """
        try:
            hash_obj = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {str(e)}")
            return ""
    
    @staticmethod
    def check_duplicate_content(
        source_file: str,
        target_folder: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a file with identical content already exists in target folder.
        
        Args:
            source_file: Path to the source file
            target_folder: Target folder path
            
        Returns:
            Tuple of (is_duplicate, existing_file_path)
        """
        try:
            source_hash = FileOperations.get_file_hash(source_file)
            if not source_hash:
                return False, None
            
            source_size = Path(source_file).stat().st_size
            target_path = Path(target_folder)
            if not target_path.exists():
                return False, None
            
            # Check all files in target folder
            for existing_file in target_path.rglob("*"):
                if existing_file.is_file():
                    # Optimization: Only hash if file sizes are identical
                    try:
                        if existing_file.stat().st_size == source_size:
                            existing_hash = FileOperations.get_file_hash(str(existing_file))
                            if existing_hash == source_hash:
                                logger.warning(f"Duplicate content found: {existing_file.name}")
                                return True, str(existing_file)
                    except FileNotFoundError:
                        continue
            
            return False, None
        
        except Exception as e:
            logger.error(f"Error checking duplicates: {str(e)}")
            return False, None
    
    @staticmethod
    def check_duplicate_filename(
        filename: str,
        target_folder: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a file with the same name already exists in target folder.
        
        Args:
            filename: Filename to check
            target_folder: Target folder path
            
        Returns:
            Tuple of (exists, full_path)
        """
        target_file = Path(target_folder) / filename
        if target_file.exists():
            return True, str(target_file)
        return False, None
    
    @staticmethod
    def move_file(
        source_path: str,
        target_folder: str,
        new_filename: Optional[str] = None,
        overwrite: bool = False
    ) -> Tuple[bool, Optional[str], str]:
        """
        Move a file to the target folder with optional renaming.
        
        Args:
            source_path: Source file path
            target_folder: Target folder path (must exist)
            new_filename: New filename (optional)
            overwrite: Whether to overwrite existing files
            
        Returns:
            Tuple of (success, new_file_path, message)
        """
        try:
            source_path = Path(source_path)
            target_folder = Path(target_folder)
            
            # Ensure target folder exists
            target_folder.mkdir(parents=True, exist_ok=True)
            
            # Determine final filename
            filename = new_filename if new_filename else source_path.name
            filename = FileOperations.sanitize_filename(filename)
            
            target_file = target_folder / filename
            
            # Handle existing files
            if target_file.exists() and not overwrite:
                # Add counter to filename
                name_parts = filename.rsplit(".", 1)
                counter = 1
                while target_file.exists():
                    if len(name_parts) > 1:
                        new_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                    else:
                        new_name = f"{filename}_{counter}"
                    
                    target_file = target_folder / new_name
                    counter += 1
                
                logger.info(f"File exists, renamed to: {target_file.name}")
            
            # Move the file
            shutil.move(str(source_path), str(target_file))
            logger.info(f"✅ File moved: {source_path.name} → {target_file.name}")
            
            return True, str(target_file), "File moved successfully"
        
        except Exception as e:
            error_msg = f"Error moving file: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    @staticmethod
    def move_to_unsorted(
        source_path: str,
        reason: str = "Low confidence classification"
    ) -> Tuple[bool, Optional[str]]:
        """
        Move a file to the Unsorted_Review folder.
        
        Args:
            source_path: Source file path
            reason: Reason for moving to unsorted
            
        Returns:
            Tuple of (success, new_file_path)
        """
        try:
            UNSORTED_FOLDER.mkdir(parents=True, exist_ok=True)
            success, new_path, msg = FileOperations.move_file(
                source_path,
                str(UNSORTED_FOLDER)
            )
            
            if success:
                logger.info(f"File moved to Unsorted_Review: {reason}")
            
            return success, new_path
        
        except Exception as e:
            logger.error(f"Error moving to unsorted: {str(e)}")
            return False, None
    
    @staticmethod
    def is_file_stable(file_path: str, stable_time: float = 2.0) -> bool:
        """
        Check if a file has stopped being written to (is stable).
        
        Args:
            file_path: Path to the file
            stable_time: Time in seconds to wait for stability
            
        Returns:
            True if file is stable
        """
        try:
            import time
            
            file_path = Path(file_path)
            if not file_path.exists():
                return False
            
            initial_size = file_path.stat().st_size
            time.sleep(stable_time)
            
            current_size = file_path.stat().st_size
            
            # File is stable if size hasn't changed
            return initial_size == current_size
        
        except Exception as e:
            logger.error(f"Error checking file stability: {str(e)}")
            return False
    
    @staticmethod
    def get_relative_path(target_folder: str) -> str:
        """
        Get relative path from TARGET_ROOT to target folder.
        
        Args:
            target_folder: Absolute path to target folder
            
        Returns:
            Relative path or folder name
        """
        try:
            target_path = Path(target_folder)
            if target_path.is_relative_to(TARGET_ROOT):
                return str(target_path.relative_to(TARGET_ROOT))
            else:
                return target_path.name
        except:
            return Path(target_folder).name
