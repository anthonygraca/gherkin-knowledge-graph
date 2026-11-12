#!/usr/bin/env python3
"""Offline commit format and issue-map validation for SETUP-01 (#8)."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# The last commit before adoption. Never advance this to exempt later failures.
LEGACY_BASELINE = "efa824b5b225db74c7ddba50365dad918d3212cc"
ISSUE_MAP = "docs/traceability-issue-map.md"
ISSUE_URL = "https://github.com/anthonygraca/gherkin-knowledge-graph/issues/"
SUBJECT = re.compile(
    r"(?:feat|fix|docs|test|refactor|chore|ci)"
    r"(?:\([a-z0-9][a-z0-9._/-]*\))?: "
    r"\[issue #(?P<issue>[1-9][0-9]*)\] (?P<description>\S(?:[^\r\n]*\S)?)"
)
REFERENCE = re.compile(r"(?:Refs|Closes) #[1-9][0-9]*(?:, #[1-9][0-9]*)*")
EXPECTED = "<type>[optional scope]: [issue #N] <description>"


class LintError(RuntimeError):
    """Invalid Git range or unavailable traceability input; never silently skip it."""


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise LintError(result.stderr.strip() or f"git {args[0]} failed")
    return result.stdout.rstrip("\n")


def known_issues(markdown: str) -> set[int]:
    """Read the issue column of story/task tables, excluding features and prose."""
    issues: set[int] = set()
    section = ""
    link = re.compile(r"\[#([1-9][0-9]*)\]\(" + re.escape(ISSUE_URL) + r"\1\)")
    for line in markdown.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        if section not in {"User stories", "Task issues"} or not line.startswith("|"):
            continue
        columns = line.split("|")
        if len(columns) > 3 and (match := link.fullmatch(columns[2].strip())):
            issues.add(int(match[1]))
    if not issues:
        raise LintError(f"{ISSUE_MAP} has no recognized story/task issue entries")
    return issues


def check_message(message: str, issues: set[int]) -> list[str]:
    lines = message.splitlines()
    subject = lines[0] if lines else ""
    match = SUBJECT.fullmatch(subject)
    if not match:
        return [f"expected {EXPECTED}; e.g. ci(traceability): [issue #8] lint commits"]
    referenced = {int(match["issue"])}
    errors = []
    for line in lines[1:]:
        if re.match(r"^(?:Refs|Closes)\b", line):
            if not REFERENCE.fullmatch(line):
                errors.append(f"malformed reference line: {line!r}; use Refs #8 or Closes #8")
            else:
                referenced.update(int(number) for number in re.findall(r"#([0-9]+)", line))
    for issue in sorted(referenced - issues):
        errors.append(f"issue #{issue} is not a story/task in {ISSUE_MAP}")
    return errors


def resolve_commit(repo: Path, revision: str) -> str:
    return git(repo, "rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}")


def commits_to_check(repo: Path, head: str, base: str | None, legacy_baseline: str) -> list[str]:
    if git(repo, "rev-parse", "--is-shallow-repository") == "true":
        raise LintError("full Git history is required; fetch with fetch-depth: 0")
    head_sha = resolve_commit(repo, head)
    legacy_sha = resolve_commit(repo, legacy_baseline)
    # Old branches can lint without rewriting history, but must include the adoption baseline.
    if git(repo, "merge-base", legacy_sha, head_sha) != legacy_sha:
        raise LintError("head must contain the adoption baseline; update the branch first")
    exclusions = [legacy_sha]
    if base is not None:
        base_sha = resolve_commit(repo, base)
        if git(repo, "merge-base", legacy_sha, base_sha) != legacy_sha:
            raise LintError("base must contain the adoption baseline")
        # PR bases can diverge from head; exclude their reachable history, not just HEAD~1.
        exclusions.append(base_sha)
    return git(repo, "rev-list", "--reverse", head_sha, "--not", *exclusions).splitlines()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Git repository root")
    parser.add_argument("--base", help="exclude commits already reachable from this PR base")
    parser.add_argument("--head", default="HEAD", help="tip to check (default: HEAD)")
    parser.add_argument(
        "--message-file", type=Path, help="check a proposed message before committing"
    )
    args = parser.parse_args(argv)
    if args.message_file is not None and (args.base is not None or args.head != "HEAD"):
        parser.error("--message-file cannot be combined with a revision range")

    try:
        failures = []
        if args.message_file is not None:
            issues = known_issues((args.repo / ISSUE_MAP).read_text(encoding="utf-8"))
            failures = check_message(args.message_file.read_text(encoding="utf-8"), issues)
            count = 1
        else:
            commits = commits_to_check(args.repo, args.head, args.base, LEGACY_BASELINE)
            count = len(commits)
            for commit in commits:
                # Check the map at the commit being judged, not an unrelated working tree.
                issues = known_issues(git(args.repo, "show", f"{commit}:{ISSUE_MAP}"))
                message = git(args.repo, "show", "-s", "--format=%B", commit)
                failures.extend(
                    f"{commit[:12]}: {error}" for error in check_message(message, issues)
                )
        if failures:
            for failure in failures:
                print(f"commitlint: {failure}", file=sys.stderr)
            return 1
        print(f"commitlint: checked {count} {'message(s)' if args.message_file else 'commit(s)'}")
        return 0
    except (LintError, OSError, UnicodeError) as error:
        print(f"commitlint: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
