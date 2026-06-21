"""
Main Orchestrator for LAFO
Coordinates all components to create a complete file organization system.
"""
import io
import logging
import sys
import os
from pathlib import Path
from typing import Optional
import concurrent.futures
import threading

try:
    import msvcrt
except ImportError:
    msvcrt = None

class SingleInstance:
    """
    Prevents multiple instances of the application from running simultaneously.
    Uses Windows-specific file locking via msvcrt if available, otherwise acts as a no-op.
    """
    def __init__(self, lockfile_path: Path):
        self.lockfile_path = Path(lockfile_path)
        self.fd = None
        self.is_locked = False

    def acquire(self) -> bool:
        if msvcrt is None:
            return True
        try:
            self.lockfile_path.parent.mkdir(parents=True, exist_ok=True)
            self.fd = os.open(self.lockfile_path, os.O_WRONLY | os.O_CREAT)
            msvcrt.locking(self.fd, msvcrt.LK_NBLCK, 1)
            self.is_locked = True
            return True
        except (OSError, IOError):
            if self.fd is not None:
                try:
                    os.close(self.fd)
                except Exception:
                    pass
                self.fd = None
            return False

    def release(self):
        if self.fd is not None:
            try:
                if msvcrt is not None and self.is_locked:
                    os.lseek(self.fd, 0, os.SEEK_SET)
                    msvcrt.locking(self.fd, msvcrt.LK_UNLCK, 1)
                os.close(self.fd)
            except Exception:
                pass
            
            try:
                if self.lockfile_path.exists():
                    os.remove(self.lockfile_path)
            except Exception:
                pass
            
            self.fd = None
            self.is_locked = False


# Prevent pythonw.exe None stream crashes and redirect them to a file for diagnostics
class FileStream(io.IOBase):
    def __init__(self, filepath):
        self.filepath = filepath
    def write(self, s):
        try:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(s)
        except Exception:
            pass
        return len(s)
    def flush(self):
        pass
    def isatty(self):
        return False

try:
    logs_dir = Path(r"C:\Users\bussu\Documents\LAFO logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    startup_log_path = logs_dir / "startup_error.log"
    
    if sys.stdout is None or sys.stdout.__class__.__name__ == 'NoneType':
        sys.stdout = FileStream(startup_log_path)
    if sys.stderr is None or sys.stderr.__class__.__name__ == 'NoneType':
        sys.stderr = FileStream(startup_log_path)
except Exception:
    class DummyStream(io.IOBase):
        def write(self, s):
            return len(s)
        def flush(self):
            pass
        def isatty(self):
            return False
    if sys.stdout is None:
        sys.stdout = DummyStream()
    if sys.stderr is None:
        sys.stderr = DummyStream()

# Reconfigure standard output streams to handle unencodable characters on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(errors="replace")
    except Exception:
        pass

from vector_store import VectorStoreManager
from file_monitor import FileMonitor
from text_extractor import TextExtractor
from agent import RoutingAgent
from file_operations import FileOperations
from execution_logger import ExecutionLogger, DynamicDateFileHandler

from config import (
    DOWNLOADS_DIR,
    TARGET_ROOT,
    UNSORTED_FOLDER,
    CONFIDENCE_THRESHOLD,
    VERBOSE_LOGGING,
    MAX_WORKERS,
    LOGS_DIR,
    MAX_CANDIDATES
)

# Setup logging
logging.basicConfig(
    level=logging.INFO if VERBOSE_LOGGING else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        DynamicDateFileHandler(LOGS_DIR, "debug", encoding="utf-8"),
        logging.StreamHandler()
    ],
    force=True
)

logger = logging.getLogger(__name__)

