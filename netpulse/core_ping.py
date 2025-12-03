import socket
import time


def tcp_ping(host, port):

    total_start = time.perf_counter()
    result = {
        "host": host,
        "port": port,
        "success": False,
        "msg": None,
        "dns_lookup_time": None,
        "tcp_handshake_time": None,
        "total_connection_time": None,
        "error": None,
    }
    try:
        dns_start = time.perf_counter()

        ip_address = socket.gethostbyname(host)
        dns_end = time.perf_counter()
        dns_time_ms = (dns_end - dns_start) * 1000.0
    except socket.error as e:
        result["error"] = "DNS Error: " + str(e)
        return result
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)

    try:
        tcp_start = time.perf_counter()
        sock.connect((ip_address, port))
        tcp_end = time.perf_counter()
        tcp_handshake_time_ms = (tcp_end - tcp_start) * 1000.0
        result["success"] = True
        result["msg"] = f"Successfully connected to {host} ({ip_address}:{port})"

    except socket.error as e:
        result["error"] = "TCP Connection Error: " + str(e)
        return result
    finally:
        sock.close()

    total_end = time.perf_counter()
    total_time_ms = (total_end - total_start) * 1000.0

    result["dns_lookup_time"] = f"{dns_time_ms:.2f} ms"
    result["handshake_time"] = f"{tcp_handshake_time_ms:.2f} ms"
    result["total_connection_time"] = f"Total Connection Time:  {total_time_ms:.2f} ms"

    return result


if __name__ == "__main__":
    result = tcp_ping("localhost", 5000)
    print(result)
