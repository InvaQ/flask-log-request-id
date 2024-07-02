# Import necessary libraries
import uuid
import logging
import flask
from flask import request, g, current_app, has_app_context, has_request_context

# Ensure ExecutedOutsideContext is properly defined
class ExecutedOutsideContext(Exception):
    pass

# Import internal modules
from .parser import auto_parser

# Initialize logger
logger = logging.getLogger(__name__)

def flask_ctx_get_request_id():
    """
    Get request id from flask's G object
    :return: The id or None if not found.
    """
    if not (has_request_context() or has_app_context()):
        logger.error("Attempted to fetch request ID outside of Flask context.")
        raise ExecutedOutsideContext("No Flask app or request context available.")

    # Simplified context fetching
    ctx = current_app._get_current_object() if has_app_context() else None

    if ctx is None:
        logger.error("Failed to fetch Flask application context.")
        raise ExecutedOutsideContext("Failed to fetch Flask application context.")

    g_object_attr = ctx.config.get('LOG_REQUEST_ID_G_OBJECT_ATTRIBUTE', 'log_request_id')
    return getattr(g, g_object_attr, None)

class RequestID:
    def __init__(self, app=None, request_id_parser=None, request_id_generator=None):
        self.app = app
        self._request_id_parser = request_id_parser or auto_parser
        self._request_id_generator = request_id_generator or (lambda: str(uuid.uuid4()))
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('LOG_REQUEST_ID_GENERATE_IF_NOT_FOUND', True)
        app.config.setdefault('LOG_REQUEST_ID_LOG_ALL_REQUESTS', False)
        app.config.setdefault('LOG_REQUEST_ID_G_OBJECT_ATTRIBUTE', 'log_request_id')

        @app.before_request
        def _persist_request_id():
            g_object_attr = app.config['LOG_REQUEST_ID_G_OBJECT_ATTRIBUTE']
            request_id = self._request_id_parser()
            if not request_id and app.config['LOG_REQUEST_ID_GENERATE_IF_NOT_FOUND']:
                request_id = self._request_id_generator()
            setattr(g, g_object_attr, request_id)

        if app.config['LOG_REQUEST_ID_LOG_ALL_REQUESTS']:
            app.after_request(self._log_http_event)

    @staticmethod
    def _log_http_event(response):
        if has_request_context():
            logger.info(f'{request.remote_addr} - - "{request.method} {request.path} {response.status_code}"')
        return response

# Initialize the request ID fetcher
class MultiContextRequestIdFetcher:
    def __init__(self):
        self.fetchers = []

    def register_fetcher(self, fetcher):
        self.fetchers.append(fetcher)

    def get_request_id(self):
        for fetcher in self.fetchers:
            try:
                request_id = fetcher()
                if request_id:
                    return request_id
            except Exception as e:
                logger.error(f"Error fetching request ID: {e}")
        return None

current_request_id = MultiContextRequestIdFetcher()
current_request_id.register_fetcher(flask_ctx_get_request_id)