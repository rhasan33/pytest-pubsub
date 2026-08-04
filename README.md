# pytest-pubsub

In-memory mock of Google Cloud Pub/Sub topics and subscriptions, for use in tests. No network
access, no credentials, no emulator process required. Compatible with Python 3.9+.

## Install

```bash
pip install pytest-pubsub
```

## How it works

Everything is backed by a single in-memory `PubSubBroker` that tracks topics, subscriptions,
and their pending/in-flight messages. Publishing to a topic fans the message out to every
subscription attached to it, matching real Pub/Sub delivery semantics. Nothing touches the
network — the broker is just plain Python data structures.

Errors mirror `google.api_core.exceptions`: operating on a topic or subscription that doesn't
exist raises `NotFound`; creating one that already exists raises `AlreadyExists`. Code written
against the real client's exception handling works unchanged against the mock.

## Publisher usage

`MockPublisherClient` implements the subset of `google.cloud.pubsub_v1.PublisherClient` used in
practice — `topic_path`, `create_topic`/`get_topic`/`delete_topic`/`list_topics`, and `publish`.
It's constructed with an explicit `PubSubBroker` and passed into your code via dependency
injection — nothing is monkeypatched globally:

```python
from pytest_pubsub.publisher import MockPublisherClient
from pytest_pubsub.registry import PubSubBroker

broker = PubSubBroker()
client = MockPublisherClient(broker)

topic_path = client.topic_path("my-project", "events")
client.create_topic(name=topic_path)

future = client.publish(topic_path, b"hello", source="test")
message_id = future.result()
```

## Status

Under active development. See below for design notes as functionality lands.
