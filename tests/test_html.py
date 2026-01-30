import pytest
from app import app as flask_app
from app import db

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with flask_app.app_context():
        db.create_all()
        with flask_app.test_client() as client:
            yield client
        db.drop_all()


def test_books_inheritance(client):
    response = client.get("/books")
    html = response.data.decode('utf-8')

    assert response.status_code == 200
    assert "Books" in html
    assert "Library" in html

def test_bootstrap_connected(client):
    response = client.get("/")
    html = response.data.decode('utf-8')

    assert response.status_code == 200
    assert "bootstrap.min.css" in html
    assert "bootstrap.bundle.min.js" in html