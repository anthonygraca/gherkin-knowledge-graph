"""Pure text parsers for artifact declarations.

Declaration conventions are defined in ``docs/domain-contracts.md``:

* requirement: YAML front matter with ``id:`` and ``title:`` in ``requirements/*.md``;
* scenario: an ``@SCN-nnn`` tag immediately preceding the Gherkin ``Scenario:`` line.

Parsers are pure functions over text so malformed-input behaviour is testable without Git, and
they never guess: an unrecognizable declaration raises :class:`IngestionError` rather than
producing a partial result.

Lexing rules that matter (each exists because a review probe broke a looser rule):

* Front-matter boundaries are ``---`` lines at column 0. The YAML document is the **exact original
  substring** between them — it is never split and rejoined, so control characters, Unicode line
  separators, and CRLF reach PyYAML unchanged. PyYAML is the authority on YAML validity.
* Gherkin lines are split on LF only; a trailing CR is removed. No other character is treated as
  a line boundary.
* Only string scalars are accepted for front matter, matching the requirement schema.
"""

from __future__ import annotations

import io
import re
import tokenize
from dataclasses import dataclass
from typing import Any

import yaml

from app.ingestion.errors import IngestionError

SCENARIO_ID_RE = re.compile(r"SCN-\d{3}")
SCENARIO_LINE_RE = re.compile(r"^[ \t]*Scenario:[ \t]*(?P<title>\S.*?)[ \t]*$")
ANNOTATION_RE = re.compile(r"^#\s*cta:artifact\s+(?P<id>(?:CODE|TEST)-\d{3})\s*$")
ANNOTATION_ATTEMPT_RE = re.compile(r"^\s*#\s*cta:artifact\b")
DOC_STRING_DELIMITERS = ('"""', "```")

INDENT = " \t"
LINE_END = " \t\r"


