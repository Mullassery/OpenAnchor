# OpenAnchor — Vision & Scope

**OpenAnchor is an analysis and enrichment layer for token intelligence.**

It intercepts LLM calls, calls PyTokenCalc for accurate token counting, and enriches PyTokenCalc's database with intelligent analysis: token attribution, pattern detection, and optimization recommendations.

**Critical:** OpenAnchor does NOT manage its own database. It reads from and writes enrichments to PyTokenCalc's database. It's purely an analysis layer, not a storage platform.

**Like Helicone but different:** Where Helicone focuses on cost tracking and caching, OpenAnchor focuses on **token intelligence and optimization** for RAG and agent systems. Unlike Helicone (which is standalone), OpenAnchor requires PyTokenCalc.

---

## Core Mission

OpenAnchor solves the observability and optimization problem for developers building token-conscious LLM systems:

> **Teams see total tokens consumed but don't understand them: Where did tokens come from? What patterns emerge? How do we optimize effectively?**

### Architecture Pattern

```
Your Application
    ↓
OpenAnchor Middleware (INTERCEPTS)
├─ Captures incoming prompt
├─ Proxies to LLM provider
├─ Captures outgoing response
├─ Calls PyTokenCalc for token counts
├─ Categorizes prompt type
└─ Stores enrichments in PyTokenCalc's database
    ↓
PyTokenCalc (Token Counting)
├─ Provides accurate token counts
├─ Handles provider switching
└─ Reconciles via repeated API calls
    ↓
Shared Database (PyTokenCalc's database)
├─ PyTokenCalc storage: token_events
├─ OpenAnchor storage: attribution, patterns, recommendations
├─ Query APIs (Python library)
└─ OTEL Streaming (visualization)
    ↓
User's Application (gets insights)
```

**Key Point:** OpenAnchor is purely analysis. PyTokenCalc owns storage. Both use the same database.

---

## What OpenAnchor Does

### 1. Middleware Interception

OpenAnchor sits between your application and LLM providers, capturing:

- **Incoming:** Full prompt, model, provider, metadata, timestamp
- **Outgoing:** Full response, token counts, latency, quality metrics
- **Latency:** Total time, time-to-first-token (TTFT), token generation rate

```python
# Your code just works; OpenAnchor intercepts automatically
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "..."}]
)
# OpenAnchor captured request + response in the background
```

### 2. Intelligent Prompt Categorization

Automatically categorizes prompts to understand usage patterns:

- Code review prompts
- Summarization prompts
- Classification prompts
- Reasoning prompts
- Retrieval-augmented prompts
- Agent planning prompts
- etc.

**Why it matters:** Different prompt types have different token profiles. Understanding patterns helps optimization.

### 3. Six-Dimensional Token Attribution

Breaks down WHERE tokens went and WHY:

```
WHEN: Request (5000 tokens) vs Response (450 tokens)
WHERE: Retrieval (1500) vs System prompt (500) vs User input (2000) vs Overhead (1000)
HOW: Retrieval breakdown - top-5 documents vs semantic search overhead
WHICH: Using "rag_analyzer_v2" prompt (vs v1: 6100 tokens)
SESSION/PHASE: Phase 2 (analysis) of "project_q3" (600K tokens total)
WHY: Retrieval growing 15%/week (pattern), recommendation: improve ranking
```

### 4. Pattern Detection & Analysis

Automatically detects:
- **Anomalies:** Token spikes (>2σ from baseline)
- **Trends:** Token growth rates, seasonality
- **Drift:** Prompt patterns changing
- **Efficiency:** Which prompts/operations waste tokens
- **Quality correlation:** Token spend vs quality achieved

### 5. Actionable Recommendations

Provides specific optimization opportunities:

```
Optimization: Improve retrieval ranking
├─ Current: Fetching 12 documents per query
├─ Problem: Only 3-4 are relevant (33% relevance)
├─ Solution: Implement better ranking/filtering
├─ Token impact: Reduce retrieval tokens from 1500 → 700 (47% savings)
├─ Quality risk: Low (relevance stays same, just fewer irrelevant docs)
└─ Implementation effort: Medium (2-3 days)
```

### 6. Analysis via Integrated Database

All analysis data stored in PyTokenCalc's database (managed by bundled PyTokenCalc):

```python
from openanchor import OpenAnchor

# pip install openanchor (automatically includes PyTokenCalc)

# Single unified initialization
openanchor = OpenAnchor(
    database_url="your-database-connection"
)
# PyTokenCalc is bundled and initialized automatically

# Query analysis across both token counts + OpenAnchor tables
stats = openanchor.get_token_breakdown_by_prompt_type(
    start_date="2026-07-01",
    session_id="project_q3"
)
# Reads from PyTokenCalc's token_events + OpenAnchor's enrichment tables

# Detect anomalies (using OpenAnchor's pattern_detections table)
anomalies = openanchor.detect_anomalies(metric="tokens", threshold=2.0)
# Returns: [{timestamp, prompt_type, tokens, baseline, deviation}]

# Get recommendations (from OpenAnchor's recommendations table)
recommendations = openanchor.get_recommendations()
# Returns: [Optimization(...), ...]
```

