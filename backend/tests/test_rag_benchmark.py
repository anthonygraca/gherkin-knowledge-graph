"""AI-09: claim/finding scoring must reject fabricated success prose."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("evaluate_rag", ROOT / "tools" / "evaluate_rag.py")
evaluate_rag = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(evaluate_rag)


def test_fabricated_success_claim_fails_labeled_tokens() -> None:
    case = {
        "required_answer_tokens": ["verification_failed", "EV-003"],
        "forbidden_answer_tokens": ["reverification_required", "all its tests passed"],
    }
    assert evaluate_rag.answer_claims_match(
        case, "verification_failed due to EV-003; not a reverification request"
    )
    assert not evaluate_rag.answer_claims_match(
        case, "REQ-003 is verified at baseline-b; all its tests passed."
    )


def test_abstention_claim_tokens_are_enforced() -> None:
    case = {
        "required_answer_tokens": ["no accepted verification scenario", "no verification claim"],
        "forbidden_answer_tokens": ["verification_failed"],
    }
    assert evaluate_rag.answer_claims_match(
        case, "REQ-002 has no accepted verification scenario. No verification claim is made."
    )
    assert not evaluate_rag.answer_claims_match(
        case, "REQ-002 has no accepted verification scenario. Verification is failed."
    )
