"""Puts the repository root on sys.path so the fixture tests can import the `src` package."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
