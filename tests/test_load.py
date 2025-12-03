from netpulse.core_load import run_load_test


def test_load():
    result = run_load_test("https://www.jumia.com.ng", "GET", "GET", 0, 2)
    assert "metrics" in result
