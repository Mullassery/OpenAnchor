"""
OpenAnchor: Token Consumption Intelligence Platform

OpenAnchor provides observability, attribution, pattern detection, and
optimization intelligence for AI token consumption.

Built on PyTokenCalc (token accounting foundation).

Quick Start:
    from openanchor import TokenCollector

    collector = TokenCollector()
    events = collector.collect_from_pytokencalc()
"""

__version__ = "0.1.0"
__author__ = "Georgi Mammen Mullassery"
__license__ = "MIT"

# Core API (will be populated as modules are implemented)
__all__ = [
    "TokenCollector",
    "TokenEvent",
    "AttributionModel",
    "PatternDetector",
]
