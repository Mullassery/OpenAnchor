# OpenAnchor: Open-Source Stack Architecture

**OpenAnchor is middleware-only.** No custom UI, no new frameworks. Just a cost-optimization layer that works with any agent framework.

---

## Architecture: Four Layers

```
┌────────────────────────────────────────────────────────────────┐
│ Layer 0: Frontend (Chainlit)                                   │
│ ├─ Web UI for agent interaction                               │
│ ├─ Real-time cost meter display                               │
│ ├─ Chat interface for multi-turn conversations                │
│ └─ Optimization recommendations UI                            │
└────────────────────────────────────────────────────────────────┘
                           ▲
                           │
┌────────────────────────────────────────────────────────────────┐
│ Layer 1: OpenAnchor Core (Rust + Python SDKs)                 │
│ ├─ Runtime: Task classifier + spike detectors + optimizers    │
│ ├─ Quality Guardian: Regression testing                        │
│ └─ Integration: Pluggable via interfaces                       │
└────────────────────────────────────────────────────────────────┘
                           ▲
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
┌─────────────────────────────┐  ┌──────────────────────────────┐
│ Layer 2a: Cost Intelligence │  │ Layer 2b: Retrieval Auditing │
│ (PyCostAudit Integration)   │  │ (Pyvectorhound Integration)  │
│                             │  │                              │
│ ├─ Real-time cost calc      │  │ ├─ Component isolation       │
│ ├─ Pricing database         │  │ ├─ Root cause analysis       │
│ ├─ Cost attribution         │  │ ├─ Embedding quality check   │
│ ├─ Recommendation engine    │  │ ├─ Vector search optimization│
│ └─ Historical tracking      │  │ └─ Reranker calibration      │
└─────────────────────────────┘  └──────────────────────────────┘
        ▲                                   ▲
        │                                   │
        └───────────────┬───────────────────┘
                        │
        ┌───────────────┴────────────────┐
        ▼                                ▼
┌─────────────────────────────┐  ┌──────────────────────────────┐
│ Layer 3a: LLM Services      │  │ Layer 3b: Infrastructure     │
│ (Open-Source & APIs)        │  │ (Open-Source Only)           │
│                             │  │                              │
│ ├─ OpenRouter               │  │ ├─ Qdrant (vector DB)        │
│ │  (315+ models)            │  │ ├─ Chroma (vector DB)        │
│ ├─ Ollama (local inference) │  │ ├─ Milvus (vector DB)        │
│ ├─ vLLM (fast inference)    │  │ ├─ PostgreSQL pgvector       │
│ ├─ Mistral OCR              │  │ ├─ Weaviate (vector DB)      │
│ ├─ DSPy (optimization)      │  │ ├─ SQLite (local)            │
│ └─ LiteLLM (model routing)  │  │ ├─ Redis (caching)           │
│                             │  │ ├─ OpenTelemetry (tracing)   │
│                             │  │ └─ Prometheus (metrics)      │
└─────────────────────────────┘  └──────────────────────────────┘
```

---

## Detailed Integrations

### Layer 2a: PyCostAudit Integration

**What:** Real-time cost calculation and attribution

**Your Code Integration:**
```
openanchor-rust/
├─ src/
│  ├─ cost_calculator.rs (REUSE from PyCostAudit)
│  ├─ pricing.rs (REUSE from PyCostAudit)
│  ├─ recommender.rs (REUSE from PyCostAudit)
│  └─ ...

Cargo.toml:
[dependencies]
pycostaudit = { path = "../PyCostAudit/crates/cost-reporter" }
```

**Capabilities:**
- ✅ Track cost per operation (in real-time)
- ✅ Model pricing database (auto-updated)
- ✅ Cost recommendations (use cheaper models)
- ✅ Historical cost tracking (SQLite)
- ✅ Cost attribution (which optimization saved what?)

**Python Wrapper:**
```python
from pycostaudit import CostCalculator, PricingDB

calc = CostCalculator(db_path="~/.openanchor/costs.db")
cost = calc.calculate_operation(
    model="claude-3-5-sonnet",
    tokens_input=1000,
    tokens_output=500
)
print(f"Cost: ${cost:.4f}")
```

---

### Layer 2b: Pyvectorhound Integration

