#!/usr/bin/env python3
"""
HELP GUIDE - How to use the OCR CLI tools
"""

print("""
🔥 OCR + TABLE EXTRACTION CLI GUIDE 🔥

🎆 CLEANEST OPTION (RECOMMENDED): All-in-one with cleanup
   ./ocr_and_reorder.sh "your_file.pdf"
   
   ✨ Result: ONLY the final reordered table file - no temp files!
   ✅ Runs OCR → Extracts tables → Reorders columns → Cleans up

📋 OPTION 2: Manual control
   
   Step 1 - OCR + JSON Export:
   python3 sample_analyze_read.py "your_file.pdf" --json
   
   Step 2 - Extract final table with cleanup:
   python3 extract_final_table.py "your_file_tables.json" --cleanup

📋 OPTION 3: Keep intermediate files
   
   Step 1: python3 sample_analyze_read.py "your_file.pdf" --json
   Step 2: python3 extract_final_table.py "your_file_tables.json"
   (No --cleanup flag = keeps all files)

🎯 FINAL OUTPUT:
   • filename_final_table.json - Your reordered table (ID first!)
   • All temp files automatically cleaned up 🧹

💡 EXAMPLES:
   
   # Clean processing (recommended)
   ./ocr_and_reorder.sh "student_list.pdf"
   
   # Manual with cleanup
   python3 sample_analyze_read.py "document.pdf" --json
   python3 extract_final_table.py "document_tables.json" --cleanup
   
   # Hebrew files work perfectly
   ./ocr_and_reorder.sh "השומר_החדש.pdf"

🔧 COLUMN REORDERING:
   
   Original:  ["שם פרטי", "שם משפחה", "תז"]
   Final:     ["תז", "שם פרטי", "שם משפחה"]
   
   🎯 Perfect: ID → First Name → Last Name → Others

✨ CLEAN WORKFLOW = PDF in → Final JSON out → No mess!

❓ NEED HELP? Run: python3 help.py
""")

