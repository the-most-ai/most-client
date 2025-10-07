import pytest

from most.score_calculation import ScoreCalculation
from most.types import (
    ColumnResult,
    Result,
    ScriptScoreMapping,
    SubcolumnResult,
    UpdateResult,
)


def _build_score_calculation() -> ScoreCalculation:
    return ScoreCalculation(
        score_mapping=[
            ScriptScoreMapping(column="quality", subcolumn="tone", from_score=0, to_score=2),
            ScriptScoreMapping(column="quality", subcolumn="tone", from_score=1, to_score=3),
            ScriptScoreMapping(column="compliance", subcolumn="script", from_score=5, to_score=7),
        ]
    )


def _build_result() -> Result:
    return Result(
        id="result-1",
        results=[
            ColumnResult(
                name="quality",
                subcolumns=[
                    SubcolumnResult(name="tone", score=0),
                    SubcolumnResult(name="speed", score=4),
                ],
            ),
            ColumnResult(
                name="compliance",
                subcolumns=[SubcolumnResult(name="script", score=5)],
            ),
        ],
    )


def test_modify_returns_none_for_missing_result() -> None:
    calc = _build_score_calculation()
    assert calc.modify(None) is None


def test_modify_updates_result_scores_matching_mapping() -> None:
    calc = _build_score_calculation()
    original = _build_result()

    modified = calc.modify(original)

    assert modified is not original
    assert modified.results[0].subcolumns[0].score == 2
    assert modified.results[0].subcolumns[1].score == 4
    assert modified.results[1].subcolumns[0].score == 7


def test_modify_updates_update_result_instance() -> None:
    calc = _build_score_calculation()
    update = UpdateResult(
        column_name="quality",
        subcolumn_name="tone",
        score=0,
        description="initial",
    )

    modified = calc.modify(update)

    assert isinstance(modified, UpdateResult)
    assert modified is not update
    assert modified.score == 2
    assert modified.column_name == "quality"
    assert modified.subcolumn_name == "tone"
    assert modified.description == "initial"


def test_unmodify_returns_none_for_missing_result() -> None:
    calc = _build_score_calculation()
    assert calc.unmodify(None) is None


def test_unmodify_reverts_scores_to_original_values() -> None:
    calc = _build_score_calculation()
    transformed = _build_result()
    # Apply score mapping so that we can test the inverse behaviour.
    transformed.results[0].subcolumns[0].score = 2
    transformed.results[1].subcolumns[0].score = 7

    reverted = calc.unmodify(transformed)

    assert reverted.results[0].subcolumns[0].score == 0
    assert reverted.results[0].subcolumns[1].score == 4
    assert reverted.results[1].subcolumns[0].score == 5


def test_unmodify_updates_update_result_instance() -> None:
    calc = _build_score_calculation()
    update = UpdateResult(
        column_name="quality",
        subcolumn_name="tone",
        score=3,
    )

    reverted = calc.unmodify(update)

    assert isinstance(reverted, UpdateResult)
    assert reverted.score == 1


def test_modify_single_returns_target_score_when_mapping_exists() -> None:
    calc = _build_score_calculation()
    assert calc.modify_single("quality", "tone", 1) == 3


def test_modify_single_returns_none_when_mapping_missing() -> None:
    calc = _build_score_calculation()
    assert calc.modify_single("quality", "tone", 5) is None


def test_unmodify_single_returns_from_score_for_exact_match() -> None:
    calc = _build_score_calculation()
    assert calc.unmodify_single("quality", "tone", 3) == 1


def test_unmodify_single_returns_closest_upper_and_lower_matches() -> None:
    calc = ScoreCalculation(
        score_mapping=[
            ScriptScoreMapping(column="quality", subcolumn="tone", from_score=0, to_score=10),
            ScriptScoreMapping(column="quality", subcolumn="tone", from_score=1, to_score=15),
            ScriptScoreMapping(column="quality", subcolumn="tone", from_score=2, to_score=5),
        ]
    )

    assert calc.unmodify_single("quality", "tone", 12, bound="upper") == 1
    assert calc.unmodify_single("quality", "tone", 12, bound="lower") == 0


def test_unmodify_single_returns_none_when_no_bound_matches() -> None:
    calc = ScoreCalculation(
        score_mapping=[
            ScriptScoreMapping(column="quality", subcolumn="tone", from_score=0, to_score=10),
        ]
    )

    assert calc.unmodify_single("quality", "tone", 12, bound="upper") is None
    assert calc.unmodify_single("quality", "tone", 5, bound="lower") is None
    assert calc.unmodify_single("quality", "tone", 12, bound="strict") is None