**What:** RAG retrieval diagnostics + optimization

**Your Code Integration:**
```
openanchor-rust/
├─ src/
│  └─ retrieval_auditor.rs (NEW - wraps Pyvectorhound)

Cargo.toml:
[dependencies]
pyvectorhound = { path = "../Pyvectorhound/src" }  # TODO: verify path
```

**Capabilities:**
- ✅ Diagnose why RAG retrieval is failing
- ✅ Component isolation (embedding → vector search → reranker)
- ✅ Root cause analysis (which component is broken?)
- ✅ Recommendations (use different model, adjust reranker, etc.)
- ✅ Cost-quality tradeoffs (cheaper embedding vs accuracy)

**Use Case in OpenAnchor:**
```
When DocIngest engine chunks PDFs + creates embeddings:

1. Send queries through Pyvectorhound diagnostic
2. If retrieval quality <95%:
   ├─ Identify root cause (embedding? vector search? reranker?)
   ├─ Get recommendation (use different model, adjust threshold)
   └─ Calculate cost impact of fix
3. Auto-apply fix if ROI positive
```

**Python Wrapper:**
```python
from pyvectorhound import RAGDiagnostics

diagnostics = RAGDiagnostics(
    vector_db="qdrant",  # or chroma, milvus, weaviate, pgvector
    embedding_model="all-MiniLM-L6-v2"
)

# Diagnose retrieval issue
result = diagnostics.diagnose(
    query="What are cost reduction strategies?",
    ground_truth=["RAG optimization", "token compression"]
)

print(result)
# Output:
# {
#   "root_cause": "embedding_model_weak",
#   "diagnosis": "all-MiniLM-L6-v2 lacks domain knowledge",
#   "recommendation": "Use open-source domain model (e.g., bge-small-en-v1.5)",
#   "cost_impact": "-$0.02/query",
#   "quality_gain": "+8%"
# }
```

---

### Layer 3a: LLM Services (Open-Source & APIs)

#### OpenRouter (Primary)
**What:** API gateway to 315+ models (open-source + proprietary)

**Integration:**
```rust
// In model_router.rs
use openrouter::OpenRouterClient;

let client = OpenRouterClient::new(api_key);
let response = client.complete(
    model_id="meta-llama/llama-2-70b",  // Open-source
    prompt="...",
    cost_budget_cents=100  // Stop if costs exceed
).await?;
```

**Why:** Unified API for all model types + cost control

#### Ollama (Local Inference)
**What:** Run open-source models locally

**Integration:**
```bash
# User runs locally:
ollama run llama2
ollama run mistral
```

```rust
// OpenAnchor detects + uses local
let local_models = ollama::list_running_models()?;
if local_models.contains("llama2") {
    route_to_ollama("llama2")  // Use local, free
} else {
    route_to_openrouter()  // Use API
}
```

#### DSPy (Optimization)
**What:** Structured prompting + automatic optimization

**Integration:**
```python
import dspy

# Auto-optimize task classifier via DSPy
class TaskClassifier(dspy.ChainOfThought):
    def forward(self, prompt):
        return dspy.ChainOfThought("classify_task")(
            prompt=prompt,
            task_types=["code_review", "pdf_analysis", "web_research"]
        )

# DSPy auto-tunes via few-shot learning
classifier = TaskClassifier()
dspy.ChainOfThought.load(classifier, "examples.json")
```

#### LiteLLM (Model Routing)
**What:** Unified interface for routing between models

**Integration:**
```python
import litellm

# Route to cheapest model that meets quality threshold
response = litellm.completion(
    model="router::my-routing-config",  # Custom routing rules
    messages=[...],
    max_tokens=100,
    cost_limit_cents=10
)
```

---

### Layer 3b: Infrastructure (Open-Source Only)

#### Vector Databases
```
Supported (OpenAnchor works with all):
├─ Qdrant (Rust-native, fast)
├─ Chroma (Python, easy local setup)
├─ Milvus (scalable, distributed)
├─ Weaviate (GraphQL interface)
└─ PostgreSQL pgvector (SQL-native)

Integration:
openanchor-rust/src/vector_db/ 
├─ qdrant.rs
├─ chroma.rs
├─ milvus.rs
├─ weaviate.rs
└─ pgvector.rs
```

