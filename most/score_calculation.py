import dataclasses
from typing import Dict, Tuple, List, Optional

from .types import Result, ScriptScoreMapping


class ScoreCalculation:
    def __init__(self, score_mapping: List[ScriptScoreMapping]):
        super(ScoreCalculation, self).__init__()
        self.score_mapping = {
            (sm.column, sm.subcolumn, sm.from_score): sm.to_score
            for sm in score_mapping
        }

    def modify(self, result: Optional[Result]):
        if result is None:
            return None
        result = dataclasses.replace(result)
        for column_result in result.results:
            for subcolumn_result in column_result.subcolumns:
                subcolumn_result.score = self.score_mapping[(column_result.name, subcolumn_result.name, subcolumn_result.score)]

        return result
