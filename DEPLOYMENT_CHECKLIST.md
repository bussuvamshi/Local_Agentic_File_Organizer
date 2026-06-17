# ✅ LAFO Deployment & Setup Checklist

## Pre-Deployment Checklist

### System Requirements
- [ ] Windows 10/11 operating system
- [ ] Python 3.10 or higher installed
- [ ] At least 8GB RAM (16GB recommended)
- [ ] At least 50GB free disk space
- [ ] Stable internet connection (for initial setup only)

### External Software
- [ ] Ollama downloaded and installed
- [ ] Tesseract-OCR downloaded and installed
- [ ] Git (optional, for cloning)

---

## Installation Checklist

### Step 1: Python Setup
- [ ] Python installed and added to PATH
  ```bash
  python --version  # Should be 3.10+
  ```
- [ ] pip is working
  ```bash
  pip --version
  ```

### Step 2: Ollama Setup
- [ ] Ollama installed from https://ollama.ai
- [ ] Ollama service running
  ```bash
  ollama serve
  ```
- [ ] Llama 3 model pulled
  ```bash
  ollama pull llama3:8b
  ```
- [ ] Model loading works
  ```bash
  ollama list  # Should show llama3:8b
  ```

### Step 3: Tesseract OCR Setup
- [ ] Tesseract installer downloaded
- [ ] Tesseract installed to: `C:\Program Files\Tesseract-OCR\`
- [ ] Installation verified
  ```bash
  "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
  ```

### Step 4: Project Setup
- [ ] LAFO project folder created at:
  ```
  c:\Users\bussu\MyPracticalsVScode\AI\Local_Agentic_File_Organizer_(LAFO)\
  ```
- [ ] All project files copied/created
- [ ] requirements.txt present

### Step 5: Virtual Environment
- [ ] Virtual environment created
  ```bash
  cd c:\Users\bussu\MyPracticalsVScode\AI\Local_Agentic_File_Organizer_(LAFO)\
  python -m venv venv
  ```
- [ ] Virtual environment activated
  ```bash
  venv\Scripts\activate
  ```
- [ ] Pip upgraded (recommended)
  ```bash
  python -m pip install --upgrade pip
  ```

### Step 6: Dependencies Installation
- [ ] All dependencies installed successfully
  ```bash
  pip install -r requirements.txt
  ```
- [ ] Installation completed without errors
- [ ] No import errors on critical packages
  ```bash
  python -c "import langchain; import faiss; import watchdog; print('✅ All imports OK')"
  ```

---

## Configuration Checklist

### Step 7: Path Configuration
Edit `config.py`:

- [ ] `DOWNLOADS_DIR` is correct
  ```python
  # Usually: C:\Users\{username}\Downloads
  DOWNLOADS_DIR = Path(os.path.expanduser("~/Downloads"))
  ```

- [ ] `TARGET_ROOT` is correct and exists
  ```python
  # Update to your document organization folder
  TARGET_ROOT = Path(r"C:\Users\bussu\Documents\vamshi\SCANNED DOCUMENTS")
  ```

- [ ] `TESSERACT_PATH` is correct
  ```python
  TESSERACT_PATH = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
  ```

- [ ] `OLLAMA_API` is correct (localhost:11434)
  ```python
  OLLAMA_API = "http://localhost:11434/api/chat"
  ```

- [ ] `OLLAMA_MODEL` is available
  ```python
  OLLAMA_MODEL = "llama3:8b"  # Verify: ollama list
  ```

### Step 8: Directory Structure
- [ ] Target root folder exists
  ```bash
  ls "C:\Users\bussu\Documents\vamshi\SCANNED DOCUMENTS"
  ```

- [ ] At least one subfolder exists (e.g., "Medical Reports")
  
- [ ] Subdirectories are readable/writable
  ```bash
  # Try creating a test file in one subfolder
  # Should succeed
  ```

- [ ] No special characters in folder names
  - Avoid: `<>:"|?*\`
  - OK: Letters, numbers, spaces, hyphens, underscores

---

## Pre-Launch Verification

### Step 9: Component Testing

#### Test Vector Store
```bash
python -c "
from vector_store import VectorStoreManager
vs = VectorStoreManager()
vs.initialize_vectorstore()
print('✅ Vector store OK')
"
```
- [ ] Vector store initializes without error
- [ ] No missing directory warnings

#### Test Text Extractor
```bash
python -c "
from text_extractor import TextExtractor
# Should not raise ImportError
print('✅ Text extractor OK')
"
```
- [ ] Text extractor imports successfully

#### Test Ollama Connection
```bash
python -c "
from agent import RoutingAgent
agent = RoutingAgent()
if agent.check_ollama_connection():
    print('✅ Ollama connection OK')
else:
    print('❌ Ollama not responding')
"
```
- [ ] Ollama connection succeeds
- [ ] If fails: Run `ollama serve` in separate terminal

#### Test File Monitor
```bash
python -c "
from file_monitor import FileMonitor
# Should not raise ImportError
print('✅ File monitor OK')
"
```
- [ ] File monitor imports successfully

