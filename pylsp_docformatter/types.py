from typing import TypedDict


class RangeBoundary(TypedDict):
    line: int
    character: int


class Range(TypedDict):
    start: RangeBoundary
    end: RangeBoundary


class FormatResult(TypedDict):
    range: Range
    newText: str