**Deployment Model:** 
- `pip install pytokencalc` — Token counting only (OpenAnchor optional)
- `pip install openanchor` — Includes PyTokenCalc automatically + adds analysis layer
- OpenAnchor REQUIRES PyTokenCalc; PyTokenCalc does NOT require OpenAnchor

### 7. OTEL Streaming & Visualization

Streams insights to observability platforms:

```
OpenAnchor → OTEL Metrics
├─ token_consumption_total
├─ token_latency_ms
├─ prompt_category_distribution
├─ anomaly_scores
└─ optimization_signals
    ↓
Grafana / Datadog / Custom Dashboards
```

---

## Who Should Use OpenAnchor

### ✅ Perfect Fit

- **RAG developers:** "I build retrieval-augmented systems; need to understand token efficiency"
- **Agent builders:** "Multi-step agents; need to know which steps waste tokens"
- **LangChain developers:** Already using LLM frameworks; need observability + intelligence
- **Custom LLM apps:** Building specialized systems; need to understand and optimize token usage
- **Production systems:** Running models at scale; need cost awareness and efficiency

### ❌ Not the Right Tool

- **Claude Code users:** Use PyTokenCalc (OpenAnchor requires middleware setup)
- **Chat interfaces:** No application control (use Langfuse instead)
- **Research/prototypes:** Overkill for non-production work
- **Black-box services:** Can't intercept external APIs

---

## How OpenAnchor Differs from Alternatives

| Feature | Helicone | Langfuse | LangSmith | OpenAnchor |
|---------|----------|----------|-----------|-----------|
| **Middleware interception** | ✅ | ❌ | ❌ | ✅ |
| **Captures req + response** | ✅ | ✅ | ✅ | ✅ |
| **Stores in database** | ✅ | ✅ | ✅ | ✅ |
| **Query APIs** | ✅ | ✅ | ✅ | ✅ |
| **Cost tracking** | ✅ (primary) | ✅ | ✅ | ❌ (token-focused) |
| **Token attribution** | ❌ | ⚠️ (manual) | ❌ | ✅ (automatic, 6D) |
| **Prompt categorization** | ⚠️ (basic) | ❌ | ❌ | ✅ (intelligent) |
| **Pattern detection** | ❌ | ❌ | ❌ | ✅ |
| **Recommendations** | ❌ | ❌ | ❌ | ✅ |
| **OTEL streaming** | ⚠️ | ✅ | ❌ | ✅ |
| **Active development** | ❌ (maintenance) | ✅ | ✅ | ✅ |

**Why OpenAnchor?**
- Helicone: In maintenance mode (acquired by Mintlify)
- Langfuse: Great traces but requires manual attribution tagging
- LangSmith: LangChain-specific, no attribution or recommendations
- **OpenAnchor:** Active development, automatic token intelligence, RAG/agent optimized

---

## Key Design Decisions

### 1. Middleware-First Architecture
OpenAnchor intercepts LLM calls at the application level, not external proxy. This enables:
- Deep visibility into requests AND responses
- Accurate latency measurement
- Direct integration with frameworks (LangChain, LlamaIndex, raw API)
- Full control over data handling

### 2. Token-First, Not Cost-First
OpenAnchor focuses on **token understanding**, not cost tracking:
- **Shows:** WHERE tokens came from (attribution)
- **Doesn't:** Calculate costs (users multiply tokens × their pricing)
- **Why:** Tokens are universal; costs are user-specific (Groq $0.59/M vs DeepInfra $0.23/M)
- **Benefit:** Works with any pricing model, no pricing database maintenance

### 3. Intelligent Prompt Analysis
Automatically categorizes prompts to understand usage patterns:
- Detects prompt intent (code, reasoning, retrieval, etc)
- Tracks efficiency per category
- Identifies over-engineered prompts
- Recommends category-specific optimizations

### 4. Database for Long-Term Analysis
PyTokenCalc's database stores all events enabling:
- Historical trend analysis
- Cross-session pattern detection
- Long-term efficiency tracking
- Seasonal pattern discovery

### 5. OTEL as Integration Standard
Streams insights via OpenTelemetry so users can:
- Visualize in Grafana, Datadog, custom dashboards
- Set alerts in their existing monitoring
- Build custom analysis pipelines
- No vendor lock-in

---

## Success Metrics (v1.0)