### Step 10: Dry Run
```bash
python -c "
from main import LAFOOrchestrator
orchestrator = LAFOOrchestrator()
if orchestrator.initialize():
    print('✅ Full initialization successful')
    orchestrator.print_statistics()
else:
    print('❌ Initialization failed')
"
```
- [ ] Initialization completes successfully
- [ ] All components load without errors
- [ ] No security/permission warnings

---

## Launch & Testing

### Step 11: Initial Launch
- [ ] Open two terminals in the project folder

**Terminal 1 - Start Ollama:**
```bash
ollama serve
# Should show: Listening on 127.0.0.1:11434
```
- [ ] Ollama is listening

**Terminal 2 - Activate environment and run LAFO:**
```bash
venv\Scripts\activate
python main.py
```
- [ ] LAFO initializes successfully
- [ ] Shows: "✅ LAFO Initialization Complete!"
- [ ] Shows: "🎯 LAFO is now running..."
- [ ] Ready to monitor Downloads folder

### Step 12: First File Test
- [ ] Download a test file to Downloads folder
  - Recommendation: Small PDF or image (< 5MB)
  
- [ ] Wait for LAFO to detect and process
  - Should take 10-20 seconds
  
- [ ] Check LAFO output in Terminal 2
  - Should show file being processed
  - Should show decision (moved/review)
  
- [ ] Check file location
  - Should be in target folder OR Unsorted_Review
  
- [ ] Check execution.log
  ```bash
  type execution.log
  ```
  - [ ] Entry for test file present
  - [ ] Status shows SUCCESS or appropriate flag

### Step 13: Multiple File Test
- [ ] Download 3-5 different file types
  - PDF, Image, DOCX, etc.
  
- [ ] Allow LAFO to process all
  - Each should take 10-30 seconds
  
- [ ] Monitor statistics
  - Check final stats in Terminal 2
  - Should show: Files Moved, Files Skipped, etc.
  
- [ ] Verify file organization
  - Check target folders for moved files
  - Check Unsorted_Review for low-confidence files

---

## Post-Deployment Configuration

### Step 14: Threshold Tuning
After processing 5-10 test files:

- [ ] Review Unsorted_Review folder
  - Should have 0-2 files (low-confidence)
  
- [ ] If too many manual reviews:
  ```python
  # In config.py, lower threshold:
  CONFIDENCE_THRESHOLD = 70  # was 75
  ```
  
- [ ] If too many misroutes:
  ```python
  # In config.py, raise threshold:
  CONFIDENCE_THRESHOLD = 80  # was 75
  ```
  
- [ ] Retest after adjustment

### Step 15: Folder Structure Optimization
- [ ] Review your folder names
  - Are they descriptive? (Good: "Medical Reports - Lab Tests")
  - Are they specific? (Good: "Invoices", Bad: "Documents")
  
- [ ] Consider adding keywords to folder structure
  - Example: "Bank Statements - Savings Account - Checking Account"
  
- [ ] Force vector store rebuild after changes
  ```bash
  # In main.py, set: force_rebuild=True
  # Then run: python main.py
  ```

### Step 16: System Prompt Customization (Optional)
- [ ] Review classification results
- [ ] If many misclassifications, update system prompt
  - See ADVANCED_CONFIG.md for examples
- [ ] Test changes with 5-10 files
- [ ] Keep prompt concise and specific

---

## Production Setup

### Step 17: Continuous Operation
- [ ] Test running for 1 hour
  - Monitor Terminal 2 for any errors
  - Check logs regularly

- [ ] Register LAFO as a silent startup background service using the helper script:
  - [ ] Open a PowerShell console.
  - [ ] Run the registration script:
    ```powershell
    Set-ExecutionPolicy Bypass -Scope Process
    .\register_startup.ps1
    ```
  - [ ] Confirm that the output reports success and that a shortcut `LAFO_Background_Organizer.lnk` is created in your Windows Startup directory.
  - [ ] The script automatically starts LAFO silently in the background.

- [ ] To stop and unregister the background service at any time:
  - [ ] Run the unregistration script in PowerShell:
    ```powershell
    .\unregister_startup.ps1
    ```
  - [ ] This stops the active background processes and removes the logon shortcut.


- [ ] Test reboot and auto-launch
  - [ ] Restart computer
  - [ ] Verify LAFO starts automatically
  - [ ] Download file to test

### Step 18: Monitoring Setup
- [ ] Set up daily log review
  - [ ] Check execution.log for errors
  - [ ] Monitor Unsorted_Review folder
  - [ ] Review statistics
  
- [ ] Create monthly maintenance schedule
  - [ ] Clear old logs (quarterly)
  - [ ] Archive organized files (yearly)
  - [ ] Update folder structure (as needed)

### Step 19: Backup & Recovery
- [ ] Backup LAFO project folder
  ```bash
  # Backup to external drive monthly
  ```
  
- [ ] Backup execution logs
  ```bash
  # Keep execution.log for audit trail
  ```
  
- [ ] Document custom configurations
  - [ ] Save custom system prompt (if modified)
  - [ ] Document folder structure
  - [ ] Save config.py changes

