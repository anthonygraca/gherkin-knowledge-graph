"""Fixture-backed persistence and the ingested repository store."""

from app.persistence.fixtures import load_json, load_model
from app.persistence.ingested import IngestedStore

__all__ = ["IngestedStore", "load_json", "load_model"]
