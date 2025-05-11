import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Literal, Optional, Union

from bson import ObjectId
from dataclasses_json import DataClassJsonMixin, dataclass_json


@dataclass_json
@dataclass
class IDCondition(DataClassJsonMixin):
    equal: Optional[ObjectId] = None
    in_set: Optional[List[ObjectId]] = None
    greater_than: Optional[ObjectId] = None
    less_than: Optional[ObjectId] = None


@dataclass_json
@dataclass
class ChannelsCondition(DataClassJsonMixin):
    equal: Optional[int] = None


@dataclass_json
@dataclass
class DurationCondition(DataClassJsonMixin):
    greater_than: Optional[int] = None
    less_than: Optional[int] = None


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
    column_idx: int
    subcolumn_idx: int
    model_id: str
    score_equal: Optional[int] = None
    score_in_set: Optional[List[int]] = None
    score_greater_than: Optional[int] = None
    score_less_than: Optional[int] = None


@dataclass_json
@dataclass
class SearchParams(DataClassJsonMixin):
    must: List[StoredInfoCondition | ResultsCondition | DurationCondition | ChannelsCondition | IDCondition ] = field(default_factory=list)
    should: List[StoredInfoCondition | ResultsCondition | DurationCondition | ChannelsCondition | IDCondition ] = field(default_factory=list)
    must_not: List[StoredInfoCondition | ResultsCondition | DurationCondition | ChannelsCondition | IDCondition ] = field(default_factory=list)
    should_not: List[StoredInfoCondition | ResultsCondition | DurationCondition | ChannelsCondition | IDCondition ] = field(default_factory=list)
