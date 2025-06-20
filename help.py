#!/usr/bin/env python3
"""
HELP GUIDE - How to use the OCR CLI tools
"""

print("""
🔥 OCR + TABLE EXTRACTION CLI GUIDE 🔥

🚀 NEW! BATCH PROCESSING (RECOMMENDED FOR MULTIPLE FILES):
   ./batch_ocr.sh
   
   ✨ Features:
   • Process multiple PDF files from 'files' directory
   • Interactive file selection (choose which files to process)
   • Automatic Excel output with all results combined
   • Source filename as first column in Excel
   • Supports subdirectories
   
   📂 Setup:
   1. mkdir files
   2. Copy PDF files to ./files/
   3. Run: ./batch_ocr.sh
   4. Select files when prompted
   5. Get: ocr_results.xlsx
   
   🎛️ Options:
   ./batch_ocr.sh -o custom_name.xlsx     # Custom output filename
   ./batch_ocr.sh --files-dir other_dir   # Use different directory

🎆 SINGLE FILE PROCESSING: All-in-one with cleanup
   ./ocr_and_reorder.sh "your_file.pdf"
   
   ✨ Result: ONLY the final reordered table file - no temp files!
   ✅ Runs OCR → Extracts tables → Reorders columns → Cleans up

📋 MANUAL CONTROL (Single file):
   
   Step 1 - OCR + JSON Export:
   python3 sample_analyze_read.py "your_file.pdf" --json
   
   Step 2 - Extract final table with cleanup:
   python3 extract_final_table.py "your_file_tables.json" --cleanup

🎯 OUTPUT FILES:
   • Batch: ocr_results.xlsx - Excel with all data + source filenames
   • Single: filename_final_table.json - Reordered table (ID first!)
   • All temp files automatically cleaned up 🧹

💡 EXAMPLES:
   
   # Batch processing (NEW!)
   mkdir files
   cp *.pdf files/
   ./batch_ocr.sh
   
   # Single file processing
   ./ocr_and_reorder.sh "student_list.pdf"
   
   # Manual with cleanup
   python3 sample_analyze_read.py "document.pdf" --json
   python3 extract_final_table.py "document_tables.json" --cleanup
   
   # Hebrew files work perfectly
   ./batch_ocr.sh  # processes Hebrew PDFs in files/ directory

🔧 COLUMN REORDERING:
   
   Original:  ["שם פרטי", "שם משפחה", "תז"]
   Final:     ["תז", "שם פרטי", "שם משפחה"]
   
   🎯 Perfect: ID → First Name → Last Name → Others

✨ WORKFLOWS:
   • BATCH: PDFs in files/ → Select → Excel out
   • SINGLE: PDF in → Final JSON out → No mess!

❓ NEED HELP? Run: python3 help.py
""")

