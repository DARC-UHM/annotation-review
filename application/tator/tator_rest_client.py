import base64

import requests

from application.tator.tator_type import TatorStateType


class TatorRestClient:
    """
    Thin wrapper around the Tator REST API. Handles auth headers and URL construction.
    Use instead of raw requests calls to avoid repeating boilerplate.
    """

    def __init__(self, tator_url: str, token: str):
        self.base_url = tator_url
        self._headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {token}',
        }

    @staticmethod
    def login(tator_url: str, username: str, password: str) -> str:
        """Returns a Tator API token for the given credentials, or raises HTTPError on failure."""
        res = requests.post(
            url=f'{tator_url}/rest/Token',
            headers={'Content-Type': 'application/json'},
            json={'username': username, 'password': password, 'refresh': True},
        )
        res.raise_for_status()
        return res.json()['token']

    def get_localizations(self, project_id: int, section: str = None, media_id: list[int] = None) -> list:
        if media_id is not None:
            url = f'{self.base_url}/rest/Localizations/{project_id}?media_id={",".join(str(m) for m in media_id)}'
        elif section is not None:
            url = f'{self.base_url}/rest/Localizations/{project_id}?section={section}'
        else:
            raise ValueError('Must provide either section or media_id')
        res = requests.get(url=url, headers=self._headers)
        res.raise_for_status()
        return res.json()

    def get_section_by_id(self, section_id: str) -> dict:
        url = f'{self.base_url}/rest/Section/{section_id}'
        res = requests.get(url=url, headers=self._headers)
        res.raise_for_status()
        return res.json()

    def get_medias_for_section(self, project_id: int, section: str) -> list:
        url = f'{self.base_url}/rest/Medias/{project_id}?section={section}'
        res = requests.get(url=url, headers=self._headers)
        res.raise_for_status()
        return res.json()

    def get_media_by_id(self, media_id: str) -> dict:
        url = f'{self.base_url}/rest/Media/{media_id}'
        res = requests.get(url=url, headers=self._headers)
        res.raise_for_status()
        return res.json()

    def get_substrates_for_medias(self, project_id: int, transect_media: list[dict]) -> list[dict]:
        """Returns substrates grouped by media ID, sorted by timestamp."""
        states = self._get_states(project_id, [str(media['id']) for media in transect_media])
        grouped: dict[int, list] = {}
        fps_map = {media['id']: media['fps'] for media in transect_media}
        for state in states:
            if state['type'] == TatorStateType.SUBSTRATE:
                media_id = state['media'][0]
                grouped.setdefault(media_id, []).append(
                    {
                        **state['attributes'],
                        'timestamp': self._format_timestamp(state['frame'] / fps_map[media_id]) if media_id in fps_map else None,
                        'frame': state['frame'],
                    }
                )
        for entries in grouped.values():
            entries.sort(key=lambda entry: (entry['timestamp'] is None, entry['timestamp']))
        return [{'media_id': media_id, 'substrates': entries} for media_id, entries in grouped.items()]

    def _get_states(self, project_id: int, media_ids: list[str]):
        states_url = f'{self.base_url}/rest/States/{project_id}?media_id={",".join(media_ids)}'
        states_res = requests.get(url=states_url, headers=self._headers)
        states_res.raise_for_status()
        return states_res.json()

    def get_user(self, user_id: int) -> dict:
        url = f'{self.base_url}/rest/User/{user_id}'
        res = requests.get(url=url, headers=self._headers)
        res.raise_for_status()
        return res.json()

    def get_frame(self, media_id: int, frame: int = None, quality: int = None) -> bytes:
        url = f'{self.base_url}/rest/GetFrame/{media_id}'
        params = {}
        if frame is not None:
            params['frames'] = frame
        if quality is not None:
            params['quality'] = quality
        res = requests.get(url=url, headers=self._headers, params=params)
        res.raise_for_status()
        base64_image = base64.b64encode(res.content).decode('utf-8')
        return base64.b64decode(base64_image)

    def get_localization_graphic(self, localization_id: int) -> bytes:
        url = f'{self.base_url}/rest/LocalizationGraphic/{localization_id}'
        res = requests.get(url=url, headers=self._headers)
        res.raise_for_status()
        base64_image = base64.b64encode(res.content).decode('utf-8')
        return base64.b64decode(base64_image)

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        total = round(seconds)
        return f'{total // 60:02d}:{total % 60:02d}'
