"""Pytest config — add project root to sys.path so tests can import vietnam_compliance."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
