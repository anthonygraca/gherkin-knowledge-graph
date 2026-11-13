"""Closed vocabularies for the CTA domain contracts.

Every enum here is part of the versioned contract. Adding a member is a MINOR schema
change; removing or renaming a member is MAJOR (docs/domain-contracts.md).
"""

from __future__ import annotations

from enum import StrEnum


class ArtifactType(StrEnum):
    """Kind of engineering artifact under traceability."""

    REQUIREMENT = "requirement"
    SCENARIO = "scenario"
    SOURCE = "source"
    TEST = "test"


class RelationType(StrEnum):
    """Directional relation vocabulary: ``source --relation_type--> target``.

    Only relations that the fixture oracle and the M1/M2 rule engine actually use are
    defined here. New relation types require a schema MINOR bump plus an update to
    docs/domain-contracts.md.
    """

    #: requirement -> scenario. A scenario supplies verification for a requirement.
    VERIFIED_BY = "verified_by"
    #: scenario -> source. A source artifact implements a scenario.
    IMPLEMENTED_BY = "implemented_by"
    #: scenario -> test. A test exercises a scenario.
    EXERCISED_BY = "exercised_by"


class ReviewState(StrEnum):
    """Human review state of a :class:`~app.domain.models.TraceLink`."""

    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ReviewDecision(StrEnum):
    """Input vocabulary for a human review action (``POST /api/links/{link_id}/review``)."""

    ACCEPT = "accept"
    REJECT = "reject"


class EvidenceResult(StrEnum):
    """Outcome of one recorded test execution."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FindingType(StrEnum):
    """Assurance finding vocabulary (labels are defined in the fixture oracle)."""

    MISSING_VERIFICATION_LINK = "missing_verification_link"
    MISSING_IMPLEMENTATION_LINK = "missing_implementation_link"
    REVERIFICATION_REQUIRED = "reverification_required"
    VERIFICATION_FAILED = "verification_failed"
    CANDIDATE_PENDING_REVIEW = "candidate_pending_review"
    LIFECYCLE_REVIEW_REQUIRED = "lifecycle_review_required"


class FindingStatus(StrEnum):
    """Lifecycle of a finding between baselines (used for M4 diffing)."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RuleId(StrEnum):
    """Stable identifiers for deterministic assurance rules."""

    MISSING_VERIFICATION_LINK = "RULE-MISSING-VERIFICATION-LINK"
    MISSING_IMPLEMENTATION_LINK = "RULE-MISSING-IMPLEMENTATION-LINK"
    REVERIFICATION_REQUIRED = "RULE-REVERIFICATION-REQUIRED"
    VERIFICATION_FAILED = "RULE-VERIFICATION-FAILED"
    CANDIDATE_PENDING_REVIEW = "RULE-CANDIDATE-PENDING-REVIEW"
    LIFECYCLE_SUPERSEDED = "RULE-LIFECYCLE-SUPERSEDED"


#: Allowed ``(source type, target type)`` for each relation. Ingestion rejects a link whose
#: artifact types disagree with this table; the vocabulary and direction are the contract
#: (docs/domain-contracts.md), not a convention each consumer re-implements.
RELATION_DIRECTION: dict[RelationType, tuple[ArtifactType, ArtifactType]] = {
    RelationType.VERIFIED_BY: (ArtifactType.REQUIREMENT, ArtifactType.SCENARIO),
    RelationType.IMPLEMENTED_BY: (ArtifactType.SCENARIO, ArtifactType.SOURCE),
    RelationType.EXERCISED_BY: (ArtifactType.SCENARIO, ArtifactType.TEST),
}
