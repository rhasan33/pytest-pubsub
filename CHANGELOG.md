# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.1] - 2026-08-05

### Added
- `py.typed` marker — the package now advertises inline type information to type checkers.

### Changed
- Migrated dev/CI tooling from pip+tox to uv; tested/supported Python versions now include 3.14.
- Enabled strict mypy checking across the package.

## [0.1.0] - 2026-08-05

Initial release.

### Added
- In-memory `PubSubBroker` tracking topics, subscriptions, and pending/in-flight messages, with
  `NotFound`/`AlreadyExists` exceptions mirroring `google.api_core.exceptions`.
- `MockTopic`, `MockSubscription`, `MockMessage`, and `MockPublishFuture` models.
- `MockPublisherClient` — topic CRUD and `publish`.
- `MockSubscriberClient` — subscription CRUD, synchronous `pull`, `acknowledge`,
  `modify_ack_deadline`, and a simplified `subscribe()` streaming-pull loop.
- Fan-out delivery to multiple subscriptions, nack/redelivery, and ordering-key preservation.
- pytest plugin (`pytest11` entry point) with `pubsub_broker`, `mock_publisher_client`,
  `mock_subscriber_client`, `pubsub_topic_factory`, and `pubsub_subscription_factory` fixtures.
- Pre-commit hooks (ruff, mypy) and a GitHub Actions CI workflow across Python 3.9–3.13.
