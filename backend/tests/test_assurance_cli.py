"""CLI regressions for M4 assurance failure and publication edges."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import assurance
from tests.conftest import BuiltFixture

from app.persistence.ingested import IngestedStore


def _evaluate_args(
    tmp_path: Path, built_fixture: BuiltFixture, baseline: str = "baseline-b", name: str = "report"
):
    return assurance._parser().parse_args(
        [
            "evaluate",
            "--baseline",
            baseline,
            "--fixture-repo",
            str(built_fixture.repo),
            "--report",
            str(tmp_path / f"{name}.json"),
            "--manifest",
            str(tmp_path / f"{name}-manifest.json"),
        ]
    )


def test_unreadable_historical_commit_is_incomplete(
    built_fixture: BuiltFixture, tmp_path: Path
) -> None:
    args = _evaluate_args(tmp_path, built_fixture)
    with patch.object(
        IngestedStore, "artifacts_at", side_effect=OSError("injected historical read failure")
    ):
        assert assurance._evaluate(args) == 2
    report = json.loads((tmp_path / "report.json").read_text("utf-8"))
    assert report["tool_outcome"] == "incomplete"
    assert report["failure_stage"] == "input"
    assert report["failure_code"] == "input-unreadable"
    assert report["findings"] == []
    assert any(
        entry["kind"] == "historical_artifact"
        and entry["available"] is False
        and entry["digest"] is None
        for entry in report["inputs"]
    )


def test_non_utf8_report_is_refused(built_fixture: BuiltFixture, tmp_path: Path, capsys) -> None:
    valid = _evaluate_args(tmp_path, built_fixture, baseline="baseline-a", name="valid")
    assert assurance._evaluate(valid) == 0
    bad = tmp_path / "bad.json"
    bad.write_bytes(b"\xff\xfe\x00{")
    args = assurance._parser().parse_args(
        [
            "diff",
            "--previous",
            str(tmp_path / "valid.json"),
            "--current",
            str(bad),
        ]
    )
    assert assurance._diff(args) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == "findings-not-comparable"
    assert payload["classifications"] is None


def test_diff_publication_failure_returns_two(built_fixture: BuiltFixture, tmp_path: Path) -> None:
    first = _evaluate_args(tmp_path, built_fixture, baseline="baseline-a", name="a")
    second = _evaluate_args(tmp_path, built_fixture, baseline="baseline-b", name="b")
    assert assurance._evaluate(first) == 0
    assert assurance._evaluate(second) == 0
    directory = tmp_path / "summary-dir"
    directory.mkdir()
    args = assurance._parser().parse_args(
        [
            "diff",
            "--previous",
            str(tmp_path / "a.json"),
            "--current",
            str(tmp_path / "b.json"),
            "--summary",
            str(directory),
        ]
    )
    assert assurance._diff(args) == 2
