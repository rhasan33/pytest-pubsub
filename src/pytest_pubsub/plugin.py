"""pytest fixtures for pytest-pubsub.

Registered as a pytest plugin via the `pytest11` entry point, so these
fixtures are available in any test suite once the package is installed —
no explicit `pytest_plugins` import needed. The mock clients are never
monkeypatched into `google.cloud.pubsub_v1`; tests pass them explicitly
into the code under test.
"""

from __future__ import annotations

from typing import Callable

import pytest

from pytest_pubsub.publisher import MockPublisherClient
from pytest_pubsub.registry import PubSubBroker
from pytest_pubsub.subscriber import MockSubscriberClient
from pytest_pubsub.subscription import MockSubscription
from pytest_pubsub.topic import MockTopic


@pytest.fixture
def pubsub_broker() -> PubSubBroker:
    """A fresh, isolated in-memory broker for a single test."""
    return PubSubBroker()


@pytest.fixture
def mock_publisher_client(pubsub_broker: PubSubBroker) -> MockPublisherClient:
    """A MockPublisherClient bound to the test's pubsub_broker."""
    return MockPublisherClient(pubsub_broker)


@pytest.fixture
def mock_subscriber_client(pubsub_broker: PubSubBroker) -> MockSubscriberClient:
    """A MockSubscriberClient bound to the test's pubsub_broker."""
    return MockSubscriberClient(pubsub_broker)


@pytest.fixture
def pubsub_topic_factory(
    mock_publisher_client: MockPublisherClient,
) -> Callable[[str, str], MockTopic]:
    """Callable(project, topic) -> MockTopic; creates the topic in the broker."""

    def _create(project: str, topic: str) -> MockTopic:
        topic_path = mock_publisher_client.topic_path(project, topic)
        return mock_publisher_client.create_topic(name=topic_path)

    return _create


@pytest.fixture
def pubsub_subscription_factory(
    mock_subscriber_client: MockSubscriberClient,
) -> Callable[[str, str, str], MockSubscription]:
    """Callable(project, subscription, topic_path) -> MockSubscription."""

    def _create(project: str, subscription: str, topic_path: str) -> MockSubscription:
        sub_path = mock_subscriber_client.subscription_path(project, subscription)
        return mock_subscriber_client.create_subscription(name=sub_path, topic=topic_path)

    return _create
