import datetime
from json import JSONDecodeError
from unittest.mock import patch

import pytest
import requests

from application import create_app
from application.main import server_error


class MockMainResponse:
    def __init__(self, json_data=None, status_code=200, json_error=False):
        self._json_data = json_data
        self.status_code = status_code
        self._json_error = json_error

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f'{self.status_code} error')

    def json(self):
        if self._json_error:
            raise JSONDecodeError('bad json', 'doc', 0)
        return self._json_data


def mocked_get(url, headers=None):
    if 'reviewer/all' in url:
        return MockMainResponse([{'name': 'Bob'}])
    if 'stats' in url:
        return MockMainResponse({
            'unread_comments': 2,
            'read_comments': 3,
            'total_comments': 5,
            'active_reviewers': ['Bob'],
        })
    if 'videosequences/names' in url:
        return MockMainResponse(['Dive 1'])
    if 'concept' in url:
        return MockMainResponse(['Concept1'])
    return MockMainResponse({})


def mocked_get_with_github(github_response):
    def _get(url, headers=None, timeout=None):
        if 'api.github.com' in url:
            if isinstance(github_response, Exception):
                raise github_response
            return github_response
        return mocked_get(url, headers)
    return _get


class TestMain:
    def test_favicon(self, client):
        response = client.get('/favicon.ico')
        assert response.status_code == 200

    def test_video(self, client):
        response = client.get('/video?link=https://example.com/video.mp4&time=42')
        assert response.status_code == 200
        assert b'https://example.com/video.mp4#t=42' in response.data

    def test_page_not_found_renders_404(self, client):
        response = client.get('/this-route-does-not-exist')
        assert response.status_code == 404
        assert b'Page not found' in response.data

    def test_server_error_renders_500_and_skips_webhook_outside_production(self, app):
        app.config['ENV'] = 'development'
        with app.test_request_context('/'), patch('requests.post') as mock_post:
            _, status_code = server_error(ValueError('oh no!'))

        assert status_code == 500
        mock_post.assert_not_called()

    def test_server_error_logs_to_darc_review_in_production(self, app):
        app.config['ENV'] = 'production'
        with app.test_request_context('/some-page'), patch('requests.post') as mock_post:
            server_error(ValueError('oh no!'))

        mock_post.assert_called_once()
        assert mock_post.call_args.kwargs['json']['url'].endswith('/some-page')

    @patch('application.main.requests.get', side_effect=mocked_get)
    def test_index_fetches_data_and_populates_session(self, mock_get, client):
        response = client.get('/')

        assert response.status_code == 200
        with client.session_transaction() as session:
            assert session['vars_video_sequences'] == ['Dive 1']
            assert session['vars_concepts'] == ['Concept1']
            assert session['reviewers'] == [{'name': 'Bob'}]

    @patch('application.main.requests.get')
    def test_index_flashes_error_when_a_fetch_fails(self, mock_get, client):
        mock_get.side_effect = requests.exceptions.ConnectionError('connection refused')

        response = client.get('/')

        assert response.status_code == 200
        assert b'Unable to connect' in response.data
        # falls back to empty session values rather than failing the whole page
        with client.session_transaction() as session:
            assert session['vars_video_sequences'] == []

    @patch('application.main.requests.get', return_value=MockMainResponse(json_error=True))
    def test_index_flashes_error_when_json_parsing_fails(self, mock_get, client):
        response = client.get('/')

        assert response.status_code == 200
        assert b'Failed to parse JSON' in response.data

    def test_create_app_records_local_commit_for_update_check(self):
        with patch('application.subprocess.check_output', return_value=b'abc123\n'):
            app = create_app()

        assert app.config['LOCAL_COMMIT_HASH'] == 'abc123'
        assert app.config['LAST_CHECKED_ORIGIN_AT'] is not None

    def test_index_shows_update_banner_when_github_main_is_ahead(self, app, client):
        app.config['UPDATE_AVAILABLE'] = False
        app.config['LAST_CHECKED_ORIGIN_AT'] = (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat()
        app.config['LOCAL_COMMIT_HASH'] = 'abc123'
        github_response = MockMainResponse({'status': 'ahead', 'ahead_by': 2, 'behind_by': 0})

        with patch('application.main.requests.get', side_effect=mocked_get_with_github(github_response)) as mock_get:
            response = client.get('/')

        assert response.status_code == 200
        assert app.config['UPDATE_AVAILABLE'] is True
        assert b'Update available!' in response.data
        assert any('compare/abc123...main' in call.args[0] for call in mock_get.call_args_list)

    @pytest.mark.parametrize('github_response', [
        MockMainResponse({'status': 'identical', 'ahead_by': 0, 'behind_by': 0}),
        MockMainResponse({'status': 'behind', 'ahead_by': 0, 'behind_by': 3}),  # local has unreleased commits
        MockMainResponse(status_code=404),  # local commit was never pushed
        requests.exceptions.ConnectionError('no internet'),
    ])
    def test_index_no_update_banner_when_not_behind_github(self, github_response, app, client):
        app.config['UPDATE_AVAILABLE'] = False
        app.config['LAST_CHECKED_ORIGIN_AT'] = (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat()
        app.config['LOCAL_COMMIT_HASH'] = 'abc123'

        with patch('application.main.requests.get', side_effect=mocked_get_with_github(github_response)):
            response = client.get('/')

        assert response.status_code == 200
        assert app.config['UPDATE_AVAILABLE'] is False
        assert b'Update available!' not in response.data
        # check marked as having run so it doesn't retry on every single request
        last_check = datetime.datetime.fromisoformat(app.config['LAST_CHECKED_ORIGIN_AT'])
        assert datetime.datetime.now() - last_check < datetime.timedelta(minutes=1)

    def test_index_skips_update_check_when_recently_checked(self, app, client):
        app.config['UPDATE_AVAILABLE'] = False
        app.config['LAST_CHECKED_ORIGIN_AT'] = datetime.datetime.now().isoformat()

        with patch('application.main.requests.get', side_effect=mocked_get) as mock_get:
            client.get('/')

        assert not any('api.github.com' in call.args[0] for call in mock_get.call_args_list)
