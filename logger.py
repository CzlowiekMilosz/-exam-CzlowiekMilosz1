import logging
from flask import request


def setup_logging(app):
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    if hasattr(app, '_logging_configured'):
        return
    @app.after_request
    def log_request(response):
        method = request.method
        path = request.path
        status = response.status_code
        client_ip = request.remote_addr
        log_message = f"method: {method}; path: {path}; status: {status}; client_ip: {client_ip}"
        logging.getLogger("app").info(log_message)
        return response
    app._logging_configured = True
