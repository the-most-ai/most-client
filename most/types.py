from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Audio:
    id: str
    url: str


@dataclass
class SubcolumnResult:
    name: str
    score: Optional[int]
    description: str


@dataclass
class ColumnResult:
    name: str
    subcolumns: List[SubcolumnResult]


@dataclass
class Result:
    id: str
    text: Optional[str]
    url: Optional[str]
    results: Optional[List[ColumnResult]]


@dataclass
class Column:
    name: str
    subcolumns: List[str]


@dataclass
class Script:
    columns: List[Column]
