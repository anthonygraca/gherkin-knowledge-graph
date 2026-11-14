"""Cucumber Messages (NDJSON) adapter for registered definitions, matches, and executions.

The adapter never guesses a match. It reads the framework's own resolution:

* ``stepDefinition`` envelopes give registered definitions and their source locators;
* ``testCase.testSteps[].stepDefinitionIds`` gives the framework's resolution for one concrete
  case (empty = the framework reported the step as undefined; two or more = ambiguous);
* ``testStepFinished`` gives the observed outcome of each executed step.

A missing report is *no evidence*: callers must answer ``UNKNOWN``/``NOT_AVAILABLE`` rather than
inventing undefined-step defects. Runtime-generated message ids are kept as provenance, never used
as engineering artifact identity.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.domain.portable import (
    ExecutionOutcome,
    ScenarioExecutionRecord,
    StepDefinitionRecord,
    StepExecutionRecord,
    StepMatchStatus,
    StepResolutionRecord,
)
from app.ingestion.errors import IngestionError

ADAPTER_NAME = "cucumber-messages"


class CucumberReportError(IngestionError):
    """The supplied report is not a trustworthy Cucumber Messages stream."""


@dataclass(frozen=True)
class CucumberReportData:
    report_uri: str
    report_digest: str
    runtime: str
    protocol_version: str
    adapter: str
    #: ``uri -> sha256:...`` of the feature bytes the run actually parsed. Used to prove the report
    #: applies to the indexed snapshot instead of relabelling an old run with a new commit.
    sources: tuple[tuple[str, str], ...]
    step_definitions: tuple[StepDefinitionRecord, ...]
    resolutions: tuple[StepResolutionRecord, ...]
    executions: tuple[ScenarioExecutionRecord, ...]
    diagnostics: tuple[str, ...]


def _digest(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _definition_key(repository_id: str, uri: str, line: int, pattern: str) -> str:
    suffix = hashlib.sha256(pattern.encode("utf-8")).hexdigest()[:8]
    return f"{repository_id}:{uri}#DEF-L{line}-{suffix}"


def _timestamp(value: dict[str, Any] | None, *, where: str) -> datetime:
    if not value:
        raise CucumberReportError(f"{where}: report has no execution timestamp")
    seconds = value.get("seconds")
    nanos = value.get("nanos", 0)
    if not isinstance(seconds, int):
        raise CucumberReportError(f"{where}: timestamp.seconds is not an integer")
    return datetime.fromtimestamp(seconds + nanos / 1_000_000_000, tz=UTC)


_STATUS = {
    "PASSED": ExecutionOutcome.PASSED,
    "FAILED": ExecutionOutcome.FAILED,
    "SKIPPED": ExecutionOutcome.SKIPPED,
    "PENDING": ExecutionOutcome.PENDING,
    "UNDEFINED": ExecutionOutcome.UNDEFINED,
    "AMBIGUOUS": ExecutionOutcome.AMBIGUOUS,
    "UNKNOWN": ExecutionOutcome.UNKNOWN,
}

_PRIORITY = (
    ExecutionOutcome.FAILED,
    ExecutionOutcome.AMBIGUOUS,
    ExecutionOutcome.UNDEFINED,
    ExecutionOutcome.PENDING,
    ExecutionOutcome.UNKNOWN,
    ExecutionOutcome.SKIPPED,
    ExecutionOutcome.PASSED,
)


class CucumberMessagesAdapter:
    """Parse one NDJSON stream. No filesystem writes; the report is read once."""

    def parse(
        self, report_path: Path, *, repository_id: str, tested_commit: str
    ) -> CucumberReportData:
        try:
            payload = Path(report_path).read_bytes()
        except FileNotFoundError as exc:
            raise CucumberReportError(f"report {report_path} does not exist") from exc
        envelopes: list[dict[str, Any]] = []
        for number, line in enumerate(payload.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                envelope = json.loads(line)
            except json.JSONDecodeError as exc:
                raise CucumberReportError(
                    f"{report_path}:{number}: not valid JSON: {exc.msg}"
                ) from exc
            if not isinstance(envelope, dict):
                raise CucumberReportError(f"{report_path}:{number}: envelope is not an object")
            envelopes.append(envelope)
        if not envelopes:
            raise CucumberReportError(f"{report_path} contains no Cucumber Messages envelopes")

        meta = next((item["meta"] for item in envelopes if "meta" in item), {})
        runtime = "{name} {version}".format(
            name=meta.get("implementation", {}).get("name", "unknown"),
            version=meta.get("implementation", {}).get("version", "unknown"),
        )

        documents: dict[str, dict[str, Any]] = {}
        sources: dict[str, str] = {}
        step_nodes: dict[str, dict[str, Any]] = {}
        scenario_nodes: dict[str, dict[str, Any]] = {}
        example_rows: dict[str, tuple[str, int]] = {}
        definitions: dict[str, StepDefinitionRecord] = {}
        pickles: dict[str, dict[str, Any]] = {}
        test_cases: dict[str, dict[str, Any]] = {}
        started: dict[str, dict[str, Any]] = {}
        step_started: set[tuple[str, str]] = set()
        finished: dict[str, dict[str, Any]] = {}
        test_run_finished: dict[str, Any] | None = None

        for envelope in envelopes:
            if "source" in envelope:
                source = envelope["source"]
                uri = source.get("uri")
                data = source.get("data")
                if not uri or data is None:
                    raise CucumberReportError("source envelope is missing uri or data")
                sources[uri] = _digest(data.encode("utf-8"))
            elif "gherkinDocument" in envelope:
                document = envelope["gherkinDocument"]
                uri = document.get("uri")
                if not uri:
                    raise CucumberReportError("gherkinDocument envelope has no uri")
                documents[uri] = document
                feature = document.get("feature") or {}
                for child in feature.get("children", []):
                    _index_children(
                        child,
                        uri=uri,
                        repository_id=repository_id,
                        step_nodes=step_nodes,
                        scenario_nodes=scenario_nodes,
                        example_rows=example_rows,
                        rule=None,
                    )
            elif "stepDefinition" in envelope:
                definition = envelope["stepDefinition"]
                source = definition.get("sourceReference") or {}
                uri = source.get("uri")
                line = (source.get("location") or {}).get("line")
                pattern = (definition.get("pattern") or {}).get("source")
                if not uri or not line or pattern is None:
                    raise CucumberReportError(
                        "stepDefinition envelope is missing pattern or sourceReference"
                    )
                key = _definition_key(repository_id, uri, line, pattern)
                definitions[definition["id"]] = StepDefinitionRecord(
                    definition_key=key,
                    framework_definition_id=definition["id"],
                    pattern=pattern,
                    pattern_type=(definition.get("pattern") or {}).get("type", "UNKNOWN"),
                    source_path=uri,
                    line=line,
                    runtime=runtime,
                )
            elif "pickle" in envelope:
                pickle = envelope["pickle"]
                pickles[pickle["id"]] = pickle
            elif "testCase" in envelope:
                case = envelope["testCase"]
                test_cases[case["id"]] = case
            elif "testCaseStarted" in envelope:
                item = envelope["testCaseStarted"]
                started[item["id"]] = item
            elif "testStepStarted" in envelope:
                item = envelope["testStepStarted"]
                step_started.add((item["testCaseStartedId"], item["testStepId"]))
            elif "testStepFinished" in envelope:
                item = envelope["testStepFinished"]
                finished[item["testStepId"] + "@" + item["testCaseStartedId"]] = item
            elif "testRunFinished" in envelope:
                test_run_finished = envelope["testRunFinished"]

        if not sources:
            raise CucumberReportError(f"{report_path} contains no source envelopes")
        if not pickles or not test_cases or not started:
            raise CucumberReportError(
                f"{report_path} is not a complete run: pickles={len(pickles)} "
                f"testCases={len(test_cases)} testCaseStarted={len(started)}"
            )
        if test_run_finished is None:
            raise CucumberReportError(f"{report_path} has no testRunFinished envelope")

        resolutions: dict[tuple[str, str | None, str], StepResolutionRecord] = {}
        executions: list[ScenarioExecutionRecord] = []
        diagnostics: list[str] = []

        for case_id, case in test_cases.items():
            pickle = pickles.get(case.get("pickleId", ""))
            if pickle is None:
                raise CucumberReportError(f"testCase {case_id} references an unknown pickle")
            uri = pickle.get("uri", "")
            ast_ids = pickle.get("astNodeIds") or []
            scenario_node = scenario_nodes.get(ast_ids[0]) if ast_ids else None
            if scenario_node is None:
                raise CucumberReportError(
                    f"pickle {pickle['id']} does not reference a known Gherkin scenario node"
                )
            scenario_key = scenario_node["scenario_key"]
            instance_key = None
            if len(ast_ids) > 1 and ast_ids[1] in example_rows:
                instance_key = example_rows[ast_ids[1]][0] + f"/EX-{example_rows[ast_ids[1]][1]}"
            step_lookup = {
                (case_step.get("pickleStepId") or ""): case_step
                for case_step in case.get("testSteps", [])
                if case_step.get("pickleStepId")
            }
            for attempt_id, attempt in started.items():
                if attempt.get("testCaseId") != case_id:
                    continue
                executed_at = _timestamp(attempt.get("timestamp"), where=f"{report_path}:{case_id}")
                step_executions: list[StepExecutionRecord] = []
                outcomes: list[ExecutionOutcome] = []
                incomplete = False
                for step in pickle.get("steps", []):
                    case_step = step_lookup.get(step["id"])
                    if case_step is None:
                        continue
                    node = step_nodes.get((step.get("astNodeIds") or [None])[0])
                    if node is None:
                        diagnostics.append(
                            f"step {step['text']!r} in pickle {pickle['id']} has no "
                            "Gherkin location"
                        )
                        continue
                    definition_ids = case_step.get("stepDefinitionIds") or []
                    known = [definitions[i] for i in definition_ids if i in definitions]
                    if len(known) != len(definition_ids):
                        diagnostics.append(
                            f"step {step['text']!r} matched a definition id absent from the "
                            "report's stepDefinition envelopes"
                        )
                    if not definition_ids:
                        status = StepMatchStatus.UNDEFINED
                    elif len(definition_ids) > 1:
                        status = StepMatchStatus.AMBIGUOUS
                    elif known:
                        status = StepMatchStatus.MATCHED
                    else:
                        status = StepMatchStatus.UNKNOWN
                    key = (scenario_key, instance_key, node["step_key"])
                    resolutions[key] = StepResolutionRecord(
                        scenario_key=scenario_key,
                        instance_key=instance_key,
                        step_key=node["step_key"],
                        step_text=step["text"],
                        status=status,
                        definition_keys=[d.definition_key for d in known],
                    )
                    finished_key = case_step["id"] + "@" + attempt_id
                    result = finished.get(finished_key, {}).get("testStepResult") or {}
                    outcome = _STATUS.get(result.get("status", ""), ExecutionOutcome.UNKNOWN)
                    outcomes.append(outcome)
                    duration = result.get("duration") or {}
                    duration_ms = (
                        duration.get("seconds", 0) * 1000 + duration.get("nanos", 0) / 1_000_000
                        if result
                        else None
                    )
                    step_executions.append(
                        StepExecutionRecord(
                            step_key=node["step_key"],
                            text=step["text"],
                            outcome=outcome,
                            definition_keys=[d.definition_key for d in known],
                            duration_ms=round(duration_ms, 3) if duration_ms is not None else None,
                        )
                    )
                # Hook outcomes decide the scenario result too: a failing After hook fails the
                # scenario even when every Gherkin step passed. A missing result is incomplete,
                # not a pass.
                for case_step in case.get("testSteps", []):
                    result = finished.get(case_step["id"] + "@" + attempt_id)
                    if result is None:
                        incomplete = True
                        continue
                    outcomes.append(
                        _STATUS.get(
                            (result.get("testStepResult") or {}).get("status", ""),
                            ExecutionOutcome.UNKNOWN,
                        )
                    )
                overall = (
                    ExecutionOutcome.UNKNOWN
                    if incomplete
                    else next(
                        (candidate for candidate in _PRIORITY if candidate in outcomes),
                        ExecutionOutcome.UNKNOWN,
                    )
                )
                executions.append(
                    ScenarioExecutionRecord(
                        execution_key=(
                            f"{repository_id}:{tested_commit[:12]}:"
                            f"{_digest(payload)[7:19]}:{attempt_id}"
                        ),
                        scenario_key=scenario_key,
                        instance_key=instance_key,
                        scenario_name=pickle.get("name") or scenario_node["name"],
                        feature_path=uri,
                        outcome=overall,
                        tested_commit=tested_commit,
                        executed_at=executed_at,
                        runtime=runtime,
                        report_uri=str(report_path),
                        report_digest=_digest(payload),
                        steps=step_executions,
                    )
                )
                if not step_executions:
                    diagnostics.append(f"attempt {attempt_id} produced no step executions")
        executions.sort(key=lambda item: (item.scenario_key, item.executed_at, item.execution_key))
        return CucumberReportData(
            report_uri=str(report_path),
            report_digest=_digest(payload),
            runtime=runtime,
            protocol_version=meta.get("protocolVersion", "unknown"),
            adapter=ADAPTER_NAME,
            sources=tuple(sorted(sources.items())),
            step_definitions=tuple(sorted(definitions.values(), key=lambda d: d.definition_key)),
            resolutions=tuple(
                sorted(
                    resolutions.values(),
                    key=lambda r: (r.scenario_key, r.instance_key or "", r.step_key),
                )
            ),
            executions=tuple(executions),
            diagnostics=tuple(sorted(set(diagnostics))),
        )


def _index_children(
    child: dict[str, Any],
    *,
    uri: str,
    repository_id: str,
    step_nodes: dict[str, dict[str, Any]],
    scenario_nodes: dict[str, dict[str, Any]],
    example_rows: dict[str, tuple[str, int]],
    rule: dict[str, Any] | None,
) -> None:
    if "background" in child:
        _index_steps(
            child["background"].get("steps", []),
            uri=uri,
            repository_id=repository_id,
            step_nodes=step_nodes,
        )
        return
    if "rule" in child:
        nested = child["rule"]
        for sub in nested.get("children", []):
            _index_children(
                sub,
                uri=uri,
                repository_id=repository_id,
                step_nodes=step_nodes,
                scenario_nodes=scenario_nodes,
                example_rows=example_rows,
                rule=nested,
            )
        return
    if "scenario" not in child:
        return
    scenario = child["scenario"]
    line = scenario["location"]["line"]
    scenario_key = f"{repository_id}:{uri}#SCN-L{line}"
    scenario_nodes[scenario["id"]] = {
        "scenario_key": scenario_key,
        "name": scenario.get("name", ""),
        "uri": uri,
    }
    _index_steps(
        scenario.get("steps", []),
        uri=uri,
        repository_id=repository_id,
        step_nodes=step_nodes,
    )
    row_index = 0
    for example in scenario.get("examples", []):
        for row in example.get("tableBody", []):
            row_index += 1
            example_rows[row["id"]] = (scenario_key, row_index)


def _index_steps(
    steps: list[dict[str, Any]],
    *,
    uri: str,
    repository_id: str,
    step_nodes: dict[str, dict[str, Any]],
) -> None:
    for step in steps:
        step_nodes[step["id"]] = {
            "step_key": f"{repository_id}:{uri}#STEP-L{step['location']['line']}",
            "text": step.get("text", ""),
        }
