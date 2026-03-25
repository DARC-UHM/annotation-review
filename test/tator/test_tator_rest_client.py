from unittest.mock import patch

import pytest
import requests

from application.tator.tator_rest_client import TatorRestClient
from application.tator.tator_type import TatorStateType

TATOR_URL = 'https://whats.tator.precious'
TOKEN = 'test-token'


class MockResponse:
    def __init__(self, status_code=200, json_data=None, content=b''):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.content = content

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError()


def mocked_requests_get(*args, **kwargs):
    url = kwargs.get('url')
    if url == f'{TATOR_URL}/rest/Localizations/1?section=abc123':
        return MockResponse(json_data=[{'id': 1}, {'id': 2}])
    if url == f'{TATOR_URL}/rest/Localizations/1?media_id=10,20':
        return MockResponse(json_data=[{'id': 3}])
    if url == f'{TATOR_URL}/rest/Section/section123':
        return MockResponse(json_data={'id': 'section123', 'name': 'Test Section'})
    if url == f'{TATOR_URL}/rest/Medias/1?section=section123':
        return MockResponse(json_data=[{'id': 10}, {'id': 20}])
    if url == f'{TATOR_URL}/rest/Media/10':
        return MockResponse(json_data={'id': 10, 'name': 'test_media'})
    if url == f'{TATOR_URL}/rest/States/1?media_id=10,20':
        return MockResponse(json_data=[
            {'type': TatorStateType.SUBSTRATE, 'media': [10], 'frame': 90, 'attributes': {'Relief': 'Low / moderate: Low (<1m)', 'timestamp': '00:03'}},
            {'type': TatorStateType.SUBSTRATE, 'media': [10], 'frame': 30, 'attributes': {'Relief': 'Flat'}},
            {'type': TatorStateType.SUB_MODE,  'media': [10], 'frame': 60, 'attributes': {'Mode': 'Exploratory'}},
            {'type': TatorStateType.SUBSTRATE, 'media': [20], 'frame': 50, 'attributes': {'Relief': 'Flat'}},
        ])
    if url == f'{TATOR_URL}/rest/User/42':
        return MockResponse(json_data={'id': 42, 'username': 'testuser'})
    if url == f'{TATOR_URL}/rest/GetFrame/10':
        return MockResponse(content=b'fake-frame-bytes')
    if url == f'{TATOR_URL}/rest/LocalizationGraphic/99':
        return MockResponse(content=b'fake-graphic-bytes')
    return MockResponse(status_code=404)


def mocked_requests_post(*args, **kwargs):
    url = kwargs.get('url')
    if url == f'{TATOR_URL}/rest/Token':
        if kwargs.get('json', {}).get('username') == 'testuser':
            return MockResponse(json_data={'token': 'my-token'})
        return MockResponse(status_code=401)
    return MockResponse(status_code=404)


class TestTatorRestClient:
    def test_init(self):
        client = TatorRestClient(TATOR_URL, TOKEN)
        assert client.base_url == TATOR_URL
        assert client._headers == {
            'Content-Type': 'application/json',
            'Authorization': f'Token {TOKEN}',
        }

    @patch('requests.post', side_effect=mocked_requests_post)
    def test_login(self, _):
        token = TatorRestClient.login(TATOR_URL, 'testuser', 'password')
        assert token == 'my-token'

    @patch('requests.post', side_effect=mocked_requests_post)
    def test_login_invalid_credentials(self, _):
        with pytest.raises(requests.exceptions.HTTPError):
            TatorRestClient.login(TATOR_URL, 'baduser', 'badpass')

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_localizations_by_section(self, _):
        client = TatorRestClient(TATOR_URL, TOKEN)
        result = client.get_localizations(project_id=1, section='abc123')
        assert result == [{'id': 1}, {'id': 2}]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_localizations_by_media_id(self, _):
        client = TatorRestClient(TATOR_URL, TOKEN)
        result = client.get_localizations(project_id=1, media_id=[10, 20])
        assert result == [{'id': 3}]

    def test_get_localizations_no_args_raises(self):
        client = TatorRestClient(TATOR_URL, TOKEN)
        with pytest.raises(ValueError):
            client.get_localizations(project_id=1)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_section_by_id(self, _):
        client = TatorRestClient(TATOR_URL, TOKEN)
        result = client.get_section_by_id('section123')
        assert result == {'id': 'section123', 'name': 'Test Section'}

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_medias_for_section(self, _):
        client = TatorRestClient(TATOR_URL, TOKEN)
        result = client.get_medias_for_section(project_id=1, section='section123')
        assert result == [{'id': 10}, {'id': 20}]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_media_by_id(self, _):
        client = TatorRestClient(TATOR_URL, TOKEN)
        result = client.get_media_by_id('10')
        assert result == {'id': 10, 'name': 'test_media'}

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_substrates_groups_and_sorts_by_timestamp(self, _):
        client = TatorRestClient(TATOR_URL, TOKEN)
        transect_media = [
            {'id': 10, 'fps': 30.0},
            {'id': 20, 'fps': 25.0},
        ]
        result = client.get_substrates_for_medias(project_id=1, transect_media=transect_media)
        media_10 = next(r for r in result if r['media_id'] == 10)
        media_20 = next(r for r in result if r['media_id'] == 20)
        # substrates for media 10 should be sorted by timestamp (man @ 1s before sed @ 3s)
        assert media_10['substrates'] == [
            {'Relief': 'Flat', 'timestamp': '00:01', 'frame': 30},
            {'Relief': 'Low / moderate: Low (<1m)', 'timestamp': '00:03', 'frame': 90},
        ]
        assert media_20['substrates'] == [
            {'Relief': 'Flat', 'timestamp': '00:02', 'frame': 50},
        ]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_user(self, _):
        client = TatorRestClient(TATOR_URL, TOKEN)
        result = client.get_user(42)
        assert result == {'id': 42, 'username': 'testuser'}

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_frame(self, _):
        client = TatorRestClient(TATOR_URL, TOKEN)
        result = client.get_frame(media_id=10)
        assert result == b'fake-frame-bytes'

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_localization_graphic(self, _):
        client = TatorRestClient(TATOR_URL, TOKEN)
        result = client.get_localization_graphic(localization_id=99)
        assert result == b'fake-graphic-bytes'

    def test_format_timestamp_zero(self):
        assert TatorRestClient._format_timestamp(0) == '00:00'

    def test_format_timestamp_minutes_and_seconds(self):
        assert TatorRestClient._format_timestamp(90) == '01:30'

    def test_format_timestamp_rounds(self):
        assert TatorRestClient._format_timestamp(61.4) == '01:01'
