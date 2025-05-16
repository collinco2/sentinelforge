"""
A pytest plugin to clean Python cache files before test collection.

This helps prevent import mismatch errors during pytest collection.
"""

import pytest
from pathlib import Path
import shutil
import os


def pytest_configure(config):
    """Clean Python cache files at the start of a pytest run."""
    # Get the current directory to search for cache files
    root_dir = Path.cwd()

    print("\nCleaning Python cache files before test collection...\n")

    # Count of items removed
    pycache_count = 0
    pyc_count = 0

    # Remove __pycache__ directories
    for pycache_dir in root_dir.glob("**/__pycache__"):
        print(f"Removing {pycache_dir}")
        try:
            shutil.rmtree(pycache_dir)
            pycache_count += 1
        except Exception as e:
            print(f"  Error: {e}")

    # Remove .pyc files
    for pyc_file in root_dir.glob("**/*.pyc"):
        print(f"Removing {pyc_file}")
        try:
            os.remove(pyc_file)
            pyc_count += 1
        except Exception as e:
            print(f"  Error: {e}")

    print(
        f"\nRemoved {pycache_count} __pycache__ directories and {pyc_count} .pyc files\n"
    )
