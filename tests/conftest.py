import pytest
from app import app as flask_app
from app import db


@pytest.fixture(scope='function', autouse=True)
def reset_app():
    """Reset the Flask app between tests to allow fresh setup_logging calls."""
    # Reset the logging configuration flag
    if hasattr(flask_app, '_logging_configured'):
        delattr(flask_app, '_logging_configured')
    
    # Reset request tracking
    flask_app._got_first_request = False
    
    yield
    
    # Cleanup after test
    if hasattr(flask_app, '_logging_configured'):
        delattr(flask_app, '_logging_configured')

