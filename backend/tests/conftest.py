"""
pytest configuration for Vibebells backend tests

This module configures pytest and provides common fixtures.
"""

import sys
import os

# Add backend directory to path so tests can import app modules
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
