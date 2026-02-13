import copy
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Union

import aiofiles
import httpx
from dataclasses_json import DataClassJsonMixin, dataclass_json


@dataclass_json
@dataclass
class StoredAudioData(DataClassJsonMixin):
    id: str
    url: str
    data: Optional[Dict[str, Union[str, int, float]]] = None
    results: Optional[Dict[str, List["ColumnResult"]]] = None


@dataclass_json
@dataclass
class Audio(DataClassJsonMixin):
    id: str
    url: str

    async def download_async(self, cached_path):
        print(f"Downloading {self.url} -> {cached_path}")
        async with httpx.AsyncClient() as client:
            async with aiofiles.open(cached_path, "wb") as f:
                resp = await client.get(self.url, headers={"User-Agent": "most"})
                await f.write(resp.content)

    def download(self, cached_path):
        print(f"Downloading {self.url} -> {cached_path}")
        with httpx.Client() as client:
            with open(cached_path, "wb") as f:
                resp = client.get(self.url, headers={"User-Agent": "most"})
                f.write(resp.content)


@dataclass_json
@dataclass
class Text(DataClassJsonMixin):
    id: str


@dataclass_json
@dataclass
class StoredTextData(DataClassJsonMixin):
    id: str
    data: Optional[Dict[str, Union[str, int, float]]] = None
    results: Optional[Dict[str, List["ColumnResult"]]] = None


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
    tags: List[str] = field(default_factory=list)
    subtags: List[List[str]] = field(default_factory=list)

    def __post_init__(self):
        if not self.subtags:
            self.subtags = [[] for _ in self.subcolumns]


@dataclass_json
@dataclass
class Script(DataClassJsonMixin):
    columns: List[Column]


@dataclass_json
@dataclass
class ModelInfo(DataClassJsonMixin):
    model_id: str
    secondary_model_ids: List[str]
    script: Script


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
class UpdateResult(DataClassJsonMixin):
    column_name: str
    subcolumn_name: str
    score: Optional[int] = None
    description: Optional[str] = None

    data: Optional[Dict[str, Union[str, int, float]]] = None
    timestamp: Optional[int] = None


@dataclass_json
@dataclass
class Result(DataClassJsonMixin):
    id: str
    text: Optional[str] = None
    url: Optional[str] = None
    results: Optional[List[ColumnResult]] = None
    created_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None

    edits: Optional[List[UpdateResult]] = None

    def get_script(self) -> Optional[Script]:
        if self.results is None:
            return None

        return Script(columns=[Column(name=column_result.name,
                                      subcolumns=[subcolumn_result.name
                                                  for subcolumn_result in column_result.subcolumns])
                               for column_result in self.results])

    def apply_edits(self, inplace=True):
        result = self
        if not inplace:
            result = copy.deepcopy(self)

        if result.edits is None:
            return result

        if result.results is None:
            return result

        edits = sorted(result.edits, key=lambda x: x.timestamp)
        for edit in edits:
            column = next((c for c in result.results
                           if c.name == edit.column_name), None)
            if column is None:
                continue
            subcolumn = next((s for s in column.subcolumns
                              if s.name == edit.subcolumn_name), None)
            if subcolumn is None:
                continue
            if edit.score is not None:
                subcolumn.score = edit.score
            if edit.description is not None:
                subcolumn.description = edit.description
        result.edits = None
        return result


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

    def to_raw_text(self):
        return ' '.join([segment.text
                         for segment in self.segments])

    def to_raw_speaker_text(self, speaker):
        return ' '.join([segment.text
                         for segment in self.segments
                         if segment.speaker == speaker])

    def get_speaker_names(self):
        return list(set([segment.speaker
                         for segment in self.segments]))


@dataclass_json
@dataclass
class GlossaryNGram(DataClassJsonMixin):
    original: List[str]
    pronunciation: List[str]
    weight: float = 2
    id: Optional[str] = None


