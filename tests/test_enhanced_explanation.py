def test_explanation(ioc_value):
    """
    Simple test for enhanced explanation functionality.
    Uses the ioc_value fixture from conftest.py.
    """
    assert (
        ioc_value == "test.example.com"
    ), "IOC value fixture should be initialized correctly"
