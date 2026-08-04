"""Lightweight stand-in for google.cloud.pubsub_v1.types.Subscription."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MockSubscription:
    name: str
    topic: str
    ack_deadline_seconds: int = 10
