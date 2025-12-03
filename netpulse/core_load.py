import time
import json
import random
import string
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import sys
from netpulse.core_http import perform_http_request


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}',
)
logger = logging.getLogger(__name__)


def generate_user_data(user_id: int) -> Dict[str, str]:

    username_base = f"sim_user_{user_id}"
    email = f"{username_base}@{random.choice(['testcorp.com', 'example.org'])}"
    password = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    return {"username": username_base, "email": email, "password": password}


def _request_and_record(url, method, payload, headers, step_name, user_metrics):

    files_to_send = None
    data_payload = payload
    metric_payload = payload

    if isinstance(payload, dict) and "files" in payload:

        upload_payload = payload.copy()

        files_to_send = upload_payload.get("files")

        data_payload = upload_payload.get("data", None)

        metric_payload = data_payload

    else:
        # Standard requests (Login, Registration, etc.) use the original payload directly
        data_payload = payload
        metric_payload = payload

    # print(data_payload) # Debug print temporarily removed, but was helpful

    # --- 2. EXECUTE THE REQUEST ---
    # The crucial call now separates data and file arguments
    result = perform_http_request(
        url=url,
        method=method,
        payload=data_payload,
        headers=headers,
        files_to_upload=files_to_send,  # Passes the file path dictionary or None
    )

    # --- 3. RECORD METRICS ---
    user_metrics["requests"].append(
        {
            "step": step_name,
            "method": method,
            "url": url,
            "latency_ms": result.get("latency_ms"),
            "success": result.get("success"),
            "status_code": result.get("status_code"),
            "payload": metric_payload,
        }
    )

    return result


def simulate_user(
    user_data: Dict[str, Any],
    base_url: str,
    registration_endpoint: str,
    login_endpoint: str,
    target_endpoint: str,
    http_method: str,
    auth_header_key: str,
    auth_token_format: str,
    delay_ms: int,
    target_payload: Dict[str, Any] = None,
):

    user_id = user_data.get("email") or user_data.get("id", "unknown_user")
    user_metrics: Dict[str, Any] = {"user_id": user_id, "requests": []}
    login_payload = user_data.copy()
    token = None

    is_new_user = "email" not in user_data

    if is_new_user:

        generated_data = generate_user_data(user_data.get("id"))
        login_payload.update(generated_data)
        user_metrics["email"] = login_payload["email"]

        reg_url = base_url + registration_endpoint
        reg_result = _request_and_record(
            reg_url, "POST", login_payload, None, "registration", user_metrics
        )

        if not reg_result["success"]:
            return user_metrics

    else:
        user_metrics["email"] = login_payload["email"]

    login_url = base_url + login_endpoint
    credentials = {
        "email": login_payload["email"],
        "password": login_payload["password"],
    }

    login_result = _request_and_record(
        login_url, "POST", credentials, None, "login", user_metrics
    )

    if login_result["success"] and "token" in login_result["response_data"]:

        token = login_result["response_data"]["token"]

        user_metrics["token"] = token
    else:
        logger.error(
            json.dumps(
                {
                    "event": "login_failed",
                    "user": user_id,
                    "status_code": login_result.get("status_code", -1),
                    "error_detail": login_result.get("error", "No response data"),
                }
            )
        )
        return user_metrics

    time.sleep(delay_ms / 1000.0)
    target_url = base_url + target_endpoint
    headers = {auth_header_key: auth_token_format.format(token=token)}

    _request_and_record(
        target_url,
        http_method,
        target_payload,
        headers,
        "authenticated_target",
        user_metrics,
    )

    return user_metrics


