# Architecture Boundaries: PyTokenCalc ↔ OpenAnchor

**Critical:** This document defines the permanent, non-negotiable architectural boundary between PyTokenCalc and OpenAnchor. Both projects evolve independently within these boundaries.

---

## The Hierarchy

```
┌──────────────────────────────────────────────────────────────┐
│                      Your Applications                        │
│                  (LangChain, Claude Code, etc)                │
└─────────────────────────────▲───────────────────────────────┘
                              │
                    LLM Calls + Observability
                              │
         ┌────────────────────┴────────────────────┐
         │                                         │
┌────────┴─────────────────────────────┐  ┌──────┴──────────────────────┐
│         OpenAnchor                   │  │   Your Code/Frameworks       │
│  (Intelligence Layer)                │  │                              │
│                                      │  │ Uses PyTokenCalc for:        │
│  • Attribution                       │  │ - Count tokens              │
│  • Pattern detection                 │  │ - Route by cost             │
│  • Trend analysis                    │  │ - Enforce budgets           │
│  • Recommendations                   │  │                              │
│  • Observability export              │  │ (Direct PyTokenCalc users)  │
│                                      │  │                              │
└────────┬──────────────────────────────┘  └──────┬──────────────────────┘
         │                                        │
         │          PyTokenCalc Events             │
         │  (Token counts + metadata)             │
         │                                        │
         └────────────────────┬────────────────────┘
                              │
            ┌─────────────────┴──────────────────┐
            │                                    │
     ┌──────┴──────────────────────┐  ┌─────────┴───────────────┐
     │     PyTokenCalc              │  │   LLM Provider APIs     │
     │  (Accounting Layer)           │  │                        │
     │                              │  │ • OpenAI (tiktoken)    │
     │  • Token counting            │  │ • Anthropic            │
     │  • Provider integration      │  │ • Google Gemini        │
     │  • Local + cached counting   │  │ • Llama/Mistral (HF)   │
     │  • Exact counts + breakdown  │  │ • Groq, DeepInfra, etc │
     │                              │  │                        │
     └─────────────────────────────┘  └────────────────────────┘
```

---

## Responsibility Matrix

### PyTokenCalc's ONLY Job: Count Total Tokens

| Question | Answer | Who Answers |
|----------|--------|-------------|
| "How many total tokens did this use?" | **INT** | **PyTokenCalc** ✅ |
| "How many input vs output tokens?" | INT + INT | **PyTokenCalc** ✅ |
| "Tokens per modality (text/image)?" | BREAKDOWN | **PyTokenCalc** ✅ |
| "What's the provider?" | STRING | **PyTokenCalc** ✅ |
| "What's the exact model?" | STRING | **PyTokenCalc** ✅ |

### OpenAnchor's Job: Explain Those Total Tokens

| Question | Answer | Who Answers |
|----------|--------|-------------|
| "HOW were tokens distributed?" | ATTRIBUTION* | **OpenAnchor** ✅ |
| "System prompt vs context vs user input?" | BREAKDOWN | **OpenAnchor** ✅ |
| "WHY those tokens?" | EXPLANATION | **OpenAnchor** ✅ |
| "Did anything change?" | PATTERNS | **OpenAnchor** ✅ |
| "Is it growing?" | TRENDS | **OpenAnchor** ✅ |
| "What should we do?" | RECOMMENDATIONS | **OpenAnchor** ✅ |

*Attribution = Breaking down TOTAL tokens by component (system prompt, context, user input, etc). PyTokenCalc provides the TOTAL; OpenAnchor explains how it was used.

### What NEITHER Does

| Question | Answer | Who Answers |
|----------|--------|-------------|
| "What's the cost?" | $ amount | Neither (user calculates) |
| "Should I switch models?" | YES/NO | Neither (user decides) |
| "Alert me when it spikes" | ⚠️ notification | Neither (platform does) |
| "Show me on dashboard" | 📊 visual | Neither (Grafana/Langfuse) |

