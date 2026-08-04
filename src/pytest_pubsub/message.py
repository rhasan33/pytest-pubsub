"""Stand-ins for the real client's Message and publish-result Future."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional


@dataclass
class MockMessage:
    """Mimics google.cloud.pubsub_v1.subscriber.message.Message."""

    data: bytes
    message_id: str
    ack_id: str
    attributes: Dict[str, str] = field(default_factory=dict)
    ordering_key: str = ""
    publish_time: float = field(default_factory=time.time)
    _ack_fn: Optional[Callable[[str], None]] = field(default=None, repr=False)
    _nack_fn: Optional[Callable[[str], None]] = field(default=None, repr=False)

    def ack(self) -> None:
        if self._ack_fn is not None:
            self._ack_fn(self.ack_id)

    def nack(self) -> None:
        if self._nack_fn is not None:
            self._nack_fn(self.ack_id)


class MockPublishFuture:
    """Mimics google.cloud.pubsub_v1.publisher.futures.Future.

    Publishing in the mock is synchronous, so the result is always available
    immediately; this only exists to match the real client's `.result()`
    interface.
    """

    def __init__(self, message_id: str) -> None:
        self._message_id = message_id

    def result(self, timeout: Optional[float] = None) -> str:
        return self._message_id

    def cancel(self) -> bool:
        return False

    def cancelled(self) -> bool:
        return False

    def done(self) -> bool:
        return True
