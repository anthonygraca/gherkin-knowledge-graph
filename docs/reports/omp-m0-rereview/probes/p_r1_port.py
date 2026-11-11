"""R1 re-check: FixtureStore satisfies ArtifactRepository; a port-only consumer reads data."""

from app.domain.enums import ReviewState
from app.domain.ports import ArtifactRepository
from app.persistence.store import FixtureStore
from app.settings import load_settings

store = FixtureStore.from_settings(load_settings())
print("isinstance(store, ArtifactRepository):", isinstance(store, ArtifactRepository))

for method, args, kwargs in (
    ("get_artifact", ("REQ-001",), {"baseline": "baseline-a"}),
    ("list_links", ("baseline-a",), {"review_state": ReviewState.ACCEPTED}),
    ("changed_artifacts", ("baseline-b", "baseline-a"), {}),
):
    try:
        result = getattr(store, method)(*args, **kwargs)
        shown = [link.link_id for link in result] if method == "list_links" else result
        print(f"{method}{args}: OK -> {shown}")
    except AttributeError as exc:
        print(f"{method}: AttributeError: {exc}")

port: ArtifactRepository = store  # must type-check as the port, not the concrete class
print(
    "port-only reads:",
    port.resolve_baseline(None),
    "|",
    [a.artifact_id for a in port.list_artifacts("baseline-a")],
)
print("evidence:", [e.evidence_id for e in port.list_evidence("baseline-a")])
