# 🚀 LAFO - Local Agentic File Organizer

## Overview

LAFO is a 100% private, local, AI-powered file organization system that automatically monitors your Windows Downloads folder, intelligently categorizes files, renames them semantically, and moves them to appropriate folders in your document structure.

**Key Features:**
- ✅ **Completely Local** - No cloud uploads, no data transmission
- ✅ **Parallel Document Processing (New in v1.2)** - Process multiple downloads concurrently using a thread pool
- ✅ **GPU Auto-Detection (New in v1.2)** - Automatically utilizes your local GPU (CUDA) for embeddings when available
- ✅ **Semantic Intelligence** - Uses local or cloud-based LLMs to understand file content
- ✅ **Automatic Organization** - Monitors Downloads and routes files to appropriate folders
- ✅ **Smart Renaming** - Generates readable filenames from document content
- ✅ **Confidence Scoring** - Routes low-confidence files for manual review
- ✅ **Duplicate Detection** - Prevents duplicate files in destination folders using size optimization and SHA-256 content hashes
- ✅ **Execution Logging** - Thread-safe logging tracks all operations in a central audit trail
- ✅ **Robust Windows Support** - Integrates watchdog monitor for browser rename events (`on_moved`) and bypasses Controlled Folder Access restrictions.

## Architecture

### System & Thread Pool Architecture (v1.2)

LAFO utilizes a multithreaded architecture. When the file monitor detects file creations or renames, instead of blocking the main thread, events are submitted to a thread pool for parallel execution.

```
                  ┌──────────────────────────────────────────┐
                  │               WATCHDOG                   │
                  │   Monitors Downloads Folder (on_moved)   │
                  └────────────────────┬─────────────────────┘
                                       │
                                       ▼ (Submits task)
                  ┌──────────────────────────────────────────┐
                  │        THREAD POOL EXECUTOR              │
                  │   Queues and processes tasks in parallel  │
                  └──────┬────────────────────────────┬──────┘
                         │                            │
            (Thread 1)   ▼               (Thread 2)   ▼
        ┌────────────────────────┐        ┌────────────────────────┐
        │   TEXT EXTRACTION      │        │   TEXT EXTRACTION      │
        │   (PDF / OCR fallback) │        │   (PDF / OCR fallback) │
        └──────────┬─────────────┘        └──────────┬─────────────┘
                   │                                 │
                   ▼                                 ▼
        ┌────────────────────────┐        ┌────────────────────────┐
        │   VECTOR SEARCH        │        │   VECTOR SEARCH        │
        │   (HuggingFace GPU/CPU)│        │   (HuggingFace GPU/CPU)│
        └──────────┬─────────────┘        └──────────┬─────────────┘
                   │                                 │
                   ▼                                 ▼
        ┌────────────────────────┐        ┌────────────────────────┐
        │   SEMANTIC ROUTING     │        │   SEMANTIC ROUTING     │
        │   (Gemini API/Ollama)  │        │   (Gemini API/Ollama)  │
        └──────────┬─────────────┘        └──────────┬─────────────┘
                   │                                 │
                   ▼ (Sync File Operations)          ▼ (Sync File Operations)
        ┌──────────────────────────────────────────────────────────┐
        │                 FILESYSTEM LOCK                          │
        │   - Thread-safe duplicate check (SHA-256)                │
        │   - Atomic file move & rename                            │
        │   - Thread-safe statistics updates & execution logs      │
        └──────────────────────────────────────────────────────────┘
```

### Thread Safety and Concurrency Controls
* **File System Operations Lock (`self.file_op_lock`):** Ensures that duplicate content checks and file moves do not clash when multiple threads try to write files to the same target folder at the same millisecond.
* **Statistics Lock (`self.stats_lock`):** Synchronizes operations on global stats counters.
* **Execution Log Lock (`self.lock`):** Serializes append operations to `execution.log` to prevent log interleaving or corruption.
* **GPU Auto-Detection:** Automatically leverages PyTorch GPU (CUDA) resources for the embeddings model, falling back to CPU if GPU drivers or CUDA builds are unavailable.��─────────────────┐
│          SEMANTIC ROUTING AGENT                         │
│  - Local LLM (Llama 3 via Ollama)                      │
│  - Classifies documents                                │
│  - Extracts dates                                       │
│  - Generates confidence scores                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         FILE OPERATIONS & ROUTING                       │
│  - Duplicate detection (content hash)                  │
│  - Smart renaming                                       │
│  - Move to destination or Unsorted_Review              │
│  - Execution logging                                    │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

