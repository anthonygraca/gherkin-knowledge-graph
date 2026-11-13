"""Ingestion failures.

Malformed repository content is not a client-request error and must not be skipped silently.
Parsers raise :class:`IngestionError`; the caller decides how to present it (the fixture-backed
API maps it to a documented server-side problem document).
"""

from __future__ import annotations


class IngestionError(ValueError):
    """Repository content or Git access made ingestion impossible."""
