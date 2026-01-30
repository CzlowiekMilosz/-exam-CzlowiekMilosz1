import logging
import pytest
from app import app as flask_app
from logger import setup_logging


@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def test_setup_logging_levels(app):
    setup_logging(app)
    assert logging.getLogger("werkzeug").level == logging.WARNING


def test_request_logging(client, caplog):
    with caplog.at_level(logging.INFO):
        response = client.get("/health")
        assert response.status_code == 200

        log_records = [rec.message for rec in caplog.records if "method: GET" in rec.message]

        assert len(log_records) > 0
        assert "path: /health" in log_records[0]
        assert "status: 200" in log_records[0]
        assert "client_ip:" in log_records[0]
        assert log_records[0].count(";") == 3


def test_log_request_on_404(client, caplog):
    with caplog.at_level(logging.INFO):
        client.get("/non-existent-page")

        log_records = [rec.message for rec in caplog.records if "status: 404" in rec.message]
        assert len(log_records) > 0
        assert "path: /non-existent-page" in log_records[0]