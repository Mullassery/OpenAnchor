"""
OpenAnchor v0.2.0: Token Consumption Intelligence Platform

OpenAnchor provides observability, attribution, pattern detection, and
optimization intelligence for AI token consumption.

Built on PyTokenCalc (token accounting foundation).

Phase 1 Features (v0.1):
- Token collection and attribution
- Cost governance and anomaly detection
- Token profiles and catalogs

Phase 2 Features (v0.2):
- Semantic caching for query deduplication
- 6D Attribution analysis (tokens, latency, cost, quality, model, operation)
- Advanced optimization recommendations

Quick Start:
    from openanchor import TokenCollector, Analytics, SemanticCache, Attribution6DAnalyzer

    # Token collection
    collector = TokenCollector()
    event = collector.capture_event(
        call_id="call_1",
        model="gpt-4",
        provider="openai",
        input_tokens=100,
        output_tokens=50
    )

    # Semantic caching
    cache = SemanticCache()
    cache.put("What is AI?", "AI is artificial intelligence...")

    # 6D Attribution
    analyzer = Attribution6DAnalyzer()
    summary = analyzer.get_summary()
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

# Phase 2: Semantic Caching & 6D Attribution (v0.2+)
from .semantic_cache import (
    SemanticCache as SemanticCacheImpl,
    CachedEntry,
    CacheOptimizer,
)
from .attribution_6d import (
    Attribution6D,
    Attribution6DAnalyzer,
    Quality,
)

__version__ = "0.2.0"
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
    # Phase 2: Semantic Caching
    "SemanticCacheImpl",
    "CachedEntry",
    "CacheOptimizer",
    # Phase 2: 6D Attribution
    "Attribution6D",
    "Attribution6DAnalyzer",
    "Quality",
]

# MCP 2.0 Support (v0.1.3+)
from openanchor._mcp_connector import SemanticCache
