"""Fixture JSON loading with contract validation and actionable errors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.domain.errors import FixtureDataInvalid, FixtureDataMissing

ModelT = TypeVar("ModelT", bound=BaseModel)


def load_json(path: Path) -> Any:
    """Read a JSON file, converting absence into a server-side configuration error."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise FixtureDataMissing(
            f"Fixture file '{path}' is missing. Run "
            f"'uv run --project backend python tools/fixturectl.py all' "
            f"from the repository root to generate fixture data."
        ) from exc
    except json.JSONDecodeError as exc:
        raise FixtureDataInvalid(f"Fixture file '{path}' is not valid JSON: {exc}") from exc


def load_model(path: Path, model_type: type[ModelT]) -> ModelT:
    """Load a fixture file and validate it against its contract."""
    payload = load_json(path)
    try:
        return model_type.model_validate(payload)
    except ValidationError as exc:
        raise FixtureDataInvalid(
            f"Fixture file '{path}' does not satisfy {model_type.__name__}:\n{exc}"
        ) from exc
