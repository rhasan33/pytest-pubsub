import pytest

from pytest_pubsub.exceptions import AlreadyExists, NotFound
from pytest_pubsub.registry import PubSubBroker


@pytest.fixture
def broker() -> PubSubBroker:
    return PubSubBroker()


def test_create_and_list_topic(broker):
    broker.create_topic("t1")
    assert broker.list_topics() == ["t1"]
    assert broker.topic_exists("t1")


def test_create_topic_twice_raises(broker):
    broker.create_topic("t1")
    with pytest.raises(AlreadyExists):
        broker.create_topic("t1")


def test_create_subscription_requires_topic(broker):
    with pytest.raises(NotFound):
        broker.create_subscription("s1", topic="missing")


def test_create_and_list_subscription(broker):
    broker.create_topic("t1")
    broker.create_subscription("s1", topic="t1")
    assert broker.list_subscriptions("t1") == ["s1"]
    assert broker.subscription_exists("s1")


def test_delete_topic_cascades_to_subscriptions(broker):
    broker.create_topic("t1")
    broker.create_subscription("s1", topic="t1")
    broker.delete_topic("t1")
    assert not broker.topic_exists("t1")
    assert not broker.subscription_exists("s1")


def test_publish_pull_ack_roundtrip(broker):
    broker.create_topic("t1")
    broker.create_subscription("s1", topic="t1")

    message_id = broker.publish("t1", b"hello", attributes={"k": "v"})
    assert message_id

    received = broker.pull("s1", max_messages=1)
    assert len(received) == 1
    ack_id, message = received[0]
    assert message.data == b"hello"
    assert message.attributes == {"k": "v"}

    broker.acknowledge("s1", [ack_id])
    assert broker.pull("s1", max_messages=1) == []


def test_nack_redelivers_message(broker):
    broker.create_topic("t1")
    broker.create_subscription("s1", topic="t1")
    broker.publish("t1", b"hello")

    ack_id, _ = broker.pull("s1", max_messages=1)[0]
    broker.nack("s1", [ack_id])

    redelivered = broker.pull("s1", max_messages=1)
    assert len(redelivered) == 1
    assert redelivered[0][1].data == b"hello"


def test_publish_requires_existing_topic(broker):
    with pytest.raises(NotFound):
        broker.publish("missing", b"data")


def test_delete_subscription(broker):
    broker.create_topic("t1")
    broker.create_subscription("s1", topic="t1")
    broker.delete_subscription("s1")
    assert not broker.subscription_exists("s1")
    assert broker.list_subscriptions("t1") == []