@dataclass(frozen=True)
class ScenarioDeclaration:
    """One tagged scenario found in a feature file."""

    scenario_id: str
    title: str


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys instead of overwriting them."""


def _construct_mapping(
    loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise IngestionError(f"front matter keys must be strings, got {key!r}")
        if key in mapping:
            raise IngestionError(f"duplicate front matter key {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def parse_front_matter(text: str, *, where: str) -> dict[str, str]:
    """Return the top-level string fields of a leading YAML front matter block.

    Delimiters are recognized only as column-0 ``---`` lines; an indented ``---`` belongs to the
    YAML content. The payload is sliced from the original text, preserving every character, so the
    document PyYAML validates is the document the repository contains.
    """
    first_newline = text.find("\n")
    if first_newline == -1:
        raise IngestionError(
            f"{where}: expected a '---' front matter block at the start of the file"
        )
    if text[:first_newline].rstrip("\r") != "---":
        raise IngestionError(
            f"{where}: expected a '---' front matter block at the start of the file"
        )

    payload_start = first_newline + 1
    position = payload_start
    payload: str | None = None
    while position <= len(text):
        newline = text.find("\n", position)
        line_end = len(text) if newline == -1 else newline
        if text[position:line_end].rstrip("\r") == "---":
            payload = text[payload_start:position]
            break
        if newline == -1:
            break
        position = newline + 1
    if payload is None:
        raise IngestionError(f"{where}: front matter block is not terminated by '---'")

    try:
        parsed = yaml.load(payload, Loader=_UniqueKeyLoader)
    except IngestionError as exc:
        raise IngestionError(f"{where}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise IngestionError(f"{where}: front matter is not valid YAML: {exc}") from exc

    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise IngestionError(f"{where}: front matter must be a YAML mapping")
    fields: dict[str, str] = {}
    for key, value in parsed.items():
        if not isinstance(value, str):
            raise IngestionError(
                f"{where}: front matter key {key!r} must be a string scalar "
                f"(quote values that YAML would read as numbers or booleans)"
            )
        fields[key] = value
    return fields


def parse_scenarios(text: str, *, where: str) -> list[ScenarioDeclaration]:
    """Return the scenarios declared with an ``@SCN-nnn`` tag, in file order.

    Only a ``Scenario:`` line directly after the tag (blank lines, comment lines, and additional
    non-identity tags are allowed) consumes the identity. Any other declaration — ``Rule:``,
    ``Scenario Outline:``, a step, a doc string — leaves the tag dangling and is an error, so an
    identity can never attach to an unrelated scenario. Doc-string contents are data: tags and
    ``Scenario:`` text inside them are ignored.
    """
    found: list[ScenarioDeclaration] = []
    pending: str | None = None
    in_doc_string = False
    doc_delimiter = ""

    for raw_line in text.split("\n"):
        line = raw_line.rstrip("\r")
        stripped = line.strip(INDENT)
        if in_doc_string:
            if stripped == doc_delimiter:
                in_doc_string = False
            continue
        if stripped.startswith(DOC_STRING_DELIMITERS):
            if pending is not None:
                raise IngestionError(
                    f"{where}: tag @{pending} is not followed by a 'Scenario:' line"
                )
            doc_delimiter = '"""' if stripped.startswith('"""') else "```"
            in_doc_string = True
            continue
        if not stripped or stripped.startswith("#"):
            continue
        if line.lstrip(INDENT).startswith("@"):
            identities = _identity_tokens(stripped, where=where)
            if len(identities) > 1:
                raise IngestionError(
                    f"{where}: a scenario tag line carries more than one identity tag: "
                    f"{', '.join(identities)}"
                )
            if identities:
                if pending is not None:
                    raise IngestionError(
                        f"{where}: tag @{pending} is not followed by a 'Scenario:' line"
                    )
                pending = identities[0]
            continue
        if pending is None:
            continue
        match = SCENARIO_LINE_RE.match(line)
        if match:
            found.append(ScenarioDeclaration(scenario_id=pending, title=match.group("title")))
            pending = None
            continue
        raise IngestionError(f"{where}: tag @{pending} is not followed by a 'Scenario:' line")

    if in_doc_string:
        raise IngestionError(f"{where}: doc string opened with {doc_delimiter!r} is not terminated")
    if pending is not None:
        raise IngestionError(f"{where}: tag @{pending} is not followed by a 'Scenario:' line")
    return found


def parse_annotation(text: str, *, where: str) -> str | None:
    """Return the first-line ``# cta:artifact CODE-nnn|TEST-nnn`` identity, if any.

    Python's tokenizer decides what is a comment: annotation-like text inside a string literal
    is data. A comment that follows code on the same line is trailing and is data; a comment that
    is the only content on its line is a declaration candidate. Only a column-0 candidate on the
    physical first line declares an identity. A later candidate is an error (naming both
    identities when the first is valid), and an incomplete tokenization is an error rather than a
    silently partial inventory.
    """
    lines = text.split("\n")
    declarations = []
    for row, column, comment in _annotation_comments(text, where=where):
        line = lines[row - 1] if 0 < row <= len(lines) else ""
        if line[:column].strip():
            continue
        declarations.append((row, column, comment))
    if not declarations:
        return None
    if len(declarations) > 1:
        described = ", ".join(
            (
                match.group("id")
                if (match := ANNOTATION_RE.fullmatch(comment)) is not None
                else comment
            )
            for _, _, comment in declarations
        )
        raise IngestionError(
            f"{where}: a file may declare only one artifact annotation; found {described}"
        )
    row, column, comment = declarations[0]
    match = ANNOTATION_RE.fullmatch(comment)
    if row != 1 or column != 0 or match is None:
        raise IngestionError(
            f"{where}: an artifact annotation must be the first line at column 0 and use "
            f"'# cta:artifact CODE-nnn|TEST-nnn': {comment!r} at line {row}"
        )
    return match.group("id")


def _annotation_comments(text: str, *, where: str) -> list[tuple[int, int, str]]:
    """Declaration-like comment tokens as ``(row, column, text)``, in source order.

    Tokenization errors abort the scan: a partial comment inventory could hide a declaration or a
    conflict, so the caller receives an error instead of a successful incomplete result.
    """
    found: list[tuple[int, int, str]] = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            if token.type == tokenize.COMMENT and ANNOTATION_ATTEMPT_RE.match(token.string):
                found.append((token.start[0], token.start[1], token.string))
    except (tokenize.TokenError, IndentationError, SyntaxError) as exc:
        raise IngestionError(
            f"{where}: cannot tokenize the file to verify artifact declarations: {exc}"
        ) from exc
    return found


def _identity_tokens(line: str, *, where: str) -> list[str]:
    """Valid ``@SCN-nnn`` identities on a tag line; malformed reserved tokens raise."""
    identities: list[str] = []
    for token in re.split(r"[ \t]+", line.strip(INDENT)):
        if not token.startswith("@"):
            continue
        name = token[1:]
        if name.startswith("SCN"):
            if not SCENARIO_ID_RE.fullmatch(name):
                raise IngestionError(
                    f"{where}: malformed scenario identity {token!r}; expected @SCN-nnn"
                )
            identities.append(name)
    return identities
