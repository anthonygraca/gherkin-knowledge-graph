"""Repository ingestion (roadmap §3): revision-pinned parsing into domain artifacts.

The package is intentionally small. DT-01 adds requirement and Gherkin parsing; DT-02 adds
source/test annotations; DT-03 adds link ingestion; DT-04 assembles threads from the result.
Nothing here writes accepted links, review states, or verification evidence on its own: links
and evidence are *read* from declared repository files.
"""

from app.ingestion.errors import IngestionError
from app.ingestion.repository import GitRepository
from app.ingestion.scan import scan_artifacts

__all__ = ["GitRepository", "IngestionError", "scan_artifacts"]
