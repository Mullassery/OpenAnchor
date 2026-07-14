# OpenAnchor — Vision & Scope

**OpenAnchor is the Token Consumption Intelligence Platform.**

OpenAnchor consumes token counts produced by PyTokenCalc and transforms them into operational intelligence: attribution, pattern detection, trend analysis, and actionable optimization recommendations.

**Relationship:** OpenAnchor sits ON TOP of PyTokenCalc (strict dependency hierarchy).

---

## Core Mission

OpenAnchor solves the intelligence problem in multi-LLM development:

> **Teams track token consumption but don't understand it: Why did costs spike? Where are tokens actually spent? What should we do about it?**

### Division of Responsibility

| Question | Answered By |
|----------|-------------|
| "How many tokens were used?" | PyTokenCalc (token counting) |
| "How many tokens by modality (text/image)?" | PyTokenCalc (breakdown) |
| "Why were those tokens used?" | **OpenAnchor (attribution)** |
| "What changed?" | **OpenAnchor (pattern detection)** |
| "What's the trend?" | **OpenAnchor (trend analysis)** |
| "What should we do?" | **OpenAnchor (recommendations)** |

---

## What We Solve

### Problem 1: Invisible Token Consumption
- Teams see "$47/day" but don't know where it's spent
- Is it long conversations? PDFs? Too many tools? Wrong model?
- Cost spikes happen; root causes remain unknown

### Problem 2: No Attribution
- Token counts are aggregate numbers, not actionable
- Can't trace tokens to: system prompts, context, retrieval, MCP calls
- No way to know which optimization matters most

