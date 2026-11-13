"""Unit tests for the pure artifact-declaration parsers (DT-01)."""

from __future__ import annotations

import pytest

from app.ingestion.errors import IngestionError
from app.ingestion.parsers import parse_annotation, parse_front_matter, parse_scenarios

WHERE = "test:requirements/REQ-900.md"
SOURCE_WHERE = "test:src/accounts.py"


# ---------------------------------------------------------------------------- front matter


def test_front_matter_returns_the_declared_fields() -> None:
    text = "---\nid: REQ-900\ntitle: A stated title\nstatus: active\n---\n\n# Body\n"
    assert parse_front_matter(text, where=WHERE) == {
        "id": "REQ-900",
        "title": "A stated title",
        "status": "active",
    }


def test_front_matter_rejects_a_file_without_a_block() -> None:
    with pytest.raises(IngestionError, match="front matter block at the start"):
        parse_front_matter("# No front matter\n", where=WHERE)


def test_front_matter_rejects_an_unterminated_block() -> None:
    with pytest.raises(IngestionError, match="not terminated"):
        parse_front_matter("---\nid: REQ-900\n", where=WHERE)


def test_front_matter_rejects_an_unusable_line() -> None:
    with pytest.raises(IngestionError, match="not valid YAML"):
        parse_front_matter("---\nid: REQ-900\nnot a pair\n---\n", where=WHERE)


def test_front_matter_rejects_a_duplicate_key() -> None:
    with pytest.raises(IngestionError, match="duplicate front matter key"):
        parse_front_matter("---\nid: REQ-900\nid: REQ-901\n---\n", where=WHERE)


def test_front_matter_parses_quoted_values_and_comments() -> None:
    text = '---\nid: "REQ-900"\ntitle: "A quoted title"\nstatus: superseded # historical\n---\n'
    assert parse_front_matter(text, where=WHERE) == {
        "id": "REQ-900",
        "title": "A quoted title",
        "status": "superseded",
    }


def test_front_matter_rejects_invalid_yaml() -> None:
    with pytest.raises(IngestionError, match="not valid YAML"):
        parse_front_matter('---\nid: REQ-900\ntitle: "unterminated\n---\n', where=WHERE)


def test_front_matter_rejects_non_string_scalars() -> None:
    with pytest.raises(IngestionError, match="must be a string scalar"):
        parse_front_matter("---\nid: REQ-900\nstatus: yes\n---\n", where=WHERE)


def test_front_matter_accepts_crlf_and_a_closing_delimiter_at_eof() -> None:
    crlf = "---\r\nid: REQ-900\r\ntitle: A title\r\n---\r\n"
    assert parse_front_matter(crlf, where=WHERE) == {"id": "REQ-900", "title": "A title"}
    at_eof = "---\nid: REQ-900\ntitle: A title\n---"
    assert parse_front_matter(at_eof, where=WHERE) == {"id": "REQ-900", "title": "A title"}


def test_indented_separator_inside_a_block_scalar_is_content() -> None:
    """R5: a closing delimiter belongs to column 0; indented `---` is scalar content."""
    text = (
        "---\n"
        "id: REQ-900\n"
        "title: |-\n"
        "  Before delimiter\n"
        "  ---\n"
        "  After delimiter\n"
        "status: superseded\n"
        "---\n"
    )
    assert parse_front_matter(text, where=WHERE) == {
        "id": "REQ-900",
        "title": "Before delimiter\n---\nAfter delimiter",
        "status": "superseded",
    }


def test_indented_separator_inside_a_quoted_scalar_is_content() -> None:
    text = '---\nid: REQ-900\ntitle: "Before\n  ---\n  After"\n---\n'
    # Flow scalars fold line breaks to spaces; the indented separator is content, not a boundary.
    assert parse_front_matter(text, where=WHERE)["title"] == "Before --- After"


def test_malformed_yaml_after_an_indented_separator_is_rejected() -> None:
    text = '---\nid: REQ-900\ntitle: |-\n  Before\n  ---\n  After\nbroken: "unterminated\n---\n'
    with pytest.raises(IngestionError, match="not valid YAML"):
        parse_front_matter(text, where=WHERE)


def test_an_indented_opening_delimiter_is_rejected() -> None:
    with pytest.raises(IngestionError, match="front matter block at the start"):
        parse_front_matter("  ---\nid: REQ-900\n---\n", where=WHERE)


def test_control_characters_inside_yaml_are_rejected() -> None:
    """R6: the loader receives the original substring; PyYAML rejects control characters."""
    text = "---\nid: REQ-900\ntitle: |-\n  Before\x0b  After\nstatus: superseded\n---\n"
    with pytest.raises(IngestionError, match="not valid YAML"):
        parse_front_matter(text, where=WHERE)
    with pytest.raises(IngestionError, match="not valid YAML"):
        parse_front_matter(text.replace("\x0b", "\x0c"), where=WHERE)