---

## Data Flow: Token → Intelligence

```
┌─────────────────────────────────────────────────────────┐
│ Your LLM Call (LangChain, etc)                          │
│ Input: "Analyze this code review..."                    │
└────────────────────┬────────────────────────────────────┘
                     │
          ┌──────────▼──────────────────────┐
          │  1. PyTokenCalc.count_tokens()  │
          │  ├─ Input: model, prompt, ctx  │
          │  └─ Output: exact token count  │
          └──────────┬───────────────────────┘
                     │
       ┌─────────────▼──────────────────────┐
       │ Token Count Event Generated:       │
       │ (PyTokenCalc responsibility)       │
       │ {                                  │
       │   input_tokens: 3200,    ← TOTAL  │
       │   output_tokens: 450,    ← TOTAL  │
       │   by_modality: {text: 3500, ...}, │
       │   model: "claude-3-5-sonnet",     │
       │   provider: "anthropic",           │
       │   timestamp: "2026-07-15T10:00Z"   │
       │ }                                  │
       │ NOTE: No breakdown by component   │
       │ (system vs context vs user input) │
       └─────────────┬──────────────────────┘
                     │
          ┌──────────▼──────────────────────┐
          │  2. OpenAnchor.analyze()        │
          │  ├─ Input: Token event         │
          │  └─ Output: Intelligence       │
          └──────────┬───────────────────────┘
                     │
       ┌─────────────▼──────────────────────────────────────┐
       │ Intelligence Enrichments Stored:                  │
       │ (OpenAnchor writes 8+ tables to shared DB)        │
       │                                                    │
       │ 1. Token Attribution (6-Dimensional):             │
       │    ├─ system_prompt: 500 tokens                   │
       │    ├─ user_input: 1200 tokens                     │
       │    ├─ retrieval_context: 1500 tokens              │
       │    ├─ model_overhead: 0 tokens                    │
       │    ├─ conversation_history: 0 tokens              │
       │    └─ response_generation: 450 tokens             │
       │                                                    │
       │ 2. Prompt Intelligence:                           │
       │    ├─ prompt_id: "abc123"                         │
       │    ├─ prompt_category: "code_review"              │
       │    ├─ prompt_version: "v2"                        │
       │    ├─ prompt_complexity_score: 0.73               │
       │    └─ expected_efficiency_baseline: 4500 tokens   │
       │                                                    │
       │ 3. Operational Breakdown (WHERE):                 │
       │    ├─ pdf_extraction: 1200 tokens                 │
       │    ├─ retrieval_search: 300 tokens                │
       │    └─ mcp_overhead: 0 tokens                      │
       │                                                    │
       │ 4. Session & Phase Tracking:                      │
       │    ├─ session_id: "project_q3"                    │
       │    ├─ phase_id: "analysis_phase_2"                │
       │    ├─ phase_token_budget: 600000 tokens           │
       │    └─ phase_tokens_used: 452300 tokens            │
       │                                                    │
       │ 5. Quality Metrics:                               │
       │    ├─ quality_score: 0.96                         │
       │    ├─ latency_ttft_ms: 450                        │
       │    ├─ token_generation_rate: 65 tok/s             │
       │    └─ user_satisfaction: 0.92                     │
       │                                                    │
       │ 6. Pattern Detection:                             │
       │    ├─ anomaly_flags: ["spike", "drift"]           │
       │    ├─ anomaly_severity: 0.78                      │
       │    ├─ trend_direction: "up"                       │
       │    ├─ trend_growth_rate: "15%/week"               │
       │    └─ detected_patterns: ["context_growing", ..] │
       │                                                    │
       │ 7. Efficiency Analysis:                           │
       │    ├─ efficiency_score: 0.81                      │
       │    ├─ efficiency_rank: 7 (vs similar prompts)     │
       │    ├─ cost_per_quality_ratio: 0.045 $/quality     │
       │    ├─ comparison_to_baseline: "-12% efficiency"   │
       │    └─ improvement_opportunity_flag: true          │
       │                                                    │
       │ 8. Recommendations:                               │
       │    ├─ recommended_action: "Improve retrieval"     │
       │    ├─ token_savings_estimate: 600 tokens          │
       │    ├─ confidence_score: 0.95                      │
       │    ├─ implementation_difficulty: "medium"         │
       │    └─ potential_quality_impact: "+2% quality"     │
       │                                                    │
       │ 9. Root Cause Analysis:                           │
       │    ├─ root_cause_component: "retrieval_context"   │
       │    ├─ root_cause_hypothesis: "12 docs fetched.."  │
       │    ├─ supporting_evidence: [metrics]              │
       │    └─ confidence_in_diagnosis: 0.88               │
       │                                                    │
       │ 10. Multi-Dimensional Context:                    │
       │    ├─ operation_type: "retrieval"                 │
       │    ├─ operation_subtype: "semantic_search"        │
       │    ├─ correlation_with_quality: 0.73              │
       │    ├─ correlation_with_latency: 0.82              │
       │    └─ seasonal_patterns: [pattern data]           │
       │                                                    │
       │ 11. A/B Testing & Comparison:                     │
       │    ├─ variant_id: "v2"                            │
       │    ├─ control_vs_treatment: "treatment"           │
       │    ├─ comparison_to_similar: "+8% efficiency"     │
       │    ├─ statistical_significance: 0.96              │
       │    └─ improvement_delta: 340 tokens               │
       │                                                    │
       └─────────────┬──────────────────────────────────────┘
                     │
       ┌─────────────▼──────────────────────┐
       │  3. Export to Platforms:           │
       │  ├─ Grafana dashboard              │
       │  ├─ Langfuse observability         │
       │  ├─ OpenTelemetry signals          │
       │  └─ Your custom system             │
       └────────────────────────────────────┘
```

