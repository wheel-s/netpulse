import json
import typer
from typing import Optional, Dict, Any
from netpulse.core_ping import tcp_ping
from netpulse.core_http import perform_http_request
from netpulse.core_security import get_security_info
from netpulse.core_load import run_load_test
from netpulse.logger import log_json

main = typer.Typer(help="NetPulse CLI - Network & API testing tool")


# -------------------- PING --------------------
@main.command()
def ping(host: str, port: Optional[int] = 443, path: Optional[str] = None):

    result = tcp_ping(host, port)
    print(json.dumps(result, indent=4))
    if path:
        log_json(result, path)


# -------------------- HTTP --------------------


@main.command()
def http(
    url: str,
    method: str = "POST",
    token: Optional[str] = None,
    payload: Optional[str] = None,
    files: Optional[str] = None,
    timeout: float = 5.0,
    output: Optional[str] = None,
):
    token = token.replace("/", " ") if token else None

    headers_dict = {"Authorization": f"{token}"} if token else None
    payload_data: Optional[dict] = json.loads(payload) if payload else None
    files_data: Optional[Dict[str, Any]] = json.loads(files) if files else None

    result = perform_http_request(
        url,
        method,
        headers_dict,
        payload_data,
        files_to_upload=files_data,
        timeout=timeout,
    )
    print(json.dumps(result, indent=4))
    if output:
        log_json(result, output)


# -------------------- SECURITY --------------------
@main.command()
def security(host: str, port: int = 443, path: Optional[str] = None):

    result = get_security_info(host, port)
    print(json.dumps(result, indent=4))
    if path:
        log_json(result, path)


# -------------------- LOAD --------------------
@main.command()
def load(
    url: str,
    method: str = "GET",
    users: int = 10,
    delay: int = 50,
    target: Optional[str] = "/GET",
    timeout: float = 5.0,
    payload: Optional[str] = None,
    start: Optional[str] = 101,
    login_P: Optional[str] = "/api/v1/login",
    register_P: Optional[str] = "/api/v1/register",
    path: Optional[str] = None,
):
    """Run load test with multiple simulated users"""
    payload_data: Optional[dict] = json.loads(payload) if payload else None
    result = run_load_test(
        base_url=url,
        target_endpoint=target,
        http_method=method,
        login_endpoint="/api/v1/login",
        num_new_users=users,
        start_user_id=start,
        auth_token_format="",
        delay_ms=delay,
        target_payload=payload_data,
    )
    print(json.dumps(result, indent=4))
    if path:
        log_json(path)


# -------------------- MAIN --------------------
if __name__ == "__main__":
    main()
