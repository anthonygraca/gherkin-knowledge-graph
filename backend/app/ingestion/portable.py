"""Read-only, annotation-free Gherkin indexing from a pinned Git commit.

Why this exists next to :mod:`app.ingestion.scan`: the M1 scanner enforces CTA's controlled
fixture contract (``@SCN-nnn`` tags, YAML front matter, first-line ``# cta:artifact`` annotations).
That contract is the right thing to keep for the fixture oracle, but it must not be a prerequisite
for indexing a real repository. This module therefore:

* parses with the official Gherkin parser (``gherkin-official``), not a tag-shaped subset;
* reads blobs from one resolved commit, never the working tree;
* derives deterministic, repository-scoped identities and records the strategy;
* returns diagnostics instead of silently dropping files it could not index;
* performs no writes, imports no project code, and runs no hooks or test commands.

The strict and portable paths are selected by the caller; neither weakens the other.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gherkin.errors import CompositeParserException
from gherkin.parser import Parser
from gherkin.token_scanner import TokenScanner

from app.domain.portable import (
    IdentityStrategy,
    PortableCounts,
    PortableDiagnostic,
    PortableFeature,
    PortableScenario,
    PortableScenarioInstance,
    PortableSnapshot,
    PortableStep,
    ScenarioKind,
)
from app.ingestion.errors import IngestionError
from app.ingestion.repository import GitRepository

FEATURE_SUFFIX = ".feature"
PARSER_IDENTITY = "gherkin-official"
REPOSITORY_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


class PortableIndexError(IngestionError):
    """The repository could not be indexed at the requested revision."""


@dataclass(frozen=True)
class IndexLimits:
    """Explicit resource limits so a hostile repository cannot exhaust the indexer."""

    max_feature_bytes: int = 5_000_000
    max_features: int = 2_000
    max_tree_entries: int = 200_000


def _sha256(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _tag_names(node: dict[str, Any]) -> list[str]:
    return sorted({tag["name"] for tag in node.get("tags", [])})


def _text(node: dict[str, Any]) -> str:
    return node.get("name", "")


def _convert_step(
    node: dict[str, Any], *, path: str, repository_id: str, background: bool
) -> PortableStep:
    line = node["location"]["line"]
    data_table = None
    if "dataTable" in node:
        data_table = [
            [cell.get("value", "") for cell in row["cells"]] for row in node["dataTable"]["rows"]
        ]
    doc_string = node.get("docString", {}).get("content")
    return PortableStep(
        step_key=f"{repository_id}:{path}#STEP-L{line}",
        keyword=node["keyword"].strip(),
        text=node["text"],
        line=line,
        column=node["location"]["column"],
        from_background=background,
        doc_string=doc_string,
        data_table=data_table,
    )


def _interpolate(value: str, values: dict[str, str]) -> str:
    for name, replacement in values.items():
        value = value.replace(f"<{name}>", replacement)
    return value


def _instances(
    scenario: dict[str, Any],
    *,
    scenario_key: str,
    repository_id: str,
    path: str,
    name: str,
    steps: list[PortableStep],
) -> list[PortableScenarioInstance]:
    """Expand ``Examples`` rows into concrete case identities (order-preserving)."""
    instances: list[PortableScenarioInstance] = []
    row_number = 0
    for example in scenario.get("examples", []):
        header = [cell.get("value", "") for cell in example.get("tableHeader", {}).get("cells", [])]
        for row in example.get("tableBody", []):
            row_number += 1
            values = {
                column: cell.get("value", "")
                for column, cell in zip(header, row.get("cells", []), strict=True)
            }
            instance_steps = [
                step.model_copy(
                    update={
                        "text": _interpolate(step.text, values),
                        "doc_string": (
                            _interpolate(step.doc_string, values)
                            if step.doc_string is not None
                            else None
                        ),
                        "data_table": (
                            [
                                [_interpolate(cell, values) for cell in row_cells]
                                for row_cells in step.data_table
                            ]
                            if step.data_table is not None
                            else None
                        ),
                    }
                )
                for step in steps
            ]
            suffix = "/".join(values.values()) if values else str(row_number)
            instances.append(
                PortableScenarioInstance(
                    instance_key=f"{scenario_key}/EX-{row_number}",
                    scenario_key=scenario_key,
                    name=f"{name} [{suffix}]",
                    example_row=row_number,
                    example_values=values,
                    steps=instance_steps,
                )
            )
    return instances


def _convert_scenario(
    scenario: dict[str, Any],
    *,
    feature_key: str,
    repository_id: str,
    path: str,
    rule_name: str | None,
    background_steps: list[PortableStep],
) -> PortableScenario:
    line = scenario["location"]["line"]
    scenario_key = f"{repository_id}:{path}#SCN-L{line}"
    kind = (
        ScenarioKind.SCENARIO_OUTLINE
        if scenario.get("keyword", "").strip() == "Scenario Outline"
        else ScenarioKind.SCENARIO
    )
    steps = [
        _convert_step(step, path=path, repository_id=repository_id, background=False)
        for step in scenario.get("steps", [])
    ]
    effective = [*background_steps, *steps] if background_steps else steps
    return PortableScenario(
        scenario_key=scenario_key,
        feature_key=feature_key,
        path=path,
        line=line,
        keyword=scenario.get("keyword", "Scenario").strip(),
        name=_text(scenario),
        description=scenario.get("description", ""),
        tags=_tag_names(scenario),
        rule_name=rule_name,
        kind=kind,
        steps=effective,
        instances=_instances(
            scenario,
            scenario_key=scenario_key,
            repository_id=repository_id,
            path=path,
            name=_text(scenario),
            steps=steps,
        ),
    )


def _convert_feature(
    document: dict[str, Any], *, repository_id: str, path: str, content_hash: str
) -> PortableFeature:
    feature = document["feature"]
    feature_key = f"{repository_id}:{path}"
    feature_background = [
        _convert_step(step, path=path, repository_id=repository_id, background=True)
        for child in feature.get("children", [])
        if "background" in child
        for step in child["background"].get("steps", [])
    ]
    scenarios: list[PortableScenario] = []
    for child in feature.get("children", []):
        if "rule" in child:
            rule = child["rule"]
            rule_background = [
                _convert_step(step, path=path, repository_id=repository_id, background=True)
                for sub in rule.get("children", [])
                if "background" in sub
                for step in sub["background"].get("steps", [])
            ]
            for sub in rule.get("children", []):
                if "scenario" in sub:
                    scenarios.append(
                        _convert_scenario(
                            sub["scenario"],
                            feature_key=feature_key,
                            repository_id=repository_id,
                            path=path,
                            rule_name=_text(rule),
                            background_steps=[*feature_background, *rule_background],
                        )
                    )
            continue
        if "scenario" in child:
            scenarios.append(
                _convert_scenario(
                    child["scenario"],
                    feature_key=feature_key,
                    repository_id=repository_id,
                    path=path,
                    rule_name=None,
                    background_steps=feature_background,
                )
            )
    return PortableFeature(
        feature_key=feature_key,
        path=path,
        line=feature["location"]["line"],
        language=feature.get("language", "en"),
        name=_text(feature),
        description=feature.get("description", ""),
        tags=_tag_names(feature),
        background_steps=feature_background,
        scenarios=scenarios,
        content_hash=content_hash,
    )


def normalize_remote_url(value: str) -> str:
    """Normalize a Git remote URL to ``host/path`` so two clones hash identically."""
    text = value.strip()
    text = re.sub(r"^[a-zA-Z+]+://", "", text)  # strip scheme
    text = text.replace("git@", "", 1)
    text = text.split("@", 1)[-1] if text.count("@") == 1 and ":" in text else text
    text = text.replace(":", "/", 1) if re.match(r"^[^/]+:[^/]", text) else text
    text = text.rstrip("/")
    if text.endswith(".git"):
        text = text[: -len(".git")]
    return text.lower()


def derive_repository_id(root: Path, explicit: str | None) -> tuple[str, IdentityStrategy]:
    """Resolve a stable repository id without trusting the working tree's path."""
    if explicit is not None:
        normalized = explicit.strip().lower()
        if not REPOSITORY_ID_RE.fullmatch(normalized):
            raise PortableIndexError(
                f"repository id {explicit!r} must match {REPOSITORY_ID_RE.pattern}"
            )
        return normalized, IdentityStrategy.EXPLICIT
    repository = GitRepository(root)
    remote = repository.remote_url()
    if remote:
        digest = hashlib.sha256(normalize_remote_url(remote).encode("utf-8")).hexdigest()[:12]
        return f"repo-{digest}", IdentityStrategy.REMOTE_URL
    roots = repository.root_commits()
    if not roots:
        raise PortableIndexError(
            f"{root} has no commits, so no deterministic repository identity can be derived"
        )
    digest = hashlib.sha256(roots[0].encode("utf-8")).hexdigest()[:12]
    return f"repo-{digest}", IdentityStrategy.ROOT_COMMIT


