# OpenAnchor: Token Intelligence for LLM Systems

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Status: v0.1 Released](https://img.shields.io/badge/Status-v0.1%20Released-brightgreen)
![Next: v0.2 (6-week roadmap)](https://img.shields.io/badge/Next-v0.2%20(6--week%20roadmap)-blue)

**OpenAnchor is a token intelligence analysis layer that intercepts LLM calls, works with PyTokenCalc for accurate counts, and provides optimization insights.**

Like Helicone but focused on token INTELLIGENCE instead of cost tracking. Like Langfuse but with automatic token attribution and pattern detection. 

**Dependency:** OpenAnchor REQUIRES PyTokenCalc. Install `pip install openanchor` and PyTokenCalc is automatically included. PyTokenCalc can be used standalone without OpenAnchor.

---

## Roadmap

### v0.1.0 ✅ RELEASED
- 6-Dimensional Token Attribution (WHEN, WHERE, HOW, WHICH, SESSION, WHY)
- Token Collection & Aggregation
- Analytics APIs (query by operation, phase, model, time)
- LangChain Middleware Integration
- SQLite Storage (PostgreSQL v1.0)
- 25 Tests (100% passing)

### v0.2.0 (In Progress - 6-week roadmap)
**Priority P0 (Weeks 1-2):**
- [Task 2.1] Pattern Detection & Anomaly Alerts (2 weeks)
- [Task 2.2] OpenTelemetry Export to Grafana/Datadog (1.5 weeks)

**Priority P1 (Weeks 2-3, parallel):**
- [Task 2.3] Auto Prompt Tagging (ML-based, 95%+ accuracy)
- [Task 2.4] LangSmith Integration
- [Task 2.5] LlamaIndex Integration

**Priority P2 (Weeks 3-4, dependent):**
- [Task 2.6] Cost Optimization Engine (5 techniques: DocIngest, LazyMCP, ContextCompressor, Caveman, SkillLoader)
- [Task 2.7] Quality Assurance Framework (A/B testing, auto-rollback)

**Expected Release:** Mid-August 2026

For full task breakdown, see [OPENANCHOR v0.2 Roadmap](planning/OPENANCHOR_PRODUCT_VISION.md)

### v1.0 (Later)
- PostgreSQL Support
- Enterprise Dashboard
- Advanced Cost Optimization
- Multi-Model Orchestration
- Custom Optimization Rules

---

## Installation

### For Users

```bash
pip install openanchor
```

### For Developers

```bash
# Clone the repository
git clone https://github.com/Mullassery/openanchor.git
cd openanchor

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/
```

**Requirements:**
- Python 3.9+
- PyTokenCalc 0.8+
- pip or uv

---

## What It Does

**Intercepts.** Sits between your application and LLM providers, capturing every call.

**Records.** Tokens consumed, latency, prompt details, response quality.

**Analyzes.** Where did tokens go? What patterns emerge? How to optimize?

**Recommends.** Specific optimizations with estimated token savings.

**Streams.** Insights via OpenTelemetry to Grafana/Datadog/custom tools.

---

## Core Features

### 1. Automatic Request/Response Capture

```python
# Your code stays the same; OpenAnchor intercepts automatically

from openanchor.middleware.langchain import OpenAnchorMiddleware

chain = my_chain | OpenAnchorMiddleware()
response = chain.run("query")
# ✅ Captured: prompt, response, tokens, latency
```

### 2. Six-Dimensional Token Attribution

Understand WHERE tokens went:

```python
breakdown = analyzer.get_attribution(call_id="xyz")
# Returns:
{
  "system_prompt": 500,
  "user_input": 2000,
  "retrieval_context": 1500,
  "model_overhead": 200,
  
  # With patterns:
  "patterns": ["retrieval_heavy"],
  "recommendation": "Improve ranking; save 40%"
}
```

### 3. Automatic Pattern Detection

```python
patterns = analyzer.detect_patterns(session_id="project_q3")
# Detects: anomalies, trends, drift, efficiency issues
```

### 4. Intelligent Recommendations

```python
recommendations = analyzer.get_recommendations()
# [
#   {action: "Improve retrieval ranking", 
#    tokens_saved: 600, confidence: 0.95},
#   ...
# ]
```

### 5. Query APIs

```python
# Query by prompt type
stats = client.get_tokens_by_prompt_category()

# Query by time range
usage = client.get_session_stats(
    session_id="project_q3",
    start_date="2026-07-01"
)

# Detect anomalies
anomalies = client.detect_anomalies()
```

### 6. OTEL Streaming

Streams to your existing observability tools:

```
OpenAnchor → OTEL Metrics
    ├─ token_consumption_total
    ├─ token_latency_ms
    ├─ prompt_category_distribution
    └─ anomaly_alerts
    ↓
Grafana / Datadog / Custom Dashboards
```

---

## Quick Start

### Installation

```bash
pip install openanchor
```

### LangChain Integration

```python
# pip install openanchor
# (PyTokenCalc is automatically included)

from openanchor.middleware.langchain import OpenAnchorMiddleware

# Setup (PyTokenCalc bundled automatically)
middleware = OpenAnchorMiddleware(
    database_url="your-database-connection",
    project_name="my_rag_app"
)

# Use with chain
chain = my_chain | middleware
response = chain.run("Your question")

# Analyze (queries both token counts + enrichments)
recommendations = middleware.get_recommendations()
for rec in recommendations:
    print(f"Optimize: {rec['action']} (save {rec['tokens_saved']} tokens)")
```

### LlamaIndex Integration

```python
from openanchor.middleware.llamaindex import OpenAnchorCallback

callback = OpenAnchorCallback(
    database_url="your-database-connection"
)

query_engine = index.as_query_engine(
    callbacks=[callback]
)
response = query_engine.query("Your question")

# Analyze
analyzer = callback.analyzer
efficiency = analyzer.rank_prompts_by_efficiency()
```

### Raw Proxy Mode

```python
from openanchor import OpenAnchorProxy

proxy = OpenAnchorProxy(database_url="your-database-connection")

response = proxy.call(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

# Built-in analysis
analyzer = proxy.analyzer
patterns = analyzer.detect_patterns()
```

---

## How It Works

### Architecture

```
Your Application
    ↓
OpenAnchor Middleware
├─ Capture incoming prompt
├─ Proxy to LLM provider
├─ Capture outgoing response
├─ Call PyTokenCalc for token counts
└─ Enrich PyTokenCalc's database
    ↓
PyTokenCalc (Token Accounting)
├─ Provide accurate token counts
├─ Store raw token_events
└─ Manage database
    ↓
Shared Database
├─ PyTokenCalc tables (token_events)
├─ OpenAnchor tables (attribution, patterns, recommendations)
├─ Query APIs (Python)
└─ OTEL Export
    ↓
Grafana/Datadog/Custom Dashboards
```

**Important:** OpenAnchor uses PyTokenCalc's database. It doesn't create or manage its own database.

### What It Captures

Each LLM call creates an event:

```python
{
  timestamp: "2026-07-15T10:00:00Z",
  
  request: {
    model: "gpt-4",
    provider: "openai",
    prompt: "...",
    metadata: {...}
  },
  
  response: {
    tokens: {input: 3200, output: 450},
    latency_ms: 1800,
    ttft_ms: 450,
    quality_score: 0.94
  }
}
```

---

## Use Cases

### Use Case 1: RAG System Optimization

```python
# Your RAG system with retrieval
def rag_query(pdf_path: str, query: str):
    docs = retrieve(pdf_path, query)
    response = llm(build_prompt(docs, query))
    return response

# OpenAnchor shows
breakdown = analyzer.get_attribution()
# "Retrieval: 1500 tokens (47% of total)"
# "Recommendation: Improve ranking, save 40%"

# You implement optimization
# ✅ Save 600 tokens per query
```

### Use Case 2: Agent System Debugging

```python
# Multi-step agent
def agent_workflow(task: str):
    # Step 1: Plan
    # Step 2: Retrieve
    # Step 3: Reason
    # Step 4: Respond
    pass

# OpenAnchor shows where tokens went
breakdown = analyzer.get_operation_breakdown()
# "Planning: 40%, Retrieval: 30%, Reasoning: 20%, Response: 10%"
# "Recommendation: Planning is too complex; simplify"
```

### Use Case 3: Prompt Efficiency

```python
# Multiple prompt versions?
efficiency = analyzer.rank_prompts_by_efficiency()
# v2: 4200 tokens, 96% quality ← Use this
# v1: 6100 tokens, 94% quality

# OpenAnchor recommendation: Use v2, save 1900 tokens
```

---

## Comparison with Alternatives

| Feature | Helicone | Langfuse | LangSmith | OpenAnchor |
|---------|----------|----------|-----------|-----------|
| **Middleware** | ✅ | ❌ | ❌ | ✅ |
| **Captures req+resp** | ✅ | ✅ | ✅ | ✅ |
| **Database** | ✅ | ✅ | ✅ | ✅ |
| **Token attribution** | ❌ | ⚠️ (manual) | ❌ | ✅ (automatic, 6D) |
| **Pattern detection** | ❌ | ❌ | ❌ | ✅ |
| **Recommendations** | ❌ | ❌ | ❌ | ✅ |
| **Cost focus** | ✅ (primary) | ✅ | ✅ | ❌ (token-focused) |
| **Active dev** | ❌ (maintenance) | ✅ | ✅ | ✅ |

**Why OpenAnchor?**
- Helicone in maintenance mode (acquired by Mintlify)
- Langfuse great for traces but requires manual attribution
- LangSmith LangChain-specific, no recommendation engine
- **OpenAnchor:** Automatic token intelligence + active development

---

## Key Principles

1. **Middleware-First:** Intercept at application level for visibility
2. **Token-Centric:** Focus on understanding tokens, not costs
3. **Automatic:** No manual configuration; analyze automatically
4. **Database-Backed:** Store everything for historical analysis
5. **Open Integration:** Use OTEL, not proprietary formats

---

## Current Status

🚀 **v0.1 Alpha** (in development)

- ✅ Middleware framework
- ✅ LangChain integration
- ✅ LlamaIndex integration
- ✅ Database storage (PyTokenCalc)
- ⏳ Token attribution engine
- ⏳ Pattern detection
- ⏳ Recommendations engine

See [ROADMAP.md](./ROADMAP.md) for detailed timeline.

---

## Setup

### Local Development

```bash
# Start database
docker-compose -f docker/dev-compose.yml up -d

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ --cov=openanchor

# Run example
python examples/langchain_example.py
```

### Production Deployment

See deployment guide in documentation (coming in v1.0).

---

## Examples

See `examples/` directory:

- `langchain_example.py` — LangChain integration
- `llamaindex_example.py` — LlamaIndex integration
- `raw_proxy_example.py` — Raw API proxy
- `analysis_example.py` — Query and analysis patterns

---

## Contributing

Contributions welcome! See [CLAUDE.md](./CLAUDE.md) for guidelines.

---

## License

MIT License — see [LICENSE](./LICENSE)

---

## Acknowledgments

Built on patterns from [Helicone](https://github.com/helicone/helicone).

Uses PyTokenCalc's database for analytics storage.

Integrates with [PyTokenCalc](https://github.com/Mullassery/pytokencalc) for token accuracy.

---

**Questions?** Open an issue on GitHub.

**Want to contribute?** See [CLAUDE.md](./CLAUDE.md).

---

**Last Updated:** 2026-07-15  
**Status:** v0.1 Alpha (middleware architecture)  
**Maintainer:** Georgi Mammen Mullassery
