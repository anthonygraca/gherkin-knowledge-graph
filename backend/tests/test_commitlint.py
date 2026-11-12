"""SETUP-01 (#8): enforce future commit traceability without rewriting legacy history."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import commitlint
import pytest

ISSUE_MAP = """## Features
| F-01 | [#7](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/7) |
## User stories
| SETUP-01 | [#8](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/8) |
| FT-02 | [#19](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/19) |
The closed duplicate #33 must not become an allowed reference.
## Task issues
| Repair | [#5](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/5) |
"""


@pytest.mark.parametrize(
    "message",
    [
        "ci: [issue #8] enforce traceability",
        "fix(contracts): [issue #19] reject invalid proposals\n\nWhy this matters.\n\nRefs #8",
        "test(api/contracts): [issue #5] cover failure\n\nRefs #8, #19",
        "docs: [issue #8] explain the convention\n\nCloses #5",
    ],
)
def test_accepts_issue_linked_messages(message: str) -> None:
    assert commitlint.check_message(message, {5, 8, 19}) == []


@pytest.mark.parametrize(
    "message",
    [
        "ci: enforce traceability\n\nRefs #8",  # Old body-only reference is insufficient.
        "ci: [issue #0] invalid identifier",
        "ci: [issue #08] invalid identifier",
        "ci: [issue #N] placeholder",
        "ci: [issue #8] ",
        "ci(): [issue #8] empty scope",
        "unknown: [issue #8] unsupported type",
        "ci: [#8] wrong reference syntax",
        "ci: [issue #999] unregistered issue",
        "ci: [issue #8] valid subject\n\nRefs #999",
        "ci: [issue #8] valid subject\n\nRefs #8, #N",
        "ci: [issue #8] valid subject\n\nCloses #0",
        "fixup! ci: [issue #8] temporary commit",
        "Merge pull request #8 from example/branch",
        "",
    ],
)
def test_rejects_untraceable_messages(message: str) -> None:
    assert commitlint.check_message(message, {5, 8, 19})


def test_issue_map_accepts_only_story_and_task_entries() -> None:
    assert commitlint.known_issues(ISSUE_MAP) == {5, 8, 19}
    foreign_map = ISSUE_MAP.replace("anthonygraca/gherkin-knowledge-graph", "someone/else")
    with pytest.raises(commitlint.LintError):
        commitlint.known_issues(foreign_map)
    with pytest.raises(commitlint.LintError):
        commitlint.known_issues("missing issue tables")


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def commit(repo: Path, message: str) -> str:
    git(repo, "add", ".")
    git(repo, "commit", "--allow-empty", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def history(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    # Isolate the synthetic history from the developer's signing/hooks/default branch settings.
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "0")
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Commit lint tests")
    git(repo, "config", "user.email", "commitlint@example.invalid")
    git(repo, "config", "commit.gpgsign", "false")
    (repo / "docs").mkdir()
    (repo / commitlint.ISSUE_MAP).write_text(ISSUE_MAP, encoding="utf-8")
    legacy = commit(repo, "legacy message without a reference")
    monkeypatch.setattr(commitlint, "LEGACY_BASELINE", legacy)
    return repo, legacy


def test_grandfathers_legacy_history_but_checks_every_new_commit(history, capsys) -> None:
    repo, legacy = history
    assert commitlint.main(["--repo", str(repo)]) == 0
    bad = commit(repo, "forgot the issue")
    commit(repo, "ci: [issue #8] valid final commit")
    assert commitlint.main(["--repo", str(repo)]) == 1
    errors = capsys.readouterr().err
    assert bad[:12] in errors
    assert legacy[:12] not in errors


def test_pr_range_excludes_diverged_base_and_includes_all_branch_commits(history) -> None:
    repo, legacy = history
    git(repo, "checkout", "-b", "topic")
    first = commit(repo, "ci: [issue #8] topic change")
    second = commit(repo, "test: [issue #8] topic evidence")
    git(repo, "checkout", "main")
    commit(repo, "ci: [issue #8] independent base change")
    assert commitlint.commits_to_check(repo, "topic", "main", legacy) == [first, second]
    assert commitlint.main(["--repo", str(repo), "--base", "main", "--head", "topic"]) == 0


@pytest.mark.parametrize(
    ("merge_message", "expected"),
    [("Merge branch 'topic'", 1), ("chore(merge): [issue #8] integrate the change", 0)],
)
def test_real_merge_commits_must_follow_the_convention(history, merge_message, expected) -> None:
    repo, _ = history
    git(repo, "checkout", "-b", "topic")
    commit(repo, "ci: [issue #8] topic change")
    git(repo, "checkout", "main")
    git(repo, "merge", "--no-ff", "topic", "-m", merge_message)
    assert commitlint.main(["--repo", str(repo)]) == expected


def test_side_branch_failure_is_not_hidden_by_a_valid_merge(history, capsys) -> None:
    repo, _ = history
    git(repo, "checkout", "-b", "topic")
    bad = commit(repo, "unlinked branch change")
    git(repo, "checkout", "main")
    git(repo, "merge", "--no-ff", "topic", "-m", "chore: [issue #8] merge topic")
    assert commitlint.main(["--repo", str(repo)]) == 1
    assert bad[:12] in capsys.readouterr().err


def test_range_uses_issue_map_at_each_commit(history) -> None:
    repo, _ = history
    (repo / commitlint.ISSUE_MAP).write_text(ISSUE_MAP.replace("#19", "#29"), encoding="utf-8")
    commit(repo, "ci: [issue #19] reference absent from this snapshot")
    # A later working-tree edit must not make the bad historical reference pass.
    (repo / commitlint.ISSUE_MAP).write_text(ISSUE_MAP, encoding="utf-8")
    assert commitlint.main(["--repo", str(repo)]) == 1


def test_message_file_can_be_checked_before_commit(history, tmp_path: Path) -> None:
    repo, _ = history
    message = tmp_path / "message.txt"
    message.write_text("ci: [issue #8] lint future commits\n", encoding="utf-8")
    assert commitlint.main(["--repo", str(repo), "--message-file", str(message)]) == 0
    message.write_text("missing reference", encoding="utf-8")
    assert commitlint.main(["--repo", str(repo), "--message-file", str(message)]) == 1


def test_missing_revisions_and_shallow_history_fail_closed(history, tmp_path: Path) -> None:
    repo, _ = history
    assert commitlint.main(["--repo", str(repo), "--head", "missing"]) == 2
    assert commitlint.main(["--repo", str(repo), "--base", "missing"]) == 2
    shallow = tmp_path / "shallow"
    git(repo, "clone", "--depth", "1", repo.as_uri(), str(shallow))
    assert commitlint.main(["--repo", str(shallow)]) == 2
