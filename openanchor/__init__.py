"""
OpenAnchor v0.1.3: Token Consumption Intelligence Platform

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

# Core models and data structures
from .models import (
    TokenEvent,
    TokenConsumption,
    Attribution,
    SessionStats,
    OperationType,
    RequestPhase,
)

# Collection and storage
from .collector import TokenCollector
from .storage import EventStore, SqliteEventStore

# Analysis
from .attribution import AttributionModel
from .analytics import Analytics

# OKF cost governance
from .okf_cost_governance import (
    CostAnomaly,
    BudgetPolicy,
    OKFCostGovernance,
)

# OKF token profiles
from .okf_token_profiles import (
    TokenProfile,
    OKFTokenProfileCatalog,
    TokenProfileAnalyzer,
)

# OKF optimization tracking
from .okf_optimization_tracking import (
    OptimizationResult,
    OKFOptimizationTracking,
    OptimizationLeaderboard,
)

__version__ = "0.1.4"
__author__ = "Georgi Mammen Mullassery"
__license__ = "Proprietary"

__all__ = [
    # Models
    "TokenEvent",
    "TokenConsumption",
    "Attribution",
    "SessionStats",
    "OperationType",
    "RequestPhase",
    # Collection/Storage
    "TokenCollector",
    "EventStore",
    "SqliteEventStore",
    # Analysis
    "AttributionModel",
    "Analytics",
    # OKF Cost Governance
    "CostAnomaly",
    "BudgetPolicy",
    "OKFCostGovernance",
    # OKF Token Profiles
    "TokenProfile",
    "OKFTokenProfileCatalog",
    "TokenProfileAnalyzer",
    # OKF Optimization
    "OptimizationResult",
    "OKFOptimizationTracking",
    "OptimizationLeaderboard",
]

# MCP 2.0 Support (v0.1.3+)
from openanchor._mcp_connector import SemanticCache
