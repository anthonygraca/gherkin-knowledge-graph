"""Version constants for the CTA package and its contracts."""

PACKAGE_VERSION = "0.1.0"

#: Version of the shared domain/API contract set (models, enums, rule ids, error types).
#:
#: Bump rules (see docs/domain-contracts.md):
#:   MINOR — additive: new optional field, new enum member, new error type, new endpoint.
#:   MAJOR — breaking: removed/renamed field, changed field meaning, changed relation
#:           direction, changed fingerprint inputs.
#: Fixture files carry the value they were generated against; loaders reject mismatches.
SCHEMA_VERSION = "0.1.0"
