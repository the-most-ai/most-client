import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Literal, Optional

from dataclasses_json import DataClassJsonMixin, dataclass_json


@dataclass_json
@dataclass
class StoredAudioData(DataClassJsonMixin):
    id: str
    data: Dict[str, str]


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
    score: Optional[int] = None
    description: str = ""


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
class ScriptScoreMapping(DataClassJsonMixin):
    column: str
    subcolumn: str
    from_score: int
    to_score: int


@dataclass_json
@dataclass
class JobStatus(DataClassJsonMixin):
    status: Literal["not_found", "pending", "completed", "error"]


@dataclass_json
@dataclass
class Result(DataClassJsonMixin):
    id: str
    text: Optional[str] = None
    url: Optional[str] = None
    results: Optional[List[ColumnResult]] = None
    created_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None

    def get_script(self) -> Optional[Script]:
        if self.results is None:
            return None

        return Script(columns=[Column(name=column_result.name,
                                      subcolumns=[subcolumn_result.name
                                                  for subcolumn_result in column_result.subcolumns])
                               for column_result in self.results])


@dataclass_json
@dataclass
class DialogSegment(DataClassJsonMixin):
    start_time_ms: int
    end_time_ms: int
    text: str
    speaker: str
    emotion: Optional[str] = None
    intensity: Optional[float] = None

    def to_text(self):
        if self.emotion is None:
            return f'{self.speaker}: {self.text}\n'
        else:
            return f'{self.speaker}: <emotion name="{self.emotion}" intensity="{self.intensity}">{self.text}</emotion>\n'


@dataclass_json
@dataclass
class Dialog(DataClassJsonMixin):
    segments: List[DialogSegment]

    def to_text(self):
        return ''.join([segment.to_text()
                        for segment in self.segments])


@dataclass_json
@dataclass
class DialogResult(DataClassJsonMixin):
    id: str
    dialog: Optional[Dialog] = None
    url: Optional[str] = None
    results: Optional[List[ColumnResult]] = None


@dataclass_json
@dataclass
class StoredInfoCondition(DataClassJsonMixin):
    key: str
    match: Optional[str] = None
    starts_with: Optional[str] = None
    ends_with: Optional[str] = None


@dataclass_json
@dataclass
class ResultsCondition(DataClassJsonMixin):
    column: str
    subcolumn: str
    score_greater_than: Optional[int] = None
    score_less_than: Optional[int] = None


@dataclass_json
@dataclass
class SearchParams(DataClassJsonMixin):
    must: List[StoredInfoCondition | ResultsCondition]
    should: List[StoredInfoCondition | ResultsCondition]
    must_not: List[StoredInfoCondition | ResultsCondition]


def is_valid_objectid(oid: str) -> bool:
    """
    Check if a given string is a valid MongoDB ObjectId (24-character hex).
    """
    return bool(re.fullmatch(r"^[0-9a-fA-F]{24}$", oid))


def is_valid_id(smth_id: Optional[str]) -> bool:
    if smth_id is None:
        return False

    if smth_id.startswith("most-"):
        smth_id = smth_id[5:]

    return is_valid_objectid(smth_id)
