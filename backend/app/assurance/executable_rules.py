"""Deterministic executability findings over portable data.

These findings answer "can this Gherkin suite execute, and did it?" — never "is the requirement
satisfied?". They are only evaluated when a trusted framework report exists; absence of metadata
produces no finding at all (the query surface says ``NOT_AVAILABLE``).

Precedence and scope:

* ``undefined_step`` / ``ambiguous_step`` describe the framework's own resolution result.
* ``execution_failed`` describes one observed failing scenario instance; it preserves the failing
  step and the execution key.
* Missing execution coverage is reported as counts, not as a defect: an unexecuted scenario has
  unknown status, not a failing one.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.domain.enums import FindingStatus, FindingType, RuleId
from app.domain.executable import ExecutableFinding
from app.domain.models import finding_fingerprint
from app.domain.policy import RULE_DEFAULT_SEVERITY
from app.domain.portable import (
    ExecutionOutcome,
    ScenarioExecutionRecord,
    StepMatchStatus,
    StepResolutionRecord,
)


def evaluate_executable_findings(
    *,
    repository_id: str,
    revision: str,
    resolutions: Iterable[StepResolutionRecord],
    executions: Iterable[ScenarioExecutionRecord],
    definition_paths: dict[str, str],
) -> list[ExecutableFinding]:
    findings: dict[str, ExecutableFinding] = {}

    def add(
        *,
        rule_id: RuleId,
        finding_type: FindingType,
        artifact_keys: list[str],
        execution_keys: list[str],
        explanation: str,
    ) -> None:
        fingerprint = finding_fingerprint(rule_id, finding_type, artifact_keys)
        findings.setdefault(
            fingerprint,
            ExecutableFinding(
                finding_id=fingerprint,
                rule_id=rule_id,
                finding_type=finding_type,
                status=FindingStatus.OPEN,
                severity=RULE_DEFAULT_SEVERITY[rule_id],
                artifact_keys=sorted(set(artifact_keys)),
                evaluated_baseline=revision,
                execution_keys=sorted(set(execution_keys)),
                explanation=explanation,
            ),
        )

    for resolution in resolutions:
        location = f"{resolution.scenario_key} step at {resolution.step_key}"
        if resolution.status is StepMatchStatus.UNDEFINED:
            add(
                rule_id=RuleId.UNDEFINED_STEP,
                finding_type=FindingType.UNDEFINED_STEP,
                artifact_keys=[resolution.scenario_key, resolution.step_key],
                execution_keys=[],
                explanation=(
                    f"The imported {repository_id} report resolved no step definition for "
                    f"{resolution.step_text!r} ({location}). The framework reported the step as "
                    "undefined at this revision."
                ),
            )
        elif resolution.status is StepMatchStatus.AMBIGUOUS:
            paths = ", ".join(
                sorted(definition_paths.get(key, key) for key in resolution.definition_keys)
            )
            add(
                rule_id=RuleId.AMBIGUOUS_STEP,
                finding_type=FindingType.AMBIGUOUS_STEP,
                artifact_keys=[
                    resolution.scenario_key,
                    resolution.step_key,
                    *resolution.definition_keys,
                ],
                execution_keys=[],
                explanation=(
                    f"The imported {repository_id} report resolved {resolution.step_text!r} "
                    f"({location}) to {len(resolution.definition_keys)} step definitions "
                    f"({paths}); the framework reported the step as ambiguous."
                ),
            )

    for execution in executions:
        if execution.outcome is not ExecutionOutcome.FAILED:
            continue
        failing = next(
            (step for step in execution.steps if step.outcome is ExecutionOutcome.FAILED), None
        )
        keys = [execution.scenario_key]
        detail = "no individual step was recorded as failed"
        if failing is not None:
            keys.append(failing.step_key)
            detail = f"step {failing.text!r} at {failing.step_key} failed"
        add(
            rule_id=RuleId.EXECUTION_FAILED,
            finding_type=FindingType.EXECUTION_FAILED,
            artifact_keys=keys,
            execution_keys=[execution.execution_key],
            explanation=(
                f"Execution {execution.execution_key} recorded a failing run of "
                f"{execution.scenario_name!r} at tested commit {execution.tested_commit} "
                f"({detail}). This is an observed scenario failure, not a requirement verdict."
            ),
        )

    return sorted(findings.values(), key=lambda finding: finding.finding_id)
