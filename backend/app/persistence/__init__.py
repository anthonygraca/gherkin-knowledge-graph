"""Fixture-backed persistence (M0 mock services)."""

from app.persistence.fixtures import load_json, load_model
from app.persistence.store import FixtureStore

__all__ = ["FixtureStore", "load_json", "load_model"]
