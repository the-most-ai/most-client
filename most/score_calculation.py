from typing import Dict, Tuple, List, Optional, Literal
from dataclasses_json import dataclass_json, DataClassJsonMixin
from dataclasses import dataclass, replace
from .types import Result, ScriptScoreMapping


@dataclass_json
@dataclass
class ScoreCalculation(DataClassJsonMixin):
    score_mapping: List[ScriptScoreMapping]

    def modify(self, result: Optional[Result]):
        score_mapping = {
            (sm.column, sm.subcolumn, sm.from_score): sm.to_score
            for sm in self.score_mapping
        }
        if result is None:
            return None
        result = replace(result)
        for column_result in result.results:
            for subcolumn_result in column_result.subcolumns:
                subcolumn_result.score = score_mapping.get((column_result.name,
                                                            subcolumn_result.name,
                                                            subcolumn_result.score),
                                                           subcolumn_result.score)

        return result

    def unmodify(self, result: Optional[Result]):
        score_mapping = {
            (sm.column, sm.subcolumn, sm.to_score): sm.from_score
            for sm in self.score_mapping
        }
        if result is None:
            return None
        result = replace(result)
        for column_result in result.results:
            for subcolumn_result in column_result.subcolumns:
                subcolumn_result.score = score_mapping.get((column_result.name,
                                                            subcolumn_result.name,
                                                            subcolumn_result.score),
                                                           subcolumn_result.score)

        return result

    def modify_single(self,
                      column: str, subcolumn: str,
                      from_score: int):
        for sm in self.score_mapping:
            if sm.column == column and sm.subcolumn == subcolumn and sm.from_score == from_score:
                return sm.to_score

    def unmodify_single(self,
                        column: str, subcolumn: str,
                        to_score: int,
                        bound: Literal["strict", "upper", "lower"] = "strict"):
        upper_from_score = None
        lower_from_score = None

        for sm in self.score_mapping:
            if sm.column == column and sm.subcolumn == subcolumn:
                if sm.to_score == to_score:
                    return sm.from_score

                if sm.to_score > to_score:
                    if upper_from_score is None or sm.to_score < upper_from_score[1]:
                        upper_from_score = (sm.from_score, sm.to_score)
                elif sm.to_score < to_score:
                    if lower_from_score is None or sm.to_score > lower_from_score[1]:
                        lower_from_score = (sm.from_score, sm.to_score)

        if bound == "strict":
            return None
        elif bound == "upper" and upper_from_score is not None:
            return upper_from_score[0]
        elif bound == "lower" and lower_from_score is not None:
            return lower_from_score[0]
        else:
            return None