### System Requirements
- **OS:** Windows 10/11
- **Python:** 3.10+
- **RAM:** 8GB minimum (16GB recommended for LLM)
- **Disk:** 50GB free (for models and vector database)

### Required Software

1. **Python 3.10+**
   - Download from https://python.org
   - Install with "Add Python to PATH"

2. **LLM Provider (Choose One or Both):**
   - **Option A: Google Gemini API (Cloud Option - Recommended for speed)**
     - Get a free API Key from [Google AI Studio](https://aistudio.google.com/)
     - Default model: `gemini-2.5-flash`
   - **Option B: Ollama (Local LLM Runtime)**
     - Download from https://ollama.ai
     - Install and run: `ollama serve`
     - Pull Llama 3 model: `ollama pull llama3:8b` (or another model like `mistral`)

3. **Tesseract-OCR** (For image text extraction)
   - Download installer from https://github.com/UB-Mannheim/tesseract/wiki or "https://sourceforge.net/projects/tesseract-ocr.mirror/files/latest/download"
   - Install to: `C:\Program Files\Tesseract-OCR\`
   - Update path in `config.py` if different

## Environment Configuration

Create a `.env` file in the project root directory and define the following variables:

```ini
# Choose 'gemini' or 'ollama'
LLM_PROVIDER=gemini

# If using Gemini, paste your API Key here:
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# If using local Ollama (optional configuration):
# OLLAMA_MODEL=llama3:8b
```

## Installation

### 1. Clone/Copy the Project

```bash
cd c:\Users\bussu\MyPracticalsVScode\AI\Agentic_File_Organizer
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**First-time setup note:** Installing dependencies takes 10-15 minutes due to:
- HuggingFace embedding models (~400MB)
- PyTorch (~500MB)
- FAISS (~200MB)

### 4. Configure Paths

Edit `config.py` and verify these paths:

```python
# Source directory (where files are downloaded)
DOWNLOADS_DIR = Path(os.path.expanduser("~/Downloads"))

# Target directory (where files will be organized)
TARGET_ROOT = Path(r"C:\Users\bussu\Documents\vamshi\SCANNED DOCUMENTS")

# Unsorted review folder (auto-created)
UNSORTED_FOLDER = TARGET_ROOT / "Unsorted_Review"

# Tesseract OCR path (for image text extraction)
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### 5. Initialize Directory Taxonomy

The system automatically scans your target folder structure on first run. Make sure your folder structure exists:

```
C:\Users\bussu\Documents\vamshi\SCANNED DOCUMENTS\
├── Medical Reports/
├── Invoices/
├── Vehicle Documents/
├── Bank Statements/
├── Insurance/
├── Utilities/
└── [Other Categories]/
```

## Running LAFO

### Start the System

```bash
# Activate virtual environment (if not already active)
venv\Scripts\activate

# Run LAFO
python main.py
```

You should see:

```
======================================================================
🚀 LAFO - Local Agentic File Organizer Starting
======================================================================

📋 Initializing LAFO Components...
1️⃣  Initializing Vector Store...
   ✅ Vector store ready
2️⃣  Initializing Routing Agent...
   ✅ Routing agent ready (Ollama connected)
3️⃣  Verifying Directory Structure...
   ✅ Directory structure verified
4️⃣  Initializing File Monitor...
   ✅ File monitor started

✅ LAFO Initialization Complete!
======================================================================
📁 Monitoring: C:\Users\bussu\Downloads
📂 Target Root: C:\Users\bussu\Documents\vamshi\SCANNED DOCUMENTS
======================================================================

🎯 LAFO is now running. Waiting for files in Downloads...
Press Ctrl+C to stop.
```

### How It Works

1. **File Detection**
   - Monitors Downloads folder in real-time
   - Ignores temporary files (.crdownload, .tmp, .part)
   - Waits for file to be completely written

2. **Content Extraction**
   - Extracts text from PDFs (native + OCR fallback)
   - Extracts text from images using OCR
   - Extracts text from DOCX, HTML, TXT files

3. **Semantic Analysis**
   - Sends document to local Llama 3 LLM
   - Analyzes against your folder taxonomy
   - Extracts document date
   - Generates confidence score (0-100%)

4. **Smart Routing**
   - **High Confidence (≥75%)**: Automatically moves file with new name
   - **Low Confidence (<75%)**: Routes to Unsorted_Review for manual check
   - **Duplicate Detected**: Skips file to prevent overwrites

5. **Execution Logging**
   - All operations logged to `execution.log`
   - Format: `[timestamp] status | filename | source → destination | message`

## Configuration

### Key Parameters in `config.py`

#### Confidence Threshold
```python
CONFIDENCE_THRESHOLD = 75  # 0-100 (default 75%)
```
Files with confidence below this go to Unsorted_Review.

#### Model Selection
```python
LLM_PROVIDER = "gemini"            # Options: "gemini", "ollama"
GEMINI_MODEL = "gemini-2.5-flash"  # Used if LLM_PROVIDER is "gemini"
OLLAMA_MODEL = "llama3:8b"         # Used if LLM_PROVIDER is "ollama"
```

#### Embedding Model
```python
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Lightweight, fast
# Or: "all-mpnet-base-v2" (more accurate, slower)
```

#### File Monitoring
```python
FILE_STABLE_TIME = 2  # Seconds to wait for file stability
DEBOUNCE_TIME = 3     # Seconds before processing
WATCH_POLL_INTERVAL = 2  # Check frequency
```

## Execution Log Format

```
[2024-06-15T14:32:45.123456] ✅ SUCCESS | Apollo_Diagnostics_CBC.pdf | C:\Users\bussu\Downloads → Medical Reports | Confidence: 92.3%

[2024-06-15T14:35:22.654321] ⚠️  MANUAL_REVIEW | unknown_document.pdf | C:\Users\bussu\Downloads → Unsorted_Review | Low confidence classification (65.0%) | Confidence: 65.0%

[2024-06-15T14:38:10.987654] ❌ ERROR | corrupted_file.pdf | C:\Users\bussu\Downloads | Failed to extract text content

[2024-06-15T14:40:55.321098] ⏭️  SKIPPED | duplicate_bill.pdf | C:\Users\bussu\Downloads | Duplicate content found: utility_bill_2024-06.pdf
```

## Troubleshooting

### Ollama Connection Error
```
❌ Cannot connect to Ollama: [Errno 10061]
```

**Solution:**
```bash
# In a separate terminal/command prompt:
ollama serve

# In another terminal, ensure the model is available:
ollama pull llama3:8b
```

### Text Extraction Fails
```
❌ Error extracting PDF text: 'pdfplumber' module not found
```

**Solution:**
```bash
pip install pdfplumber
```

### Low Confidence Files
If many files go to Unsorted_Review, consider:
1. Lower confidence threshold in `config.py`
2. Improve folder naming in your directory structure
3. Ensure documents contain clear category keywords

### OCR Issues
If image text extraction fails:
1. Verify Tesseract installation: `C:\Program Files\Tesseract-OCR\tesseract.exe`
2. For high-DPI images: Ensure image quality is sufficient
3. Check OCR language setting in `config.py`

## Advanced Features

### 1. Custom System Prompt
Edit the routing system prompt in `config.py`:

```python
ROUTING_SYSTEM_PROMPT = """
You are an expert document classification AI...
[customize classification behavior]
"""
```

### 2. Different LLM Models

Switch models in `config.py`:

```python
# Faster, lower quality
OLLAMA_MODEL = "mistral"  # 7B parameters, ~4GB

# More accurate
OLLAMA_MODEL = "llama3:8b"  # 8B parameters, ~5GB

# Smaller, slower
OLLAMA_MODEL = "llama2"  # 7B parameters, ~4GB
```

Pull new models:
```bash
ollama pull <model_name>
```

### 3. Vector Store Refresh
If you add new folder categories:

```python
# Force rebuild in main.py before running:
if __name__ == "__main__":
    orchestrator = LAFOOrchestrator()
    orchestrator.vector_store.refresh_from_filesystem()
    orchestrator.run()
```

## Performance Optimization

### For Slower Systems
1. **Reduce embedding model size:**
   ```python
   EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Already smallest
   ```

2. **Use faster LLM:**
   ```python
   OLLAMA_MODEL = "mistral"
   ```

3. **Limit text extraction:**
   ```python
   MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB instead of 500MB
   ```

### For Production Use
1. **Increase confidence threshold:**
   ```python
   CONFIDENCE_THRESHOLD = 85  # More selective routing
   ```

2. **Enable verbose logging:**
   ```python
   VERBOSE_LOGGING = True
   ```

3. **Regular log review:**
   - Check `execution.log` daily
   - Verify Unsorted_Review folder
   - Retrain by adjusting folder names

## Project Structure

```
Agentic_File_Organizer/
├── main.py                 # Orchestrator & entry point
├── config.py              # Configuration & constants
├── vector_store.py        # Vector DB management
├── text_extractor.py      # PDF, image, document parsing
├── agent.py               # LLM-based routing agent
├── file_monitor.py        # Watchdog file monitoring
├── file_operations.py     # File moving & duplicate detection
├── execution_logger.py    # Logging system
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── vectorstore/           # Local vector database (auto-created)
│   ├── index.faiss
│   ├── index.pkl
│   └── directory_metadata.json
├── execution.log          # Operation log (auto-created)
├── lafo.log              # Debug log (auto-created)
└── lafo_debug.log        # Detailed debug log (auto-created)
```

## Privacy & Security

LAFO is designed for maximum privacy:

✅ **Never Transmitted:**
- File paths
- File names (except in local logs)
- Document text or content
- Metadata
- Classification decisions

✅ **Local Only:**
- All processing on your machine
- No network calls except to local Ollama
- All data stored locally
- Full audit trail in logs

## Support & Debugging

### Enable Debug Logging
Modify `config.py`:
```python
VERBOSE_LOGGING = True
```

### Check Logs
```bash
# Real-time processing log
tail -f execution.log

# Detailed debug log
tail -f lafo.log

# Full debug output
tail -f lafo_debug.log
```

### Test Individual Components
```python
# Test vector store
from vector_store import VectorStoreManager
vs = VectorStoreManager()
vs.initialize_vectorstore()

# Test text extraction
from text_extractor import TextExtractor
text, success = TextExtractor.extract_content("your_file.pdf")

# Test agent
from agent import RoutingAgent
agent = RoutingAgent()
print(agent.check_ollama_connection())
```

## Next Steps / Future Enhancements

1. **Web Dashboard** - Real-time monitoring UI
2. **Conflict Resolution** - Interactive manual routing
3. **Training Mode** - Learn from manual corrections
4. **Batch Processing** - Process existing Downloads backlog
5. **Cloud Sync** - Optional encrypted cloud backup
6. **Email Integration** - Auto-organize email attachments
7. **Scheduled Tasks** - Run on Windows Task Scheduler

## License & Credits

This project uses open-source libraries:
- **LangChain** - AI orchestration framework
- **Ollama** - Local LLM runtime
- **Watchdog** - File system monitoring
- **pdfplumber** - PDF text extraction
- **FAISS** - Vector database
- **HuggingFace** - Embeddings

## Contact & Issues

For questions or issues:
1. Check the troubleshooting section
2. Review execution logs
3. Test individual components
4. Verify Ollama is running

---

**Happy organizing! 🎉**
