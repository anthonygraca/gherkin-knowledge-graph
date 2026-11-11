"""AI-01/AI-04 at the provider level: the fake provider proposes and cannot accept."""

from __future__ import annotations

import pytest

from app.discovery.fake import FakeCandidateDiscovery, compute_index_revision
from app.domain.enums import RelationType
from app.domain.oracle import CandidateIndexFile
from app.domain.ports import CandidateDiscovery
from app.persistence.fixtures import load_model
from app.settings import Settings


@pytest.fixture(scope="module")
def index(fixture_settings: Settings) -> CandidateIndexFile:
    return load_model(fixture_settings.expected_dir / "candidate-links.json", CandidateIndexFile)


@pytest.fixture(scope="module")
def provider(index: CandidateIndexFile) -> FakeCandidateDiscovery:
    return FakeCandidateDiscovery(index)


def test_provider_identity_is_reported(
    provider: FakeCandidateDiscovery, index: CandidateIndexFile
) -> None:
    assert provider.provider_name == index.provider == "fake"
    assert provider.model_version == "fake-fixture-v1"
    assert provider.index_revision == compute_index_revision(index)
    assert provider.index_revision.startswith("sha256:")


def test_provider_satisfies_the_discovery_port(provider: FakeCandidateDiscovery) -> None:
    assert isinstance(provider, CandidateDiscovery)
    assert provider.discover("SCN-003")  # the port is usable, not merely declared


def test_provider_has_no_write_surface() -> None:
    public = {name for name in dir(FakeCandidateDiscovery) if not name.startswith("_")}
    write_like = {
        "accept",
        "approve",
        "reject",
        "record",
        "save",
        "store",
        "write",
        "review",
        "ingest",
        "link",
    }
    assert public.isdisjoint(write_like)
    callable_members = {name for name in public if callable(getattr(FakeCandidateDiscovery, name))}
    assert callable_members == {"discover", "from_fixture"}


def test_discovers_the_likely_implementation_for_a_scenario(
    provider: FakeCandidateDiscovery,
) -> None:
    candidates = provider.discover("SCN-001")
    first = candidates[0]
    assert (first.target_id, first.proposed_relation_type, first.rank) == (
        "CODE-001",
        RelationType.IMPLEMENTED_BY,
        1,
    )
    assert first.discovery_provider == "fake"
    assert first.index_revision == provider.index_revision
    assert first.rationale


def test_candidates_are_ranked_by_score(provider: FakeCandidateDiscovery) -> None:
    candidates = provider.discover("SCN-001")
    assert [candidate.rank for candidate in candidates] == [1, 2]
    scores = [candidate.score for candidate in candidates]
    assert scores == sorted(scores, reverse=True)


def test_top_k_trims_and_renumbers(provider: FakeCandidateDiscovery) -> None:
    assert [candidate.rank for candidate in provider.discover("SCN-001", top_k=1)] == [1]
    assert [candidate.target_id for candidate in provider.discover("SCN-001", top_k=1)] == [
        "CODE-001"
    ]


def test_relation_type_filter(provider: FakeCandidateDiscovery) -> None:
    candidates = provider.discover("SCN-001", relation_types=[RelationType.EXERCISED_BY])
    assert [candidate.target_id for candidate in candidates] == ["TEST-001"]
    assert provider.discover("SCN-001", relation_types=[RelationType.VERIFIED_BY]) == []


def test_unknown_source_returns_no_candidates(provider: FakeCandidateDiscovery) -> None:
    assert provider.discover("REQ-003") == []
    assert provider.discover("SCN-999") == []


def test_top_k_must_be_positive(provider: FakeCandidateDiscovery) -> None:
    with pytest.raises(ValueError):
        provider.discover("SCN-001", top_k=0)


def test_wrong_suggestions_are_returned_rather_than_hidden(
    provider: FakeCandidateDiscovery,
) -> None:
    """A plausible-but-wrong candidate must reach the reviewer; the label is harness metadata."""
    candidates = provider.discover("SCN-002")
    assert [candidate.target_id for candidate in candidates] == ["CODE-001"]


def test_index_revision_tracks_index_content(index: CandidateIndexFile) -> None:
    original = FakeCandidateDiscovery(index)
    mutated = index.model_copy(
        update={
            "candidates": [
                index.candidates[0].model_copy(update={"score": 0.4}),
                *index.candidates[1:],
            ]
        }
    )
    changed = FakeCandidateDiscovery(mutated)
    assert changed.index_revision != original.index_revision
    assert changed.discover("REQ-002")[0].score == 0.4


def test_unknown_relation_type_is_rejected(provider: FakeCandidateDiscovery) -> None:
    with pytest.raises(ValueError):
        provider.discover("SCN-001", relation_types=["refines"])  # type: ignore[list-item]
