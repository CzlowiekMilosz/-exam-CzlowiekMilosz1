import pytest
from app import Book, app, db
from unittest.mock import patch


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


def test_new_book_creation():
    book = Book(
        ol_key="OL12345W",
        title="The Great Gatsby",
        author="F. Scott Fitzgerald",
        year=1925,
    )
    assert book.ol_key == "OL12345W"
    assert book.author == "F. Scott Fitzgerald"
    assert book.year == 1925


def test_search_renders_results(client, requests_mock):
    mock_data = {
        "docs": [
            {
                "key": "k1",
                "title": "Book 1",
                "author_name": ["Author 1"],
                "first_publish_year": 2001,
            }
        ]
    }
    requests_mock.get("https://openlibrary.org/search.json", json=mock_data)

    resp = client.get("/search?q=test")
    assert resp.status_code == 200

    html = resp.data.decode("utf-8")
    assert "Book 1" in html


def test_add_persists_single_book(client):
    resp = client.post(
        "/add",
        data={
            "q": "test",
            "ol_key": "p1",
            "title": "Persistent Book",
            "author": "Author",
            "year": "2020",
        },
    )

    assert resp.status_code in (302, 303)

    with app.app_context():
        book = Book.query.filter_by(ol_key="p1").first()
        assert book is not None
        assert book.title == "Persistent Book"
        assert book.author == "Author"
        assert book.year == 2020


def test_add_duplicate_book_does_not_create_second_row(client):
    with app.app_context():
        db.session.add(
            Book(
                ol_key="dup1",
                title="Original",
                author="Author",
                year=2020,
            )
        )
        db.session.commit()

    client.post(
        "/add",
        data={
            "q": "test",
            "ol_key": "dup1",
            "title": "Original copy",
            "author": "Author",
            "year": "2020",
        },
    )

    with app.app_context():
        count = Book.query.filter_by(ol_key="dup1").count()
        assert count == 1


def test_delete_non_existent_book(client):
    response = client.post("/books/delete/999")

    assert response.status_code == 404
    assert response.get_json() == {"status": "error"}


def test_delete_book_success(client):
    with app.app_context():
        b = Book(ol_key="del_key", title="To Be Deleted", author="None")
        db.session.add(b)
        db.session.commit()
        book_id = b.id

    response = client.post(f"/books/delete/{book_id}")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}

    with app.app_context():
        assert Book.query.get(book_id) is None


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "db": "ok"}


def test_health_db_failure(client):
    with patch("app.db.session.execute", side_effect=Exception("DB Down")):
        response = client.get("/health")

        assert response.status_code == 500

        data = response.get_json()
        assert data["status"] == "error"
        assert data["db"] == "error"


