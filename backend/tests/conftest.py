"""
conftest.py — Pytest configuration for backend test suite.
Adds the backend/ directory to sys.path so `from app.xxx import ...` works
when running pytest from the project root.
"""
import sys
import os

# Ensure the backend package root is on the path
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(BACKEND_DIR))