class LAFOOrchestrator:
    """
    Main orchestrator for the Local Agentic File Organizer system.
    Coordinates all components for intelligent file organization.
    """
    
    def __init__(self):
        """Initialize the LAFO orchestrator."""
        logger.info("=" * 70)
        logger.info("🚀 LAFO - Local Agentic File Organizer Starting")
        logger.info("=" * 70)
        
        # Initialize components
        self.vector_store = None
        self.file_monitor = None
        self.routing_agent = None
        self.execution_logger = ExecutionLogger()
        
        # Track statistics
        self.stats = {
            "files_processed": 0,
            "files_moved": 0,
            "files_skipped": 0,
            "errors": 0,
            "manual_reviews": 0
        }
        
        # Thread pool and synchronization locks for parallel processing
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.stats_lock = threading.Lock()
        self.file_op_lock = threading.Lock()
    
    def initialize(self) -> bool:
        """
        Initialize all LAFO components.
        
        Returns:
            True if initialization successful
        """
        try:
            logger.info("\n📋 Initializing LAFO Components...")
            
            # 1. Initialize vector store
            logger.info("1️⃣  Initializing Vector Store...")
            self.vector_store = VectorStoreManager()
            if not self.vector_store.initialize_vectorstore(force_rebuild=True):
                logger.error("Failed to initialize vector store")
                return False
            logger.info("   ✅ Vector store ready")
            
            # 2. Initialize routing agent
            logger.info("2️⃣  Initializing Routing Agent...")
            self.routing_agent = RoutingAgent()
            if not self.routing_agent.check_ollama_connection():
                logger.error("Cannot connect to Ollama")
                return False
            logger.info("   ✅ Routing agent ready (Ollama connected)")
            
            # 3. Verify directories
            logger.info("3️⃣  Verifying Directory Structure...")
            if not self._verify_directories():
                return False
            logger.info("   ✅ Directory structure verified")
            
            # 4. Initialize file monitor
            logger.info("4️⃣  Initializing File Monitor...")
            self.file_monitor = FileMonitor(self.enqueue_file_processing)
            if not self.file_monitor.start():
                logger.error("Failed to start file monitor")
                return False
            logger.info("   ✅ File monitor started")
            
            logger.info("\n✅ LAFO Initialization Complete!")
            logger.info("=" * 70)
            logger.info(f"📁 Monitoring: {DOWNLOADS_DIR}")
            logger.info(f"📂 Target Root: {TARGET_ROOT}")
            logger.info("=" * 70 + "\n")
            
            return True
        
        except Exception as e:
            logger.error(f"Initialization error: {str(e)}")
            return False
    
    def _verify_directories(self) -> bool:
        """
        Verify that required directories exist.
        
        Returns:
            True if all directories are valid
        """
        try:
            # Check Downloads directory
            if not Path(DOWNLOADS_DIR).exists():
                logger.error(f"Downloads directory not found: {DOWNLOADS_DIR}")
                return False
            logger.info(f"   Downloads: {DOWNLOADS_DIR}")
            
            # Check target root
            if not Path(TARGET_ROOT).exists():
                logger.error(f"Target root not found: {TARGET_ROOT}")
                return False
            logger.info(f"   Target Root: {TARGET_ROOT}")
            
            # Create Unsorted_Review folder if needed
            Path(UNSORTED_FOLDER).mkdir(parents=True, exist_ok=True)
            logger.info(f"   Unsorted_Review: {UNSORTED_FOLDER}")
            
            return True
        except Exception as e:
            logger.error(f"Directory verification error: {str(e)}")
            return False
    def enqueue_file_processing(self, file_path: str):
        """
        Enqueue a file for processing in the thread pool.
        
        Args:
            file_path: Path to the file to process
        """
        logger.info(f"📥 Enqueuing file for parallel processing: {Path(file_path).name}")
        self.executor.submit(self.process_file, file_path)

    def process_file(self, file_path: str):
        """
        Process a newly detected file.
        
        Args:
            file_path: Path to the file to process
        """
        try:
            file_path = Path(file_path)
            
            # Check if file still exists (it might have been renamed or deleted)
            if not file_path.exists():
                logger.info(f"ℹ️ File no longer exists, skipping processing: {file_path.name}")
                return
                
            logger.info(f"\n{'='*70}")
            logger.info(f"📄 Processing: {file_path.name}")
            logger.info(f"{'='*70}")
            
            with self.stats_lock:
                self.stats["files_processed"] += 1
            
            # Step 1: Check if file is stable
            if not FileOperations.is_file_stable(str(file_path)):
                logger.warning("File is still being written to, skipping...")
                self.execution_logger.log_skipped(
                    file_path.name,
                    str(file_path.parent),
                    "File not stable"
                )
                with self.stats_lock:
                    self.stats["files_skipped"] += 1
                return
            
            # Step 2: Extract text content
            logger.info("📖 Extracting text content...")
            text_content, success = TextExtractor.extract_content(str(file_path))
            
            if not success or not text_content.strip():
                logger.error("Failed to extract text from file")
                self.execution_logger.log_error(
                    file_path.name,
                    str(file_path.parent),
                    "Failed to extract text content"
                )
                with self.stats_lock:
                    self.stats["errors"] += 1
                return
            
            logger.info(f"   ✅ Extracted {len(text_content)} characters")
            
            # Step 3: Search for candidate folders using vector similarity
            logger.info("🔍 Searching for candidate folders...")
            similar_folders = self.vector_store.search_similar_folders(text_content, k=MAX_CANDIDATES)
            
            if similar_folders:
                available_categories = {
                    folder_path: folder_name
                    for folder_path, _, folder_name in similar_folders
                }
                logger.info(f"   Narrowed down to top {len(available_categories)} candidate folders:")
                for fp, fn in available_categories.items():
                    logger.info(f"     - {fn} ({fp})")
            else:
                logger.warning("Similarity search returned no folders. Falling back to all categories.")
                available_categories = self.vector_store.get_all_categories()
            
            if not available_categories:
                logger.error("No categories available")
                self.execution_logger.log_error(
                    file_path.name,
                    str(file_path.parent),
                    "No available categories in target directory"
                )
                with self.stats_lock:
                    self.stats["errors"] += 1
                return
            
            # Step 4: Semantic routing
            logger.info("🧠 Analyzing document and routing...")
            classification = self.routing_agent.classify_document(
                text_content,
                available_categories,
                file_path.name
            )
            
            if not classification:
                logger.error("Failed to classify document after retries. Moving to Unsorted_Review...")
                success, new_path = FileOperations.move_to_unsorted(
                    str(file_path),
                    "Classification failed (LLM timeout or parsing error)"
                )
                if success:
                    self.execution_logger.log_manual_review(
                        file_path.name,
                        str(file_path.parent),
                        "Classification failed (LLM timeout or parsing error)",
                        0.0
                    )
                    with self.stats_lock:
                        self.stats["manual_reviews"] += 1
                else:
                    logger.error("Failed to move file to Unsorted_Review")
                    self.execution_logger.log_error(
                        file_path.name,
                        str(file_path.parent),
                        "Classification failed and failed to move to Unsorted_Review"
                    )
                    with self.stats_lock:
                        self.stats["errors"] += 1
                return
            
            # Validate classification
            if not self.routing_agent.validate_classification(classification):
                logger.error("Classification validation failed. Moving to Unsorted_Review...")
                success, new_path = FileOperations.move_to_unsorted(
                    str(file_path),
                    "Classification validation failed (Invalid schema values)"
                )
                if success:
                    self.execution_logger.log_manual_review(
                        file_path.name,
                        str(file_path.parent),
                        "Classification validation failed",
                        0.0
                    )
                    with self.stats_lock:
                        self.stats["manual_reviews"] += 1
                else:
                    logger.error("Failed to move file to Unsorted_Review")
                    self.execution_logger.log_error(
                        file_path.name,
                        str(file_path.parent),
                        "Classification validation failed and failed to move to Unsorted_Review"
                    )
                    with self.stats_lock:
                        self.stats["errors"] += 1
                return
            
            # Log classification details
            confidence = classification.get("confidence_score", 0)
            category = classification.get("category_folder", "Unknown")
            # Preserve original filename instead of renaming
            new_filename = file_path.name
            doc_date = classification.get("document_date", "Unknown")
            reasoning = classification.get("reasoning", "")
            
            logger.info(f"\n📊 Classification Result:")
            logger.info(f"   Category: {category}")
            logger.info(f"   Confidence: {confidence:.1f}%")
            logger.info(f"   Date: {doc_date}")
            logger.info(f"   Suggested Name: {new_filename}")
            logger.info(f"   Reasoning: {reasoning}\n")
            
            # Step 5: Check confidence threshold
            if confidence < CONFIDENCE_THRESHOLD:
                logger.warning(f"⚠️  Low confidence ({confidence:.1f}% < {CONFIDENCE_THRESHOLD}%)")
                logger.info("Moving to Unsorted_Review for manual review...")
                
                success, new_path = FileOperations.move_to_unsorted(
                    str(file_path),
                    f"Low confidence classification ({confidence:.1f}%)"
                )
                
                if success:
                    self.execution_logger.log_manual_review(
                        file_path.name,
                        str(file_path.parent),
                        f"Confidence below threshold: {reasoning}",
                        confidence
                    )
                    with self.stats_lock:
                        self.stats["manual_reviews"] += 1
                else:
                    logger.error("Failed to move file to Unsorted_Review")
                    self.execution_logger.log_error(
                        file_path.name,
                        str(file_path.parent),
                        "Failed to move to Unsorted_Review"
                    )
                    with self.stats_lock:
                        self.stats["errors"] += 1
                
                return
            
            # Step 6: Check for duplicates & Step 7: Move file
            # Protect these operations to avoid parallel race conditions on target folder
            with self.file_op_lock:
                # Double check if file was renamed or deleted during the long LLM classification call
                if not file_path.exists():
                    logger.info(f"ℹ️ File no longer exists (likely renamed during classification): {file_path.name}")
                    return
                
                category_folder = classification.get("category_folder", "")
                
                # Resolve target folder path from available_categories if possible
                resolved_rel_path = None
                if category_folder in available_categories:
                    resolved_rel_path = category_folder
                else:
                    # Match base folder name case-insensitively
                    for path, name in available_categories.items():
                        if category_folder.lower() == name.lower() or Path(path).name.lower() == category_folder.lower():
                            resolved_rel_path = path
                            break
                            
                # Determine final target folder path and verify it exists on disk
                target_folder = None
                if resolved_rel_path:
                    potential_folder = TARGET_ROOT / resolved_rel_path
                    if potential_folder.is_dir():
                        target_folder = potential_folder
                
                # If target folder was not resolved or does not exist, move to Unsorted_Review
                if not target_folder:
                    logger.warning(f"⚠️ Target folder '{category_folder}' not identified properly or does not exist on disk. Moving to Unsorted_Review...")
                    success, new_path = FileOperations.move_to_unsorted(
                        str(file_path),
                        f"Target folder '{category_folder}' not identified properly or does not exist"
                    )
                    if success:
                        self.execution_logger.log_manual_review(
                            file_path.name,
                            str(file_path.parent),
                            f"Target folder '{category_folder}' does not exist or not identified: {reasoning}",
                            confidence
                        )
                        with self.stats_lock:
                            self.stats["manual_reviews"] += 1
                    else:
                        logger.error("Failed to move file to Unsorted_Review")
                        self.execution_logger.log_error(
                            file_path.name,
                            str(file_path.parent),
                            "Failed to move to Unsorted_Review"
                        )
                        with self.stats_lock:
                            self.stats["errors"] += 1
                    return
                
                is_dup_content, existing_file = FileOperations.check_duplicate_content(
                    str(file_path),
                    str(target_folder)
                )
                
                if is_dup_content:
                    logger.warning(f"⚠️  Duplicate content detected: {existing_file}")
                    self.execution_logger.log_skipped(
                        file_path.name,
                        str(file_path.parent),
                        f"Duplicate content found: {Path(existing_file).name}"
                    )
                    with self.stats_lock:
                        self.stats["files_skipped"] += 1
                    return
                
                # Step 7: Move file
                logger.info(f"🚀 Moving file to target folder...")
                success, new_file_path, message = FileOperations.move_file(
                    str(file_path),
                    str(target_folder),
                    new_filename
                )
                
                if not success:
                    logger.error(f"Failed to move file: {message}")
                    self.execution_logger.log_error(
                        file_path.name,
                        str(file_path.parent),
                        message
                    )
                    with self.stats_lock:
                        self.stats["errors"] += 1
                    return
                
                # Log success
                relative_path = FileOperations.get_relative_path(str(target_folder))
                self.execution_logger.log_success(
                    Path(new_file_path).name,
                    str(file_path.parent),
                    relative_path,
                    confidence
                )
                with self.stats_lock:
                    self.stats["files_moved"] += 1
                
                logger.info(f"✅ File organized successfully!")
                logger.info(f"   Final path: {new_file_path}\n")
        
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            self.execution_logger.log_error(
                file_path.name if 'file_path' in locals() else "unknown",
                str(file_path.parent) if 'file_path' in locals() else "unknown",
                str(e)
            )
            with self.stats_lock:
                self.stats["errors"] += 1
    
    def print_statistics(self):
        """Print processing statistics."""
        with self.stats_lock:
            stats_copy = self.stats.copy()
        logger.info("\n" + "=" * 70)
        logger.info("📊 LAFO Statistics")
        logger.info("=" * 70)
        logger.info(f"Files Processed: {stats_copy['files_processed']}")
        logger.info(f"Files Moved: {stats_copy['files_moved']}")
        logger.info(f"Files Skipped: {stats_copy['files_skipped']}")
        logger.info(f"Manual Reviews: {stats_copy['manual_reviews']}")
        logger.info(f"Errors: {stats_copy['errors']}")
        logger.info("=" * 70 + "\n")
    
    def run(self):
        """
        Run the LAFO system.
        This starts the file monitor and keeps it running.
        """
        try:
            if not self.initialize():
                logger.error("Failed to initialize LAFO")
                return False
            
            logger.info("🎯 LAFO is now running. Waiting for files in Downloads...")
            logger.info("Press Ctrl+C to stop.\n")
            
            # Keep the monitor running
            self.file_monitor.wait()
            
            return True
        
        except KeyboardInterrupt:
            logger.info("\n⏹️  LAFO shutting down...")
            self.shutdown()
            return True
        
        except Exception as e:
            logger.error(f"Fatal error in LAFO: {str(e)}")
            self.shutdown()
            return False
    
    def shutdown(self):
        """Shutdown LAFO gracefully."""
        if self.file_monitor:
            self.file_monitor.stop()
        
        logger.info("⏹️  Shutting down parallel processing thread pool...")
        try:
            self.executor.shutdown(wait=True)
        except Exception as e:
            logger.error(f"Error shutting down thread pool: {str(e)}")
            
        self.print_statistics()
        logger.info("👋 LAFO stopped")


def main():
    """Main entry point."""
    lock_path = LOGS_DIR / "lafo.lock"
    instance_lock = SingleInstance(lock_path)
    
    if not instance_lock.acquire():
        print("⚠️  Another instance of LAFO is already running. Exiting.", file=sys.stderr)
        return 0
        
    try:
        orchestrator = LAFOOrchestrator()
        success = orchestrator.run()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        return 1
    finally:
        instance_lock.release()


if __name__ == "__main__":
    sys.exit(main())
