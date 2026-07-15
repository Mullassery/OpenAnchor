# CLAUDE.md — OpenAnchor Developer Guidelines

**READ FIRST:** [VISION.md](./VISION.md) (middleware observability platform) and [ROADMAP.md](./ROADMAP.md) (16-week implementation)

**CORE ARCHITECTURE:** Middleware-based LLM observability (like Helicone), focused on token intelligence and optimization.

---

## Project Overview

OpenAnchor is a middleware platform that intercepts LLM calls (request + response), enriches data in PyTokenCalc's database, analyzes token consumption, and provides optimization recommendations.

**What it does:**
- Intercepts both incoming prompts and outgoing responses
- Records tokens, latency, and metadata
- Stores everything in a database
- Analyzes token attribution (6 dimensions)
- Detects patterns automatically
- Generates optimization recommendations
- Streams insights via OTEL

**What it does NOT:**
- Manage its own database (uses bundled PyTokenCalc's database)
- Create or initialize database (bundled PyTokenCalc does that)
- Calculate costs (tokens only; users apply their pricing)
- Automatically optimize code (recommends; users implement)
- Visualize dashboards (OTEL exports to Grafana/Datadog)

**Core dependency:** PyTokenCalc (bundled automatically with OpenAnchor, REQUIRED)

**Deployment model:** 
- `pip install openanchor` → Includes PyTokenCalc automatically as a dependency
- PyTokenCalc handles database creation and token counting
- OpenAnchor adds analysis tables to the same database
- No separate PyTokenCalc installation or configuration needed
- OpenAnchor cannot be used without PyTokenCalc
- PyTokenCalc can be used alone without OpenAnchor

---

## Repository Structure

```
openanchor/
├── openanchor/
│   ├── __init__.py                  # Public API
│   ├── core/
│   │   ├── middleware.py            # Abstract middleware interface
│   │   ├── events.py                # Event/data types
│   │   └── database.py              # Database client
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── base.py                  # Base middleware class
│   │   ├── langchain.py             # LangChain integration
│   │   ├── llamaindex.py            # LlamaIndex integration
│   │   └── proxy.py                 # Raw API proxy mode
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── attribution.py           # 6D token attribution
│   │   ├── patterns.py              # Pattern detection
│   │   ├── anomalies.py             # Anomaly detection
│   │   ├── trends.py                # Trend analysis
│   │   ├── efficiency.py            # Prompt efficiency
│   │   └── categorization.py        # Prompt categorization
│   ├── recommendations/
│   │   ├── __init__.py
│   │   ├── engine.py                # Recommendation generation
│   │   ├── detectors/               # Opportunity detectors
│   │   └── estimators/              # Savings estimators
│   ├── query/
│   │   ├── __init__.py
│   │   ├── client.py                # Database query client
│   │   ├── builders.py              # Query builders
│   │   └── results.py               # Result types
│   ├── export/
│   │   ├── __init__.py
│   │   ├── otel.py                  # OTEL export
│   │   ├── grafana.py               # Grafana templates
│   │   └── json.py                  # JSON export
│   └── storage/
│       ├── __init__.py
│       ├── schema.py                # Table definitions (for PyTokenCalc's DB)
│       └── migrations.py            # Create tables in PyTokenCalc's DB
├── tests/
│   ├── test_middleware.py
│   ├── test_attribution.py
│   ├── test_patterns.py
│   ├── test_recommendations.py
│   ├── test_query.py
│   └── test_integration.py
├── examples/
│   ├── langchain_example.py
│   ├── llamaindex_example.py
│   ├── raw_proxy_example.py
│   └── analysis_example.py
├── docs/
│   ├── VISION.md                    # Product vision
│   ├── ROADMAP.md                   # Implementation plan
│   ├── ARCHITECTURE.md              # Architecture overview
│   └── API.md                       # API reference
├── docker/
│   ├── database.yml                 # Database setup
│   └── dev-compose.yml              # Local dev environment
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

---

## Key Concepts

### Middleware Architecture

OpenAnchor sits between application and LLM provider, working WITH PyTokenCalc:

```
Application Code
    ↓
OpenAnchor Middleware (INTERCEPTS)
    ├─ Capture incoming request
    ├─ Proxy to LLM provider
    ├─ Capture outgoing response
    ├─ Call PyTokenCalc for accurate counts
    └─ Store enrichments in PyTokenCalc's DB
    ↓
PyTokenCalc (Token Accounting)
    ├─ Count tokens (via API, cache, or reconciliation)
    ├─ Store raw token_events
    └─ Provide counts to OpenAnchor
    ↓
Shared Database (PyTokenCalc's database)
├─ PyTokenCalc Tables:
│  └─ token_events (raw tokens, owned by PyTokenCalc)
├─ OpenAnchor Tables (same database, owned by OpenAnchor):
│  ├─ token_attribution
│  ├─ pattern_detections
│  ├─ recommendations
│  └─ ... (enrichments)
    ↓
Query APIs (Python)
    ├─ Direct database queries
    ├─ Pattern analysis
    └─ Recommendation queries
    ↓
OTEL Export (observability)
    ├─ Metrics stream
    └─ Visualization in Grafana/etc
```

**Key:** OpenAnchor does NOT manage the database. It reads from PyTokenCalc's tables and writes its own enrichment tables to the same database.

### Token Events

Each LLM call generates an event:

```python
TokenEvent = {
  timestamp: "2026-07-15T10:00:00Z",
  request: {
    prompt: str,
    model: str,
    provider: str,
    metadata: dict
  },
  response: {
    text: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
    ttft_ms: int,
    quality_score: float  # optional user feedback
  }
}
```

### 6-Dimensional Attribution

Breaking down WHERE tokens went:

```
WHEN: Request (5000) vs Response (450) phases
WHERE: System (500), User (2000), Retrieval (1500), Overhead (1000)
HOW: Retrieval detail - top-5 docs (800), search overhead (700)
WHICH: Prompt "rag_analyzer_v2" (vs v1: 6100 tokens)
SESSION/PHASE: "project_q3" phase 2 (600K total)
WHY: Retrieval growing 15%/week; recommendation: improve ranking
```

### Prompt Categorization

Automatically categorizes prompts:

```
Categories:
- code_review: Analyzing code
- summarization: Condensing text
- classification: Categorizing content
- reasoning: Complex reasoning
- retrieval: RAG queries
- creative: Creative writing
- analysis: Data analysis
- planning: Agent planning
```

---

## Development Workflow

### Add Middleware Integration

```python
# openanchor/middleware/your_framework.py

from openanchor.middleware.base import BaseMiddleware

class YourFrameworkMiddleware(BaseMiddleware):
    def intercept_request(self, request):
        """Intercept before LLM call."""
        return {
            "prompt": request.prompt,
            "model": request.model,
            "metadata": request.metadata
        }
    
    def intercept_response(self, response):
        """Intercept after LLM call."""
        return {
            "text": response.text,
            "tokens": response.usage,
            "latency_ms": response.latency
        }
```

### Add Pattern Detector

```python
# openanchor/analysis/patterns.py

class CustomPatternDetector:
    def detect(self, events: List[TokenEvent]) -> List[Pattern]:
        """Detect specific pattern."""
        patterns = []
        
        # Your detection logic
        if condition(events):
            patterns.append(Pattern(
                type="custom_pattern",
                description="What changed",
                severity="high"
            ))
        
        return patterns
```

### Add Query Helper

```python
# openanchor/query/builders.py

class CustomQueryBuilder:
    def get_tokens_for_category(self, category: str, start_date, end_date):
        """Query tokens by prompt category."""
        query = f"""
        SELECT SUM(input_tokens + output_tokens) as total_tokens
        FROM token_events
        WHERE prompt_category = '{category}'
          AND timestamp >= '{start_date}'
          AND timestamp < '{end_date}'
        """
        return self.client.execute(query)
```

---

## Testing Requirements

### Unit Tests (80%+ coverage per module)

```python
def test_middleware_captures_request():
    """Middleware must capture incoming request."""
    middleware = YourMiddleware()
    request = create_test_request()
    captured = middleware.intercept_request(request)
    assert captured["prompt"] == request.prompt

def test_attribution_sums_to_total():
    """Attribution breakdown must sum to total tokens."""
    event = create_test_event(total_tokens=1000)
    attribution = attribute(event)
    assert sum(attribution.values()) == 1000

def test_anomaly_detection():
    """Detect spikes >2σ from baseline."""
    baseline = [1000] * 10
    spike = 3000
    assert detector.is_anomaly(spike, baseline)
```

### Integration Tests

- Middleware captures full request/response
- Attribution breaks down tokens correctly
- Database storage and retrieval
- Query builders work correctly
- OTEL export formats correctly

### Example Scripts

All major features should have runnable examples:

```bash
python examples/langchain_example.py
python examples/llamaindex_example.py
python examples/raw_proxy_example.py
```

---

## Scope Discipline

### ✅ DO

**Middleware & Interception:**
- Improve middleware accuracy
- Add framework integrations (FastAPI, aiohttp, etc)
- Better latency measurement
- Metadata extraction

**Analysis:**
- Add new pattern detectors
- Improve attribution accuracy
- Better categorization
- New anomaly detection types

**Recommendations:**
- New optimization types
- Better savings estimation
- Priority ranking improvements

**Query & Export:**
- More query helpers
- OTEL enhancements
- Grafana template improvements

### ❌ DON'T

**Scope Boundaries (STRICT):**
- ❌ Cost calculation (PyTokenCalc responsibility)
- ❌ Automatic code optimization (user's responsibility)
- ❌ Model selection (frameworks/users decide)
- ❌ Dashboard/UI (Grafana, Datadog provide visualization)
- ❌ Pricing database (maintenance burden, user-specific)
- ❌ User authentication (identity providers)
- ❌ Real-time alerting (alerting platforms)

**Avoid:**
- ❌ Re-implementing PyTokenCalc
- ❌ Building visualization UI
- ❌ Complex ML models (keep it simple)
- ❌ Scope creep into optimization execution

---

## Architecture Constraints

### Middleware Must Be Non-Invasive
- <5ms overhead per call
- Transparent to application
- Works with any framework

### Database Must Scale
- Handle 1M+ events efficiently
- Sub-second query latency
- Good compression ratio

### Attribution Must Be Accurate
- 100% of tokens attributed
- Breakdown adds to total
- Verifiable against PyTokenCalc

### Recommendations Must Be Actionable
- Specific changes recommended
- Token savings quantified
- Risk/effort assessed
- Confidence scored

---

## Commit Guidelines

**Format:**
```
<type>: <description>

<detailed explanation>

Closes: <issue number if applicable>
```

**Types:**
- `feat:` New middleware integration, pattern detector, or query helper
- `fix:` Bug fix
- `docs:` Documentation updates
- `refactor:` Code reorganization
- `test:` Test additions
- `perf:` Performance improvement

**Examples:**
```
feat: Add LlamaIndex middleware integration

Enables automatic interception of LlamaIndex queries.
Captures request/response with <3ms overhead.

Closes: #42
```

```
feat: Implement token attribution breakdown

6-dimensional breakdown: WHEN, WHERE, HOW, WHICH, SESSION, WHY.
Algorithms for inferring system vs context vs user tokens.

Closes: #15
```

---

## Before Making a PR

- [ ] Read VISION.md (understand purpose)
- [ ] Read ROADMAP.md (understand phase)
- [ ] Check scope against "Scope Discipline"
- [ ] Run tests: `pytest tests/ --cov=openanchor` (80%+)
- [ ] Code format: `black openanchor/`
- [ ] Lint: `ruff check openanchor/`
- [ ] Add tests for new feature
- [ ] Update docs if needed
- [ ] Test with real LLM calls (if applicable)
- [ ] Follow commit guidelines

---

## Common Questions

**Q: Should I add cost calculation?**  
A: No. Show tokens; users apply their pricing. Costs are user-specific.

**Q: Can I optimize code automatically?**  
A: No. Recommend optimizations; users implement.

**Q: What if PyTokenCalc is missing a model?**  
A: Update PyTokenCalc in a separate PR, then use it.

**Q: Can I add real-time alerting?**  
A: No. Export via OTEL; alerting platforms handle notifications.

**Q: Should I support <LLM Provider X>?**  
A: Yes! If PyTokenCalc supports it, add middleware integration.

**Q: Can I build a dashboard?**  
A: No. Grafana/Datadog provide visualization. Export via OTEL.

---

## Performance Targets

- Middleware latency: <5ms per call
- Event processing: <1ms
- Query latency: <1s (even complex queries)
- Attribution accuracy: 100%
- Pattern detection: <5% false positive rate
- Memory: <500MB for 1M events

---

## Resources

- **Helicone (reference):** https://github.com/helicone/helicone
- **PyTokenCalc:** https://github.com/Mullassery/pytokencalc
- **ClickHouse:** https://clickhouse.com/
- **OpenTelemetry:** https://opentelemetry.io/
- **Grafana:** https://grafana.com/

---

## Local Development Setup

```bash
# Start database (PyTokenCalc will initialize schema)
docker-compose -f docker/dev-compose.yml up -d

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ --cov=openanchor

# Run example
python examples/langchain_example.py

# Check database tables
# (commands depend on database type; see docker-compose.yml)
```

---

**Last Updated:** 2026-07-15  
**Maintainer:** Georgi Mammen Mullassery  
**Status:** v0.1 Alpha (middleware architecture)
