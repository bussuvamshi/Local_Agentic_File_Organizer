# 🚀 LAFO Quick Start Guide

## 5-Minute Setup

### 1. Prerequisites Check
- ✅ Python 3.10+ installed
- ✅ Ollama running (`ollama serve` in terminal)
- ✅ Llama 3 model available (`ollama pull llama3:8b`)
- ✅ Tesseract-OCR installed (for image text extraction)

### 2. Install & Configure
```bash
# Navigate to project
cd c:\Users\bussu\MyPracticalsVScode\AI\Local_Agentic_File_Organizer_(LAFO)

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Verify Paths (Edit config.py)
```python
DOWNLOADS_DIR = Path(os.path.expanduser("~/Downloads"))  # Should be fine
TARGET_ROOT = Path(r"C:\Users\bussu\Documents\vamshi\SCANNED DOCUMENTS")  # Update if needed
TESSERACT_PATH = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"  # Update if installed elsewhere
```

### 4. Run LAFO
```bash
python main.py
```

You should see:
```
🚀 LAFO - Local Agentic File Organizer Starting
✅ LAFO Initialization Complete!
🎯 LAFO is now running. Waiting for files in Downloads...
```

### 5. Test It
1. Download a PDF or image to your Downloads folder
2. LAFO automatically detects and processes it
3. Check `execution.log` for status

---

## Common Issues & Quick Fixes

### ❌ "Cannot connect to Ollama"
```bash
# In separate terminal:
ollama serve

# Then pull model if needed:
ollama pull llama3:8b
```

### ❌ "No category folders found"
Verify folder structure exists at:
```
C:\Users\bussu\Documents\vamshi\SCANNED DOCUMENTS\
├── Medical Reports/
├── Invoices/
└── [other folders]/
```

### ❌ "pdfplumber not found"
```bash
pip install pdfplumber
```

### ❌ "Tesseract not found"
1. Install from: https://github.com/UB-Mannheim/tesseract/wiki
2. Update path in config.py

---

## File Organization Flow

```
📥 File in Downloads
    ↓
🔍 Monitor detects it (watchdog)
    ↓
📖 Extract text (PDF/OCR/DOCX)
    ↓
🔍 Search local FAISS Vector store (Directory Taxonomy + File Exemplars)
    ↓
⚡ Filter down to top 3-5 candidates (prevents LLM timeout)
    ↓
🧠 Local LLM analyzes content (with native JSON mode & retries)
    ↓
❓ High confidence (≥75%)?
    ├─ YES → ✅ Move to appropriate folder with new name (after duplicate checks)
    └─ NO  → ⚠️  Move to Unsorted_Review for manual review (quarantine fallback)
    ↓
📊 Log to execution.log
```

---

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point - runs orchestrator and handles SingleInstance lock |
| `config.py` | All configuration (paths, thresholds, candidates, model selection) |
| `vector_store.py` | Manages directory taxonomy, indexes up to 15 exemplars per folder, FAISS DB |
| `agent.py` | LLM-based document routing (Ollama/Gemini, native JSON formatting, retry loops) |
| `file_monitor.py` | Watches Downloads folder and schedules files to parallel worker threads |
| `text_extractor.py` | Extracts text from PDF, DOCX, TXT, HTML, and images (Tesseract OCR) |
| `file_operations.py` | Move, rename, file stability, content duplicate checks (SHA-256) |
| `execution_logger.py` | Logs all operations (thread-safe, daily rotating) |
| `register_startup.ps1` | Registers LAFO to start silently as a Windows background task at logon |
| `unregister_startup.ps1`| Stops running background LAFO daemons and removes Windows logon registration |


---

## Configuration Quick Reference

```python
# config.py - Key settings

# Paths
DOWNLOADS_DIR = Path(os.path.expanduser("~/Downloads"))
TARGET_ROOT = Path(r"C:\Users\...\SCANNED DOCUMENTS")

# LLM & Models
OLLAMA_MODEL = "llama3:8b"  # or "mistral", "llama2"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Routing
CONFIDENCE_THRESHOLD = 75  # Percent (0-100)

# OCR
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Logging
VERBOSE_LOGGING = True  # Set to False for less output
```

---

## Logs & Monitoring

### Check Processing Status
```bash
# Real-time log
tail -f execution.log

# All events
tail -f lafo.log

# Full debug
tail -f lafo_debug.log
```

### Execution Log Format
```
[2024-06-15T14:32:45] ✅ SUCCESS | document.pdf | Downloads → Medical Reports | Confidence: 92.3%
[2024-06-15T14:35:22] ⚠️  MANUAL_REVIEW | unknown.pdf | Downloads → Unsorted_Review | Confidence: 65.0%
[2024-06-15T14:38:10] ❌ ERROR | bad_file.pdf | Downloads | Failed to extract text
```

---

## Performance Tips

### For Slow Systems
```python
# Use faster model
OLLAMA_MODEL = "mistral"

# Use smaller embedding model (already optimized)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Reduce max file size
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
```

### For Better Accuracy
```python
# Raise confidence threshold
CONFIDENCE_THRESHOLD = 85

# Improve folder naming with keywords
# Instead of: "Documents"
# Use: "Medical Reports - Doctor Bills - Lab Tests"
```

---

## Advanced: Manual Vector Store Refresh

If you add new folders to your target directory:

```python
# main.py
if __name__ == "__main__":
    orchestrator = LAFOOrchestrator()
    # Force rebuild the vector store
    orchestrator.vector_store = VectorStoreManager()
    orchestrator.vector_store.initialize_vectorstore(force_rebuild=True)
    orchestrator.run()
```

---

## Workflow Examples

### Example 1: Medical Report Processing
```
File: "document(1).pdf"
Content: "Apollo Diagnostics Complete Blood Count Report 2024-06-15..."

LAFO Processing:
1. ✅ Extracts: Medical test result text + date
2. 🧠 LLM thinks: "This is clearly a medical report"
3. 📊 Confidence: 94%
4. ✅ Renames: "Apollo_Diagnostics_Complete_Blood_Count_2024-06-15.pdf"
5. 📁 Moves to: SCANNED DOCUMENTS\Medical Reports\
6. 📝 Logs: SUCCESS | 94% confidence
```

### Example 2: Ambiguous Document
```
File: "IMG_2024_001.jpg"
Content: Blurry image, unclear content

LAFO Processing:
1. 📖 Extracts: Minimal text from OCR
2. 🧠 LLM thinks: "Could be insurance or utility..."
3. 📊 Confidence: 63% (below 75% threshold)
4. ⚠️  Moves to: SCANNED DOCUMENTS\Unsorted_Review\
5. 📝 Logs: MANUAL_REVIEW | 63% confidence
6. 🙋 Awaits your manual review
```

---

## Next Steps

1. ✅ Verify installation
2. ✅ Run initial test
3. ✅ Monitor first few files
4. ✅ Review execution.log
5. ✅ Adjust confidence threshold if needed
6. ✅ Let it run continuously!

---

## For Help

1. Check `README.md` for detailed documentation
2. Review logs: `execution.log`, `lafo.log`
3. Test components individually
4. Verify Ollama is running
5. Ensure folder structure exists

---

**Happy organizing! 🎉**
