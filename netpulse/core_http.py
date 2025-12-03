import requests
import os
import time
from typing import Optional, Dict, Any

FileStructure = Dict[str, Any]


def perform_http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    payload: Optional[Any] = None,
    files_to_upload: Optional[FileStructure] = None,
    timeout: float = 5.0,
) -> Dict[str, Any]:

    method = method.upper()
    start_time = time.perf_counter()
    status_code = -1
    success = False
    error_message = None
    response_data = {}

    open_file_handles = []
    methods_with_payload = ["POST", "PUT", "PATCH"]

    request_kwargs = {"headers": headers, "timeout": timeout, "allow_redirects": False}

    if files_to_upload:
        prepared_files = {}
        for field_name, file_path in files_to_upload.items():
            if os.path.exists(file_path):
                file_handle = open(file_path, "rb")
                open_file_handles.append(file_handle)
                prepared_files[field_name] = file_handle
            else:
                raise FileExistsError(f"file not found at path: {file_path}")
            request_kwargs["files"] = prepared_files

    if method in methods_with_payload and payload is not None:

        if isinstance(payload, dict) or isinstance(payload, list):
            request_kwargs["json"] = payload
        else:

            request_kwargs["data"] = payload
    elif method not in methods_with_payload and payload is not None:
        print(
            f"Warning: Payload provided for '{method}' request. Payloads for GET/DELETE are typically ignored by servers."
        )

    try:

        response = requests.request(method, url, **request_kwargs)
        end_time = time.perf_counter()

        status_code = response.status_code
        success = response.ok

        res_text = response.text

        if res_text:
            try:
                response_data = response.json()
            except requests.exceptions.JSONDecodeError:
                response = res_text

    except requests.exceptions.Timeout:
        end_time = time.perf_counter()
        error_message = f"Request timed out after {timeout} seconds."
    except requests.exceptions.RequestException as e:
        end_time = time.perf_counter()
        error_message = f"An error occurred: {e}"
    finally:
        for f in open_file_handles:
            f.close()

    latency_ms = (end_time - start_time) * 1000.0 if "end_time" in locals() else None

    return {
        "status_code": status_code,
        "latency_ms": round(latency_ms, 2) if latency_ms is not None else None,
        "success": success,
        "response_data": response_data,
        "error": error_message,
    }


# Example Usage:

if __name__ == "__main__":
    result_post = perform_http_request(
        url="http://localhost:5000",
        method="GET",
    )

    print(f"GET Request Result: {result_post}")
