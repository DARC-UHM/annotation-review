import base64

import requests


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
