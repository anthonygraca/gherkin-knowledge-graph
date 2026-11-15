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

    def __init__(
        self,
        detail: str,
        *,
        failed_provider: str | None = None,
        registered: list[str] | None = None,
    ) -> None:
        super().__init__(detail)
        self.failed_provider = failed_provider
        self.registered_providers = registered


class InvalidRequest(DomainError):
    code = "invalid-request"
    title = "Invalid request"
    status = 400


class RequestValidationFailed(DomainError):
    """A semantically invalid request body that is not a Pydantic shape failure."""

    code = "request-validation"
    title = "Request validation failed"
    status = 422


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


class RetrievalSnapshotNotFound(DomainError):
    """No retrieval manifest is published for the requested baseline or binding."""

    code = "retrieval-snapshot-not-found"
    title = "Retrieval snapshot not found"
    status = 404


class MixedIndexContext(DomainError):
    """Candidate batches from different snapshot bindings cannot form one ranked list."""

    code = "mixed-index-context"
    title = "Mixed index context"
    status = 409


class ProviderUnavailable(DomainError):
    """A registered discovery provider failed while executing a request."""

    code = "provider-unavailable"
    title = "Discovery provider unavailable"
    status = 503

    def __init__(self, detail: str, *, failed_provider: str) -> None:
        super().__init__(detail)
        self.failed_provider = failed_provider


class ReviewIdentityUnavailable(DomainError):
    """Review writes are disabled because no operator identity is configured."""

    code = "review-identity-unavailable"
    title = "Review identity unavailable"
    status = 503


class ReviewIdentityMismatch(DomainError):
    """The caller-supplied reviewer does not match the server-assigned operator."""

    code = "review-identity-mismatch"
    title = "Review identity mismatch"
    status = 403


class ReviewLoopbackRequired(DomainError):
    """Review writes are accepted only from a loopback peer."""

    code = "review-loopback-required"
    title = "Loopback review write required"
    status = 403


class ReviewOriginForbidden(DomainError):
    """A browser origin outside the trusted loopback boundary attempted a review write."""

    code = "review-origin-forbidden"
    title = "Review origin forbidden"
    status = 403


class ReviewConflict(DomainError):
    """A terminal decision already exists for the proposal."""

    code = "review-conflict"
    title = "Review conflict"
    status = 409


class ReviewReasonRequired(DomainError):
    """A rejection was supplied without a meaningful reason."""

    code = "review-reason-required"
    title = "Review reason required"
    status = 422


class ProposalInvalid(DomainError):
    """A capture names unknown endpoints or contradicts the relation direction."""

    code = "proposal-invalid"
    title = "Proposal invalid"
    status = 422


class ProposalConflict(DomainError):
    """A different pending snapshot already exists for the same proposal triple."""

    code = "proposal-conflict"
    title = "Proposal conflict"
    status = 409


class ProposalStale(DomainError):
    """Submitted or recorded endpoint content no longer matches the selected baseline."""

    code = "proposal-stale"
    title = "Proposal stale"
    status = 409


class ProposalNotFound(DomainError):
    """No captured or baseline proposal exists for the link id at the selected baseline."""

    code = "proposal-not-found"
    title = "Proposal not found"
    status = 404


class ReviewStorageUnavailable(DomainError):
    """The append-only review journal could not durably store or confirm a record."""

    code = "review-storage-unavailable"
    title = "Review storage unavailable"
    status = 503

    def __init__(self, detail: str, *, durability: str = "not_committed") -> None:
        super().__init__(detail)
        self.durability = durability


class ReportsNotComparable(DomainError):
    """Two assurance reports cannot be compared without inventing a classification."""

    code = "findings-not-comparable"
    title = "Findings not comparable"
    status = 400

    def __init__(self, detail: str, *, invalid_input: str) -> None:
        super().__init__(detail)
        self.invalid_input = invalid_input
