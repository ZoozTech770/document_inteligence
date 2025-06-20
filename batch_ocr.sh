#!/bin/bash

# Batch OCR Processing Script
# Processes multiple PDF files from 'files' directory and outputs to Excel

set -e

# Check for help flag
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "Batch OCR Processor"
    echo "=================="
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -o, --output FILE     Output Excel file (default: ocr_results.xlsx)"
    echo "  --files-dir DIR       Directory containing files (default: files)"
    echo "  --limit NUMBER        Limit number of files to process (for testing)"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                              # Process all files"
    echo "  $0 --limit 50                   # Process only first 50 files (testing)"
    echo "  $0 -o test_results.xlsx --limit 10  # Test with 10 files, custom output"
    echo ""
    echo "Features:"
    echo "  ✅ Smart caching - reuses previous results to save API costs"
    echo "  ✅ File limit - test with smaller batches first"
    echo "  ✅ Cost tracking - shows API call savings"
    exit 0
fi

echo "Batch OCR Processor"
echo "=================="
echo "This script will process files from folders in the 'files' directory"
echo "and create an Excel file with all extracted table data."
echo "Supports: PDF, JPEG, PNG, HTML, DOCX, XLSX, and more"
echo ""

# Check if files directory exists
if [ ! -d "files" ]; then
    echo "Error: 'files' directory does not exist."
    echo "Please create the 'files' directory and add your files."
    echo ""
    echo "You can create it with: mkdir files"
    echo "Then copy your files to: ./files/"
    exit 1
fi

# Check if there are any supported files
if [ -z "$(find files -type f \( -name '*.pdf' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' -o -name '*.html' -o -name '*.docx' -o -name '*.xlsx' \))" ]; then
    echo "Error: No supported files found in 'files' directory."
    echo "Please add supported files to the 'files' directory."
    echo "Supported formats: PDF, JPEG, PNG, HTML, DOCX, XLSX, and more"
    exit 1
fi

# Run the batch processor
python3 batch_ocr_processor.py "$@"

echo ""
echo "Batch processing completed!"
echo "Check the Excel file for results."

