# OpenAnchor: Refined Product Strategy (Based on PyCostAudit Learnings)

## Context from PyCostAudit

**Problem Identified:** Claude Code users see "$47/day" but don't know where it's spent:
- 60% from file operations (PDF reads, RAG extraction)
- 25% from MCP server overhead
- 10% from long conversation context
- 5% from model mismatch

**Solution PyCostAudit provides:** Real-time cost attribution by operation type

**What OpenAnchor adds:** Automatic cost-spike interception at runtime (not just tracking)

---

## The Real Cost Drivers (Per PyCostAudit Research)

### 1. **MCP Server Overhead** (HIGHEST PRIORITY) ⭐⭐⭐
- **Cost:** 55,000 tokens before first message with 5 MCP servers connected
- **Current behavior:** All MCP tool schemas loaded on session start
- **Problem:** 90% of tools never used in that session
- **Solution:** Lazy-load only semantically-relevant tool schemas per task
- **Savings:** 46-70% on session start overhead

### 2. **File/Document Processing** (HIGH PRIORITY) ⭐⭐
- **Cost:** 2MB PDF = 97,000 tokens raw; same PDF as Markdown = 20,000 tokens
- **Current behavior:** Raw PDF text injected into context
- **Problem:** No OCR, no structure, no chunking
- **Solution:** Smart extraction (PyMuPDF → Markdown) + semantic chunking + RAG
- **Savings:** 60-80% per document operation

### 3. **Context Bloat from Long Sessions** (HIGH PRIORITY) ⭐⭐
- **Cost:** 50-turn conversation: 15,000 tokens re-transmitted per turn
- **Current behavior:** Full history re-sent as input on every turn
- **Problem:** No compression, no rolling summarization
- **Solution:** Anchored summarization (compress old turns, keep recent)
- **Savings:** 70% on long sessions

### 4. **Model Mismatch** (MEDIUM PRIORITY) ⭐
- **Cost:** Opus 5x more expensive than Sonnet; 80% of tasks don't need Opus
- **Current behavior:** Single model for all tasks
- **Problem:** No task-aware routing
- **Solution:** Classify task complexity → route to cheapest capable model
- **Savings:** 60-75% cost reduction

### 5. **Skill Loading into Context** (NEW GAP) ⭐
- **Cost:** Agent has 20 skills; all definitions loaded every session = 30K tokens
- **Current behavior:** Skills in system prompt always
- **Problem:** Most skills unused in given session
- **Solution:** External skill calling (not context); load only relevant skills
- **Savings:** 60-80% context reduction

---

## Architecture: Cost Interception at Runtime

```
User Prompt
    ↓
[OpenAnchor Runtime]
    ├─ Task Classifier: What kind of task? (code, doc review, pdf analysis, etc.)
    ├─ Spike Detector: Which cost patterns apply? (PDF? MCP? Long context?)
    ├─ Auto-Optimizer: Apply appropriate fixes
    │   ├─ DocIngest (if PDF/doc detected)
    │   ├─ LazyMCP (load only relevant tools)
    │   ├─ SkillLoader (load only relevant skills externally)
    │   ├─ ContextCompressor (if conversation long)
    │   └─ ModelRouter (route to cheapest model)
    ├─ Quality Guardian: Regression test optimization
    └─ CostMeter: Track what was saved
    ↓
Agent Runtime
    ↓
LLM API (with optimized input)
    ↓
[Cost Attribution] → CostMeter reports savings
```

**Key principle:** All optimizations happen BEFORE the LLM sees input. User never knows they're happening; CostMeter reports the savings.

---

## MVP v0.1: Rust Backend + Python/Node SDKs

### Rust Core (High-Performance Cost Interception)
**File:** `/openanchor-rust/`

