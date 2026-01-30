import pytest
from app import Book, app, db


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


def test_search_books_success(client, requests_mock):
    mock_data = {
        "docs": [
            {
                "key": "test_key_1",
                "title": "Test Book",
                "author_name": ["John Doe"],
                "first_publish_year": 2023,
            }
        ]
    }
    requests_mock.get("https://openlibrary.org/search.json", json=mock_data)

    response = client.get("/search?q=test")
    assert response.status_code == 200

    with app.app_context():
        assert Book.query.count() == 0

    html = response.data.decode("utf-8")
    assert "Test Book" in html
    assert "John Doe" in html
    assert 'action="/add"' in html


def test_search_limit_is_20(client, requests_mock):
    many_docs = [{"key": f"key_{i}", "title": f"Book {i}"} for i in range(50)]
    requests_mock.get("https://openlibrary.org/search.json", json={"docs": many_docs})

    resp = client.get("/search?q=many")
    assert resp.status_code == 200

    html = resp.data.decode("utf-8")
    assert "Book 0" in html
    assert "Book 19" in html
    assert "Book 20" not in html
    assert "Book 49" not in html


def test_api_error_handling_no_crash(client, requests_mock):
    requests_mock.get(
        "https://openlibrary.org/search.json",
        status_code=500,
        text="Internal Server Error",
    )

    resp = client.get("/search?q=python")
    assert resp.status_code == 200

    html = resp.data.decode("utf-8")
    assert "No results found." in html


def test_add_book_saves_to_db(client):
    resp = client.post(
        "/add",
        data={
            "ol_key": "test_key_1",
            "title": "Test Book",
            "author": "John Doe",
            "year": "2023",
        },
    )
    assert resp.status_code in (302, 303)

    with app.app_context():
        book = Book.query.filter_by(ol_key="test_key_1").first()
        assert book is not None
        assert book.title == "Test Book"
        assert book.author == "John Doe"
        assert book.year == 2023


