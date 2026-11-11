"""Continuous Traceability Assurance — backend package.

Offline-first: nothing in this package requires a GPU, LLM, embedding service, or
network access. Semantic discovery is reachable only through provider plugins that
must satisfy :class:`app.domain.ports.CandidateDiscovery`.
"""

from app.version import PACKAGE_VERSION, SCHEMA_VERSION

__all__ = ["PACKAGE_VERSION", "SCHEMA_VERSION"]
