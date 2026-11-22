import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from application.vars.beholder import Beholder

BASE_URL = 'https://some.cool.url/capture'
API_KEY = 'super-secret-api-key'
VIDEO_URL = 'https://some.cool.url/capture/some-cool-video.m4v'
JPEG_BYTES = b'\xff\xd8\xff\xe0fake-jpeg-data\xff\xd9'


def mock_response(status_code: int, content: bytes = b''):
    res = MagicMock()
    res.status_code = status_code
    res.content = content
    return res


class TestBeholder:
    def test_init(self):
        beholder = Beholder(base_url=BASE_URL, api_key=API_KEY)
        assert beholder.base_url == BASE_URL
        assert beholder.headers == {'X-API-Key': API_KEY}

    @patch('requests.post', return_value=mock_response(200, JPEG_BYTES))
    def test_get_frame_returns_image_bytes(self, mock_post):
        beholder = Beholder(base_url=BASE_URL, api_key=API_KEY)
        assert beholder.get_frame(video_url=VIDEO_URL, elapsed_time_millis=5000) == JPEG_BYTES

    @patch('requests.post', return_value=mock_response(200, JPEG_BYTES))
    def test_get_frame_request(self, mock_post):
        beholder = Beholder(base_url=BASE_URL, api_key=API_KEY)
        beholder.get_frame(video_url=VIDEO_URL, elapsed_time_millis=5000)
        mock_post.assert_called_once()
        kwargs = mock_post.call_args.kwargs
        assert kwargs['url'] == f'{BASE_URL}/capture'
        assert kwargs['headers']['X-API-Key'] == API_KEY
        assert json.loads(kwargs['data']) == {
            'videoUrl': VIDEO_URL,
            'elapsedTimeMillis': 5000,
        }

    @pytest.mark.parametrize('status_code', [400, 401, 404, 500, 503])
    def test_get_frame_non_200_raises(self, status_code):
        beholder = Beholder(base_url=BASE_URL, api_key=API_KEY)
        with patch('requests.post', return_value=mock_response(status_code)):
            with pytest.raises(ValueError):
                beholder.get_frame(video_url=VIDEO_URL, elapsed_time_millis=5000)

    @patch('requests.post', side_effect=requests.exceptions.ConnectionError('connection refused'))
    def test_get_frame_connection_error_propagates(self, mock_post):
        beholder = Beholder(base_url=BASE_URL, api_key=API_KEY)
        with pytest.raises(requests.exceptions.ConnectionError):
            beholder.get_frame(video_url=VIDEO_URL, elapsed_time_millis=5000)
