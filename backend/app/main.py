"""Application factory for the CTA API.

Offline by construction: the app reads committed fixture files. It opens no socket, loads
no model, and requires no service other than itself. Building the app requires the
materialized fixtures to exist (run ``tools/fixturectl.py build materialize``).
"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.answer_routes import router as answer_router
from app.api.errors import register_exception_handlers
from app.api.portable_routes import router as portable_router
from app.api.retrieval_lifecycle_routes import router as retrieval_lifecycle_router
from app.api.retrieval_routes import router as retrieval_router
from app.api.review_routes import router as review_router
from app.api.routes import router
from app.assurance.rules import DeterministicAssuranceEvaluator
from app.discovery.registry import ProviderRegistry
from app.ingestion.repository import GitRepository
from app.persistence.ingested import IngestedStore
from app.persistence.portable import PortableRegistry
from app.persistence.review import ReviewWorkspace
from app.retrieval.lifecycle import RetrievalLifecycle
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

M3 status: artifacts, links, evidence, and threads are parsed from the nested fixture repository
at the requested revision; `POST /api/ingestion/run` reports what it ingested. `GET /api/findings`
evaluates the deterministic rule set. Discovery proposals are separate from accepted links;
review decisions are append-only workspace events, and the optional local/CocoIndex providers are
plugins behind `CandidateDiscovery`. No endpoint currently returns 501.
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
            {
                "name": "assurance",
                "description": "Deterministic rules; no model calls, no network.",
            },
            {"name": "discovery", "description": "Candidate proposals only; never writes links."},
            {
                "name": "portable",
                "description": "Read-only repository-scoped queries for external Gherkin projects.",
            },
            {
                "name": "review",
                "description": "Trusted-local-operator proposal capture, decisions, and workspace.",
            },
            {
                "name": "contract-only",
                "description": "Frozen shape, implementation in a later milestone (501).",
            },
        ],
    )
    app.state.settings = resolved
    app.state.store = IngestedStore.from_settings(resolved)
    app.state.evaluator = DeterministicAssuranceEvaluator(app.state.store)
    app.state.providers = ProviderRegistry(resolved, app.state.store)
    app.state.portable = PortableRegistry()
    app.state.review = ReviewWorkspace(app.state.store, resolved)
    app.state.retrieval = RetrievalLifecycle(
        app.state.store,
        GitRepository(resolved.fixture_repo),
        resolved.retrieval_snapshots,
        repository_name=resolved.fixture,
    )
    register_exception_handlers(app)
    app.include_router(router)
    app.include_router(portable_router)
    app.include_router(retrieval_router)
    app.include_router(answer_router)
    app.include_router(review_router)
    app.include_router(retrieval_lifecycle_router)
    return app


app = create_app()
