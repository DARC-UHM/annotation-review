from unittest.mock import patch

import pytest

from application.tator.tator_rest_client import TatorRestClient
from application.tator.tator_sub_qaqc_processor import TatorSubQaqcProcessor
from application.tator.tator_type import TatorLocalizationType
from test.tator.conftest import TATOR_URL, formatted_start_time, make_localization, make_media, mock_get_section_by_id


@pytest.mark.usefixtures('mock_phylogeny_cache')
class TestTatorSubQaqcProcessor:
    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_check_missing_ancillary_data_flags_incomplete_records(self, fake_session, stub_annotator, stub_worms_match):
        tator_qaqc_processor = TatorSubQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            # fully populated -> not flagged
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={
                    'Scientific Name': 'X',
                    'Depth': 100.0,
                    'Position': [-158.0, 21.0],
                    'DO Temperature (celsius)': 5.0,
                },
            ),
            # missing depth -> flagged
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={
                    'Scientific Name': 'X',
                    'Position': [-158.0, 21.0],
                    'DO Temperature (celsius)': 5.0,
                },
            ),
            # missing position -> flagged
            make_localization(
                elemental_id=3,
                frame=3,
                attributes={
                    'Scientific Name': 'X',
                    'Depth': 100.0,
                    'DO Temperature (celsius)': 5.0,
                },
            ),
            # missing DO temp -> flagged
            make_localization(
                elemental_id=4,
                frame=4,
                attributes={
                    'Scientific Name': 'X',
                    'Depth': 100.0,
                    'Position': [-158.0, 21.0],
                },
            ),
        ]

        tator_qaqc_processor.check_missing_ancillary_data()

        flagged_ids = {record['observation_uuid'] for record in tator_qaqc_processor.final_records}
        assert flagged_ids == {2, 3, 4}

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_check_missing_upon_and_not_fish(self, fake_session, stub_annotator):
        tator_qaqc_processor = TatorSubQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )

        def fake_fetch_worms(self, scientific_name):
            if scientific_name == 'FishTaxon':
                self.data['FishTaxon'] = {'phylum': 'Chordata'}
            elif scientific_name == 'InvertTaxon':
                self.data['InvertTaxon'] = {'phylum': 'Mollusca'}
            return True

        tator_qaqc_processor.sections[0].localizations = [
            # no Upon attribute at all -> flagged
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={'Scientific Name': 'InvertTaxon'},
            ),
            # placeholder value -> flagged
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={
                    'Scientific Name': 'InvertTaxon',
                    'Upon': '--',
                },
            ),
            # "water" but this taxon is a fish (phylum Chordata) -> not flagged
            make_localization(
                elemental_id=3,
                frame=3,
                attributes={
                    'Scientific Name': 'FishTaxon',
                    'Upon': 'water column',
                },
            ),
            # "water" and this taxon is not a fish -> flagged
            make_localization(
                elemental_id=4,
                frame=4,
                attributes={
                    'Scientific Name': 'InvertTaxon',
                    'Upon': 'water column',
                },
            ),
            # a real substrate/host value -> not flagged
            make_localization(
                elemental_id=5,
                frame=5,
                attributes={
                    'Scientific Name': 'InvertTaxon',
                    'Upon': 'rock',
                },
            ),
        ]

        with patch('application.util.phylogeny_cache.PhylogenyCache.fetch_worms', fake_fetch_worms):
            tator_qaqc_processor.check_missing_upon_and_not_fish()

        flagged_ids = {record['observation_uuid'] for record in tator_qaqc_processor.final_records}
        assert flagged_ids == {1, 2, 4}
        assert all(record['problems'] == 'Upon' for record in tator_qaqc_processor.final_records)

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_check_upons_are_current_substrate_or_previous_animal(
            self, fake_session, stub_annotator, stub_worms_match,
    ):
        media_id = 100
        substrates_response = [{
            'media_id': media_id,
            'substrates': [
                {
                    'frame': 0,
                    'Primary Substrate': 'sand',
                    'Secondary Substrate': '--',
                },
            ],
        }]
        tator_qaqc_processor = TatorSubQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            # upon matches the current substrate -> not flagged
            make_localization(
                elemental_id=1,
                media=media_id,
                frame=10,
                attributes={
                    'Scientific Name': 'Anemone',
                    'Upon': 'sand',
                },
            ),
            # upon matches a previously-seen animal (Anemone, above) -> not flagged
            make_localization(
                elemental_id=2,
                media=media_id,
                frame=20,
                attributes={
                    'Scientific Name': 'Clownfish',
                    'Upon': 'Anemone',
                },
            ),
            # matches neither the substrate nor any previously-seen animal -> flagged
            make_localization(
                elemental_id=3,
                media=media_id,
                frame=30,
                attributes={
                    'Scientific Name': 'Krabby',
                    'Upon': 'Pikachu',
                },
            ),
            # "water" upons are skipped entirely, regardless of match
            make_localization(
                elemental_id=4,
                media=media_id,
                frame=40,
                attributes={
                    'Scientific Name': 'Fish',
                    'Upon': 'water column',
                },
            ),
            # no upon at all -> skipped
            make_localization(
                elemental_id=5,
                media=media_id,
                frame=50,
                attributes={'Scientific Name': 'Other'},
            ),
        ]

        with patch.object(TatorRestClient, 'get_substrates', return_value=substrates_response):
            tator_qaqc_processor.check_upons_are_current_substrate_or_previous_animal()

        records_by_id = {record['observation_uuid']: record for record in tator_qaqc_processor.final_records}
        assert set(records_by_id.keys()) == {3}
        assert records_by_id[3]['problems'] == 'Upon'
        assert records_by_id[3]['substrate'] == {'frame': 0, 'Primary Substrate': 'sand', 'Secondary Substrate': '--'}

    def test_upon_matches_substrate_true_when_substring_of_current_value(self):
        substrate_entries = [
            {
                'frame': 0,
                'Primary Substrate': 'sand',
                'Secondary Substrate': '--',
            },
        ]

        result = TatorSubQaqcProcessor._upon_matches_substrate(
            substrate_entries=substrate_entries,
            localization={
                'frame': 10,
                'upon': 'sand',
                'scientific_name': 'X',
                'media_id': 1,
            },
        )

        assert result is True

    def test_upon_matches_substrate_false_when_no_current_substrate(self):
        result = TatorSubQaqcProcessor._upon_matches_substrate(
            substrate_entries=[],
            localization={
                'frame': 10,
                'upon': 'sand',
                'scientific_name': 'X',
                'media_id': 1,
            },
        )

        assert result is False

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_suspicious_records_flags_upon_equal_to_scientific_name(
            self, fake_session, stub_annotator, stub_worms_match,
    ):
        tator_qaqc_processor = TatorSubQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={
                    'Scientific Name': 'Squalus',
                    'Upon': 'Squalus',
                },
            ),
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={
                    'Scientific Name': 'Squalus',
                    'Upon': 'sand',
                },
            ),
        ]

        tator_qaqc_processor.get_suspicious_records()

        assert len(tator_qaqc_processor.final_records) == 1
        assert tator_qaqc_processor.final_records[0]['observation_uuid'] == 1
        assert tator_qaqc_processor.final_records[0]['problems'] == 'Scientific Name,Upon'

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_find_long_host_associate_time_diff(self, fake_session, stub_annotator, stub_worms_match):
        media_id = 100
        fps = 30
        tator_qaqc_processor = TatorSubQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            # the host itself
            make_localization(
                elemental_id=1,
                media=media_id,
                frame=0,
                attributes={'Scientific Name': 'Anemone'},
            ),
            # 59s after the host -> not flagged
            make_localization(
                elemental_id=2,
                media=media_id,
                frame=59 * fps,
                attributes={
                    'Scientific Name': 'Clownfish',
                    'Upon': 'Anemone',
                },
            ),
            # 60s after host -> flagged
            make_localization(
                elemental_id=3,
                media=media_id,
                frame=61 * fps,
                attributes={
                    'Scientific Name': 'Damselfish',
                    'Upon': 'Anemone',
                },
            ),
            # host never appears in this deployment -> flagged
            make_localization(
                elemental_id=4,
                media=media_id,
                frame=20 * fps,
                attributes={
                    'Scientific Name': 'Turtle',
                    'Upon': 'Coral',
                },
            ),
            # lowercase upon (a substrate, not a host) -> skipped entirely
            make_localization(
                elemental_id=5,
                media=media_id,
                frame=40 * fps,
                attributes={
                    'Scientific Name': 'Fish2',
                    'Upon': 'sand',
                },
            ),
            # no upon -> skipped
            make_localization(
                elemental_id=6,
                media=media_id,
                frame=50 * fps,
                attributes={'Scientific Name': 'Fish3'}),
        ]

        with patch.object(TatorRestClient, 'get_media_by_id', return_value={'id': media_id, 'fps': fps}):
            tator_qaqc_processor.find_long_host_associate_time_diff()

        records_by_id = {record['observation_uuid']: record for record in tator_qaqc_processor.final_records}
        assert set(records_by_id.keys()) == {3, 4}
        assert '61 seconds' in records_by_id[3]['host_upon_time_diff']
        assert records_by_id[4]['host_upon_time_diff'] == 'Unable to find matching host in previous records'

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_all_sizes_counts_unique_combinations(self, fake_session, stub_annotator, stub_worms_match):
        tator_qaqc_processor = TatorSubQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={
                    'Scientific Name': 'X',
                    'Size': '10cm',
                },
            ),
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={
                    'Scientific Name': 'X',
                    'Size': '10cm',
                },
            ),
            make_localization(
                elemental_id=3,
                frame=3,
                attributes={
                    'Scientific Name': 'X',
                    'Size': '20cm',
                },
            ),
        ]

        tator_qaqc_processor.get_all_sizes()

        assert tator_qaqc_processor.final_records['X:::10cm']['count'] == 2
        assert tator_qaqc_processor.final_records['X:::20cm']['count'] == 1

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_unique_taxa_tracks_counts(self, fake_session, stub_annotator, stub_worms_match):
        tator_qaqc_processor = TatorSubQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            make_localization(
                elemental_id=1,
                frame=1,
                width=1,
                height=1,
                localization_type=TatorLocalizationType.SUB_BOX,
                attributes={'Scientific Name': 'X', 'Categorical Abundance': '1-19'},  # count 10
            ),
            make_localization(
                elemental_id=2,
                frame=2,
                localization_type=TatorLocalizationType.SUB_DOT,
                attributes={'Scientific Name': 'X', 'Categorical Abundance': '100-999'},  # count 500, new max
            ),
        ]

        tator_qaqc_processor.get_unique_taxa()

        taxa = tator_qaqc_processor.final_records['X::']
        assert taxa['box_count'] == 1
        assert taxa['dot_count'] == 1
        assert taxa['max_count'] == 500

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_summary_processes_records_with_substrates_and_timestamp(
            self, fake_session, stub_annotator, stub_worms_match,
    ):
        media_id = 100
        media = make_media(media_id=media_id)
        substrates_response = [
            {
                'media_id': media_id,
                'substrates': [
                    {
                        'frame': 0,
                        'Relief': 'flat',
                    },
                ],
            },
        ]
        tator_qaqc_processor = TatorSubQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            make_localization(
                elemental_id=1,
                media=media_id,
                frame=30,
                localization_type=TatorLocalizationType.SUB_DOT,
                attributes={'Scientific Name': 'X'},
            ),
        ]

        with patch.object(TatorRestClient, 'get_substrates', return_value=substrates_response), \
                patch.object(TatorRestClient, 'get_medias_for_sections', return_value=[media]):
            tator_qaqc_processor.get_summary()

        record = tator_qaqc_processor.final_records[0]
        assert record['timestamp'] == formatted_start_time(plus_seconds=1)
        assert record['relief'] == 'flat'
