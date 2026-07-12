from unittest.mock import patch

import pytest
from application import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config.update({'TESTING': True})
    yield app


@pytest.fixture
def client(app):
    # Create a test client using the Flask test client
    return app.test_client()


@pytest.fixture
def mock_phylogeny_cache():
    """
    PhylogenyCache reads/writes cache/phylogeny.json on the real filesystem. Without this, tests would read
    whatever a developer happens to have cached locally (making assertions non-deterministic and dependent on
    machine state) and would overwrite that real cache file with test data.
    """
    with patch('application.util.phylogeny_cache.PhylogenyCache.load', lambda self: setattr(self, 'data', {'Animalia': {}})), \
         patch('application.util.phylogeny_cache.PhylogenyCache.save', lambda self: None):
        yield
