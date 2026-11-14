"""Deterministic GraphRAG answer assembly over the existing CTA store (AI-08).

Accepted links define the only traversable graph. Proposed links and semantic code candidates are
kept as separate response fields. Findings come from the M2 evaluator; the answer explains them and
never re-derives policy.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from app.assurance.rules import DeterministicAssuranceEvaluator
from app.discovery.code_index import CodeDiscovery
from app.domain.answers import (
    AnswerReferences,
    AnswerRequest,
    AnswerResponse,
    AnswerStatus,
    EvidenceSummary,
    GraphPath,
)
from app.domain.enums import ArtifactType, RelationType
from app.domain.errors import BaselineNotFound, InvalidRequest
from app.domain.models import Artifact
from app.domain.ports import ArtifactRepository
from app.domain.retrieval import CodeRetrievalRequest, RetrievalMethod

REQUIREMENT_RE = re.compile(r"\bREQ-\d{3}\b")


class AnswerService:
    def __init__(
        self,
        repository: ArtifactRepository,
        *,
        evaluator: DeterministicAssuranceEvaluator | None = None,
        code_discovery: CodeDiscovery | None = None,
    ) -> None:
        self._repository = repository
        self._evaluator = evaluator or DeterministicAssuranceEvaluator(repository)
        self._code = code_discovery

    def answer(self, request: AnswerRequest) -> AnswerResponse:
        try:
            baseline = self._repository.resolve_baseline(request.baseline)
            commit = self._repository.commit_of(baseline)
        except BaselineNotFound as exc:
            return self._failure(request, str(exc), status=AnswerStatus.NOT_FOUND)
        requirement = self._identify(request, baseline)
        if requirement is None:
            return self._failure(
                request,
                "No requirement matched the question; no verification claim is made.",
                status=AnswerStatus.NOT_FOUND,
                baseline=baseline,
                revision=commit,
            )
        thread = (
            self._repository.thread(requirement.artifact_id, baseline=baseline)
            if hasattr(self._repository, "thread")
            else None
        )
        if thread is None:
            raise InvalidRequest("the repository cannot assemble threads for answers")
        accepted = list(thread.accepted_links)
        proposed = list(thread.proposed_links)
        artifacts = list(thread.artifacts)
        evidence = list(thread.evidence)
        scenarios = {
            link.target_id
            for link in accepted
            if link.relation_type is RelationType.VERIFIED_BY
            and link.source_id == requirement.artifact_id
        }
        verified_links = [
            link
            for link in accepted
            if link.relation_type is RelationType.VERIFIED_BY
            and link.source_id == requirement.artifact_id
        ]
        paths = self._paths(requirement.artifact_id, verified_links, accepted, evidence)
        findings = [
            finding
            for finding in self._evaluator.evaluate(baseline)
            if self._finding_relevant(finding.artifact_ids, requirement.artifact_id, scenarios)
        ]
        evidence_state = self._evidence_state(scenarios, evidence, findings)
        answer, status, uncertainties = self._compose(
            requirement,
            baseline,
            scenarios,
            paths,
            evidence,
            findings,
            evidence_state,
            proposed,
        )
        semantic = []
        semantic_method = None
        if request.include_semantic_candidates and scenarios and self._code is not None:
            semantic_method = request.semantic_method or RetrievalMethod.LEXICAL
            for scenario in sorted(scenarios):
                response = self._code.retrieve(
                    CodeRetrievalRequest(
                        artifact_id=scenario,
                        baseline=baseline,
                        top_k=3,
                        method=semantic_method,
                    )
                )
                semantic.extend(response.hits)
                uncertainties.append(
                    "Semantic code candidates are proposals and are not part of the accepted graph."
                )
        references = self._references(
            requirement, artifacts, accepted, evidence, findings, semantic
        )
        return AnswerResponse(
            schema_version=self._schema_version(),
            question=request.question or f"Evidence for {requirement.artifact_id}",
            requirement_id=requirement.artifact_id,
            baseline=baseline,
            revision=commit,
            status=status,
            answer=answer,
            evidence_state=evidence_state,
            accepted_links=accepted,
            proposed_links=proposed,
            artifacts=artifacts,
            evidence=evidence,
            graph_paths=paths,
            findings=findings,
            semantic_candidates=semantic,
            semantic_method=semantic_method,
            references=references,
            explanation_method="deterministic",
            chat_model=None,
            uncertainties=sorted(set(uncertainties)),
        )

    # ------------------------------------------------------------------ helpers

    def _identify(self, request: AnswerRequest, baseline: str) -> Artifact | None:
        if request.requirement_id:
            artifact = self._repository.get_artifact(request.requirement_id, baseline=baseline)
            if artifact.artifact_type is not ArtifactType.REQUIREMENT:
                raise InvalidRequest("answers are rooted at a requirement artifact")
            return artifact
        assert request.question is not None
        candidates = [
            artifact
            for artifact in self._repository.list_artifacts(baseline)
            if artifact.artifact_type is ArtifactType.REQUIREMENT
        ]
        exact = REQUIREMENT_RE.search(request.question)
        if exact is not None:
            return next(
                (artifact for artifact in candidates if artifact.artifact_id == exact.group(0)),
                None,
            )
        tokens = {token.lower() for token in re.findall(r"[A-Za-z]{3,}", request.question)}
        scored = [
            (
                len(tokens.intersection(set(re.findall(r"[A-Za-z]{3,}", artifact.title.lower())))),
                artifact,
            )
            for artifact in candidates
        ]
        scored.sort(key=lambda item: (-item[0], item[1].artifact_id))
        return scored[0][1] if scored and scored[0][0] > 0 else None

    @staticmethod
    def _paths(
        requirement_id: str,
        verified_links,
        accepted,
        evidence,
    ) -> list[GraphPath]:
        paths: list[GraphPath] = []
        for link in verified_links:
            scenario = link.target_id
            paths.append(
                GraphPath(
                    artifact_ids=[requirement_id, scenario],
                    link_ids=[link.link_id],
                    evidence_ids=[
                        row.evidence_id for row in evidence if row.scenario_id == scenario
                    ],
                )
            )
            for child in accepted:
                if child.source_id != scenario:
                    continue
                evidence_ids = [
                    row.evidence_id
                    for row in evidence
                    if row.test_id == child.target_id or row.scenario_id == scenario
                ]
                paths.append(
                    GraphPath(
                        artifact_ids=[requirement_id, scenario, child.target_id],
                        link_ids=[link.link_id, child.link_id],
                        evidence_ids=evidence_ids,
                    )
                )
        return paths

    @staticmethod
    def _finding_relevant(ids: Sequence[str], requirement_id: str, scenarios: set[str]) -> bool:
        return requirement_id in ids or bool(scenarios.intersection(ids))

    @staticmethod
    def _evidence_state(scenarios: set[str], evidence, findings) -> EvidenceSummary:
        """Use M2 precedence: an applicable failure wins; a stale pass is not a failure."""
        finding_types = {finding.finding_type.value for finding in findings}
        if "verification_failed" in finding_types:
            return EvidenceSummary.FAILED
        if "reverification_required" in finding_types:
            return EvidenceSummary.PASSED
        relevant = [row for row in evidence if row.scenario_id in scenarios]
        if not relevant:
            return EvidenceSummary.NONE
        latest: dict[str, object] = {}
        for row in relevant:
            key = row.scenario_id or ""
            current = latest.get(key)
            if current is None or (row.executed_at, row.evidence_id) > (
                current.executed_at,
                current.evidence_id,
            ):
                latest[key] = row
        results = {row.result.value for row in latest.values()}
        if results == {"passed"}:
            return EvidenceSummary.PASSED
        if "failed" in results:
            return EvidenceSummary.UNKNOWN
        return EvidenceSummary.MISSING

    def _compose(
        self,
        requirement: Artifact,
        baseline: str,
        scenarios: set[str],
        paths: list[GraphPath],
        evidence,
        findings,
        evidence_state: EvidenceSummary,
        proposed,
    ) -> tuple[str, AnswerStatus, list[str]]:
        uncertainties = [
            "An accepted link is a graph fact, not proof of requirement satisfaction.",
            "A passing test is a configuration-specific execution result.",
        ]
        if not scenarios:
            proposed_note = (
                " Proposed links remain proposals: "
                f"{', '.join(sorted(link.link_id for link in proposed))}."
                if proposed
                else ""
            )
            return (
                f"{requirement.artifact_id} has no accepted verification scenario at {baseline}. "
                f"No verification claim is made.{proposed_note}",
                AnswerStatus.ABSTAINED,
                uncertainties + ["No accepted verification relationship exists."],
            )
        finding_types = {finding.finding_type.value for finding in findings}
        if "verification_failed" in finding_types:
            failure = next(
                finding
                for finding in findings
                if finding.finding_type.value == "verification_failed"
            )
            failing = failure.evidence_ids
            return (
                f"{requirement.artifact_id} has a recorded failing execution at {baseline} "
                f"({', '.join(sorted(failing))}). The deterministic finding is "
                "verification_failed. "
                "This reports an observed failure, not a reverification request.",
                AnswerStatus.ANSWERED,
                uncertainties,
            )
        if "reverification_required" in finding_types:
            return (
                f"{requirement.artifact_id} has a reverification_required finding at {baseline}: "
                "relevant content changed after the recorded passing evidence. This is not a "
                "verification failure.",
                AnswerStatus.ANSWERED,
                uncertainties,
            )
        if evidence_state is EvidenceSummary.NONE:
            return (
                f"{requirement.artifact_id} has accepted links to {', '.join(sorted(scenarios))} "
                f"at {baseline}, but no execution evidence is recorded. Verification is unknown.",
                AnswerStatus.ABSTAINED,
                uncertainties + ["No execution evidence is recorded for the accepted scenarios."],
            )
        if evidence_state is EvidenceSummary.UNKNOWN:
            return (
                f"{requirement.artifact_id} has accepted links and historical evidence at "
                f"{baseline}, but the latest recorded run does not apply cleanly to this baseline. "
                "Verification is unknown; the historical result is not reported as a current "
                "failure.",
                AnswerStatus.ABSTAINED,
                uncertainties + ["Historical evidence does not apply to the evaluated baseline."],
            )
        return (
            f"{requirement.artifact_id} has an accepted chain at {baseline}: "
            f"{', '.join(sorted({link_id for path in paths for link_id in path.link_ids}))}. "
            "Recorded evidence is "
            f"{evidence_state.value}; this does not establish universal requirement satisfaction.",
            AnswerStatus.ANSWERED,
            uncertainties,
        )

    @staticmethod
    def _references(
        requirement, artifacts, accepted, evidence, findings, semantic
    ) -> AnswerReferences:
        artifact_ids = {requirement.artifact_id}
        link_ids = set()
        evidence_ids = set()
        finding_ids = set()
        for artifact in artifacts:
            artifact_ids.add(artifact.artifact_id)
        for link in accepted:
            link_ids.add(link.link_id)
            artifact_ids.update({link.source_id, link.target_id})
        for row in evidence:
            evidence_ids.add(row.evidence_id)
            artifact_ids.add(row.test_id)
            if row.scenario_id:
                artifact_ids.add(row.scenario_id)
        for finding in findings:
            finding_ids.add(finding.finding_id)
            artifact_ids.update(finding.artifact_ids)
            evidence_ids.update(finding.evidence_ids)
        for hit in semantic:
            artifact_ids.add(hit.artifact_id)
        return AnswerReferences(
            artifact_ids=sorted(artifact_ids),
            link_ids=sorted(link_ids),
            evidence_ids=sorted(evidence_ids),
            finding_ids=sorted(finding_ids),
        )

    def _failure(
        self,
        request: AnswerRequest,
        detail: str,
        *,
        status: AnswerStatus,
        baseline: str | None = None,
        revision: str | None = None,
    ) -> AnswerResponse:
        return AnswerResponse(
            schema_version=self._schema_version(),
            question=request.question or f"Evidence for {request.requirement_id}",
            requirement_id=request.requirement_id,
            baseline=baseline,
            revision=revision,
            status=status,
            answer=detail,
            evidence_state=EvidenceSummary.NONE,
            uncertainties=[detail],
        )

    @staticmethod
    def _schema_version() -> str:
        from app.version import SCHEMA_VERSION

        return SCHEMA_VERSION