### Problem 3: Undetected Patterns
- Context inflation happens gradually (users don't notice)
- Retrieval quality degrades (not measured)
- Token growth correlates with issues (but invisible)

### Problem 4: Manual Optimization
- Finding optimization opportunities requires manual analysis
- Users don't know: should we compress memory? Improve retrieval? Switch models?
- Decisions are guesswork, not data-driven

---

## What OpenAnchor Provides

### 1. Complete Visibility
Attribute token consumption to:
- ✅ System prompts
- ✅ User input
- ✅ Conversation history
- ✅ Retrieval context (RAG)
- ✅ MCP server calls
- ✅ Tool execution results
- ✅ Image/audio encoding
- ✅ Agent memory systems
- ✅ Model context overhead

**Result:** Teams know exactly where every token is spent.

### 2. Pattern Detection
Automatically detect:
- ✅ Token growth trends (over time)
- ✅ Prompt drift (user inputs changing)
- ✅ Context inflation (history growing)
- ✅ Retrieval inefficiency (fetch count increasing)
- ✅ MCP expansion (more server calls)
- ✅ Model behavior changes (same input, different cost)

**Result:** Issues are caught before they become expensive.

### 3. Optimization Intelligence
Identify opportunities to:
- ✅ Reduce unnecessary context
- ✅ Improve retrieval efficiency
- ✅ Compress conversation memory
- ✅ Optimize MCP interactions
- ✅ Switch to cheaper models (without quality loss)
- ✅ Batch similar requests
- ✅ Use prompt caching effectively

**Result:** Concrete, prioritized optimization actions.

### 4. Open Integration
Integrate with:
- ✅ Langfuse (observability)
- ✅ OpenTelemetry (standard observability)
- ✅ Grafana (dashboards)
- ✅ Prometheus (metrics)
- ✅ ClickHouse (data warehouse)
- ✅ DuckDB (local analytics)
- ✅ Snowflake (enterprise data lake)
- ✅ Custom BI tools

**Result:** Token intelligence flows into existing infrastructure.

---

## What OpenAnchor IS

✅ **An intelligence layer that:**
- Consumes token accounting data from PyTokenCalc
- Transforms events into observability signals
- Attributes consumption to components
- Detects patterns and anomalies
- Recommends optimizations
- Integrates with observability platforms

✅ **Built on:**
- PyTokenCalc: Token accounting (source of truth)
- OpenTelemetry: Standard observability events
- Open formats: Easy integration with any stack

✅ **Design Philosophy:**
- Observability-first (not optimization-first)
- Attribution-focused (not aggregate)
- Pattern-aware (not reactive)
- Open-integration (not proprietary)

---

## What OpenAnchor IS NOT

### ✅ STRICTLY PyTokenCalc's Responsibility (Never OpenAnchor)
❌ **NOT token counting** → PyTokenCalc does this
  - Does not count tokens
  - Does not manage tokenizers
  - Does not integrate with APIs
  - Does not cache token counts

❌ **NOT cost calculation** → PyTokenCalc handles this
  - Does not calculate costs from tokens
  - Does not manage pricing data
  - Does not track budgets

### ✅ STRICTLY Separate Projects (Never OpenAnchor)
❌ **NOT a middleware wrapper** → Frameworks handle execution
  - Does not intercept LLM calls
  - Does not wrap models
  - Does not manage APIs

❌ **NOT an optimization engine** → Separate service
  - Does not automatically optimize
  - Does not execute optimizations
  - Does not modify behavior

❌ **NOT a complete observability system** → Use platforms
  - Does not provide dashboards (Grafana does)
  - Does not store data (ClickHouse, etc do)
  - Does not generate alerts (platforms do)

### ✅ STRICTLY Integration Points (OpenAnchor Consumes, Doesn't Produce)
❌ **NOT replacing:**
- PyTokenCalc (we depend on it)
- LangChain, LlamaIndex (we integrate with them)
- Observability platforms (we feed data into them)
- Model selection frameworks (we provide signals, not decisions)

---

## Scope: IN vs OUT

### STRICTLY IN-SCOPE
- Token event collection and transformation
- Attribution breakdown by component
- Pattern detection (anomalies, trends, drift)
- Observability signal generation
- Integration with observability platforms
- Optimization opportunity identification
- Usage forecasting based on patterns
- Governance policy enforcement
- Multi-tenant data isolation

### STRICTLY OUT-OF-SCOPE
- Token counting (PyTokenCalc)
- Cost calculation (PyTokenCalc)
- Model selection (frameworks)
- LLM API management (frameworks)
- Automatic optimization execution
- Model re-training
- Custom metric computation
- Data storage (use observability platforms)
- Dashboard UI (use Grafana, etc.)

### RELATED SEPARATE PROJECTS
- **PyTokenCalc:** Token accounting foundation
- **OpenObservability:** Dashboard UI for token visualization
- **OpenOptimize:** Automatic cost optimization (separate service)
- **ModelIntelligence:** Model selection and provider routing

---

## Integration With PyTokenCalc

### What OpenAnchor Consumes FROM PyTokenCalc
```
PyTokenCalc Output (Token Counts):
├─ Token count (exact number)
├─ Model name (specific model used)
├─ Provider name (OpenAI, Anthropic, etc)
├─ Input tokens (user + context)
├─ Output tokens (model response)
├─ By modality (text tokens, image tokens, etc)
└─ Metadata (timestamp, user_id, session_id, etc)

↓ OpenAnchor consumes this data for attribution/pattern detection
```

### What OpenAnchor Does NOT Do
✅ Never counts tokens (PyTokenCalc does this)
✅ Never calculates pricing (PyTokenCalc can do this)
✅ Never manages APIs (PyTokenCalc manages tokenizer APIs)
✅ Never caches token counts (PyTokenCalc handles caching)

### OpenAnchor Data Flow Example
```
User calls LLM with code review request
   ↓
LLM library (LangChain, etc)
   ↓
PyTokenCalc: "Count tokens for this request"
   ↓
PyTokenCalc Returns: {
     input_tokens: 3200,
     output_tokens: 450,
     model: "claude-3-5-sonnet",
     timestamp: "2026-07-15T10:00:00Z"
   }
   ↓
OpenAnchor: "Analyze this token event"
   ↓
OpenAnchor Returns: {
     attribution: {
        system_prompt: 500,
        user_code: 1200,
        conversation_history: 1000,
        model_overhead: 500
     },
     patterns: ["context_growing"],
     recommendations: ["compress_history"]
   }
```

### Boundary: What Each Project Owns

**PyTokenCalc is responsible for:**
✅ Token counting accuracy (99%+)
✅ Supporting 20+ providers
✅ Local + API tokenizers
✅ Caching strategy
✅ Exact token breakdown by modality

**OpenAnchor is responsible for:**
✅ Consuming token counts from PyTokenCalc
✅ Attribution (who consumed tokens)
✅ Pattern detection (what changed)
✅ Trend analysis (is it growing?)
✅ Recommendations (what to do)

---

## Design Principles

### 1. PyTokenCalc is Foundation (Strict)
OpenAnchor depends on PyTokenCalc for all token accounting.
We NEVER re-implement: tokenization, token counting, cost calculation, model APIs.
PyTokenCalc is the single source of truth for token counts.

### 2. Observability First
OpenAnchor is an observability layer, not an optimization layer.
We detect and report; users decide actions.
Integration with platforms (Grafana, Langfuse) is primary.

### 3. Attribution Matters
Aggregate token counts hide the story.
Disaggregation by component reveals the reality.
Every metric should answer: "What part of the system consumed this?"

### 4. Pattern Intelligence
Raw counts are historical; patterns are predictive.
Detect growth trends, drift, inflation before they become problems.
Anomaly detection enables proactive management.

### 5. Open Integration
No proprietary formats, no lock-in.
Standard observability protocols (OpenTelemetry).
Easy to export, integrate, visualize anywhere.

---

## Success Metrics

After v1.0:

- **Visibility:** 100% of token consumption attributed to components
- **Pattern detection:** Anomalies detected within 24h of occurrence
- **Integration:** Seamless export to Grafana, Langfuse, OpenTelemetry
- **Adoption:** Used by 50+ teams tracking token consumption
- **Community:** Contributions for custom attribution models
- **Accuracy:** 100% agreement with PyTokenCalc counts (verify)

---

## Roadmap Summary

### v0.1: Core Intelligence
- Token event collection from PyTokenCalc
- Basic attribution (system prompt, user input, context)
- Simple trend detection
- CSV export for analysis

### v0.2: Pattern Detection
- Anomaly detection (spikes, drift)
- Conversation-level analysis
- Model-specific tracking
- Integration with Langfuse

### v0.3: Advanced Integration
- OpenTelemetry export
- Grafana dashboard templates
- Custom attribution rules
- Optimization recommendations

### v1.0: Enterprise Ready
- Multi-tenant support
- Advanced pattern learning
- Governance policies
- SLA/compliance reporting

---

## Long-Term Vision

Become the operational intelligence layer for AI token consumption.

Just as:
- **Prometheus** provides visibility into infrastructure metrics
- **Datadog** provides operational intelligence for systems
- **Grafana** visualizes any observability data
- **OpenTelemetry** standardizes observability signals

**OpenAnchor** should provide visibility and intelligence for token consumption across AI systems.

The standard that every AI team uses to understand and optimize token efficiency.

---

**Last Updated:** 2026-07-15  
**Author:** Georgi Mammen Mullassery  
**License:** MIT
