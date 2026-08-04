import pytest

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


def test_publish_fans_out_to_every_subscription(publisher, subscriber):
    topic_path = publisher.topic_path("proj", "events")
    publisher.create_topic(name=topic_path)

    sub_a = subscriber.subscription_path("proj", "sub-a")
    sub_b = subscriber.subscription_path("proj", "sub-b")
    subscriber.create_subscription(name=sub_a, topic=topic_path)
    subscriber.create_subscription(name=sub_b, topic=topic_path)

    publisher.publish(topic_path, b"broadcast")

    for sub_path in (sub_a, sub_b):
        received = subscriber.pull(subscription=sub_path, max_messages=1).received_messages
        assert len(received) == 1
        assert received[0].message.data == b"broadcast"


def test_each_subscription_gets_independent_copy(publisher, subscriber):
    topic_path = publisher.topic_path("proj", "events")
    publisher.create_topic(name=topic_path)
    sub_a = subscriber.subscription_path("proj", "sub-a")
    sub_b = subscriber.subscription_path("proj", "sub-b")
    subscriber.create_subscription(name=sub_a, topic=topic_path)
    subscriber.create_subscription(name=sub_b, topic=topic_path)

    publisher.publish(topic_path, b"broadcast")

    received_a = subscriber.pull(subscription=sub_a, max_messages=1).received_messages[0]
    subscriber.acknowledge(subscription=sub_a, ack_ids=[received_a.ack_id])

    # Acking on sub_a must not affect sub_b's independent copy of the message.
    received_b = subscriber.pull(subscription=sub_b, max_messages=1).received_messages
    assert len(received_b) == 1
    assert received_b[0].message.data == b"broadcast"


def test_nacked_message_is_redelivered_before_newer_ones(publisher, subscriber):
    topic_path = publisher.topic_path("proj", "events")
    publisher.create_topic(name=topic_path)
    sub_path = subscriber.subscription_path("proj", "sub")
    subscriber.create_subscription(name=sub_path, topic=topic_path)

    publisher.publish(topic_path, b"first")
    first = subscriber.pull(subscription=sub_path, max_messages=1).received_messages[0]
    first.message.nack()

    publisher.publish(topic_path, b"second")
    redelivered = subscriber.pull(subscription=sub_path, max_messages=2).received_messages
    assert [m.message.data for m in redelivered] == [b"first", b"second"]


def test_ordering_key_preserved_and_messages_delivered_in_publish_order(publisher, subscriber):
    topic_path = publisher.topic_path("proj", "events")
    publisher.create_topic(name=topic_path)
    sub_path = subscriber.subscription_path("proj", "sub")
    subscriber.create_subscription(name=sub_path, topic=topic_path)

    publisher.publish(topic_path, b"one", ordering_key="key-a")
    publisher.publish(topic_path, b"two", ordering_key="key-a")
    publisher.publish(topic_path, b"three", ordering_key="key-b")

    received = subscriber.pull(subscription=sub_path, max_messages=3).received_messages
    assert [m.message.data for m in received] == [b"one", b"two", b"three"]
    assert [m.message.ordering_key for m in received] == ["key-a", "key-a", "key-b"]
