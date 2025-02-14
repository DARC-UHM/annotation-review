
import pytest
import json

from unittest.mock import patch

from application.server.annosaurus import Annosaurus, AuthenticationError
from test.data.vars_responses import ex_23060001


class MockResponse:
    def __init__(self, url: str, method: str, status_code: int, headers=None, data=None):
        self.url = url
        self.status_code = status_code
        self.method = method
        self.headers = headers or {}
        self.data = data

    def json(self):
        if self.status_code == 404:
            return {}
        if self.method == 'GET':
            match self.url:
                case 'http://localhost:test/observations/0059f860-4799-485f-c06c-5830e5ddd31e':
                    return ex_23060001['annotations'][0]
                case 'http://localhost:test/observations/0d9133d7-1d49-47d5-4b6d-6e4fb25dd41e':
                    return ex_23060001['annotations'][1]
                case 'http://localhost:test/observations/080118db-baa2-468a-d06a-144249c1d41e':
                    return ex_23060001['annotations'][2]
                case 'http://localhost:test/observations/35aa2bb9-d067-419b-9a6e-09cdce8ed41e':
                    return ex_23060001['annotations'][3]
                case 'http://localhost:test/observations/invalid':
                    return {}
        elif self.method == 'POST':
            match self.url:
                case 'http://localhost:test/auth':
                    if self.headers.get('Authorization') == 'APIKEY valid':
                        return {'access_token': 'jwt'}
                case 'http://localhost:test/associations':
                    data = self.data
                    del data['observation_uuid']
                    data['uuid'] = 'new_uuid'
                    return data
        elif self.method == 'PUT':
            match self.url:
                case 'http://localhost:test/annotations/0059f860-4799-485f-c06c-5830e5ddd31e':
                    annotation = ex_23060001['annotations'][0].copy()
                    annotation['concept'] = self.data['concept']
                    return annotation
                case 'http://localhost:test/associations/abc123':
                    data = self.data
                    data['uuid'] = 'abc123'
                    return self.data
                case 'http://localhost:test/associations/c4eaa100-comment':
                    data = self.data
                    data['uuid'] = 'c4eaa100-comment'
                    return self.data
                case 'http://localhost:test/associations/faf820ac-93fd-4d5a-486a-87775ec1d41e':
                    data = self.data
                    data['uuid'] = 'faf820ac-93fd-4d5a-486a-87775ec1d41e'
                    return self.data
                case 'http://localhost:test/associations/297d23d7-5979-46e7-6f66-8f1fcf8ed41e':
                    data = self.data
                    data['uuid'] = '297d23d7-5979-46e7-6f66-8f1fcf8ed41e'
                    return self.data
        elif self.method == 'DELETE':
            match self.url:
                case 'http://localhost:test/associations/abc123':
                    return {}
        raise json.JSONDecodeError('Unable to decode JSON', '', 0)

    def text(self):
        return '<html>Invalid</html>'


def mocked_requests_get(*args, **kwargs):
    return MockResponse(
        url=kwargs.get('url'),
        method='GET',
        status_code=200,
        headers=kwargs.get('headers'),
    )


def mocked_requests_get_404(*args, **kwargs):
    return MockResponse(
        url=kwargs.get('url'),
        method='GET',
        status_code=404,
        headers=kwargs.get('headers'),
    )


def mocked_requests_post(*args, **kwargs):
    return MockResponse(
        url=kwargs.get('url'),
        method='POST',
        status_code=201,
        headers=kwargs.get('headers'),
        data=kwargs.get('data'),
    )


def mocked_requests_put(*args, **kwargs):
    return MockResponse(
        url=kwargs.get('url'),
        method='PUT',
        status_code=200,
        headers=kwargs.get('headers'),
        data=kwargs.get('data'),
    )


