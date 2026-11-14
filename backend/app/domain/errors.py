"""Domain errors and their HTTP mapping.

Each error carries a stable ``code``; the API renders ``urn:cta:error:<code>`` as the
RFC 9457 ``type`` (docs/domain-contracts.md).
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for errors that map to a documented API problem document."""

    code = "domain-error"
    title = "Domain error"
    status = 500

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class ArtifactNotFound(DomainError):
    code = "artifact-not-found"
    title = "Artifact not found"
    status = 404


class BaselineNotFound(DomainError):
    code = "baseline-not-found"
    title = "Baseline not found"
    status = 404


class ThreadNotFound(DomainError):
    code = "thread-not-found"
    title = "Thread not found"
    status = 404


class ProviderNotRegistered(DomainError):
    code = "provider-not-registered"
    title = "Discovery provider not registered"
    status = 400


class InvalidRequest(DomainError):
    code = "invalid-request"
    title = "Invalid request"
    status = 400


class FixtureDataMissing(DomainError):
    """A required fixture file is absent — server-side misconfiguration, not client error."""

    code = "fixture-data-missing"
    title = "Fixture data missing"
    status = 500


class FixtureDataInvalid(DomainError):
    """A fixture file exists but violates the contract it claims to implement."""

    code = "fixture-data-invalid"
    title = "Fixture data invalid"
    status = 500


class FeatureNotImplemented(DomainError):
    """Endpoint exists as a contract but its implementation belongs to a later milestone.

    The problem document names the owning story and milestone so callers (and agents)
    never mistake a 501 for a bug or for working behaviour.
    """

    code = "not-implemented"
    title = "Not implemented in this milestone"
    status = 501

    def __init__(self, *, story: str, milestone: str, detail: str) -> None:
        super().__init__(detail)
        self.story = story
        self.milestone = milestone


class RepositoryNotIndexed(DomainError):
    """A portable query named a repository or revision that has not been indexed."""

    code = "repository-not-indexed"
    title = "Repository not indexed"
    status = 404


class ReportNotApplicable(DomainError):
    """A supplied execution report cannot be attributed to the requested repository revision."""

    code = "report-not-applicable"
    title = "Report not applicable"
    status = 400


class ScenarioNotFound(DomainError):
    """A portable query named a scenario key that does not exist at the pinned revision."""

    code = "scenario-not-found"
    title = "Scenario not found"
    status = 404


class RetrievalUnavailable(DomainError):
    """A configured optional retrieval provider could not be used."""

    code = "retrieval-unavailable"
    title = "Retrieval unavailable"
    status = 503
