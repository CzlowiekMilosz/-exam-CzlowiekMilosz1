import pytest
from app import Book, app, db
from sqlalchemy import text

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


def test_sql_injection_search(client, requests_mock):
    with app.app_context():
        db.session.add(Book(ol_key="secret", title="Secret Data", author="Admin"))
        db.session.commit()

    requests_mock.get("https://openlibrary.org/search.json", json={"docs": []})

    malicious_query = "'; DROP TABLE book; --"

    resp = client.get("/search", query_string={"q": malicious_query})
    assert resp.status_code in (200, 302, 303)

    with app.app_context():
        assert Book.query.count() == 1
        assert Book.query.filter_by(ol_key="secret").first() is not None

    resp2 = client.get("/books")
    assert resp2.status_code == 200
    html2 = resp2.data.decode("utf-8")
    assert "Books" in html2


def test_search_results_handle_apostrophes_and_duplicates(client, requests_mock):
    mock_data = {
        "docs": [
            {"key": "key_oreilly", "title": "O'Reilly Media", "author_name": ["Author"], "first_publish_year": 2000}
        ]
    }
    requests_mock.get("https://openlibrary.org/search.json", json=mock_data)

    with app.app_context():
        db.session.add(Book(ol_key="key_oreilly", title="O'Reilly Media", author="Author", year=2000))
        db.session.commit()

    resp = client.get("/search", query_string={"q": "O'Reilly"})
    assert resp.status_code == 200


def test_sql_injection_on_search_does_not_drop_table(client, requests_mock):
    with app.app_context():
        db.session.add(Book(ol_key="safe_key", title="Safe Book", author="Author"))
        db.session.commit()

    requests_mock.get("https://openlibrary.org/search.json", json={"docs": []})

    malicious_query = "'; DROP TABLE book; --"
    resp = client.get("/search", query_string={"q": malicious_query})

    assert resp.status_code in (200, 302, 303)
    with app.app_context():
        count = Book.query.count()
        assert count == 1