"""
Pytest configuration for API handler tests.
BaseHTTPRequestHandler.__init__ calls self.handle() which tries to read
a real HTTP request. Patch it to a no-op so tests can construct handlers
and call do_GET()/do_POST() directly.
"""
import pytest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler


@pytest.fixture(autouse=True)
def no_http_server():
    """Prevent handler __init__ from processing a real request."""
    with patch.object(BaseHTTPRequestHandler, 'handle', return_value=None):
        yield
