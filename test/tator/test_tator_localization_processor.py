from unittest.mock import MagicMock, patch

from application.tator.tator_localization_processor import TatorLocalizationProcessor
from application.tator.tator_rest_client import TatorRestClient

TATOR_URL = 'https://tator.url'
DARC_REVIEW_URL = 'https://darc.review.url'


def mock_get_section_by_id(self, section_id):
    return {'id': section_id, 'name': f'Section {section_id}', 'path': f'Expedition1.Section{section_id}'}


class TestTatorLocalizationProcessor:
    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_init(self):
        media_list = [{'id': 1, 'name': 'media1'}, {'id': 2, 'name': 'media2'}]
        # flask.session is a werkzeug LocalProxy; unittest.mock.patch() can't auto-create a MagicMock for it
        # outside of a request context, so we build the replacement ourselves and pass it via `new=`.
        mock_session = MagicMock()
        mock_session.__getitem__.return_value = 'fake-token'
        with patch('application.tator.tator_localization_processor.session', new=mock_session):
            localization_processor = TatorLocalizationProcessor(
                project_id=1,
                section_ids=['1', '2'],
                tator_url=TATOR_URL,
                darc_review_url=DARC_REVIEW_URL,
                media_list=media_list
            )
        assert localization_processor.project_id == 1
        assert localization_processor.tator_url == TATOR_URL
        assert localization_processor.darc_review_url == DARC_REVIEW_URL
        assert len(localization_processor.sections) == 2
        assert localization_processor.media_list == media_list
        mock_session.__getitem__.assert_called_once_with('tator_token')
