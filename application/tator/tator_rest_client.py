import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from application.tator.tator_type import TatorStateType

RETRYABLE_STATUS_CODES = frozenset({500, 502, 503, 504})
DEFAULT_TIMEOUT = (10, 30)  # (connect, read) seconds


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
        self._session = self._build_session()

    @staticmethod
    def _build_session() -> requests.Session:
        """Session that retries transient 5xx/connection/read errors with backoff."""
        session = requests.Session()
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            status=3,
            backoff_factor=1,
            status_forcelist=RETRYABLE_STATUS_CODES,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        return session

    @staticmethod
    def login(tator_url: str, username: str, password: str) -> str:
        """Returns a Tator API token for the given credentials, or raises HTTPError on failure."""
        res = TatorRestClient._build_session().post(
            url=f'{tator_url}/rest/Token',
            headers={'Content-Type': 'application/json'},
            json={'username': username, 'password': password, 'refresh': True},
            timeout=DEFAULT_TIMEOUT,
        )
        res.raise_for_status()
        return res.json()['token']

    def get_localizations(self, project_id: int, section_id: int = None, media_ids: list[int] = None) -> list:
        if media_ids is not None:
            url = f'{self.base_url}/rest/Localizations/{project_id}?media_id={",".join(str(m) for m in media_ids)}'
        elif section_id is not None:
            url = f'{self.base_url}/rest/Localizations/{project_id}?section={section_id}'
        else:
            raise ValueError('Must provide either section or media_id')
        res = self._session.get(url=url, headers=self._headers, timeout=DEFAULT_TIMEOUT)
        res.raise_for_status()
        return res.json()

    def get_section_by_id(self, section_id: int) -> dict:
        url = f'{self.base_url}/rest/Section/{section_id}'
        res = self._session.get(url=url, headers=self._headers, timeout=DEFAULT_TIMEOUT)
        res.raise_for_status()
        return res.json()

    def get_medias_for_sections(self, project_id: int, section_ids: list[int]) -> list:
        url = f'{self.base_url}/rest/Medias/{project_id}?multi_section={",".join([str(s) for s in section_ids])}'
        res = self._session.get(url=url, headers=self._headers, timeout=DEFAULT_TIMEOUT)
        res.raise_for_status()
        return res.json()

    def get_media_by_id(self, media_id: int) -> dict:
        url = f'{self.base_url}/rest/Media/{media_id}'
        res = self._session.get(url=url, headers=self._headers, timeout=DEFAULT_TIMEOUT)
        res.raise_for_status()
        return res.json()

    def get_substrates(self, project_id: int, section_ids: list[int] = None, media_list: list[dict] = None) -> list[dict]:
        """Returns substrates grouped by media ID, sorted by timestamp."""
        if section_ids is None and media_list is None:
            raise ValueError('Must provide either section_ids or media_ids')
        if media_list is None:
            media_list = self.get_medias_for_sections(project_id, section_ids)
        states = self._get_states(project_id, [media['id'] for media in media_list])
        grouped: dict[int, list] = {}
        fps_map = {media['id']: media['fps'] for media in media_list}
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

    def _get_states(self, project_id: int, media_ids: list[int]):
        states_url = f'{self.base_url}/rest/States/{project_id}?media_id={",".join([str(m) for m in media_ids])}'
        states_res = self._session.get(url=states_url, headers=self._headers, timeout=DEFAULT_TIMEOUT)
        states_res.raise_for_status()
        return states_res.json()

    def get_user(self, user_id: int) -> dict:
        url = f'{self.base_url}/rest/User/{user_id}'
        res = self._session.get(url=url, headers=self._headers, timeout=DEFAULT_TIMEOUT)
        res.raise_for_status()
        return res.json()

    def get_frame(self, media_id: int, frame: int = None, quality: int = None) -> bytes:
        url = f'{self.base_url}/rest/GetFrame/{media_id}'
        params = {}
        if frame is not None:
            params['frames'] = frame
        if quality is not None:
            params['quality'] = quality
        res = self._session.get(url=url, headers=self._headers, params=params, timeout=DEFAULT_TIMEOUT)
        res.raise_for_status()
        return res.content

    def get_localization_graphic(self, localization_id: int) -> bytes:
        url = f'{self.base_url}/rest/LocalizationGraphic/{localization_id}'
        res = self._session.get(url=url, headers=self._headers, timeout=DEFAULT_TIMEOUT)
        res.raise_for_status()
        return res.content

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        total = round(seconds)
        return f'{total // 60:02d}:{total % 60:02d}'