### Step 20: Documentation
- [ ] Create local documentation
  - [ ] Screenshot of folder structure
  - [ ] List of custom settings
  - [ ] Emergency contacts/notes
  
- [ ] Create troubleshooting guide for yourself
  - [ ] Common issues you encountered
  - [ ] Solutions that worked
  - [ ] Who to contact if stuck

---

## Verification Checklist (Run Weekly)

### Weekly Tasks
- [ ] Check execution.log for errors
  ```bash
  type execution.log | tail -20
  ```
  
- [ ] Review Unsorted_Review folder
  - [ ] Move correctly classified files
  - [ ] Delete duplicates
  
- [ ] Verify disk space
  ```bash
  # Check C: drive available space
  # Should be > 10GB free
  ```
  
- [ ] Test new file processing
  - [ ] Download test file
  - [ ] Verify it gets organized
  - [ ] Check execution.log entry

### Monthly Tasks
- [ ] Archive old logs
  ```bash
  # Keep last 3 months only
  ```
  
- [ ] Review statistics
  - [ ] Any unusual patterns?
  - [ ] High error rate?
  - [ ] Need threshold adjustment?
  
- [ ] Check folder structure
  - [ ] Any new folders to add?
  - [ ] Any folders to consolidate?
  - [ ] Rebuild vector store if changed

### Quarterly Tasks
- [ ] Backup system configuration
  - [ ] Save config.py
  - [ ] Save execution logs
  - [ ] Document any customizations
  
- [ ] Performance review
  - [ ] Average processing time per file
  - [ ] Success rate
  - [ ] Any bottlenecks?
  
- [ ] Update dependencies (optional)
  ```bash
  pip install --upgrade -r requirements.txt
  ```

---

## Troubleshooting Checklist

If LAFO doesn't start:

- [ ] Check Ollama is running
  ```bash
  # Should be running: ollama serve
  ```
  
- [ ] Check Python version
  ```bash
  python --version  # Must be 3.10+
  ```
  
- [ ] Check virtual environment
  ```bash
  # Should show (venv) in prompt
  venv\Scripts\activate
  ```
  
- [ ] Check dependencies
  ```bash
  pip install -r requirements.txt
  ```
  
- [ ] Check paths in config.py
  - [ ] DOWNLOADS_DIR exists
  - [ ] TARGET_ROOT exists
  - [ ] TESSERACT_PATH is correct
  
- [ ] Check logs
  ```bash
  type lafo_debug.log
  # Look for specific errors
  ```

If files aren't being processed:

- [ ] Check Downloads folder path
  ```bash
  # Verify: C:\Users\{username}\Downloads
  ```
  
- [ ] Check file extensions
  - [ ] File must be: .pdf, .jpg, .png, .docx, .html, .txt
  
- [ ] Check file isn't temporary
  - [ ] Not: .crdownload, .tmp, .part
  
- [ ] Check target folder structure
  ```bash
  ls "C:\Users\bussu\Documents\vamshi\SCANNED DOCUMENTS"
  # Should show subfolders
  ```
  
- [ ] Restart LAFO
  - [ ] Press Ctrl+C to stop
  - [ ] Run: python main.py again

If confidence scores are too low:

- [ ] Check folder names
  - [ ] Too generic? (Bad: "Documents", Good: "Medical Reports")
  - [ ] Rebuild vector store
  
- [ ] Lower confidence threshold (config.py)
  ```python
  CONFIDENCE_THRESHOLD = 70  # was 75
  ```
  
- [ ] Improve folder descriptions
  - [ ] Rename folders more specifically
  - [ ] Force vector store rebuild

---

## Success Criteria

### System is working correctly when:
- ✅ Ollama serves locally without errors
- ✅ Python imports all required packages
- ✅ Vector store initializes with folder categories
- ✅ LAFO starts and monitors Downloads
- ✅ Test files are detected within 5 seconds
- ✅ Files are processed and moved within 30 seconds
- ✅ Execution log shows SUCCESS entries
- ✅ Confidence scores are 70%+
- ✅ No permission errors when moving files
- ✅ Logs accumulate properly

### Ready for Production when:
- ✅ 10+ files processed successfully
- ✅ Manual review rate < 10%
- ✅ Error rate = 0%
- ✅ Windows silent background service startup works
- ✅ Folder structure handles expected file types
- ✅ Daily monitoring routine established
- ✅ Backup/recovery plan documented


---

## Final Checklist

- [ ] All prerequisites installed
- [ ] LAFO project fully configured
- [ ] Components tested individually
- [ ] Full dry run successful
- [ ] Multiple files tested successfully
- [ ] Thresholds tuned appropriately
- [ ] Auto-launch configured (optional)
- [ ] Monitoring schedule established
- [ ] Backup plan in place
- [ ] Team/family notified (if shared system)

---

**🎉 Congratulations! LAFO is now ready for production use.**

For ongoing support, see:
- README.md - Full documentation
- QUICKSTART.md - Quick reference
- ADVANCED_CONFIG.md - Advanced tuning
- ARCHITECTURE.md - Technical details

Monitor `execution.log` regularly and adjust as needed!
