import pytest

from pytest_pubsub.exceptions import NotFound
from pytest_pubsub.message import MockMessage, MockPublishFuture
from pytest_pubsub.registry import PubSubBroker
from pytest_pubsub.subscription import MockSubscription
from pytest_pubsub.topic import MockTopic


@pytest.fixture
def broker() -> PubSubBroker:
    return PubSubBroker()


def test_get_topic_returns_mock_topic(broker):
    broker.create_topic("t1")
    topic = broker.get_topic("t1")
    assert isinstance(topic, MockTopic)
    assert topic.name == "t1"


def test_get_topic_missing_raises(broker):
    with pytest.raises(NotFound):
        broker.get_topic("missing")


def test_get_subscription_returns_mock_subscription(broker):
    broker.create_topic("t1")
    broker.create_subscription("s1", topic="t1", ack_deadline_seconds=30)
    sub = broker.get_subscription("s1")
    assert isinstance(sub, MockSubscription)
    assert sub.name == "s1"
    assert sub.topic == "t1"
    assert sub.ack_deadline_seconds == 30


def test_mock_message_ack_invokes_callback():
    calls = []
    message = MockMessage(
        data=b"hi",
        message_id="1",
        ack_id="ack-1",
        _ack_fn=calls.append,
    )
    message.ack()
    assert calls == ["ack-1"]


def test_mock_message_nack_invokes_callback():
    calls = []
    message = MockMessage(
        data=b"hi",
        message_id="1",
        ack_id="ack-1",
        _nack_fn=calls.append,
    )
    message.nack()
    assert calls == ["ack-1"]


def test_mock_publish_future_result_is_synchronous():
    future = MockPublishFuture("msg-123")
    assert future.result() == "msg-123"
    assert future.done()
    assert not future.cancelled()
    assert future.cancel() is False
