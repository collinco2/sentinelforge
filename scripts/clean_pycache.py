#!/usr/bin/env python
"""
Clean Python bytecode and cache files.

This script removes __pycache__ directories and .pyc files to prevent
import conflicts during test discovery.
"""

import os
import shutil
from pathlib import Path


def clean_pycache(directory="."):
    """Remove __pycache__ directories and .pyc files recursively."""
    root_dir = Path(directory).resolve()

    # Find and remove __pycache__ directories
    for pycache_dir in root_dir.glob("**/__pycache__"):
        print(f"Removing {pycache_dir}")
        try:
            shutil.rmtree(pycache_dir)
        except Exception as e:
            print(f"  Error: {e}")

    # Find and remove .pyc files
    for pyc_file in root_dir.glob("**/*.pyc"):
        print(f"Removing {pyc_file}")
        try:
            os.remove(pyc_file)
        except Exception as e:
            print(f"  Error: {e}")

    # Find and remove .pyo files
    for pyo_file in root_dir.glob("**/*.pyo"):
        print(f"Removing {pyo_file}")
        try:
            os.remove(pyo_file)
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    import sys

    print("Cleaning Python bytecode and cache files...")

    if len(sys.argv) > 1:
        directory = sys.argv[1]
        clean_pycache(directory)
    else:
        clean_pycache()

    print("Done.")
