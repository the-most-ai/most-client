from dataclasses import dataclass
from dataclasses_json import dataclass_json, DataClassJsonMixin
from typing import Optional, List, Literal


@dataclass_json
@dataclass
class Audio(DataClassJsonMixin):
    id: str
    url: str


@dataclass_json
@dataclass
class Text(DataClassJsonMixin):
    id: str


@dataclass_json
@dataclass
class SubcolumnResult(DataClassJsonMixin):
    name: str
    score: Optional[int]
    description: str


@dataclass_json
@dataclass
class ColumnResult(DataClassJsonMixin):
    name: str
    subcolumns: List[SubcolumnResult]


@dataclass_json
@dataclass
class Column(DataClassJsonMixin):
    name: str
    subcolumns: List[str]


@dataclass_json
@dataclass
class Script(DataClassJsonMixin):
    columns: List[Column]


@dataclass_json
@dataclass
class JobStatus(DataClassJsonMixin):
    status: Literal["not_found", "pending", "completed", "error"]


@dataclass_json
@dataclass
class Result(DataClassJsonMixin):
    id: str
    text: Optional[str]
    url: Optional[str]
    results: Optional[List[ColumnResult]]

    def get_script(self) -> Optional[Script]:
        if self.results is None:
            return None

        return Script(columns=[Column(name=column_result.name,
                                      subcolumns=[subcolumn_result.name
                                                  for subcolumn_result in column_result.subcolumns])
                               for column_result in self.results])
