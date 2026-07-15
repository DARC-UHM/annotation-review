from unittest.mock import patch

import pytest

from application.tator.tator_rest_client import TatorRestClient
from application.tator.tator_type import TatorLocalizationType

TATOR_URL = 'https://tator.url'
DARC_REVIEW_URL = 'https://darc.review.url'


def mock_get_section_by_id(_, section_id):
    return {'id': section_id, 'name': f'Section_{section_id}', 'path': f'Expedition1.Section{section_id}'}


def make_localization(*,
                      localization_id=1,
                      elemental_id='elemental-id',
                      version=1,
                      localization_type: int = TatorLocalizationType.DOT,
                      media=100,
                      frame=10,
                      created_by=1,
                      x=0.5,
                      y=0.5,
                      width=None,
                      height=None,
                      attributes=None):
    # only the fields process_records() actually reads
    return {
        'id': localization_id,
        'elemental_id': elemental_id,
        'version': version,
        'type': localization_type,
        'media': media,
        'frame': frame,
        'created_by': created_by,
        'x': x,
        'y': y,
        'width': width,
        'height': height,
        'attributes': attributes or {},
    }


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


@pytest.fixture
def stub_annotator():
    # yields the mock itself so tests can assert on it (via call_count) instead of patching get_user themselves
    with patch.object(
            TatorRestClient,
            'get_user',
            return_value={'first_name': 'Joe', 'last_name': 'Dirt'},
    ) as mock_get_user:
        yield mock_get_user


@pytest.fixture
def stub_worms_match():
    # most process_records() tests don't care about phylogeny resolution.
    # tests that need specific behavior should patch fetch_worms themselves instead of requesting this fixture.
    with patch('application.util.phylogeny_cache.PhylogenyCache.fetch_worms', return_value=True):
        yield
