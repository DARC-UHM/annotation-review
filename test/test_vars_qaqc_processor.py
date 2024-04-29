from unittest.mock import patch

from application.server.functions import parse_datetime
from application.server.vars_qaqc_processor import VarsQaqcProcessor
from test.data.vars_responses import ex_23060001, pomacentridae



class MockResponse:
    def __init__(self, url: str):
        self.url = url
        self.status_code = 200

    def json(self):
        match self.url:
            case 'http://hurlstor.soest.hawaii.edu:8086/query/dive/Deep%20Discoverer%2023060001':
                return ex_23060001
            case 'http://hurlstor.soest.hawaii.edu:8083/kb/v1/phylogeny/up/Pomacentridae':
                return pomacentridae
        return None


def mocked_requests_get(*args, **kwargs):
    return MockResponse(url=kwargs.get('url'))


class TestVarsQaqcProcessor:
    def test_init(self):
        qaqc_processor = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        assert qaqc_processor.sequence_names == ['Deep Discoverer 23060001']
        assert qaqc_processor.videos == []
        assert qaqc_processor.working_records == []
        assert qaqc_processor.final_records == []
        assert len(qaqc_processor.phylogeny.keys()) > 0

    def test_load_phylogeny(self):
        annotation_processor = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        annotation_processor.load_phylogeny()
        assert len(annotation_processor.phylogeny.keys()) > 0

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_fetch_annotations(self, _):
        qaqc_processor = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        assert qaqc_processor.fetch_annotations('Deep Discoverer 23060001') == ex_23060001['annotations']
        assert qaqc_processor.videos == [
            {
                'start_timestamp': parse_datetime('2023-08-24T18:30:00Z'),
                'uri': 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_01/EX2306_01_20230824T183000Z.m4v',
                'sequence_name': 'Deep Discoverer 23060001',
                'video_reference_uuid': 'dda3dc62-9f78-4dbb-91cd-5015026e0434',
            },
            {
                'start_timestamp':  parse_datetime('2023-08-24T20:30:00Z'),
                'uri': 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_01/EX2306_01_20230824T203000Z.m4v',
                'sequence_name': 'Deep Discoverer 23060001',
                'video_reference_uuid': 'd955c4ef-94e0-4f0d-83f5-d0144a09a933',
            },
        ]

    def test_tests_done(self):
        assert False
