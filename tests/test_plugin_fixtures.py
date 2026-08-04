import pytest

from pytest_pubsub.publisher import MockPublisherClient
from pytest_pubsub.registry import PubSubBroker
from pytest_pubsub.subscriber import MockSubscriberClient


def test_broker_and_client_fixtures_are_wired_together(
    pubsub_broker, mock_publisher_client, mock_subscriber_client
):
    assert isinstance(pubsub_broker, PubSubBroker)
    assert isinstance(mock_publisher_client, MockPublisherClient)
    assert isinstance(mock_subscriber_client, MockSubscriberClient)
    assert mock_publisher_client.broker is pubsub_broker
    assert mock_subscriber_client.broker is pubsub_broker


def test_broker_fixture_is_fresh_per_test(pubsub_broker):
    assert pubsub_broker.list_topics() == []
    pubsub_broker.create_topic("t1")
    assert pubsub_broker.list_topics() == ["t1"]


def test_topic_and_subscription_factories(
    pubsub_topic_factory, pubsub_subscription_factory, mock_publisher_client
):
    topic = pubsub_topic_factory("proj", "events")
    sub = pubsub_subscription_factory("proj", "events-sub", topic.name)

    assert topic.name == "projects/proj/topics/events"
    assert sub.topic == topic.name
    assert sub.name == "projects/proj/subscriptions/events-sub"


def test_end_to_end_publish_pull_via_fixtures(
    pubsub_topic_factory, pubsub_subscription_factory, mock_publisher_client, mock_subscriber_client
):
    topic = pubsub_topic_factory("proj", "events")
    sub = pubsub_subscription_factory("proj", "events-sub", topic.name)

    mock_publisher_client.publish(topic.name, b"hello")
    response = mock_subscriber_client.pull(subscription=sub.name, max_messages=1)

    assert response.received_messages[0].message.data == b"hello"


def test_plugin_registers_via_entry_point(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        def test_uses_pubsub_fixtures(pubsub_broker, mock_publisher_client, mock_subscriber_client):
            topic_path = mock_publisher_client.topic_path("proj", "events")
            mock_publisher_client.create_topic(name=topic_path)
            assert pubsub_broker.topic_exists(topic_path)
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
