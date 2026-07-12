import json
from unittest.mock import mock_open, patch

import pytest

from application.util.phylogeny_cache import CACHE_PATH, PhylogenyCache, WORMS_REST_URL
from test.data.vars_responses import pomacentridae
from test.data.worms_responses import clownfish, clownfish_tree


@pytest.fixture
def mock_open_file():
    with patch('builtins.open', mock_open()) as m:
        yield m


class MockResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data


def route_urls(routes: dict):
    def side_effect(*args, **kwargs):
        return routes.get(kwargs.get('url'), MockResponse(status_code=404))
    return side_effect


class TestPhylogenyCache:
    def test_load_existing_file(self, mock_open_file):
        cached = {'Pomacentridae': {'family': 'Pomacentridae'}}
        mock_open_file.return_value.read.return_value = json.dumps(cached)
        cache = PhylogenyCache()
        mock_open_file.assert_called_once_with(CACHE_PATH, 'r')
        assert cache.data == cached

    def test_load_missing_file_defaults(self, mock_open_file):
        mock_open_file.side_effect = FileNotFoundError
        cache = PhylogenyCache()
        assert cache.data == {'Animalia': {}}

    def test_save_writes_data(self, mock_open_file):
        cache = PhylogenyCache.__new__(PhylogenyCache)
        cache.data = {'Pomacentridae': {'family': 'Pomacentridae'}}
        cache.save()
        mock_open_file.assert_called_once_with(CACHE_PATH, 'w')
        written = ''.join(call.args[0] for call in mock_open_file().write.call_args_list)
        assert json.loads(written) == cache.data

    def test_save_creates_missing_cache_directory(self, mock_open_file):
        cache = PhylogenyCache.__new__(PhylogenyCache)
        cache.data = {'Pomacentridae': {'family': 'Pomacentridae'}}
        mock_open_file.side_effect = [FileNotFoundError, mock_open_file.return_value]
        with patch('os.makedirs') as mock_makedirs:
            cache.save()
        mock_makedirs.assert_called_once_with('cache')
        assert mock_open_file.call_count == 2

    @patch('requests.get')
    def test_fetch_vars_success(self, mock_get):
        mock_get.return_value = MockResponse(json_data=pomacentridae)
        cache = PhylogenyCache.__new__(PhylogenyCache)
        cache.data = {}
        no_match_records = set()

        cache.fetch_vars(
            concept_name='Pomacentridae',
            vars_kb_url='https://all.the.knowledge',
            no_match_records=no_match_records,
        )

        mock_get.assert_called_once_with(url='https://all.the.knowledge/phylogeny/up/Pomacentridae')
        assert cache.data['Pomacentridae'] == {
            'phylum': 'Chordata',
            'subphylum': 'Vertebrata',
            'superclass': 'Pisces',
            'class': 'Actinopterygii',
            'order': 'Perciformes',
            'family': 'Pomacentridae',
        }
        assert len(no_match_records) == 0

    @patch('requests.get')
    def test_fetch_vars_not_found_in_kb(self, mock_get):
        mock_get.return_value = MockResponse(json_data={})  # no 'children' - can't walk the tree
        cache = PhylogenyCache.__new__(PhylogenyCache)
        cache.data = {}
        no_match_records = set()

        cache.fetch_vars(
            concept_name='MadeUpConcept',
            vars_kb_url='https://all.the.knowledge',
            no_match_records=no_match_records,
        )

        assert cache.data == {}
        assert no_match_records == {'MadeUpConcept'}

    @patch('requests.get')
    def test_fetch_vars_http_error(self, mock_get):
        mock_get.return_value = MockResponse(status_code=404)
        cache = PhylogenyCache.__new__(PhylogenyCache)
        cache.data = {}

        cache.fetch_vars('Pomacentridae', 'https://all.the.knowledge', set())

        assert cache.data == {}

    @patch('requests.get')
    def test_fetch_worms_direct_match(self, mock_get):
        mock_get.side_effect = route_urls({
            f'{WORMS_REST_URL}/AphiaIDByName/Amphiprioninae?marine_only=true': MockResponse(json_data=714652),
            f'{WORMS_REST_URL}/AphiaClassificationByAphiaID/714652': MockResponse(json_data=clownfish_tree),
        })
        cache = PhylogenyCache.__new__(PhylogenyCache)
        cache.data = {}

        result = cache.fetch_worms('Amphiprioninae')

        assert result is True
        assert cache.data['Amphiprioninae'] == {
            'superdomain': 'Biota',
            'kingdom': 'Animalia',
            'phylum': 'Chordata',
            'subphylum': 'Vertebrata',
            'infraphylum': 'Gnathostomata',
            'parvphylum': 'Osteichthyes',
            'gigaclass': 'Actinopterygii',
            'superclass': 'Actinopteri',
            'class': 'Teleostei',
            'order': 'Ovalentaria incertae sedis',
            'family': 'Pomacentridae',
            'subfamily': 'Amphiprioninae',
            'aphia_id': 714652,
        }

    @patch('requests.get')
    def test_fetch_worms_ambiguous_name_falls_back_to_records_by_name(self, mock_get):
        mock_get.side_effect = route_urls({
            # more than one matching record
            f'{WORMS_REST_URL}/AphiaIDByName/Amphiprioninae?marine_only=true': MockResponse(json_data=-999),
            f'{WORMS_REST_URL}/AphiaRecordsByName/Amphiprioninae?like=false&marine_only=true&offset=1': MockResponse(json_data=[clownfish]),
            f'{WORMS_REST_URL}/AphiaClassificationByAphiaID/714652': MockResponse(json_data=clownfish_tree),
        })
        cache = PhylogenyCache.__new__(PhylogenyCache)
        cache.data = {}

        result = cache.fetch_worms('Amphiprioninae')

        assert result is True
        assert cache.data['Amphiprioninae']['aphia_id'] == 714652
        assert cache.data['Amphiprioninae']['family'] == 'Pomacentridae'

    @patch('requests.get')
    def test_fetch_worms_no_match_found(self, mock_get):
        mock_get.side_effect = route_urls({
            f'{WORMS_REST_URL}/AphiaIDByName/Fakeconcept?marine_only=true': MockResponse(json_data=-999),
            f'{WORMS_REST_URL}/AphiaRecordsByName/Fakeconcept?like=false&marine_only=true&offset=1': MockResponse(json_data=[]),
        })
        cache = PhylogenyCache.__new__(PhylogenyCache)
        cache.data = {}

        result = cache.fetch_worms('Fakeconcept')

        assert result is False
        assert cache.data == {}
