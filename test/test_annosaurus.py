import pytest
import json

from unittest.mock import patch

from application.server.annosaurus import Annosaurus, AuthenticationError
from test.data.vars_responses import ex_23060001


class MockResponse:
    def __init__(self, req_url: str, method: str, status_code: int, headers=None):
        self.req_url = req_url
        self.status_code = status_code
        self.method = method
        self.headers = headers or {}

    def json(self):
        if self.method == 'GET':
            match self.req_url:
                case 'http://localhost:test/observations/abc123':
                    return ex_23060001['annotations'][0]
                case 'http://localhost:test/observations/invalid':
                    return {}
        elif self.method == 'POST':
            match self.req_url:
                case 'http://localhost:test/auth':
                    if self.headers.get('Authorization') == 'APIKEY valid':
                        return {'access_token': 'jwt'}
                case 'http://localhost:test/associations':
                    return {'status': self.status_code, 'json': {'link_name': 'test', 'to_concept': 'test'}}
        elif self.method == 'PUT':
            match self.req_url:
                case 'http://localhost:test/associations/abc123':
                    return {}
                case 'http://localhost:test/annotations/abc123':
                    return {}
        elif self.method == 'DELETE':
            match self.req_url:
                case 'http://localhost:test/associations/abc123':
                    return {}
        raise json.JSONDecodeError('Unable to decode JSON', '', 0)

    def text(self):
        return '<html>Invalid</html>'


def mocked_requests_get(*args, **kwargs):
    return MockResponse(args[0], method='GET', status_code=200, headers=kwargs.get('headers'))


def mocked_requests_get_404(*args, **kwargs):
    return MockResponse(args[0], method='GET', status_code=404, headers=kwargs.get('headers'))


def mocked_requests_post(*args, **kwargs):
    return MockResponse(args[0], method='POST', status_code=201, headers=kwargs.get('headers'))


def mocked_requests_put(*args, **kwargs):
    return MockResponse(args[0], method='PUT', status_code=200, headers=kwargs.get('headers'))


def mocked_requests_delete(*args, **kwargs):
    return MockResponse(args[0], method='DELETE', status_code=200, headers=kwargs.get('headers'))


class TestAnnosaurus:
    def test_init(self):
        anno = Annosaurus('http://localhost:test/')
        assert anno.base_url == 'http://localhost:test'

    def test_authorize_jwt(self):
        anno = Annosaurus('http://localhost:test/')
        assert anno.authorize(jwt='jwt') == 'jwt'

    @patch('requests.post', side_effect=mocked_requests_post)
    def test_authorize_client_secret(self, mock_post):
        anno = Annosaurus('http://localhost:test/')
        assert anno.authorize(client_secret='valid') == 'jwt'
        assert mock_post.call_args[1]['headers'] == {'Authorization': 'APIKEY valid'}

    @patch('requests.post', side_effect=mocked_requests_post)
    def test_authorize_invalid(self, _):
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
    def test_create_association(self, _):
        anno = Annosaurus('http://localhost:test')
        new_association = {'link_name': 'test', 'to_concept': 'test'}
        res = anno.create_association(
            observation_uuid='abc123',
            association=new_association,
            jwt='jwt',
        )
        assert res['status'] == 201
        assert res['json'] == new_association

    def test_create_association_missing_link_value(self):
        anno = Annosaurus('http://localhost:test')
        with pytest.raises(ValueError):
            anno.create_association(
                observation_uuid='abc123',
                association={'to_concept': 'test'},
                jwt='jwt',
            )
    """
    @patch('requests.put', side_effect=mocked_requests_put)
    def test_update_association(self, _):
        anno = Annosaurus('http://localhost:test')
        assert anno.update_association(
            observation_uuid='abc123',
            association={'link_name': 'test', 'to_concept': 'test'},
            jwt='jwt',
        ) == 200

    @patch('requests.delete', side_effect=mocked_requests_delete)
    def test_delete_association(self, _):
        anno = Annosaurus('http://localhost:test')
        assert anno.delete_association(
            observation_uuid='abc123',
            jwt='jwt',
        ) == 200

    @patch('requests.get', side_effect=mocked_requests_get_404)
    def test_update_annotation_404(self, _):
        anno = Annosaurus('http://localhost:test')
        assert anno.update_annotation(
            observation_uuid='invalid',
            updated_annotation={},
            jwt='jwt',
        ) == 404

    @patch('requests.get', side_effect=mocked_requests_get)
    @patch('requests.put', side_effect=mocked_requests_put)
    def test_update_annotation_concept_name(self, _, __):
        anno = Annosaurus('http://localhost:test')
        assert anno.update_annotation(
            observation_uuid='abc123',
            updated_annotation={
                'concept': 'Magikarp',
                'identity-certainty': '',
                'identity-reference': '',
                'upon': 'sed',
                'comment': '',
                'guide-photo': '',
            },
            jwt='jwt',
        ) == 200

    @patch('requests.get', side_effect=mocked_requests_get)
    @patch('requests.put', side_effect=mocked_requests_put)
    def test_update_annotation_id_certainty(self, _, __):
        anno = Annosaurus('http://localhost:test')
        anno.update_annotation(
            observation_uuid='abc123',
            updated_annotation={
                'concept': 'Magikarp',
                'identity-certainty': None,
                'identity-reference': None,
                'upon': 'sed',
                'comment': None,
                'guide-photo': None,
            },
            jwt='jwt',
        )
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
    """
