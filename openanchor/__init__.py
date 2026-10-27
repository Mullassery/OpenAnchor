"""
OpenAnchor: LLM token-attribution middleware.

OpenAnchor provides observability, attribution, pattern detection, and
optimization intelligence for AI token consumption — plus real OpenTelemetry
span export (``openanchor.otel``) and real semantic caching backed by
actual embeddings + SQLite + cosine similarity (``openanchor.semantic_cache``,
``openanchor._mcp_tools``).

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
from .analytics import Analytics

# Analysis
from .attribution import AttributionModel

# Collection and storage
from .collector import TokenCollector
from .instrumentation import (
    InstrumentationUnavailable,
    OpenAnchorSpanProcessor,
    enable_auto_instrumentation,
)
from .models import (
    Attribution,
    OperationType,
    RequestPhase,
    SessionStats,
    TokenConsumption,
    TokenEvent,
)

# OKF cost governance
from .okf_cost_governance import (
    BudgetPolicy,
    CostAnomaly,
    OKFCostGovernance,
)

# OKF optimization tracking
from .okf_optimization_tracking import (
    OKFOptimizationTracking,
    OptimizationLeaderboard,
    OptimizationResult,
)

# OKF token profiles
from .okf_token_profiles import (
    OKFTokenProfileCatalog,
    TokenProfile,
    TokenProfileAnalyzer,
)

# Observability (OTEL) — see openanchor/otel.py
from .otel import configure_tracing, is_otel_available

# LLM providers — see openanchor/providers/llm.py
from .providers import (
    LLMProvider,
    LLMProviderRegistry,
    LLMResponse,
    OpenRouterProvider,
    default_provider,
    get_default_provider,
    set_default_provider,
)

# Semantic caching primitives — see openanchor/semantic_cache.py
from .semantic_cache import (
    EmbeddingProvider,
    HashingEmbeddingProvider,
    OllamaEmbeddingProvider,
    SemanticCacheStore,
)
from .storage import EventStore, SqliteEventStore

__version__ = "0.6.4"
__author__ = "Georgi Mammen Mullassery"
__license__ = "Apache-2.0"

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
    "OpenAnchorSpanProcessor",
    "enable_auto_instrumentation",
    "InstrumentationUnavailable",
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
    # Observability (OTEL)
    "configure_tracing",
    "is_otel_available",
    # Semantic caching
    "SemanticCacheStore",
    "EmbeddingProvider",
    "OllamaEmbeddingProvider",
    "HashingEmbeddingProvider",
    "SemanticCache",
    # LLM providers
    "LLMProvider",
    "LLMResponse",
    "OpenRouterProvider",
    "LLMProviderRegistry",
    "default_provider",
    "set_default_provider",
    "get_default_provider",
]

# MCP 2.0 Support (v0.1.3+)
from openanchor._mcp_connector import SemanticCache
