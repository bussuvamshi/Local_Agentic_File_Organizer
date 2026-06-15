"""
File System Monitor for LAFO
Watches the Downloads folder for new files using watchdog.
"""
import logging
import time
from pathlib import Path
from typing import Callable, List

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from config import (
    DOWNLOADS_DIR,
    TEMP_PATTERNS,
    SUPPORTED_EXTENSIONS,
    FILE_STABLE_TIME,
    WATCH_POLL_INTERVAL
)

logger = logging.getLogger(__name__)

class DownloadsEventHandler(FileSystemEventHandler):
    """
    Handles file system events from the Downloads directory.
    Detects new file downloads and triggers processing.
    """
    
    def __init__(self, on_new_file: Callable):
        """
        Initialize the event handler.
        
        Args:
            on_new_file: Callback function to call when a new file is detected
        """
        super().__init__()
        self.on_new_file = on_new_file
        self.processed_files = set()
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Ignore if already processed or in progress
        if str(file_path) in self.processed_files:
            return
            
        logger.debug(f"File created: {file_path.name}")
        
        # Check if it's a temporary file
        if self._is_temp_file(file_path):
            logger.debug(f"Ignoring temporary file: {file_path.name}")
            return
        
        # Check if it's a supported file type
        if not self._is_supported_file(file_path):
            logger.debug(f"Ignoring unsupported file type: {file_path.name}")
            return
        
        # Wait for file to be stable (stop being written to)
        logger.info(f"🔍 New file detected: {file_path.name}")
        if self._wait_for_file_stable(file_path):
            # Double check it wasn't processed by another event while waiting
            if str(file_path) in self.processed_files:
                return
            self.processed_files.add(str(file_path))
            
            logger.info(f"✅ File ready for processing: {file_path.name}")
            self.on_new_file(str(file_path))
        else:
            logger.warning(f"File stability check failed: {file_path.name}")
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Ignore if we've already processed this file
        if str(file_path) in self.processed_files:
            return
        
        # For very large files, trigger on modification if they're stable
        try:
            if file_path.exists() and file_path.stat().st_size > 50 * 1024 * 1024:  # 50 MB
                if self._is_supported_file(file_path) and not self._is_temp_file(file_path):
                    if self._wait_for_file_stable(file_path):
                        # Double check it wasn't processed by another event while waiting
                        if str(file_path) in self.processed_files:
                            return
                        self.processed_files.add(str(file_path))
                        
                        logger.info(f"✅ Large file stable: {file_path.name}")
                        self.on_new_file(str(file_path))
        except FileNotFoundError:
            pass

    def on_moved(self, event):
        """Handle file rename/move events (crucial for browser downloads)."""
        if event.is_directory:
            return
        
        file_path = Path(event.dest_path)
        
        # Ignore if already processed or in progress
        if str(file_path) in self.processed_files:
            return
            
        logger.debug(f"File moved/renamed: {file_path.name}")
        
        # Check if it's a temporary file
        if self._is_temp_file(file_path):
            logger.debug(f"Ignoring temporary file: {file_path.name}")
            return
        
        # Check if it's a supported file type
        if not self._is_supported_file(file_path):
            logger.debug(f"Ignoring unsupported file type: {file_path.name}")
            return
        
        # Wait for file to be stable and process it
        logger.info(f"🔍 New file detected via rename: {file_path.name}")
        if self._wait_for_file_stable(file_path):
            # Double check it wasn't processed by another event while waiting
            if str(file_path) in self.processed_files:
                return
            self.processed_files.add(str(file_path))
            
            logger.info(f"✅ File ready for processing: {file_path.name}")
            self.on_new_file(str(file_path))
        else:
            logger.warning(f"File stability check failed: {file_path.name}")
    
    @staticmethod
    def _is_temp_file(file_path: Path) -> bool:
        """
        Check if a file is a temporary/in-progress download.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file is temporary
        """
        filename = file_path.name.lower()
        return any(filename.endswith(pattern) or filename.startswith(pattern) for pattern in TEMP_PATTERNS)
    
    @staticmethod
    def _is_supported_file(file_path: Path) -> bool:
        """
        Check if a file type is supported.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file type is supported
        """
        return any(file_path.suffix.lower() == ext for ext in SUPPORTED_EXTENSIONS)
    
    @staticmethod
    def _wait_for_file_stable(file_path: Path, max_wait: int = 30) -> bool:
        """
        Wait for a file to become stable (stop being written to).
        
        Args:
            file_path: Path to the file
            max_wait: Maximum seconds to wait
            
        Returns:
            True if file became stable, False if timeout
        """
        import time
        
        # Check if file exists before proceeding
        if not file_path.exists():
            logger.warning(f"File not found at start of stability check: {file_path.name}")
            return False
        
        start_time = time.time()
        try:
            prev_size = file_path.stat().st_size
        except FileNotFoundError:
            logger.warning(f"File disappeared before stability check: {file_path.name}")
            return False
        
        stable_checks = 0
        required_stable_checks = 2  # File size must not change for 2 consecutive checks
        
        while time.time() - start_time < max_wait:
            time.sleep(FILE_STABLE_TIME)
            
            if not file_path.exists():
                logger.warning(f"File disappeared during stability check: {file_path.name}")
                return False
            
            try:
                current_size = file_path.stat().st_size
            except FileNotFoundError:
                logger.warning(f"File disappeared during size check: {file_path.name}")
                return False
            
            if current_size == prev_size:
                stable_checks += 1
                if stable_checks >= required_stable_checks:
                    logger.debug(f"File is stable: {file_path.name}")
                    return True
            else:
                stable_checks = 0
            
            prev_size = current_size
        
        logger.warning(f"File stability timeout: {file_path.name}")
        return False


class FileMonitor:
    """Monitors the Downloads folder for new files."""
    
    def __init__(self, on_new_file: Callable):
        """
        Initialize the file monitor.
        
        Args:
            on_new_file: Callback function when new file is detected
        """
        self.downloads_dir = str(DOWNLOADS_DIR)
        self.on_new_file = on_new_file
        self.observer = None
        self.event_handler = None
    
    def start(self):
        """Start monitoring the Downloads folder."""
        if not Path(self.downloads_dir).exists():
            logger.error(f"Downloads directory not found: {self.downloads_dir}")
            return False
        
        try:
            # Create event handler
            self.event_handler = DownloadsEventHandler(self.on_new_file)
            
            # Create observer
            self.observer = Observer()
            self.observer.schedule(
                self.event_handler,
                self.downloads_dir,
                recursive=False  # Don't monitor subfolders
            )
            
            # Start observer
            self.observer.start()
            logger.info(f"✅ File monitor started: {self.downloads_dir}")
            return True
        
        except Exception as e:
            logger.error(f"Error starting file monitor: {str(e)}")
            return False
    
    def stop(self):
        """Stop monitoring the Downloads folder."""
        if self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=5)
                logger.info("✅ File monitor stopped")
            except Exception as e:
                logger.error(f"Error stopping file monitor: {str(e)}")
    
    def wait(self):
        """
        Wait for the observer to finish (blocking).
        This should be called after start() to keep the monitor running.
        """
        if self.observer:
            try:
                self.observer.join()
            except KeyboardInterrupt:
                logger.info("Monitor interrupted by user")
                self.stop()
