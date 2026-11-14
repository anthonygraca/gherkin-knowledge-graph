# M2 assurance metrics

| Measure | Value |
| --- | --- |
| Rules implemented | 6 / 6 |
| Oracle findings baseline-a / baseline-b | 4 / 6 |
| Oracle fields compared | rule, type, severity, artifacts, evidence, explanation, evaluated baseline, revisions, fingerprint |
| Mismatches | 0 |
| New M2 tests | 10 (`test_m2_assurance.py`, including review-1 counterfactuals) |
| Backend suite | 443 passed, 3 opt-in skips |
| Frontend component tests | 13 passed (2 new drill-down tests) |
| Browser demonstrations | 2 findings (reverification, failure), 0 console errors |
| Evidence records preserved | EV-001/EV-002/EV-003, tested commits distinct from the storing commit |
| Change set baseline-a→b | CODE-001, TEST-002; TEST-001 unchanged |
| Impacted accepted links | LNK-002, LNK-006 |
| Schema | 0.3.0 (additive) |
