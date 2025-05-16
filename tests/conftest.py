import pytest
import sys
from pathlib import Path

# Import the cache cleaning plugin
pytest_plugins = ["scripts.pytest_clean_cache"]


@pytest.fixture(scope="session", autouse=True)
def ensure_path_setup():
    """Add the project root to sys.path to ensure proper imports."""
    root_dir = Path(__file__).parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))


@pytest.fixture
def ioc_value():
    """Provides a test IOC value for testing."""
    return "test.example.com"