---

## The Red Lines: What NEVER Crosses

### PyTokenCalc → OpenAnchor (ALLOWED)
✅ Token counts flow from PyTokenCalc to OpenAnchor  
✅ Metadata flows (model, provider, timestamp)  
✅ This is the ONLY data dependency  

### OpenAnchor → PyTokenCalc (FORBIDDEN)
❌ OpenAnchor never calls back into PyTokenCalc  
❌ OpenAnchor never modifies token counts  
❌ OpenAnchor never caches/stores tokens  

### PyTokenCalc vs OpenAnchor Features (FORBIDDEN)
❌ PyTokenCalc never detects patterns  
❌ PyTokenCalc never provides recommendations  
❌ PyTokenCalc never integrates with platforms  

❌ OpenAnchor never counts tokens  
❌ OpenAnchor never manages APIs  
❌ OpenAnchor never caches token values  

### Both vs Other Systems (FORBIDDEN)
❌ Neither implements optimization logic  
❌ Neither creates dashboards  
❌ Neither sends alerts  
❌ Neither makes final decisions  

---

## Integrated Deployment: OpenAnchor Uses PyTokenCalc's Database

**CRITICAL ARCHITECTURAL TRUTH:** OpenAnchor does NOT have its own database. It is a pure **analysis and enrichment layer** that reads from and writes enrichments to **PyTokenCalc's database**.

