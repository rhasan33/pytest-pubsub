"""Exceptions raised by the mock clients.

These subclass google.api_core.exceptions so that `except` blocks written
against the real google-cloud-pubsub client keep working unchanged when
pointed at the mock.
"""

from google.api_core.exceptions import AlreadyExists, NotFound

__all__ = ["AlreadyExists", "NotFound"]