def mocked_requests_delete(*args, **kwargs):
    return MockResponse(
        url=kwargs.get('url'),
        method='DELETE',
        status_code=204,
        headers=kwargs.get('headers'),
    )


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
        created = anno.create_association(
            observation_uuid='abc123',
            association=new_association,
            jwt='jwt',
        )
        assert created['status'] == 201
        assert created['json'] == {
            'link_name': 'test',
            'link_value': 'nil',
            'to_concept': 'test',
            'uuid': 'new_uuid',
        }

    def test_create_association_missing_link_value(self):
        anno = Annosaurus('http://localhost:test')
        with pytest.raises(ValueError):
            anno.create_association(
                observation_uuid='abc123',
                association={'to_concept': 'test'},
                jwt='jwt',
            )

    @patch('requests.put', side_effect=mocked_requests_put)
    def test_update_association(self, _):
        anno = Annosaurus('http://localhost:test')
        updated = anno.update_association(
            association_uuid='abc123',
            association={'link_name': 'test', 'to_concept': 'test'},
            jwt='jwt',
        )
        assert updated['status'] == 200
        assert updated['json'] == {
            'link_name': 'test',
            'to_concept': 'test',
            'uuid': 'abc123',
        }

    @patch('requests.delete', side_effect=mocked_requests_delete)
    def test_delete_association(self, _):
        anno = Annosaurus('http://localhost:test')
        deleted = anno.delete_association(
            association_uuid='abc123',
            jwt='jwt',
        )
        assert deleted['status'] == 204
        assert deleted['json'] == {}

    @patch('requests.put', side_effect=mocked_requests_put)
    def test_update_concept_name(self, _):
        anno = Annosaurus('http://localhost:test')
        updated = anno.update_concept_name(
            observation_uuid='0059f860-4799-485f-c06c-5830e5ddd31e',
            concept='Magikarp',
            jwt='jwt',
        )
        old_anno = ex_23060001['annotations'][0].copy()
        old_anno['concept'] = 'Magikarp'
        assert updated['status'] == 200
        assert updated['json'] == old_anno

    @patch('requests.get', side_effect=mocked_requests_get_404)
    def test_update_annotation_comment_404(self, _):
        anno = Annosaurus('http://localhost:test')
        updated = anno.update_annotation_comment(
            observation_uuid='invalid',
            reviewers=['Test Reviewer'],
            jwt='jwt',
        )
        assert updated['status'] == 404
        assert updated['json'] == {}

    @patch('requests.get', side_effect=mocked_requests_get)
    @patch('requests.post', side_effect=mocked_requests_post)
    def test_update_annotation_comment_new_one_reviewer(self, _, __):
        anno = Annosaurus('http://localhost:test')
        created = anno.update_annotation_comment(
            observation_uuid='0059f860-4799-485f-c06c-5830e5ddd31e',
            reviewers=['Test Reviewer'],
            jwt='jwt',
        )
        assert created['status'] == 201
        assert created['json'] == {
            'link_name': 'comment',
            'link_value': 'Added for review: Test Reviewer',
            'to_concept': 'self',
            'uuid': 'new_uuid'
        }

    @patch('requests.get', side_effect=mocked_requests_get)
    @patch('requests.post', side_effect=mocked_requests_post)
    def test_update_annotation_comment_new_multiple_reviewers(self, _, __):
        anno = Annosaurus('http://localhost:test')
        created = anno.update_annotation_comment(
            observation_uuid='0059f860-4799-485f-c06c-5830e5ddd31e',
            reviewers=['Test Reviewer', 'Ronald McDonald'],
            jwt='jwt',
        )
        assert created['status'] == 201
        assert created['json'] == {
            'link_name': 'comment',
            'link_value': 'Added for review: Test Reviewer, Ronald McDonald',
            'to_concept': 'self',
            'uuid': 'new_uuid'
        }

    @patch('requests.get', side_effect=mocked_requests_get)
    @patch('requests.put', side_effect=mocked_requests_put)
    def test_update_annotation_comment_update_no_prev_reviewers(self, _, __):
        anno = Annosaurus('http://localhost:test')
        updated = anno.update_annotation_comment(
            observation_uuid='0d9133d7-1d49-47d5-4b6d-6e4fb25dd41e',
            reviewers=['J. Dolan'],
            jwt='jwt',
        )
        assert updated['status'] == 200
        assert updated['json'] == {
            'link_value': 'this is a comment; Added for review: J. Dolan',
            'uuid': 'c4eaa100-comment'
        }

    @patch('requests.get', side_effect=mocked_requests_get)
    @patch('requests.put', side_effect=mocked_requests_put)
    def test_update_annotation_comment_update_prev_reviewers_add(self, _, __):
        anno = Annosaurus('http://localhost:test')
        updated = anno.update_annotation_comment(
            observation_uuid='080118db-baa2-468a-d06a-144249c1d41e',
            reviewers=['J. Dolan', 'Don Draper'],
            jwt='jwt',
        )
        assert updated['status'] == 200
        assert updated['json'] == {
            'link_value': 'Added for review: J. Dolan, Don Draper',
            'uuid': 'faf820ac-93fd-4d5a-486a-87775ec1d41e'
        }

    @patch('requests.get', side_effect=mocked_requests_get)
    @patch('requests.put', side_effect=mocked_requests_put)
    def test_update_annotation_comment_update_prev_reviewers_replace(self, _, __):
        anno = Annosaurus('http://localhost:test')
        updated = anno.update_annotation_comment(
            observation_uuid='080118db-baa2-468a-d06a-144249c1d41e',
            reviewers=['J. Dolan'],
            jwt='jwt',
        )
        assert updated['status'] == 200
        assert updated['json'] == {
            'link_value': 'Added for review: J. Dolan',
            'uuid': 'faf820ac-93fd-4d5a-486a-87775ec1d41e'
        }

    @patch('requests.get', side_effect=mocked_requests_get)
    @patch('requests.delete', side_effect=mocked_requests_delete)
    def test_update_annotation_comment_delete_empty(self, _, __):
        anno = Annosaurus('http://localhost:test')
        deleted = anno.update_annotation_comment(
            observation_uuid='080118db-baa2-468a-d06a-144249c1d41e',
            reviewers=[],
            jwt='jwt',
        )
        assert deleted['status'] == 204
        assert deleted['json'] == {}

    @patch('requests.get', side_effect=mocked_requests_get)
    @patch('requests.put', side_effect=mocked_requests_put)
    def test_update_annotation_comment_delete_not_empty(self, _, __):
        anno = Annosaurus('http://localhost:test')
        deleted = anno.update_annotation_comment(
            observation_uuid='35aa2bb9-d067-419b-9a6e-09cdce8ed41e',
            reviewers=[],
            jwt='jwt',
        )
        assert deleted['status'] == 200
        assert deleted['json'] == {
            'link_value': 'This is a weird lookin sponge thing!',
            'uuid': '297d23d7-5979-46e7-6f66-8f1fcf8ed41e'
        }
