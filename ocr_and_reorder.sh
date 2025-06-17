#!/bin/bash

# Simple CLI wrapper for OCR + Column Reordering
# Usage: ./ocr_and_reorder.sh "your_file.pdf"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <pdf_file>"
    echo "Example: $0 'student_list.pdf'"
    echo ""
    echo "This script will:"
    echo "1. Run OCR on your PDF"
    echo "2. Extract tables as JSON"
    echo "3. Reorder columns: ID first, then names"
    exit 1
fi

PDF_FILE="$1"

if [ ! -f "$PDF_FILE" ]; then
    echo "Error: File '$PDF_FILE' not found!"
    exit 1
fi

echo "🚀 Starting OCR + Table Extraction..."
echo "📄 Processing: $PDF_FILE"
echo ""

# Step 1: Run OCR with JSON export
echo "Step 1: Running OCR..."
python3 sample_analyze_read.py "$PDF_FILE" --json

if [ $? -ne 0 ]; then
    echo "❌ OCR failed!"
    exit 1
fi

# Generate the expected table JSON filename
BASE_NAME=$(basename "$PDF_FILE" .pdf)
TABLE_JSON="${BASE_NAME}_tables.json"

echo ""
echo "Step 2: Reordering columns (ID first, then names)..."

if [ -f "$TABLE_JSON" ]; then
    # Use the clean extraction script with cleanup
    python3 extract_final_table.py "$TABLE_JSON" --cleanup
    
    if [ $? -eq 0 ]; then
        FINAL_FILE="${BASE_NAME}_final_table.json"
        
        echo ""
        echo "🧹 Cleaning up remaining temporary files..."
        
        # Clean up OCR results file
        OCR_FILE="${BASE_NAME}_ocr_results.txt"
        if [ -f "$OCR_FILE" ]; then
            echo "   🗑️  Removing: $OCR_FILE"
            rm "$OCR_FILE"
        fi
        
        echo ""
        echo "✨ All done! You now have only the final result:"
        echo "📄 $FINAL_FILE"
        echo ""
        echo "💡 This file contains your table with columns ordered as:"
        echo "   ID → First Name → Last Name → Others"
        echo ""
        echo "🔥 Clean workflow complete - PDF in, final JSON out, no mess!"
    else
        echo "❌ Final table extraction failed!"
        exit 1
    fi
else
    echo "⚠️  Table JSON file not found: $TABLE_JSON"
    echo "📋 Available files:"
    ls -la *json *txt 2>/dev/null || echo "No output files found"
fi

