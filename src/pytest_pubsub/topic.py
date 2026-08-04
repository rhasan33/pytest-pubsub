"""Lightweight stand-in for google.cloud.pubsub_v1.types.Topic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class MockTopic:
    name: str
    labels: Dict[str, str] = field(default_factory=dict)
