"""Repository ingestion (roadmap §3): revision-pinned parsing into domain artifacts.

DT-01 adds requirement and Gherkin parsing; DT-02 adds source/test annotations; DT-03 adds link
ingestion; DT-04 adds evidence, thread assembly, and the store cutover. Nothing here writes
accepted links, review states, or verification evidence on its own: links and evidence are *read*
from declared repository files.
"""

from app.ingestion.errors import IngestionError
from app.ingestion.repository import GitRepository
from app.ingestion.revision import IngestedRevision, ingest_revision
from app.ingestion.scan import scan_artifacts
from app.ingestion.thread import assemble_thread

__all__ = [
    "GitRepository",
    "IngestedRevision",
    "IngestionError",
    "assemble_thread",
    "ingest_revision",
    "scan_artifacts",
]
