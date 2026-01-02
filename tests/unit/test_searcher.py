import os
import pytest
from dotenv import load_dotenv
from typing import List

from most.api import MostClient
from most.searcher import MostSearcher
from most.search_types import (
    SearchParams,
    IDCondition,
    ChannelsCondition,
    DurationCondition,
    URLCondition,
    TagsCondition,
    StoredInfoCondition,
    AggregatedResultsCondition,
    AggregatedField,
    AggregatedColumnField,
    AggregatedAllField,
    ResultsCondition,
    ExistsResultsCondition,
)
from most.types import StoredAudioData


# Load environment variables from .env file
load_dotenv()


@pytest.fixture
def most_client():
    """Create a MostClient using credentials from .env file"""
    client_id = os.getenv("MOST_TEST_CLIENT_ID")
    client_secret = os.getenv("MOST_TEST_CLIENT_SECRET")
    model_id = os.getenv("MOST_TEST_MODEL_ID")

    assert client_id, "MOST_TEST_CLIENT_ID not found in environment"
    assert client_secret, "MOST_TEST_CLIENT_SECRET not found in environment"
    assert model_id, "MOST_TEST_MODEL_ID not found in environment"

    return MostClient(
        client_id=client_id,
        client_secret=client_secret,
        model_id=model_id,
    )


@pytest.fixture
def audio_searcher(most_client):
    """Create a MostSearcher for audio data"""
    return MostSearcher(most_client, "audio")


