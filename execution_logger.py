"""
Execution Logging Module for LAFO
Tracks all file operations and maintains execution logs.
"""
import logging
import os
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import (
    LOGS_DIR,
    LOG_FORMAT,
    LOG_STATUS_SUCCESS,
    LOG_STATUS_ERROR,
    LOG_STATUS_SKIPPED,
    LOG_STATUS_MANUAL_REVIEW,
    VERBOSE_LOGGING
)

logger = logging.getLogger(__name__)

class DynamicDateFileHandler(logging.FileHandler):
    """
    A file handler that dynamically determines the filename based on the current date
    and rotates to a new file when the date changes.
    """
    def __init__(self, logs_dir: Path, suffix: str = "debug", encoding: Optional[str] = "utf-8"):
        self.logs_dir = Path(logs_dir)
        self.suffix = suffix
        self.encoding = encoding
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Ensure directory exists
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine the initial file path
        filename = f"{self.current_date}_{self.suffix}.log"
        filepath = self.logs_dir / filename
        
        # Initialize base FileHandler
        super().__init__(filepath, mode='a', encoding=self.encoding)
        
    def emit(self, record):
        """Emit a record, rotating to a new file if the date has changed."""
        try:
            self.acquire()
            today = datetime.now().strftime("%Y-%m-%d")
            if today != self.current_date:
                self.current_date = today
                self.close()
                filename = f"{self.current_date}_{self.suffix}.log"
                self.baseFilename = os.path.abspath(self.logs_dir / filename)
                self.stream = self._open()
            logging.FileHandler.emit(self, record)
        except Exception:
            self.handleError(record)
        finally:
            self.release()

class ExecutionLogger:
    """Manages execution logging for file operations."""
    
    def __init__(self):
        """Initialize the execution logger."""
        self.logs_dir = LOGS_DIR
        self.lock = threading.Lock()
        self.setup_logging()
    
    def setup_logging(self):
        """Configure Python logging by adding handler explicitly to root logger."""
        try:
            root_logger = logging.getLogger()
            
            # Check if we already have a DynamicDateFileHandler to avoid duplicates
            has_dynamic_handler = False
            for handler in root_logger.handlers:
                if isinstance(handler, DynamicDateFileHandler) and handler.suffix == "debug":
                    has_dynamic_handler = True
                    break
            
            if not has_dynamic_handler:
                log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                file_handler = DynamicDateFileHandler(self.logs_dir, "debug", encoding="utf-8")
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
        date_str = datetime.now().strftime("%Y-%m-%d")
        
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
        
        status_to_suffix = {
            LOG_STATUS_SUCCESS: "info",
            LOG_STATUS_ERROR: "error",
            LOG_STATUS_SKIPPED: "skipped",
            LOG_STATUS_MANUAL_REVIEW: "manual_review"
        }
        suffix = status_to_suffix.get(status, "info")
        log_file = self.logs_dir / f"{date_str}_{suffix}.log"
        
        # Write to log file
        try:
            with self.lock:
                self.logs_dir.mkdir(parents=True, exist_ok=True)
                with open(log_file, "a", encoding="utf-8") as f:
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
    
    def get_log_contents(self, status: Optional[str] = None, limit: Optional[int] = None) -> str:
        """
        Get the contents of today's execution log for a specific status or info log by default.
        
        Args:
            status: Optional status to get logs for (SUCCESS, ERROR, SKIPPED, MANUAL_REVIEW)
            limit: Number of latest lines to return (None for all)
            
        Returns:
            Log file contents
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        status_to_suffix = {
            LOG_STATUS_SUCCESS: "info",
            LOG_STATUS_ERROR: "error",
            LOG_STATUS_SKIPPED: "skipped",
            LOG_STATUS_MANUAL_REVIEW: "manual_review"
        }
        suffix = status_to_suffix.get(status, "info") if status else "info"
        log_file = self.logs_dir / f"{date_str}_{suffix}.log"
        
        if not log_file.exists():
            return f"No execution log found for today's {suffix} logs"
        
        try:
            with self.lock:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            
            if limit:
                lines = lines[-limit:]
            
            return "".join(lines)
        except Exception as e:
            return f"Error reading log: {str(e)}"
    
    def clear_log(self):
        """Clear today's execution logs."""
        try:
            with self.lock:
                date_str = datetime.now().strftime("%Y-%m-%d")
                for suffix in ["info", "error", "skipped", "manual_review"]:
                    log_file = self.logs_dir / f"{date_str}_{suffix}.log"
                    if log_file.exists():
                        log_file.unlink()
                logger.info("Today's execution logs cleared")
        except Exception as e:
            logger.error(f"Error clearing log: {str(e)}")
