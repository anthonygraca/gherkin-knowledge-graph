"""Append-only review journal and workspace projection (AS-06).

The journal is the source of truth for review decisions. It is application-owned, lives outside
the fixture/evaluated repository, and is written as committed payload/commit pairs so a refused
write cannot silently become an accepted decision after restart. The workspace projects committed
decisions over immutable baseline reads; it never rewrites baseline links, evidence, findings, or
fixture bytes.
"""

from __future__ import annotations

import json
import os
import re
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from app.domain.enums import RELATION_DIRECTION, ArtifactType, ReviewDecision, ReviewState
from app.domain.errors import (
    ArtifactNotFound,
    InvalidRequest,
    ProposalConflict,
    ProposalInvalid,
    ProposalNotFound,
    ProposalStale,
    RequestValidationFailed,
    ReviewConflict,
    ReviewIdentityMismatch,
    ReviewIdentityUnavailable,
    ReviewReasonRequired,
    ReviewStorageUnavailable,
    ThreadNotFound,
)
from app.domain.models import LINK_ID_PATTERN, Artifact, TraceLink
from app.domain.review import (
    JournalCommit,
    JournalPayload,
    LinkProposalResponse,
    ProposalCaptureRequest,
    ProposalRecord,
    ProposalSnapshot,
    ReviewConfigResponse,
    ReviewEvent,
    WorkspaceHistoryResponse,
    WorkspaceProposalsResponse,
    WorkspaceThreadResponse,
    compute_record_digest,
    make_proposal_snapshot,
)
from app.persistence.ingested import IngestedStore
from app.settings import Settings
from app.version import SCHEMA_VERSION


