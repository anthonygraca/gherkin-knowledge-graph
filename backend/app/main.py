"""Application factory for the CTA API.

Offline by construction: the app reads committed fixture files. It opens no socket, loads
no model, and requires no service other than itself. Building the app requires the
materialized fixtures to exist (run ``tools/fixturectl.py build materialize``).
"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routes import router
from app.assurance.sample_findings import SampleFindingsSource
from app.discovery.registry import ProviderRegistry
from app.persistence.ingested import IngestedStore
from app.settings import Settings, load_settings
from app.version import PACKAGE_VERSION

DESCRIPTION = """
Continuous Traceability Assurance connects requirements, Gherkin scenarios, source code,
tests, Git revisions, and verification evidence.

Invariants this API upholds:

* **Proposals are not accepted relationships.** `POST /api/discovery` returns candidates;
  they carry no link id and no review state, and accepting one is a separate, audited act.
* **Accepted relationships are not verification.** A link is a claim about intent; evidence
  comes only from recorded test executions pinned to a commit.
* **Change is not failure.** A relevant change after verification yields
  `reverification_required`, never `verification_failed`. Failure requires a recorded
  failing execution at the evaluated baseline.
* **Version-aware.** Artifacts carry a revision and a content hash; findings and evidence
  are pinned to the baseline they were evaluated at.

M1 status: artifacts, links, evidence, and threads are parsed from the nested fixture repository
at the requested revision; `POST /api/ingestion/run` reports what it ingested. `GET /api/findings`
still replays reviewed sample findings. The endpoints tagged `contract-only` return 501 and name the
story that will implement them.
"""


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or load_settings()
    app = FastAPI(
        title="Continuous Traceability Assurance API",
        version=PACKAGE_VERSION,
        description=DESCRIPTION,
        openapi_tags=[
            {"name": "reads", "description": "Implemented over the ingested fixture repository."},
            {"name": "ingestion", "description": "Parses the configured repository at a revision."},
            {"name": "discovery", "description": "Candidate proposals only; never writes links."},
            {
                "name": "contract-only",
                "description": "Frozen shape, implementation in a later milestone (501).",
            },
        ],
    )
    app.state.settings = resolved
    app.state.store = IngestedStore.from_settings(resolved)
    app.state.findings_source = SampleFindingsSource.from_settings(resolved)
    app.state.providers = ProviderRegistry(resolved)
    register_exception_handlers(app)
    app.include_router(router)
    return app


app = create_app()
