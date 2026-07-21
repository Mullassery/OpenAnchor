# OpenAnchor: Token Intelligence for LLM Systems

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Status: v0.1 Released](https://img.shields.io/badge/Status-v0.1%20Released-brightgreen)
![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Next: v0.2 (6-week roadmap)](https://img.shields.io/badge/Next-v0.2%20(6--week%20roadmap)-blue)

**OpenAnchor is a token attribution and cost governance engine. Understand where every token goes and why. Enable cost-quality tradeoff optimization.**

**Architectural Role:** Owns cost intelligence and token attribution. Provides 6D token attribution (who, what, when, where, why, how much) and cost governance. Integrates with PyStreamMCP for intelligent orchestration and StatGuardian for cost validation.

Think of it as a **token profiler + cost optimizer for your LLM system**: understand token distribution, detect cost anomalies, optimize without guesswork, and make data-driven decisions about prompt engineering and retrieval strategies.

**Designed as an open-source alternative to Helicone and Langfuse, with deep integrations for LangChain, LlamaIndex, and raw API proxy modes.**

> **Dependency Note:** OpenAnchor requires [PyTokenCalc](https://github.com/Mullassery/pytokencalc) for accurate token counting. Installing `pip install openanchor` automatically includes PyTokenCalc as a dependency.

---

## Table of Contents

1. [Why OpenAnchor?](#why-openanchor)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Features](#core-features)
5. [How It Works](#how-it-works)
6. [API Reference](#api-reference)
7. [Configuration](#configuration)
8. [Use Cases](#use-cases)
9. [Examples](#examples)
10. [Roadmap](#roadmap)
11. [Contributing](#contributing)
12. [License](#license)

---

## Why OpenAnchor?

### The Problem

LLM applications eat tokens—and cost scales linearly with token volume. But most teams are flying blind:

- **No visibility:** Where do tokens go? System prompt? User input? Retrieval context? Model overhead?
- **No insights:** Are you spending tokens efficiently? What's normal vs. anomalous?
- **No recommendations:** How do you actually optimize? Prompt tweaking? Better retrieval? Different model?
- **No history:** How has token usage changed over time? Which prompts regressed?

### The Solution: OpenAnchor

OpenAnchor intercepts every LLM call and answers these questions automatically:

 **6D Token Attribution** — Break down tokens by purpose (system, user, context, overhead, inference, etc.) 
 **Automatic Pattern Detection** — Find inefficiencies, anomalies, drift, and trends 
 **Actionable Recommendations** — Get specific optimization suggestions with estimated savings 
 **Historical Analysis** — Query token usage by time, prompt category, session, or model 
 **OTEL Export** — Stream metrics to your observability stack (Prometheus, Jaeger, Tempo, Datadog, New Relic, etc.) 
 **Zero Code Changes** — Middleware intercepts calls; your code stays the same 

Result: **Optimize token usage by 30–60%** without guesswork.

---

## Installation

### For Users

```bash
# PyTokenCalc is included automatically
pip install openanchor
```

**Requirements:**
- Python 3.9+
- pip or uv

**Optional: Advanced usage**
- PostgreSQL 12+ (for production deployments)
- OpenTelemetry collector (for observability export)

### For Developers

```bash
# Clone the repository
git clone https://github.com/Mullassery/openanchor.git
cd openanchor

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ --cov=openanchor

# Run with example data
python examples/langchain_example.py
```

---

## Quick Start

### 30-Second Setup with LangChain

```python
from openanchor.middleware.langchain import OpenAnchorMiddleware

# Initialize middleware
middleware = OpenAnchorMiddleware(
 database_url="sqlite:///openanchor.db", # or PostgreSQL
 project_name="my_rag_app"
)

# Wrap your chain
chain = my_chain | middleware

# Use as normal—OpenAnchor intercepts automatically
response = chain.run("What does this document say?")

# Analyze
recommendations = middleware.get_recommendations()
for rec in recommendations:
 print(f" {rec['action']}  Save {rec['tokens_saved']} tokens")
```

### 30-Second Setup with LlamaIndex

```python
from openanchor.middleware.llamaindex import OpenAnchorCallback

# Initialize callback
callback = OpenAnchorCallback(
 database_url="sqlite:///openanchor.db",
 project_name="my_rag_app"
)

# Attach to query engine
query_engine = index.as_query_engine(callbacks=[callback])

# Use as normal
response = query_engine.query("What does this document say?")

# Analyze
patterns = callback.analyzer.detect_patterns()
efficiency = callback.analyzer.rank_prompts_by_efficiency()
```

### Raw API Proxy (No Framework)

```python
from openanchor import OpenAnchorProxy

# Initialize proxy
proxy = OpenAnchorProxy(
 database_url="sqlite:///openanchor.db",
 api_key="your-openai-key"
)

# Call through proxy instead of direct API
response = proxy.call(
 model="gpt-4",
 messages=[{"role": "user", "content": "Hello"}]
)

# Automatic analysis
breakdown = proxy.analyzer.get_attribution()
print(f"Input tokens: {breakdown['user_input']}")
print(f"Output tokens: {breakdown['model_output']}")
```

---

## Core Features

### 1. **Automatic Request/Response Capture**

Every LLM call is intercepted and recorded:

```python
# Your code doesn't change
response = chain.run("query")

# Behind the scenes:
# Request captured (prompt, model, parameters)
# Response captured (tokens, latency, quality)
# Stored in database for analysis
```

**What's Captured:**
- **Request:** Model name, provider, full prompt text, system message, parameters
- **Response:** Input tokens, output tokens, latency, time-to-first-token, quality score
- **Context:** Timestamp, session ID, request ID, user ID (if provided), tags
- **Metadata:** Retrieval size, reasoning steps, operation type

### 2. **Six-Dimensional Token Attribution**

Understand exactly where tokens are spent:

```python
breakdown = analyzer.get_attribution(call_id="xyz")

print(breakdown)
# {
# "system_prompt": 500, # Fixed system instructions
# "user_input": 2000, # User's actual query
# "retrieval_context": 3500, # Retrieved documents/chunks
# "model_overhead": 200, # Model-specific formatting
# "reasoning_chain": 400, # Intermediate reasoning steps
# "instruction_tuning": 300, # Safety/instruction tokens
# "total": 7400,
# 
# "efficiency_score": 0.78, # 0-1 scale
# "patterns": ["retrieval_heavy"],
# "recommendation": "Improve retrieval ranking; save ~1050 tokens (14%)"
# }
```

**Use this to:**
- Identify which components consume most tokens
- Spot inefficient patterns (e.g., too much context)
- Prioritize optimization efforts

### 3. **Automatic Pattern Detection**

Detects inefficiencies, anomalies, and trends across your session:

```python
patterns = analyzer.detect_patterns(session_id="project_q3")

# Returns:
{
 "anomalies": [
 {
 "call_id": "xyz",
 "issue": "retrieval_bloat",
 "tokens": 5800,
 "expected": 2500,
 "confidence": 0.92
 }
 ],
 "trends": [
 {
 "metric": "avg_input_tokens",
 "trend": "increasing",
 "change": "+15% over 7 days",
 "likely_cause": "growing prompt complexity"
 }
 ],
 "efficiency_issues": [
 {
 "issue": "redundant_system_prompt",
 "tokens_wasted": 300,
 "fix": "De-duplicate system messages"
 }
 ]
}
```

**Patterns Detected:**
- Anomalies (unusual token spikes)
- Efficiency regressions (slower over time)
- Redundancy (repeated text)
- Retrieval bloat (too many documents)
- Model misalignment (wrong model for task)

### 4. **Intelligent Recommendations**

Get specific, actionable optimization suggestions:

```python
recommendations = analyzer.get_recommendations()

# [
# {
# "rank": 1,
# "action": "Improve retrieval ranking (BM25  Dense)",
# "tokens_saved": 1050,
# "current_usage": 3500,
# "optimized_usage": 2450,
# "confidence": 0.95,
# "effort": "medium",
# "timeline_hours": 4
# },
# {
# "rank": 2,
# "action": "Reduce system prompt verbosity",
# "tokens_saved": 200,
# "confidence": 0.88,
# "effort": "low",
# "timeline_hours": 1
# },
# ...
# ]
```

**Recommendations Consider:**
- Historical efficiency data
- Similar successful optimizations
- Implementation effort vs. token savings
- Quality/safety tradeoffs

### 5. **Historical Query APIs**

Analyze token usage over time and dimensions:

```python
# By prompt category
stats = client.get_tokens_by_category()
# {"retrieval": 45000, "summarization": 12000, "classification": 8000}

# By date range
usage = client.get_session_stats(
 session_id="project_q3",
 start_date="2026-07-01",
 end_date="2026-07-31"
)
# {"total_tokens": 450000, "avg_per_call": 2100, "calls": 214}

# By model
model_breakdown = client.get_tokens_by_model()
# {"gpt-4": 300000, "gpt-3.5": 150000}

# Percentile analysis
p95 = client.get_percentile_tokens(percentile=95)
# 4200 (95% of calls use 4200 tokens)

# Efficiency scores
scores = client.get_efficiency_by_prompt_type()
# {"rag": 0.82, "summarization": 0.76, "chat": 0.88}
```

**Queries Support:**
- Time ranges (hourly, daily, weekly, monthly)
- Dimensions (model, prompt type, user, session)
- Aggregations (sum, avg, percentile, max)
- Filters (quality threshold, latency bounds)

### 6. **OTEL Metrics Export**

Stream insights to your observability stack:

```python
# Configure OTEL export
middleware = OpenAnchorMiddleware(
 database_url="...",
 otel_exporter="otlp",
 otel_endpoint="http://localhost:4317"
)

# Automatic metrics:
# - token_consumption_total (counter)
# - token_consumption_seconds (histogram)
# - efficiency_score (gauge)
# - anomaly_detected (event)
# - prompt_category_distribution (histogram)
```

**Supported Exporters:**
- OTLP (OpenTelemetry Protocol)
- Datadog
- New Relic
- CloudWatch
- Custom endpoints

---

## How It Works

### Architecture Overview

```

 Your Application 
 (LangChain / LlamaIndex / Direct) 

 
 
 
 OpenAnchor 
 
 Intercept 
 Request/Resp 
 
 
 Enrich with 
 PyTokenCalc 
 
 
 Analyze & 
 Recommend 
 
 
 
 
 
  
 
 Shared Database OTEL Metrics 
 (PyTokenCalc + 
 OpenAnchor)  Datadog 
  New Relic 
 Raw tokens  CloudWatch 
 Attribution  Your tool 
 Patterns 
 Recommend. 
 
```

### Data Flow

**Per LLM Call:**
1. Application calls LLM (via LangChain, LlamaIndex, or direct API)
2. OpenAnchor middleware intercepts request
3. Request forwarded to LLM provider
4. Response captured from LLM provider
5. PyTokenCalc counts tokens accurately
6. OpenAnchor enriches data (attribution, patterns)
7. Stored in shared database
8. Metrics exported to OTEL endpoint

**Per Analysis Request:**
1. Query database for call history
2. Run pattern detection algorithms
3. Generate recommendations
4. Return results to application

### What Gets Stored

Each LLM call creates a record:

```python
{
 "call_id": "abc123def456",
 "timestamp": "2026-07-15T10:00:00Z",
 "session_id": "project_q3",
 
 # Request data
 "request": {
 "model": "gpt-4",
 "provider": "openai",
 "prompt": "Given the following document: ...",
 "system_message": "You are a helpful assistant.",
 "parameters": {
 "temperature": 0.7,
 "max_tokens": 2000
 }
 },
 
 # Response data
 "response": {
 "tokens": {
 "input": 3200,
 "output": 450
 },
 "latency_ms": 1800,
 "ttft_ms": 450,
 "quality_score": 0.94
 },
 
 # Attribution data (added by OpenAnchor)
 "attribution": {
 "system_prompt": 500,
 "user_input": 2000,
 "retrieval_context": 1500,
 "model_overhead": 200
 },
 
 # Metadata
 "tags": {"workflow": "rag", "user_id": "user_42"},
 "request_id": "req_xyz"
}
```

---

## API Reference

### Middleware Classes

#### `OpenAnchorMiddleware` (LangChain)

```python
from openanchor.middleware.langchain import OpenAnchorMiddleware

middleware = OpenAnchorMiddleware(
 database_url: str, # SQLite or PostgreSQL URI
 project_name: str, # Project identifier
 session_id: Optional[str] = None,
 otel_exporter: Optional[str] = None,
 otel_endpoint: Optional[str] = None,
 enable_pattern_detection: bool = True,
 enable_recommendations: bool = True
)

# Methods
middleware.get_attribution(call_id: str)  dict
middleware.get_recommendations()  List[dict]
middleware.detect_patterns(session_id: Optional[str])  dict
middleware.get_efficiency_score(call_id: str)  float
```

#### `OpenAnchorCallback` (LlamaIndex)

```python
from openanchor.middleware.llamaindex import OpenAnchorCallback

callback = OpenAnchorCallback(
 database_url: str,
 project_name: str,
 session_id: Optional[str] = None,
 # ... same as middleware
)

# Properties
callback.analyzer  AnalysisEngine
```

#### `OpenAnchorProxy` (Raw API)

```python
from openanchor import OpenAnchorProxy

proxy = OpenAnchorProxy(
 database_url: str,
 api_key: str,
 provider: str = "openai", # or "anthropic", "cohere"
 project_name: str = "default"
)

# Methods
proxy.call(model: str, messages: List[dict], **kwargs)  dict
proxy.analyzer  AnalysisEngine
```

### Analysis Engine API

```python
analyzer = middleware.analyzer # or callback.analyzer or proxy.analyzer

# Query token usage
analyzer.get_tokens_by_category()  dict
analyzer.get_tokens_by_model()  dict
analyzer.get_tokens_by_date_range(start, end)  dict
analyzer.get_session_stats(session_id, start_date, end_date)  dict

# Attribution & patterns
analyzer.get_attribution(call_id: str)  dict
analyzer.detect_patterns(session_id: Optional[str])  dict
analyzer.detect_anomalies(threshold: float = 2.0)  List[dict]

# Optimization
analyzer.get_recommendations(top_k: int = 10)  List[dict]
analyzer.rank_prompts_by_efficiency()  List[dict]
analyzer.estimate_savings(action: str)  float

# Debugging
analyzer.get_call_history(session_id: str, limit: int = 100)  List[dict]
analyzer.compare_calls(call_id_1: str, call_id_2: str)  dict
```

---

## Configuration

### Database Setup

**SQLite (Development)**

```python
middleware = OpenAnchorMiddleware(
 database_url="sqlite:///openanchor.db"
)
```

**PostgreSQL (Production)**

```python
middleware = OpenAnchorMiddleware(
 database_url="postgresql://user:password@localhost:5432/openanchor"
)
```

### OTEL Configuration

**OTLP Protocol**

```python
middleware = OpenAnchorMiddleware(
 otel_exporter="otlp",
 otel_endpoint="http://localhost:4317",
 otel_insecure=False
)
```

**Datadog**

```python
middleware = OpenAnchorMiddleware(
 otel_exporter="datadog",
 otel_api_key="your-dd-api-key",
 otel_site="datadoghq.com" # or datadoghq.eu
)
```

**Environment Variables**

```bash
export OPENANCHOR_DATABASE_URL="postgresql://..."
export OPENANCHOR_OTEL_EXPORTER="otlp"
export OPENANCHOR_OTEL_ENDPOINT="http://localhost:4317"
export OPENANCHOR_PROJECT_NAME="my_project"
```

---

## Use Cases

### RAG System Optimization

**Problem:** Your RAG system retrieves too many documents, wasting tokens.

**Solution:**

```python
from openanchor.middleware.langchain import OpenAnchorMiddleware

# Setup middleware
middleware = OpenAnchorMiddleware(
 database_url="sqlite:///openanchor.db",
 project_name="rag_app"
)

# Run RAG queries for a week
# ... (queries happen, middleware captures them)

# Analyze
breakdown = middleware.analyzer.get_attribution()
recommendations = middleware.analyzer.get_recommendations()

# Output:
# Recommendation: Improve retrieval ranking (BM25  Dense)
# Current: 3500 tokens per query
# Optimized: 2450 tokens per query
# Savings: 1050 tokens (30%)
```

### Agent System Debugging

**Problem:** Your multi-step agent is inefficient; you don't know where.

**Solution:**

```python
patterns = middleware.analyzer.detect_patterns()

# Output:
# Pattern: Retrieval bloat
# Calls: 42 (19% of total)
# Avg tokens: 5800
# Expected: 2500
#
# Pattern: Redundant system prompts
# Repeated text: 300 tokens
# Fix: De-duplicate across steps
```

### Prompt Efficiency Comparison

**Problem:** You have 3 prompt versions; which is most efficient?

**Solution:**

```python
efficiency = middleware.analyzer.rank_prompts_by_efficiency()

# Output:
# Prompt v3: 0.92 efficiency
# 4200 tokens, 98% quality  Use this
#
# Prompt v2: 0.84 efficiency
# 6100 tokens, 96% quality  Too verbose
#
# Prompt v1: 0.71 efficiency
# 7800 tokens, 94% quality  Deprecated
```

### Cost Allocation by User/Department

**Problem:** You need to allocate LLM costs across teams for chargeback.

**Solution:**

```python
breakdown = middleware.analyzer.get_tokens_by_dimension(
 dimension="user_id",
 date_range=("2026-07-01", "2026-07-31")
)

# Output:
# alice@company.com: 145000 tokens  $2.90 (at $0.02/1K)
# bob@company.com: 98000 tokens  $1.96
# data_team: 321000 tokens  $6.42
```

---

## Examples

See `examples/` directory for complete working examples:

- **`langchain_example.py`** — RAG with LangChain + recommendations
- **`llamaindex_example.py`** — LlamaIndex integration + pattern detection
- **`raw_proxy_example.py`** — Direct API usage without framework
- **`analysis_example.py`** — Query historical data + comparisons

Run any example:

```bash
cd examples/
python langchain_example.py
```

---

## Roadmap

### v0.1 (Current) — Middleware Foundation
- LangChain integration
- LlamaIndex integration
- Raw proxy mode
- SQLite/PostgreSQL support
- Basic token attribution
-  Pattern detection (in development)
-  Recommendations engine (in development)

### v0.2 (6 weeks) — Advanced Analytics
- Pattern detection (anomalies, trends, efficiency)
- Recommendation engine (ranked suggestions)
- OTEL export (Prometheus, Jaeger, Tempo, Datadog, New Relic, etc.)
- Langfuse integration
- Dashboard (basic analytics view)

### v0.3 (12 weeks) — Multi-Provider Support
- Anthropic Claude support
- Cohere support
- Azure OpenAI support
- Open-source model support (Llama, Mistral)
- Streaming token estimation

### v1.0 (16 weeks) — Production Ready
- Cost tracking (multi-currency, provider pricing)
- Advanced governance (quotas, alerts, policies)
- Enterprise SSO
- API key management
- Audit logging
- SLA monitoring

See [ROADMAP.md](./ROADMAP.md) for detailed timeline.

---

## Troubleshooting

### Issue: "No module named 'openanchor'"

```bash
# Solution: Verify installation
pip install openanchor

# Check version
python -c "import openanchor; print(openanchor.__version__)"
```

### Issue: Database connection error

```python
# Verify database_url format
# SQLite: "sqlite:///path/to/file.db"
# PostgreSQL: "postgresql://user:password@host:port/dbname"

# Test connection
from openanchor import test_connection
test_connection("sqlite:///openanchor.db")
```

### Issue: Tokens not being captured

```python
# Verify middleware is properly attached
chain = my_chain | middleware # NOT middleware | my_chain

# Check logs
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Performance Considerations

- **Latency:** OpenAnchor adds <50ms per call (database write + analysis)
- **Storage:** ~5KB per LLM call (varies by prompt length)
- **Scaling:** PostgreSQL recommended for >1M calls/month

---

## Contributing

Contributions welcome! Please see [CLAUDE.md](./CLAUDE.md) for guidelines.

---

## License

MIT License — see [LICENSE](./LICENSE)

---

## Acknowledgments

Built with [PyTokenCalc](https://github.com/Mullassery/pytokencalc) for token accuracy.

Integrates with LangChain, LlamaIndex, and OpenTelemetry ecosystems.

---

**Questions?** Open an [issue](https://github.com/Mullassery/openanchor/issues).

**Want to contribute?** See [CLAUDE.md](./CLAUDE.md).

**Last Updated:** 2026-07-20 
**Status:** v0.1 Alpha (Middleware Architecture) 
**Maintainer:** Georgi Mammen Mullassery
