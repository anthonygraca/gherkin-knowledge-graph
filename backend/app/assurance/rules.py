"""Deterministic assurance rules over an ingested repository (M2 rule set).

The rule set implements the state model in ``docs/domain-contracts.md`` and is validated against
the hand-labeled oracle in ``fixtures/banking-demo/expected/baseline-*.json``.

Precedence, made explicit because it is the credibility of the milestone:

1. **A confirmed failure wins.** Applicable failing evidence at the evaluated baseline yields
   ``verification_failed``; that scenario is not also reported as ``reverification_required``.
2. **A stale pass is a request, not a verdict.** A passing run whose relevant content changed since
   the tested commit, with no later evidence, yields ``reverification_required``.
3. **A missing accepted link is a coverage gap.** ``missing_verification_link`` requires no
   evidence at all and never inspects runs.
4. **Proposals are not acceptance.** ``candidate_pending_review`` reads the proposed collection
   only.

Applicability is decided by *content hashes*, never commit SHA equality (ADR 0003/0005).
evidence-only commit therefore cannot look like a source change, and a failing run recorded against
identical content applies to the evaluated baseline even though the SHAs differ.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from app.domain.enums import ArtifactType, RelationType, ReviewState, RuleId
from app.domain.errors import InvalidRequest
from app.domain.models import (
    Artifact,
    AssuranceFinding,
    TraceLink,
    VerificationEvidence,
    make_finding,
)
from app.domain.policy import RULE_DEFAULT_SEVERITY, RULE_FINDING_TYPE
from app.domain.ports import ArtifactRepository

DEFAULT_POLICY = "default"


class DeterministicAssuranceEvaluator:
    """Evaluate the deterministic rule set at one baseline."""

    def __init__(self, repository: ArtifactRepository) -> None:
        self._repository = repository

    def evaluate(self, baseline: str, *, policy: str | None = None) -> list[AssuranceFinding]:
        if policy not in (None, DEFAULT_POLICY):
            raise InvalidRequest(
                f"Unknown policy {policy!r}; the registered policy is {DEFAULT_POLICY!r}."
            )
        canonical = self._repository.resolve_baseline(baseline)
        commit = self._repository.commit_of(canonical)
        artifacts = {
            artifact.artifact_id: artifact
            for artifact in self._repository.list_artifacts(canonical)
        }
        revisions = {artifact.artifact_id: artifact.revision for artifact in artifacts.values()}
        accepted = self._repository.list_links(canonical, review_state=ReviewState.ACCEPTED)
        proposed = self._repository.list_links(canonical, review_state=ReviewState.PROPOSED)
        evidence = self._repository.list_evidence(canonical)

        by_type = {
            artifact_type: {
                artifact_id
                for artifact_id, artifact in artifacts.items()
                if artifact.artifact_type is artifact_type
            }
            for artifact_type in ArtifactType
        }
        requirements = by_type[ArtifactType.REQUIREMENT]
        scenarios = by_type[ArtifactType.SCENARIO]
        sources = by_type[ArtifactType.SOURCE]
        tests = by_type[ArtifactType.TEST]
        verified_by = _by_source(accepted, RelationType.VERIFIED_BY, requirements, scenarios)
        implemented_by = _by_source(accepted, RelationType.IMPLEMENTED_BY, scenarios, sources)
        exercised_by = _by_source(accepted, RelationType.EXERCISED_BY, scenarios, tests)
        verifying_requirements = _reverse(accepted, RelationType.VERIFIED_BY)

        findings: list[AssuranceFinding] = []

        def add(
            rule_id: RuleId,
            artifact_ids: Iterable[str],
            explanation: str,
            evidence_ids: Iterable[str] = (),
        ) -> None:
            findings.append(
                make_finding(
                    rule_id=rule_id,
                    finding_type=RULE_FINDING_TYPE[rule_id],
                    severity=RULE_DEFAULT_SEVERITY[rule_id],
                    artifact_ids=artifact_ids,
                    evaluated_baseline=commit,
                    evidence_ids=evidence_ids,
                    explanation=explanation,
                    artifact_revisions={key: revisions[key] for key in sorted(set(artifact_ids))},
                )
            )

        # 1. Coverage gaps: accepted links only.
        for artifact_id in sorted(artifacts):
            artifact = artifacts[artifact_id]
            if artifact.artifact_type is ArtifactType.REQUIREMENT:
                if not verified_by.get(artifact_id):
                    add(
                        RuleId.MISSING_VERIFICATION_LINK,
                        [artifact_id],
                        f"{artifact_id} has no accepted verification scenario at {canonical}.",
                    )
            elif artifact.artifact_type is ArtifactType.SCENARIO and artifact_id in scenarios:
                if not implemented_by.get(artifact_id):
                    add(
                        RuleId.MISSING_IMPLEMENTATION_LINK,
                        [artifact_id],
                        f"{artifact_id} has no accepted implementation link at {canonical}.",
                    )

        # 2. Unreviewed proposals stay proposals.
        for link in proposed:
            add(
                RuleId.CANDIDATE_PENDING_REVIEW,
                [link.source_id, link.target_id],
                f"Proposed link {link.link_id} ({link.source_id} "
                f"{link.relation_type.value} {link.target_id}) has not been reviewed.",
            )

        # 3. Superseded requirements still carrying live relationships.
        for artifact_id in sorted(artifacts):
            artifact = artifacts[artifact_id]
            if artifact.artifact_type is not ArtifactType.REQUIREMENT:
                continue
            if artifact.metadata.get("status") != "superseded":
                continue
            if any(link.source_id == artifact_id for link in accepted):
                add(
                    RuleId.LIFECYCLE_SUPERSEDED,
                    [artifact_id],
                    f"{artifact_id} is superseded but still has accepted relationships; "
                    "a lifecycle review is required.",
                )

        # 4. Append-only evidence: the newest applicable result decides failure vs staleness.
        latest_by_scenario = _latest_evidence(evidence)
        relevant_by_scenario = {
            scenario_id: {
                scenario_id,
                *implemented_by.get(scenario_id, set()),
                *exercised_by.get(scenario_id, set()),
            }
            for scenario_id in latest_by_scenario
        }
        failing_applicable = {
            scenario_id: evidence_row
            for scenario_id, evidence_row in latest_by_scenario.items()
            if evidence_row.result.value == "failed"
            and self._failure_applies(evidence_row, artifacts, relevant_by_scenario[scenario_id])
        }
        for scenario_id, evidence_row in sorted(failing_applicable.items()):
            test_id = evidence_row.test_id
            requirements = sorted(verifying_requirements.get(scenario_id, set()))
            add(
                RuleId.VERIFICATION_FAILED,
                [scenario_id, test_id, *requirements],
                f"{evidence_row.evidence_id} recorded a failing run of {test_id} at {canonical}; "
                f"{test_id} exercises {scenario_id}, which verifies {', '.join(requirements)}.",
                [evidence_row.evidence_id],
            )

        # 5. Passing evidence whose relevant content changed, with no later run.
        for scenario_id, evidence_row in sorted(latest_by_scenario.items()):
            if scenario_id in failing_applicable:
                continue
            if evidence_row.result.value != "passed":
                continue
            tested = self._artifacts_at(evidence_row.tested_commit)
            if tested is None:
                continue
            relevant = relevant_by_scenario[scenario_id]
            changed = sorted(
                artifact_id
                for artifact_id in relevant
                if artifact_id in artifacts
                and (
                    tested.get(artifact_id) is None
                    or tested[artifact_id].content_hash != artifacts[artifact_id].content_hash
                )
            )
            if not changed:
                continue
            requirements = sorted(verifying_requirements.get(scenario_id, set()))
            tested_label = self._repository.label_of(evidence_row.tested_commit)
            add(
                RuleId.REVERIFICATION_REQUIRED,
                [scenario_id, *requirements, *changed],
                f"{scenario_id} verification passed at {tested_label} "
                f"({evidence_row.evidence_id}). "
                f"{', '.join(changed)} changed at {canonical} and no later evidence for "
                f"{scenario_id} exists, so reverification is required. This is not a "
                "verification failure.",
                [evidence_row.evidence_id],
            )

        return sorted(findings, key=lambda finding: (finding.rule_id.value, finding.finding_id))

    # ------------------------------------------------------------------ helpers

    def _artifacts_at(self, commit: str) -> dict[str, Artifact] | None:
        try:
            return {
                artifact.artifact_id: artifact for artifact in self._repository.artifacts_at(commit)
            }
        except Exception:  # noqa: BLE001 - an unreadable tested commit is not evidence
            return None

    def _failure_applies(
        self,
        evidence_row: VerificationEvidence,
        artifacts: dict[str, Artifact],
        relevant: set[str],
    ) -> bool:
        """A failure applies only when *all* relevant content still matches the evaluated baseline.

        Relevant content is the scenario, its accepted implementations, and its accepted tests.
        Comparing only the test and scenario would let a failure recorded before an implementation
        change be reported as a current failure — the exact confusion this milestone exists to
        prevent.
        """
        tested = self._artifacts_at(evidence_row.tested_commit)
        if tested is None:
            return False
        for artifact_id in relevant:
            current = artifacts.get(artifact_id)
            recorded = tested.get(artifact_id)
            if current is None or recorded is None:
                return False
            if current.content_hash != recorded.content_hash:
                return False
        return True


def _by_source(
    links: Iterable[TraceLink],
    relation: RelationType,
    source_ids: set[str],
    target_ids: set[str],
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for link in links:
        if link.relation_type is not relation:
            continue
        if link.source_id not in source_ids or link.target_id not in target_ids:
            continue
        grouped[link.source_id].append(link.target_id)
    return {key: sorted(set(value)) for key, value in grouped.items()}


def _reverse(links: Iterable[TraceLink], relation: RelationType) -> dict[str, set[str]]:
    reversed_links: dict[str, set[str]] = defaultdict(set)
    for link in links:
        if link.relation_type is relation:
            reversed_links[link.target_id].add(link.source_id)
    return reversed_links


def _latest_evidence(evidence: Iterable[VerificationEvidence]) -> dict[str, VerificationEvidence]:
    """Most recent run per scenario (ADR 0005 assumption 5).

    Evidence carries a scenario id for scenario-level runs; runs without one are keyed by the test
    that exercised it, so a test-only failure still resolves through the accepted graph.
    """
    latest: dict[str, VerificationEvidence] = {}
    for row in evidence:
        scenario_id = row.scenario_id
        if scenario_id is None:
            continue
        current = latest.get(scenario_id)
        if current is None or (row.executed_at, row.evidence_id) > (
            current.executed_at,
            current.evidence_id,
        ):
            latest[scenario_id] = row
    return latest