def run_load_test(
    base_url: str,
    target_endpoint: str,
    http_method: str,
    existing_users_data: List[Dict[str, Any]] = None,
    num_new_users: int = 0,
    start_user_id: int = 1,
    registration_endpoint: str = "/api/v1/register",
    login_endpoint: str = "/api/v1/login",
    auth_header_key: str = "Authorization",
    auth_token_format: str = "Bearer {token}",
    delay_ms: int = 50,
    error_threshold: float = 0.05,
    target_payload: Dict[str, Any] = None,
) -> Dict[str, Any]:

    if num_new_users > 0:

        start = start_user_id
        end = start_user_id + num_new_users
        users_data = [{"id": i} for i in range(start, end)]
        mode = "New Users (Registration + Login)"
    elif existing_users_data:

        users_data = existing_users_data
        mode = "Existing Users (Login Only)"
    else:
        raise ValueError(
            "Must provide either 'existing_users_data' or a positive 'num_new_users'."
        )

    num_users = len(users_data)

    common_args = {
        "base_url": base_url,
        "registration_endpoint": registration_endpoint,
        "login_endpoint": login_endpoint,
        "target_endpoint": target_endpoint,
        "http_method": http_method,
        "auth_header_key": auth_header_key,
        "auth_token_format": auth_token_format,
        "delay_ms": delay_ms,
        "target_payload": target_payload,
    }

    # --- CONCURRENT EXECUTION USING THREADING ---
    start_total = time.time()

    with ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [
            executor.submit(simulate_user, user_data=data, **common_args)
            for data in users_data
        ]

        user_results = [f.result() for f in futures]

    end_total = time.time()

    all_latencies_ms = [
        r["latency_ms"]
        for user in user_results
        for r in user["requests"]
        if r["success"]
    ]

    total_requests = sum(len(user["requests"]) for user in user_results)
    successful_requests = sum(
        r["success"] for user in user_results for r in user["requests"]
    )
    failed_requests = total_requests - successful_requests
    error_rate = failed_requests / total_requests if total_requests else 0

    def get_latency_stat(data, percentile=None):
        if not data:
            return "N/A"
        if percentile is None:
            return f"{sum(data) / len(data):.2f}"
        if percentile == "max":
            return f"{max(data):.2f}"
        if percentile == "min":
            return f"{min(data):.2f}"
        return f"{sorted(data)[int(len(data) * percentile)]:.2f}"

    summary = {
        "test_mode": mode,
        "test_parameters": {
            "num_users": num_users,
            "http_method": http_method,
            "target_endpoint": target_endpoint,
            "total_runtime_seconds": f"{end_total - start_total:.2f}",
        },
        "metrics": {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "error_rate": f"{error_rate:.2%}",
            "average_latency_ms": get_latency_stat(all_latencies_ms),
            "max_latency_ms": get_latency_stat(all_latencies_ms, "max"),
            "min_latency_ms": get_latency_stat(all_latencies_ms, "min"),
            "p90_latency_ms": get_latency_stat(all_latencies_ms, 0.90),
        },
        "user_results_detail": user_results,
    }

    if error_rate > error_threshold:
        logger.warning(
            json.dumps(
                {
                    "event": "error_rate_exceeded",
                    "threshold": f"{error_threshold:.2%}",
                    "actual_rate": f"{error_rate:.2%}",
                    "message": "The API's error rate is unacceptably high under this load.",
                }
            )
        )

    return summary


if __name__ == "__main__":

    print("\n" + "=" * 50)
    print("SCENARIO 2: EXISTING USER LOGIN & FILE UPLOAD LOAD TEST (1 USER)")
    print("=" * 50)

    existing_users_data = [
        {"email": "cuzan2005@gmail.com", "password": "a"},
    ]

    file_upload_payload = {"files": {"file": "./requirements.txt"}}

    results_existing = run_load_test(
        existing_users_data=existing_users_data,
        base_url="http://localhost:5000",
        login_endpoint="/api/v1/login",
        target_endpoint="/api/v1/upload",
        http_method="POST",
        delay_ms=100,
        target_payload=file_upload_payload,
        auth_token_format="ApiKey {token}",
    )

    print("\nREPORT - EXISTING USERS:")
    print(json.dumps(results_existing["metrics"], indent=4))
    print(f"\nExample User 1 Requests ({results_existing['test_mode']}):")
    print(json.dumps(results_existing["user_results_detail"][0]["requests"], indent=4))
