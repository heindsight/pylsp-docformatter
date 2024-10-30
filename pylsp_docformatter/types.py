"""LSP type definitions."""

from typing import Any, Dict, TypedDict


class Position(TypedDict):
    """A position in a document."""

    line: int
    character: int


class Range(TypedDict):
    """An LSP text range."""

    start: Position
    end: Position


class TextEdit(TypedDict):
    """The result of a formatting operation."""

    range: Range
    newText: str


LspSettings = Dict[str, Any]