```
src/
├─ runtime.rs          # Main interception loop
├─ task_classifier.rs  # Detect task type → apply optimizations
├─ spike_detector.rs   # Which cost patterns apply?
├─ optimizers/
│   ├─ doc_ingester.rs        # PDF → OCR → Markdown → chunk → index
│   ├─ mcp_lazy_loader.rs     # Load only semantically relevant tools
│   ├─ skill_loader.rs        # External skill calling (not context)
│   ├─ context_compressor.rs  # Rolling summarization
│   ├─ model_router.rs        # Task complexity → cheapest model
│   └─ cost_calculator.rs     # Real-time cost tracking (reuse PyCostAudit)
├─ quality_guardian.rs # Regression testing on optimizations
└─ cost_meter.rs       # Cost attribution per optimization
```

**Why Rust:**
- Performance-critical: every prompt interception must be <10ms
- Concurrency: handle multiple sessions in parallel
- Reuse PyCostAudit core: `cost_calculator.rs` can import from PyCostAudit

### Python SDK
```python
from openanchor import OpenAnchorRuntime, CostMeter

# Initialize
guard = OpenAnchorRuntime(
    model="claude-3-5-sonnet",
    mcp_servers=["github", "slack", "notion"],  # Lazy-load only relevant
    skills=["CodeReview", "TestGen", "SecurityAudit"],  # External call
    enable_doc_ingestion=True,
    enable_cost_meter=True
)

# Interception happens automatically
response = guard.run_agent_task(
    task="Review this code for security issues",
    context={"file": "src/auth.rs"}  # OpenAnchor auto-handles PDF extraction, etc.
)

# Check what was optimized
print(guard.cost_meter.report())
# Output:
# {
#   "optimizations_applied": ["DocIngest", "LazyMCP", "SkillLoader"],
#   "cost_savings": {
#       "MCP": "46% (8.5K tokens saved)",
#       "DocIngest": "79% (20K tokens saved)",
#       "SkillLoader": "65% (12K tokens saved)"
#   },
#   "total_savings": "62% (40.5K tokens saved)",
#   "estimated_cost_before": "$0.45",
#   "actual_cost_after": "$0.17"
# }
```

### Node.js SDK
```javascript
const { OpenAnchorRuntime } = require("openanchor");

const guard = new OpenAnchorRuntime({
  model: "claude-3-5-sonnet",
  mcpServers: ["github", "slack"],
  skills: ["CodeReview", "TestGen"],
  enableDocIngestion: true,
  enableCostMeter: true
});

const response = await guard.runAgentTask({
  task: "Analyze this PDF for compliance issues",
  context: { filePath: "./report.pdf" }
});

console.log(guard.costMeter.report());
```

---

## The Three Pillars of OpenAnchor

### Pillar 1: Real-Time Cost Attribution (from PyCostAudit)
- Track every operation's cost in real-time
- Show breakdown by type (MCP, PDF, context, model, etc.)
- CostMeter widget shows savings per optimization

### Pillar 2: Automatic Spike Interception (NEW)
- Detect when user is about to trigger a spike
- Apply optimization automatically before LLM call
- Never block the user; optimization is invisible

### Pillar 3: External Skill/Tool Loading (ARCHITECTURAL FIX)
- Skills are NOT loaded into system prompt
- Call skills only when needed (via tool_use)
- Reduce system prompt bloat by 60-80%
- Task classifier determines which skills are relevant

---

## Key Differences from Competitors

| Feature | Claude Code | Deep Agents | Hermes | OpenAnchor |
|---------|-------------|------------|--------|-----------|
| **Real-time cost attribution** | None | None | None | ✅ Per-operation breakdown |
| **Automatic cost-spike interception** | None | Manual config | None | ✅ Auto-detect + fix |
| **MCP lazy loading** | Partial (Tool Search) | None | None | ✅ Full lazy + semantic match |
| **Skill external calling** | Skills in context | Skills in context | Skills in context | ✅ External only |
| **Rust backend** | No | No | No | ✅ High-performance |
| **Model discovery** | None | Manual | None | ✅ CloudModelIntel + OSS provider tracking |
| **Cost savings reporting** | None | None | None | ✅ CostMeter dashboard |
| **PDF auto-RAG** | Manual | Manual | None | ✅ Automatic |
| **Doc content extraction** | None | None | None | ✅ HTML → Markdown, OCR |

