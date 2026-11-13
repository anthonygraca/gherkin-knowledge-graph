"""FastAPI dependencies.

All collaborator state hangs off ``app.state`` so a test (or a future worker) can build an
application with different settings without monkeypatching imports.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.assurance.rules import DeterministicAssuranceEvaluator
from app.assurance.sample_findings import SampleFindingsSource
from app.discovery.registry import ProviderRegistry
from app.domain.ports import ArtifactRepository
from app.persistence.ingested import IngestedStore
from app.settings import Settings


def provide_settings(request: Request) -> Settings:
    return request.app.state.settings


def provide_repository(request: Request) -> ArtifactRepository:
    """The shared port: routes read artifacts, links, and evidence through this, not the class."""
    return request.app.state.store


def provide_store(request: Request) -> IngestedStore:
    """The concrete store, for ingestion and fixture-facing helpers."""
    return request.app.state.store


def provide_findings_source(request: Request) -> SampleFindingsSource:
    return request.app.state.findings_source


def provide_evaluator(request: Request) -> DeterministicAssuranceEvaluator:
    return request.app.state.evaluator


def provide_providers(request: Request) -> ProviderRegistry:
    return request.app.state.providers


SettingsDep = Annotated[Settings, Depends(provide_settings)]
RepositoryDep = Annotated[ArtifactRepository, Depends(provide_repository)]
StoreDep = Annotated[IngestedStore, Depends(provide_store)]
FindingsDep = Annotated[SampleFindingsSource, Depends(provide_findings_source)]
EvaluatorDep = Annotated[DeterministicAssuranceEvaluator, Depends(provide_evaluator)]
ProvidersDep = Annotated[ProviderRegistry, Depends(provide_providers)]
