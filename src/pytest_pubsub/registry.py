"""In-memory broker tracking topics, subscriptions, and their messages."""

from __future__ import annotations

import itertools
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Set, Tuple

from pytest_pubsub.exceptions import AlreadyExists, NotFound
from pytest_pubsub.subscription import MockSubscription
from pytest_pubsub.topic import MockTopic

_id_counter = itertools.count(1)


@dataclass
class _QueuedMessage:
    message_id: str
    data: bytes
    attributes: Dict[str, str]
    ordering_key: str = ""


@dataclass
class _SubscriptionState:
    name: str
    topic: str
    ack_deadline_seconds: int = 10
    pending: Deque[_QueuedMessage] = field(default_factory=deque)
    in_flight: Dict[str, _QueuedMessage] = field(default_factory=dict)


class PubSubBroker:
    """Holds all topics and subscriptions for a single test."""

    def __init__(self) -> None:
        self._topics: Dict[str, Set[str]] = {}
        self._subscriptions: Dict[str, _SubscriptionState] = {}

    # -- topics ---------------------------------------------------------

    def create_topic(self, name: str) -> None:
        if name in self._topics:
            raise AlreadyExists(f"Topic already exists: {name}")
        self._topics[name] = set()

    def delete_topic(self, name: str) -> None:
        self._require_topic(name)
        for sub_name in list(self._topics[name]):
            self._subscriptions.pop(sub_name, None)
        del self._topics[name]

    def list_topics(self) -> List[str]:
        return list(self._topics)

    def topic_exists(self, name: str) -> bool:
        return name in self._topics

    def get_topic(self, name: str) -> MockTopic:
        self._require_topic(name)
        return MockTopic(name=name)

    def _require_topic(self, name: str) -> None:
        if name not in self._topics:
            raise NotFound(f"Topic not found: {name}")

    # -- subscriptions ----------------------------------------------------

    def create_subscription(
        self, name: str, topic: str, ack_deadline_seconds: int = 10
    ) -> None:
        self._require_topic(topic)
        if name in self._subscriptions:
            raise AlreadyExists(f"Subscription already exists: {name}")
        self._subscriptions[name] = _SubscriptionState(
            name=name, topic=topic, ack_deadline_seconds=ack_deadline_seconds
        )
        self._topics[topic].add(name)

    def delete_subscription(self, name: str) -> None:
        state = self._require_subscription(name)
        self._topics.get(state.topic, set()).discard(name)
        del self._subscriptions[name]

    def list_subscriptions(self, topic: Optional[str] = None) -> List[str]:
        if topic is None:
            return list(self._subscriptions)
        self._require_topic(topic)
        return list(self._topics[topic])

    def subscription_exists(self, name: str) -> bool:
        return name in self._subscriptions

    def get_subscription(self, name: str) -> MockSubscription:
        state = self._require_subscription(name)
        return MockSubscription(
            name=state.name,
            topic=state.topic,
            ack_deadline_seconds=state.ack_deadline_seconds,
        )

    def _require_subscription(self, name: str) -> _SubscriptionState:
        if name not in self._subscriptions:
            raise NotFound(f"Subscription not found: {name}")
        return self._subscriptions[name]

    # -- publish / pull / ack --------------------------------------------

    def publish(
        self,
        topic: str,
        data: bytes,
        attributes: Optional[Dict[str, str]] = None,
        ordering_key: str = "",
    ) -> str:
        self._require_topic(topic)
        message_id = str(next(_id_counter))
        for sub_name in self._topics[topic]:
            queued = _QueuedMessage(
                message_id=message_id,
                data=data,
                attributes=dict(attributes or {}),
                ordering_key=ordering_key,
            )
            self._subscriptions[sub_name].pending.append(queued)
        return message_id

    def pull(self, subscription: str, max_messages: int = 1) -> List[Tuple[str, _QueuedMessage]]:
        state = self._require_subscription(subscription)
        received = []
        for _ in range(max_messages):
            if not state.pending:
                break
            queued = state.pending.popleft()
            ack_id = uuid.uuid4().hex
            state.in_flight[ack_id] = queued
            received.append((ack_id, queued))
        return received

    def acknowledge(self, subscription: str, ack_ids: List[str]) -> None:
        state = self._require_subscription(subscription)
        for ack_id in ack_ids:
            state.in_flight.pop(ack_id, None)

    def nack(self, subscription: str, ack_ids: List[str]) -> None:
        state = self._require_subscription(subscription)
        for ack_id in ack_ids:
            queued = state.in_flight.pop(ack_id, None)
            if queued is not None:
                state.pending.appendleft(queued)

    def modify_ack_deadline(
        self, subscription: str, ack_ids: List[str], ack_deadline_seconds: int
    ) -> None:
        # In-memory mock resolves acks synchronously, so deadlines never expire
        # on their own; a deadline of 0 is treated the same as a nack.
        state = self._require_subscription(subscription)
        if ack_deadline_seconds == 0:
            self.nack(subscription, ack_ids)
        else:
            state.ack_deadline_seconds = ack_deadline_seconds
