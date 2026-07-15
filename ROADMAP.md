# OpenAnchor Implementation Roadmap

**Goal:** Build a middleware-based token intelligence platform that intercepts LLM calls, analyzes token consumption, stores data, and provides optimization recommendations.

**Timeline:** v0.1 (Week 1-2) → v1.0 (Week 16)  
**Architecture:** Middleware-first (like Helicone) but token-intelligence focused  
**Target:** RAG and agent system developers

---

## v0.1: Middleware Foundation (2 weeks)

**Goal:** Build middleware interception layer and basic storage/query infrastructure.

### Deliverables

- ✅ Middleware interception for LangChain
- ✅ Middleware interception for LlamaIndex
- ✅ Raw API proxy support
- ✅ Request/response capture (tokens + latency)
- ✅ Basic prompt categorization
- ✅ ClickHouse database setup and storage
- ✅ Basic query APIs (Python)
- ✅ Simple OTEL metrics export
- ✅ Documentation + examples

### Key Features

**Middleware Interception:**
```python
# LangChain integration
from openanchor.integrations.langchain import OpenAnchorMiddleware
chain = my_chain | OpenAnchorMiddleware(database="clickhouse://localhost")

# LlamaIndex integration
from openanchor.integrations.llamaindex import OpenAnchorCallback
query_engine.run(query, callbacks=[OpenAnchorCallback()])

# Raw proxy
from openanchor import OpenAnchorProxy
response = proxy.call(model="gpt-4", messages=[...])
```

**Data Capture:**
```python
# Each LLM call captures:
{
  timestamp: "2026-07-15T10:00:00Z",
  request: {
    prompt: "...",
    model: "gpt-4",
    provider: "openai"
  },
  response: {
    tokens: {input: 3200, output: 450},
    latency_ms: 1800,
    ttft_ms: 450
  },
  metadata: {...}
}
```

**Basic Queries:**
```python
analyzer = OpenAnchorClient(database="clickhouse://localhost")

# Total tokens by session
stats = analyzer.get_session_stats(session_id="session_123")

# Tokens by model
model_usage = analyzer.get_tokens_by_model()

# Latency analysis
latencies = analyzer.get_latency_stats()
```

### Tasks

1. **Middleware framework**
   - Abstract middleware interface
   - LangChain integration
   - LlamaIndex integration
   - Raw API proxy mode
   - Request/response capture
   - Minimal latency overhead (<5ms)

2. **Prompt categorization (v0.1 basic)**
   - Heuristic-based categorization
   - Categories: code, reasoning, retrieval, creative, analysis, etc
   - Simple rules (prompt length, keywords, structure)

3. **Database setup**
   - ClickHouse schema design
   - Event storage
   - Data indexing for queries
   - Compression for efficiency

4. **Query APIs**
   - Session statistics
   - Model/provider breakdown
   - Latency metrics
   - Basic filtering

5. **OTEL export (basic)**
   - Token metrics
   - Latency metrics
   - Simple gauge exports

6. **Documentation**
   - Middleware integration guide
   - Database setup guide
   - Query API examples
   - Basic examples

### Success Criteria

- ✅ Middleware captures all LLM calls with <5ms overhead
- ✅ Request + response data stored correctly
- ✅ Token counts match PyTokenCalc/official counts
- ✅ Query APIs functional and <1s latency
- ✅ Basic categorization works
- ✅ OTEL export functional
- ✅ Examples runnable (LangChain, LlamaIndex)
- ✅ 90%+ test coverage

### Timeline

```
Day 1-2: Middleware framework + LangChain integration
Day 3: LlamaIndex integration + raw proxy
Day 4-5: Database schema + storage
Day 6-7: Query APIs + categorization
Day 8-9: OTEL export + examples
Day 10-14: Testing + documentation + polish
```

---

## v0.2: Token Intelligence (3 weeks)

**Goal:** Implement 6-dimensional token attribution and pattern detection.

### Deliverables

- ✅ Token attribution engine (6 dimensions)
- ✅ Request/response breakdown analysis
- ✅ Anomaly detection (spikes, drift)
- ✅ Trend analysis (growth rates, seasonality)
- ✅ Operation-type breakdown (retrieval, reasoning, etc)
- ✅ Prompt efficiency ranking
- ✅ Advanced query APIs
- ✅ Pattern streaming via OTEL

### Key Features

**Token Attribution (6 Dimensions):**
```python
breakdown = analyzer.get_attribution_breakdown(call_id="xyz")
# Returns:
{
  "when": {
    "request_phase": 3200,
    "response_phase": 450
  },
  "where": {
    "system_prompt": 500,
    "user_input": 1200,
    "retrieval_context": 1500,
    "overhead": 0
  },
  "how": {
    "retrieval_top_5_docs": 800,
    "retrieval_semantic_search": 700
  },
  "which": {
    "prompt_template": "rag_analyzer_v2",
    "prompt_category": "retrieval"
  },
  "session_phase": {
    "session": "project_q3",
    "phase": "analysis"
  },
  "why": {
    "patterns": ["retrieval_heavy", "growth_trend"],
    "recommendation": "Improve ranking; save 40%"
  }
}
```

