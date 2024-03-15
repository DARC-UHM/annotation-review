from unittest.mock import patch

from application.server.annotation_processor import AnnotationProcessor
from application.server.functions import parse_datetime
from test.data.vars_responses import ex_23060001, pomacentridae


class MockResponse:
    def __init__(self, req_url: str):
        self.req_url = req_url
        self.status_code = 200

    def json(self):
        match self.req_url:
            case 'NO_MATCH':
                return {}
            case 'http://hurlstor.soest.hawaii.edu:8086/query/dive/Deep%20Discoverer%2023060001':
                return ex_23060001
            case 'http://hurlstor.soest.hawaii.edu:8083/kb/v1/phylogeny/up/Pomacentridae':
                return pomacentridae
        return None


def mocked_requests_get(*args, **kwargs):
    return MockResponse(args[0])


class TestAnnotationProcessor:
    def test_init(self):
        annotation_processor = AnnotationProcessor(['Deep Discoverer 23060001'])
        assert annotation_processor.vessel_name == 'Deep Discoverer'
        assert annotation_processor.sequence_names == ['Deep Discoverer 23060001']

    def test_load_phylogeny(self):
        annotation_processor = AnnotationProcessor(['Deep Discoverer 23060001'])
        annotation_processor.load_phylogeny()
        assert len(annotation_processor.phylogeny.keys()) > 0

    @patch('application.server.annotation_processor.requests.get', side_effect=mocked_requests_get)
    def test_fetch_media(self, mock_get):
        annotation_processor = AnnotationProcessor(['Deep Discoverer 23060001'])
        sequence_videos = []
        annotation_processor.fetch_media(annotation_processor.sequence_names[0], sequence_videos)
        assert sequence_videos == [
            {
                'start_timestamp': parse_datetime('2023-08-24T18:30:00Z'),
                'uri': 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_01/EX2306_01_20230824T183000Z.m4v',
                'sequence_name': 'Deep Discoverer 23060001',
            },
            {
                'start_timestamp':  parse_datetime('2023-08-24T20:30:00Z'),
                'uri': 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_01/EX2306_01_20230824T203000Z.m4v',
                'sequence_name': 'Deep Discoverer 23060001',
            },
        ]
        assert len(annotation_processor.image_records) == 2

    @patch('application.server.annotation_processor.requests.get', side_effect=mocked_requests_get)
    def test_fetch_vars_phylogeny(self, mock_get):
        annotation_processor = AnnotationProcessor(['Deep Discoverer 23060001'])
        annotation_processor.fetch_vars_phylogeny('Pomacentridae')
        assert annotation_processor.phylogeny['Pomacentridae'] == {
            'phylum': 'Chordata',
            'subphylum': 'Vertebrata',
            'superclass': 'Pisces',
            'class': 'Actinopterygii',
            'order': 'Perciformes',
            'family': 'Pomacentridae',
        }

    def test_get_image_url_only_one(self):  # only one image to choose from
        annotation_processor = AnnotationProcessor(['Deep Discoverer 23060001'])
        assert annotation_processor.get_image_url(ex_23060001['annotations'][1]) \
               == 'https://hurlimage.soest.hawaii.edu/SupplementalPhotos/Hphotos/NA138photos/H1920/cam1_20220419064757.png'

    def test_get_image_url_png(self):  # multiple images to choose from, get the png
        annotation_processor = AnnotationProcessor(['Deep Discoverer 23060001'])
        assert annotation_processor.get_image_url(ex_23060001['annotations'][0]) \
               == 'https://hurlimage.soest.hawaii.edu/Hercules/images/1381920/20220418T202402.015Z--542830a8-ec69-4ee5-a57d-9de66a412dba.png'

    @patch('application.server.annotation_processor.requests.get', side_effect=mocked_requests_get)
    def test_get_video_url_first_media(self, mock_get):
        annotation_processor = AnnotationProcessor(['Deep Discoverer 23060001'])
        sequence_videos = []
        annotation_processor.fetch_media(annotation_processor.sequence_names[0], sequence_videos)
        assert annotation_processor.get_video_url(ex_23060001['annotations'][0], sequence_videos) \
               == 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_01/EX2306_01_20230824T183000Z.m4v#t=374'

    @patch('application.server.annotation_processor.requests.get', side_effect=mocked_requests_get)
    def test_get_video_url_second_media(self, mock_get):
        annotation_processor = AnnotationProcessor(['Deep Discoverer 23060001'])
        sequence_videos = []
        annotation_processor.fetch_media(annotation_processor.sequence_names[0], sequence_videos)
        assert annotation_processor.get_video_url(ex_23060001['annotations'][1], sequence_videos) \
               == 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_01/EX2306_01_20230824T203000Z.m4v#t=3505'
