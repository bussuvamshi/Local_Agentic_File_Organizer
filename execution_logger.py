"""
Execution Logging Module for LAFO
Tracks all file operations and maintains execution logs.
"""
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import (
    EXECUTION_LOG,
    LOG_FORMAT,
    LOG_STATUS_SUCCESS,
    LOG_STATUS_ERROR,
    LOG_STATUS_SKIPPED,
    LOG_STATUS_MANUAL_REVIEW,
    VERBOSE_LOGGING
)

logger = logging.getLogger(__name__)

class ExecutionLogger:
    """Manages execution logging for file operations."""
    
    def __init__(self):
        """Initialize the execution logger."""
        self.log_file = Path(EXECUTION_LOG)
        self.lock = threading.Lock()
        self.setup_logging()
    
    def setup_logging(self):
        """Configure Python logging by adding handler explicitly to root logger."""
        try:
            root_logger = logging.getLogger()
            
            # Check if we already have a FileHandler for lafo.log to avoid duplicates
            has_lafo_handler = False
            for handler in root_logger.handlers:
                if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename).name == "lafo.log":
                    has_lafo_handler = True
                    break
            
            if not has_lafo_handler:
                log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                file_handler = logging.FileHandler("lafo.log", encoding="utf-8")
                file_handler.setFormatter(logging.Formatter(log_format))
                file_handler.setLevel(logging.INFO if VERBOSE_LOGGING else logging.WARNING)
                root_logger.addHandler(file_handler)
        except Exception as e:
            import sys
            print(f"Error setting up execution logger handlers: {str(e)}", file=sys.stderr)
    
    def log_operation(
        self,
        status: str,
        filename: str,
        source_dir: str,
        target_dir: str,
        message: str = "",
        confidence_score: Optional[float] = None
    ):
        """
        Log a file operation to the execution log.
        
        Args:
            status: Operation status (SUCCESS, ERROR, SKIPPED, MANUAL_REVIEW)
            filename: Name of the file
            source_dir: Source directory path
            target_dir: Target directory path or destination folder name
            message: Additional message (e.g., error details)
            confidence_score: Confidence score for the operation (0-100)
        """
        timestamp = datetime.now().isoformat()
        
        # Build log line
        log_line = LOG_FORMAT.format(
            timestamp=timestamp,
            status=status,
            filename=filename,
            source_dir=source_dir,
            target_dir=target_dir,
            message=message
        )
        
        # Add confidence score if provided
        if confidence_score is not None:
            log_line += f" | Confidence: {confidence_score:.1f}%"
        
        # Write to log file
        try:
            with self.lock:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(log_line + "\n")
        except Exception as e:
            logger.error(f"Failed to write to execution log: {str(e)}")
        
        # Also log to Python logger
        log_level = logging.INFO if status == LOG_STATUS_SUCCESS else logging.WARNING
        if status == LOG_STATUS_ERROR:
            log_level = logging.ERROR
        
        logger.log(log_level, log_line)
    
    def log_success(
        self,
        filename: str,
        source_dir: str,
        target_dir: str,
        confidence_score: float = 100.0
    ):
        """
        Log a successful file operation.
        
        Args:
            filename: Name of the file
            source_dir: Source directory
            target_dir: Target directory
            confidence_score: Confidence score (default 100% for success)
        """
        self.log_operation(
            status=LOG_STATUS_SUCCESS,
            filename=filename,
            source_dir=source_dir,
            target_dir=target_dir,
            confidence_score=confidence_score
        )
    
    def log_error(
        self,
        filename: str,
        source_dir: str,
        error_message: str
    ):
        """
        Log a file operation error.
        
        Args:
            filename: Name of the file
            source_dir: Source directory
            error_message: Error details
        """
        self.log_operation(
            status=LOG_STATUS_ERROR,
            filename=filename,
            source_dir=source_dir,
            target_dir="N/A",
            message=error_message
        )
    
    def log_skipped(
        self,
        filename: str,
        source_dir: str,
        reason: str
    ):
        """
        Log a skipped file operation.
        
        Args:
            filename: Name of the file
            source_dir: Source directory
            reason: Reason for skipping
        """
        self.log_operation(
            status=LOG_STATUS_SKIPPED,
            filename=filename,
            source_dir=source_dir,
            target_dir="N/A",
            message=reason
        )
    
    def log_manual_review(
        self,
        filename: str,
        source_dir: str,
        reason: str,
        confidence_score: float
    ):
        """
        Log a file that requires manual review (low confidence).
        
        Args:
            filename: Name of the file
            source_dir: Source directory
            reason: Reason for manual review
            confidence_score: Confidence score
        """
        self.log_operation(
            status=LOG_STATUS_MANUAL_REVIEW,
            filename=filename,
            source_dir=source_dir,
            target_dir="Unsorted_Review",
            message=reason,
            confidence_score=confidence_score
        )
    
    def get_log_contents(self, limit: Optional[int] = None) -> str:
        """
        Get the contents of the execution log.
        
        Args:
            limit: Number of latest lines to return (None for all)
            
        Returns:
            Log file contents
        """
        if not self.log_file.exists():
            return "No execution log found"
        
        try:
            with self.lock:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            
            if limit:
                lines = lines[-limit:]
            
            return "".join(lines)
        except Exception as e:
            return f"Error reading log: {str(e)}"
    
    def clear_log(self):
        """Clear the execution log."""
        try:
            with self.lock:
                if self.log_file.exists():
                    self.log_file.unlink()
                    logger.info("Execution log cleared")
        except Exception as e:
            logger.error(f"Error clearing log: {str(e)}")