**Pattern Detection:**
```python
patterns = analyzer.detect_patterns(session_id="project_q3")
# Returns:
{
  "anomalies": [
    {"date": "2026-07-10", "tokens": 8000, "vs_baseline": 3000, "reason": "spike"}
  ],
  "trends": [
    {"metric": "tokens_per_session", "trend": "up", "rate": "15%/week"}
  ],
  "drift": [
    {"type": "prompt_length", "change": "+25%", "correlation": "token_growth"}
  ]
}
```

**Prompt Efficiency:**
```python
efficiency = analyzer.rank_prompts_by_efficiency()
# Returns:
[
  {"prompt": "rag_analyzer_v2", "tokens": 4200, "quality": 0.96, "rank": 1},
  {"prompt": "rag_analyzer_v1", "tokens": 6100, "quality": 0.94, "rank": 2}
]
```

### Tasks

1. **Attribution engine**
   - Token breakdown algorithms
   - Component inference (system, user, context, overhead)
   - Accuracy validation
   - Handle edge cases

2. **Anomaly detection**
   - Baseline calculation (mean, σ)
   - Spike detection (>2σ)
   - Context inflation detection
   - Quality degradation detection

3. **Trend analysis**
   - Growth rate calculation
   - Time-series analysis
   - Correlation detection
   - Seasonality patterns

4. **Operation-type analysis**
   - Categorize operations (retrieval, reasoning, parsing, etc)
   - Track costs per operation
   - Efficiency ranking

5. **Prompt efficiency**
   - Compare prompt versions
   - Correlate with quality
   - Identify over-engineered prompts
   - Efficiency frontier

6. **Advanced queries**
   - Time-range queries
   - Multi-dimension filtering
   - Aggregations
   - Custom metrics

### Success Criteria

- ✅ Attribution breakdown accurate (100%)
- ✅ Anomaly detection <5% false positive rate
- ✅ Pattern detection identifies real trends
- ✅ Prompt efficiency ranking correct
- ✅ All queries <1s latency
- ✅ 90%+ test coverage

### Timeline

```
Week 1: Attribution engine + algorithms
Week 2: Anomaly detection + trend analysis
Week 3: Operation breakdown + prompt efficiency
Week 4: Query APIs + OTEL streaming + testing
```

---

## v0.3: Optimization Engine (4 weeks)

**Goal:** Generate actionable optimization recommendations.

### Deliverables

- ✅ Optimization opportunity detection
- ✅ Token savings estimation
- ✅ Root cause analysis
- ✅ Prioritized recommendations
- ✅ Session/phase breakdown
- ✅ A/B testing framework (preliminary)
- ✅ Full OTEL integration
- ✅ Grafana dashboard templates

### Key Features

**Recommendations with Token Savings:**
```python
recommendations = analyzer.get_recommendations()
# Returns:
[
  {
    "action": "Improve retrieval ranking",
    "component": "retrieval",
    "current_tokens": 1500,
    "estimated_tokens": 900,
    "savings": 600,
    "pct_savings": 40,
    "confidence": 0.95,
    "effort": "medium",
    "description": "12 docs fetched but only 3 relevant; improve ranking"
  },
  {
    "action": "Use simpler prompt for summarization",
    "component": "prompt",
    "savings": 200,
    "pct_savings": 8,
    "confidence": 0.87,
    "effort": "low"
  }
]
```

**Root Cause Analysis:**
```python
root_causes = analyzer.analyze_spike(
    session_id="project_q3",
    date="2026-07-10"
)
# Why did tokens spike on July 10?
# Returns: Analysis of what changed
```

**Session/Phase Breakdown:**
```python
phases = analyzer.get_phase_breakdown(session_id="project_q3")
# Returns:
{
  "discovery": {"tokens": 200000, "pct": 20},
  "analysis": {"tokens": 600000, "pct": 60},
  "synthesis": {"tokens": 200000, "pct": 20}
}
# Insights: Analysis phase uses 3x tokens; recommend parallelization
```

### Tasks

1. **Opportunity detection**
   - Identify inefficiencies
   - Detect waste patterns
   - Find over-engineering
   - Spot redundant operations

2. **Savings estimation**
   - Estimate token reduction per optimization
   - Break-even analysis
   - Risk assessment
   - Confidence scoring

3. **Prioritization**
   - Sort by impact
   - Balance with effort
   - Account for risk
   - ROI-ranked list

4. **Root cause analysis**
   - Why did tokens spike?
   - What component changed?
   - What's the pattern?

5. **A/B testing framework**
   - Define experiment (prompt variant, model, etc)
   - Run on next N calls
   - Compare metrics
   - Detect winner

6. **Full OTEL integration**
   - Stream all metrics and insights
   - Recommendation signals
   - Anomaly alerts
   - Trend notifications

### Success Criteria

