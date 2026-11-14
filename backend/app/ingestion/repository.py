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
class TreeEntry:
    """One ``git ls-tree -r -l`` row: a blob, symlink, or submodule at a path."""

    mode: str
    object_type: str
    object_id: str
    path: str
    size: int | None


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

    def list_tree(self, revision: str) -> list[TreeEntry]:
        """Tree entries with mode, object id, and size, in one Git invocation.

        The portable indexer needs the object id (to read blobs without re-resolving paths) and the
        mode (to refuse symlinks and submodules instead of treating them as regular files).
        """
        output = self._run("ls-tree", "-r", "-z", "-l", revision)
        entries: list[TreeEntry] = []
        for record in output.split(b"\0"):
            if not record:
                continue
            header, _, raw_path = record.partition(b"\t")
            fields = header.decode("utf-8", "replace").split()
            if len(fields) < 4:
                raise IngestionError(f"unexpected `git ls-tree` record: {record!r}")
            mode, object_type, object_id = fields[0], fields[1], fields[2]
            size_field = fields[3]
            entries.append(
                TreeEntry(
                    mode=mode,
                    object_type=object_type,
                    object_id=object_id,
                    path=raw_path.decode("utf-8"),
                    size=int(size_field) if size_field.isdigit() else None,
                )
            )
        return sorted(entries, key=lambda entry: entry.path)

    def read_object(self, object_id: str) -> bytes:
        """Exact bytes of a blob object (the content hash is taken over these)."""
        return self._run("cat-file", "blob", object_id)

    def remote_url(self) -> str | None:
        """``remote.origin.url``, or the first configured remote, without failing when absent."""
        try:
            output = self._run("config", "--get", "remote.origin.url")
        except IngestionError:
            return None
        value = output.decode("utf-8", "replace").strip()
        return value or None

    def tags(self) -> dict[str, str]:
        """Lightweight and annotated tags pinned to commits, as ``name -> commit``."""
        output = self._run("for-each-ref", "--format=%(refname:short) %(objectname)", "refs/tags")
        tags: dict[str, str] = {}
        for line in output.decode("utf-8", "replace").splitlines():
            name, _, object_id = line.partition(" ")
            if not name:
                continue
            try:
                tags[name] = self.resolve(name)
            except IngestionError:
                continue
        return tags

    def root_commits(self) -> list[str]:
        """Root commit SHAs, used as a clone-stable identity when no remote is configured."""
        output = self._run("rev-list", "--max-parents=0", "HEAD")
        return [line.strip() for line in output.decode("utf-8", "replace").splitlines() if line]

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
