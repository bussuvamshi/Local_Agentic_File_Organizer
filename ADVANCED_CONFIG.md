# 🛠️ LAFO Advanced Configuration Guide

## Table of Contents
1. [Custom System Prompts](#custom-system-prompts)
2. [Model Selection & Tuning](#model-selection--tuning)
3. [Confidence & Routing](#confidence--routing)
4. [Performance Optimization](#performance-optimization)
5. [Vector Store Customization](#vector-store-customization)
6. [Logging & Monitoring](#logging--monitoring)

---

## Custom System Prompts

### Improving LLM Classification Behavior

The system prompt controls how the LLM classifies documents. Edit `config.py`:

```python
ROUTING_SYSTEM_PROMPT = """
You are an expert document classification AI for a personal file organization system.
Your task is to:
1. Analyze the document content extracted from files
2. Compare it against existing folder categories in the user's file system
3. Recommend the best-fitting destination folder
4. Extract the most relevant date from the document
5. Provide a confidence score for your classification decision

IMPORTANT GUARDRAILS:
- You work ENTIRELY locally with no cloud connections
- You MUST analyze the document text to determine its category
- If you cannot confidently classify the document, output a confidence < 75%
- You MUST extract a specific date (document date, transaction date, test date, etc.)
- Date format: YYYY-MM-DD (e.g., 2024-06-15)
- If no clear date exists, use today's date

OUTPUT FORMAT:
Respond in this exact JSON format:
{
    "confidence_score": <0-100>,
    "category_folder": "<best matching folder name>",
    "suggested_filename": "<new clean filename without path>",
    "document_date": "YYYY-MM-DD",
    "reasoning": "<brief explanation of your classification>"
}
"""
```

### Example: Custom Prompt for Business Documents

```python
ROUTING_SYSTEM_PROMPT = """
You are an expert business document classification AI.

FOLDER CATEGORIES (user's actual structure):
- Invoices & Receipts
- Payroll & HR Documents
- Bank Statements
- Tax Returns
- Legal Contracts
- Project Documentation

CLASSIFICATION RULES:
1. Look for invoice numbers, vendor names, amounts
2. Extract date as: Document Date > Statement Date > Transaction Date
3. For ambiguous docs, check for:
   - Company letterhead or official stamps
   - Signature lines (more formal = higher confidence)
   - Multi-page documents (higher confidence than single page)

CONFIDENCE SCORING:
- 95-100%: Clear category keywords, formatted document, recent date
- 80-94%: Some identifying features, reasonable document quality
- 65-79%: Minimal indicators, ambiguous content, poor quality scan
- <65%: Insufficient information for confident classification

OUTPUT JSON:
{
    "confidence_score": <0-100>,
    "category_folder": "<exact folder name from categories above>",
    "suggested_filename": "<CATEGORY_DOCUMENT_DATE.pdf>",
    "document_date": "YYYY-MM-DD",
    "reasoning": "<explain what led to this classification>"
}
"""
```

---

## Model Selection & Tuning

### Available LLM Models

| Model | Size | Speed | Quality | VRAM | Best For |
|-------|------|-------|---------|------|----------|
| **mistral** | 7B | ⚡⚡⚡ | ⭐⭐⭐ | 5GB | Fast processing, reasonable accuracy |
| **llama3:8b** | 8B | ⚡⚡ | ⭐⭐⭐⭐ | 6GB | **Default - balanced** |
| **llama2** | 7B | ⚡⚡ | ⭐⭐⭐ | 4GB | Lightweight, older model |
| **neural-chat** | 7B | ⚡⚡⚡ | ⭐⭐⭐⭐ | 5GB | Conversational, good quality |

### Installation & Selection

```bash
# Pull different models
ollama pull mistral
ollama pull llama3:8b
ollama pull neural-chat
ollama pull llama2

# Set in config.py
OLLAMA_MODEL = "mistral"  # Switch between models
```

### Temperature & Sampling

Add to `agent.py` in `_call_ollama()`:

```python
payload = {
    "model": self.model,
    "messages": messages,
    "stream": False,
    "temperature": 0.3,        # 0.0 = deterministic, 1.0 = creative
    "top_p": 0.9,             # Nucleus sampling
    "top_k": 40,              # Top-k sampling
}
```

**Temperature Tuning:**
- `0.1-0.3`: Very deterministic (recommended for routing)
- `0.5-0.7`: Balanced (default behavior)
- `0.8-1.0`: More creative (worse for classification)

### Embedding Model Selection

```python
# config.py
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, lightweight
# OR
EMBEDDING_MODEL = "all-mpnet-base-v2"  # More accurate, slower
# OR
EMBEDDING_MODEL = "paraphrase-MiniLM-L6-v2"  # Semantic similarity
```

Download custom models:

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('your-model-name')
# This downloads and caches the model
```

---

## Confidence & Routing

### Confidence Threshold Configuration

```python
# config.py

# Minimum confidence for automatic routing (75%)
CONFIDENCE_THRESHOLD = 75

# For stricter routing (fewer errors)
CONFIDENCE_THRESHOLD = 85

# For more lenient routing (fewer manual reviews)
CONFIDENCE_THRESHOLD = 65
```

### Confidence Distribution

Typical distribution after processing:
```
90-100%: 60% of files (clear documents)
75-89%: 25% of files (mostly clear)
60-74%: 10% of files (somewhat ambiguous)
<60%:  5% of files (very ambiguous)
```

If distribution is skewed, adjust:
1. **Too many manual reviews?** → Lower threshold
2. **Too many misroutes?** → Raise threshold
3. **Many 60-75% files?** → Improve folder naming

### Custom Routing Logic

Edit `main.py` to add custom rules:

```python
# In process_file() method, after classification:

classification = self.routing_agent.classify_document(...)

# Custom rule example: invoices always need high confidence
if "invoice" in classification.get("category_folder", "").lower():
    if confidence < 85:  # Stricter for invoices
        logger.warning("Invoice with low confidence, routing to manual review")
        FileOperations.move_to_unsorted(str(file_path), "Invoice needs verification")
        return

# Custom rule: always check date validity
doc_date = classification.get("document_date")
if not is_recent_date(doc_date):
    logger.warning(f"Unusual document date: {doc_date}")
    # Can decide to route to manual review
```

---

## Performance Optimization

### CPU Mode vs GPU Mode

```python
# config.py - Force CPU (if you lack GPU)

# This is automatic, but you can configure:
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Force CPU

# Or use Ollama flags:
# ollama serve --gpu 0  (disable GPU)
# ollama serve --gpu 1  (enable GPU)
```

### Batch Processing

Process multiple files efficiently:

```python
# Create batch_processor.py
from pathlib import Path
from main import LAFOOrchestrator

def batch_process(folder_path):
    orchestrator = LAFOOrchestrator()
    if not orchestrator.initialize():
        return
    
    files = list(Path(folder_path).glob("*"))
    for file_path in files:
        if file_path.is_file():
            print(f"\nProcessing {file_path.name}...")
            orchestrator.process_file(str(file_path))
    
    orchestrator.print_statistics()

if __name__ == "__main__":
    batch_process("C:/Users/bussu/Downloads")
```

### Cache Management

LAFO automatically caches:
- Embedding models (~400MB)
- Vector store index
- Ollama models (5-6GB each)

Clear cache if needed:

```bash
# HuggingFace cache
rm -r C:\Users\bussu\.cache\huggingface

# Ollama models
ollama rm llama3:8b

# LAFO vector store
rm -r vectorstore/

# Execution logs
rm execution.log lafo.log lafo_debug.log
```

### Memory Optimization

For systems with <8GB RAM:

```python
# config.py

# Use smaller embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Already minimal

# Use faster LLM
OLLAMA_MODEL = "mistral"

# Reduce text extraction size
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB instead of 500MB

# Reduce vector search results
VECTOR_SEARCH_K = 3  # instead of 5
```

---

## Vector Store Customization

### Vector Candidate Pre-Filtering (New in v1.3)

To prevent LLM CPU timeouts on large folder taxonomies (e.g. 302 categories), LAFO uses FAISS similarity search to pre-filter and narrow down the list of destination folders before invoking the LLM.

Modify these parameters in `config.py`:
```python
# Maximum number of candidate folders to send to LLM for classification
MAX_CANDIDATES = 3

# Number of direct taxonomy matches retrieved from the FAISS database
VECTOR_SEARCH_K = 5
```

- **How it works:** When a document is processed, its text is sent to the FAISS database using local embeddings. The database returns the top `VECTOR_SEARCH_K` nearest taxonomy or exemplar matches. The system extracts unique parent folder paths, resulting in a narrowed set of categories (capped at `MAX_CANDIDATES`), which are then passed to the LLM.
- **Benefit:** Reduces the LLM's context size from >20,000 characters to <1,500 characters, resolving Ollama timeouts and increasing processing speed.

### Exemplar-Based File Indexing (New in v1.3)

LAFO's vector database does not just index folder names; it also indexes the files already stored in those folders to learn your manual naming conventions.

- **Scanning exemplars:** On initialization/refresh, `VectorStoreManager` scans the subdirectories inside your target directory. For each subdirectory, it indexes the first **15 files** (excluding hidden files) as semantic "exemplars".
- **Matching pattern:** If you drag a new file that has a similar naming pattern to existing files in a specific folder, the FAISS similarity search will match against those file exemplars, pointing the system to the correct parent folder.
- **Configuration:** You can adjust the limit of exemplars per folder in `vector_store.py` (default: `15`).

### Rebuild Directory Taxonomy


When you add/change folder structure:

```python
# main.py - Force rebuild before running

if __name__ == "__main__":
    orchestrator = LAFOOrchestrator()
    
    # Force rebuild vector store from filesystem
    orchestrator.vector_store = VectorStoreManager()
    orchestrator.vector_store.initialize_vectorstore(force_rebuild=True)
    
    orchestrator.run()
```

### Add Custom Metadata to Folders

```python
# Modify vector_store.py - build_directory_taxonomy()

# Instead of just folder name, add description:
doc_content = f"""
Folder Category: {folder_name}
Path: {relative_path}
Description: This is a file category folder in the document organization system.
Category Name: {folder_name}

Keywords: {', '.join(get_folder_keywords(folder_name))}
"""

def get_folder_keywords(folder_name):
    keywords_map = {
        "Medical Reports": ["doctor", "diagnosis", "patient", "hospital", "prescription", "test", "lab"],
        "Invoices": ["invoice", "bill", "payment", "vendor", "amount", "receipt"],
        "Bank Statements": ["bank", "account", "transaction", "statement", "deposit", "withdrawal"],
        # Add more...
    }
    return keywords_map.get(folder_name, [])
```

### Custom Vector Search

```python
# In agent.py - classify_document()

# Get similar categories
matches = self.vector_store.search_similar_folders(document_text, k=3)

# Custom scoring based on keyword matches
for folder_path, similarity, folder_name in matches:
    keyword_score = count_matching_keywords(document_text, folder_name)
    combined_score = 0.7 * similarity + 0.3 * keyword_score
    # Use combined score for routing
```

---

## Logging & Monitoring

### Debug Logging Configuration

```python
# config.py

# Enable verbose logging
VERBOSE_LOGGING = True

# Set log level
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Add custom logger for specific modules
import logging
logging.getLogger("vector_store").setLevel(logging.DEBUG)
logging.getLogger("agent").setLevel(logging.DEBUG)
```

### Custom Log Analysis

```python
# Create log_analyzer.py
from pathlib import Path
from datetime import datetime
import json
from collections import defaultdict

def analyze_execution_log(log_file="execution.log"):
    stats = {
        "success": 0,
        "error": 0,
        "skipped": 0,
        "manual_review": 0,
        "categories": defaultdict(int),
        "avg_confidence": [],
    }
    
    with open(log_file, "r") as f:
        for line in f:
            if "SUCCESS" in line:
                stats["success"] += 1
                # Extract confidence
                if "Confidence:" in line:
                    conf = float(line.split("Confidence: ")[1].split("%")[0])
                    stats["avg_confidence"].append(conf)
            elif "ERROR" in line:
                stats["error"] += 1
            # ... parse other statuses
    
    print(f"Success: {stats['success']}")
    print(f"Average Confidence: {sum(stats['avg_confidence']) / len(stats['avg_confidence']):.1f}%")
    print(f"Error Rate: {stats['error'] / (stats['success'] + stats['error']) * 100:.1f}%")

if __name__ == "__main__":
    analyze_execution_log()
```

### Real-time Monitoring Dashboard

```python
# Create dashboard.py (requires Flask)
from flask import Flask, render_template
from pathlib import Path
import time

app = Flask(__name__)

@app.route("/status")
def status():
    log_file = Path("execution.log")
    last_lines = log_file.read_text().split("\n")[-10:]
    
    return {
        "last_operations": last_lines,
        "timestamp": time.time()
    }

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

---

## Integration Examples

### Windows Task Scheduler

Run LAFO automatically on startup:

```batch
@echo off
cd C:\Users\bussu\MyPracticalsVScode\AI\Local_Agentic_File_Organizer_(LAFO)
call venv\Scripts\activate.bat
python main.py
```

Save as `run_lafo.bat`, then:
1. Open Task Scheduler
2. Create Basic Task → "LAFO File Organizer"
3. Trigger: On startup
4. Action: Run `run_lafo.bat`

### Email Attachment Processing

```python
# future_enhancement.py - not yet implemented
import imaplib
from email.mime.base import MIMEBase

def process_email_attachments():
    # Extract attachments from email
    # Save to Downloads
    # LAFO processes automatically
    pass
```

### Slack Notifications

```python
# Create slack_notifier.py (future enhancement)
from slack_sdk import WebClient

def notify_file_organized(filename, folder, confidence):
    client = WebClient(token="xoxb-...")
    client.chat_postMessage(
        channel="#file-organization",
        text=f"📁 {filename} → {folder} ({confidence}%)"
    )
```

---

## Troubleshooting Advanced Issues

### Low Confidence Always
```python
# Check if folder names are descriptive enough
# Rename from: "Documents", "Files"
# Rename to: "Medical Records - Doctor Bills", "Legal Contracts - Agreements"

# Improve system prompt to look for specific keywords
```

### OCR Not Working
```python
# Verify Tesseract installation
import subprocess
result = subprocess.run(["tesseract", "--version"])
print(result.stdout)

# Update config.py path if needed
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### Vector Search Not Finding Matches
```python
# Check metadata file
import json
with open("vectorstore/directory_metadata.json") as f:
    metadata = json.load(f)
    print(f"Categories: {len(metadata['categories'])}")
    for cat in metadata['categories']:
        print(f"  - {cat['folder_name']}")

# Force rebuild if new folders added
```

---

## Performance Benchmarks

Typical performance on modern hardware (i7, 16GB RAM):

- **File Detection:** <100ms
- **Text Extraction (PDF):** 0.5-2s (depends on size)
- **Text Extraction (OCR):** 1-3s per page
- **LLM Classification:** 3-8s
- **File Move:** <100ms
- **Total per file:** 5-15 seconds

---

## Best Practices

1. **Folder Naming**
   - Use descriptive, specific names
   - Include key categories: "Medical Reports - Lab Tests"
   - Avoid generic names: "Documents"

2. **Confidence Threshold**
   - Start at 75%
   - Adjust based on false positives/negatives
   - Review Unsorted_Review folder weekly

3. **Monitoring**
   - Check logs daily initially
   - Review misclassified files
   - Retrain by improving folder names

4. **Maintenance**
   - Clean Unsorted_Review monthly
   - Archive processed files yearly
   - Clear logs quarterly

---

**For more help, see README.md and QUICKSTART.md**