- ✅ **Accuracy:** 100% token counts vs PyTokenCalc/official counts
- ✅ **Latency:** <5ms middleware overhead per call
- ✅ **Database:** Stores 1M+ events efficiently
- ✅ **Query performance:** <1s for complex queries
- ✅ **Categorization:** 95%+ accuracy on prompt types
- ✅ **Recommendations:** Actual 30%+ token savings when implemented
- ✅ **Adoption:** Real-world RAG/agent systems using it

---

## Roadmap Overview

### v0.1 (2 weeks): Middleware Foundation
- Middleware interception (LangChain, LlamaIndex, raw API)
- Token + latency capture
- Basic prompt categorization
- Database setup and storage
- Basic query APIs
- Simple OTEL export

### v0.2 (3 weeks): Token Intelligence
- 6-dimensional token attribution
- Pattern detection (anomalies, trends)
- Prompt efficiency ranking
- Operation-type breakdown
- Advanced query APIs

### v0.3 (4 weeks): Optimization Engine
- Detailed recommendations with token savings
- Root cause analysis
- Session/phase breakdown
- A/B testing framework (preliminary)
- Full OTEL integration

### v0.4 (4 weeks): Advanced Features
- Complete A/B testing framework
- Gradual rollout support
- Performance regression detection
- Conditional routing recommendations
- Advanced categorization

### v1.0 (3 weeks): Production Ready
- Multi-tenant support
- Security features (encryption, RBAC, audit logs)
- Performance optimization (<50ms queries)
- Comprehensive documentation
- Enterprise features

**Total: 16 weeks** (realistic for this architecture)

---

## Architecture Highlights

### Middleware Integration Points

```python
# LangChain
from openanchor.integrations.langchain import OpenAnchorMiddleware
chain = my_chain | OpenAnchorMiddleware()

# LlamaIndex
from openanchor.integrations.llamaindex import OpenAnchorCallback
callback = OpenAnchorCallback()
query_engine.run(query, callbacks=[callback])

# Raw API
from openanchor import OpenAnchorProxy
proxy = OpenAnchorProxy(database_url="your-database-connection")
response = proxy.call(model="gpt-4", messages=[...])
```

### Database Schema

```sql
CREATE TABLE token_events (
  timestamp DateTime,
  session_id String,
  phase_id String,
  
  -- Request
  prompt_raw String,
  prompt_category String,
  model String,
  provider String,
  
  -- Response
  response_raw String,
  input_tokens UInt32,
  output_tokens UInt32,
  
  -- Latency
  total_latency_ms UInt32,
  ttft_ms UInt32,
  
  -- Attribution
  system_prompt_tokens UInt32,
  user_input_tokens UInt32,
  retrieval_context_tokens UInt32,
  history_tokens UInt32,
  overhead_tokens UInt32,
  
  -- Quality
  quality_score Float32,
  error_flag Boolean,
  
  -- Metadata
  metadata String,  -- JSON
  tags Array(String)
) ENGINE = MergeTree()
ORDER BY (timestamp, session_id)
```

---

## Design Principles

### 1. Middleware-First
Intercept at application level for deep visibility.

### 2. Token-Centric
Focus on understanding token consumption, not cost calculation.

### 3. Automatic Intelligence
No manual configuration; analyze automatically.

### 4. Database-Backed
Store everything for historical analysis and trends.

### 5. Open Integration
Use OTEL, not proprietary formats; users choose visualization tools.

### 6. RAG/Agent Optimized
Built specifically for retrieval-augmented and multi-step agent systems.

---

## What OpenAnchor IS

✅ A middleware platform that intercepts LLM calls  
✅ Captures requests, responses, tokens, and latency  
✅ Stores everything in a database for analysis  
✅ Provides automatic token attribution (6 dimensions)  
✅ Detects patterns and generates recommendations  
✅ Streams insights via OTEL to visualization tools  
✅ Enables query APIs for programmatic access  
✅ Actively developed and optimized for RAG/agents  

---

## What OpenAnchor IS NOT

❌ A cost tracker (Helicone focus)  
❌ A trace visualizer (Langfuse/LangSmith focus)  
❌ A pricing database (user provides their pricing)  
❌ Automatic optimizer (recommends; users implement)  
❌ For end-user tools (requires app-level integration)  

---

## Long-Term Vision

Become the standard token intelligence layer for LLM applications.

Just as:
- **Prometheus** provides infrastructure metrics visibility
- **Grafana** visualizes any observability data
- **OpenTelemetry** standardizes observability signals

**OpenAnchor** should provide token consumption understanding for every team building with LLMs.

The go-to platform for understanding WHERE tokens go and HOW to optimize token efficiency.

---

**Last Updated:** 2026-07-15  
**Author:** Georgi Mammen Mullassery  
**Status:** LOCKED (Ready for v0.1 implementation with correct architecture)  
**License:** MIT
