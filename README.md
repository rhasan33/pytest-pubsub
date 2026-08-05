# pytest-pubsub

[![CI](https://github.com/rhasan33/pytest-pubsub/actions/workflows/ci.yml/badge.svg)](https://github.com/rhasan33/pytest-pubsub/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pytest-pubsub.svg)](https://pypi.org/project/pytest-pubsub/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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

## Subscriber usage

`MockSubscriberClient` implements the subset of `google.cloud.pubsub_v1.SubscriberClient` used
in practice — `subscription_path`, `create_subscription`/`get_subscription`/
`delete_subscription`, synchronous `pull`, `acknowledge`, `modify_ack_deadline`, and a simplified
`subscribe()` for streaming-pull-style consumers:

```python
from pytest_pubsub.registry import PubSubBroker
from pytest_pubsub.publisher import MockPublisherClient
from pytest_pubsub.subscriber import MockSubscriberClient

broker = PubSubBroker()
publisher = MockPublisherClient(broker)
subscriber = MockSubscriberClient(broker)

topic_path = publisher.topic_path("my-project", "events")
publisher.create_topic(name=topic_path)

sub_path = subscriber.subscription_path("my-project", "events-sub")
subscriber.create_subscription(name=sub_path, topic=topic_path)

publisher.publish(topic_path, b"hello")

response = subscriber.pull(subscription=sub_path, max_messages=1)
message = response.received_messages[0].message
assert message.data == b"hello"
message.ack()
```

Or with a streaming-pull-style callback:

```python
def handle(message):
    print(message.data)
    message.ack()


future = subscriber.subscribe(sub_path, handle)
# ... later
future.cancel()
future.result(timeout=1)
```

## pytest fixtures

Installing the package registers a pytest plugin (via the `pytest11` entry point), so these
fixtures are available in any test suite with no extra configuration:

| Fixture | Description |
| --- | --- |
| `pubsub_broker` | Fresh, isolated `PubSubBroker` for the test |
| `mock_publisher_client` | `MockPublisherClient` bound to `pubsub_broker` |
| `mock_subscriber_client` | `MockSubscriberClient` bound to the same `pubsub_broker` |
| `pubsub_topic_factory` | `factory(project, topic) -> MockTopic`, creates the topic |
| `pubsub_subscription_factory` | `factory(project, subscription, topic_path) -> MockSubscription` |

No monkeypatching happens automatically. Your code under test should accept a client instance
(constructor injection, a factory function, etc.) so the fixture can be passed in explicitly:

```python
# app/publisher.py — code under test, accepts an injected client
def send_event(client, topic_path: str, payload: bytes):
    future = client.publish(topic_path, payload)
    return future.result()


# tests/test_publisher.py
def test_send_event(mock_publisher_client, mock_subscriber_client, pubsub_broker):
    topic_path = mock_publisher_client.topic_path("proj", "events")
    mock_publisher_client.create_topic(name=topic_path)

    sub_path = mock_subscriber_client.subscription_path("proj", "events-sub")
    mock_subscriber_client.create_subscription(name=sub_path, topic=topic_path)

    from app.publisher import send_event

    message_id = send_event(mock_publisher_client, topic_path, b"hello")
    assert message_id

    response = mock_subscriber_client.pull(subscription=sub_path, max_messages=1)
    assert response.received_messages[0].message.data == b"hello"
    mock_subscriber_client.acknowledge(
        subscription=sub_path,
        ack_ids=[response.received_messages[0].ack_id],
    )
```

## Limitations / non-goals

- **Client-level mock only.** There is no fake gRPC/HTTP server — this does not emulate the
  Pub/Sub emulator wire protocol, so it's not a drop-in for tests that talk to the emulator over
  the network. Code under test must accept a client instance instead of constructing
  `google.cloud.pubsub_v1.PublisherClient`/`SubscriberClient` directly.
- **No automatic ack-deadline expiry.** `pull`/`acknowledge` are synchronous and in-process, so
  messages never redeliver on their own after a deadline; use `message.nack()` or
  `modify_ack_deadline(..., ack_deadline_seconds=0)` to force redelivery in a test.
- **No IAM, retention policies, dead-lettering, or push subscriptions.**

## Running the tests

```bash
make install    # uv sync --all-extras
make test       # uv run pytest --cov=pytest_pubsub
```

Other Makefile targets:

```bash
make lint         # ruff check
make format       # ruff format
make format-check # ruff format --check
make typecheck    # mypy --strict
make check        # lint + format-check + typecheck + test
```

## Linting and type checking

```bash
make install
uv run pre-commit install   # runs ruff and mypy automatically on every commit
uv run pre-commit run --all-files
```

CI (`.github/workflows/ci.yml`) runs `make check` (`ruff check`, `ruff format --check`, `mypy
--strict`, and the test suite) across Python 3.9–3.14 on every pull request and on every push to
`main`.

## Contributing

Issues and pull requests are welcome. Please include tests for any behavior change — every
source change in this repo ships with its own tests in the same commit.

## License

MIT
