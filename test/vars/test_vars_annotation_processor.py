from unittest.mock import patch

import pytest

from application.vars.vars_annotation_processor import VarsAnnotationProcessor
from application.util.functions import parse_datetime
from test.data.vars_responses import ex_23060001
from test.util.mock_response import MockResponse


def mocked_requests_get(*args, **kwargs):
    return MockResponse(url=kwargs.get('url'))


class MockJsonResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data


@pytest.mark.usefixtures('mock_phylogeny_cache')
class TestVarsAnnotationProcessor:
    def test_init(self):
        annotation_processor = VarsAnnotationProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        assert annotation_processor.vessel_name == 'Deep Discoverer'
        assert annotation_processor.sequence_names == ['Deep Discoverer 23060001']
        assert annotation_processor.highest_id_ref == 0
        assert annotation_processor.videos == []
        assert annotation_processor.working_records == []
        assert annotation_processor.final_records == []
        assert len(annotation_processor.phylogeny.data.keys()) > 0

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_fetch_media(self, mock_get):
        annotation_processor = VarsAnnotationProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        annotation_processor.process_sequences()
        assert annotation_processor.videos == [
            {
                'start_timestamp': parse_datetime('2023-08-24T18:30:00Z'),
                'uri': 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_01/EX2306_01_20230824T183000Z.m4v',
                'sequence_name': 'Deep Discoverer 23060001',
                'video_reference_uuid': 'dda3dc62-9f78-4dbb-91cd-5015026e0434',
                'duration_millis': 7199993,
            },
            {
                'start_timestamp':  parse_datetime('2023-08-24T20:30:00Z'),
                'uri': 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_01/EX2306_01_20230824T203000Z.m4v',
                'sequence_name': 'Deep Discoverer 23060001',
                'video_reference_uuid': 'd955c4ef-94e0-4f0d-83f5-d0144a09a933',
                'duration_millis': 7199993,
            },
        ]

    # TODO move to PhylogenyCache test
    @patch('requests.get', side_effect=mocked_requests_get)
    def test_fetch_vars_phylogeny(self, mock_get):
        annotation_processor = VarsAnnotationProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        annotation_processor.phylogeny.fetch_vars(
            concept_name='Pomacentridae',
            vars_kb_url=MockResponse.VARS_KB_URL,
            no_match_records=set()
        )
        assert annotation_processor.phylogeny.data['Pomacentridae'] == {
            'phylum': 'Chordata',
            'subphylum': 'Vertebrata',
            'superclass': 'Pisces',
            'class': 'Actinopterygii',
            'order': 'Perciformes',
            'family': 'Pomacentridae',
        }

    def test_get_image_url_only_one(self):  # only one image to choose from
        assert VarsAnnotationProcessor.get_image_url(ex_23060001['annotations'][1]) \
               == 'https://hurlimage.soest.hawaii.edu/SupplementalPhotos/Hphotos/NA138photos/H1920/cam1_20220419064757.png'

    def test_get_image_url_png(self):  # multiple images to choose from, get the png
        assert VarsAnnotationProcessor.get_image_url(ex_23060001['annotations'][0]) \
               == 'https://hurlimage.soest.hawaii.edu/Hercules/images/1381920/20220418T202402.015Z--542830a8-ec69-4ee5-a57d-9de66a412dba.png'

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_video(self, mock_get):
        annotation_processor = VarsAnnotationProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        annotation_processor.process_sequences()
        assert annotation_processor.get_video(ex_23060001['annotations'][0])['uri'] \
               == 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_01/EX2306_01_20230824T183000Z.m4v#t=374'

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_video_url_second_media(self, mock_get):
        annotation_processor = VarsAnnotationProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        annotation_processor.process_sequences()
        assert annotation_processor.get_video(ex_23060001['annotations'][1])['uri'] \
               == 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_01/EX2306_01_20230824T203000Z.m4v#t=3505'

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_process_images(self, mock_get):
        annotation_processor = VarsAnnotationProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        annotation_processor.process_sequences()
        assert annotation_processor.process_working_records() == [
            {
                'observation_uuid': '0059f860-4799-485f-c06c-5830e5ddd31e',
                'concept': 'Pomacentridae',
                'associations': ex_23060001['annotations'][0]['associations'],
                'identity_reference': '12',
                'image_url': 'https://hurlimage.soest.hawaii.edu/Hercules/images/1381920/20220418T202402.015Z--542830a8-ec69-4ee5-a57d-9de66a412dba.png',
                'video_url': 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_01/EX2306_01_20230824T183000Z.m4v#t=374',
                'recorded_timestamp': '2023-08-24T18:36:14.245Z',
                'video_sequence_name': 'Deep Discoverer 23060001',
                'annotator': 'Nikki Cunanan',
                'depth': 668,
                'phylum': 'Chordata',
                'subphylum': 'Vertebrata',
                'superclass': 'Pisces',
                'class': 'Actinopterygii',
                'order': 'Perciformes',
                'family': 'Pomacentridae',
                'activity': None,
            },
            {
                'observation_uuid': '0d9133d7-1d49-47d5-4b6d-6e4fb25dd41e',
                'concept': 'Pomacentridae',
                'associations': ex_23060001['annotations'][1]['associations'],
                'identity_reference': '13',
                'image_url': 'https://hurlimage.soest.hawaii.edu/SupplementalPhotos/Hphotos/NA138photos/H1920/cam1_20220419064757.png',
                'video_url': 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_01/EX2306_01_20230824T203000Z.m4v#t=3505',
                'recorded_timestamp': '2023-08-24T21:28:25.675Z',
                'video_sequence_name': 'Deep Discoverer 23060001',
                'annotator': 'Meagan Putts',
                'depth': 668,
                'phylum': 'Chordata',
                'subphylum': 'Vertebrata',
                'superclass': 'Pisces',
                'class': 'Actinopterygii',
                'order': 'Perciformes',
                'family': 'Pomacentridae',
                'activity': 'cruise',
            },
            {
                'observation_uuid': '0059f860-4799-485f-c06c-asdfasdfadsf',
                'concept': 'Pomacentridae',
                'identity_reference': '12',
                'associations': ex_23060001['annotations'][5]['associations'],
                'annotator': 'Nikki Cunanan',
                'depth': 668,
                'phylum': 'Chordata',
                'subphylum': 'Vertebrata',
                'superclass': 'Pisces',
                'class': 'Actinopterygii',
                'order': 'Perciformes',
                'family': 'Pomacentridae',
                'image_url': 'https://hurlimage.soest.hawaii.edu/Hercules/images/1381920/20220418T202402.015Z--542830a8-ec69-4ee5-a57d-9de66a412dba.png',
                'video_url': 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_01/EX2306_01_20230824T183000Z.m4v#t=913',
                'recorded_timestamp': '2023-08-24T18:45:13Z',
                'video_sequence_name': 'Deep Discoverer 23060001',
                'activity': None,
            },
        ]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_sort_records(self, mock_get):
        annotation_processor = VarsAnnotationProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        annotation_processor.process_sequences()
        assert annotation_processor.final_records == [
            {
                'observation_uuid': '0059f860-4799-485f-c06c-5830e5ddd31e',
                'concept': 'Pomacentridae',
                'identity_reference': '12',
                'associations': ex_23060001['annotations'][0]['associations'],
                'annotator': 'Nikki Cunanan',
                'depth': 668,
                'phylum': 'Chordata',
                'class': 'Actinopterygii',
                'order': 'Perciformes',
                'family': 'Pomacentridae',
                'genus': None,
                'species': None,
                'image_url': 'https://hurlimage.soest.hawaii.edu/Hercules/images/1381920/20220418T202402.015Z--542830a8-ec69-4ee5-a57d-9de66a412dba.png',
                'video_url': 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_01/EX2306_01_20230824T183000Z.m4v#t=374',
                'recorded_timestamp': '24 Aug 23 18:36:14 UTC',
                'video_sequence_name': 'Deep Discoverer 23060001',
                'activity': None,
            },
            {
                'observation_uuid': '0059f860-4799-485f-c06c-asdfasdfadsf',
                'concept': 'Pomacentridae',
                'identity_reference': '12',
                'associations': ex_23060001['annotations'][5]['associations'],
                'annotator': 'Nikki Cunanan',
                'depth': 668,
                'phylum': 'Chordata',
                'class': 'Actinopterygii',
                'order': 'Perciformes',
                'family': 'Pomacentridae',
                'genus': None,
                'species': None,
                'image_url': 'https://hurlimage.soest.hawaii.edu/Hercules/images/1381920/20220418T202402.015Z--542830a8-ec69-4ee5-a57d-9de66a412dba.png',
                'video_url': 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_01/EX2306_01_20230824T183000Z.m4v#t=913',
                'recorded_timestamp': '24 Aug 23 18:45:13 UTC',
                'video_sequence_name': 'Deep Discoverer 23060001',
                'activity': None,
            },
            {
                'observation_uuid': '0d9133d7-1d49-47d5-4b6d-6e4fb25dd41e',
                'concept': 'Pomacentridae',
                'associations': ex_23060001['annotations'][1]['associations'],
                'identity_reference': '13',
                'annotator': 'Meagan Putts',
                'depth': 668,
                'phylum': 'Chordata',
                'class': 'Actinopterygii',
                'order': 'Perciformes',
                'family': 'Pomacentridae',
                'genus': None,
                'species': None,
                'image_url': 'https://hurlimage.soest.hawaii.edu/SupplementalPhotos/Hphotos/NA138photos/H1920/cam1_20220419064757.png',
                'video_url': 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_01/EX2306_01_20230824T203000Z.m4v#t=3505',
                'recorded_timestamp': '24 Aug 23 21:28:25 UTC',
                'video_sequence_name': 'Deep Discoverer 23060001',
                'activity': 'cruise',
            },

        ]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_process_multiple_sequences(self, mock_get):
        annotation_processor = VarsAnnotationProcessor(
            sequence_names=['Deep Discoverer 23060001', 'Deep Discoverer 23060002'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        annotation_processor.process_sequences()
        # assert result includes annotations from all dives
        sequence_names = {record['video_sequence_name'] for record in annotation_processor.final_records}
        assert 'Deep Discoverer 23060001' in sequence_names
        assert 'Deep Discoverer 23060002' in sequence_names

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_highest_id_refs(self, mock_get):
        annotation_processor = VarsAnnotationProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        annotation_processor.process_sequences()
        assert annotation_processor.highest_id_ref == 13

    def test_fetch_media_and_annotations_returns_empty_when_charybdis_request_fails(self):
        annotation_processor = VarsAnnotationProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )

        with patch('requests.get', return_value=MockJsonResponse(status_code=500)):
            result = annotation_processor.fetch_media_and_annotations('Deep Discoverer 23060001', images_only=True)

        assert result == []

    def test_get_video_returns_empty_when_annotation_has_no_recorded_timestamp(self):
        annotation_processor = VarsAnnotationProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )

        assert annotation_processor.get_video({'concept': 'X'}) == {}

    def test_fetch_vam_media_returns_empty_when_no_vam_url_configured(self):
        annotation_processor = VarsAnnotationProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )

        with patch('requests.get') as mock_get:
            result = annotation_processor._fetch_vam_media('Deep Discoverer 23060001')

        mock_get.assert_not_called()
        assert result == []

    def test_fetch_vam_media_returns_empty_when_vam_request_fails(self):
        annotation_processor = VarsAnnotationProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
            vars_vam_url='https://vam.url',
        )

        with patch('requests.get', return_value=MockJsonResponse(status_code=500)):
            result = annotation_processor._fetch_vam_media('Deep Discoverer 23060001')

        assert result == []

    def test_fetch_vam_media_formats_first_video_reference_per_video(self):
        annotation_processor = VarsAnnotationProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
            vars_vam_url='https://vam.url',
        )
        vam_response = [
            {
                'start_timestamp': '2023-08-24T18:00:00Z',
                'duration_millis': 7200000,
                'video_references': [
                    # only the first reference is used
                    {'uuid': 'vam-uuid-1', 'uri': 'http://hurlstor.soest.hawaii.edu/videoarchive/vam-video.m4v'},
                    {'uuid': 'vam-uuid-2', 'uri': 'http://hurlstor.soest.hawaii.edu/videoarchive/vam-video-alt.m4v'},
                ],
            },
            {
                # image-collection references are filtered out entirely
                'start_timestamp': '2023-08-24T20:00:00Z',
                'duration_millis': 3600000,
                'video_references': [{'uuid': 'vam-uuid-3', 'uri': 'urn:imagecollection:org:foo'}],
            },
        ]

        with patch('requests.get', return_value=MockJsonResponse(json_data=vam_response)) as mock_get:
            result = annotation_processor._fetch_vam_media('Deep Discoverer 23060001')

        mock_get.assert_called_once_with(
            url='https://vam.url/videos/videosequence/name/Deep%20Discoverer%2023060001',
        )
        assert result == [
            {
                'start_timestamp': parse_datetime('2023-08-24T18:00:00Z'),
                'uri': 'https://hurlvideo.soest.hawaii.edu/vam-video.m4v',
                'sequence_name': 'Deep Discoverer 23060001',
                'video_reference_uuid': 'vam-uuid-1',
                'duration_millis': 7200000,
            }
        ]

    def test_process_working_records_falls_back_to_vam_when_no_video_found(self):
        annotation_processor = VarsAnnotationProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
            vars_vam_url='https://vam.url',
        )
        # Charybdis never returned any media for this sequence, so self.videos starts empty
        annotation_processor.working_records = [
            {
                'observation_uuid': 'abc',
                'concept': 'none',
                'associations': [],
                'recorded_timestamp': '2023-08-24T18:36:14.245Z',
                'observer': 'NikkiCunanan',
                'sequence_name': 'Deep Discoverer 23060001',
                'image_references': [],
            }
        ]
        vam_response = [
            {
                'start_timestamp': '2023-08-24T18:00:00Z',
                'duration_millis': 7200000,
                'video_references': [
                    {'uuid': 'vam-uuid-1', 'uri': 'http://hurlstor.soest.hawaii.edu/videoarchive/vam-video.m4v'},
                ],
            }
        ]

        with patch('requests.get', return_value=MockJsonResponse(json_data=vam_response)):
            formatted_records = annotation_processor.process_working_records()

        assert annotation_processor.videos[0]['video_reference_uuid'] == 'vam-uuid-1'
        # 18:36:14.245 - 18:00:00 = 36m 14.245s = 2174.245s, truncated to whole seconds
        assert formatted_records[0]['video_url'] == 'https://hurlvideo.soest.hawaii.edu/vam-video.m4v#t=2174'

    def test_process_working_records_only_fetches_vam_once_per_sequence(self):
        annotation_processor = VarsAnnotationProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
            vars_vam_url='https://vam.url',
        )
        make_annotation = lambda uuid, timestamp: {
            'observation_uuid': uuid,
            'concept': 'none',
            'associations': [],
            'recorded_timestamp': timestamp,
            'observer': 'NikkiCunanan',
            'sequence_name': 'Deep Discoverer 23060001',
            'image_references': [],
        }
        annotation_processor.working_records = [
            make_annotation('abc', '2023-08-24T18:36:14.245Z'),
            make_annotation('def', '2023-08-24T18:40:00Z'),
        ]
        vam_response = [
            {
                'start_timestamp': '2023-08-24T18:00:00Z',
                'duration_millis': 7200000,
                'video_references': [
                    {'uuid': 'vam-uuid-1', 'uri': 'http://hurlstor.soest.hawaii.edu/videoarchive/vam-video.m4v'},
                ],
            }
        ]

        with patch('requests.get', return_value=MockJsonResponse(json_data=vam_response)) as mock_get:
            formatted_records = annotation_processor.process_working_records()

        assert mock_get.call_count == 1
        assert all(record['video_url'] for record in formatted_records)
