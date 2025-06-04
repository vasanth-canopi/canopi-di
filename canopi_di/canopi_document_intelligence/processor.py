import frappe
import json
from datetime import datetime
from frappe.utils.file_manager import save_file
import requests
import os
from datetime import date
from canopi_di.canopi_document_intelligence.classifier.azure_pdfsplitter import classify_first_page, split_pdf_by_first_page
from canopi_di.canopi_document_intelligence.extractor.azure_document_extractor import analyze_document
from canopi_di.canopi_document_intelligence.jmespath_mapper import extract_fields


@frappe.whitelist()
def set_field(dt, dn, fd, vl):
    frappe.db.set_value(dt, dn, fd, vl)
    frappe.db.commit()


@frappe.whitelist()
def enqueue_func(path, data):
    frappe.enqueue(
        path,
        data=data,
#        track_job=True,
#        job_name="Calling Syntax API"
    )


# Define allowed status values
allowed_status_values = ["Unprocessed", "Processing", "Processed", "Failed"]

# Helper function to set status with validation
def set_document_status(docname, status, response=None):
    if status not in allowed_status_values:
        frappe.throw(f"Invalid status value: {status}")
    frappe.db.set_value("Document", docname, "status", status)
    if response is not None:
        frappe.db.set_value("Document", docname, "response", str(response))
    frappe.db.commit()

# Process PDF documents, Split them, and create new documents as per their doctype.

@frappe.whitelist()
def process_document(data):
    try:
        data = json.loads(data)
        docname = data.get("docname")
        document_path = data.get("document_path")
        document_type = data.get("document_type")
        split_mode = data.get("split_mode")
        
        pdf_files = None
        split_success = False


        document_path = frappe.get_doc("File", {"file_url": document_path}).get_full_path()

        #---- SPLIT PDF if SPLIT_MODE = TRUE -----#
        if split_mode:
            try:
                # Ensure the directory for split files exists

                # Split the PDF into separate files based on the first page classification
                result = classify_first_page(document_path)
                pdf_files_metadata = split_pdf_by_first_page(document_path, result)

                split_output = json.dumps(pdf_files_metadata, indent=2)

                # Save the output_file paths into pdf_files
                pdf_files = [file_data["file_url"] for file_data in pdf_files_metadata]
            

                # Iterate over the split files and create new "Invoice" documents
                for file_path in pdf_files:

                    
                    new_doc = frappe.get_doc({
                        "doctype": document_type,
                        "file": file_path,
                        "document_id": data.get("docname")  # Use the current document's name
                    })
                    new_doc.insert(ignore_permissions=True)
                    new_doc.invoice_id = new_doc.name
                    new_doc.save()


                split_success = True
                set_document_status(docname, "Processed", split_output)

            except Exception as e:
                frappe.log_error(frappe.get_traceback(), "Error during PDF splitting - " + str(docname))
                set_document_status(docname, "Failed", str(e))
                return

        #---- END SPLIT PDF -----#



    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Canopi DI: Process Document - " + str(docname))
        set_document_status(docname, "Failed", str(e))


# Extract content from PDF documents based on its type.

@frappe.whitelist()
def extract_document(data):
    try:
        data = json.loads(data)
        doctype = data.get("doctype")
        docname = data.get("docname")
        document_path = data.get("document_path")

        document_path = frappe.get_doc("File", {"file_url": document_path}).get_full_path()
        
        json_file_url = analyze_document(document_path)

        # Save the JSON file URL to the document
        set_field(doctype, docname, "json_file", json_file_url)
        set_field(doctype, docname, "status", "Processed")
        

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Canopi DI: Extract Document - " + str(docname))
        set_field(doctype, docname, "status", "Failed")
        return

@frappe.whitelist()
def validate_document_fields(data):
    try:
        data = json.loads(data)
        doctype = data.get("doctype")
        docname = data.get("docname")
        input_json = data.get("input_json")
        map_json = data.get("map_json")

        result = extract_fields(map_source=map_json, input_source=input_json)
        #frappe.log_error(frappe.get_traceback(), "Canopi DI: Extract Document Fields - " + str(json.dumps(result.get("result"), indent=2)))

        set_field(doctype, docname, "output_json", json.dumps(result.get("result"), indent=2))
        return result
            
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Canopi DI: Extract Document Fields - " + str(docname))
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def extract_document_fields(data):
    try:
        data = json.loads(data)
        doctype = data.get("doctype")
        docname = data.get("docname")
        input_json = data.get("input_json")
        map_json = data.get("map_json")


        map_json_txt = frappe.get_doc("Data Mapper", map_json).map_json

        frappe.log_error(frappe.get_traceback(),f"Extracting fields for {doctype} {docname} - Input JSON: {input_json}, Map JSON: {map_json}")
        result = extract_fields(map_source=map_json_txt, input_source=input_json)


        set_field(doctype, docname, "status", "Processed")
        values = result.get("result")

        if isinstance(values, dict):
            for fieldname, value in values.items():
                if fieldname:  # Ensure fieldname is not None or empty
                    frappe.logger().info(f"Updating {doctype} {docname} - {fieldname}: {value}")
                    frappe.db.set_value(doctype, docname, fieldname, value)
        else:
            frappe.throw("Invalid data: result['result'] is not a dict.")

        return result
            
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Canopi DI: Extract Document Fields - " + str(docname))
        return {"status": "error", "message": str(e)}