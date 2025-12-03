import ssl
import socket
import datetime
import requests


def get_security_info(host, port=443):

    security_info = {
        "ssl_expiry": {},
        "tls_protocols": {},
        "security_headers": {},
        "errors": [],
    }

    # 1. SSL Expiry Check
    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, port)) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                not_after_str = cert["notAfter"]
                not_after_date = datetime.datetime.strptime(
                    not_after_str, "%b %d %H:%M:%S %Y %Z"
                )
                days_remaining = (not_after_date - datetime.datetime.now()).days

                security_info["ssl_expiry"] = {
                    "not_after": not_after_str,
                    "days_remaining": days_remaining,
                    "expired": days_remaining < 0,
                }
    except Exception as e:
        security_info["errors"].append(f"SSL Expiry Check failed: {e}")

    try:

        context_tls1_3 = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context_tls1_3.minimum_version = ssl.TLSVersion.TLSv1_3
        context_tls1_3.check_hostname = True
        context_tls1_3.verify_mode = ssl.CERT_REQUIRED

        try:
            with socket.create_connection((host, port)) as sock:
                with context_tls1_3.wrap_socket(sock, server_hostname=host):
                    security_info["tls_protocols"]["TLSv1_3_supported"] = True
        except ssl.SSLError:
            security_info["tls_protocols"]["TLSv1_3_supported"] = False

        context_tls1_2 = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context_tls1_2.minimum_version = ssl.TLSVersion.TLSv1_2
        context_tls1_2.check_hostname = True
        context_tls1_2.verify_mode = ssl.CERT_REQUIRED

        try:
            with socket.create_connection((host, port)) as sock:
                with context_tls1_2.wrap_socket(sock, server_hostname=host):
                    security_info["tls_protocols"]["TLSv1_2_supported"] = True
        except ssl.SSLError:
            security_info["tls_protocols"]["TLSv1_2_supported"] = False

    except Exception as e:
        security_info["errors"].append(f"TLS Protocol Check failed: {e}")

    # 3. Security Headers Check
    try:

        url = f"https://{host}" if not host.startswith("http") else host
        response = requests.get(url, timeout=5)
        headers = response.headers

        security_headers_to_check = [
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Referrer-Policy",
            "Permissions-Policy",
        ]

        for header in security_headers_to_check:
            security_info["security_headers"][header] = headers.get(header, "Not Set")

    except requests.exceptions.RequestException as e:
        security_info["errors"].append(f"Security Headers Check failed: {e}")
    except Exception as e:
        security_info["errors"].append(f"Security Headers Check failed: {e}")

    return security_info


# Example Usage:

if __name__ == "__main__":
    host_to_check = "google.com"
    security_report = get_security_info(host_to_check)

    for key, value in security_report.items():
        print(f"{key} : {value}\n")
