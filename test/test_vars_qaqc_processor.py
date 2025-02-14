from unittest.mock import patch

from application.server.functions import parse_datetime
from application.server.vars_qaqc_processor import VarsQaqcProcessor
from test.data.vars_responses import ex_23060001, ex_23060002
from test.util.mock_response import MockResponse


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

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_duplicate_associations(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor_problems = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        qaqc_processor_okay.find_duplicate_associations()
        qaqc_processor_problems.find_duplicate_associations()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][0]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_s1(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor_problems = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        qaqc_processor_okay.find_missing_s1()
        qaqc_processor_problems.find_missing_s1()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][1]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_identical_s1_s2(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor_problems = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        qaqc_processor_okay.find_identical_s1_s2()
        qaqc_processor_problems.find_identical_s1_s2()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][2]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_duplicate_s2(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor_problems = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        qaqc_processor_okay.find_duplicate_s2()
        qaqc_processor_problems.find_duplicate_s2()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][1]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_upon_substrate(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor_problems = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        qaqc_processor_okay.find_missing_upon_substrate()
        qaqc_processor_problems.find_missing_upon_substrate()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][0]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_mismatched_substrates(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor_problems = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        qaqc_processor_okay.find_mismatched_substrates()
        qaqc_processor_problems.find_mismatched_substrates()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][3], ex_23060002['annotations'][5]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_upon(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor_problems = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        qaqc_processor_okay.find_missing_upon()
        qaqc_processor_problems.find_missing_upon()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][3]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_num_records_missing_ancillary_data(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor_problems = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        assert qaqc_processor_okay.get_num_records_missing_ancillary_data() == 0
        assert qaqc_processor_problems.get_num_records_missing_ancillary_data() == 2

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_ancillary_data(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor_problems = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        qaqc_processor_okay.find_missing_ancillary_data()
        qaqc_processor_problems.find_missing_ancillary_data()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][2], ex_23060002['annotations'][3]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_id_refs_different_concept_name(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor_problems = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        qaqc_processor_okay.find_id_refs_different_concept_name()
        qaqc_processor_problems.find_id_refs_different_concept_name()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][2], ex_23060002['annotations'][3]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_id_refs_conflicting_associations(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor_problems = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        qaqc_processor_okay.find_id_refs_conflicting_associations()
        qaqc_processor_problems.find_id_refs_conflicting_associations()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][2], ex_23060002['annotations'][3]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_blank_associations(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor_problems = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        qaqc_processor_okay.find_blank_associations()
        qaqc_processor_problems.find_blank_associations()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][0], ex_23060002['annotations'][1]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_suspicious_hosts(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor_problems = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        qaqc_processor_okay.find_suspicious_hosts()
        qaqc_processor_problems.find_suspicious_hosts()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][1]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_expected_association(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor_problems = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        qaqc_processor_okay.find_missing_expected_association()
        qaqc_processor_problems.find_missing_expected_association()
        assert qaqc_processor_okay.final_records == []
        assert qaqc_processor_problems.final_records == [
            {
                'observation_uuid': '006fb032-13b5-4517-136c-11aa9597e81e',
                'concept': 'Hydroidolina',
                'associations': ex_23060002['annotations'][0]['associations'],
                'activity': 'cruise',
                'annotator': 'Nikki Cunanan',
                'depth': 4255.0,
                'phylum': 'Cnidaria',
                'class': 'Hydrozoa',
                'order': None,
                'family': None,
                'genus': None,
                'species': None,
                'identity_reference': '50',
                'image_url': '',
                'video_url': 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_02/EX2306_02_20230825T195000Z.m4v#t=3725',
                'recorded_timestamp': '25 Aug 23 20:52:05 UTC',
                'video_sequence_name': 'Deep Discoverer 23060002',
            }
        ]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_long_host_associate_time_diff(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor_problems = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        qaqc_processor_okay.find_long_host_associate_time_diff()
        qaqc_processor_problems.find_long_host_associate_time_diff()
        assert qaqc_processor_okay.final_records == []
        assert qaqc_processor_problems.final_records == [
            {
                'observation_uuid': '01f3e954-b793-40a3-6166-88f24898e81e',
                'concept': 'Pomacentridae',
                'associations': ex_23060002['annotations'][1]['associations'],
                'activity': 'cruise',
                'annotator': 'Nikki Cunanan',
                'depth': 4256.0,
                'phylum': 'Chordata',
                'class': 'Actinopterygii',
                'order': 'Perciformes',
                'family': 'Pomacentridae',
                'genus': None,
                'species': None,
                'identity_reference': None,
                'image_url': '',
                'video_url': 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_02/EX2306_02_20230825T195000Z.m4v#t=4543',
                'recorded_timestamp': '25 Aug 23 21:05:43 UTC',
                'video_sequence_name': 'Deep Discoverer 23060002',
                'status': 'Host not found in previous records'
            },
            {
                'observation_uuid': '02dfd7f4-c834-433d-4960-9577c98ce81e',
                'concept': 'Hydroidolina',
                'associations': ex_23060002['annotations'][2]['associations'],
                'activity': 'cruise',
                'annotator': 'Nikki Cunanan',
                'depth': None,
                'phylum': 'Cnidaria',
                'class': 'Hydrozoa',
                'order': None,
                'family': None,
                'genus': None,
                'species': None,
                'identity_reference': '13',
                'image_url': '',
                'video_url': 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_02/EX2306_02_20230825T195000Z.m4v#t=2435',
                'recorded_timestamp': '25 Aug 23 20:30:35 UTC',
                'video_sequence_name': 'Deep Discoverer 23060002',
                'status': 'Time between record and closest previous matching host record greater than one minute (95 seconds)'
            },
            {
                'observation_uuid': '0983d9f1-d28a-482e-0160-6d3df753e91e',
                'concept': 'AssociateConcept',
                'associations': ex_23060002['annotations'][4]['associations'],
                'activity': 'stationary',
                'annotator': 'Nikki Cunanan',
                'depth': 4260.0,
                'phylum': None,
                'class': None,
                'order': None,
                'family': None, 'genus': None,
                'species': None,
                'identity_reference': None,
                'image_url': '',
                'video_url': 'https://hurlvideo.soest.hawaii.edu/D2/2023/EX2306_02/EX2306_02_20230825T195000Z.m4v#t=2941',
                'recorded_timestamp': '25 Aug 23 20:39:01 UTC',
                'video_sequence_name': 'Deep Discoverer 23060002',
                'status': 'Time between record and closest previous matching host record greater than five minutes (10 mins, 0 seconds)'
            },
        ]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_num_bounding_boxes(self, _):
        qaqc_processor = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor.find_num_bounding_boxes()
        assert qaqc_processor.final_records == [{
            'bounding_box_counts': {
                'Pomacentridae': {'annos': 5, 'boxes': 1},
                'none': {'annos': 1, 'boxes': 0}
            },
            'total_count_annos': 6,
            'total_count_boxes': 1,
        }]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_unique_fields(self, _):
        qaqc_processor = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor.find_unique_fields()
        assert qaqc_processor.final_records == [
            {
                'concept-names': {
                    'Pomacentridae': {
                        'individuals': 5,
                        'records': 5,
                    },
                    'none': {
                        'individuals': 1,
                        'records': 1,
                    }
                },
            },
            {
                'concept-upon-combinations': {
                    'Pomacentridae:bed': {
                        'individuals': 2,
                        'records': 2,
                    },
                    'Pomacentridae:sed': {
                        'individuals': 3,
                        'records': 3,
                    },
                    'none:None': {
                        'individuals': 1,
                        'records': 1,
                    }
                },
            },
            {
                'substrate-combinations': {
                    '': {
                        'individuals': 1,
                        'records': 1,
                    },
                    'bed, bou, sed': {
                        'individuals': 1,
                        'records': 1,
                    },
                    'bed, sed': {
                        'individuals': 1,
                        'records': 1,
                    },
                    'mantra, sed': {
                        'individuals': 1,
                        'records': 1,
                    },
                    'sed': {
                        'individuals': 2,
                        'records': 2,
                    },
                },
            },
            {
                'comments': {
                    None: {
                        'individuals': 3,
                        'records': 3,
                    },
                    'Added for review: Don Draper': {
                        'individuals': 1,
                        'records': 1,
                    },
                    'Added for review: Jon Snow; This is a weird lookin sponge thing!': {
                        'individuals': 1,
                        'records': 1,
                    },
                    'this is a comment': {
                        'individuals': 1,
                        'records': 1,
                    },
                },
            },
            {
                'condition-comments': {
                    None: {
                        'individuals': 6,
                        'records': 6,
                    },
                },
            },
            {
                'megahabitats': {
                    None: {
                        'individuals': 5,
                        'records': 5,
                    },
                    'continental shelf': {
                        'individuals': 1,
                        'records': 1,
                    },
                },
            },
            {
                'habitats': {
                    None: {
                        'individuals': 5,
                        'records': 5,
                    },
                    'slope': {
                        'individuals': 1,
                        'records': 1,
                    },
                },
            },
            {
                'habitat-comments': {
                    None: {
                        'individuals': 5,
                        'records': 5,
                    },
                    'loose talus': {
                        'individuals': 1,
                        'records': 1,
                    },
                },
            },
            {
                'identity-certainty': {
                    None: {
                        'individuals': 4,
                        'records': 4,
                    },
                    'maybe': {
                        'individuals': 2,
                        'records': 2,
                    },
                },
            },
            {
                'occurrence-remarks': {
                    None: {
                        'individuals': 4,
                        'records': 4,
                    },
                    'bottom in sight': {
                        'individuals': 1,
                        'records': 1,
                    },
                    'in water column on descent': {
                        'individuals': 1,
                        'records': 1,
                    },
                },
            },
        ]
