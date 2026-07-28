import datetime
from json import JSONDecodeError
from unittest.mock import patch

import requests

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

    @patch('application.main.requests.get', side_effect=mocked_get)
    def test_index_checks_for_updates_when_stale(self, mock_get, app, client):
        app.config['UPDATE_AVAILABLE'] = False
        app.config['LAST_CHECKED_ORIGIN_AT'] = (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat()
        app.config['LOCAL_COMMIT_HASH'] = 'abc123'

        with patch('subprocess.run') as mock_run, patch('subprocess.check_output', return_value=b'def456\n'):
            response = client.get('/')

        assert response.status_code == 200
        mock_run.assert_called_once()
        assert app.config['UPDATE_AVAILABLE'] is True  # 'def456' != 'abc123'

    @patch('application.main.requests.get', side_effect=mocked_get)
    def test_index_treats_git_fetch_failure_as_no_update_available(self, mock_get, app, client):
        app.config['UPDATE_AVAILABLE'] = False
        app.config['LAST_CHECKED_ORIGIN_AT'] = (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat()
        app.config['LOCAL_COMMIT_HASH'] = 'abc123'

        with patch('subprocess.run', side_effect=FileNotFoundError('git not found')):
            response = client.get('/')

        assert response.status_code == 200
        assert app.config['UPDATE_AVAILABLE'] is False
        # check marked as having run so it doesn't retry on every single request
        assert app.config['LAST_CHECKED_ORIGIN_AT'] is not None
