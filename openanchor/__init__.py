"""
OpenAnchor: Token Consumption Intelligence Platform

OpenAnchor provides observability, attribution, pattern detection, and
optimization intelligence for AI token consumption.

Built on PyTokenCalc (token accounting foundation).

Quick Start:
    from openanchor import TokenCollector, Analytics

    collector = TokenCollector()
    event = collector.capture_event(
        call_id="call_1",
        model="gpt-4",
        provider="openai",
        input_tokens=100,
        output_tokens=50
    )

    # Analyze
    from openanchor import AttributionModel
    attribution = AttributionModel(collector.store)
    breakdown = attribution.analyze_call("call_1")
"""

from .models import (
    TokenEvent,
    TokenConsumption,
    Attribution,
    SessionStats,
    OperationType,
    RequestPhase,
)
from .collector import TokenCollector
from .storage import EventStore, SqliteEventStore
from .attribution import AttributionModel
from .analytics import Analytics

__version__ = "0.1.0"
__author__ = "Georgi Mammen Mullassery"
__license__ = "MIT"

__all__ = [
    "TokenEvent",
    "TokenConsumption",
    "Attribution",
    "SessionStats",
    "OperationType",
    "RequestPhase",
    "TokenCollector",
    "EventStore",
    "SqliteEventStore",
    "AttributionModel",
    "Analytics",
]