class PortableIndexer:
    """Index one commit of one repository into portable facts."""

    def __init__(self, limits: IndexLimits | None = None) -> None:
        self._limits = limits or IndexLimits()
        self._parser = Parser()

    def index(
        self,
        root: Path,
        *,
        repository_id: str | None = None,
        revision: str | None = None,
    ) -> PortableSnapshot:
        repository = GitRepository(Path(root))
        if not repository.root.is_dir():
            raise PortableIndexError(f"repository path {root} is not a directory")
        try:
            commit = repository.resolve(revision)
            entries = repository.list_tree(commit)
        except IngestionError as exc:
            raise PortableIndexError(str(exc)) from exc
        if len(entries) > self._limits.max_tree_entries:
            raise PortableIndexError(
                f"{root} has {len(entries)} tree entries, above the index limit of "
                f"{self._limits.max_tree_entries}"
            )
        resolved_id, strategy = derive_repository_id(repository.root, repository_id)
        digest = hashlib.sha256()
        features: list[PortableFeature] = []
        diagnostics: list[PortableDiagnostic] = []
        feature_entries = [entry for entry in entries if entry.path.endswith(FEATURE_SUFFIX)]
        if len(feature_entries) > self._limits.max_features:
            raise PortableIndexError(
                f"{root} has {len(feature_entries)} feature files, above the index limit of "
                f"{self._limits.max_features}"
            )
        for entry in entries:
            digest.update(
                f"{entry.mode}\0{entry.object_type}\0{entry.object_id}\0{entry.path}\0".encode()
            )
        for entry in feature_entries:
            if entry.mode == "120000":
                diagnostics.append(
                    PortableDiagnostic(
                        path=entry.path,
                        code="symlink",
                        detail="symlinked feature files are not followed during indexing",
                    )
                )
                continue
            if entry.mode not in ("100644", "100755"):
                diagnostics.append(
                    PortableDiagnostic(
                        path=entry.path,
                        code="unsupported-mode",
                        detail=f"tree entry mode {entry.mode} is not a regular file",
                    )
                )
                continue
            if entry.size is not None and entry.size > self._limits.max_feature_bytes:
                diagnostics.append(
                    PortableDiagnostic(
                        path=entry.path,
                        code="file-too-large",
                        detail=f"{entry.size} bytes exceeds the {self._limits.max_feature_bytes} "
                        "byte feature limit",
                    )
                )
                continue
            try:
                blob = repository.read_object(entry.object_id)
            except IngestionError as exc:
                diagnostics.append(
                    PortableDiagnostic(path=entry.path, code="read-failed", detail=str(exc))
                )
                continue
            if len(blob) > self._limits.max_feature_bytes:
                diagnostics.append(
                    PortableDiagnostic(
                        path=entry.path,
                        code="file-too-large",
                        detail=f"{len(blob)} bytes exceeds the feature limit",
                    )
                )
                continue
            try:
                text = blob.decode("utf-8")
            except UnicodeDecodeError as exc:
                diagnostics.append(
                    PortableDiagnostic(
                        path=entry.path,
                        code="unsupported-encoding",
                        detail=f"feature file is not valid UTF-8: {exc}",
                    )
                )
                continue
            try:
                document = self._parser.parse(TokenScanner(text))
            except CompositeParserException as exc:
                for error in exc.errors:
                    detail = getattr(error, "message", None) or str(error)
                    location = getattr(error, "location", None)
                    line = getattr(location, "line", None)
                    if line is None:
                        match = re.match(r"^\((\d+):\d+\)", detail)
                        line = int(match.group(1)) if match else None
                    diagnostics.append(
                        PortableDiagnostic(
                            path=entry.path,
                            code="invalid-gherkin",
                            detail=detail,
                            line=line,
                        )
                    )
                continue
            except Exception as exc:  # noqa: BLE001 - parser failure must not abort the scan
                diagnostics.append(
                    PortableDiagnostic(
                        path=entry.path,
                        code="invalid-gherkin",
                        detail=str(exc) or type(exc).__name__,
                    )
                )
                continue
            if "feature" not in document:
                diagnostics.append(
                    PortableDiagnostic(
                        path=entry.path,
                        code="invalid-gherkin",
                        detail="file contains no Feature section",
                    )
                )
                continue
            features.append(
                _convert_feature(
                    document,
                    repository_id=resolved_id,
                    path=entry.path,
                    content_hash=_sha256(blob),
                )
            )
        features.sort(key=lambda feature: feature.path)
        return PortableSnapshot(
            repository_id=resolved_id,
            identity_strategy=strategy,
            revision=commit,
            source_digest=_sha256(digest.digest()),
            parser=f"{PARSER_IDENTITY} {_parser_version()}",
            indexed_at=datetime.now(UTC),
            features=features,
            diagnostics=sorted(
                diagnostics, key=lambda item: (item.path, item.line or 0, item.code)
            ),
        )


def _parser_version() -> str:
    from importlib.metadata import version

    return version("gherkin-official")


def summarize(snapshot: PortableSnapshot, *, files_modified: int = 0) -> PortableCounts:
    scenarios = [scenario for feature in snapshot.features for scenario in feature.scenarios]
    return PortableCounts(
        features=len(snapshot.features),
        scenarios=len(scenarios),
        scenario_outlines=sum(1 for s in scenarios if s.kind is ScenarioKind.SCENARIO_OUTLINE),
        example_instances=sum(len(s.instances) for s in scenarios),
        steps=sum(len(feature.background_steps) for feature in snapshot.features)
        + sum(len(scenario.steps) - _background_count(scenario) for scenario in scenarios),
        untagged_scenarios=sum(1 for s in scenarios if not s.tags),
        diagnostics=len(snapshot.diagnostics),
    )


def _background_count(scenario: PortableScenario) -> int:
    return sum(1 for step in scenario.steps if step.from_background)