@dataclass_json
@dataclass
class Item(DataClassJsonMixin):
    title: str
    pronunciation: str

    url: Optional[str] = None
    price: Optional[int] = None
    category: Optional[str] = None
    image_urls: List[str] = field(default_factory=list)
    available: bool = True

    metadata: Dict[str, Union[str, int, float, bool]] = field(default_factory=dict)
    id: Optional[str] = None


@dataclass_json
@dataclass
class DialogResult(DataClassJsonMixin):
    id: str
    dialog: Optional[Dialog] = None
    url: Optional[str] = None
    results: Optional[List[ColumnResult]] = None


@dataclass_json
@dataclass
class HumanFeedback(DataClassJsonMixin):
    data_point_id: str
    data_point_type: Literal["audio", "text"]
    column_name: str
    subcolumn_name: str
    score: int
    description: str = ""

    @classmethod
    def calculate_accuracy(cls,
                           preds: List["HumanFeedback"],
                           gt: List["HumanFeedback"]) -> float:
        preds = {(y_pred.data_point_id, y_pred.column_name, y_pred.subcolumn_name): y_pred.score
                 for y_pred in preds}
        gt = {(y_true.data_point_id, y_true.column_name, y_true.subcolumn_name): y_true.score
              for y_true in gt}
        common_keys = set(preds.keys()) & set(gt.keys())
        return sum((preds[key] == gt[key]) for key in common_keys) / len(common_keys)


@dataclass_json
@dataclass
class Usage(DataClassJsonMixin):
    apply_audio_async: int
    apply_audio_async_duration: int
    apply_text_async: int

    apply_audio: int
    apply_audio_duration: int
    apply_text: int

    upload_audio: int
    upload_audio_duration: int
    upload_text: int

    start_dt: datetime
    end_dt: datetime


def is_valid_objectid(oid: str) -> bool:
    """
    Check if a given string is a valid MongoDB ObjectId (24-character hex).
    """
    return bool(re.fullmatch(r"^[0-9a-fA-F]{24}$", oid))


def is_valid_english_word(text: str) -> bool:
    """
    Returns True if the text starts with a letter and contains only English letters and digits.
    """
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9\-]*", text))


def is_valid_id(smth_id: Optional[str]) -> bool:
    if smth_id is None:
        return False

    if smth_id.startswith("most-"):
        smth_id = smth_id[5:]

    return is_valid_objectid(smth_id) or is_valid_english_word(smth_id)


@dataclass_json
@dataclass
class CommunicationRequest(DataClassJsonMixin):
    source_entity_id: str
    most_communication_id: str
    start_dt: str
    manager: str
    end_dt: Optional[str] = None  # :(
    talk_duration: Optional[int] = None  # :(
    client_phone: Optional[str] = None
    wait_duration: Optional[int] = None
    status: Optional[str] = None
    communication_type: Literal["call", "chat"] = "call"
    manager_extension: Optional[str] = None
    manager_direct_number: Optional[str] = None
    communication_direction: Optional[Literal["inbound", "outbound"]] = None
    communication_result: Optional[Literal["answered", "missed", "no_answer", "busy", "failed", "unknown"]] = None
    result: Optional[Literal["answered", "missed", "no_answer", "busy", "failed", "unknown"]] = None
    extra_fields: Optional[Dict[str, Union[str, int, float, bool]]] = None
    tech_fields: Optional[Dict[str, Union[str, int, float, bool]]] = None


@dataclass_json
@dataclass
class CommunicationResponse(DataClassJsonMixin):
    reason: str
    success: bool = True


@dataclass_json
@dataclass
class CommunicationBatchRequest(DataClassJsonMixin):
    communications: List[CommunicationRequest]
    overwrite: bool = False


@dataclass_json
@dataclass
class CommunicationBatchResponse(DataClassJsonMixin):
    status_per_communication: Dict[str, CommunicationResponse]
    total_saved: int
    success: bool = True


@dataclass_json
@dataclass
class ProcessCommunicationByIdResponse(DataClassJsonMixin):
    """Ответ после отправки коммуникации в n8n."""
    success: bool
    most_communication_id: str
    execution_id: Optional[str] = None
    error: Optional[str] = None