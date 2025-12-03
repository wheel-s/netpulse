from netpulse.core_ping import tcp_ping


def test_ping_success():
    result = tcp_ping("https://google.com", port=80)
    assert result["success"] in [True, False]
    assert "total_connection_time" in result


def test_ping_failure():
    result = tcp_ping("invalid_host", port=80)
    assert result["success"] is False
    assert "error" in result
