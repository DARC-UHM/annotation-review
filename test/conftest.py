import pytest
from application import app


@pytest.fixture
def app():
    # Create a test version of your Flask app
    app.config.update({'TESTING': True})
    yield app


@pytest.fixture
def client(app):
    # Create a test client using the Flask test client
    return app.test_client()
