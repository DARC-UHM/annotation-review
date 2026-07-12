from unittest.mock import patch

import pytest

from application.tator.tator_localization_processor import TatorLocalizationProcessor
from application.tator.tator_rest_client import TatorRestClient

TATOR_URL = 'https://tator.url'
DARC_REVIEW_URL = 'https://darc.review.url'


def mock_get_section_by_id(_, section_id):
    return {'id': section_id, 'name': f'Section_{section_id}', 'path': f'Expedition1.Section{section_id}'}


class FakeSession(dict):
    # flask.session behaves like a dict but also carries a ".modified" flag
    modified = False


@pytest.fixture
def fake_session():
    # flask.session is a werkzeug LocalProxy; unittest.mock.patch() can't auto-create a replacement for it
    # outside a request context, so we patch in a real dict-like stand-in and keep the patch active for
    # the whole test, since methods beyond __init__ (e.g. _get_annotator_name) also read/write session.
    session = FakeSession({'tator_token': 'fake-token'})
    with patch('application.tator.tator_localization_processor.session', new=session):
        yield session


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
            processor = TatorLocalizationProcessor(
                project_id=1,
                section_ids=['1', '2'],
                tator_url=TATOR_URL,
                media_list=media_list,
            )
            with pytest.raises(ValueError):
                processor.fetch_localizations()

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_fetch_localizations_batches_media_ids_by_50(self, fake_session):
        media_list = [{'id': i} for i in range(1, 121)]  # 120 media -> batches of 50, 50, 20

        with patch.object(TatorRestClient, 'get_localizations', return_value=[]) as mock_get_localizations:
            processor = TatorLocalizationProcessor(
                project_id=1,
                section_ids=['1'],
                tator_url=TATOR_URL,
                media_list=media_list,
            )
            processor.fetch_localizations()

        batches = [call.kwargs['media_ids'] for call in mock_get_localizations.call_args_list]
        assert [len(batch) for batch in batches] == [50, 50, 20]

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_media_id_map_uses_media_list_when_present(self, fake_session):
        media_list = [{'id': '10', 'name': 'a'}, {'id': 20, 'name': 'b'}]
        processor = TatorLocalizationProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
            media_list=media_list,
        )

        result = processor._get_media_id_map()

        assert result == {10: media_list[0], 20: media_list[1]}

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_media_id_map_fetches_from_rest_when_no_media_list(self, fake_session):
        fetched_media = [{'id': 5, 'name': 'x'}]

        with patch.object(TatorRestClient, 'get_medias_for_sections', return_value=fetched_media) as mock_get_medias:
            processor = TatorLocalizationProcessor(
                project_id=1,
                section_ids=['1', '2'],
                tator_url=TATOR_URL,
            )
            result = processor._get_media_id_map()

        mock_get_medias.assert_called_once_with(project_id=1, section_ids=[1, 2])
        assert result == {5: fetched_media[0]}

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_annotator_name_fetches_and_caches(self, fake_session):
        with patch.object(TatorRestClient, 'get_user', return_value={'first_name': 'Joe', 'last_name': 'Dirt'}) as mock_get_user:
            processor = TatorLocalizationProcessor(
                project_id=1,
                section_ids=['1'],
                tator_url=TATOR_URL,
            )
            first = processor._get_annotator_name(42)
            second = processor._get_annotator_name(42)

        assert first == 'Joe Dirt'
        assert second == 'Joe Dirt'
        assert mock_get_user.call_count == 1  # second call was served from the session cache
        assert fake_session['tator_usernames'] == {42: 'Joe Dirt'}

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_annotator_name_unknown_user(self, fake_session):
        with patch.object(TatorRestClient, 'get_user', return_value={}):  # no 'first_name' in the response
            processor = TatorLocalizationProcessor(
                project_id=1,
                section_ids=['1'],
                tator_url=TATOR_URL,
            )
            name = processor._get_annotator_name(99)

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