class ReviewJournal:
    """Committed-pair append-only journal with rollback and poison semantics.

    ``_fsync`` and ``_truncate`` are overridable so tests can exercise the failure boundary
    without patching global ``os`` functions. Production uses the real syscalls.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.poison_path = path.with_name(path.name + ".poisoned")
        self._events: list[ReviewEvent] = []
        self._lock = threading.RLock()
        self._uncommitted_tail = False
        self._poisoned = self.poison_path.exists()
        self._committed_offset = 0
        self._replay()

    @property
    def events(self) -> list[ReviewEvent]:
        return list(self._events)

    @property
    def review_revision(self) -> int:
        return len(self._events)

    @property
    def blocked(self) -> str | None:
        if self._poisoned:
            return "journal contains an unconfirmed record; operator reconciliation is required"
        if self._uncommitted_tail:
            return "journal ends with an uncommitted record; truncate it before further writes"
        return None

    # ---------------------------------------------------------------- replay

    def _replay(self) -> None:
        if not self.path.exists():
            return
        raw = self.path.read_bytes()
        if not raw:
            return
        terminated = raw.endswith(b"\n")
        lines = raw.split(b"\n")
        if terminated:
            lines = lines[:-1]
        else:
            # The final segment is an incomplete append, never a committed record.
            self._uncommitted_tail = True
            lines = lines[:-1]

        offset = 0
        index = 0
        while index < len(lines):
            payload_line = lines[index]
            if index + 1 >= len(lines):
                self._uncommitted_tail = True
                break
            commit_line = lines[index + 1]
            try:
                payload_raw = json.loads(payload_line)
                commit_raw = json.loads(commit_line)
            except json.JSONDecodeError as exc:
                if index + 2 >= len(lines) and not terminated:
                    self._uncommitted_tail = True
                    break
                raise ReviewStorageUnavailable(
                    f"Review journal {self.path} contains a malformed committed record: {exc}",
                    durability="indeterminate",
                ) from exc
            if not isinstance(commit_raw, dict) or "commit" not in commit_raw:
                self._uncommitted_tail = True
                break
            try:
                payload = JournalPayload.model_validate(payload_raw)
                commit = JournalCommit.model_validate(commit_raw)
            except ValidationError as exc:
                raise ReviewStorageUnavailable(
                    f"Review journal {self.path} contains an invalid committed record: {exc}",
                    durability="indeterminate",
                ) from exc
            event = payload.event
            if commit.commit != payload.record_digest:
                raise ReviewStorageUnavailable(
                    f"Review journal {self.path} commit marker does not match its payload",
                    durability="indeterminate",
                )
            if compute_record_digest(event) != payload.record_digest:
                raise ReviewStorageUnavailable(
                    f"Review journal {self.path} record digest does not match its event",
                    durability="indeterminate",
                )
            if event.review_revision != len(self._events) + 1:
                raise ReviewStorageUnavailable(
                    f"Review journal {self.path} has a non-contiguous review revision",
                    durability="indeterminate",
                )
            self._events.append(event)
            offset += len(payload_line) + 1 + len(commit_line) + 1
            index += 2
        self._committed_offset = offset

    # ---------------------------------------------------------------- append

    def append(self, event: ReviewEvent) -> None:
        with self._lock:
            blocked = self.blocked
            if blocked is not None:
                raise ReviewStorageUnavailable(
                    blocked,
                    durability="indeterminate" if self._poisoned else "not_committed",
                )
            if event.review_revision != len(self._events) + 1:
                raise ValueError("event review_revision must follow the committed journal")
            payload = JournalPayload(event=event, record_digest=compute_record_digest(event))
            payload_bytes = (payload.model_dump_json() + "\n").encode("utf-8")
            commit_bytes = (
                JournalCommit(commit=payload.record_digest).model_dump_json() + "\n"
            ).encode("utf-8")

            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            except OSError as exc:
                raise ReviewStorageUnavailable(
                    f"Review journal {self.path} cannot be opened: {exc}",
                    durability="not_committed",
                ) from exc

            try:
                before = os.fstat(fd).st_size
                try:
                    _write_all(fd, payload_bytes)
                    self._fsync(fd)
                    _write_all(fd, commit_bytes)
                    self._fsync(fd)
                except OSError as exc:
                    try:
                        self._truncate(fd, before)
                        self._fsync(fd)
                    except OSError:
                        self._poisoned = True
                        try:
                            self.poison_path.write_text(
                                "unconfirmed journal append; reconcile before further writes",
                                encoding="utf-8",
                            )
                        except OSError:
                            pass
                        raise ReviewStorageUnavailable(
                            f"Review journal {self.path} could not confirm durability or roll "
                            f"back: {exc}",
                            durability="indeterminate",
                        ) from exc
                    raise ReviewStorageUnavailable(
                        f"Review journal {self.path} refused the record and rolled back: {exc}",
                        durability="not_committed",
                    ) from exc
            finally:
                os.close(fd)

            self._events.append(event)
            self._committed_offset = before + len(payload_bytes) + len(commit_bytes)

    # ------------------------------------------------------------ overridable

    def _fsync(self, fd: int) -> None:
        os.fsync(fd)

    def _truncate(self, fd: int, size: int) -> None:
        os.ftruncate(fd, size)


def _write_all(fd: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError("short write to review journal")
        view = view[written:]


class ReviewWorkspace:
    """Projects committed review events over immutable baseline facts."""

    def __init__(
        self,
        store: IngestedStore,
        settings: Settings,
        *,
        journal: ReviewJournal | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._settings = settings
        self._journal = journal or ReviewJournal(settings.review_journal)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._lock = threading.RLock()
        self._captures: dict[str, ReviewEvent] = {}
        self._decisions: dict[str, ReviewEvent] = {}
        self._links: dict[str, TraceLink] = {}
        self._snapshots: dict[str, ProposalSnapshot] = {}
        for event in self._journal.events:
            self._apply(event)

    @property
    def review_revision(self) -> int:
        return self._journal.review_revision

    @property
    def operator(self) -> str | None:
        return self._settings.review_operator

    # ---------------------------------------------------------------- config

    def config(self) -> ReviewConfigResponse:
        return ReviewConfigResponse(
            schema_version=SCHEMA_VERSION,
            enabled=self._settings.review_enabled,
            operator=self._settings.review_operator,
            loopback_only=True,
        )

    # --------------------------------------------------------------- capture

    def capture(self, request: ProposalCaptureRequest) -> LinkProposalResponse:
        with self._lock:
            self._require_writable_journal()
            operator = self._require_operator()
            canonical, commit = self._baseline(request.baseline)
            artifacts = {
                artifact.artifact_id: artifact for artifact in self._store.artifacts_at(commit)
            }
            source = artifacts.get(request.source_id)
            target = artifacts.get(request.target_id)
            if source is None or target is None:
                missing = request.source_id if source is None else request.target_id
                raise ProposalInvalid(
                    f"Capture references unknown artifact {missing!r} at {canonical}."
                )
            self._validate_direction(source, target, request)
            if (
                source.content_hash != request.source_content_hash
                or target.content_hash != request.target_content_hash
            ):
                raise ProposalStale(
                    f"Submitted endpoint hashes do not match {canonical} "
                    f"({commit[:12]}). Re-read the artifacts and capture again."
                )

            snapshot = make_proposal_snapshot(
                source_id=request.source_id,
                target_id=request.target_id,
                relation_type=request.relation_type,
                baseline=canonical,
                baseline_commit=commit,
                source_content_hash=source.content_hash,
                target_content_hash=target.content_hash,
                provider=request.provider,
                model_version=request.model_version,
                index_revision=request.index_revision,
                score=request.score,
                rationale=request.rationale,
                captured_at=self._clock(),
            )
            existing = self._proposal_for_triple(
                canonical, request.source_id, request.target_id, request.relation_type
            )
            if existing is not None:
                link_id, existing_snapshot, decided = existing
                if decided:
                    raise ReviewConflict(
                        f"Proposal {link_id} for this relationship already has a terminal "
                        "decision; reopening requires a separately reviewed change."
                    )
                if existing_snapshot is not None and (
                    existing_snapshot.snapshot_digest == snapshot.snapshot_digest
                ):
                    return LinkProposalResponse(
                        schema_version=SCHEMA_VERSION,
                        link=self._links[link_id],
                        snapshot=existing_snapshot,
                        review_revision=self.review_revision,
                        created=False,
                    )
                raise ProposalConflict(
                    f"Proposal {link_id} already exists for this relationship with a different "
                    "snapshot; the existing proposal is unchanged."
                )

            now = self._clock()
            link = TraceLink(
                link_id=self._next_link_id(canonical),
                source_id=request.source_id,
                target_id=request.target_id,
                relation_type=request.relation_type,
                review_state=ReviewState.PROPOSED,
                provenance=self._capture_provenance(request, snapshot, canonical, now, operator),
                created_at=now,
                updated_at=now,
            )
            event = ReviewEvent(
                review_revision=self.review_revision + 1,
                event="proposal_captured",
                recorded_at=now,
                operator=operator,
                baseline=canonical,
                baseline_commit=commit,
                link=link,
                snapshot=snapshot,
                decision=None,
                reason=None,
            )
            self._journal.append(event)
            self._apply(event)
            return LinkProposalResponse(
                schema_version=SCHEMA_VERSION,
                link=link,
                snapshot=snapshot,
                review_revision=self.review_revision,
                created=True,
            )

    # ---------------------------------------------------------------- review

    def review(
        self,
        link_id: str,
        *,
        decision: ReviewDecision,
        reviewer_id: str,
        baseline: str,
        reason: str | None = None,
        reason_present: bool = True,
    ) -> TraceLink:
        with self._lock:
            self._require_writable_journal()
            operator = self._require_operator()
            if reviewer_id != operator:
                raise ReviewIdentityMismatch(
                    f"Reviewer {reviewer_id!r} is not the configured local operator "
                    f"{operator!r}. Review writes are server-assigned."
                )
            canonical, commit = self._baseline(baseline)
            proposal = self._find_proposal(link_id, canonical, commit)
            if proposal is None:
                raise ProposalNotFound(
                    f"No proposal {link_id!r} is captured or declared at {canonical}."
                )
            if decision is ReviewDecision.REJECT:
                if not reason_present or reason is None:
                    raise RequestValidationFailed(
                        "A rejection requires a reason field; an absent or null reason is invalid."
                    )
                if not reason.strip():
                    raise ReviewReasonRequired(
                        "A rejection requires a nonblank reason retained in the decision history."
                    )
            link, snapshot = proposal
            if link_id in self._decisions:
                raise ReviewConflict(
                    f"Proposal {link_id} already has a terminal decision; decisions are "
                    "append-only and cannot be replaced."
                )
            self._require_fresh(snapshot, commit, canonical)

            now = self._clock()
            state = (
                ReviewState.ACCEPTED if decision is ReviewDecision.ACCEPT else ReviewState.REJECTED
            )
            provenance = dict(link.provenance)
            provenance.update(
                {
                    "decision": str(decision),
                    "reviewed_by": operator,
                    "decided_at": now.isoformat(),
                    "review_revision": self.review_revision + 1,
                    "snapshot_digest": snapshot.snapshot_digest,
                    "baseline": canonical,
                    "baseline_commit": commit,
                }
            )
            if reason is not None:
                provenance["reason"] = reason
            decided_link = TraceLink.model_validate(
                {
                    **link.model_dump(mode="python"),
                    "review_state": state,
                    "provenance": provenance,
                    "updated_at": now,
                }
            )
            event = ReviewEvent(
                review_revision=self.review_revision + 1,
                event="decision_recorded",
                recorded_at=now,
                operator=operator,
                baseline=canonical,
                baseline_commit=commit,
                link=decided_link,
                snapshot=snapshot,
                decision=decision,
                reason=reason,
            )
            self._journal.append(event)
            self._apply(event)
            return decided_link

    # ------------------------------------------------------------- reads

    def pending(self, baseline: str | None) -> WorkspaceProposalsResponse:
        canonical, commit = self._baseline(baseline)
        records: list[ProposalRecord] = []
        for link in self._store.list_links(canonical, review_state=ReviewState.PROPOSED):
            if link.link_id in self._decisions:
                continue
            records.append(
                ProposalRecord(
                    link=link,
                    snapshot=self._snapshots.get(link.link_id),
                    binding="captured" if link.link_id in self._snapshots else "legacy",
                )
            )
        for event in self._captures.values():
            link_id = event.link.link_id
            if link_id in self._decisions:
                continue
            if not self._is_current(event.snapshot, commit):
                continue
            records.append(
                ProposalRecord(
                    link=self._links[link_id],
                    snapshot=event.snapshot,
                    binding="captured",
                )
            )
        unique = {record.link.link_id: record for record in records}
        return WorkspaceProposalsResponse(
            schema_version=SCHEMA_VERSION,
            baseline=canonical,
            review_revision=self.review_revision,
            proposals=[unique[key] for key in sorted(unique)],
        )

    def history(self, baseline: str | None) -> WorkspaceHistoryResponse:
        canonical, commit = self._baseline(baseline)
        events = [event for event in self._journal.events if self._applies(event.snapshot, commit)]
        return WorkspaceHistoryResponse(
            schema_version=SCHEMA_VERSION,
            baseline=canonical,
            review_revision=self.review_revision,
            events=events,
        )

    def thread(self, root_id: str, *, baseline: str | None = None) -> WorkspaceThreadResponse:
        canonical, commit = self._baseline(baseline)
        artifacts = self._store.list_artifacts(canonical)
        by_id = {artifact.artifact_id: artifact for artifact in artifacts}
        root = by_id.get(root_id)
        if root is None:
            raise ArtifactNotFound(f"No artifact {root_id!r} at {canonical}.")
        if root.artifact_type is not ArtifactType.REQUIREMENT:
            raise ThreadNotFound(
                f"No thread materialized for {root_id!r} at {canonical}; workspace threads "
                "are rooted at requirements."
            )
        accepted = list(self._store.list_links(canonical, review_state=ReviewState.ACCEPTED))
        proposed: list[TraceLink] = []
        for link in self._store.list_links(canonical, review_state=ReviewState.PROPOSED):
            decision = self._decisions.get(link.link_id)
            if decision is None:
                try:
                    snapshot = self._snapshot_for(link, commit=commit, baseline=canonical)
                except ProposalStale:
                    continue
                if self._is_current(snapshot, commit):
                    proposed.append(link)
                continue
            if not self._applies(decision.snapshot, commit):
                continue
            if decision.decision is ReviewDecision.ACCEPT:
                accepted.append(decision.link)
        for event in self._captures.values():
            link_id = event.link.link_id
            decision = self._decisions.get(link_id)
            if decision is None:
                if self._is_current(event.snapshot, commit):
                    proposed.append(event.link)
                continue
            if not self._applies(decision.snapshot, commit):
                continue
            if decision.decision is ReviewDecision.ACCEPT:
                accepted.append(decision.link)
        accepted = _dedupe_links(accepted)
        accepted_ids = {link.link_id for link in accepted}
        proposed = [link for link in _dedupe_links(proposed) if link.link_id not in accepted_ids]
        # The workspace thread is a review neighbourhood, not a verification traversal: it follows
        # both accepted and proposed links so an accepted decision on a branch that is still a
        # proposal remains visible. The arrays stay partitioned; a consumer walking only
        # accepted_links still cannot reach a branch that is merely proposed.
        accepted_by_source: dict[str, list[TraceLink]] = {}
        proposed_by_source: dict[str, list[TraceLink]] = {}
        for link in accepted:
            accepted_by_source.setdefault(link.source_id, []).append(link)
        for link in proposed:
            proposed_by_source.setdefault(link.source_id, []).append(link)
        visited = {root_id}
        frontier = [root_id]
        while frontier:
            following: list[str] = []
            for artifact_id in frontier:
                for link in [
                    *accepted_by_source.get(artifact_id, []),
                    *proposed_by_source.get(artifact_id, []),
                ]:
                    if link.target_id not in visited:
                        visited.add(link.target_id)
                        following.append(link.target_id)
            frontier = following
        return WorkspaceThreadResponse(
            schema_version=SCHEMA_VERSION,
            root_id=root_id,
            baseline=canonical,
            artifacts=sorted(
                (artifact for artifact in artifacts if artifact.artifact_id in visited),
                key=lambda artifact: artifact.artifact_id,
            ),
            accepted_links=sorted(
                (
                    link
                    for link in accepted
                    if link.source_id in visited and link.target_id in visited
                ),
                key=lambda link: link.link_id,
            ),
            proposed_links=sorted(
                (
                    link
                    for link in proposed
                    if link.source_id in visited or link.target_id in visited
                ),
                key=lambda link: link.link_id,
            ),
            evidence=sorted(
                (
                    run
                    for run in self._store.list_evidence(canonical)
                    if run.scenario_id in visited or run.test_id in visited
                ),
                key=lambda run: run.evidence_id,
            ),
            review_revision=self.review_revision,
        )

    # ------------------------------------------------------------- internals

    def _apply(self, event: ReviewEvent) -> None:
        self._links[event.link.link_id] = event.link
        self._snapshots[event.link.link_id] = event.snapshot
        if event.event == "proposal_captured":
            self._captures[event.link.link_id] = event
        else:
            self._decisions[event.link.link_id] = event

    def _require_operator(self) -> str:
        if self._settings.review_operator is None:
            raise ReviewIdentityUnavailable(
                "Review writes are disabled: no operator identity is configured "
                "(CTA_REVIEW_OPERATOR)."
            )
        return self._settings.review_operator

    def _require_writable_journal(self) -> None:
        blocked = self._journal.blocked
        if blocked is not None:
            raise ReviewStorageUnavailable(
                blocked,
                durability="indeterminate" if "unconfirmed" in blocked else "not_committed",
            )

    def _baseline(self, baseline: str | None) -> tuple[str, str]:
        canonical = self._store.resolve_baseline(baseline)
        return canonical, self._store.commit_of(canonical)

    def _validate_direction(
        self, source: Artifact, target: Artifact, request: ProposalCaptureRequest
    ) -> None:
        expected_source, expected_target = RELATION_DIRECTION[request.relation_type]
        if (source.artifact_type, target.artifact_type) != (expected_source, expected_target):
            raise ProposalInvalid(
                f"Relation {request.relation_type.value!r} must connect "
                f"{expected_source.value} -> {expected_target.value}, got "
                f"{source.artifact_type.value} -> {target.artifact_type.value}."
            )

    def _capture_provenance(
        self,
        request: ProposalCaptureRequest,
        snapshot: ProposalSnapshot,
        canonical: str,
        now: datetime,
        operator: str,
    ) -> dict[str, object]:
        provenance: dict[str, object] = {
            "method": "discovery-proposal",
            "captured_by": operator,
            "captured_at": now.isoformat(),
            "snapshot_digest": snapshot.snapshot_digest,
            "baseline": canonical,
        }
        if request.provider is not None:
            provenance["discovery_provider"] = request.provider
        if request.model_version is not None:
            provenance["model_version"] = request.model_version
        if request.index_revision is not None:
            provenance["index_revision"] = request.index_revision
        if request.score is not None:
            provenance["score"] = request.score
        if request.rationale is not None:
            provenance["note"] = request.rationale
        return provenance

    def _next_link_id(self, baseline: str) -> str:
        used: set[str] = set(self._links)
        used.update(link.link_id for link in self._store.list_links(baseline))
        numbers = [
            int(link_id.removeprefix("LNK-"))
            for link_id in used
            if re.fullmatch(LINK_ID_PATTERN, link_id)
        ]
        next_number = max(numbers, default=0) + 1
        if next_number > 999:
            raise InvalidRequest("The LNK-nnn link id space is exhausted.")
        return f"LNK-{next_number:03d}"

    def _proposal_for_triple(
        self, baseline: str, source_id: str, target_id: str, relation_type
    ) -> tuple[str, ProposalSnapshot | None, bool] | None:
        candidates: list[tuple[str, ProposalSnapshot | None]] = []
        for link in self._store.list_links(baseline, review_state=ReviewState.ACCEPTED):
            if (
                link.source_id == source_id
                and link.target_id == target_id
                and link.relation_type == relation_type
            ):
                return link.link_id, None, True
        for link in self._store.list_links(baseline, review_state=ReviewState.PROPOSED):
            if (
                link.source_id == source_id
                and link.target_id == target_id
                and link.relation_type == relation_type
            ):
                candidates.append((link.link_id, self._snapshots.get(link.link_id)))
        for event in self._captures.values():
            link = event.link
            if event.baseline != baseline:
                continue
            if (
                link.source_id == source_id
                and link.target_id == target_id
                and link.relation_type == relation_type
            ):
                candidates.append((link.link_id, event.snapshot))
        for link_id, snapshot in candidates:
            if link_id in self._decisions:
                return link_id, snapshot, True
        if candidates:
            link_id, snapshot = candidates[0]
            return link_id, snapshot, False
        return None

    def _find_proposal(
        self, link_id: str, canonical: str, commit: str
    ) -> tuple[TraceLink, ProposalSnapshot] | None:
        capture = self._captures.get(link_id)
        if capture is not None:
            return capture.link, capture.snapshot
        for link in self._store.list_links(canonical, review_state=ReviewState.PROPOSED):
            if link.link_id != link_id:
                continue
            snapshot = self._snapshots.get(link_id)
            if snapshot is None:
                snapshot = self._snapshot_for(link, commit=commit, baseline=canonical)
            return link, snapshot
        return None

    def _snapshot_for(self, link: TraceLink, *, commit: str, baseline: str) -> ProposalSnapshot:
        """Derive a legacy snapshot at the selected baseline (never durably until a decision)."""
        artifacts = {
            artifact.artifact_id: artifact for artifact in self._store.artifacts_at(commit)
        }
        source = artifacts.get(link.source_id)
        target = artifacts.get(link.target_id)
        if source is None or target is None:
            raise ProposalStale(
                f"Legacy proposal {link.link_id} endpoints are not both present at "
                f"{baseline} ({commit[:12]})."
            )
        return make_proposal_snapshot(
            source_id=link.source_id,
            target_id=link.target_id,
            relation_type=link.relation_type,
            baseline=baseline,
            baseline_commit=commit,
            source_content_hash=source.content_hash,
            target_content_hash=target.content_hash,
            provider=_optional_str(link.provenance.get("discovery_provider")),
            model_version=_optional_str(link.provenance.get("model_version")),
            index_revision=_optional_str(link.provenance.get("index_revision")),
            score=_optional_float(link.provenance.get("score")),
            rationale=_optional_str(link.provenance.get("note")),
            captured_at=self._clock(),
        )

    def _require_fresh(self, snapshot: ProposalSnapshot, commit: str, canonical: str) -> None:
        artifacts = {
            artifact.artifact_id: artifact for artifact in self._store.artifacts_at(commit)
        }
        source = artifacts.get(snapshot.source_id)
        target = artifacts.get(snapshot.target_id)
        if source is None or target is None:
            raise ProposalStale(
                f"Proposal endpoints are not both present at {canonical} ({commit[:12]})."
            )
        if (
            source.content_hash != snapshot.source_content_hash
            or target.content_hash != snapshot.target_content_hash
        ):
            raise ProposalStale(
                f"Proposal snapshot content no longer matches {canonical} ({commit[:12]}); "
                "re-capture the candidate at the current revision."
            )

    def _endpoint_hashes(self, commit: str, snapshot: ProposalSnapshot) -> tuple[str, str] | None:
        artifacts = {
            artifact.artifact_id: artifact for artifact in self._store.artifacts_at(commit)
        }
        source = artifacts.get(snapshot.source_id)
        target = artifacts.get(snapshot.target_id)
        if source is None or target is None:
            return None
        return source.content_hash, target.content_hash

    def _is_current(self, snapshot: ProposalSnapshot | None, commit: str) -> bool:
        if snapshot is None:
            return True
        if snapshot.baseline_commit == commit:
            return True
        return self._endpoint_hashes(commit, snapshot) == (
            snapshot.source_content_hash,
            snapshot.target_content_hash,
        )

    def _applies(self, snapshot: ProposalSnapshot, commit: str) -> bool:
        return snapshot.baseline_commit == commit or self._endpoint_hashes(commit, snapshot) == (
            snapshot.source_content_hash,
            snapshot.target_content_hash,
        )


def _dedupe_links(links: list[TraceLink]) -> list[TraceLink]:
    by_id: dict[str, TraceLink] = {}
    for link in links:
        by_id[link.link_id] = link
    return [by_id[key] for key in sorted(by_id)]


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _optional_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


__all__ = ["ReviewJournal", "ReviewWorkspace"]
