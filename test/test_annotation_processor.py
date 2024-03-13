from unittest.mock import patch

from application.server.annotation_processor import AnnotationProcessor
from test.mock_response import MockResponse


def mocked_requests_get(*args, **kwargs):
    return MockResponse(args[0])


class TestAnnotationProcessor:
    def test_init(self):
        annotation_processor = AnnotationProcessor(['Deep Discoverer 23060001'])
        assert annotation_processor.vessel_name == 'Deep Discoverer'
        assert annotation_processor.sequence_names == ['Deep Discoverer 23060001']

    @patch('application.server.annotation_processor.requests.get', side_effect=mocked_requests_get)
    def test_fetch_images(self):
        annotation_processor = AnnotationProcessor(['Deep Discoverer 23060001'])
        annotation_processor.fetch_images(annotation_processor.sequence_names[0])
