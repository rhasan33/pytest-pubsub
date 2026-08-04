import time

import pytest

from pytest_pubsub.exceptions import NotFound
from pytest_pubsub.publisher import MockPublisherClient
from pytest_pubsub.registry import PubSubBroker
from pytest_pubsub.subscriber import MockSubscriberClient


@pytest.fixture
def broker() -> PubSubBroker:
    return PubSubBroker()


@pytest.fixture
def publisher(broker) -> MockPublisherClient:
    return MockPublisherClient(broker)


@pytest.fixture
def subscriber(broker) -> MockSubscriberClient:
    return MockSubscriberClient(broker)


def test_subscription_path_format(subscriber):
    assert (
        subscriber.subscription_path("proj", "events-sub")
        == "projects/proj/subscriptions/events-sub"
    )


def test_create_subscription(publisher, subscriber):
    topic_path = publisher.topic_path("proj", "events")
    publisher.create_topic(name=topic_path)

    sub_path = subscriber.subscription_path("proj", "events-sub")
    created = subscriber.create_subscription(
        name=sub_path, topic=topic_path, ack_deadline_seconds=20
    )
    assert created.name == sub_path
    assert created.topic == topic_path
    assert created.ack_deadline_seconds == 20


def test_publish_pull_ack_via_clients(publisher, subscriber):
    topic_path = publisher.topic_path("proj", "events")
    publisher.create_topic(name=topic_path)
    sub_path = subscriber.subscription_path("proj", "events-sub")
    subscriber.create_subscription(name=sub_path, topic=topic_path)

    publisher.publish(topic_path, b"hello")

    response = subscriber.pull(subscription=sub_path, max_messages=1)
    assert len(response.received_messages) == 1
    received = response.received_messages[0]
    assert received.message.data == b"hello"

    subscriber.acknowledge(subscription=sub_path, ack_ids=[received.ack_id])
    assert subscriber.pull(subscription=sub_path, max_messages=1).received_messages == []


def test_message_ack_method_acknowledges(publisher, subscriber):
    topic_path = publisher.topic_path("proj", "events")
    publisher.create_topic(name=topic_path)
    sub_path = subscriber.subscription_path("proj", "events-sub")
    subscriber.create_subscription(name=sub_path, topic=topic_path)
    publisher.publish(topic_path, b"hello")

    received = subscriber.pull(subscription=sub_path, max_messages=1).received_messages[0]
    received.message.ack()

    assert subscriber.pull(subscription=sub_path, max_messages=1).received_messages == []


def test_message_nack_redelivers(publisher, subscriber):
    topic_path = publisher.topic_path("proj", "events")
    publisher.create_topic(name=topic_path)
    sub_path = subscriber.subscription_path("proj", "events-sub")
    subscriber.create_subscription(name=sub_path, topic=topic_path)
    publisher.publish(topic_path, b"hello")

    received = subscriber.pull(subscription=sub_path, max_messages=1).received_messages[0]
    received.message.nack()

    redelivered = subscriber.pull(subscription=sub_path, max_messages=1).received_messages
    assert len(redelivered) == 1
    assert redelivered[0].message.data == b"hello"


def test_delete_subscription(publisher, subscriber):
    topic_path = publisher.topic_path("proj", "events")
    publisher.create_topic(name=topic_path)
    sub_path = subscriber.subscription_path("proj", "events-sub")
    subscriber.create_subscription(name=sub_path, topic=topic_path)

    subscriber.delete_subscription(subscription=sub_path)
    with pytest.raises(NotFound):
        subscriber.get_subscription(subscription=sub_path)


def test_subscribe_streaming_pull_invokes_callback(publisher, subscriber):
    topic_path = publisher.topic_path("proj", "events")
    publisher.create_topic(name=topic_path)
    sub_path = subscriber.subscription_path("proj", "events-sub")
    subscriber.create_subscription(name=sub_path, topic=topic_path)

    received = []
    future = subscriber.subscribe(sub_path, received.append, poll_interval=0.01)
    try:
        publisher.publish(topic_path, b"hello")
        deadline = time.time() + 2
        while not received and time.time() < deadline:
            time.sleep(0.01)
    finally:
        future.cancel()
        future.result(timeout=1)

    assert len(received) == 1
    assert received[0].data == b"hello"