#### Caching & Storage
```
Redis (optional):
├─ Prompt caching (repeated queries)
├─ Result caching (avoid re-computation)
└─ Distributed deployment

SQLite (default, local):
├─ Cost tracking
├─ Query history
├─ Regression test results
└─ No external dependencies
```

#### Frontend: Dual-Tab Interface (MVP Strategy)

**Two Modes, Same Enterprise**

Enterprises use BOTH depending on the task:

1. **QUICK ANSWERS Mode** (Chainlit) → Interactive troubleshooting, instant feedback
   - Dev asks: "Why is this PDF taking 20K tokens?"
   - Agent: Analyzes, suggests fix, user approves/rejects
   - Speed: Seconds

2. **AUTONOMOUS Mode** (Deep Agents) → Complex workflows, hands-off
   - Dev says: "Optimize all PDF processing costs for the team"
   - Agent: Analyzes all PDFs, recommends fixes, auto-applies safe changes, reports
   - Speed: Minutes to hours (runs overnight)

**Concurrent Execution Model:**

**Alice's Day (Same User, Parallel Workflows):**
```
10:00am: Starts Deep Agents Tab
  └─ "Run 24-hour cost audit on all PDF processing"
  └─ Deep Agent starts autonomous work (will take 2 hours)

10:05am: Switches to Chat Tab
  └─ "Is this RAG retrieval working?"
  └─ Gets instant answer while Deep Agent runs in background

10:15am: Asks in Chat
  └─ "What's the status of the cost audit?"
  └─ Chat queries running Deep Agent → Shows progress

11:30am: Deep Agent finishes (in background)
  └─ Shows $15K/month savings opportunity
  └─ Alice still in Chat Tab asking other questions

12:00pm: Reviews Deep Agent results
  └─ Approves recommendations
  └─ Deep Agent auto-applies safe changes
```

**Architecture Enables Concurrency:**
```
OpenAnchor Unified Backend (Rust Core)
├─ Concurrent Execution Pool
│  ├─ Deep Agent Task #1 (running) → Cost audit
│  └─ Chat Query #2 (running) → Status check
├─ Shared State
│  ├─ Cost Tracker (real-time updates)
│  ├─ Task Queue (prioritized)
│  └─ Results Cache (instant retrieval)
└─ WebSocket Connections
   ├─ Deep Agents Tab (streaming results)
   └─ Chat Tab (live progress updates)
```

**Benefits:**
- ✅ **Non-blocking:** User doesn't wait for autonomous tasks to finish
- ✅ **Parallel execution:** Multiple tasks run simultaneously
- ✅ **Real-time progress:** Chat can query status of running agents
- ✅ **Unified state:** One cost meter for all work
- ✅ **Enterprise workflow:** "Start audit at 10am, continue with other work, review results at 2pm"

---

**Tab 1: Chainlit Chat Interface (Quick Answers)**
```python
import chainlit as cl
from openanchor import OpenAnchorRuntime

guard = OpenAnchorRuntime()

@cl.on_message
async def main(message: cl.Message):
    # Run agent task through OpenAnchor
    response = await guard.run_task(message.content)
    
    # Display response
    await cl.Message(content=response).send()
    
    # Display cost breakdown
    cost_report = guard.cost_meter.report()
    await cl.Message(
        content=f"**Cost Breakdown:**\n{cost_report}",
        author="CostMeter"
    ).send()
```

**Tab 2: Deep Agents (Autonomous Workflows)**
```python
from langgraph.graph import StateGraph
from openanchor import OpenAnchorRuntime

guard = OpenAnchorRuntime()

# Define autonomous agent workflow
workflow = StateGraph()
workflow.add_node("analyze", lambda state: guard.analyze_task(state["prompt"]))
workflow.add_node("plan", lambda state: guard.create_plan(state["analysis"]))
workflow.add_node("execute", lambda state: guard.execute_plan(state["plan"]))
workflow.add_node("verify", lambda state: guard.verify_results(state["execution"]))
workflow.add_node("report", lambda state: guard.cost_meter.report())

# Add edges for autonomous execution
workflow.add_edge("analyze", "plan")
workflow.add_edge("plan", "execute")
workflow.add_edge("execute", "verify")
workflow.add_edge("verify", "report")

# Compile to autonomous agent
app = workflow.compile()

# Agent runs end-to-end without waiting for user input
result = app.invoke({"prompt": "Deploy new feature, optimize costs, verify quality"})
```