- **PyTokenCalc:** Middleware + Database (self-contained, works alone)
- **OpenAnchor:** Middleware + Analysis (depends on PyTokenCalc's database)

### Deployment Scenarios

**Scenario 1: PyTokenCalc Only (Standalone)**
```
Your Application
    ↓
PyTokenCalc Middleware
    ├─ Counts tokens (via API, local cache, or repeated calls)
    ├─ Stores token events in its database
    └─ Handles provider switching + reconciliation
    ↓
PyTokenCalc's Database (owned and maintained by PyTokenCalc)
├─ token_events (raw data)
│  ├─ timestamp, model, provider
│  ├─ input_tokens, output_tokens
│  ├─ latency, metadata
│  └─ ... (PyTokenCalc owns this storage)
```

**Scenario 2: OpenAnchor + PyTokenCalc (Integrated)**
```
Your Application
    ↓
OpenAnchor Middleware
    ├─ Intercepts request/response
    ├─ Calls PyTokenCalc for accurate counts
    └─ Stores enrichments in PyTokenCalc's database
    ↓
PyTokenCalc Middleware
    ├─ Provides token counts
    ├─ Stores raw events
    └─ Handles reconciliation
    ↓
PyTokenCalc's Database (shared by both, managed by PyTokenCalc)
├─ PyTokenCalc Storage (owned by PyTokenCalc):
│  └─ token_events (raw token data)
│
└─ OpenAnchor Enrichments (owned by OpenAnchor, stored in same DB):
   ├─ token_attribution (6D breakdown, references token_events)
   ├─ prompt_catalog (categorization)
   ├─ pattern_detections (anomalies, trends, drift)
   ├─ recommendations (optimization opportunities)
   ├─ quality_metrics (latency, user scores)
   ├─ operation_breakdown (retrieval, reasoning, etc)
   ├─ efficiency_scores (prompt rankings)
   └─ root_cause_analysis (spike investigation)

✅ PyTokenCalc owns storage and reconciliation
✅ OpenAnchor owns analysis and enrichment
✅ Single database instance (no duplication)
✅ Rich integrated queries (join PyTokenCalc + OpenAnchor tables)
✅ OpenAnchor is optional—PyTokenCalc works standalone
```

### Database Schema (Integrated)

**PyTokenCalc Owns:**
```
token_events (table owned by PyTokenCalc):
  id, timestamp, session_id, request_id,
  model, provider, context_window, max_output,
  input_tokens, output_tokens, by_modality,
  latency_ms, ttft_ms, cost_base_rate,
  metadata

-- PyTokenCalc creates this table and owns the schema
-- OpenAnchor ONLY reads from this table
```

**OpenAnchor Adds** (to the same database that PyTokenCalc maintains):
```
token_attribution (table created by OpenAnchor):
  request_id, timestamp,
  system_prompt_tokens, user_input_tokens,
  retrieval_context_tokens, model_overhead_tokens,
  response_generation_tokens,
  attribution_confidence, attribution_method

prompt_catalog (table created by OpenAnchor):
  prompt_id, prompt_hash, first_seen,
  prompt_category, prompt_complexity_score,
  prompt_version, prompt_template_name

pattern_detections (table created by OpenAnchor):
  detection_id, timestamp, session_id,
  pattern_type (anomaly/trend/drift/efficiency),
  pattern_description, severity_level,
  affected_component, supporting_metrics

recommendations (table created by OpenAnchor):
  recommendation_id, timestamp, session_id,
  action_description, token_savings_estimate,
  confidence_score, effort_level, priority_rank,
  component_affected, implementation_notes

quality_metrics (table created by OpenAnchor):
  request_id, timestamp,
  latency_ttft_ms, token_generation_rate,
  user_satisfaction_score, quality_score,
  correlation_with_tokens

operation_breakdown (table created by OpenAnchor):
  request_id, operation_type, operation_subtype,
  operation_tokens, operation_duration_ms,
  operation_success_flag, operation_result_tokens

efficiency_scores (table created by OpenAnchor):
  prompt_id, efficiency_rank, efficiency_score,
  cost_per_quality_ratio, comparison_to_baseline,
  improvement_opportunity_detected

root_cause_analysis (table created by OpenAnchor):
  anomaly_id, investigation_timestamp,
  root_cause_component, root_cause_hypothesis,
  supporting_evidence, confidence_in_diagnosis,
  recommended_remediation

-- OpenAnchor creates these tables in the SAME database as PyTokenCalc maintains
-- All tables are in one database instance
-- OpenAnchor READS from token_events (PyTokenCalc's table)
-- OpenAnchor WRITES to its own enrichment tables
```

### Query Examples (Integrated View)

**Example 1: Complete Call Analysis**
```
Query across PyTokenCalc (token_events) + OpenAnchor enrichment tables:
  - Token counts from token_events
  - Attribution breakdown from token_attribution
  - Detected patterns from pattern_detections
  - Recommendations from recommendations table
  WHERE session_id = 'project_q3'
```

**Example 2: Session Breakdown (tokens + patterns + recommendations)**
```
Query:
  - SUM(input_tokens + output_tokens) from token_events
  - Count of calls
  - AVG(retrieval_context_tokens) from token_attribution
  - Distinct patterns detected
  - Potential token savings from recommendations
  GROUP BY session_id
```

**Example 3: Efficiency vs Quality**
```
Query:
  - Prompt category from prompt_catalog
  - Call count from token_events
  - Average tokens (input + output)
  - Average quality score from quality_metrics
  - Efficiency rank and ratio from efficiency_scores
  GROUP BY prompt_category
```

### Integration Points

**PyTokenCalc writes:**
- Raw token counts (accurate, provider-specific)
- Metadata (model, provider, latency)
- Session/call tracking

**OpenAnchor reads from:**
- token_events (PyTokenCalc data)
- Enriches with 6-dimensional attribution
- Analyzes patterns
- Generates recommendations
- Stores all in same database

**Both query:**
- Shared tables for analysis
- No API calls between projects
- Database is the integration point

### Configuration

**When deploying OpenAnchor (UNIFIED):**

```python
# Install: pip install openanchor
# PyTokenCalc is automatically included as a dependency

from openanchor import OpenAnchor

# Single unified setup (specify database connection)
openanchor = OpenAnchor(
    database_url="your-database-connection-string"
)

# Behind the scenes:
# 1. OpenAnchor initializes its bundled PyTokenCalc instance
# 2. PyTokenCalc creates token_events storage in the database
# 3. OpenAnchor creates its enrichment tables in the SAME database
# 4. Middleware handles both interception AND token counting
```

**When deploying PyTokenCalc standalone (Without OpenAnchor):**

```python
# Install: pip install pytokencalc
# Use PyTokenCalc alone (no OpenAnchor)

from pytokencalc import PyTokenCalc

pytokencalc = PyTokenCalc(
    database_url="your-database-connection-string"
)
# Stores tokens, handles reconciliation via repeated API calls
# No enrichment/analysis tables created
```

**Key Deployment Model:**
- **pip install pytokencalc** → Standalone, works without OpenAnchor (OpenAnchor is OPTIONAL)
- **pip install openanchor** → Automatically includes PyTokenCalc as a dependency (PyTokenCalc is REQUIRED)
- Both use the same database (managed by PyTokenCalc)
- OpenAnchor cannot be used without PyTokenCalc
- PyTokenCalc can be used without OpenAnchor

### Cost & Operational Implications

| Aspect | PyTokenCalc Only | PyTokenCalc + OpenAnchor |
|--------|------------------|--------------------------|
| Database instances | 1 | 1 (same database) |
| Storage (1M events) | ~500MB | ~1.5GB (token_events + enrichments) |
| Query latency | <1s | <1s (both in same DB) |
| Operational overhead | Minimal | Low (just added tables) |
| Data sync complexity | None | None (co-located) |
| Infrastructure cost | $X/month | $X/month (single instance, larger) |
| OpenAnchor storage cost | N/A | Included in PyTokenCalc DB |

**Key Point:** OpenAnchor does NOT increase operational complexity because it doesn't manage its own database. It adds tables to PyTokenCalc's database. The infrastructure cost is essentially the same, just slightly larger to hold enrichment tables.

---

## Provider Abstraction: Why PyTokenCalc Stays Separate

**Critical Design Principle:** OpenAnchor COULD count tokens (it sees request + response), but it SHOULD NOT. Here's why.

### The Real-World Problem

Users change LLM providers **constantly and frequently**:

```
Timeline of a Real Application:

Day 1:   Using Ollama locally
         └─ Need Ollama tokenization

Day 2:   Switching to AWS Bedrock
         └─ Need Bedrock tokenization (different API, different counting)

Day 3:   Switching to Claude official API
         └─ Need Anthropic tokenization (yet another approach)

Day 4:   Switching to GCP Vertex AI
         └─ Need Google tokenization (completely different)

Week 2:  Switching to Groq for speed
         └─ Need Groq tokenization

Month 1: Multi-provider routing (use best provider for each task)
         └─ Need abstraction across multiple providers
```

### Why PyTokenCalc Must Handle All Tokenization

**If OpenAnchor also counted tokens:**

❌ Would duplicate token counting logic with PyTokenCalc  
❌ Would need to implement tokenization for Ollama, AWS, Claude, GCP, Groq, etc.  
❌ Every new provider requires updates in TWO places  
❌ Every bug fix must be done in TWO places  
❌ Users changing providers must update BOTH PyTokenCalc AND OpenAnchor  
❌ Maintenance nightmare  

**With PyTokenCalc as the abstraction layer:**

✅ PyTokenCalc: "Handle tokenization for all providers (Ollama, AWS, Claude, GCP, Groq, etc)"  
✅ OpenAnchor: "Just use PyTokenCalc for accurate counts, I focus on analysis"  
✅ Users change providers: update PyTokenCalc reference (ONE place)  
✅ OpenAnchor works unchanged with any provider  
✅ Clean separation, no duplication  

### Example: Provider Switch Scenario

**Scenario 1: OpenAnchor counts tokens (WRONG)**

```python
# User switches from Ollama to AWS Bedrock
# Day 1 (Ollama):
class OllamaTokenCounter:
    def count(self, prompt):
        # Ollama-specific counting

# Day 2 (Switch to AWS):
❌ Must rewrite PyTokenCalc to handle Bedrock
❌ Must rewrite OpenAnchor to handle Bedrock tokenization
❌ Two codebases to update
❌ High chance of mismatches
```

**Scenario 2: PyTokenCalc abstracts tokens (CORRECT)**

```python
# User switches from Ollama to AWS Bedrock
# Day 1 (Ollama):
tokens = PyTokenCalc.count_tokens(
    model="ollama:llama2",
    prompt="...",
    provider="ollama"
)

# Day 2 (Switch to AWS):
tokens = PyTokenCalc.count_tokens(
    model="claude-3-sonnet",
    prompt="...",
    provider="bedrock"
)

# OpenAnchor UNCHANGED:
analysis = OpenAnchor.analyze(tokens)
# Still works perfectly, no changes needed
```

### What This Means

**PyTokenCalc is the provider abstraction layer:**
- Centralized place for "how to count tokens in provider X"
- Users can swap providers without touching OpenAnchor
- Single source of truth for token counting

**OpenAnchor focuses on insights:**
- Latency analysis (how fast was the request?)
- Token attribution (where did tokens go?)
- Pattern detection (what changed?)
- Recommendations (what to optimize?)

**Separation allows flexibility:**
- Switch providers → update PyTokenCalc config
- Improve analysis → update OpenAnchor logic
- Two concerns, two projects, no duplication

### Why This Matters

From **PyCostAudit failure** → learning:
- Original PyCostAudit tried to do everything (counting + analysis + cost)
- Failed because cost analysis requires attribution (can't do everywhere)
- Split into:
  - **PyTokenCalc:** Universal token counting abstraction
  - **OpenAnchor:** Specialized token intelligence (requires visibility)
- Keep them separate to avoid provider lock-in and duplication

---

## Evolution: Independent But Coordinated

### PyTokenCalc Roadmap (Token Counting)
- v0.8: Cloud API integration (count tokens via API)
- v0.9: Vision/multimodal support
- v1.0: Production hardened
- Future: Add new providers, improve accuracy

### OpenAnchor Roadmap (Intelligence)
- v0.1: Basic attribution + trend tracking
- v0.2: Pattern detection (anomalies)
- v0.3: Observability platform integration
- v0.4: Optimization recommendations
- v1.0: Production hardened

### Compatibility Rules
1. **OpenAnchor always depends on PyTokenCalc** (not vice versa)
2. **PyTokenCalc never knows about OpenAnchor** (no coupling back)
3. **Both use standard data formats** (JSON events, not proprietary)
4. **Integration via PyTokenCalc's public API only** (not internals)

---

## Decision Tree: Which Project?

### Is it about counting tokens?
→ **PyTokenCalc**

### Is it about tokenizer APIs, local vs cloud, caching?
→ **PyTokenCalc**

### Is it about explaining why tokens were used?
→ **OpenAnchor**

### Is it about detecting patterns in token consumption?
→ **OpenAnchor**

### Is it about recommendations for optimization?
→ **OpenAnchor**

### Is it about integrating with Grafana/Langfuse/OTEL?
→ **OpenAnchor**

### Is it about cost calculation?
→ **Neither** (belongs in user code or separate project)

### Is it about automatic optimization?
→ **Neither** (belongs in separate service)

### Is it about budget enforcement?
→ **Mostly PyTokenCalc** (has budget API), but recommendations from OpenAnchor

---

## Example: Complete User Journey

**Scenario:** User wants "alert me when token costs spike"

```
Step 1: Count tokens
├─ User's LLM call
├─ PyTokenCalc.count_tokens() → 3200 tokens
└─ Event sent to OpenAnchor

Step 2: Analyze pattern
├─ OpenAnchor detects: "3200 tokens vs baseline 1500"
├─ Pattern: SPIKE (2.13x normal)
└─ Recommendation: "Context inflation detected"

Step 3: Send to platforms
├─ Export via OpenTelemetry
├─ Dashboard: "Context history 85% of input tokens"
└─ Langfuse: Log anomaly

Step 4: User decides
├─ Sees the spike on Grafana dashboard
├─ Reads the analysis from OpenAnchor
├─ Manually decides: compress history OR move to cheaper model
└─ Implements in their code
```

**Note:** Neither PyTokenCalc nor OpenAnchor made the decision—they provided data and analysis. The user decided.

---

## Commit Philosophy

### For PyTokenCalc Commits
Focus: Token counting accuracy, provider support, performance

```
feat: Add Google Gemini token counting via API
fix: Improve cache hit rate for repeated prompts
perf: Reduce tokenizer initialization time
```

### For OpenAnchor Commits
Focus: Intelligence, patterns, integrations

```
feat: Add context inflation pattern detection
feat: Integrate with OpenTelemetry
fix: Improve attribution accuracy
```

### Cross-Project Commits (RARE)
Only if both change:
```
chore: Update PyTokenCalc dependency to v0.8
```

---

## Testing Philosophy

### PyTokenCalc Tests
- Accuracy: Count matches official tokenizers ✓
- Performance: <100ms for token counting ✓
- Providers: Support all 20+ correctly ✓

### OpenAnchor Tests
- Attribution: Breakdown adds up to total ✓
- Patterns: Detect anomalies correctly ✓
- Integrations: Export to platforms works ✓

### Integration Tests (MINIMAL)
- OpenAnchor correctly consumes PyTokenCalc output
- End-to-end: Token → Analysis → Export

---

## Summary: The Permanent Boundary

```
PyTokenCalc: "I count tokens accurately"
OpenAnchor: "I explain what those tokens mean"

Together they answer:
- HOW many tokens? (PyTokenCalc)
- WHY those tokens? (OpenAnchor)
- WHAT changed? (OpenAnchor)
- WHAT to do? (OpenAnchor + user judgment)
```

**Each project owns its domain completely.**  
**Neither crosses into the other's domain.**  
**Both evolve independently.**  
**Integration is data-only (JSON events).**

---

**Last Updated:** 2026-07-15  
**Authority:** Georgi Mammen Mullassery  
**Status:** Architectural Decision - FINAL
