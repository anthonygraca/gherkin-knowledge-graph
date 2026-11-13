"""Read-only Git access for ingestion.

Uses the Git CLI — the project's documented prerequisite (roadmap §3, docs/setup.md) — and
reads committed objects, never the working tree. Only the operations ingestion needs are
exposed; there is no write path.

Paths and blob contents are treated as untrusted input: paths come from ``git ls-tree -z`` and
object expressions are terminated with ``--end-of-options`` so a repository cannot smuggle a
command-line option into a revision expression.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.ingestion.errors import IngestionError

GIT_READ_FLAGS = ("-c", "core.autocrlf=false")


@dataclass(frozen=True)
class GitRepository:
    """A repository read at explicit revisions."""

    root: Path

    def resolve(self, revision: str | None = None) -> str:
        """Resolve a revision expression (tag, SHA, branch) to a commit SHA.

        ``None`` selects the repository's current ``HEAD``. An unknown expression raises.
        """
        expression = revision or "HEAD"
        output = self._run("rev-parse", "--verify", "--end-of-options", f"{expression}^{{commit}}")
        return output.decode("utf-8", "replace").strip()

    def list_paths(self, revision: str) -> list[str]:
        """Every file path in the revision's tree, sorted, NUL-delimited for exact names."""
        output = self._run("ls-tree", "-r", "-z", "--name-only", revision)
        paths = [entry.decode("utf-8") for entry in output.split(b"\0") if entry]
        return sorted(paths)

    def read_blob(self, revision: str, path: str) -> bytes:
        """Exact bytes of ``path`` at ``revision`` (the content hash is taken over these)."""
        object_id = (
            self._run("rev-parse", "--verify", "--end-of-options", f"{revision}:{path}")
            .decode("utf-8", "replace")
            .strip()
        )
        return self._run("cat-file", "blob", object_id)

    def _run(self, *args: str) -> bytes:
        try:
            result = subprocess.run(
                ["git", *GIT_READ_FLAGS, *args],
                cwd=self.root,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise IngestionError(
                "git is not installed; ingestion reads committed revisions through the Git CLI"
            ) from exc
        if result.returncode != 0:
            detail = result.stderr.decode("utf-8", "replace").strip() or "no diagnostic output"
            raise IngestionError(f"git {' '.join(args)} failed in {self.root}: {detail}")
        return result.stdout