def test_unicode_line_separator_in_a_quoted_scalar_is_preserved() -> None:
    """R6: U+2028 is YAML content; it must not be split and rejoined as an ASCII newline."""
    text = '---\nid: REQ-900\ntitle: "Before\u2028  After"\n---\n'
    assert parse_front_matter(text, where=WHERE)["title"] == "Before\u2028After"


# ------------------------------------------------------------------------ source/test annotations


def test_annotation_declares_a_source_or_test_identity() -> None:
    assert (
        parse_annotation("# cta:artifact CODE-001\nprint('x')\n", where=SOURCE_WHERE) == "CODE-001"
    )
    assert parse_annotation("# cta:artifact TEST-002\n", where=SOURCE_WHERE) == "TEST-002"


def test_no_annotation_returns_none() -> None:
    text = (
        '"""Documents the annotation convention without declaring one.\n\n'
        "# cta:artifact CODE-001\n"
        '"""\n'
        "VALUE = 1\n"
    )
    assert parse_annotation(text, where=SOURCE_WHERE) is None


def test_annotation_after_the_first_line_is_rejected() -> None:
    with pytest.raises(IngestionError, match="must be the first line"):
        parse_annotation('"""doc"""\n# cta:artifact CODE-001\n', where=SOURCE_WHERE)


def test_a_malformed_first_line_annotation_is_rejected() -> None:
    with pytest.raises(IngestionError, match="must be the first line"):
        parse_annotation("# cta:artifact CODE-1\n", where=SOURCE_WHERE)


def test_a_second_annotation_is_rejected_naming_both_identities() -> None:
    with pytest.raises(IngestionError) as failure:
        parse_annotation("# cta:artifact CODE-001\n# cta:artifact TEST-002\n", where=SOURCE_WHERE)
    message = str(failure.value)
    assert "only one artifact annotation" in message
    assert "CODE-001" in message
    assert "TEST-002" in message


def test_a_requirement_prefix_is_not_a_source_or_test_annotation() -> None:
    with pytest.raises(IngestionError, match="must be the first line"):
        parse_annotation("# cta:artifact REQ-001\n", where=SOURCE_WHERE)


def test_an_annotated_file_may_mention_other_identities_in_strings() -> None:
    text = '# cta:artifact CODE-001\n"""Example:\n# cta:artifact TEST-002\n"""\nVALUE = 1\n'
    assert parse_annotation(text, where=SOURCE_WHERE) == "CODE-001"


def test_a_trailing_comment_is_not_a_declaration() -> None:
    text = "VALUE = 1  # cta:artifact CODE-001\n"
    assert parse_annotation(text, where=SOURCE_WHERE) is None


def test_a_trailing_comment_after_a_valid_declaration_is_ignored() -> None:
    text = "# cta:artifact CODE-001\nVALUE = 1  # cta:artifact TEST-002\n"
    assert parse_annotation(text, where=SOURCE_WHERE) == "CODE-001"


def test_incomplete_tokenization_is_rejected() -> None:
    text = "# cta:artifact CODE-001\nif True:\n    pass\n  pass\n# cta:artifact TEST-002\n"
    with pytest.raises(IngestionError, match="cannot tokenize"):
        parse_annotation(text, where=SOURCE_WHERE)


def test_an_indented_standalone_annotation_is_rejected() -> None:
    text = "# cta:artifact CODE-001\ndef example():\n    # cta:artifact TEST-002\n    pass\n"
    with pytest.raises(IngestionError) as failure:
        parse_annotation(text, where=SOURCE_WHERE)
    message = str(failure.value)
    assert "CODE-001" in message
    assert "TEST-002" in message


def test_a_late_standalone_annotation_is_rejected() -> None:
    text = "VALUE = 1\ndef example():\n    # cta:artifact TEST-002\n    pass\n"
    with pytest.raises(IngestionError, match="first line at column 0"):
        parse_annotation(text, where=SOURCE_WHERE)


# ------------------------------------------------------------------------------- scenarios


def test_scenarios_use_the_tag_as_identity_and_the_line_as_title() -> None:
    text = (
        "Feature: Demo\n\n"
        "  @SCN-901\n"
        "  Scenario: First behaviour\n"
        "    Given a thing\n\n"
        "  @SCN-902\n"
        "  Scenario: Second behaviour\n"
        "    Then another thing\n"
    )
    assert [(item.scenario_id, item.title) for item in parse_scenarios(text, where=WHERE)] == [
        ("SCN-901", "First behaviour"),
        ("SCN-902", "Second behaviour"),
    ]


def test_untagged_scenarios_are_ignored() -> None:
    text = (
        "Feature: Demo\n\n"
        "  Scenario: No identity\n"
        "    Given a thing\n\n"
        "  @SCN-903\n"
        "  Scenario: Tagged\n"
        "    Then another thing\n"
    )
    assert [item.scenario_id for item in parse_scenarios(text, where=WHERE)] == ["SCN-903"]


def test_a_tag_must_be_followed_by_a_scenario_line() -> None:
    text = "Feature: Demo\n\n  @SCN-904\n  Rule: not a scenario\n"
    with pytest.raises(IngestionError, match="tag @SCN-904 is not followed by a 'Scenario:' line"):
        parse_scenarios(text, where=WHERE)


