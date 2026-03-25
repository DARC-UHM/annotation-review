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
