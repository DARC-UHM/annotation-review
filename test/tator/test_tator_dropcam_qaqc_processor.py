from unittest.mock import MagicMock, patch

import pytest

from application.tator.tator_dropcam_qaqc_processor import TatorDropcamQaqcProcessor
from application.tator.tator_rest_client import TatorRestClient
from application.tator.tator_type import TatorLocalizationType
from test.tator.conftest import (
    DARC_REVIEW_URL,
    DEFAULT_MEDIA_START_TIME,
    TATOR_URL,
    formatted_start_time,
    make_localization,
    make_media,
    mock_get_section_by_id,
)


@pytest.mark.usefixtures('mock_phylogeny_cache')
class TestTatorDropcamQaqcProcessor:
    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_check_attracted_not_attracted_flags_mismatches(self, fake_session, stub_annotator, stub_worms_match):
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        attracted_dict = {'Either': 2, 'NeverAttracted': 0, 'AlwaysAttracted': 1}
        tator_qaqc_processor.sections[0].localizations = [
            # scientific name not in attracted_dict at all -> flagged
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={
                    'Scientific Name': 'Not in dict',
                    'Attracted': 'Attracted',
                },
            ),
            # attracted_dict says "either" (2) -> always flagged
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={
                    'Scientific Name': 'Either',
                    'Attracted': 'Attracted',
                },
            ),
            # marked Attracted but attracted_dict says this taxon is never attracted (0) -> mismatch, flagged
            make_localization(
                elemental_id=3,
                frame=3,
                attributes={
                    'Scientific Name': 'NeverAttracted',
                    'Attracted': 'Attracted',
                },
            ),
            # marked Not Attracted but attracted_dict says this taxon is always attracted (1) -> mismatch, flagged
            make_localization(
                elemental_id=4,
                frame=4,
                attributes={
                    'Scientific Name': 'AlwaysAttracted',
                    'Attracted': 'Not Attracted',
                },
            ),
            # consistent with attracted_dict -> not flagged
            make_localization(
                elemental_id=5,
                frame=5,
                attributes={
                    'Scientific Name': 'AlwaysAttracted',
                    'Attracted': 'Attracted',
                },
            ),
            make_localization(
                elemental_id=6,
                frame=6,
                attributes={
                    'Scientific Name': 'NeverAttracted',
                    'Attracted': 'Not Attracted',
                },
            ),
        ]

        tator_qaqc_processor.check_attracted_not_attracted(attracted_dict)

        assert len(tator_qaqc_processor.final_records) == 4
        flagged_ids = {record['observation_uuid'] for record in tator_qaqc_processor.final_records}
        assert flagged_ids == {1, 2, 3, 4}

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_check_same_name_qualifier_flags_mismatched_qualifiers(
            self, fake_session, stub_annotator, stub_worms_match
    ):
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            # same scientific name, different qualifier -> both flagged
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={
                    'Scientific Name': 'Mellivora',
                    'Qualifier': 'stet.',
                },
            ),
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={
                    'Scientific Name': 'Mellivora',
                    'Qualifier': 'indet.',
                },
            ),
            # same scientific name, same qualifier -> not flagged
            make_localization(
                elemental_id=3,
                frame=3,
                attributes={
                    'Scientific Name': 'Nautilus',
                    'Qualifier': 'stet.',
                },
            ),
            make_localization(
                elemental_id=4,
                frame=4,
                attributes={
                    'Scientific Name': 'Nautilus',
                    'Qualifier': 'stet.',
                },
            ),
            # same scientific name but different tentative ID -> treated as a different combo, not compared
            make_localization(
                elemental_id=5,
                frame=5,
                attributes={
                    'Scientific Name': 'Amphiprion',
                    'Tentative ID': 'Amphiprion barberi',
                    'Qualifier': 'stet.',
                },
            ),
            make_localization(
                elemental_id=6,
                frame=6,
                attributes={
                    'Scientific Name': 'Amphiprion',
                    'Tentative ID': 'Amphiprion ocellaris',
                    'Qualifier': 'indet.',
                },
            ),
        ]

        tator_qaqc_processor.check_same_name_qualifier()

        flagged_ids = {record['observation_uuid'] for record in tator_qaqc_processor.final_records}
        assert flagged_ids == {1, 2}

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_check_non_target_not_attracted_flags_attracted_non_target_records(
            self, fake_session, stub_annotator, stub_worms_match,
    ):
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            # non-target reason but still marked attracted -> flagged
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={
                    'Scientific Name': 'Oreamnos',
                    'Reason': 'Non-target taxon',
                    'Attracted': 'Attracted',
                },
            ),
            # non-target reason and correctly marked not attracted -> not flagged
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={
                    'Scientific Name': 'Cervidae',
                    'Reason': 'Non-target taxon',
                    'Attracted': 'Not Attracted',
                },
            ),
            # not a non-target reason at all -> not flagged
            make_localization(
                elemental_id=3,
                frame=3,
                attributes={
                    'Scientific Name': 'Carcharhinus',
                    'Reason': '--',
                    'Attracted': 'Attracted',
                },
            ),
        ]

        tator_qaqc_processor.check_non_target_not_attracted()

        assert len(tator_qaqc_processor.final_records) == 1
        assert tator_qaqc_processor.final_records[0]['observation_uuid'] == 1

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_check_exists_in_image_references(self, fake_session, stub_annotator, stub_worms_match):
        image_refs = {'Known': {}}
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            # plain scientific name already in image_refs -> not flagged
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={'Scientific Name': 'Known'},
            ),
            # plain scientific name not in image_refs -> flagged
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={'Scientific Name': 'Unknown'},
            ),
            # composite key (name + tentative ID) not in image_refs -> flagged
            make_localization(
                elemental_id=3,
                frame=3,
                attributes={'Scientific Name': 'Known', 'Tentative ID': 'Tent'},
            ),
            # both tentative ID and morphospecies set -> always flagged, regardless of image_refs
            make_localization(
                elemental_id=4,
                frame=4,
                attributes={'Scientific Name': 'Known', 'Tentative ID': 'Tent', 'Morphospecies': 'sp1'},
            ),
            # composite key (name + morphospecies, no tentative ID) not in image_refs -> flagged
            make_localization(
                elemental_id=5,
                frame=5,
                attributes={'Scientific Name': 'Known', 'Morphospecies': 'sp2'},
            ),
        ]

        tator_qaqc_processor.check_exists_in_image_references(image_refs)

        records_by_id = {record['observation_uuid']: record for record in tator_qaqc_processor.final_records}
        assert set(records_by_id.keys()) == {2, 3, 4, 5}
        assert 'problems' not in records_by_id[2]
        assert 'problems' not in records_by_id[3]
        assert records_by_id[4]['problems'] == 'Tentative ID, Morphospecies'
        assert 'problems' not in records_by_id[5]

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_fetch_start_times_sets_bottom_time_from_arrival_frame(self, fake_session):
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        media_id = 100
        media = make_media(media_id=media_id, arrival='300')

        with patch.object(TatorRestClient, 'get_medias_for_sections', return_value=[media]):
            tator_qaqc_processor.fetch_start_times()

        assert fake_session['media_timestamps'][media_id] == DEFAULT_MEDIA_START_TIME
        # 300 frames / 30fps = 10s after start
        assert tator_qaqc_processor.sections[0].bottom_time == formatted_start_time(plus_seconds=10)

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_fetch_start_times_treats_not_observed_arrival_as_frame_zero(self, fake_session):
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        media = make_media(arrival='Not observed')

        with patch.object(TatorRestClient, 'get_medias_for_sections', return_value=[media]):
            tator_qaqc_processor.fetch_start_times()

        assert tator_qaqc_processor.sections[0].bottom_time == formatted_start_time()

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_fetch_start_times_skips_media_without_start_time(self, fake_session):
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        media = make_media(start_time=None, arrival='100')

        with patch.object(TatorRestClient, 'get_medias_for_sections', return_value=[media]):
            tator_qaqc_processor.fetch_start_times()

        assert 300 not in fake_session.get('media_timestamps', {})
        assert tator_qaqc_processor.sections[0].bottom_time is None

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_fetch_start_times_skips_bottom_time_when_no_arrival(self, fake_session):
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        media_id = 100
        media = make_media(media_id=media_id)  # no 'Arrival'

        with patch.object(TatorRestClient, 'get_medias_for_sections', return_value=[media]):
            tator_qaqc_processor.fetch_start_times()

        assert fake_session['media_timestamps'][media_id] == DEFAULT_MEDIA_START_TIME
        assert tator_qaqc_processor.sections[0].bottom_time is None

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_fetch_start_times_reuses_cached_media_timestamp(self, fake_session):
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        media_id = 100
        # pre-cached from an earlier fetch, deliberately different from this media's own Start Time attribute
        fake_session['media_timestamps'] = {media_id: '2020-01-01T00:00:00+00:00'}
        media_start_time = '2025-06-01T00:00:00+00:00'
        media = make_media(media_id=media_id, start_time=media_start_time, arrival='30')

        with patch.object(TatorRestClient, 'get_medias_for_sections', return_value=[media]):
            tator_qaqc_processor.fetch_start_times()

        # cached session value is left untouched (these never change, so we save a session write)
        assert fake_session['media_timestamps'][media_id] == '2020-01-01T00:00:00+00:00'
        # bottom_time is computed from the media's own Start Time attribute
        assert tator_qaqc_processor.sections[0].bottom_time == formatted_start_time(
            start_time=media_start_time, plus_seconds=1,
        )

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_fetch_start_times_raises_on_unparseable_arrival(self, fake_session):
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        media = make_media(arrival='unparseable!')

        with patch.object(TatorRestClient, 'get_medias_for_sections', return_value=[media]):
            with pytest.raises(ValueError):
                tator_qaqc_processor.fetch_start_times()

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_unique_taxa_aggregates_counts_and_first_sightings(
            self, fake_session, stub_annotator, stub_worms_match,
    ):
        media_id = 100
        media = make_media(media_id=media_id, arrival='0')
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            # box at 2s - processed first, but not the earliest sighting
            make_localization(
                elemental_id='box-2s',
                media=media_id,
                frame=60,
                width=1,
                height=1,
                localization_type=TatorLocalizationType.BOX,
                attributes={'Scientific Name': 'Squalus'},
            ),
            # box at 1s - earlier than the one above, should become "first_box"
            make_localization(
                elemental_id='box-1s',
                media=media_id,
                frame=30,
                width=1,
                height=1,
                localization_type=TatorLocalizationType.BOX,
                attributes={'Scientific Name': 'Squalus'},
            ),
            # dot at 3s - only dot sighting, becomes "first_dot"
            make_localization(
                elemental_id='dot-3s',
                media=media_id,
                frame=90,
                localization_type=TatorLocalizationType.DOT,
                attributes={'Scientific Name': 'Squalus'},
            ),
        ]

        with patch.object(TatorRestClient, 'get_medias_for_sections', return_value=[media]):
            tator_qaqc_processor.get_unique_taxa()

        assert list(tator_qaqc_processor.final_records.keys()) == ['Squalus::']
        taxa = tator_qaqc_processor.final_records['Squalus::']
        assert taxa['scientific_name'] == 'Squalus'
        assert taxa['box_count'] == 2
        assert taxa['dot_count'] == 1
        assert taxa['first_box'] == formatted_start_time(plus_seconds=1)
        assert taxa['first_box_url'] == f'{TATOR_URL}/1/annotation/{media_id}?frame=30&selected_entity=box-1s'
        assert taxa['first_dot'] == formatted_start_time(plus_seconds=3)
        assert taxa['first_dot_url'] == f'{TATOR_URL}/1/annotation/{media_id}?frame=90&selected_entity=dot-3s'

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_unique_taxa_counts_sightings_without_a_timestamp(
            self, fake_session, stub_annotator, stub_worms_match,
    ):
        media_id = 100
        # no 'Arrival' attribute -> fetch_start_times() never sets section.bottom_time, so process_records()
        # skips timestamp calculation entirely for these records
        media = make_media(media_id=media_id)
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            make_localization(
                elemental_id='box-no-timestamp',
                media=media_id,
                frame=30,
                width=1,
                height=1,
                localization_type=TatorLocalizationType.BOX,
                attributes={'Scientific Name': 'Squalus'},
            ),
            make_localization(
                elemental_id='dot-no-timestamp',
                media=media_id,
                frame=60,
                localization_type=TatorLocalizationType.DOT,
                attributes={'Scientific Name': 'Squalus'},
            ),
        ]

        with patch.object(TatorRestClient, 'get_medias_for_sections', return_value=[media]):
            tator_qaqc_processor.get_unique_taxa()

        taxa = tator_qaqc_processor.final_records['Squalus::']
        assert taxa['box_count'] == 1
        assert taxa['dot_count'] == 1
        assert taxa['first_box'] == ''
        assert taxa['first_dot'] == ''

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_max_n_tracks_highest_count_per_deployment(self, fake_session, stub_annotator, stub_worms_match):
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
            darc_review_url=DARC_REVIEW_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            # DOT, categorical abundance '1-19' -> count 10
            make_localization(
                elemental_id=1,
                media=100,
                frame=1,
                attributes={
                    'Scientific Name': 'Squalus',
                    'Attracted': 'Attracted',
                    'Categorical Abundance': '1-19',
                },
            ),
            # same taxon/deployment, later frame with a higher count -> should become the new max
            make_localization(
                elemental_id=2,
                media=100,
                frame=2,
                attributes={
                    'Scientific Name': 'Squalus',
                    'Attracted': 'Attracted',
                    'Categorical Abundance': '100-999',
                },
            ),
            # box with no abundance override -> count stays 0 -> filtered out (count < 1)
            make_localization(
                elemental_id=3,
                media=100,
                frame=3,
                localization_type=TatorLocalizationType.BOX,
                attributes={'Scientific Name': 'Squalus'},
            ),
            # marked Not Attracted -> filtered out regardless of count
            make_localization(
                elemental_id=4,
                media=100,
                frame=4,
                attributes={
                    'Scientific Name': 'Mustelus',
                    'Attracted': 'Not Attracted',
                    'Categorical Abundance': '100-999',
                },
            ),
        ]
        fieldbook_response = MagicMock(status_code=200)
        fieldbook_response.json.return_value = {'deployments': []}

        with patch('application.tator.tator_localization_processor.requests.get', return_value=fieldbook_response):
            tator_qaqc_processor.get_max_n()

        assert tator_qaqc_processor.final_records['unique_taxa'] == ['Squalus']
        max_n_dict = tator_qaqc_processor.final_records['deployments']['Section_1']['max_n_dict']
        assert max_n_dict['Squalus']['max_n'] == 500
        assert max_n_dict['Squalus']['max_n_url'] == f'{TATOR_URL}/1/annotation/100?frame=2'

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_tofa_builds_deployment_taxa_and_accumulation_curve(
            self, fake_session, stub_annotator, stub_worms_match,
    ):
        media_id = 100
        media = make_media(media_id=media_id, arrival='0')
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
            darc_review_url=DARC_REVIEW_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            # first sighting of Magikarp, 1s after bottom time
            make_localization(
                elemental_id=1,
                media=media_id,
                frame=30,
                attributes={
                    'Scientific Name': 'Magikarp',
                    'Attracted': 'Attracted',
                    'Categorical Abundance': '1-19',
                },
            ),
            # first sighting of Goldeen, 2s after bottom time
            make_localization(
                elemental_id=2,
                media=media_id,
                frame=60,
                attributes={
                    'Scientific Name': 'Goldeen',
                    'Attracted': 'Attracted',
                    'Categorical Abundance': '1-19',
                },
            ),
            # Not Attracted -> excluded, shouldn't affect Magikarp's first-seen/tofa/latest-timestamp tracking
            make_localization(
                elemental_id=3,
                media=media_id,
                frame=90,
                attributes={
                    'Scientific Name': 'Magikarp',
                    'Attracted': 'Not Attracted',
                    'Categorical Abundance': '1-19',
                },
            ),
            # box with no abundance override -> count 0 -> excluded (count < 1)
            make_localization(
                elemental_id=4,
                media=media_id,
                frame=120,
                localization_type=TatorLocalizationType.BOX,
                attributes={'Scientific Name': 'Magikarp'},
            ),
        ]
        fieldbook_response = MagicMock(status_code=200)
        fieldbook_response.json.return_value = {'deployments': []}

        with patch.object(TatorRestClient, 'get_medias_for_sections', return_value=[media]), \
                patch('application.tator.tator_localization_processor.requests.get', return_value=fieldbook_response):
            tator_qaqc_processor.get_tofa()

        assert tator_qaqc_processor.final_records['unique_taxa'] == ['Goldeen', 'Magikarp']
        assert tator_qaqc_processor.final_records['deployment_time'] == 1  # rounds up to the nearest hour
        assert tator_qaqc_processor.final_records['accumulation_data'] == [2]  # both taxa seen within hour 1
        tofa_dict = tator_qaqc_processor.final_records['deployments']['Section_1']['tofa_dict']
        assert tofa_dict['Magikarp']['tofa'] == '0:00:01'
        assert tofa_dict['Magikarp']['tofa_seconds'] == 1.0
        assert tofa_dict['Magikarp']['tofa_url'] == f'{TATOR_URL}/1/annotation/{media_id}?frame=30'
        assert tofa_dict['Goldeen']['tofa'] == '0:00:02'
        assert tofa_dict['Goldeen']['tofa_seconds'] == 2.0

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_tofa_updates_first_seen_and_tofa_when_an_earlier_sighting_is_processed_later(
            self, fake_session, stub_annotator, stub_worms_match,
    ):
        default_media = make_media(media_id=100, arrival='0')
        # no arrival: doesn't touch bottom_time
        default_media_minus_one_hour = make_media(media_id=200, start_time='2024-12-31T23:00:00+00:00')
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
            darc_review_url=DARC_REVIEW_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            make_localization(
                elemental_id=1,
                media=100,
                frame=60,
                attributes={
                    'Scientific Name': 'Nemo',
                    'Attracted': 'Attracted',
                    'Categorical Abundance': '1-19',
                },
            ),
            make_localization(
                elemental_id=2,
                media=200,
                frame=30,
                attributes={
                    'Scientific Name': 'Nemo',
                    'Attracted': 'Attracted',
                    'Categorical Abundance': '1-19',
                },
            ),
        ]
        fieldbook_response = MagicMock(status_code=200)
        fieldbook_response.json.return_value = {'deployments': []}

        with patch.object(TatorRestClient, 'get_medias_for_sections',
                          return_value=[default_media, default_media_minus_one_hour]), \
                patch('application.tator.tator_localization_processor.requests.get', return_value=fieldbook_response):
            tator_qaqc_processor.get_tofa()

        tofa_dict = tator_qaqc_processor.final_records['deployments']['Section_1']['tofa_dict']
        # the earlier sighting is before bottom_time, so its tofa clamps to 0 rather than going negative
        assert tofa_dict['Nemo']['tofa_seconds'] == 0.0
        assert tofa_dict['Nemo']['tofa_url'] == f'{TATOR_URL}/1/annotation/200?frame=30'

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_tofa_handles_no_available_timestamps(self, fake_session, stub_annotator, stub_worms_match):
        media_id = 200
        media = make_media(media_id=media_id)  # no Arrival
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
            darc_review_url=DARC_REVIEW_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            make_localization(
                elemental_id=1,
                media=media_id,
                frame=30,
                attributes={
                    'Scientific Name': 'Bruce',
                    'Attracted': 'Attracted',
                    'Categorical Abundance': '1-19',
                },
            ),
        ]
        fieldbook_response = MagicMock(status_code=200)
        fieldbook_response.json.return_value = {'deployments': []}

        with patch.object(TatorRestClient, 'get_medias_for_sections', return_value=[media]), \
                patch('application.tator.tator_localization_processor.requests.get', return_value=fieldbook_response):
            tator_qaqc_processor.get_tofa()

        assert tator_qaqc_processor.final_records == {
            'deployments': {},
            'unique_taxa': [],
            'deployment_time': 0,
            'accumulation_data': [],
        }

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_summary_processes_records_with_all_dropcam_flags(self, fake_session, stub_annotator, stub_worms_match):
        media_id = 100
        media = make_media(
            media_id=media_id,
            arrival='0',
            extra_attributes={'Primary Substrate': 'sand', 'Secondary Substrate': 'mud'},
        )
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
            darc_review_url=DARC_REVIEW_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            make_localization(
                elemental_id=1,
                media=media_id,
                frame=30,
                attributes={'Scientific Name': 'Squalus'},
            ),
        ]
        fieldbook_response = MagicMock(status_code=200)
        fieldbook_response.json.return_value = {'deployments': []}

        with patch.object(TatorRestClient, 'get_medias_for_sections', return_value=[media]), \
                patch('application.tator.tator_localization_processor.requests.get', return_value=fieldbook_response):
            tator_qaqc_processor.get_summary()

        record = tator_qaqc_processor.final_records[0]
        assert record['timestamp'] == formatted_start_time(plus_seconds=1)  # get_timestamp
        assert record['primary_substrate'] == 'sand'  # get_dropcam_substrates
        assert record['secondary_substrate'] == 'mud'
