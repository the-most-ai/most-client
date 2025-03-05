from typing import Dict, Tuple, List, Optional
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
