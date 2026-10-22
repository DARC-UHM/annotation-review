from unittest.mock import MagicMock, patch


def _checklist_response():
    response = MagicMock()
    response.__enter__.return_value = response
    response.status_code = 200
    response.json.return_value = {'names_accepted': 0}
    return response


def _section(section_id, folder):
    return {'id': section_id, 'name': f'deploy-{section_id}', 'path': f'Cruise.{folder}.{section_id}'}


class TestQaqcChecklist:
    @patch('application.qaqc.tator.dropcam.routes.requests.get')
    @patch('application.qaqc.tator.dropcam.routes.TatorRestClient')
    def test_dropcam_checklist_skips_localizations_and_media(self, mock_rest_client, mock_get, client):
        rest = mock_rest_client.return_value
        rest.get_section_by_id.side_effect = lambda section_id: _section(section_id, 'dscm')
        mock_get.return_value = _checklist_response()

        with client.session_transaction() as session:
            session['tator_token'] = 'token'
        response = client.get('/qaqc/tator/dropcam/checklist?project=26&section=10&section=11')

        assert response.status_code == 200
        assert b'Checks Complete' in response.data
        assert b'Total Localizations' not in response.data
        assert b'No records found' not in response.data
        assert b'deploy-10' in response.data
        rest.get_localizations.assert_not_called()
        rest.get_medias_for_sections.assert_not_called()

    @patch('application.qaqc.tator.sub.routes.requests.get')
    @patch('application.qaqc.tator.sub.routes.TatorRestClient')
    def test_sub_checklist_skips_localizations_and_media(self, mock_rest_client, mock_get, client):
        rest = mock_rest_client.return_value
        rest.get_section_by_id.side_effect = lambda section_id: _section(section_id, 'exploratory')
        mock_get.return_value = _checklist_response()

        with client.session_transaction() as session:
            session['tator_token'] = 'token'
        response = client.get('/qaqc/tator/sub/checklist?project=26&section=10&section=11')

        assert response.status_code == 200
        assert b'Checks Complete' in response.data
        assert b'Total Localizations' not in response.data
        assert b'No records found' not in response.data
        rest.get_localizations.assert_not_called()
        rest.get_medias_for_sections.assert_not_called()
        rest.get_media_by_id.assert_not_called()

    @patch('application.qaqc.tator.sub.routes.requests.get')
    @patch('application.qaqc.tator.sub.routes.TatorRestClient')
    def test_sub_checklist_with_media_ids_does_not_download_section_media(self, mock_rest_client, mock_get, client):
        rest = mock_rest_client.return_value
        rest.get_section_by_id.side_effect = lambda section_id: _section(section_id, 'transect')
        mock_get.return_value = _checklist_response()

        with client.session_transaction() as session:
            session['tator_token'] = 'token'
        response = client.get('/qaqc/tator/sub/checklist?project=26&section=10&media_id=9001&media_id=9002')

        assert response.status_code == 200
        rest.get_localizations.assert_not_called()
        rest.get_medias_for_sections.assert_not_called()
        rest.get_media_by_id.assert_not_called()
