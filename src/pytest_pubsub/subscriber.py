"""Mock of google.cloud.pubsub_v1.SubscriberClient."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, List, Optional

from pytest_pubsub.message import MockMessage
from pytest_pubsub.registry import PubSubBroker
from pytest_pubsub.subscription import MockSubscription


@dataclass
class ReceivedMessage:
    ack_id: str
    message: MockMessage


@dataclass
class PullResponse:
    received_messages: List[ReceivedMessage]


class StreamingPullFuture:
    """Mimics google.cloud.pubsub_v1.subscriber.futures.StreamingPullFuture."""

    def __init__(self, thread: threading.Thread, stop_event: threading.Event) -> None:
        self._thread = thread
        self._stop_event = stop_event
        self._cancelled = False

    def cancel(self) -> bool:
        self._stop_event.set()
        self._cancelled = True
        return True

    def cancelled(self) -> bool:
        return self._cancelled

    def result(self, timeout: Optional[float] = None) -> None:
        self._thread.join(timeout=timeout)


class MockSubscriberClient:
    """Drop-in replacement for SubscriberClient, backed by a PubSubBroker.

    Only the subset of the real client used for subscription management,
    synchronous pull, and streaming pull is implemented. Construct with an
    explicit broker and pass this client into the code under test (no
    monkeypatching).
    """

    def __init__(self, broker: Optional[PubSubBroker] = None) -> None:
        self.broker = broker if broker is not None else PubSubBroker()

    @staticmethod
    def subscription_path(project: str, subscription: str) -> str:
        return f"projects/{project}/subscriptions/{subscription}"

    def create_subscription(
        self,
        request: Optional[dict] = None,
        *,
        name: Optional[str] = None,
        topic: Optional[str] = None,
        ack_deadline_seconds: int = 10,
    ) -> MockSubscription:
        sub_name = _extract(request, "name", name)
        topic_name = _extract(request, "topic", topic)
        self.broker.create_subscription(sub_name, topic_name, ack_deadline_seconds)
        return self.broker.get_subscription(sub_name)

    def delete_subscription(
        self, request: Optional[dict] = None, *, subscription: Optional[str] = None
    ) -> None:
        sub_name = _extract(request, "subscription", subscription)
        self.broker.delete_subscription(sub_name)

    def get_subscription(
        self, request: Optional[dict] = None, *, subscription: Optional[str] = None
    ) -> MockSubscription:
        sub_name = _extract(request, "subscription", subscription)
        return self.broker.get_subscription(sub_name)

    def pull(
        self,
        request: Optional[dict] = None,
        *,
        subscription: Optional[str] = None,
        max_messages: int = 1,
    ) -> PullResponse:
        sub_name = _extract(request, "subscription", subscription)
        received = self.broker.pull(sub_name, max_messages=max_messages)
        messages = [
            ReceivedMessage(
                ack_id=ack_id,
                message=MockMessage(
                    data=queued.data,
                    message_id=queued.message_id,
                    ack_id=ack_id,
                    attributes=queued.attributes,
                    ordering_key=queued.ordering_key,
                    _ack_fn=lambda aid: self.broker.acknowledge(sub_name, [aid]),
                    _nack_fn=lambda aid: self.broker.nack(sub_name, [aid]),
                ),
            )
            for ack_id, queued in received
        ]
        return PullResponse(received_messages=messages)

    def acknowledge(
        self,
        request: Optional[dict] = None,
        *,
        subscription: Optional[str] = None,
        ack_ids: Optional[List[str]] = None,
    ) -> None:
        sub_name = _extract(request, "subscription", subscription)
        ids = _extract(request, "ack_ids", ack_ids)
        self.broker.acknowledge(sub_name, ids)

    def modify_ack_deadline(
        self,
        request: Optional[dict] = None,
        *,
        subscription: Optional[str] = None,
        ack_ids: Optional[List[str]] = None,
        ack_deadline_seconds: int = 10,
    ) -> None:
        sub_name = _extract(request, "subscription", subscription)
        ids = _extract(request, "ack_ids", ack_ids)
        self.broker.modify_ack_deadline(sub_name, ids, ack_deadline_seconds)

    def subscribe(
        self,
        subscription: str,
        callback: Callable[[MockMessage], None],
        poll_interval: float = 0.05,
    ) -> StreamingPullFuture:
        """Runs `callback` for each message delivered to `subscription`.

        Simplified, synchronous polling loop on a background thread — enough
        to exercise streaming-pull-style consumer code in tests without
        emulating the real gRPC streaming protocol.
        """
        stop_event = threading.Event()

        def _run() -> None:
            while not stop_event.is_set():
                response = self.pull(subscription=subscription, max_messages=1)
                for received in response.received_messages:
                    callback(received.message)
                if not response.received_messages:
                    time.sleep(poll_interval)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return StreamingPullFuture(thread, stop_event)


def _extract(request: Optional[dict], key: str, explicit):
    if explicit is not None:
        return explicit
    if request is not None and key in request:
        return request[key]
    raise TypeError(f"Missing required argument: {key}")
