import re
from unittest.mock import MagicMock, patch

import pytest
import requests

from application.image_review.expedition_status.routes import REVIEW_SERVER_TIMEOUT

ROUTES = 'application.image_review.expedition_status.routes'


def _response(payload=None, status_code=200, text='error'):
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    if isinstance(payload, Exception):
        response.json.side_effect = payload
    else:
        response.json.return_value = payload
    return response


def _checkbox_status(html, expedition_name):
    match = re.search(
        rf'data-expedition="{re.escape(expedition_name)}"\s+data-status="(\d)"',
        html,
    )
    assert match, expedition_name
    return match.group(1)


class TestExpeditionStatusPage:
    @patch(f'{ROUTES}.requests.get')
    def test_renders_statuses_from_the_review_server(self, mock_get, client):
        mock_get.return_value = _response([
            {'expedition_name': 'Deep Discoverer-2605', 'status': 1},
            {'expedition_name': 'DOEX0114_RMI_2026', 'status': 2},
            {'expedition_name': 'VUT_2025', 'status': 0},
        ])

        response = client.get('/image-review/expedition-status')

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert _checkbox_status(html, 'Deep Discoverer-2605') == '1'
        assert _checkbox_status(html, 'DOEX0114_RMI_2026') == '2'
        assert _checkbox_status(html, 'VUT_2025') == '0'
        assert 'Not started' in html
        assert 'In progress' in html
        assert 'Submitted' in html
        # one request for the whole list, with a timeout
        mock_get.assert_called_once()
        assert mock_get.call_args.args[0].endswith('/expedition-status')
        assert mock_get.call_args.kwargs['timeout'] == REVIEW_SERVER_TIMEOUT

    @patch(f'{ROUTES}.requests.get')
    def test_escapes_expedition_names(self, mock_get, client):
        mock_get.return_value = _response([{'expedition_name': '<script>x</script>', 'status': 0}])

        html = client.get('/image-review/expedition-status').get_data(as_text=True)

        assert '<script>x</script>' not in html
        assert '&lt;script&gt;x&lt;/script&gt;' in html

    @patch(f'{ROUTES}.requests.get')
    def test_server_error_flashes(self, mock_get, client):
        mock_get.return_value = _response({}, status_code=503)

        response = client.get('/image-review/expedition-status')

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert 'Unable to load expedition statuses from the external review server.' in html
        assert 'No expeditions found.' in html

    @pytest.mark.parametrize('failure', [
        requests.ConnectionError('down'),
        requests.Timeout('slow'),
    ])
    @patch(f'{ROUTES}.requests.get')
    def test_unreachable_server_flashes(self, mock_get, client, failure):
        mock_get.side_effect = failure

        response = client.get('/image-review/expedition-status')

        assert response.status_code == 200
        assert 'Unable to reach the external review server.' in response.get_data(as_text=True)

    @patch(f'{ROUTES}.requests.get')
    def test_non_json_response_flashes(self, mock_get, client):
        mock_get.return_value = _response(ValueError('not json'))

        response = client.get('/image-review/expedition-status')

        assert response.status_code == 200
        assert 'Unable to reach the external review server.' in response.get_data(as_text=True)


class TestPatchExpeditionStatus:
    @pytest.mark.parametrize('status', [0, 1, 2])
    @patch(f'{ROUTES}.requests.patch')
    def test_forwards_status_to_the_review_server(self, mock_patch, client, status):
        mock_patch.return_value = _response({'expedition_name': 'Deep Discoverer-2605', 'status': status})

        response = client.patch('/image-review/expedition-status', json={
            'expedition_name': 'Deep Discoverer-2605',
            'status': status,
        })

        assert response.status_code == 200
        assert response.json['status'] == status
        assert mock_patch.call_args.kwargs['json'] == {'status': status}
        assert mock_patch.call_args.kwargs['url'].endswith('/expedition-status/Deep%20Discoverer-2605')
        assert mock_patch.call_args.kwargs['timeout'] == REVIEW_SERVER_TIMEOUT

    @patch(f'{ROUTES}.requests.patch')
    def test_quotes_slashes_in_the_name(self, mock_patch, client):
        mock_patch.return_value = _response({'expedition_name': 'a/b', 'status': 1})

        client.patch('/image-review/expedition-status', json={'expedition_name': 'a/b', 'status': 1})

        assert mock_patch.call_args.kwargs['url'].endswith('/expedition-status/a%2Fb')

    @pytest.mark.parametrize('body', [
        {},
        {'status': 1},
        {'expedition_name': 'VUT_2025'},
        {'expedition_name': '  ', 'status': 1},
        {'expedition_name': 5, 'status': 1},
        {'expedition_name': 'VUT_2025', 'status': 3},
        {'expedition_name': 'VUT_2025', 'status': '1'},
        {'expedition_name': 'VUT_2025', 'status': True},
        {'expedition_name': 'VUT_2025', 'status': 1.5},
        {'expedition_name': 'VUT_2025', 'status': None},
        ['VUT_2025', 1],
    ])
    @patch(f'{ROUTES}.requests.patch')
    def test_rejects_bad_bodies(self, mock_patch, client, body):
        response = client.patch('/image-review/expedition-status', json=body)

        assert response.status_code == 400
        mock_patch.assert_not_called()

    @patch(f'{ROUTES}.requests.patch')
    def test_unreachable_server_is_502(self, mock_patch, client):
        mock_patch.side_effect = requests.ConnectionError('down')

        response = client.patch('/image-review/expedition-status', json={'expedition_name': 'VUT_2025', 'status': 1})

        assert response.status_code == 502
        assert response.json == {'error': 'Unable to reach the external review server'}

    @patch(f'{ROUTES}.requests.patch')
    def test_non_json_error_keeps_the_status_code(self, mock_patch, client):
        mock_patch.return_value = _response(ValueError('not json'), status_code=500)

        response = client.patch('/image-review/expedition-status', json={'expedition_name': 'VUT_2025', 'status': 1})

        assert response.status_code == 500
        assert response.json == {'error': 'External review server returned 500'}

    @patch(f'{ROUTES}.requests.patch')
    def test_review_server_errors_are_passed_through(self, mock_patch, client):
        mock_patch.return_value = _response({'error': 'Unauthorized'}, status_code=401)

        response = client.patch('/image-review/expedition-status', json={'expedition_name': 'VUT_2025', 'status': 1})

        assert response.status_code == 401
        assert response.json == {'error': 'Unauthorized'}