---

## MVP v0.1 Scope (First 2 Weeks)

**Must Have:**
1. ✅ **Rust runtime core** — Task classification + spike detection
2. ✅ **DocIngest** — PDF → OCR → Markdown → RAG (60-80% savings)
3. ✅ **LazyMCP** — Load only semantically relevant tools (46-70% savings)
4. ✅ **SkillLoader** — External skill calling, not context (60-80% savings)
5. ✅ **CostMeter UI** — Real-time cost attribution per optimization
6. ✅ **Python SDK** — Easy integration for Claude Code users
7. ✅ **Quality Guardian** — Regression test all optimizations

**Ship in v0.2:**
- Context compression (rolling summarization)
- Model router (task complexity routing)
- Cloud model discovery (pricing tracking)
- Open-source provider discovery

---

## Competitive Positioning

**Tagline:** "Automatic cost optimization for AI agents. No config, 60% savings."

**For Claude Code users:** "OpenAnchor pays for itself in 2 weeks."

**For enterprises:** "Reduce LLM spend from $50K/month to $18K/month without changing code."

**For open-source:** "First platform that intercepts cost spikes at runtime."

---

## Rust Backend Architecture Rationale

**Why Rust for OpenAnchor (vs PyCostAudit's Rust):**

1. **Interception latency critical:** Every prompt must be processed in <10ms
2. **Streaming:** Handle multiple session streams in parallel (async Tokio)
3. **Memory efficiency:** Chunk large PDFs, compress history, without GC pauses
4. **FFI boundary:** Reuse PyCostAudit's Rust cost calculation via PyO3
5. **Deployment:** Embed Rust runtime in Python/Node SDKs without subprocess overhead

**Reuse from PyCostAudit:**
- `cost_tracker.rs` — Real-time cost calculation
- `pricing.rs` — Model pricing database
- `recommender.rs` — Optimization suggestions
- `storage.rs` — SQLite backend for audit logs

---

## Success Metrics (v0.1 Launch)

**Cost Reduction:**
- Average user saves 60% on MCP + DocIngest + SkillLoader
- Typical session: $0.45 → $0.17 cost

**Accuracy:**
- Regression testing prevents quality degradation (<5% threshold)
- Cost calculations match actual LLM API usage

**Adoption:**
- 1K downloads in first month (target)
- 100+ GitHub stars (quality signal)
- Featured on PyCostAudit + AI agent communities

---

## Building on PyCostAudit

**OpenAnchor is NOT a replacement for PyCostAudit.**

Instead:
- **PyCostAudit:** Historical cost tracking & reporting (analytics)
- **OpenAnchor:** Real-time cost interception & optimization (runtime)

**Integration:**
- OpenAnchor's cost calculations feed into PyCostAudit's reporting
- Users can track both: actual spend (PyCostAudit) + what-ifs (OpenAnchor)
- Single Rust cost core shared between both

---

## Timeline

**Week 1:**
- [ ] Rust runtime skeleton
- [ ] DocIngest module (PyMuPDF + Mistral OCR)
- [ ] LazyMCP loader
- [ ] Skeleton quality guardian

**Week 2:**
- [ ] SkillLoader (external calling)
- [ ] CostMeter UI (real-time attribution)
- [ ] Python SDK
- [ ] Regression testing on all optimizations

**Week 3:**
- [ ] Documentation & examples
- [ ] Node.js SDK
- [ ] GitHub Actions CI/CD
- [ ] PyPI release

**Week 4:**
- [ ] Cloud model discovery (pricing tracker)
- [ ] v0.2 features (context compression, model routing)
- [ ] Community feedback & iteration
- [ ] Marketing/launch
