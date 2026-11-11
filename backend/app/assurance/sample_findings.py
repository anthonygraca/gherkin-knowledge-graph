"""M0 findings source: replay of the reviewed sample findings, not a rule engine.

No rule is evaluated here. The class returns the committed sample response for a baseline
(``fixtures/api-responses/findings.<baseline>.json``), which is generated from the
hand-labeled oracle in ``fixtures/banking-demo/expected/baseline-*.json``.

The deterministic evaluator (AS-01…AS-03, owner C) replaces this class in M1/M2 and is
validated against those same oracle files, so the API contract and the tests do not change
when the implementation does.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.domain.api import FindingsResponse
from app.domain.oracle import BaselineSnapshot, MaterializedFindings
from app.persistence.fixtures import load_model
from app.settings import Settings


@dataclass(frozen=True)
class SampleFindingsSource:
    responses_dir: Path

    @classmethod
    def from_settings(cls, settings: Settings) -> SampleFindingsSource:
        return cls(responses_dir=settings.api_responses_dir)

    def findings(self, resolved: BaselineSnapshot) -> FindingsResponse:
        path = self.responses_dir / f"findings.{resolved.baseline}.json"
        sample = load_model(path, MaterializedFindings)
        if sample.baseline != resolved.baseline:
            raise ValueError(
                f"sample findings file '{path}' is for baseline {sample.baseline!r}, "
                f"expected {resolved.baseline!r}"
            )
        return FindingsResponse(
            schema_version=sample.schema_version,
            baseline=resolved.baseline,
            findings=list(sample.findings),
        )
