from unittest.mock import MagicMock, patch

import pytest

from application.tator.tator_localization_processor import TatorLocalizationProcessor
from application.tator.tator_rest_client import TatorRestClient
from application.tator.tator_type import TatorLocalizationType
from test.data.tator_responses import fji_2025_dscm_03_localizations, fji_2025_dscm_03_section
from test.tator.conftest import DARC_REVIEW_URL, TATOR_URL, make_localization, mock_get_section_by_id


@pytest.mark.usefixtures('mock_phylogeny_cache')
class TestTatorLocalizationProcessor:
    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_init(self, fake_session):
        media_list = [{'id': 1, 'name': 'media1'}, {'id': 2, 'name': 'media2'}]
        localization_processor = TatorLocalizationProcessor(
            project_id=1,
            section_ids=['1', '2'],
            tator_url=TATOR_URL,
            darc_review_url=DARC_REVIEW_URL,
            media_list=media_list,
        )
        assert localization_processor.project_id == 1
        assert localization_processor.tator_url == TATOR_URL
        assert localization_processor.darc_review_url == DARC_REVIEW_URL
        assert localization_processor.sections[0].section_id == '1'
        assert localization_processor.sections[1].section_id == '2'
        assert localization_processor.media_list == media_list
        # session['tator_token'] was actually used to build the auth header, not just read
        assert localization_processor.tator_client._headers['Authorization'] == 'Token fake-token'

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_fetch_localizations_by_section(self, fake_session):
        def fake_get_localizations(project_id, section_id, media_ids=None):
            assert project_id == 1
            assert media_ids is None
            return [{'id': section_id * 10}]

        with patch.object(TatorRestClient, 'get_localizations', side_effect=fake_get_localizations):
            tator_localization_processor = TatorLocalizationProcessor(
                project_id=1,
                section_ids=['1', '2'],
                tator_url=TATOR_URL,
            )
            tator_localization_processor.fetch_localizations()

        assert tator_localization_processor.sections[0].localizations == [{'id': 10}]
        assert tator_localization_processor.sections[1].localizations == [{'id': 20}]

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_fetch_localizations_by_media_list_routes_by_master_section(self, fake_session):
        media_list = [{'id': 100}, {'id': 200}]
        localization_for_section_1 = {'id': 1, 'master_section': 1}
        localization_for_section_2 = {'id': 2, 'master_section': 2}

        with patch.object(
                TatorRestClient, 'get_localizations',
                return_value=[localization_for_section_1, localization_for_section_2],
        ) as mock_get_localizations:
            tator_localization_processor = TatorLocalizationProcessor(
                project_id=1,
                section_ids=['1', '2'],
                tator_url=TATOR_URL,
                media_list=media_list,
            )
            tator_localization_processor.fetch_localizations()

        mock_get_localizations.assert_called_once_with(1, media_ids=[100, 200])
        sections_by_id = {section.section_id: section for section in tator_localization_processor.sections}
        assert sections_by_id['1'].localizations == [localization_for_section_1]
        assert sections_by_id['2'].localizations == [localization_for_section_2]

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_fetch_localizations_raises_on_unrecognized_master_section(self, fake_session):
        media_list = [{'id': 100}]
        localizations = [{'id': 3, 'master_section': 999}]  # not among the requested sections (1, 2)

        with patch.object(TatorRestClient, 'get_localizations', return_value=localizations):
            tator_localization_processor = TatorLocalizationProcessor(
                project_id=1,
                section_ids=['1', '2'],
                tator_url=TATOR_URL,
                media_list=media_list,
            )
            with pytest.raises(ValueError):
                tator_localization_processor.fetch_localizations()

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_fetch_localizations_batches_media_ids_by_50(self, fake_session):
        media_list = [{'id': i} for i in range(1, 121)]  # 120 media -> batches of 50, 50, 20

        with patch.object(TatorRestClient, 'get_localizations', return_value=[]) as mock_get_localizations:
            tator_localization_processor = TatorLocalizationProcessor(
                project_id=1,
                section_ids=['1'],
                tator_url=TATOR_URL,
                media_list=media_list,
            )
            tator_localization_processor.fetch_localizations()

        batches = [call.kwargs['media_ids'] for call in mock_get_localizations.call_args_list]
        assert [len(batch) for batch in batches] == [50, 50, 20]

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_media_id_map_uses_media_list_when_present(self, fake_session):
        media_list = [{'id': '10', 'name': 'a'}, {'id': 20, 'name': 'b'}]
        tator_localization_processor = TatorLocalizationProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
            media_list=media_list,
        )

        result = tator_localization_processor._get_media_id_map()

        assert result == {10: media_list[0], 20: media_list[1]}

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_media_id_map_fetches_from_rest_when_no_media_list(self, fake_session):
        fetched_media = [{'id': 5, 'name': 'x'}]

        with patch.object(TatorRestClient, 'get_medias_for_sections', return_value=fetched_media) as mock_get_medias:
            tator_localization_processor = TatorLocalizationProcessor(
                project_id=1,
                section_ids=['1', '2'],
                tator_url=TATOR_URL,
            )
            result = tator_localization_processor._get_media_id_map()

        mock_get_medias.assert_called_once_with(project_id=1, section_ids=[1, 2])
        assert result == {5: fetched_media[0]}

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_annotator_name_fetches_and_caches(self, fake_session, stub_annotator):
        tator_localization_processor = TatorLocalizationProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        first = tator_localization_processor._get_annotator_name(42)
        second = tator_localization_processor._get_annotator_name(42)

        assert first == 'Joe Dirt'
        assert second == 'Joe Dirt'
        assert stub_annotator.call_count == 1  # second call was served from the session cache
        assert fake_session['tator_usernames'] == {42: 'Joe Dirt'}

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_annotator_name_unknown_user(self, fake_session):
        with patch.object(TatorRestClient, 'get_user', return_value={}):  # no 'first_name' in the response
            tator_localization_processor = TatorLocalizationProcessor(
                project_id=1,
                section_ids=['1'],
                tator_url=TATOR_URL,
            )
            name = tator_localization_processor._get_annotator_name(99)

        assert name == 'Unknown annotator (#99)'

    def test_load_substrates_maps_fields(self):
        localization_dict = {}

        TatorLocalizationProcessor._load_substrates(localization_dict, {
            'Primary Substrate': 'sand',
            'Secondary Substrate': 'mud',
            'Bedforms': 'ripples',
            'Relief': 'low',
            'Substrate Notes': 'note1',
            'Deployment Notes': 'note2',
        })

        assert localization_dict == {
            'primary_substrate': 'sand',
            'secondary_substrate': 'mud',
            'bedforms': 'ripples',
            'relief': 'low',
            'substrate_notes': 'note1',
            'deployment_notes': 'note2',
        }

    def test_get_substrate_for_frame_returns_latest_at_or_before(self):
        substrates = [
            {'frame': 0, 'Relief': 'flat'},
            {'frame': 50, 'Relief': 'moderate'},
            {'frame': 100, 'Relief': 'steep'},
        ]

        result = TatorLocalizationProcessor._get_substrate_for_frame(
            substrate_entries=substrates,
            localization={'frame': 75, 'scientific_name': 'X', 'media_id': 1},
        )

        assert result == {'frame': 50, 'Relief': 'moderate'}

    def test_get_substrate_for_frame_none_before_first_entry(self):
        substrates = [{'frame': 100, 'Relief': 'steep'}]

        result = TatorLocalizationProcessor._get_substrate_for_frame(
            substrate_entries=substrates,
            localization={'frame': 10, 'scientific_name': 'X', 'media_id': 1},
        )

        assert result is None

    def test_process_records_happy_path(self, fake_session):
        def fake_fetch_worms(self, scientific_name):
            self.data[scientific_name] = {'phylum': 'Ctenophora', 'aphia_id': 106896}
            return True

        with patch.object(TatorRestClient, 'get_section_by_id', return_value=fji_2025_dscm_03_section), \
                patch.object(TatorRestClient, 'get_user', return_value={'first_name': 'Michael', 'last_name': 'Scott'}), \
                patch('application.util.phylogeny_cache.PhylogenyCache.fetch_worms', fake_fetch_worms):
            tator_localization_processor = TatorLocalizationProcessor(
                project_id=26,
                section_ids=['22831'],
                tator_url=TATOR_URL,
            )
            tator_localization_processor.sections[0].localizations = fji_2025_dscm_03_localizations
            tator_localization_processor.process_records()

        box_record, dot_record = tator_localization_processor.final_records

        assert box_record == {
            'observation_uuid': 'b36a3114-4121-4a8f-aaf1-f99b42fd6f94',
            'all_localizations': [{
                'id': 274549696,
                'elemental_id': 'b36a3114-4121-4a8f-aaf1-f99b42fd6f94',
                'version': 45,
                'type': TatorLocalizationType.BOX,
                'points': [0.32661, 0.42762],
                'dimensions': [0.09417040358744394, 0.2297476759628154],
            }],
            'media_id': 20986981,
            'frame': 287,
            'frame_url': '/tator/frame/20986981/287',
            'annotator': 'Michael Scott',
            'type': TatorLocalizationType.BOX,
            'scientific_name': 'Cydippida',
            'section_id': '22831',
            'video_sequence_name': 'FJI_2025_dscm_03',
            'count': 0,
            'attracted': 'Not Attracted',
            'identification_remarks': '',
            'identified_by': '',
            'notes': '',
            'qualifier': 'stet.',
            'reason': 'Non-target taxon',
            'tentative_id': '',
            'morphospecies': '',
            'good_image': False,
            'depth_m': 454.157,
            'do_temp_c': 10.217,
            'do_concentration_salin_comp_mol_L': 125.679,
            'phylum': 'Ctenophora',
            'aphia_id': 106896,
        }
        assert dot_record == {
            'observation_uuid': '9940af13-edcc-48dd-8747-a438a629b373',
            'all_localizations': [{
                'id': 274549695,
                'elemental_id': '9940af13-edcc-48dd-8747-a438a629b373',
                'version': 45,
                'type': TatorLocalizationType.DOT,
                'points': [0.37369, 0.49004],
                'dimensions': None,
            }],
            'media_id': 20986981,
            'frame': 287,
            'frame_url': '/tator/frame/20986981/287',
            'annotator': 'Michael Scott',
            'type': TatorLocalizationType.DOT,
            'scientific_name': 'Cydippida',
            'section_id': '22831',
            'video_sequence_name': 'FJI_2025_dscm_03',
            'count': 1,
            'attracted': 'Not Attracted',
            'categorical_abundance': '--',
            'identification_remarks': '',
            'identified_by': '',
            'notes': '',
            'qualifier': 'stet.',
            'reason': 'Non-target taxon',
            'tentative_id': '',
            'morphospecies': '',
            'good_image': False,
            'depth_m': 454.157,
            'do_temp_c': 10.217,
            'do_concentration_salin_comp_mol_L': 125.679,
            'phylum': 'Ctenophora',
            'aphia_id': 106896,
        }

    def test_process_records_no_localizations(self, fake_session):
        with patch.object(TatorRestClient, 'get_section_by_id', return_value=fji_2025_dscm_03_section):
            tator_localization_processor = TatorLocalizationProcessor(
                project_id=26,
                section_ids=['22831'],
                tator_url=TATOR_URL,
            )
            tator_localization_processor.sections[0].localizations = []
            tator_localization_processor.process_records()

        assert tator_localization_processor.final_records == []

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_process_records_skips_unrecognized_localization_types(
            self, fake_session, stub_annotator, stub_worms_match
    ):
        tator_localization_processor = TatorLocalizationProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_localization_processor.sections[0].localizations = [
            make_localization(
                localization_id=1,
                localization_type=999,
                attributes={'Scientific Name': 'Should be skipped'},
            ),
            make_localization(
                localization_id=2,
                localization_type=TatorLocalizationType.DOT,
                attributes={'Scientific Name': 'Kept'},
            ),
        ]

        tator_localization_processor.process_records()

        assert len(tator_localization_processor.final_records) == 1
        assert tator_localization_processor.final_records[0]['scientific_name'] == 'Kept'

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    @pytest.mark.parametrize('abundance,expected_count', [
        ('1-19', 10),
        ('20-49', 35),
        ('50-99', 75),
        ('100-999', 500),
        ('1000+', 1000),
        ('bogus-value', 0),  # unrecognized value hits the default case and is left at the default
    ])
    def test_process_records_maps_categorical_abundance_to_count(
            self, fake_session, stub_annotator, stub_worms_match, abundance, expected_count,
    ):
        tator_localization_processor = TatorLocalizationProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_localization_processor.sections[0].localizations = [
            make_localization(
                localization_type=TatorLocalizationType.BOX,
                width=1,
                height=1,
                attributes={
                    'Scientific Name': 'X',
                    'Categorical Abundance': abundance,
                },
            ),
        ]

        tator_localization_processor.process_records()

        assert tator_localization_processor.final_records[0]['count'] == expected_count

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_process_records_sets_lat_long_from_position(self, fake_session, stub_annotator, stub_worms_match):
        tator_localization_processor = TatorLocalizationProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_localization_processor.sections[0].localizations = [
            make_localization(
                attributes={
                    'Scientific Name': 'X',
                    'Position': [-158.1234567, 21.7654321],
                },
            ),
        ]

        tator_localization_processor.process_records()

        record = tator_localization_processor.final_records[0]
        assert record['long'] == -158.1235
        assert record['lat'] == 21.7654

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_process_records_calculates_timestamp_for_dropcam(self, fake_session, stub_annotator, stub_worms_match):
        media_id = 100
        fake_session['media_timestamps'] = {media_id: '2025-01-01T00:00:00+00:00'}
        tator_localization_processor = TatorLocalizationProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_localization_processor.sections[0].bottom_time = '2025-01-01 00:00:10Z'
        tator_localization_processor.sections[0].localizations = [
            make_localization(
                media=media_id,
                frame=600,
                attributes={'Scientific Name': 'X'},
            ),
        ]

        with patch.object(TatorRestClient, 'get_medias_for_sections', return_value=[{'id': media_id, 'fps': 30}]):
            tator_localization_processor.process_records(get_timestamp=True)

        record = tator_localization_processor.final_records[0]
        assert record['timestamp'] == '2025-01-01 00:00:20Z'
        assert record['camera_seafloor_arrival'] == '2025-01-01 00:00:10Z'
        assert record['animal_arrival'] == '0:00:10'

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_process_records_skips_timestamp_population_for_dropcam_when_no_bottom_time(
            self, fake_session, stub_annotator, stub_worms_match
    ):
        media_id = 150
        tator_localization_processor = TatorLocalizationProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        # section.bottom_time defaults to None (no Arrival time found for this deployment)
        tator_localization_processor.sections[0].localizations = [
            make_localization(
                media=media_id,
                attributes={'Scientific Name': 'X'},
            ),
        ]

        with patch.object(TatorRestClient, 'get_medias_for_sections', return_value=[{'id': media_id, 'fps': 30}]):
            tator_localization_processor.process_records(get_timestamp=True)

        record = tator_localization_processor.final_records[0]
        assert 'timestamp' not in record
        assert 'camera_seafloor_arrival' not in record
        assert 'animal_arrival' not in record

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_process_records_calculates_timestamp_for_sub(self, fake_session, stub_annotator, stub_worms_match):
        media_id = 200
        tator_localization_processor = TatorLocalizationProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
            media_list=[
                {
                    'id': media_id,
                    'fps': 30,
                    'name': 'sub-media',
                    'attributes': {'Start Time': '2025-01-01T00:00:00+00:00'},
                }
            ],
        )
        tator_localization_processor.sections[0].localizations = [
            make_localization(
                localization_type=TatorLocalizationType.SUB_BOX,
                media=media_id,
                frame=60,
                width=1,
                height=1,
                attributes={'Scientific Name': 'X'},
            ),
        ]

        tator_localization_processor.process_records(get_timestamp=True)

        record = tator_localization_processor.final_records[0]
        assert record['timestamp'] == '2025-01-01 00:00:02Z'  # frame 60 / 30fps = 2s after Start Time
        assert 'camera_seafloor_arrival' not in record  # only the dropcam should set this

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_process_records_skips_timestamp_for_sub_when_no_start_time(
            self, fake_session, stub_annotator, stub_worms_match
    ):
        media_id = 250
        tator_localization_processor = TatorLocalizationProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
            media_list=[
                {
                    'id': media_id,
                    'fps': 30,
                    'name': 'sub-media',
                    'attributes': {}
                },
            ],
        )
        tator_localization_processor.sections[0].localizations = [
            make_localization(
                localization_type=TatorLocalizationType.SUB_BOX,
                media=media_id,
                width=1,
                height=1,
                attributes={'Scientific Name': 'X'},
            )
        ]

        tator_localization_processor.process_records(get_timestamp=True)

        assert 'timestamp' not in tator_localization_processor.final_records[0]

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_process_records_fetches_dropcam_fieldbook_data(self, fake_session, stub_annotator, stub_worms_match):
        tator_localization_processor = TatorLocalizationProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
            darc_review_url=DARC_REVIEW_URL,
        )
        # no 'Depth' attribute, so depth_m should fall back to the fieldbook's value
        tator_localization_processor.sections[0].localizations = [
            make_localization(
                attributes={'Scientific Name': 'X'}
            )
        ]
        fieldbook_response = MagicMock(status_code=200)
        fieldbook_response.json.return_value = {
            'deployments': [
                {
                    'deployment_name': 'Section_1',
                    'lat': 21.5,
                    'long': -158.5,
                    'bait_type': 'tasty fish',
                    'depth_m': 1200,
                },
            ]
        }

        with patch('application.tator.tator_localization_processor.requests.get', return_value=fieldbook_response):
            tator_localization_processor.process_records(get_dropcam_fieldbook_data=True)

        record = tator_localization_processor.final_records[0]
        assert record['lat'] == 21.5
        assert record['long'] == -158.5
        assert record['bait_type'] == 'tasty fish'
        assert record['depth_m'] == 1200

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_process_records_raises_when_fieldbook_fetch_fails(self, fake_session, stub_annotator, stub_worms_match):
        tator_localization_processor = TatorLocalizationProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
            darc_review_url=DARC_REVIEW_URL,
        )
        tator_localization_processor.sections[0].localizations = [
            make_localization(
                attributes={'Scientific Name': 'X'}
            ),
        ]
        fieldbook_response = MagicMock(status_code=500, text='server error')

        with patch('application.tator.tator_localization_processor.requests.get', return_value=fieldbook_response):
            with pytest.raises(ValueError):
                tator_localization_processor.process_records(get_dropcam_fieldbook_data=True)

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_process_records_loads_dropcam_substrates_from_media_attributes(
            self, fake_session, stub_annotator, stub_worms_match
    ):
        media_id = 300
        fetched_media = [
            {
                'id': media_id,
                'attributes': {'Primary Substrate': 'sand', 'Secondary Substrate': 'mud'},
            }
        ]
        tator_localization_processor = TatorLocalizationProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_localization_processor.sections[0].localizations = [
            make_localization(
                media=media_id,
                attributes={'Scientific Name': 'X'},
            ),
        ]

        with patch.object(TatorRestClient, 'get_medias_for_sections', return_value=fetched_media):
            tator_localization_processor.process_records(get_dropcam_substrates=True)

        record = tator_localization_processor.final_records[0]
        assert record['primary_substrate'] == 'sand'
        assert record['secondary_substrate'] == 'mud'

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_process_records_loads_substrate_for_frame_when_sub_media_substrates_given(
            self, fake_session, stub_annotator, stub_worms_match
    ):
        media_id = 400
        tator_localization_processor = TatorLocalizationProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_localization_processor.sections[0].localizations = [
            make_localization(
                media=media_id,
                frame=50,
                attributes={'Scientific Name': 'X'},
            )
        ]
        sub_media_substrates = {
            media_id: [
                {'frame': 0, 'Relief': 'flat'},
                {'frame': 40, 'Relief': 'moderate'},
            ]
        }

        tator_localization_processor.process_records(sub_media_substrates=sub_media_substrates)

        assert tator_localization_processor.final_records[0]['relief'] == 'moderate'

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_process_records_tracks_unmatched_scientific_names(self, fake_session, stub_annotator):
        no_match_records = set()

        with patch('application.util.phylogeny_cache.PhylogenyCache.fetch_worms', return_value=False):
            tator_localization_processor = TatorLocalizationProcessor(
                project_id=1,
                section_ids=['1'],
                tator_url=TATOR_URL,
            )
            tator_localization_processor.sections[0].localizations = [
                make_localization(
                    attributes={'Scientific Name': 'Unmatchable'},
                ),
            ]

            tator_localization_processor.process_records(no_match_records=no_match_records)

        assert 'Unmatchable' in no_match_records
        assert 'phylum' not in tator_localization_processor.final_records[0]
