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


def _localization_counts(project_id, section_ids, localization_type=None, attribute=None):
    if localization_type is None:
        return 100
    if attribute is None:
        return 4
    if attribute.endswith('20-49'):
        return 1
    if attribute.endswith('1000+'):
        return 1
    return 0


class TestQaqcChecklist:
    @patch('application.qaqc.tator.dropcam.routes.requests.get')
    @patch('application.qaqc.tator.dropcam.routes.TatorRestClient')
    def test_dropcam_checklist_skips_localizations_and_media(self, mock_rest_client, mock_get, client):
        rest = mock_rest_client.return_value
        rest.get_section_by_id.side_effect = lambda section_id: _section(section_id, 'dscm')
        rest.get_localization_count.side_effect = _localization_counts
        mock_get.return_value = _checklist_response()

        with client.session_transaction() as session:
            session['tator_token'] = 'token'
        response = client.get('/qaqc/tator/dropcam/checklist?project=26&section=10&section=11')

        assert response.status_code == 200
        assert b'Checks Complete' in response.data
        assert b'Total Localizations' in response.data
        assert b'Total Individuals' in response.data
        assert b'No records found' not in response.data
        assert b'const localizationCount = 100' in response.data
        assert b'const individualCount = 1039' in response.data
        assert b'deploy-10' in response.data
        rest.get_localization_count.assert_any_call(26, [10, 11])
        rest.get_localization_count.assert_any_call(26, [10, 11], localization_type=TatorLocalizationType.DOT)
        rest.get_localization_count.assert_any_call(
            26, [10, 11], localization_type=TatorLocalizationType.DOT, attribute='Categorical Abundance::20-49',
        )
        assert rest.get_localization_count.call_count == 6
        rest.get_localizations.assert_not_called()
        rest.get_medias_for_sections.assert_not_called()

    @patch('application.qaqc.tator.sub.routes.requests.get')
    @patch('application.qaqc.tator.sub.routes.TatorRestClient')
    def test_sub_checklist_skips_localizations_and_media(self, mock_rest_client, mock_get, client):
        rest = mock_rest_client.return_value
        rest.get_section_by_id.side_effect = lambda section_id: _section(section_id, 'exploratory')
        rest.get_localization_count.side_effect = _localization_counts
        mock_get.return_value = _checklist_response()

        with client.session_transaction() as session:
            session['tator_token'] = 'token'
        response = client.get('/qaqc/tator/sub/checklist?project=26&section=10&section=11')

        assert response.status_code == 200
        assert b'Checks Complete' in response.data
        assert b'Total Localizations' in response.data
        assert b'Total Individuals' in response.data
        assert b'No records found' not in response.data
        assert b'const localizationCount = 100' in response.data
        assert b'const individualCount = 1039' in response.data
        rest.get_localization_count.assert_any_call(26, [10, 11])
        rest.get_localization_count.assert_any_call(26, [10, 11], localization_type=TatorLocalizationType.SUB_DOT)
        assert rest.get_localization_count.call_count == 6
        rest.get_localizations.assert_not_called()
        rest.get_medias_for_sections.assert_not_called()
        rest.get_media_by_id.assert_not_called()

    @patch('application.qaqc.tator.sub.routes.requests.get')
    @patch('application.qaqc.tator.sub.routes.TatorRestClient')
    def test_sub_checklist_with_media_ids_does_not_download_section_media(self, mock_rest_client, mock_get, client):
        rest = mock_rest_client.return_value
        rest.get_section_by_id.side_effect = lambda section_id: _section(section_id, 'transect')
        rest.get_localization_count.side_effect = _localization_counts
        mock_get.return_value = _checklist_response()

        with client.session_transaction() as session:
            session['tator_token'] = 'token'
        response = client.get('/qaqc/tator/sub/checklist?project=26&section=10&media_id=9001&media_id=9002')

        assert response.status_code == 200
        assert b'const individualCount = 1039' in response.data
        rest.get_localization_count.assert_any_call(26, [10])
        rest.get_localization_count.assert_any_call(26, [10], localization_type=TatorLocalizationType.SUB_DOT)
        assert rest.get_localization_count.call_count == 6
        rest.get_localizations.assert_not_called()
        rest.get_medias_for_sections.assert_not_called()
        rest.get_media_by_id.assert_not_called()
