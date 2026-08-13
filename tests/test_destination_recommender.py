"""Tests for services/destination_recommender.py. The Overpass HTTP
call itself is mocked (never executed against the live internet in
this sandbox -- same convention as the rest of services/, see
geo.py's docstring) so these test the request-building and
response-parsing/sorting logic in isolation.
"""
from unittest.mock import patch, MagicMock
from conftest import load_app_module

destination_recommender = load_app_module('app.services.destination_recommender')


def _mock_response(elements):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {'elements': elements}
    return resp


def test_recommend_destinations_parses_and_sorts_by_distance():
    elements = [
        {'lat': 40.72, 'lon': -74.5, 'tags': {'name': 'Far Park'}},
        {'lat': 40.71, 'lon': -74.01, 'tags': {'name': 'Near Park'}},
    ]
    with patch('requests.post', return_value=_mock_response(elements)):
        results = destination_recommender.recommend_destinations(40.7128, -74.0060, safe_range_km=100, category='nature')
    assert results is not None
    assert len(results) == 2
    assert results[0]['name'] == 'Near Park'
    assert results[0]['distance_km'] < results[1]['distance_km']


def test_recommend_destinations_skips_unnamed_and_incomplete_elements():
    elements = [
        {'lat': 40.71, 'lon': -74.01, 'tags': {}},  # no name -- skipped
        {'lon': -74.01, 'tags': {'name': 'No Lat'}},  # missing lat -- skipped
        {'center': {'lat': 40.715, 'lon': -74.02}, 'tags': {'name': 'A Way'}},  # way with center -- kept
    ]
    with patch('requests.post', return_value=_mock_response(elements)):
        results = destination_recommender.recommend_destinations(40.7128, -74.0060, safe_range_km=50)
    assert len(results) == 1
    assert results[0]['name'] == 'A Way'


def test_recommend_destinations_returns_none_on_failure():
    with patch('requests.post', side_effect=Exception('network error')):
        results = destination_recommender.recommend_destinations(40.7128, -74.0060, safe_range_km=50)
    assert results is None


def test_recommend_destinations_respects_max_results():
    elements = [{'lat': 40.7 + i * 0.01, 'lon': -74.0, 'tags': {'name': f'Spot {i}'}} for i in range(20)]
    with patch('requests.post', return_value=_mock_response(elements)):
        results = destination_recommender.recommend_destinations(40.7128, -74.0060, safe_range_km=200, max_results=5)
    assert len(results) == 5


def test_recommend_destinations_includes_round_trip_distance():
    elements = [{'lat': 40.72, 'lon': -74.0, 'tags': {'name': 'Spot'}}]
    with patch('requests.post', return_value=_mock_response(elements)):
        results = destination_recommender.recommend_destinations(40.7128, -74.0060, safe_range_km=50)
    assert results[0]['round_trip_distance_km'] == round(results[0]['distance_km'] * 2, 1)


def test_unknown_category_falls_back_to_tourism_tag():
    assert destination_recommender.CATEGORY_TAGS.get('nonexistent_category') is None
    # recommend_destinations itself falls back internally -- verify no
    # exception and a sensible query still gets built.
    with patch('requests.post', return_value=_mock_response([])) as mock_post:
        destination_recommender.recommend_destinations(40.0, -74.0, safe_range_km=10, category='nonexistent_category')
    called_query = mock_post.call_args.kwargs['data']['data']
    assert 'tourism=attraction' in called_query
