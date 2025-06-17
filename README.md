# Document Intelligence OCR System

🔥 **Advanced OCR + Table Extraction with Custom Column Ordering**

A powerful CLI tool for extracting and processing tables from PDF documents using Azure Document Intelligence. Automatically reorders columns to put ID first, then names, with intelligent Hebrew and English text support.

## ✨ Features

- 🚀 **One-command processing**: PDF in → Clean JSON out
- 📊 **Smart table extraction** with Azure Document Intelligence
- 🔄 **Automatic column reordering**: ID → First Name → Last Name → Others
- 🌍 **Multilingual support**: Hebrew and English text recognition
- 🧹 **Auto cleanup**: No temporary files left behind
- 📱 **Simple CLI**: Easy to use command-line interface

## 🚀 Quick Start

### All-in-One Processing (Recommended)
```bash
# Process any PDF document
./ocr_and_reorder.sh "your_document.pdf"

# Result: document_final_table.json with perfect column order
```

### Manual Step-by-Step
```bash
# Step 1: OCR + Table extraction
python3 sample_analyze_read.py "document.pdf" --json

# Step 2: Reorder columns and cleanup
python3 extract_final_table.py "document_tables.json" --cleanup
```

### Get Help
```bash
python3 help.py
```

## 📋 Output Format

The system produces clean JSON with reordered columns:

```json
[
  {
    "table_index": 0,
    "row_count": 52,
    "column_count": 3,
    "rows": [
      ["תז", "שם פרטי", "שם משפחה"],
      ["519499492", "Rachel", "Adar"],
      ["A22465947", "Olivia", "Ansel"]
    ],
    "metadata": {
      "column_order": "ID → First Name → Last Name → Others"
    }
  }
]
```

## 🔧 Requirements

- Python 3.7+
- Azure Document Intelligence credentials
- Required packages: `azure-ai-documentintelligence`, `numpy`

## ⚙️ Setup

1. **Install dependencies:**
   ```bash
   pip3 install azure-ai-documentintelligence numpy
   ```

2. **Configure Azure credentials** in `sample_analyze_read.py`:
   ```python
   endpoint = "your-azure-endpoint"
   key = "your-azure-key"
   ```

3. **Make scripts executable:**
   ```bash
   chmod +x ocr_and_reorder.sh
   ```

## 📁 Project Structure

```
document_inteligence/
├── sample_analyze_read.py    # Main OCR engine
├── extract_final_table.py    # Table extraction & reordering
├── ocr_and_reorder.sh       # All-in-one CLI script
├── help.py                  # Help guide
└── README.md               # This file
```

## 🎯 Use Cases

- **Student rosters** with ID, name columns
- **Employee databases** requiring specific column order
- **Multi-language documents** (Hebrew/English)
- **Form processing** with structured data
- **Any tabular PDF data** needing custom organization

## 🔄 Column Detection

The system automatically detects and reorders:

- **ID columns**: `תז`, `ID`, `identifier`
- **First names**: `שם פרטי`, `first name`, `given name`
- **Last names**: `שם משפחה`, `last name`, `surname`
- **Other columns**: Preserved in original order after core columns

## 🌟 Why This Tool?

- ✅ **Clean workflow**: No manual column reordering needed
- ✅ **Production ready**: Handles real-world documents
- ✅ **Language agnostic**: Works with any language Azure supports
- ✅ **Zero config**: Smart defaults for common use cases
- ✅ **No mess**: Automatic cleanup of temporary files

## 📝 License

MIT License - feel free to use and modify as needed.

## 🤝 Contributing

Contributions welcome! Feel free to submit issues and pull requests.

---

**Made with ❤️ for clean, efficient document processing**

