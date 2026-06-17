import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_lafo_presentation():
    prs = Presentation()
    
    # Configure slide size to Widescreen (16:9)
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    blank_slide_layout = prs.slide_layouts[6]
    
    # Theme Color Constants
    COLOR_BG = RGBColor(11, 15, 25)          # Dark Blue-Black
    COLOR_CARD = RGBColor(22, 29, 48)       # Slightly lighter blue-gray
    COLOR_BORDER = RGBColor(40, 50, 75)     # Border color
    COLOR_TEXT_WHITE = RGBColor(241, 245, 249) # Main body text
    COLOR_TEXT_MUTED = RGBColor(148, 163, 184) # Secondary muted text
    COLOR_PRIMARY = RGBColor(56, 189, 248)    # Light blue accent
    COLOR_SECONDARY = RGBColor(192, 132, 252)  # Purple accent
    COLOR_ACCENT = RGBColor(34, 197, 94)      # Green success accent

    # Helper function to apply solid background to a slide
    def set_slide_background(slide):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = COLOR_BG

    # Helper function to add slide title
    def add_slide_title(slide, text):
        title_box = slide.shapes.add_textbox(Inches(0.75), Inches(0.5), Inches(11.83), Inches(0.8))
        tf = title_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_bottom = tf.margin_right = 0
        
        p = tf.paragraphs[0]
        p.text = text
        p.font.name = "Inter"
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = COLOR_PRIMARY
        return title_box

    # Helper function to format paragraphs
    def format_para(p, font_name="Inter", size=15, bold=False, color=COLOR_TEXT_WHITE, space_after=10):
        p.font.name = font_name
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = color
        p.space_after = Pt(space_after)

    # ----------------------------------------------------
    # SLIDE 1: Title / Cover Slide
    # ----------------------------------------------------
    slide_1 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide_1)
    
    # Large Decorative Glowing Banner Card
    banner = slide_1.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(1.5), Inches(1.8), Inches(10.33), Inches(3.8)
    )
    banner.fill.solid()
    banner.fill.fore_color.rgb = COLOR_CARD
    banner.line.color.rgb = COLOR_BORDER
    banner.line.width = Pt(1.5)
    
    # Title Text Box
    title_box = slide_1.shapes.add_textbox(Inches(2.0), Inches(2.1), Inches(9.33), Inches(2.2))
    tf = title_box.text_frame
    tf.word_wrap = True
    
    p_badge = tf.paragraphs[0]
    p_badge.text = "100% PRIVATE & OFFLINE INTELLIGENCE"
    format_para(p_badge, "Inter", 12, True, COLOR_SECONDARY, 8)
    
    p_title = tf.add_paragraph()
    p_title.text = "LAFO"
    format_para(p_title, "Inter", 54, True, COLOR_PRIMARY, 4)
    
    p_sub = tf.add_paragraph()
    p_sub.text = "Local Agentic File Organizer"
    format_para(p_sub, "Inter", 24, True, COLOR_TEXT_WHITE, 14)
    
    p_desc = tf.add_paragraph()
    p_desc.text = "Automatically monitors, extracts content, classifies, renames, and moves files using local LLMs & Vector DBs."
    format_para(p_desc, "Inter", 14, False, COLOR_TEXT_MUTED, 0)
    
    # Bottom labels on Cover Slide
    labels_box = slide_1.shapes.add_textbox(Inches(2.0), Inches(4.7), Inches(9.33), Inches(0.6))
    tf_lbls = labels_box.text_frame
    p_lbl = tf_lbls.paragraphs[0]
    p_lbl.text = "🛡️ Zero Cloud Leakage    |    🧠 FAISS Pre-Filtering    |    🤖 local Llama 3 (Ollama)"
    format_para(p_lbl, "Consolas", 12, False, COLOR_ACCENT, 0)

    # ----------------------------------------------------
    # SLIDE 2: The Core Problem
    # ----------------------------------------------------
    slide_2 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide_2)
    add_slide_title(slide_2, "The Core Ingestion Problem")
    
    # Left Content Column
    left_col = slide_2.shapes.add_textbox(Inches(0.75), Inches(1.6), Inches(7.0), Inches(5.0))
    tf_left = left_col.text_frame
    tf_left.word_wrap = True
    
    p_intro = tf_left.paragraphs[0]
    p_intro.text = "Manual file organization is a critical, time-consuming drag:"
    format_para(p_intro, "Inter", 18, False, COLOR_TEXT_WHITE, 16)
    
    p1 = tf_left.add_paragraph()
    p1.text = "• Unstructured Downloads Folder"
    format_para(p1, "Inter", 16, True, COLOR_SECONDARY, 4)
    p1_sub = tf_left.add_paragraph()
    p1_sub.text = "  Browser downloads clog up your directories with invoices, tax forms, reports, and bills mixed together."
    format_para(p1_sub, "Inter", 14, False, COLOR_TEXT_MUTED, 14)
    
    p2 = tf_left.add_paragraph()
    p2.text = "• Cloud Data Exposure / Privacy Leakage"
    format_para(p2, "Inter", 16, True, COLOR_SECONDARY, 4)
    p2_sub = tf_left.add_paragraph()
    p2_sub.text = "  Uploading sensitive papers (pension letters, bank statements, asset documents) to online AI platforms leaks personal metadata."
    format_para(p2_sub, "Inter", 14, False, COLOR_TEXT_MUTED, 14)
    
    p3 = tf_left.add_paragraph()
    p3.text = "• Model Timeout on Heavy Taxonomies"
    format_para(p3, "Inter", 16, True, COLOR_SECONDARY, 4)
    p3_sub = tf_left.add_paragraph()
    p3_sub.text = "  Passing large folder structures (e.g. 302 categories) directly to a local CPU-based LLM causes severe latency and prompt timeout crashes."
    format_para(p3_sub, "Inter", 14, False, COLOR_TEXT_MUTED, 0)

    # Right Column Visual Box
    right_card = slide_2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.3), Inches(1.8), Inches(4.28), Inches(4.5))
    right_card.fill.solid()
    right_card.fill.fore_color.rgb = COLOR_CARD
    right_card.line.color.rgb = COLOR_BORDER
    
    rc_box = slide_2.shapes.add_textbox(Inches(8.5), Inches(2.2), Inches(3.88), Inches(3.8))
    tf_rc = rc_box.text_frame
    tf_rc.word_wrap = True
    
    prc_title = tf_rc.paragraphs[0]
    prc_title.text = "CRITICAL METRIC"
    format_para(prc_title, "Inter", 12, True, COLOR_SECONDARY, 14)
    
    prc_num = tf_rc.add_paragraph()
    prc_num.text = "302"
    format_para(prc_num, "Inter", 48, True, COLOR_PRIMARY, 4)
    
    prc_lbl = tf_rc.add_paragraph()
    prc_lbl.text = "Destination Folders"
    format_para(prc_lbl, "Inter", 16, True, COLOR_TEXT_WHITE, 14)
    
    prc_desc = tf_rc.add_paragraph()
    prc_desc.text = "Passing this massive list of folders directly to Ollama creates a context of >20,000 characters, leading to massive memory bloat and CPU processing timeouts."
    format_para(prc_desc, "Inter", 13, False, COLOR_TEXT_MUTED, 0)

    # ----------------------------------------------------
    # SLIDE 3: The LAFO Solution
    # ----------------------------------------------------
    slide_3 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide_3)
    add_slide_title(slide_3, "The Privacy-First Solution")
    
    # Left Content Column
    left_col = slide_3.shapes.add_textbox(Inches(0.75), Inches(1.6), Inches(7.0), Inches(5.0))
    tf_left = left_col.text_frame
    tf_left.word_wrap = True
    
    p_sol_intro = tf_left.paragraphs[0]
    p_sol_intro.text = "LAFO operates as a secure, local background daemon:"
    format_para(p_sol_intro, "Inter", 18, False, COLOR_TEXT_WHITE, 16)
    
    p_sol1 = tf_left.add_paragraph()
    p_sol1.text = "✓ 100% Offline Processing"
    format_para(p_sol1, "Inter", 16, True, COLOR_ACCENT, 4)
    p_sol1_sub = tf_left.add_paragraph()
    p_sol1_sub.text = "  All operations—from PDF extraction and vector searches to LLM routing—happen offline on localhost. No external telemetry."
    format_para(p_sol1_sub, "Inter", 14, False, COLOR_TEXT_MUTED, 14)
    
    p_sol2 = tf_left.add_paragraph()
    p_sol2.text = "✓ Autonomous Watchdog Observer"
    format_para(p_sol2, "Inter", 16, True, COLOR_ACCENT, 4)
    p_sol2_sub = tf_left.add_paragraph()
    p_sol2_sub.text = "  Runs quietly in the system tray, scanning for file creations or browser rename events, queuing tasks to concurrent worker threads."
    format_para(p_sol2_sub, "Inter", 14, False, COLOR_TEXT_MUTED, 14)
    
    p_sol3 = tf_left.add_paragraph()
    p_sol3.text = "✓ Smart Operations & Deduplication"
    format_para(p_sol3, "Inter", 16, True, COLOR_ACCENT, 4)
    p_sol3_sub = tf_left.add_paragraph()
    p_sol3_sub.text = "  Auto-renames files semantically based on text content and extracted dates. Pre-checks SHA-256 hashes to filter out redundant file moves."
    format_para(p_sol3_sub, "Inter", 14, False, COLOR_TEXT_MUTED, 0)

    # Right Column Visual Box
    right_card = slide_3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.3), Inches(1.8), Inches(4.28), Inches(4.5))
    right_card.fill.solid()
    right_card.fill.fore_color.rgb = COLOR_CARD
    right_card.line.color.rgb = COLOR_BORDER
    
    rc_box = slide_3.shapes.add_textbox(Inches(8.5), Inches(2.2), Inches(3.88), Inches(3.8))
    tf_rc = rc_box.text_frame
    tf_rc.word_wrap = True
    
    prc_title = tf_rc.paragraphs[0]
    prc_title.text = "SECURITY AUDIT"
    format_para(prc_title, "Inter", 12, True, COLOR_ACCENT, 14)
    
    prc_status = tf_rc.add_paragraph()
    prc_status.text = "SECURE"
    format_para(prc_status, "Inter", 42, True, COLOR_ACCENT, 4)
    
    prc_lbl = tf_rc.add_paragraph()
    prc_lbl.text = "Local Sandboxed Runs"
    format_para(prc_lbl, "Inter", 16, True, COLOR_TEXT_WHITE, 14)
    
    prc_desc = tf_rc.add_paragraph()
    prc_desc.text = "• Path names remain local\n• Document strings never uploaded\n• Logs cached locally in user folder\n• Full compliance with offline environments"
    format_para(prc_desc, "Consolas", 12, False, COLOR_TEXT_MUTED, 0)

    # ----------------------------------------------------
    # SLIDE 4: Data Flow Architecture
    # ----------------------------------------------------
    slide_4 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide_4)
    add_slide_title(slide_4, "Data Flow Architecture")
    
    # Left Content Column
    left_col = slide_4.shapes.add_textbox(Inches(0.75), Inches(1.6), Inches(6.0), Inches(5.0))
    tf_left = left_col.text_frame
    tf_left.word_wrap = True
    
    p_arch_desc = tf_left.paragraphs[0]
    p_arch_desc.text = "LAFO manages ingestion through 5 sequential phases:"
    format_para(p_arch_desc, "Inter", 18, False, COLOR_TEXT_WHITE, 16)
    
    p_ph1 = tf_left.add_paragraph()
    p_ph1.text = "1. File Stability Verification:"
    format_para(p_ph1, "Inter", 15, True, COLOR_PRIMARY, 2)
    p_ph1_sub = tf_left.add_paragraph()
    p_ph1_sub.text = "   Watchdog catches files and waits for write operations to lock/complete."
    format_para(p_ph1_sub, "Inter", 13, False, COLOR_TEXT_MUTED, 8)
    
    p_ph2 = tf_left.add_paragraph()
    p_ph2.text = "2. FAISS Vector Search Pre-Filtering:"
    format_para(p_ph2, "Inter", 15, True, COLOR_PRIMARY, 2)
    p_ph2_sub = tf_left.add_paragraph()
    p_ph2_sub.text = "   Matches file text against indexed directory names & file exemplars."
    format_para(p_ph2_sub, "Inter", 13, False, COLOR_TEXT_MUTED, 8)
    
    p_ph3 = tf_left.add_paragraph()
    p_ph3.text = "3. Candidate Narrowing:"
    format_para(p_ph3, "Inter", 15, True, COLOR_PRIMARY, 2)
    p_ph3_sub = tf_left.add_paragraph()
    p_ph3_sub.text = "   Reduces the 302 categories down to the top 3-5 candidates for the LLM."
    format_para(p_ph3_sub, "Inter", 13, False, COLOR_TEXT_MUTED, 8)
    
    p_ph4 = tf_left.add_paragraph()
    p_ph4.text = "4. Native JSON Model & Retry Loops:"
    format_para(p_ph4, "Inter", 15, True, COLOR_PRIMARY, 2)
    p_ph4_sub = tf_left.add_paragraph()
    p_ph4_sub.text = "   Ollama processes candidate subset in JSON format; retries up to 3 times on parsing error."
    format_para(p_ph4_sub, "Inter", 13, False, COLOR_TEXT_MUTED, 8)
    
    p_ph5 = tf_left.add_paragraph()
    p_ph5.text = "5. Double-Check and Atomic Move:"
    format_para(p_ph5, "Inter", 15, True, COLOR_PRIMARY, 2)
    p_ph5_sub = tf_left.add_paragraph()
    p_ph5_sub.text = "   Verifies duplicate hash, renames semantically, and moves atomically."
    format_para(p_ph5_sub, "Inter", 13, False, COLOR_TEXT_MUTED, 0)

    # Right Column Diagram Drawing
    # We will build visual text representation box
    flow_box = slide_4.shapes.add_textbox(Inches(7.2), Inches(1.5), Inches(5.38), Inches(5.2))
    tf_flow = flow_box.text_frame
    tf_flow.word_wrap = True
    
    p_lbl = tf_flow.paragraphs[0]
    p_lbl.text = "PIPELINES VISUALIZER"
    format_para(p_lbl, "Consolas", 12, True, COLOR_SECONDARY, 14)
    
    def draw_diagram_node(text_val, is_active=False):
        p_node = tf_flow.add_paragraph()
        p_node.text = f"   [ {text_val} ]"
        p_node.alignment = PP_ALIGN.LEFT
        color_node = COLOR_ACCENT if is_active else COLOR_PRIMARY
        format_para(p_node, "Consolas", 14, True, color_node, 4)
        
        p_arrow = tf_flow.add_paragraph()
        p_arrow.text = "            ↓"
        p_arrow.alignment = PP_ALIGN.LEFT
        format_para(p_arrow, "Consolas", 12, False, COLOR_TEXT_MUTED, 4)

    draw_diagram_node("WATCHDOG STABILITY CHECK")
    draw_diagram_node("FAISS TAXONOMY PRE-FILTER")
    draw_diagram_node("LLM ROUTING (NATIVE JSON MODE)")
    
    p_last = tf_flow.add_paragraph()
    p_last.text = "   [ ATOMIC MOVE & LOGGING ]"
    format_para(p_last, "Consolas", 14, True, COLOR_SECONDARY, 0)

    # ----------------------------------------------------
    # SLIDE 5: Version 1.3 Key Features
    # ----------------------------------------------------
    slide_5 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide_5)
    add_slide_title(slide_5, "New in Version 1.3")
    
    # 4 Cards Grid representation
    # Top-Left Card
    tl_card = slide_5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.75), Inches(1.6), Inches(5.6), Inches(2.3))
    tl_card.fill.solid()
    tl_card.fill.fore_color.rgb = COLOR_CARD
    tl_card.line.color.rgb = COLOR_BORDER
    
    tl_box = slide_5.shapes.add_textbox(Inches(0.95), Inches(1.8), Inches(5.2), Inches(1.9))
    tf_tl = tl_box.text_frame
    tf_tl.word_wrap = True
    p_tl = tf_tl.paragraphs[0]
    p_tl.text = "1. Single-Instance Execution Lock"
    format_para(p_tl, "Inter", 16, True, COLOR_PRIMARY, 6)
    p_tl_desc = tf_tl.add_paragraph()
    p_tl_desc.text = "Uses Windows msvcrt.locking on lafo.lock to prevent multiple orchestrator instances from running simultaneously, blocking duplicate file-move operations."
    format_para(p_tl_desc, "Inter", 13, False, COLOR_TEXT_MUTED, 0)
    
    # Top-Right Card
    tr_card = slide_5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.98), Inches(1.6), Inches(5.6), Inches(2.3))
    tr_card.fill.solid()
    tr_card.fill.fore_color.rgb = COLOR_CARD
    tr_card.line.color.rgb = COLOR_BORDER
    
    tr_box = slide_5.shapes.add_textbox(Inches(7.18), Inches(1.8), Inches(5.2), Inches(1.9))
    tf_tr = tr_box.text_frame
    tf_tr.word_wrap = True
    p_tr = tf_tr.paragraphs[0]
    p_tr.text = "2. Vector Candidate Pre-Filtering"
    format_para(p_tr, "Inter", 16, True, COLOR_PRIMARY, 6)
    p_tr_desc = tf_tr.add_paragraph()
    p_tr_desc.text = "Narrow down categories from 302 to top 3-5 candidates via local similarity search before prompting the LLM, reducing CPU context by 20x and stopping timeouts."
    format_para(p_tr_desc, "Inter", 13, False, COLOR_TEXT_MUTED, 0)
    
    # Bottom-Left Card
    bl_card = slide_5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.75), Inches(4.3), Inches(5.6), Inches(2.3))
    bl_card.fill.solid()
    bl_card.fill.fore_color.rgb = COLOR_CARD
    bl_card.line.color.rgb = COLOR_BORDER
    
    bl_box = slide_5.shapes.add_textbox(Inches(0.95), Inches(4.5), Inches(5.2), Inches(1.9))
    tf_bl = bl_box.text_frame
    tf_bl.word_wrap = True
    p_bl = tf_bl.paragraphs[0]
    p_bl.text = "3. Exemplar-Based File Indexing"
    format_para(p_bl, "Inter", 16, True, COLOR_PRIMARY, 6)
    p_bl_desc = tf_bl.add_paragraph()
    p_bl_desc.text = "Indexes the first 15 files in target folders as semantic 'exemplars' inside the FAISS database. Learns your established naming and sorting patterns dynamically."
    format_para(p_bl_desc, "Inter", 13, False, COLOR_TEXT_MUTED, 0)
    
    # Bottom-Right Card
    br_card = slide_5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.98), Inches(4.3), Inches(5.6), Inches(2.3))
    br_card.fill.solid()
    br_card.fill.fore_color.rgb = COLOR_CARD
    br_card.line.color.rgb = COLOR_BORDER
    
    br_box = slide_5.shapes.add_textbox(Inches(7.18), Inches(4.5), Inches(5.2), Inches(1.9))
    tf_br = br_box.text_frame
    tf_br.word_wrap = True
    p_br = tf_br.paragraphs[0]
    p_br.text = "4. Failure Quarantining"
    format_para(p_br, "Inter", 16, True, COLOR_PRIMARY, 6)
    p_br_desc = tf_br.add_paragraph()
    p_br_desc.text = "Documents failing classification after 3 retry loops are quarantined and routed to Unsorted_Review folder instead of clogging the monitored Downloads directory."
    format_para(p_br_desc, "Inter", 13, False, COLOR_TEXT_MUTED, 0)

    # ----------------------------------------------------
    # SLIDE 6: Concurrency & GPU
    # ----------------------------------------------------
    slide_6 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide_6)
    add_slide_title(slide_6, "Concurrency & GPU Optimizations")
    
    # Left Content Column
    left_col = slide_6.shapes.add_textbox(Inches(0.75), Inches(1.6), Inches(6.0), Inches(5.0))
    tf_left = left_col.text_frame
    tf_left.word_wrap = True
    
    p_opt_intro = tf_left.paragraphs[0]
    p_opt_intro.text = "LAFO leverages multithreading for maximum responsiveness:"
    format_para(p_opt_intro, "Inter", 18, False, COLOR_TEXT_WHITE, 16)
    
    p_opt1 = tf_left.add_paragraph()
    p_opt1.text = "• ThreadPoolExecutor Workers"
    format_para(p_opt1, "Inter", 16, True, COLOR_SECONDARY, 4)
    p_opt1_sub = tf_left.add_paragraph()
    p_opt1_sub.text = "  Dispatches file tasks to a background thread pool (default 4 workers) so browser download transactions are never blocked."
    format_para(p_opt1_sub, "Inter", 14, False, COLOR_TEXT_MUTED, 14)
    
    p_opt2 = tf_left.add_paragraph()
    p_opt2.text = "• Concurrency Locks"
    format_para(p_opt2, "Inter", 16, True, COLOR_SECONDARY, 4)
    p_opt2_sub = tf_left.add_paragraph()
    p_opt2_sub.text = "  Protects stats updates, log entries, and filesystem transactions using mutex locks (`stats_lock`, `file_op_lock`) to prevent race condition write errors."
    format_para(p_opt2_sub, "Inter", 14, False, COLOR_TEXT_MUTED, 14)
    
    p_opt3 = tf_left.add_paragraph()
    p_opt3.text = "• CUDA Hardware Acceleration"
    format_para(p_opt3, "Inter", 16, True, COLOR_SECONDARY, 4)
    p_opt3_sub = tf_left.add_paragraph()
    p_opt3_sub.text = "  Automatically checks for PyTorch GPU/CUDA drivers. Runs embedding calculations locally on hardware when available, falling back safely to CPU."
    format_para(p_opt3_sub, "Inter", 14, False, COLOR_TEXT_MUTED, 0)

    # Right Column Code Visual
    right_card = slide_6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.2), Inches(1.8), Inches(5.38), Inches(4.5))
    right_card.fill.solid()
    right_card.fill.fore_color.rgb = COLOR_CARD
    right_card.line.color.rgb = COLOR_BORDER
    
    code_box = slide_6.shapes.add_textbox(Inches(7.35), Inches(2.0), Inches(5.08), Inches(4.1))
    tf_code = code_box.text_frame
    tf_code.word_wrap = True
    
    p_code_hdr = tf_code.paragraphs[0]
    p_code_hdr.text = "THREAD SAFE OPERATIONS (main.py)"
    format_para(p_code_hdr, "Consolas", 12, True, COLOR_PRIMARY, 10)
    
    p_c1 = tf_code.add_paragraph()
    p_c1.text = "def process_file(self, file_path):\n    # ... extract text\n    # ... pre-filter candidates\n    # ... classify\n    with self.file_op_lock:\n        # Verify duplicate SHA-256 hash\n        # Move file atomically\n        # Log SUCCESS to execution.log"
    format_para(p_c1, "Consolas", 11.5, False, COLOR_TEXT_WHITE, 16)
    
    p_code_lbl = tf_code.add_paragraph()
    p_code_lbl.text = "CUDA DEVICE DETECT (vector_store.py)"
    format_para(p_code_lbl, "Consolas", 12, True, COLOR_SECONDARY, 10)
    
    p_c2 = tf_code.add_paragraph()
    p_c2.text = "device = 'cuda' if torch.cuda.is_available() \\\n         else 'cpu'\nself.embeddings = HuggingFaceEmbeddings(\n    model_name=EMBEDDING_MODEL,\n    model_kwargs={'device': device}\n)"
    format_para(p_c2, "Consolas", 11.5, False, COLOR_TEXT_WHITE, 0)

    # ----------------------------------------------------
    # SLIDE 7: Startup Service Automation
    # ----------------------------------------------------
    slide_7 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide_7)
    add_slide_title(slide_7, "Windows Startup Integration")
    
    # Left Content Column
    left_col = slide_7.shapes.add_textbox(Inches(0.75), Inches(1.6), Inches(6.0), Inches(5.0))
    tf_left = left_col.text_frame
    tf_left.word_wrap = True
    
    p_srv_intro = tf_left.paragraphs[0]
    p_srv_intro.text = "Automated PowerShell installers manage continuous service runs:"
    format_para(p_srv_intro, "Inter", 18, False, COLOR_TEXT_WHITE, 16)
    
    p_srv1 = tf_left.add_paragraph()
    p_srv1.text = "• register_startup.ps1"
    format_para(p_srv1, "Inter", 16, True, COLOR_PRIMARY, 4)
    p_srv1_sub = tf_left.add_paragraph()
    p_srv1_sub.text = "  Creates a logon shortcut in the Windows Startup directory that runs powershell.exe with a hidden window, executing main.py silently in the background."
    format_para(p_srv1_sub, "Inter", 14, False, COLOR_TEXT_MUTED, 14)
    
    p_srv2 = tf_left.add_paragraph()
    p_srv2.text = "• unregister_startup.ps1"
    format_para(p_srv2, "Inter", 16, True, COLOR_PRIMARY, 4)
    p_srv2_sub = tf_left.add_paragraph()
    p_srv2_sub.text = "  Instantly searches for running background python.exe processes executing main.py, terminates them, and deletes the Startup folder shortcut."
    format_para(p_srv2_sub, "Inter", 14, False, COLOR_TEXT_MUTED, 14)
    
    p_srv3 = tf_left.add_paragraph()
    p_srv3.text = "• Dynamic Logs Folder"
    format_para(p_srv3, "Inter", 16, True, COLOR_PRIMARY, 4)
    p_srv3_sub = tf_left.add_paragraph()
    p_srv3_sub.text = "  Creates logs and execution logs in C:\\Users\\...\\Documents\\LAFO logs, ensuring zero-pollution in project structures."
    format_para(p_srv3_sub, "Inter", 14, False, COLOR_TEXT_MUTED, 0)

    # Right Column Powershell Console Visual
    right_card = slide_7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.2), Inches(1.8), Inches(5.38), Inches(4.5))
    right_card.fill.solid()
    right_card.fill.fore_color.rgb = COLOR_CARD
    right_card.line.color.rgb = COLOR_BORDER
    
    ps_box = slide_7.shapes.add_textbox(Inches(7.35), Inches(2.2), Inches(5.08), Inches(3.8))
    tf_ps = ps_box.text_frame
    tf_ps.word_wrap = True
    
    pps_hdr = tf_ps.paragraphs[0]
    pps_hdr.text = "POWERSHELL SERVICE DEPLOYMENT"
    format_para(pps_hdr, "Consolas", 12, True, COLOR_ACCENT, 14)
    
    pps_c1 = tf_ps.add_paragraph()
    pps_c1.text = "# 1. Set Execution Policy\nSet-ExecutionPolicy Bypass -Scope Process\n\n# 2. Run background registration\n.\\register_startup.ps1\n\n# 3. Check background status\nGet-CimInstance Win32_Process -Filter \\\n'Name=\"python.exe\" and CommandLine like \"%main.py%\"'"
    format_para(pps_c1, "Consolas", 12, False, COLOR_TEXT_WHITE, 0)

    # ----------------------------------------------------
    # SLIDE 8: Project Metrics & Conclusion
    # ----------------------------------------------------
    slide_8 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(slide_8)
    
    # Large Cover-like final slide
    banner = slide_8.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(1.5), Inches(1.8), Inches(10.33), Inches(3.8)
    )
    banner.fill.solid()
    banner.fill.fore_color.rgb = COLOR_CARD
    banner.line.color.rgb = COLOR_BORDER
    banner.line.width = Pt(1.5)
    
    # Text Box
    conclusion_box = slide_8.shapes.add_textbox(Inches(2.0), Inches(2.1), Inches(9.33), Inches(3.2))
    tf_con = conclusion_box.text_frame
    tf_con.word_wrap = True
    
    p_con_badge = tf_con.paragraphs[0]
    p_con_badge.text = "VERSION 1.3 RELESE-READY"
    format_para(p_con_badge, "Inter", 12, True, COLOR_ACCENT, 8)
    
    p_con_title = tf_con.add_paragraph()
    p_con_title.text = "LAFO Project Metrics"
    format_para(p_con_title, "Inter", 42, True, COLOR_PRIMARY, 16)
    
    p_stats = tf_con.add_paragraph()
    p_stats.text = "• 2,575 Lines of Core Code    |    • 2,200+ Lines of Technical Docs\n• 40+ Features Completed      |    • <15s Processing Speed / File\n• 100% Local Privacy          |    • Windows Service Enabled"
    format_para(p_stats, "Consolas", 14, True, COLOR_TEXT_WHITE, 20)
    
    p_end = tf_con.add_paragraph()
    p_end.text = "Fully production-ready for automated, secure, and offline file organization."
    format_para(p_end, "Inter", 14, False, COLOR_TEXT_MUTED, 0)

    # Save presentation
    output_path = Path("LAFO.pptx")
    prs.save(output_path)
    print(f"SUCCESS: Presentation saved to {output_path.absolute()}")

if __name__ == "__main__":
    create_lafo_presentation()
