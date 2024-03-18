import pytest
import json

from unittest.mock import patch

from application.server.annosaurus import Annosaurus, AuthenticationError


class MockResponse:
    def __init__(self, req_url: str, method: str = 'GET', headers=None):
        self.req_url = req_url
        self.status_code = 201 if method == 'POST' else 200
        self.method = method
        self.headers = headers or {}

    def json(self):
        if self.method == 'POST':
            self.status_code = 201
            match self.req_url:
                case 'http://localhost:test/auth':
                    if self.headers.get('Authorization') == 'APIKEY valid':
                        return {'access_token': 'jwt'}
                case 'http://localhost:test/associations':
                    return {}
        self.status_code = 400
        raise json.JSONDecodeError('Unable to decode JSON', '', 0)

    def text(self):
        return '<html>Invalid</html>'


def mocked_requests_get(*args, **kwargs):
    return MockResponse(args[0], headers=kwargs.get('headers'))


def mocked_requests_post(*args, **kwargs):
    return MockResponse(args[0], method='POST', headers=kwargs.get('headers'))


def mocked_requests_put(*args, **kwargs):
    return MockResponse(args[0], method='PUT', headers=kwargs.get('headers'))


class TestAnnosaurus:
    def test_init(self):
        anno = Annosaurus('http://localhost:test/')
        assert anno.base_url == 'http://localhost:test'

    def test_authorize_jwt(self):
        anno = Annosaurus('http://localhost:test/')
        assert anno.authorize(jwt='jwt') == 'jwt'

    @patch('requests.post', side_effect=mocked_requests_post)
    def test_authorize_client_secret(self, mock_get):
        anno = Annosaurus('http://localhost:test/')
        assert anno.authorize(client_secret='valid') == 'jwt'
        assert mock_get.call_args[1]['headers'] == {'Authorization': 'APIKEY valid'}

    @patch('requests.post', side_effect=mocked_requests_post)
    def test_authorize_invalid(self, mock_get):
        anno = Annosaurus('http://localhost:test/')
        with pytest.raises(AuthenticationError):
            anno.authorize(client_secret='invalid')

    def test_authorize_none(self):
        anno = Annosaurus('http://localhost:test/')
        with pytest.raises(AuthenticationError):
            anno.authorize()

    def test_auth_header(self):
        anno = Annosaurus('http://localhost:test/')
        assert anno._auth_header('jwt') == {'Authorization': 'Bearer jwt'}

    @patch('requests.post', side_effect=mocked_requests_post)
    def test_create_association(self, mock_get):
        anno = Annosaurus('http://localhost:test')
        assert anno.create_association(
            observation_uuid='abc123',
            association={'link_name': 'test', 'to_concept': 'test'},
            jwt='jwt'
        ) == 201

    def test_create_association_missing_link_value(self):
        anno = Annosaurus('http://localhost:test')
        with pytest.raises(ValueError):
            anno.create_association(
                observation_uuid='abc123',
                association={'to_concept': 'test'},
                jwt='jwt'
            )

    def test_update_association(self):
        assert False

    def test_update_association_invalid(self):
        assert False

    def test_delete_association(self):
        assert False

    def test_update_annotation_invalid(self):
        assert False

    def test_update_annotation_id_certainty(self):
        assert False

    def test_update_annotation_id_ref(self):
        assert False

    def test_update_annotation_upon(self):
        assert False

    def test_update_annotation_comment(self):
        assert False

    def test_update_annotation_guide_photo(self):
        assert False

    def test_update_annotation_multiple(self):
        assert False

    def test_update_annotation_comment_invalid(self):
        assert False

    def test_update_annotation_comment_empty(self):
        assert False

    def test_update_annotation_comment_not_empty(self):
        assert False

    def test_update_annotation_comment_empty_delete(self):
        assert False

    def test_update_annotation_comment_not_empty_delete(self):
        assert False
