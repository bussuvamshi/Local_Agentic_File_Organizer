"""
Configuration and constants for LAFO (Local Agentic File Organizer)
"""
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# LLM PROVIDER SELECTION
# ============================================================================

# Choose between 'ollama' or 'gemini'
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

# ============================================================================
# PATHS CONFIGURATION
# ============================================================================

# Source directory (Downloads folder)
DOWNLOADS_DIR = Path(os.path.expanduser("~/Downloads"))

# Target root directory for organized documents
TARGET_ROOT = Path(r"C:\Users\bussu\Documents\vamshi")

# Unsorted/Review folder for low-confidence matches
UNSORTED_FOLDER = TARGET_ROOT / "Unsorted_Review"

# Vector store location
VECTORSTORE_DIR = "vectorstore"
VECTORSTORE_METADATA = "directory_metadata.json"

# Logs directory for daily rotating logs
LOGS_DIR = Path(r"C:\Users\bussu\Documents\LAFO logs")

# ============================================================================
# OLLAMA CONFIGURATION
# ============================================================================

OLLAMA_API = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3:8b"  # Or use mistral, llama2, etc.
OLLAMA_TIMEOUT = 180  # seconds

# ============================================================================
# GEMINI CONFIGURATION
# ============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Validate Gemini API key if using Gemini
if LLM_PROVIDER == "gemini" and not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please set it.")

# ============================================================================
# FILE FILTERING
# ============================================================================

# Supported file extensions
SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".docx", ".html", ".doc", ".jpg", ".jpeg", ".png", ".bmp"]

# Temporary/In-progress file patterns to ignore
TEMP_PATTERNS = [".crdownload", ".tmp", ".part", "~$"]

# Maximum file size to process (500 MB)
MAX_FILE_SIZE = 500 * 1024 * 1024

# ============================================================================
# OCR & TEXT EXTRACTION
# ============================================================================

# PDF chunk size for text splitting
PDF_CHUNK_SIZE = 500
PDF_CHUNK_OVERLAP = 100

# OCR configuration
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Windows path
OCR_LANGUAGE = "eng"

# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

# Confidence threshold for automatic routing (0-100)
CONFIDENCE_THRESHOLD = 75

# Maximum number of candidate folders to consider
MAX_CANDIDATES = 3

# Vector similarity search k parameter
VECTOR_SEARCH_K = 5

# Maximum document characters to send to LLM (keeps input tokens low)
MAX_TEXT_LENGTH = 1500

# System prompt for the routing agent
ROUTING_SYSTEM_PROMPT = """
You are a personal document classifier. Match document content to one of the family folders.
Analyze content for names, IDs, phones, addresses, or emails to identify the person.

Folders: Vamshi, Bhagya Lasmi, Nanamma, Property documents, Vishnu, Kothapally, Jagath Reddy

Rules:
1. Extract document/transaction date as YYYY-MM-DD. Fallback: file creation date.
2. Confidence score must be an integer between 0 and 100. If unsure, set < 75.
3. Suggest a clean, concise filename.
4. Reasoning must be a single short sentence.

You must respond with a single valid JSON object. Do not wrap the JSON in markdown code blocks or add any other text outside the JSON.

Expected JSON format:
{
    "confidence_score": 90,
    "category_folder": "Vamshi",
    "suggested_filename": "vamshi_pension_details.txt",
    "document_date": "2026-06-17",
    "reasoning": "Document contains pension details belonging to Vamshi."
}
"""

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_FORMAT = "[{timestamp}] {status} | {filename} | {source_dir} -> {target_dir} | {message}"

LOG_STATUS_SUCCESS = "SUCCESS"
LOG_STATUS_ERROR = "ERROR"
LOG_STATUS_SKIPPED = "SKIPPED"
LOG_STATUS_MANUAL_REVIEW = "MANUAL_REVIEW"

# ============================================================================
# WATCH CONFIGURATION
# ============================================================================

# Watchdog event handler configuration
WATCH_POLL_INTERVAL = 2  # seconds (check every 2 seconds for new files)
DEBOUNCE_TIME = 3  # seconds (wait before processing a file)

# File modification stable time (how long to wait to ensure file is written completely)
FILE_STABLE_TIME = 2  # seconds

# Thread pool configuration for parallel processing
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))

# ============================================================================
# EMBEDDING MODEL
# ============================================================================

# Local embedding model (downloaded via HuggingFace)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Lightweight, local-friendly model

# ============================================================================
# RETRY & ERROR HANDLING
# ============================================================================

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# ============================================================================
# UI & OUTPUT
# ============================================================================

VERBOSE_LOGGING = True  # Print detailed logs to console
