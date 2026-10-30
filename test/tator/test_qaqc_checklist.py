from unittest.mock import MagicMock, patch

from application.tator.tator_type import TatorLocalizationType


def _checklist_response():
    response = MagicMock()
    response.__enter__.return_value = response
    response.status_code = 200
    response.json.return_value = {'names_accepted': 0}
    return response


def _section(section_id, folder):
    return {'id': section_id, 'name': f'deploy-{section_id}', 'path': f'Cruise.{folder}.{section_id}'}


def _sections_for(folder, *section_ids):
    return [_section(section_id, folder) for section_id in section_ids] + [_section(99, 'other')]


def _dots():
    return [
        {'attributes': {'Categorical Abundance': '1-19'}},
        {'attributes': {'Categorical Abundance': '--'}},
        {'attributes': {'Categorical Abundance': '20-49'}},
        {'attributes': {'Categorical Abundance': '1000+'}},
    ]


class TestQaqcChecklist:
    @patch('application.qaqc.tator.dropcam.routes.requests.get')
    @patch('application.qaqc.tator.dropcam.routes.TatorRestClient')
    def test_dropcam_checklist_skips_localizations_and_media(self, mock_rest_client, mock_get, client):
        rest = mock_rest_client.return_value
        rest.get_sections.return_value = _sections_for('dscm', 11, 10)
        rest.get_localization_count.return_value = 100
        rest.get_localizations.return_value = _dots()
        mock_get.return_value = _checklist_response()

        with client.session_transaction() as session:
            session['tator_token'] = 'token'
        response = client.get('/qaqc/tator/dropcam/checklist?project=26&section=10&section=11')

        assert response.status_code == 200
        assert b'Checks Complete' in response.data
        assert b'Total Localizations' in response.data
        assert b'Total Individuals' in response.data
        assert b'No localizations found for given dive' in response.data
        assert b'const localizationCount = 100' in response.data
        assert b'const individualCount = 1039' in response.data
        assert b'deploy-10' in response.data
        assert b'deploy-99' not in response.data
        assert b"['deploy-10', 'deploy-11']" in response.data
        rest.get_sections.assert_called_once_with(26)
        rest.get_section_by_id.assert_not_called()
        rest.get_localization_count.assert_called_once_with(26, [10, 11])
        rest.get_localizations.assert_called_once_with(26, section_ids=[10, 11], localization_type=TatorLocalizationType.DOT)
        rest.get_medias_for_sections.assert_not_called()

    @patch('application.qaqc.tator.sub.routes.requests.get')
    @patch('application.qaqc.tator.sub.routes.TatorRestClient')
    def test_sub_checklist_skips_localizations_and_media(self, mock_rest_client, mock_get, client):
        rest = mock_rest_client.return_value
        rest.get_sections.return_value = _sections_for('exploratory', 11, 10)
        rest.get_localization_count.return_value = 100
        rest.get_localizations.return_value = _dots()
        mock_get.return_value = _checklist_response()

        with client.session_transaction() as session:
            session['tator_token'] = 'token'
        response = client.get('/qaqc/tator/sub/checklist?project=26&section=10&section=11')

        assert response.status_code == 200
        assert b'Checks Complete' in response.data
        assert b'Total Localizations' in response.data
        assert b'Total Individuals' in response.data
        assert b'No localizations found for given transect' in response.data
        assert b'const localizationCount = 100' in response.data
        assert b'const individualCount = 1039' in response.data
        assert b'deploy-99' not in response.data
        assert b'(exploratory)' in response.data
        rest.get_sections.assert_called_once_with(26)
        rest.get_section_by_id.assert_not_called()
        rest.get_localization_count.assert_called_once_with(26, [10, 11])
        rest.get_localizations.assert_called_once_with(26, section_ids=[10, 11], localization_type=TatorLocalizationType.SUB_DOT)
        rest.get_medias_for_sections.assert_not_called()
        rest.get_media_by_id.assert_not_called()

    @patch('application.qaqc.tator.sub.routes.requests.get')
    @patch('application.qaqc.tator.sub.routes.TatorRestClient')
    def test_sub_checklist_with_media_ids_does_not_download_section_media(self, mock_rest_client, mock_get, client):
        rest = mock_rest_client.return_value
        rest.get_sections.return_value = _sections_for('transect', 10)
        rest.get_localization_count.return_value = 100
        rest.get_localizations.return_value = _dots()
        rest.get_media_by_id.side_effect = [
            {'id': 9001, 'name': 'clip-9001'},
            {'id': 9002, 'name': 'clip-9002'},
        ]
        mock_get.return_value = _checklist_response()

        with client.session_transaction() as session:
            session['tator_token'] = 'token'
        response = client.get('/qaqc/tator/sub/checklist?project=26&section=10&media_id=9001&media_id=9002')

        assert response.status_code == 200
        assert b'const individualCount = 1039' in response.data
        assert b"['clip-9001', 'clip-9002']" in response.data
        assert b'deploy-99' not in response.data
        rest.get_sections.assert_called_once_with(26)
        rest.get_section_by_id.assert_not_called()
        rest.get_localization_count.assert_called_once_with(26, media_ids=[9001, 9002])
        rest.get_localizations.assert_called_once_with(26, media_ids=[9001, 9002], localization_type=TatorLocalizationType.SUB_DOT)
        rest.get_media_by_id.assert_any_call(9001)
        rest.get_media_by_id.assert_any_call(9002)
        rest.get_medias_for_sections.assert_not_called()
