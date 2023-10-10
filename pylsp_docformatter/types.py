"""LSP type definitions."""
from typing import Any, Dict, TypedDict


class RangeBoundary(TypedDict):
    """A boundary of an LSP text range."""

    line: int
    character: int


class Range(TypedDict):
    """An LSP text range."""

    start: RangeBoundary
    end: RangeBoundary


class FormatResult(TypedDict):
    """The result of a formatting operation."""

    range: Range
    newText: str


LspSettings = Dict[str, Any]