- ✅ Detect 10+ optimization types
- ✅ Token savings estimate 90% accuracy
- ✅ Recommendations are actionable
- ✅ Root cause analysis accurate
- ✅ A/B testing framework working
- ✅ OTEL streaming complete

### Timeline

```
Week 1: Opportunity detection + savings estimation
Week 2: Prioritization + root cause analysis
Week 3: A/B testing framework
Week 4: OTEL integration + Grafana templates + testing
```

---

## v0.4: Advanced Features (4 weeks)

**Goal:** Advanced optimization and analysis capabilities.

### Deliverables

- ✅ Complete A/B testing with statistical rigor
- ✅ Gradual rollout support
- ✅ Performance regression detection
- ✅ Advanced categorization (ML-based)
- ✅ Conditional routing recommendations
- ✅ Historical benchmarking
- ✅ Custom metric support

### Features

**A/B Testing:**
```python
experiment = analyzer.create_ab_test(
    name="prompt_v2_test",
    variant_a="prompt_v1",
    variant_b="prompt_v2",
    sample_size=1000,
    metric="quality"
)
result = experiment.wait_for_completion()
# Statistical significance testing, auto-winner detection
```

**Gradual Rollout:**
```python
rollout = analyzer.create_rollout(
    experiment_id="xyz",
    schedule=[
        {percentage: 0.10, duration: "1 day"},
        {percentage: 0.50, duration: "2 days"},
        {percentage: 1.00, duration: "1 day"}
    ]
)
# Auto-monitors, rolls back if regression detected
```

**Advanced Categorization:**
- ML-based prompt understanding
- Intent detection
- Complexity scoring
- Optimal model recommendation per category

### Timeline

```
Week 1: A/B testing framework
Week 2: Gradual rollout + regression detection
Week 3: Advanced categorization + routing
Week 4: Testing + documentation
```

---

## v1.0: Production Ready (3 weeks)

**Goal:** Enterprise-grade stability, security, and performance.

### Deliverables

- ✅ Multi-tenant support
- ✅ Security (encryption, RBAC, audit logs)
- ✅ Performance optimization (<50ms queries)
- ✅ Monitoring and alerting
- ✅ Comprehensive documentation
- ✅ Enterprise features

### Tasks

1. **Multi-tenancy**
   - Data isolation per tenant
   - Per-tenant configuration
   - Audit logging
   - RBAC

2. **Security**
   - Encryption at rest
   - Encryption in transit
   - API key management
   - Audit trails
   - GDPR compliance baseline

3. **Performance**
   - Query optimization
   - Caching strategy
   - Batch operations
   - Async processing

4. **Monitoring**
   - Health checks
   - SLA monitoring
   - Error tracking
   - Performance dashboards

5. **Documentation**
   - API reference (100% coverage)
   - Deployment guide
   - Best practices
   - Troubleshooting
   - Architecture documentation

### Timeline

```
Week 1: Multi-tenancy + security
Week 2: Performance + monitoring
Week 3: Documentation + final polish
```

---

## Timeline Summary

```
v0.1 (Middleware)   ▓▓▓▓ Week 1-2     (foundation)
v0.2 (Intelligence) ▓▓▓▓▓ Week 3-5    (token analysis)
v0.3 (Optimization) ▓▓▓▓▓▓ Week 6-9   (recommendations)
v0.4 (Advanced)     ▓▓▓▓▓▓ Week 10-13 (advanced features)
v1.0 (Production)   ▓▓▓ Week 14-16   (enterprise ready)
                    ──────────────────
Total                    16 weeks
```

---

## Architecture Milestones

### v0.1: Can Intercept and Store
- ✅ Middleware working
- ✅ Data persisted in database
- ✅ Basic query APIs
- ✅ Users can ask: "How many tokens did this session use?"

### v0.2: Can Understand Patterns
- ✅ Token attribution working
- ✅ Anomaly detection working
- ✅ Users can ask: "Where did tokens go?" and "What changed?"

### v0.3: Can Recommend
- ✅ Recommendations working
- ✅ Users can ask: "What should I optimize?" and get actionable answers

### v0.4: Can Experiment
- ✅ A/B testing working
- ✅ Users can safely test optimizations

### v1.0: Production Ready
- ✅ Multi-tenant, secure, performant
- ✅ Ready for enterprise deployment

---

## Success Metrics (v1.0 Target)

| Metric | Target | Why |
|--------|--------|-----|
| Middleware latency | <5ms overhead | Transparent to users |
| Token accuracy | 100% vs official | Verify against PyTokenCalc |
| Database queries | <1s latency | Responsive analysis |
| Categorization accuracy | 95%+ | Reliable pattern detection |
| Recommendation accuracy | 90%+ token savings when implemented | Actionable insights |
| Pattern detection | <5% false positives | Trustworthy alerts |
| Uptime | 99.9% | Production grade |
| Docs coverage | 100% | Easy adoption |

---

**Last Updated:** 2026-07-15  
**Author:** Georgi Mammen Mullassery  
**Status:** LOCKED (Correct middleware architecture)  
**License:** MIT
