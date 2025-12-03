from netpulse.core_security import get_security_info


def test_security_check():
    result = get_security_info("https://www.jumia.com.ng/")
    assert "ssl_expiry" in result
    assert "tls_protocols" in result
