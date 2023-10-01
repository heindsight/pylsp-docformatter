from typing import Any, Dict, TypedDict


class RangeBoundary(TypedDict):
    line: int
    character: int


class Range(TypedDict):
    start: RangeBoundary
    end: RangeBoundary


class FormatResult(TypedDict):
    range: Range
    newText: str


LspSettings = Dict[str, Any]
