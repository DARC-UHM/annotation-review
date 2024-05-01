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
        qaqc_processor = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        qaqc_processor.find_duplicate_associations()
        assert qaqc_processor.working_records == [ex_23060002['annotations'][0]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_duplicate_associations_none(self, _):
        qaqc_processor = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor.find_duplicate_associations()
        assert qaqc_processor.working_records == []

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_s1(self, _):
        qaqc_processor = VarsQaqcProcessor(['Deep Discoverer 23060002'])
        qaqc_processor.find_missing_s1()
        assert qaqc_processor.working_records == [ex_23060002['annotations'][1]]

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_s1_none(self, _):
        qaqc_processor = VarsQaqcProcessor(['Deep Discoverer 23060001'])
        qaqc_processor.find_missing_s1()
        assert qaqc_processor.working_records == []

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_duplicate_s2(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_duplicate_s2_none(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_upon_substrate(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_upon_substrate_none(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_mismatched_substrates(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_mismatched_substrates_none(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_upon(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_upon_none(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_get_num_records_missing_ancillary_data(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_ancillary_data(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_ancillary_data_none(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_id_refs_different_concept_name(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_id_refs_different_concept_name_none(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_id_refs_conflicting_associations(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_id_refs_conflicting_associations_none(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_blank_associations(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_blank_associations_none(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_suspicious_hosts(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_suspicious_hosts_none(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_expected_association(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_missing_expected_association_none(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_long_host_associate_time_diff(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_long_host_associate_time_diff_none(self, _):
        assert False

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_find_unique_fields(self, _):
        assert False

    def test_tests_done(self):
        assert False
