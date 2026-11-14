"""FastAPI dependencies.

All collaborator state hangs off ``app.state`` so a test (or a future worker) can build an
application with different settings without monkeypatching imports.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.assurance.rules import DeterministicAssuranceEvaluator
from app.discovery.registry import ProviderRegistry
from app.domain.ports import ArtifactRepository
from app.persistence.ingested import IngestedStore
from app.persistence.portable import PortableRegistry
from app.settings import Settings


def provide_settings(request: Request) -> Settings:
    return request.app.state.settings


def provide_repository(request: Request) -> ArtifactRepository:
    """The shared port: routes read artifacts, links, and evidence through this, not the class."""
    return request.app.state.store


def provide_store(request: Request) -> IngestedStore:
    """The concrete store, for ingestion and fixture-facing helpers."""
    return request.app.state.store


def provide_evaluator(request: Request) -> DeterministicAssuranceEvaluator:
    return request.app.state.evaluator


def provide_providers(request: Request) -> ProviderRegistry:
    return request.app.state.providers


def provide_portable(request: Request) -> PortableRegistry:
    """Portable indexes and imported reports; empty until an explicit index call."""
    return request.app.state.portable


SettingsDep = Annotated[Settings, Depends(provide_settings)]
RepositoryDep = Annotated[ArtifactRepository, Depends(provide_repository)]
StoreDep = Annotated[IngestedStore, Depends(provide_store)]
EvaluatorDep = Annotated[DeterministicAssuranceEvaluator, Depends(provide_evaluator)]
ProvidersDep = Annotated[ProviderRegistry, Depends(provide_providers)]
PortableDep = Annotated[PortableRegistry, Depends(provide_portable)]
