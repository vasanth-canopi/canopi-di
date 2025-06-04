import json
import os
import logging
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import SplitMode, AnalyzeResult
import io

import base64

from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path
import frappe

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("azure_pdfsplitter")

# Load settings from Canopi Settings
settings = frappe.get_doc('Canopi Settings')


# Azure configuration
ENDPOINT = ""
KEY = ""
PAGE_CLASSIFIER_ID = ""

def load_config():
    """
    Loads configuration from environment variables.
    """
    global ENDPOINT, KEY, PAGE_CLASSIFIER_ID

    try:
        ENDPOINT = settings.azure_endpoint
        KEY = settings.azure_key
        PAGE_CLASSIFIER_ID = settings.azure_page_classifier_id


        if not ENDPOINT or not KEY or not PAGE_CLASSIFIER_ID:
            raise ValueError("One or more required azure settings are missing.")
        
        return ENDPOINT, KEY, PAGE_CLASSIFIER_ID
        logger.info("Config loaded successfully from canopi settings.")

    except Exception as e:
        logger.error(f"Error loading configuration from canopi settings: {e}")
        raise

def split_pdf_by_first_page(pdf_path: str, metadata: list) -> list:
    reader = PdfReader(pdf_path)
    splits = []
    current_split = []
    split_count = 0

    for entry in metadata:
        page_num = entry["page"]
        doc_type = entry["doc_type"]

        if doc_type == "FIRST_PAGE":
            if current_split:
                splits.append(current_split)
            current_split = [page_num]
        else:
            current_split.append(page_num)

    if current_split:
        splits.append(current_split)

    output_json = []
    base_name = Path(pdf_path).stem

    for i, page_range in enumerate(splits, start=1):
        writer = PdfWriter()
        for p in page_range:
            writer.add_page(reader.pages[p - 1])  # 0-based index
        file_name = f"{base_name}_DOCUMENT{i}.pdf"

#        with open(output_file, "wb") as f:
#            writer.write(f)


        buffer = io.BytesIO()
        writer.write(buffer)
        file_content = buffer.getvalue()

        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file_name,
            "is_private": 1,
            "content": base64.b64encode(file_content).decode('utf-8'),
            "decode": 1
        }).insert()



        output_json.append({
            "split": f"DOCUMENT{i}",
            "page_range": page_range,
            "file_url": file_doc.file_url
        })

    return output_json




def classify_first_page(pdf_path: str) -> list:
    """
    Classifies the first page of a PDF using Azure Document Intelligence custom model.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        list: A list of dictionaries containing page number, doc type, and confidence.
    """
    
    logger.info(f"ENDPOINT: {ENDPOINT}")
    
    try:
        logger.info(f"Initializing Document Intelligence Client")
        client = DocumentIntelligenceClient(endpoint=ENDPOINT, credential=AzureKeyCredential(KEY))

        with open(pdf_path, "rb") as f:
            logger.info(f"Submitting document for classification: {pdf_path}")
            poller = client.begin_classify_document(PAGE_CLASSIFIER_ID, body=f, split=SplitMode.PER_PAGE)

        result: AnalyzeResult = poller.result()

        output = [
            {
                "page": idx + 1,
                "doc_type": doc.doc_type,
                "doc_confidence": round(doc.confidence, 3)
            }
            for idx, doc in enumerate(result.documents)
        ]

        logger.info(f"Classification completed successfully for: {pdf_path}")
        return output

    except Exception as e:
        logger.error(f"Error during classification: {str(e)}", exc_info=True)
        return []


ENDPOINT, KEY, PAGE_CLASSIFIER_ID = load_config()

#result = classify_first_page('./Invoice023.pdf')
#print(json.dumps(result, indent=2))

# Example usage (for testing only):
#if __name__ == "__main__":

#    config = load_config('config.ini')
    
#    result = classify_first_page('./Invoice023.pdf')
#    print(json.dumps(result, indent=2))

#    result = split_pdf_by_first_page("./Invoice023.pdf", result, output_dir="splits")
#    print(json.dumps(result, indent=2))


