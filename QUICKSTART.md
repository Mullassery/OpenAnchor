# OpenAnchor v0.1 Quick Start

**OpenAnchor** is a token intelligence layer that automatically captures, attributes, and analyzes LLM token consumption across 6 dimensions.

## 5-Minute Setup

### Installation

```bash
pip install openanchor
```

### Basic Usage

```python
from openanchor import TokenCollector, Analytics, AttributionModel
from openanchor.models import OperationType

# 1. Create collector
collector = TokenCollector()
collector.set_session("my_project")

# 2. Capture events
collector.capture_event(
    call_id="call_1",
    model="gpt-4",
    provider="openai",
    input_tokens=500,
    output_tokens=200,
    operation_type=OperationType.RETRIEVAL,
    quality_score=0.95
)

# 3. Analyze
analytics = Analytics(collector, AttributionModel(collector.store))
summary = analytics.get_summary("my_project")
print(f"Total tokens: {summary['total_tokens']}")
print(f"By operation: {summary['by_operation']}")
```

## LangChain Integration

```python
from openanchor.middleware.langchain import OpenAnchorMiddleware

# Create middleware
middleware = OpenAnchorMiddleware(project_name="my_rag_app")

# Capture calls
middleware.capture_llm_call(
    call_id="call_1",
    model="gpt-4",
    input_tokens=100,
    output_tokens=50,
    quality_score=0.92
)

# Get insights
print(middleware.get_summary())
print(middleware.get_recommendations())
```

## Core Concepts

### 6-Dimensional Attribution

Every token is attributed across 6 dimensions:

1. **WHEN** — Request or response phase
2. **WHERE** — Operation type (retrieval, reasoning, system prompt, etc.)
3. **HOW** — Sub-operation detail (GitHub read/write/search)
4. **WHICH** — Prompt template used
5. **SESSION/PHASE** — Temporal grouping
6. **WHY** — Patterns and recommendations (v0.2+)

### Operation Types

```python
from openanchor.models import OperationType

OperationType.SYSTEM_PROMPT    # System prompt tokens
OperationType.USER_INPUT       # User input tokens
OperationType.RETRIEVAL        # Retrieved context
OperationType.MODEL_REASONING  # Model reasoning tokens
OperationType.GITHUB_READ      # GitHub read operations
OperationType.GITHUB_WRITE     # GitHub write operations
OperationType.PDF_EXTRACTION   # PDF processing
```

### Request Phases

```python
from openanchor.models import RequestPhase

RequestPhase.REQUEST   # Input tokens (request to LLM)
RequestPhase.RESPONSE  # Output tokens (LLM response)
```

## Query APIs

### Session Statistics

```python
stats = analytics.get_session_stats("my_session")
print(f"Total tokens: {stats.total_tokens}")
print(f"Total calls: {stats.total_calls}")
print(f"Avg latency: {stats.avg_latency_ms}ms")
print(f"Avg quality: {stats.avg_quality_score}")
```

### Token Breakdown

```python
# By operation type
by_op = analytics.get_tokens_by_operation("my_session")
# → {'retrieval': 5000, 'reasoning': 1000, ...}

# By request/response phase
by_phase = analytics.get_tokens_by_phase("my_session")
# → {'request': 5500, 'response': 1000}

# By model
by_model = analytics.get_tokens_by_model("my_session")
# → {'gpt-4': 6000, 'gpt-3.5-turbo': 500}

# By prompt template
by_prompt = analytics.get_tokens_by_prompt_template("my_session")
# → {'rag_prompt': 4000, 'search_prompt': 2500}
```

### Efficiency Analysis

```python
# Rank prompts by efficiency (quality per token)
ranking = analytics.rank_prompts_by_efficiency("my_session")
# → [('efficient_prompt', 0.0012), ('verbose_prompt', 0.0008)]

# Get detailed prompt stats
stats = analytics.get_prompt_stats("my_session")
for prompt, data in stats.items():
    print(f"{prompt}: {data['efficiency_score']:.4f}")
```

### Problem Detection

```python
# Find high-token, low-quality calls
problems = analytics.get_problematic_calls(
    "my_session",
    min_tokens=5000,     # Consume at least 5K tokens
    max_quality=0.8      # But have quality < 80%
)
```

### Performance Analysis

```python
# Latency statistics
latency = analytics.get_latency_stats("my_session")
# → {'avg_ms': 1500, 'p95_ms': 2000, 'p99_ms': 2500}

# Quality statistics
quality = analytics.get_quality_stats("my_session")
# → {'avg': 0.92, 'min': 0.85, 'max': 0.98}
```

## Manual vs Automatic Capture

### Manual Capture (v0.1)

```python
middleware.capture_llm_call(
    call_id="call_1",
    model="gpt-4",
    input_tokens=100,
    output_tokens=50
)
```

### Automatic Capture (v0.2+)

```python
# Middleware will auto-intercept LLM calls
# Just use your chain normally
result = chain.invoke("query")
```

## Recommendations (v0.1)

Get optimization suggestions:

```python
recs = middleware.get_recommendations()
for rec in recs:
    print(f"Action: {rec['action']}")
    print(f"Reason: {rec['reason']}")
    print(f"Confidence: {rec['confidence']}")
```

Current recommendations detect:
- High overall token consumption
- Low-quality calls
- Operation type imbalance
- Inefficient prompts (v0.2+)
- Token growth trends (v0.2+)

## Storage Options

### In-Memory (v0.1)

```python
from openanchor import EventStore, TokenCollector

store = EventStore()  # All data in memory
collector = TokenCollector(store)
```

### SQLite (v0.1)

```python
from openanchor import SqliteEventStore, TokenCollector

store = SqliteEventStore("openanchor.db")  # Persists to disk
collector = TokenCollector(store)
```

### PostgreSQL (v1.0+)

Coming in v1.0 with multi-tenant support.

## Example Scripts

See `examples/` directory:

```bash
python examples/basic_usage.py       # Basic token tracking
```

More examples coming in v0.2 (LlamaIndex, LangSmith, OTEL).

## Roadmap

**v0.1** (✅ done)
- Core infrastructure
- 6D attribution
- Analytics APIs
- LangChain middleware
- 25 tests passing

**v0.2** (in progress)
- Pattern detection (anomalies, trends)
- Advanced recommendations
- LlamaIndex integration
- OpenTelemetry export

**v0.3** (planned)
- LangSmith bridge
- A/B testing framework
- Prompt comparison tools

**v1.0** (planned)
- PostgreSQL multi-tenant
- Production deployment
- Comprehensive docs
- 3+ example systems

## FAQ

**Q: Does this replace PyTokenCalc?**  
A: No. PyTokenCalc handles token counting. OpenAnchor adds intelligence on top (attribution, patterns, recommendations).

**Q: Can I use OpenAnchor without LangChain?**  
A: Yes! Use the manual capture API or create custom middleware.

**Q: Does this work with external APIs?**  
A: Only with systems you control where you can intercept both request and response.

**Q: When should I use v0.1 vs v1.0?**  
A: v0.1 is production-ready for single-tenant deployments. v1.0 adds multi-tenant support.

## Support

- GitHub issues: https://github.com/Mullassery/openanchor/issues
- Docs: See README.md for comprehensive guide
- Examples: See `examples/` directory

---

**Next Step:** Check out `examples/basic_usage.py` for a complete walkthrough!
