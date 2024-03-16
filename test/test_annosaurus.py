from unittest.mock import patch


class MockResponse:
    def __init__(self, req_url: str):
        self.req_url = req_url
        self.status_code = 200

    def json(self):
        match self.req_url:
            case 'todo':
                return None
        return None


def mocked_requests_get(*args, **kwargs):
    return MockResponse(args[0])


class TestAnnosaurus:
    def test_create_association(self):
        assert False

    def test_create_association_invalid(self):
        assert False

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