**Unified Tab Wrapper (HTML/FastAPI)**
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

# Serve HTML with tabs
@app.get("/")
async def root():
    return HTMLResponse("""
    <html>
        <head><title>OpenAnchor</title></head>
        <body>
            <div class="tabs">
                <button onclick="showTab('chainlit')">💬 Chat (Chainlit)</button>
                <button onclick="showTab('deepagent')">🔄 Workflow (Deep Agents)</button>
            </div>
            <div id="chainlit" class="tab-content">
                <iframe src="http://localhost:8001" style="width:100%;height:600px;"></iframe>
            </div>
            <div id="deepagent" class="tab-content" style="display:none;">
                <iframe src="http://localhost:8002" style="width:100%;height:600px;"></iframe>
            </div>
            <script>
                function showTab(name) {
                    // Hide all
                    document.querySelectorAll('.tab-content').forEach(x => x.style.display='none');
                    // Show selected
                    document.getElementById(name).style.display='block';
                }
            </script>
        </body>
    </html>
    """)
```

**MVP Architecture:**
```
OpenAnchor Unified Backend (Rust Core)
├─ Port 8000: Main UI (Tab Switcher)
│  ├─ Tab 1: Chainlit (port 8001) ← Quick Answers (Interactive)
│  └─ Tab 2: Deep Agents (port 8002) ← Autonomous Work (Hands-Off)
├─ Shared Cost Meter Dashboard
└─ Real-time Cost Tracking (PyCostAudit)
```

**User Personas & Tab Choice:**

| Use Case | Tab | Example | Auto-Cost Savings |
|----------|-----|---------|------------------|
| "Review this code" | Chainlit | Paste code → Get feedback → Done | 60% |
| "Deploy, optimize, verify" | Deep Agents | Set goal → Agent runs autonomously | 60% |
| "Chat for ideas" | Chainlit | Interactive brainstorming | 60% |
| "24/7 cost optimization" | Deep Agents | Monitor + auto-fix spikes | 60% |

**Benefits:**
- ✅ **Chainlit Tab:** Quick answers, instant feedback, user in control
- ✅ **Deep Agents Tab:** Autonomous execution, fire-and-forget, complex workflows
- ✅ **Same Backend:** Unified cost tracking + optimization
- ✅ **Users pick interface:** No lock-in to either approach
- ✅ **Minimal frontend code:** FastAPI tab switcher + iframe embedding
- ✅ **Both get 60% cost savings:** Automatic regardless of interface

#### Observability (OpenTelemetry)
```python
from opentelemetry import trace, metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Export metrics to Prometheus
metrics_exporter = PrometheusMetricReader()

# Export traces to Jaeger (or stdout for local dev)
jaeger_exporter = JaegerExporter(agent_host_name="localhost")

# OpenAnchor exports:
# ├─ Cost per operation (metric)
# ├─ Latency per optimizer (trace)
# ├─ Quality regression test results (metric)
# └─ Model routing decisions (trace)
```

---

## OSS Stack Summary

```
OpenAnchor Stack (No Proprietary Tools)

Compute:
├─ Rust Core (high-performance)
├─ Python SDKs (user-friendly)
└─ Node.js SDKs (JavaScript support)

Cost Intelligence:
├─ PyCostAudit (real-time tracking)
├─ Your Rust core (cost calculation)
└─ SQLite (historical storage)

Retrieval Auditing:
├─ Pyvectorhound (diagnostics)
├─ OpenTelemetry (observability)
└─ Vector DB choice (user selects)

LLM Integration:
├─ OpenRouter API (multi-model)
├─ Ollama (local inference)
├─ DSPy (optimization)
└─ LiteLLM (routing)

Infrastructure:
├─ Qdrant/Chroma/Milvus (vectors)
├─ PostgreSQL/SQLite (structured)
├─ Redis (optional caching)
└─ OpenTelemetry (monitoring)

