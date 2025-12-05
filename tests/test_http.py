from netpulse.core_http import perform_http_request


def test_get_request():
    result = perform_http_request("https://google.com", "GET")
    assert result["success"] is True
