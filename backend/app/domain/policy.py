"""Severity policy for assurance rules.

Severity is a declared, reviewable policy — not an ad-hoc choice made inside a rule.
The fixture oracle must agree with this table (asserted by
``backend/tests/test_fixture_oracle.py``), so a change here forces a deliberate oracle
update and a contract review.
"""

from __future__ import annotations

from app.domain.enums import FindingType, RuleId, Severity

RULE_DEFAULT_SEVERITY: dict[RuleId, Severity] = {
    RuleId.MISSING_VERIFICATION_LINK: Severity.HIGH,
    RuleId.VERIFICATION_FAILED: Severity.HIGH,
    RuleId.MISSING_IMPLEMENTATION_LINK: Severity.MEDIUM,
    RuleId.REVERIFICATION_REQUIRED: Severity.MEDIUM,
    RuleId.LIFECYCLE_SUPERSEDED: Severity.MEDIUM,
    RuleId.CANDIDATE_PENDING_REVIEW: Severity.LOW,
    RuleId.UNDEFINED_STEP: Severity.HIGH,
    RuleId.AMBIGUOUS_STEP: Severity.HIGH,
    RuleId.EXECUTION_FAILED: Severity.HIGH,
}

#: Rule -> the finding type it emits. Rules emit exactly one finding type.
RULE_FINDING_TYPE: dict[RuleId, FindingType] = {
    RuleId.MISSING_VERIFICATION_LINK: FindingType.MISSING_VERIFICATION_LINK,
    RuleId.MISSING_IMPLEMENTATION_LINK: FindingType.MISSING_IMPLEMENTATION_LINK,
    RuleId.REVERIFICATION_REQUIRED: FindingType.REVERIFICATION_REQUIRED,
    RuleId.VERIFICATION_FAILED: FindingType.VERIFICATION_FAILED,
    RuleId.CANDIDATE_PENDING_REVIEW: FindingType.CANDIDATE_PENDING_REVIEW,
    RuleId.LIFECYCLE_SUPERSEDED: FindingType.LIFECYCLE_REVIEW_REQUIRED,
    RuleId.UNDEFINED_STEP: FindingType.UNDEFINED_STEP,
    RuleId.AMBIGUOUS_STEP: FindingType.AMBIGUOUS_STEP,
    RuleId.EXECUTION_FAILED: FindingType.EXECUTION_FAILED,
}
