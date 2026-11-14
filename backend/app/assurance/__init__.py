"""Assurance (workstream C).

M0 ships no rule engine — only the sample-findings replay used by the mock API and the
severity/rule policy tables in :mod:`app.domain.policy`. Deterministic rules land with
AS-01…AS-03 (C-PR1, M1) against the fixture oracle.
"""

__all__ = ["DeterministicAssuranceEvaluator"]

from app.assurance.rules import DeterministicAssuranceEvaluator  # noqa: E402
