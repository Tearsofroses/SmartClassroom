"""
Pytest configuration for weights validation tests.
Shared fixtures and setup.
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Create fixtures directory if needed
FIXTURES_DIR = Path(__file__).parent / 'fixtures' / 'frames'
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
