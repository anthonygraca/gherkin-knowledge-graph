"""Semantic discovery (workstream A). Online-first concern; M0 ships the fake provider only."""

from app.discovery.fake import FakeCandidateDiscovery, compute_index_revision
from app.discovery.registry import REGISTERED_PROVIDERS, ProviderRegistry

__all__ = [
    "REGISTERED_PROVIDERS",
    "FakeCandidateDiscovery",
    "ProviderRegistry",
    "compute_index_revision",
]