def test_a_new_tag_before_a_scenario_line_is_a_broken_declaration() -> None:
    text = "Feature: Demo\n\n  @SCN-905\n  @SCN-906\n  Scenario: Only one identity\n"
    with pytest.raises(IngestionError, match="tag @SCN-905 is not followed"):
        parse_scenarios(text, where=WHERE)


def test_identity_tag_may_share_a_line_with_non_identity_tags() -> None:
    text = "Feature: Demo\n\n  @smoke @SCN-907 @AC-9.9\n  Scenario: Tagged with friends\n"
    assert [item.scenario_id for item in parse_scenarios(text, where=WHERE)] == ["SCN-907"]


def test_one_scenario_line_cannot_carry_two_identity_tags() -> None:
    text = "Feature: Demo\n\n  @SCN-908 @SCN-909\n  Scenario: Ambiguous identity\n"
    with pytest.raises(IngestionError, match="more than one identity tag"):
        parse_scenarios(text, where=WHERE)


def test_tags_may_be_split_across_lines() -> None:
    text = "Feature: Demo\n\n  @SCN-910\n  @smoke\n  Scenario: Still identified\n"
    assert [item.scenario_id for item in parse_scenarios(text, where=WHERE)] == ["SCN-910"]


def test_tag_before_a_rule_does_not_capture_a_nested_scenario() -> None:
    text = "Feature: Demo\n\n  @SCN-911\n  Rule: Grouping\n    Scenario: Not the tagged scenario\n"
    with pytest.raises(IngestionError, match="tag @SCN-911 is not followed"):
        parse_scenarios(text, where=WHERE)


def test_tag_before_a_scenario_outline_is_rejected_as_unsupported() -> None:
    text = "Feature: Demo\n\n  @SCN-912\n  Scenario Outline: Unsupported form\n"
    with pytest.raises(IngestionError, match="tag @SCN-912 is not followed"):
        parse_scenarios(text, where=WHERE)


def test_doc_string_contents_are_data() -> None:
    text = (
        "Feature: Demo\n\n"
        "  @SCN-913\n"
        "  Scenario: Real behaviour\n"
        "    Given a payload\n"
        '      """\n'
        "      @SCN-999\n"
        "      Scenario: not real\n"
        '      """\n'
    )
    assert [item.scenario_id for item in parse_scenarios(text, where=WHERE)] == ["SCN-913"]


def test_an_unterminated_doc_string_is_rejected() -> None:
    text = (
        "Feature: Demo\n\n"
        "  @SCN-914\n"
        "  Scenario: Real behaviour\n"
        "    Given a payload\n"
        '      """\n'
        "      Scenario: still data\n"
    )
    with pytest.raises(IngestionError, match="doc string .* is not terminated"):
        parse_scenarios(text, where=WHERE)


@pytest.mark.parametrize("opening", ['""""""', "``````"])
def test_a_repeated_delimiter_line_opens_an_unterminated_doc_string(opening: str) -> None:
    """R2 round-2: an opening line is never also its own terminator (Gherkin tokenizer)."""
    text = (
        "Feature: Demo\n\n"
        "  @SCN-920\n"
        "  Scenario: Real behaviour\n"
        "    Given a payload\n"
        f"      {opening}\n"
        "      @SCN-999\n"
        "      Scenario: not real\n"
    )
    with pytest.raises(IngestionError, match="doc string .* is not terminated"):
        parse_scenarios(text, where=WHERE)


def test_a_doc_string_with_a_media_type_opens_and_closes() -> None:
    text = (
        "Feature: Demo\n\n"
        "  @SCN-921\n"
        "  Scenario: Real behaviour\n"
        "    Given a payload\n"
        '      """json\n'
        '      {"ignored": true}\n'
        '      """\n'
    )
    assert [item.scenario_id for item in parse_scenarios(text, where=WHERE)] == ["SCN-921"]


def test_fenced_doc_string_contents_are_data() -> None:
    text = (
        "Feature: Demo\n\n"
        "  @SCN-922\n"
        "  Scenario: Real behaviour\n"
        "    Given a payload\n"
        "      ```text\n"
        "      @SCN-999\n"
        "      Scenario: not real\n"
        "      ```\n"
    )
    assert [item.scenario_id for item in parse_scenarios(text, where=WHERE)] == ["SCN-922"]


def test_a_malformed_identity_token_is_rejected() -> None:
    text = "Feature: Demo\n\n  @SCN-99\n  Scenario: Broken identity\n"
    with pytest.raises(IngestionError, match="@SCN-99"):
        parse_scenarios(text, where=WHERE)


def test_a_malformed_identity_beside_a_valid_one_is_rejected() -> None:
    text = "Feature: Demo\n\n  @SCN-99 @SCN-915\n  Scenario: Broken identity\n"
    with pytest.raises(IngestionError, match="@SCN-99"):
        parse_scenarios(text, where=WHERE)
