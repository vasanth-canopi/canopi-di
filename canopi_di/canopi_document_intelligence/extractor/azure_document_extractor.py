import frappe
import os
import io
import json
import logging
import base64


from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult
from azure.core.exceptions import AzureError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("azure_document_extractor")

# Load settings from Canopi Settings
settings = frappe.get_doc('Canopi Settings')

# Azure configuration
ENDPOINT = ""
KEY = ""
DOCUMENT_EXTRACTOR_ID = ""

def load_config():
    """
    Loads configuration from environment variables.
    """
    global ENDPOINT, KEY, DOCUMENT_EXTRACTOR_ID

    try:
        ENDPOINT = settings.azure_endpoint
        KEY = settings.azure_key
        DOCUMENT_EXTRACTOR_ID = settings.azure_document_extractor_id


        if not ENDPOINT or not KEY or not DOCUMENT_EXTRACTOR_ID:
            raise ValueError("One or more required azure settings are missing.")
        
        return ENDPOINT, KEY, DOCUMENT_EXTRACTOR_ID
        logger.info("Config loaded successfully from canopi settings.")

    except Exception as e:
        logger.error(f"Error loading configuration from canopi settings: {e}")
        raise

def analyze_document(pdf_path):

    file_name = os.path.basename(pdf_path)
    # Change the file extension to .json
    json_file_name = os.path.splitext(file_name)[0] + ".json"
    # Create the full path for the JSON file
    json_file_path = os.path.join(os.path.dirname(pdf_path), json_file_name)

    # Check if the JSON file already exists
    if os.path.exists(json_file_path):
        
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": json_file_name,
            "is_private": 1
        })

        return file_doc.file_url

    # If the JSON file does not exist, proceed with the analysis
    else:

        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Input PDF File not found: {pdf_path}")

            
            document_intelligence_client = DocumentIntelligenceClient(endpoint=ENDPOINT, credential=AzureKeyCredential(KEY))
            
            with open(pdf_path, "rb") as f:
                poller = document_intelligence_client.begin_analyze_document(model_id=DOCUMENT_EXTRACTOR_ID, body=f, locale="en-US")
            
            documents: AnalyzeResult = poller.result()

            result_str = json.dumps(documents.as_dict(), indent=2)
            buffer = io.BytesIO()
            buffer.write(result_str.encode('utf-8'))  # Write JSON string to buffer
            file_content = buffer.getvalue()

            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": json_file_name,
                "is_private": 1,
                "content": base64.b64encode(file_content).decode('utf-8'),
                "decode": 1
            }).insert()
            file_doc.save()
            

            return file_doc.file_url

        except FileNotFoundError as fnf_error:
            print(f"Error: {fnf_error}")
        except AzureError as azure_error:
            print(f"Azure Service Error: {azure_error}")
        except Exception as e:
            print(f"Unexpected Error: {e}")


ENDPOINT, KEY, DOCUMENT_EXTRACTOR_ID = load_config()