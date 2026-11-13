"""Deterministic assurance rules over an ingested repository (M1 subset).

Only ``RULE-MISSING-VERIFICATION-LINK`` is implemented in M1. The evaluator is pure with respect
to the repository: it reads artifacts and accepted links, emits findings, and mutates nothing.
Proposals never satisfy verification. The remaining rules arrive with AS-02/AS-03 (M2).
"""

from __future__ import annotations

from app.domain.enums import ArtifactType, RelationType, ReviewState, RuleId
from app.domain.errors import InvalidRequest
from app.domain.models import AssuranceFinding, make_finding
from app.domain.policy import RULE_DEFAULT_SEVERITY, RULE_FINDING_TYPE
from app.domain.ports import ArtifactRepository

DEFAULT_POLICY = "default"


class DeterministicAssuranceEvaluator:
    """Evaluate the M1 rule set at one baseline."""

    def __init__(self, repository: ArtifactRepository) -> None:
        self._repository = repository

    def evaluate(self, baseline: str, *, policy: str | None = None) -> list[AssuranceFinding]:
        if policy not in (None, DEFAULT_POLICY):
            raise InvalidRequest(
                f"Unknown policy {policy!r}; the registered policy is {DEFAULT_POLICY!r}."
            )
        canonical = self._repository.resolve_baseline(baseline)
        commit = self._repository.commit_of(canonical)
        artifacts = self._repository.list_artifacts(canonical)
        accepted = self._repository.list_links(canonical, review_state=ReviewState.ACCEPTED)

        scenarios = {
            artifact.artifact_id
            for artifact in artifacts
            if artifact.artifact_type is ArtifactType.SCENARIO
        }
        verified_requirements = {
            link.source_id
            for link in accepted
            if link.relation_type is RelationType.VERIFIED_BY and link.target_id in scenarios
        }

        findings: list[AssuranceFinding] = []
        for artifact in sorted(artifacts, key=lambda item: item.artifact_id):
            if artifact.artifact_type is not ArtifactType.REQUIREMENT:
                continue
            if artifact.artifact_id in verified_requirements:
                continue
            findings.append(
                make_finding(
                    rule_id=RuleId.MISSING_VERIFICATION_LINK,
                    finding_type=RULE_FINDING_TYPE[RuleId.MISSING_VERIFICATION_LINK],
                    severity=RULE_DEFAULT_SEVERITY[RuleId.MISSING_VERIFICATION_LINK],
                    artifact_ids=[artifact.artifact_id],
                    evaluated_baseline=commit,
                    explanation=(
                        f"{artifact.artifact_id} has no accepted verification scenario at "
                        f"{canonical}."
                    ),
                    artifact_revisions={artifact.artifact_id: artifact.revision},
                )
            )
        return sorted(findings, key=lambda finding: finding.finding_id)
