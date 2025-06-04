import jmespath
import frappe
import json

from typing import Any, Union

def extract_fields(
    map_source: str,
    input_source: str
) -> Any:
    try:
        expr = jmespath.compile(map_source)

        # Load or use input JSON
        if isinstance(input_source, str):
            try:
                full_file_path = frappe.get_doc("File", {"file_url": input_source}).get_full_path()
                with open(full_file_path, 'r') as f:
                    data = json.load(f)
            except Exception as e:
                return {"status": "error", "message": f"Error loading file {str(input_source)}: {str(e)}"}
        else:
            data = input_source

        result = expr.search(data)
        return {"status": "success", "result": result}

    except Exception as e:
        return {"status": "error", "message": str(e)}