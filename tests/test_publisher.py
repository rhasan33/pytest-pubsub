import pytest

from pytest_pubsub.exceptions import NotFound
from pytest_pubsub.publisher import MockPublisherClient
from pytest_pubsub.registry import PubSubBroker


@pytest.fixture
def client() -> MockPublisherClient:
    return MockPublisherClient(PubSubBroker())


def test_topic_path_format(client):
    assert client.topic_path("proj", "events") == "projects/proj/topics/events"


def test_create_and_get_topic(client):
    topic_path = client.topic_path("proj", "events")
    created = client.create_topic(name=topic_path)
    assert created.name == topic_path
    assert client.get_topic(topic=topic_path).name == topic_path


def test_create_topic_via_request_dict(client):
    topic_path = client.topic_path("proj", "events")
    created = client.create_topic(request={"name": topic_path})
    assert created.name == topic_path


def test_list_topics(client):
    t1 = client.topic_path("proj", "a")
    t2 = client.topic_path("proj", "b")
    client.create_topic(name=t1)
    client.create_topic(name=t2)
    names = {t.name for t in client.list_topics()}
    assert names == {t1, t2}


def test_delete_topic(client):
    topic_path = client.topic_path("proj", "events")
    client.create_topic(name=topic_path)
    client.delete_topic(topic=topic_path)
    with pytest.raises(NotFound):
        client.get_topic(topic=topic_path)


def test_publish_returns_future_with_message_id(client):
    topic_path = client.topic_path("proj", "events")
    client.create_topic(name=topic_path)

    future = client.publish(topic_path, b"hello", source="test")
    message_id = future.result()
    assert message_id


def test_publish_rejects_non_bytes_data(client):
    topic_path = client.topic_path("proj", "events")
    client.create_topic(name=topic_path)
    with pytest.raises(TypeError):
        client.publish(topic_path, "not bytes")


def test_publish_missing_topic_raises(client):
    with pytest.raises(NotFound):
        client.publish("projects/proj/topics/missing", b"data")
