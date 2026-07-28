from unittest.mock import patch

import pytest

from application.util.functions import parse_datetime
from application.vars.vars_qaqc_processor import VarsQaqcProcessor
from test.data.vars_responses import ex_23060001, ex_23060002
from test.util.mock_response import MockResponse


def mocked_requests_get(*args, **kwargs):
    return MockResponse(url=kwargs.get('url'))


def make_annotation(
        *,
        observation_uuid='uuid-1',
        concept='none',
        group=None,
        associations=None,
        observer='NikkiCunanan',
        recorded_timestamp='2023-08-24T18:36:14.245Z',
        activity=None,
        ancillary_data=None,
        image_references=None,
):
    # only the fields process_working_records()/the find_* checks actually read
    annotation = {
        'observation_uuid': observation_uuid,
        'concept': concept,
        'associations': associations or [],
        'observer': observer,
        'recorded_timestamp': recorded_timestamp,
        'image_references': image_references if image_references is not None else [],
    }
    if group is not None:
        annotation['group'] = group
    if activity is not None:
        annotation['activity'] = activity
    if ancillary_data is not None:
        annotation['ancillary_data'] = ancillary_data
    return annotation


@pytest.mark.usefixtures('mock_phylogeny_cache')
class TestVarsQaqcProcessor:
    def test_init(self):
        qaqc_processor = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        assert qaqc_processor.sequence_names == ['Deep Discoverer 23060001']
        assert qaqc_processor.videos == []
        assert qaqc_processor.working_records == []
        assert qaqc_processor.final_records == []
        assert len(qaqc_processor.phylogeny.data.keys()) > 0

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_duplicate_associations(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_problems = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060002'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_okay.find_duplicate_associations()
        qaqc_processor_problems.find_duplicate_associations()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][0]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_s1(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_problems = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060002'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_okay.find_missing_s1()
        qaqc_processor_problems.find_missing_s1()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][1]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_identical_s1_s2(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_problems = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060002'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_okay.find_identical_s1_s2()
        qaqc_processor_problems.find_identical_s1_s2()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][2]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_duplicate_s2(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_problems = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060002'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_okay.find_duplicate_s2()
        qaqc_processor_problems.find_duplicate_s2()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][1]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_upon_substrate(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_problems = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060002'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_okay.find_missing_upon_substrate()
        qaqc_processor_problems.find_missing_upon_substrate()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][0]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_mismatched_substrates(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_problems = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060002'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_okay.find_mismatched_substrates()
        qaqc_processor_problems.find_mismatched_substrates()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][3], ex_23060002['annotations'][5]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_upon(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_problems = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060002'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_okay.find_missing_upon()
        qaqc_processor_problems.find_missing_upon()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][3]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_num_records_missing_ancillary_data(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_problems = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060002'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        assert qaqc_processor_okay.get_num_records_missing_ancillary_data() == 0
        assert qaqc_processor_problems.get_num_records_missing_ancillary_data() == 2

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_ancillary_data(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_problems = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060002'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_okay.find_missing_ancillary_data()
        qaqc_processor_problems.find_missing_ancillary_data()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][2], ex_23060002['annotations'][3]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_id_refs_different_concept_name(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_problems = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060002'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_okay.find_id_refs_different_concept_name()
        qaqc_processor_problems.find_id_refs_different_concept_name()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][2], ex_23060002['annotations'][3]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_id_refs_conflicting_associations(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_problems = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060002'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_okay.find_id_refs_conflicting_associations()
        qaqc_processor_problems.find_id_refs_conflicting_associations()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][2], ex_23060002['annotations'][3]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_blank_associations(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_problems = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060002'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_okay.find_blank_associations()
        qaqc_processor_problems.find_blank_associations()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][0], ex_23060002['annotations'][1]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_suspicious_hosts(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_problems = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060002'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_okay.find_suspicious_hosts()
        qaqc_processor_problems.find_suspicious_hosts()
        assert qaqc_processor_okay.working_records == []
        assert qaqc_processor_problems.working_records == [ex_23060002['annotations'][1]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_expected_association(self, _):
        qaqc_processor_okay = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_problems = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060002'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
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
        qaqc_processor_okay = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor_problems = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060002'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
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
                'image_url': 'https://hurlimage.soest.hawaii.edu/D2/2023/EX2306_02/image.png',
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
        qaqc_processor = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
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
        qaqc_processor = VarsQaqcProcessor(
            sequence_names=['Deep Discoverer 23060001'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
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

    @pytest.mark.parametrize('method_name,triggering_associations', [
        ('find_duplicate_associations', [
            {'link_name': 'megahabitat', 'to_concept': 'X', 'link_value': 'nil'},
            {'link_name': 'megahabitat', 'to_concept': 'Y', 'link_value': 'nil'},
        ]),
        ('find_identical_s1_s2', [
            {'link_name': 's1', 'to_concept': 'sed', 'link_value': 'nil'},
            {'link_name': 's2', 'to_concept': 'sed', 'link_value': 'nil'},
        ]),
        ('find_duplicate_s2', [
            {'link_name': 's2', 'to_concept': 'sed', 'link_value': 'nil'},
            {'link_name': 's2', 'to_concept': 'sed', 'link_value': 'nil'},
        ]),
        ('find_missing_upon_substrate', [
            {'link_name': 'upon', 'to_concept': 'rock', 'link_value': 'nil'},
        ]),
        ('find_blank_associations', [
            {'link_name': 'bounding box', 'to_concept': 'self', 'link_value': ''},
        ]),
        ('find_suspicious_hosts', [
            {'link_name': 'upon', 'to_concept': 'SuspiciousConcept', 'link_value': 'nil'},
        ]),
    ])
    def test_checks_skip_localization_group_annotations(self, method_name, triggering_associations):
        # each of these association sets would flag the annotation if it weren't in the "localization" group
        annotation = make_annotation(
            concept='SuspiciousConcept',
            group='localization',
            associations=triggering_associations,
        )
        qaqc_processor = VarsQaqcProcessor(
            sequence_names=['X'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )

        with patch.object(VarsQaqcProcessor, 'fetch_media_and_annotations', return_value=[annotation]):
            getattr(qaqc_processor, method_name)()

        assert qaqc_processor.working_records == []

    def test_find_id_refs_different_concept_name_skips_localization_group_annotations(self):
        # without the localization-group skip, these two different concept names sharing an id ref would flag
        localization_annotation = make_annotation(
            observation_uuid='loc-1',
            concept='ConceptA',
            group='localization',
            associations=[{'link_name': 'identity-reference', 'to_concept': 'self', 'link_value': '1'}],
        )
        other_annotation = make_annotation(
            observation_uuid='other-1',
            concept='ConceptB',
            associations=[{'link_name': 'identity-reference', 'to_concept': 'self', 'link_value': '1'}],
        )
        qaqc_processor = VarsQaqcProcessor(
            sequence_names=['X'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )

        with patch.object(
                VarsQaqcProcessor, 'fetch_media_and_annotations',
                return_value=[localization_annotation, other_annotation],
        ):
            qaqc_processor.find_id_refs_different_concept_name()

        assert qaqc_processor.working_records == []

    def test_find_id_refs_conflicting_associations_skips_localization_group_annotations(self):
        localization_annotation = make_annotation(
            observation_uuid='loc-1',
            group='localization',
            associations=[
                {'link_name': 'identity-reference', 'to_concept': 'self', 'link_value': '1'},
                {'link_name': 'habitat', 'to_concept': 'X', 'link_value': 'nil'},
            ],
        )
        other_annotation = make_annotation(
            observation_uuid='other-1',
            associations=[
                {'link_name': 'identity-reference', 'to_concept': 'self', 'link_value': '1'},
                {'link_name': 'habitat', 'to_concept': 'Y', 'link_value': 'nil'},  # would conflict, if not skipped
            ],
        )
        qaqc_processor = VarsQaqcProcessor(
            sequence_names=['X'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )

        with patch.object(
                VarsQaqcProcessor, 'fetch_media_and_annotations',
                return_value=[localization_annotation, other_annotation],
        ):
            qaqc_processor.find_id_refs_conflicting_associations()

        assert qaqc_processor.working_records == []

    def test_find_id_refs_conflicting_associations_compares_second_annotation_with_same_id_ref(self):
        first_annotation = make_annotation(
            observation_uuid='first',
            associations=[
                {'link_name': 'identity-reference', 'to_concept': 'self', 'link_value': '1'},
                {'link_name': 's2', 'to_concept': 'sed', 'link_value': 'nil'},
                {'link_name': 'sampled-by', 'to_concept': 'diver', 'link_value': 'nil'},
                {'link_name': 'sample-reference', 'to_concept': 'self', 'link_value': 'ref-1'},
                {'link_name': 'habitat', 'to_concept': 'X', 'link_value': 'nil'},
                {'link_name': 'identity-certainty', 'to_concept': 'self', 'link_value': 'certain'},
                {'link_name': 'guide-photo', 'to_concept': 'self', 'link_value': ''},
            ],
        )
        second_annotation = make_annotation(
            observation_uuid='second',
            associations=[
                {'link_name': 'identity-reference', 'to_concept': 'self', 'link_value': '1'},
                {'link_name': 'guide-photo', 'to_concept': 'self', 'link_value': ''},
                {'link_name': 's2', 'to_concept': 'mud', 'link_value': 'nil'},  # differs from first -> allowed
                {'link_name': 'sampled-by', 'to_concept': 'diver', 'link_value': 'nil'},
                {'link_name': 'sample-reference', 'to_concept': 'self', 'link_value': 'ref-1'},
                # a to_concepts field the first annotation never set
                {'link_name': 'megahabitat', 'to_concept': 'continental shelf', 'link_value': 'nil'},
                # a non-to_concepts field the first annotation never set
                {'link_name': 'comment', 'to_concept': 'self', 'link_value': 'a remark'},
                # a non-to_concepts field that conflicts with the first annotation's value -> flags and stops
                {'link_name': 'identity-certainty', 'to_concept': 'self', 'link_value': 'uncertain'},
            ],
        )
        qaqc_processor = VarsQaqcProcessor(
            sequence_names=['X'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )

        with patch.object(
                VarsQaqcProcessor, 'fetch_media_and_annotations',
                return_value=[first_annotation, second_annotation],
        ):
            qaqc_processor.find_id_refs_conflicting_associations()

        assert {record['observation_uuid'] for record in qaqc_processor.working_records} == {'first', 'second'}

    def test_find_mismatched_substrates_skips_localization_group_and_compares_s2_sets(self):
        localization_annotation = make_annotation(
            observation_uuid='loc-1',
            group='localization',
            recorded_timestamp='2023-08-24T18:00:00.000Z',
        )
        base_annotation = make_annotation(
            observation_uuid='base',
            recorded_timestamp='2023-08-24T18:36:14.100Z',
            associations=[
                {'link_name': 's1', 'to_concept': 'sed', 'link_value': 'nil'},
                {'link_name': 's2', 'to_concept': 'x', 'link_value': 'nil'},
            ],
        )
        matching_timestamp_annotation = make_annotation(
            observation_uuid='match',
            recorded_timestamp='2023-08-24T18:36:14.900Z',  # same second as base_annotation
            associations=[
                {'link_name': 's1', 'to_concept': 'sed', 'link_value': 'nil'},
                {'link_name': 's2', 'to_concept': 'y', 'link_value': 'nil'},  # different substrate -> mismatch
            ],
        )
        filler_annotation = make_annotation(
            observation_uuid='filler',
            recorded_timestamp='2023-08-24T18:40:00.000Z',
        )
        qaqc_processor = VarsQaqcProcessor(
            sequence_names=['X'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )

        with patch.object(
                VarsQaqcProcessor, 'fetch_media_and_annotations',
                return_value=[localization_annotation, base_annotation, matching_timestamp_annotation, filler_annotation],
        ):
            qaqc_processor.find_mismatched_substrates()

        assert {record['observation_uuid'] for record in qaqc_processor.working_records} == {'base', 'match'}

    def test_find_missing_expected_association_skips_localization_group_annotations(self):
        # 'Hydroidolina' is in the expected-association concept list and the lowercase, non-'dead' upon would
        # otherwise flag this record as missing its expected host association, if it weren't in the "localization"
        # group
        annotation = make_annotation(concept='Hydroidolina', group='localization', associations=[
            {'link_name': 'upon', 'to_concept': 'coral', 'link_value': 'nil'},
        ])
        qaqc_processor = VarsQaqcProcessor(
            sequence_names=['X'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )
        qaqc_processor.phylogeny.data['Hydroidolina'] = {}  # skip the real WoRMS/VARS KB phylogeny fetch

        with patch.object(VarsQaqcProcessor, 'fetch_media_and_annotations', return_value=[annotation]):
            qaqc_processor.find_missing_expected_association()

        assert qaqc_processor.final_records == []

    def test_find_localizations_without_bounding_boxes(self):
        bounding_box_association = [{'link_name': 'bounding box', 'to_concept': 'self', 'link_value': 'nil'}]
        localization_with_box = make_annotation(
            observation_uuid='loc-with-box', group='localization', associations=bounding_box_association,
        )
        localization_without_box = make_annotation(observation_uuid='loc-without-box', group='localization')
        non_localization_with_box = make_annotation(
            observation_uuid='non-loc-with-box', associations=bounding_box_association,
        )
        non_localization_without_box = make_annotation(observation_uuid='non-loc-without-box')
        qaqc_processor = VarsQaqcProcessor(
            sequence_names=['X'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )

        with patch.object(
                VarsQaqcProcessor, 'fetch_media_and_annotations',
                return_value=[
                    localization_with_box, localization_without_box,
                    non_localization_with_box, non_localization_without_box,
                ],
        ):
            qaqc_processor.find_localizations_without_bounding_boxes()

        assert {record['observation_uuid'] for record in qaqc_processor.working_records} == {
            'loc-without-box', 'non-loc-with-box',
        }

    def test_find_unique_fields_handles_condition_comment_population_quantity_and_categorical_abundance(self):
        annotations = [
            make_annotation(observation_uuid='u1', concept='X', associations=[
                {'link_name': 'condition-comment', 'to_concept': 'self', 'link_value': 'chipped shell'},
                {'link_name': 'population-quantity', 'to_concept': 'self', 'link_value': '7'},
            ]),
            make_annotation(observation_uuid='u2', concept='X', associations=[
                {'link_name': 'categorical-abundance', 'to_concept': 'self', 'link_value': '11-20'},
            ]),
            make_annotation(observation_uuid='u3', concept='X', associations=[
                {'link_name': 'categorical-abundance', 'to_concept': 'self', 'link_value': '21-50'},
            ]),
            make_annotation(observation_uuid='u4', concept='X', associations=[
                {'link_name': 'categorical-abundance', 'to_concept': 'self', 'link_value': '51-100'},
            ]),
            make_annotation(observation_uuid='u5', concept='X', associations=[
                {'link_name': 'categorical-abundance', 'to_concept': 'self', 'link_value': '>100'},
            ]),
        ]
        qaqc_processor = VarsQaqcProcessor(
            sequence_names=['X'],
            vars_charybdis_url=MockResponse.VARS_CHARYBDIS_URL,
            vars_kb_url=MockResponse.VARS_KB_URL,
        )

        with patch.object(VarsQaqcProcessor, 'fetch_media_and_annotations', return_value=annotations):
            qaqc_processor.find_unique_fields()

        concept_names = next(r for r in qaqc_processor.final_records if 'concept-names' in r)['concept-names']
        # population-quantity (7) + categorical-abundance buckets (15 + 35 + 75 + 100)
        assert concept_names['X']['individuals'] == 232
        assert concept_names['X']['records'] == 5
        condition_comments = next(
            r for r in qaqc_processor.final_records if 'condition-comments' in r
        )['condition-comments']
        assert condition_comments['chipped shell']['individuals'] == 7
