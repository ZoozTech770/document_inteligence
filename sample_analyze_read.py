"""
This code sample shows Prebuilt Read operations with the Azure AI Document Intelligence client library.
The async versions of the samples require Python 3.8 or later.

To learn more, please visit the documentation - Quickstart: Document Intelligence (formerly Form Recognizer) SDKs
https://learn.microsoft.com/azure/ai-services/document-intelligence/quickstarts/get-started-sdks-rest-api?pivots=programming-language-python
"""

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
import numpy as np
import json

"""
Remember to remove the key from your code when you're done, and never post it publicly. For production, use
secure methods to store and access your credentials. For more information, see 
https://docs.microsoft.com/en-us/azure/cognitive-services/cognitive-services-security?tabs=command-line%2Ccsharp#environment-variables-and-application-configuration
"""
endpoint = "https://hashomer-document-intelligence.cognitiveservices.azure.com/"
key = "DrFp02cDQzsMqHKqM63BGiUTyEZkI4nEINW68tmPWGOCBmuUWTHoJQQJ99BFAC5RqLJXJ3w3AAALACOGgdu5"

def format_bounding_box(bounding_box):
    if not bounding_box:
        return "N/A"
    reshaped_bounding_box = np.array(bounding_box).reshape(-1, 2)
    return ", ".join(["[{}, {}]".format(x, y) for x, y in reshaped_bounding_box])

def analyze_read(file_path=None, output_file=None, save_tables_json=False):
    document_intelligence_client  = DocumentIntelligenceClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )
    
    if file_path:
        # Use local file
        with open(file_path, "rb") as f:
            poller = document_intelligence_client.begin_analyze_document(
                "prebuilt-layout", body=f, content_type="application/octet-stream"
            )
    else:
        # Use sample URL document
        formUrl = "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-REST-api-samples/master/curl/form-recognizer/sample-layout.pdf"
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-layout", AnalyzeDocumentRequest(url_source=formUrl)
        )
    result = poller.result()

    # Prepare output content
    output_lines = []
    
    def add_output(text):
        print(text)
        output_lines.append(text)
    
    add_output(f"Document contains content: {result.content}")

    for idx, style in enumerate(result.styles):
        style_text = "Document contains {} content".format(
            "handwritten" if style.is_handwritten else "no handwritten"
        )
        add_output(style_text)

    for page in result.pages:
        add_output("----Analyzing Read from page #{}----".format(page.page_number))
        add_output(
            "Page has width: {} and height: {}, measured with unit: {}".format(
                page.width, page.height, page.unit
            )
        )

        for line_idx, line in enumerate(page.lines):
            add_output(
                "...Line # {} has text content '{}' within bounding box '{}'".format(
                    line_idx,
                    line.content,
                    format_bounding_box(line.polygon),
                )
            )

        for word in page.words:
            add_output(
                "...Word '{}' has a confidence of {}".format(
                    word.content, word.confidence
                )
            )

    # Analyze tables if any are found
    tables_data = []
    if result.tables:
        add_output("\n----Analyzing Tables----")
        for table_idx, table in enumerate(result.tables):
            add_output(f"Table # {table_idx} has {table.row_count} rows and {table.column_count} columns")
            
            # Create table data structure for JSON
            table_data = {
                "table_index": table_idx,
                "row_count": table.row_count,
                "column_count": table.column_count,
                "bounding_regions": [],
                "cells": [],
                "rows": []
            }
            
            # Add bounding regions
            if table.bounding_regions:
                for region in table.bounding_regions:
                    add_output(f"Table # {table_idx} location on page: {region.page_number} is {format_bounding_box(region.polygon)}")
                    table_data["bounding_regions"].append({
                        "page_number": region.page_number,
                        "polygon": region.polygon
                    })
            
            # Initialize rows structure
            for row_idx in range(table.row_count):
                table_data["rows"].append([])
            
            # Analyze cells
            for cell in table.cells:
                add_output(f"...Cell[{cell.row_index}][{cell.column_index}] has text '{cell.content}'")
                
                cell_data = {
                    "row_index": cell.row_index,
                    "column_index": cell.column_index,
                    "content": cell.content,
                    "bounding_regions": []
                }
                
                if cell.bounding_regions:
                    for region in cell.bounding_regions:
                        add_output(f"...content on page {region.page_number} is within bounding polygon '{format_bounding_box(region.polygon)}'")
                        cell_data["bounding_regions"].append({
                            "page_number": region.page_number,
                            "polygon": region.polygon
                        })
                
                table_data["cells"].append(cell_data)
                # Add cell content to rows structure
                table_data["rows"][cell.row_index].append(cell.content)
            
            tables_data.append(table_data)
        add_output("----End of Tables----")
    else:
        add_output("\nNo tables found in the document.")

    add_output("----------------------------------------")
    
    # Save to file if output_file is specified
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        print(f"\nResults saved to: {output_file}")
    
    # Save tables as JSON if requested
    if save_tables_json and tables_data:
        json_filename = output_file.replace('_ocr_results.txt', '_tables.json') if output_file else 'extracted_tables.json'
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(tables_data, f, ensure_ascii=False, indent=2)
        print(f"Tables saved as JSON to: {json_filename}")
    elif save_tables_json and not tables_data:
        print("No tables found to save as JSON.")


if __name__ == "__main__":
    import sys
    import os
    
    # Check for --json flag
    save_json = '--json' in sys.argv
    if save_json:
        sys.argv.remove('--json')
    
    if len(sys.argv) > 1:
        # Run with local PDF file
        pdf_file_path = sys.argv[1]
        # Generate output filename based on input filename
        base_name = os.path.splitext(os.path.basename(pdf_file_path))[0]
        output_file = f"{base_name}_ocr_results.txt"
        
        print(f"Analyzing local PDF file: {pdf_file_path}")
        print(f"Results will be saved to: {output_file}")
        if save_json:
            print(f"Tables will be saved as JSON")
        analyze_read(pdf_file_path, output_file, save_json)
    else:
        # Run with sample URL document
        print("No file specified, using sample document from URL")
        output_file = "sample_document_ocr_results.txt"
        print(f"Results will be saved to: {output_file}")
        if save_json:
            print(f"Tables will be saved as JSON")
        analyze_read(None, output_file, save_json)
