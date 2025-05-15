from dataclasses import dataclass, field
from typing import List, Optional
from dataclasses_json import DataClassJsonMixin, dataclass_json


@dataclass_json
@dataclass
class IDCondition(DataClassJsonMixin):
    equal: Optional[str] = None
    in_set: Optional[List[str]] = None
    greater_than: Optional[str] = None
    less_than: Optional[str] = None


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
class TagsCondition(DataClassJsonMixin):
    in_set: Optional[List[str]] = None


@dataclass_json
@dataclass
class StoredInfoCondition(DataClassJsonMixin):
    key: str
    match: Optional[int | str | float] = None
    starts_with: Optional[str] = None
    ends_with: Optional[str] = None
    greater_than: Optional[int | str | float] = None
    less_than: Optional[int | str | float] = None


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

    def create_from(self, client,
                    column: str, subcolumn: str,
                    score_equal: Optional[int] = None,
                    score_in_set: Optional[List[int]] = None,
                    score_greater_than: Optional[int] = None,
                    score_less_than: Optional[int] = None,
                    modified_scores: bool = False) -> 'ResultsCondition':
        from .api import MostClient
        client: MostClient
        script = client.get_model_script()
        column_idx = [column.name for column in script.columns].index(column)
        subcolumn_idx = script.columns[column_idx].subcolumns.index(subcolumn)

        if modified_scores:
            score_modifier = client.get_score_modifier()
            if score_equal is not None:
                score_equal = score_modifier.unmodify_single(column, subcolumn,
                                                             score_equal,
                                                             bound="strict")
            if score_in_set is not None:
                score_in_set = [score_modifier.unmodify_single(column, subcolumn,
                                                               score,
                                                               bound="strict")
                                for score in score_in_set]
            if score_greater_than is not None:
                score_greater_than = score_modifier.unmodify_single(column, subcolumn,
                                                                    score_greater_than,
                                                                    bound="upper")

            if score_less_than is not None:
                score_less_than = score_modifier.unmodify_single(column, subcolumn,
                                                                 score_less_than,
                                                                 bound="lower")

        return ResultsCondition(model_id=client.model_id,
                                column_idx=column_idx,
                                subcolumn_idx=subcolumn_idx,
                                score_equal=score_equal,
                                score_in_set=score_in_set,
                                score_greater_than=score_greater_than,
                                score_less_than=score_less_than)

    async def acreate_from(self, client,
                           column: str, subcolumn: str,
                           score_equal: Optional[int] = None,
                           score_in_set: Optional[List[int]] = None,
                           score_greater_than: Optional[int] = None,
                           score_less_than: Optional[int] = None,
                           modified_scores: bool = False) -> 'ResultsCondition':
        from .async_api import AsyncMostClient
        client: AsyncMostClient
        script = await client.get_model_script()
        column_idx = [column.name for column in script.columns].index(column)
        subcolumn_idx = script.columns[column_idx].subcolumns.index(subcolumn)

        if modified_scores:
            score_modifier = await client.get_score_modifier()
            if score_equal is not None:
                score_equal = score_modifier.unmodify_single(column, subcolumn,
                                                             score_equal,
                                                             bound="strict")
            if score_in_set is not None:
                score_in_set = [score_modifier.unmodify_single(column, subcolumn,
                                                               score,
                                                               bound="strict")
                                for score in score_in_set]
            if score_greater_than is not None:
                score_greater_than = score_modifier.unmodify_single(column, subcolumn,
                                                                    score_greater_than,
                                                                    bound="upper")

            if score_less_than is not None:
                score_less_than = score_modifier.unmodify_single(column, subcolumn,
                                                                 score_less_than,
                                                                 bound="lower")

        return ResultsCondition(model_id=client.model_id,
                                column_idx=column_idx,
                                subcolumn_idx=subcolumn_idx,
                                score_equal=score_equal,
                                score_in_set=score_in_set,
                                score_greater_than=score_greater_than,
                                score_less_than=score_less_than)


@dataclass_json
@dataclass
class SearchParams(DataClassJsonMixin):
    must: List[StoredInfoCondition | ResultsCondition | DurationCondition | ChannelsCondition | IDCondition | TagsCondition] = field(default_factory=list)
    should: List[StoredInfoCondition | ResultsCondition | DurationCondition | ChannelsCondition | IDCondition | TagsCondition ] = field(default_factory=list)
    must_not: List[StoredInfoCondition | ResultsCondition | DurationCondition | ChannelsCondition | IDCondition | TagsCondition ] = field(default_factory=list)
    should_not: List[StoredInfoCondition | ResultsCondition | DurationCondition | ChannelsCondition | IDCondition | TagsCondition ] = field(default_factory=list)