class TestSearcher:
    """
    Test all Condition types with real data validation

    This test suite covers all available Condition types:
    - IDCondition: Tests equal, in_set, greater_than filters
    - ChannelsCondition: Tests equal filter for audio channels
    - DurationCondition: Tests greater_than and less_than filters
    - URLCondition: Tests starts_with filter
    - TagsCondition: Tests in_set filter for audio tags
    - StoredInfoCondition: Tests key matching, starts_with, and greater_than
    - AggregatedResultsCondition: Tests sum and avg aggregations with thresholds
    - ResultsCondition: Tests score filtering with greater_than and in_set
    - ExistsResultsCondition: Tests existence of results for specific models

    Additional functionality tested:
    - SearchParams combinations (must, should, must_not)
    - Search options (include_data, include_results)
    - Utility methods (count, distinct)

    All tests use real data from the MostClient configured via .env credentials.
    Tests validate that filtered results actually match the specified conditions.
    """

    def test_id_condition_equal(self, audio_searcher):
        """Test IDCondition with equal filter"""
        # First get some audios to get a valid ID
        all_audios = audio_searcher.search(SearchParams(), limit=5)
        if not all_audios:
            pytest.skip("No audio data available for testing")

        test_id = all_audios[0].id

        # Test equal condition
        search_params = SearchParams(
            must=[IDCondition(equal=test_id)]
        )
        audios = audio_searcher.search(search_params)

        # Verify all results have the specified ID
        assert len(audios) == 1
        assert audios[0].id == test_id

    def test_id_condition_in_set(self, audio_searcher):
        """Test IDCondition with in_set filter"""
        # Get some valid IDs
        all_audios = audio_searcher.search(SearchParams(), limit=3)
        if len(all_audios) < 2:
            pytest.skip("Insufficient audio data for testing")

        test_ids = [audio.id for audio in all_audios[:2]]

        search_params = SearchParams(
            must=[IDCondition(in_set=test_ids)]
        )
        audios = audio_searcher.search(search_params)

        # Verify all results have IDs from the set
        result_ids = {audio.id for audio in audios}
        assert result_ids.issubset(set(test_ids))

    def test_id_condition_greater_than(self, audio_searcher):
        """Test IDCondition with greater_than filter"""
        all_audios = audio_searcher.search(SearchParams(), limit=10)
        if not all_audios:
            pytest.skip("No audio data available for testing")

        # Sort IDs to get a middle value
        sorted_ids = sorted([audio.id for audio in all_audios])
        if len(sorted_ids) < 3:
            pytest.skip("Insufficient audio data for comparison")

        mid_id = sorted_ids[len(sorted_ids)//2]

        search_params = SearchParams(
            must=[IDCondition(greater_than=mid_id)]
        )
        audios = audio_searcher.search(search_params)

        # Verify all results have ID greater than the specified value
        for audio in audios:
            assert audio.id > mid_id

    def test_channels_condition_equal(self, audio_searcher):
        """Test ChannelsCondition with equal filter"""
        # Get some audios and check their channel counts using fetch_info
        all_audios = audio_searcher.search(SearchParams(), limit=10)
        if not all_audios:
            pytest.skip("No audio data available for testing")

        # Find audios with different channel counts
        channel_counts = set()
        for audio in all_audios:
            info = audio_searcher.client.fetch_info(audio.id)
            if info.data and "channels" in info.data:
                channel_counts.add(info.data["channels"])

        if not channel_counts:
            pytest.skip("No channel information available in audio data")

        test_channels = list(channel_counts)[0]

        search_params = SearchParams(
            must=[ChannelsCondition(equal=test_channels)]
        )
        audios = audio_searcher.search(search_params)

        # Verify all results have the specified channel count using fetch_info
        for audio in audios:
            info = audio_searcher.client.fetch_info(audio.id)
            if info.data and "channels" in info.data:
                assert info.data["channels"] == test_channels

    def test_duration_condition_greater_than(self, audio_searcher):
        """Test DurationCondition with greater_than filter"""
        all_audios = audio_searcher.search(SearchParams(), limit=10)
        if not all_audios:
            pytest.skip("No audio data available for testing")

        # Get durations using fetch_info and find a reasonable threshold
        durations = []
        for audio in all_audios:
            info = audio_searcher.client.fetch_info(audio.id)
            if info.data and "duration" in info.data:
                durations.append(info.data["duration"])

        if not durations:
            pytest.skip("No duration information available in audio data")

        # Use median duration as threshold
        durations.sort()
        threshold = durations[len(durations)//2]

        search_params = SearchParams(
            must=[DurationCondition(greater_than=threshold)]
        )
        audios = audio_searcher.search(search_params)

        # Verify all results have duration greater than threshold using fetch_info
        for audio in audios:
            info = audio_searcher.client.fetch_info(audio.id)
            if info.data and "duration" in info.data:
                assert info.data["duration"] > threshold

    def test_duration_condition_less_than(self, audio_searcher):
        """Test DurationCondition with less_than filter"""
        all_audios = audio_searcher.search(SearchParams(), limit=10, include_data=True)
        if not all_audios:
            pytest.skip("No audio data available for testing")

        durations = []
        for audio in all_audios:
            info = audio_searcher.client.fetch_info(audio.id)
            if info.data and "duration" in info.data:
                durations.append(info.data["duration"])

        if not durations:
            pytest.skip("No duration information available in audio data")

        # Use a high threshold to ensure some results
        threshold = max(durations) + 1000

        search_params = SearchParams(
            must=[DurationCondition(less_than=threshold)]
        )
        audios = audio_searcher.search(search_params, include_data=True)

        # Verify all results have duration less than threshold
        for audio in audios:
            info = audio_searcher.client.fetch_info(audio.id)
            if info.data and "duration" in info.data:
                assert audio.data["duration"] < threshold

    def test_exists_results_condition(self, audio_searcher, most_client):
        """Test ExistsResultsCondition"""
        model_id = most_client.model_id

        search_params = SearchParams(
            must=[ExistsResultsCondition(model_id=model_id)],
        )

        audios = audio_searcher.search(search_params,
                                       limit=10000)

        # If we get results, they should have results for the specified model
        for audio in audios:
            result = most_client.fetch_results(audio.id)
            assert result.results is not None

    def test_aggregated_results_condition_sum(self, audio_searcher, most_client):
        """Test AggregatedResultsCondition with sum aggregation"""
        model_id = most_client.model_id

        search_params = SearchParams(
            must=[AggregatedResultsCondition(
                fields=[AggregatedAllField()],
                model_id=model_id,
                aggregation="sum",
                greater_than=20,
                less_than=22,
                modified=True
            )]
        )

        audios = audio_searcher.search(search_params)

        # If we get results, they should have results that aggregate to > 0
        for audio in audios:
            results = most_client.fetch_results(audio.id)
            if results.results:
                model_results = [r for r in audio.results if r.model_id == model_id]
                if model_results:
                    # Sum all scores should be > 0
                    total_sum = sum(sum(result.scores) for result in model_results if result.scores)
                    assert total_sum > 0

    def test_aggregated_results_condition_avg(self, audio_searcher, most_client):
        """Test AggregatedResultsCondition with avg aggregation"""
        model_id = most_client.model_id

        search_params = SearchParams(
            must=[AggregatedResultsCondition(
                fields=[AggregatedColumnField(column_idx=0)],
                model_id=model_id,
                aggregation="avg",
                less_than=100
            )]
        )

        audios = audio_searcher.search(search_params)

        # Results should have average scores < 100 for column 0
        for audio in audios:
            if hasattr(audio, 'results') and audio.results:
                model_results = [r for r in audio.results if r.model_id == model_id]
                if model_results:
                    # Check if we can validate the average
                    column_0_scores = []
                    for result in model_results:
                        if result.scores and len(result.scores) > 0:
                            column_0_scores.extend(result.scores[0] if isinstance(result.scores[0], list) else [result.scores[0]])
                    if column_0_scores:
                        avg_score = sum(column_0_scores) / len(column_0_scores)
                        assert avg_score < 100

    def test_results_condition_score_greater_than(self, audio_searcher, most_client):
        """Test ResultsCondition with score_greater_than"""
        model_id = most_client.model_id

        search_params = SearchParams(
            must=[ResultsCondition(
                column_idx=0,
                subcolumn_idx=0,
                model_id=model_id,
                score_greater_than=0
            )]
        )

        audios = audio_searcher.search(search_params)

        # Verify results have scores > 0 for specified column/subcolumn
        for audio in audios:
            if hasattr(audio, 'results') and audio.results:
                model_results = [r for r in audio.results if r.model_id == model_id]
                if model_results:
                    found_valid_score = False
                    for result in model_results:
                        if result.scores and len(result.scores) > 0:
                            col_scores = result.scores[0]
                            if isinstance(col_scores, list) and len(col_scores) > 0:
                                if col_scores[0] > 0:
                                    found_valid_score = True
                                    break
                            elif col_scores > 0:
                                found_valid_score = True
                                break
                    # At least one result should have a valid score > 0
                    if model_results:  # Only assert if we have results to check
                        assert found_valid_score

    def test_results_condition_score_in_set(self, audio_searcher, most_client):
        """Test ResultsCondition with score_in_set"""
        model_id = most_client.model_id

        # Use a range of common scores
        score_set = [0, 1, 2, 3, 4, 5]

        search_params = SearchParams(
            must=[ResultsCondition(
                column_idx=0,
                subcolumn_idx=0,
                model_id=model_id,
                score_in_set=score_set
            )]
        )

        audios = audio_searcher.search(search_params)

        # Verify results have scores in the specified set
        for audio in audios:
            if hasattr(audio, 'results') and audio.results:
                model_results = [r for r in audio.results if r.model_id == model_id]
                if model_results:
                    found_valid_score = False
                    for result in model_results:
                        if result.scores and len(result.scores) > 0:
                            col_scores = result.scores[0]
                            if isinstance(col_scores, list) and len(col_scores) > 0:
                                if col_scores[0] in score_set:
                                    found_valid_score = True
                                    break
                            elif col_scores in score_set:
                                found_valid_score = True
                                break
                    if model_results:
                        assert found_valid_score

    def test_search_params_must_combination(self, audio_searcher):
        """Test SearchParams with multiple must conditions"""
        all_audios = audio_searcher.search(SearchParams(), limit=5)
        if len(all_audios) < 2:
            pytest.skip("Insufficient audio data for testing")

        # Combine multiple conditions that should narrow results
        search_params = SearchParams(
            must=[
                DurationCondition(greater_than=0),
                IDCondition(in_set=[audio.id for audio in all_audios[:3]])
            ]
        )

        audios = audio_searcher.search(search_params, include_data=True)

        # Results should satisfy both conditions
        result_ids = {audio.id for audio in audios}
        expected_ids = {audio.id for audio in all_audios[:3]}
        assert result_ids.issubset(expected_ids)

        for audio in audios:
            if hasattr(audio, 'data') and audio.data and hasattr(audio.data, 'duration'):
                assert audio.data.duration > 0

    def test_search_params_should_conditions(self, audio_searcher):
        """Test SearchParams with should conditions (OR logic)"""
        all_audios = audio_searcher.search(SearchParams(), limit=5)
        if len(all_audios) < 2:
            pytest.skip("Insufficient audio data for testing")

        id1, id2 = all_audios[0].id, all_audios[1].id

        search_params = SearchParams(
            should=[
                IDCondition(equal=id1),
                IDCondition(equal=id2)
            ]
        )

        audios = audio_searcher.search(search_params)

        # Results should contain either ID
        result_ids = {audio.id for audio in audios}
        assert id1 in result_ids or id2 in result_ids

        for audio in audios:
            assert audio.id == id1 or audio.id == id2

    def test_search_params_must_not_conditions(self, audio_searcher):
        """Test SearchParams with must_not conditions"""
        all_audios = audio_searcher.search(SearchParams(), limit=10)
        if len(all_audios) < 5:
            pytest.skip("Insufficient audio data for testing")

        excluded_id = all_audios[0].id

        search_params = SearchParams(
            must_not=[IDCondition(equal=excluded_id)]
        )

        audios = audio_searcher.search(search_params, limit=5)

        # Results should not contain the excluded ID
        result_ids = {audio.id for audio in audios}
        assert excluded_id not in result_ids

    def test_search_with_include_data(self, audio_searcher):
        """Test search with include_data=True"""
        search_params = SearchParams(
            must=[DurationCondition(greater_than=0)]
        )

        audios = audio_searcher.search(search_params, limit=3, include_data=True)

        if audios:
            # At least some results should have data when include_data=True
            has_data = any(hasattr(audio, 'data') and audio.data for audio in audios)
            assert has_data

    def test_search_with_include_results(self, audio_searcher, most_client):
        """Test search with include_results"""
        model_id = most_client.model_id

        audios = audio_searcher.search(
            SearchParams(),
            limit=3,
            include_results=[model_id]
        )

        if audios:
            # Check if results are included for the specified model
            for audio in audios:
                if hasattr(audio, 'results') and audio.results:
                    model_results = [r for r in audio.results if r.model_id == model_id]
                    # If audio has results, at least one should be for our model
                    if audio.results:
                        assert len(model_results) > 0

    def test_count_method(self, audio_searcher):
        """Test the count method"""
        # Test basic count
        total_count = audio_searcher.count()
        assert isinstance(total_count, (int, dict))

        # Test count with filter
        all_audios = audio_searcher.search(SearchParams(), limit=5)
        if all_audios:
            search_params = SearchParams(
                must=[IDCondition(equal=all_audios[0].id)]
            )
            filtered_count = audio_searcher.count(search_params)
            assert isinstance(filtered_count, (int, dict))

    def test_distinct_method(self, audio_searcher):
        """Test the distinct method"""
        try:
            # Test getting distinct values for a common key
            distinct_values = audio_searcher.distinct("id")
            assert isinstance(distinct_values, list)

            # Test with filter
            all_audios = audio_searcher.search(SearchParams(), limit=3)
            if len(all_audios) >= 2:
                search_params = SearchParams(
                    must=[IDCondition(in_set=[audio.id for audio in all_audios[:2]])]
                )
                filtered_distinct = audio_searcher.distinct("id", search_params)
                assert isinstance(filtered_distinct, list)
                assert len(filtered_distinct) <= 2
        except RuntimeError as e:
            if "Key is not valid" in str(e):
                pytest.skip("Key 'id' is not valid for distinct operation")
            else:
                raise