100% Open-Source ✅
Zero Vendor Lock-in ✅
User-Owned Data ✅
```

---

## Integration Points

### At Build Time
```bash
# Copy both projects into monorepo
openanchor/
├─ openanchor-rust/
│  ├─ src/
│  ├─ Cargo.toml
│  └─ Cargo.lock
├─ pycostaudit/ (Git submodule or copy)
│  ├─ crates/cost-reporter/ (Rust core)
│  └─ python/ (Python wrapper)
├─ pyvectorhound/ (Git submodule or copy)
│  ├─ src/ (Rust core)
│  └─ pyvectorhound/ (Python wrapper)
└─ openanchor-python/
   └─ src/openanchor/
       ├─ cost_calculator.py (wraps PyCostAudit)
       └─ retrieval_auditor.py (wraps Pyvectorhound)
```

### At Runtime
```python
# User's code
from openanchor import OpenAnchorRuntime
from openanchor.integrations import PyCostAuditConnector, PyvectorhoundConnector

guard = OpenAnchorRuntime(
    cost_tracker=PyCostAuditConnector(),
    rag_auditor=PyvectorhoundConnector()
)

response = await guard.run_task("Analyze this PDF")
print(guard.cost_meter.report())  # Via PyCostAudit
print(guard.retrieval_audit.report())  # Via Pyvectorhound
```

---

## Benefits of This Stack

✅ **No vendor lock-in** — Use whatever vector DB you want
✅ **Privacy first** — All data stays local (optional cloud)
✅ **Cost transparent** — You own all cost data
✅ **Community-driven** — Every component is OSS
✅ **Leverages your work** — PyCostAudit + Pyvectorhound are core
✅ **Modular** — Swap components without rewriting
✅ **Production-ready** — All tools battle-tested

---

## Roadmap: Integration Phases

**Phase 1 (v0.1):** PyCostAudit core
- ✅ Copy cost-reporter.rs into openanchor-rust
- ✅ Wire up cost tracking in runtime
- ✅ CostMeter reports via PyCostAudit data

**Phase 2 (v0.2):** Pyvectorhound integration
- ✅ Copy src/ into openanchor-rust
- ✅ Wire up RAG diagnostics in DocIngest
- ✅ Auto-fix retrieval issues based on Pyvectorhound recommendations

**Phase 3 (v0.3):** Full observability
- ✅ OpenTelemetry export (Jaeger/Prometheus)
- ✅ Dashboard powered by exported metrics
- ✅ Team visibility into cost + retrieval quality

---

## File Structure (Final)

```
openanchor-mono/
├─ README.md (Quick start)
├─ LICENSE (MIT)
├─ Cargo.toml (Rust workspace)
│
├─ crates/
│  ├─ openanchor-core/
│  │  ├─ src/
│  │  │  ├─ lib.rs
│  │  │  ├─ runtime.rs
│  │  │  ├─ task_classifier.rs
│  │  │  ├─ spike_detectors.rs
│  │  │  ├─ optimizers/
│  │  │  ├─ quality_guardian.rs
│  │  │  ├─ cost_meter.rs
│  │  │  └─ vector_db/  (Qdrant, Chroma, etc.)
│  │  └─ Cargo.toml
│  │
│  ├─ cost-reporter/ (from PyCostAudit)
│  │  ├─ src/
│  │  │  ├─ cost_tracker.rs
│  │  │  ├─ pricing.rs
│  │  │  └─ recommender.rs
│  │  └─ Cargo.toml
│  │
│  └─ pyvectorhound-core/ (from Pyvectorhound)
│     ├─ src/
│     │  ├─ rag_diagnostics.rs
│     │  └─ component_analyzer.rs
│     └─ Cargo.toml
│
├─ python/
│  ├─ src/openanchor/
│  │  ├─ __init__.py
│  │  ├─ runtime.py
│  │  ├─ integrations/
│  │  │  ├─ pycostaudit.py
│  │  │  └─ pyvectorhound.py
│  │  └─ cost_meter.py
│  └─ pyproject.toml
│
├─ node/
│  ├─ src/
│  │  ├─ index.ts
│  │  ├─ runtime.ts
│  │  └─ integrations/
│  └─ package.json
│
└─ docs/
   ├─ ARCHITECTURE.md
   ├─ INTEGRATIONS.md
   └─ examples/
```

