# NetPulse ⚡️

NetPulse is a concurrent load testing and network utility toolkit designed for authenticating against and testing HTTP/API endpoints with high concurrency.

## Features

* **Concurrent Load Testing:** Simulate multiple users with Python threads.
* **Authentication:** Supports custom login endpoints and various token formats (e.g., Bearer, ApiKey).
* **Robust HTTP:** Handles complex requests, including `multipart/form-data` file uploads.
* **CLI:** Command-line interface for quick testing (ping, http, security, load).

## Installation

```bash
git clone https://github.com/yourusername/netpulse.git
cd netpulse
pip install .

```

#  Library Uage

``bash
from netpulse import tcp_ping, perform_http_request, get_security_info, run_load_test

# TCP Ping
result = tcp_ping("google.com", 443)
print(result)

# HTTP Request
response = perform_http_request("https://httpbin.org/get", method="GET")
print(response)

# Security Check
security_report = get_security_info("google.com")
print(security_report)

# Load Test
load_results = run_load_test(
    base_url="http://localhost:5000",
    target_endpoint="/api/v1/test",
    http_method="GET",
    num_new_users=5,
    delay_ms=50
)
print(load_results)

```
# CLI Usage

```bash
# Ping
netpulse ping --host google.com --port 443

# HTTP request
netpulse http --url https://httpbin.org/get --method GET

# Security check
netpulse security --host google.com

# Load test
netpulse load --url http://localhost:5000 --users 5 --delay 50

## help for commands
netpulse --help

```

# Contributiong

Contributions are welcome! Please:

1. Fork the repository
2. Create a branch
3. Run tests and linting
4. Submit a pull request
