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
       ┌─────────────▼──────────────────────┐
       │ Intelligence Signals Generated:   │
       │ {                                  │
       │   attribution: {                   │
       │     system_prompt: 500,            │
       │     user_code: 1200,               │
       │     conversation: 1000,            │
       │     overhead: 500                  │
       │   },                               │
       │   patterns: [                      │
       │     "context_growing",             │
       │     "spikes_after_noon"            │
       │   ],                               │
       │   recommendations: [               │
       │     "compress_history",            │
       │     "improve_retrieval"            │
       │   ]                                │
       │ }                                  │
       └─────────────┬──────────────────────┘
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
