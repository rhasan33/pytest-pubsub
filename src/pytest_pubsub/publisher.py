"""Mock of google.cloud.pubsub_v1.PublisherClient."""

from __future__ import annotations

from typing import Iterator, Optional

from pytest_pubsub.message import MockPublishFuture
from pytest_pubsub.registry import PubSubBroker
from pytest_pubsub.topic import MockTopic


class MockPublisherClient:
    """Drop-in replacement for PublisherClient, backed by a PubSubBroker.

    Only the subset of the real client used for topic management and
    publishing is implemented. Construct with an explicit broker and pass
    this client into the code under test (no monkeypatching).
    """

    def __init__(self, broker: Optional[PubSubBroker] = None) -> None:
        self.broker = broker if broker is not None else PubSubBroker()

    @staticmethod
    def topic_path(project: str, topic: str) -> str:
        return f"projects/{project}/topics/{topic}"

    def create_topic(
        self, request: Optional[dict] = None, *, name: Optional[str] = None
    ) -> MockTopic:
        topic_name = _extract(request, "name", name)
        self.broker.create_topic(topic_name)
        return self.broker.get_topic(topic_name)

    def delete_topic(self, request: Optional[dict] = None, *, topic: Optional[str] = None) -> None:
        topic_name = _extract(request, "topic", topic)
        self.broker.delete_topic(topic_name)

    def get_topic(
        self, request: Optional[dict] = None, *, topic: Optional[str] = None
    ) -> MockTopic:
        topic_name = _extract(request, "topic", topic)
        return self.broker.get_topic(topic_name)

    def list_topics(
        self, request: Optional[dict] = None, *, project: Optional[str] = None
    ) -> Iterator[MockTopic]:
        for name in self.broker.list_topics():
            yield self.broker.get_topic(name)

    def publish(
        self,
        topic: str,
        data: bytes,
        ordering_key: str = "",
        **attrs: str,
    ) -> MockPublishFuture:
        if not isinstance(data, bytes):
            raise TypeError("Data must be sent as bytes")
        message_id = self.broker.publish(topic, data, attributes=attrs, ordering_key=ordering_key)
        return MockPublishFuture(message_id)


def _extract(request: Optional[dict], key: str, explicit: Optional[str]) -> str:
    if explicit is not None:
        return explicit
    if request is not None and key in request:
        return request[key]
    raise TypeError(f"Missing required argument: {key}")
