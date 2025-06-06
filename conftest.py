"""
Global pytest configuration for SentinelForge tests.
Handles import path setup for both local and CI environments.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add the sentinelforge subdirectory to Python path for nested imports
sentinelforge_dir = project_root / "sentinelforge"
if sentinelforge_dir.exists():
    sys.path.insert(0, str(sentinelforge_dir))

print(f"Added to Python path: {project_root}")
print(f"Added to Python path: {sentinelforge_dir}")
print(f"Current Python path: {sys.path[:3]}...")  # Show first 3 entries
