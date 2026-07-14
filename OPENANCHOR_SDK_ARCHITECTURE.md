# OpenAnchor: SDK Architecture & Integration

**Philosophy:** OpenAnchor is a set of SDKs, not a framework. You add it to your agent, not the other way around.

---

## SDK Layers

### Layer 1: Rust Core (Performance)
**Location:** `openanchor-core/` (published to crates.io)

```rust
// Core runtime
openanchor-core/
├─ src/
│  ├─ runtime.rs          # Main cost interception loop
│  ├─ task_classifier.rs  # Detect task type
│  ├─ spike_detector.rs   # Which cost patterns apply?
│  ├─ optimizers/
│  │  ├─ doc_ingester.rs       # PDF → Markdown → RAG
│  │  ├─ mcp_lazy_loader.rs    # Semantic tool loading
│  │  ├─ skill_loader.rs       # External skill calling
│  │  ├─ context_compressor.rs # Rolling summarization
│  │  ├─ model_router.rs       # Task-based routing
│  │  ├─ provider_router.rs    # Multi-provider discovery
│  │  ├─ output_compressor.rs  # Semantic compression
│  │  ├─ caveman.rs           # Output token reduction
│  │  ├─ response_cache.rs    # Semantic caching
│  │  └─ cost_calculator.rs   # Real-time cost tracking
│  ├─ quality_guardian.rs # A/B testing, regression prevention
│  └─ cost_meter.rs       # Cost attribution
└─ Cargo.toml
```

**Reuses from PyCostAudit:**
- `cost_calculator.rs` - Real-time cost calculation
- `pricing.rs` - Model pricing database
- `provider_registry.rs` - Provider discovery
- `storage.rs` - SQLite backend

**Performance targets:**
- Cost interception latency: <5ms per LLM call
- Streaming support: No buffering overhead
- Memory: <50MB base, linear with session count

---

### Layer 2: Python SDK (Most Users)
**Location:** `openanchor-py/` (published to PyPI as `openanchor`)

```python
from openanchor import CostOptimizer, CostMeter
from openanchor.providers import OpenAI, Anthropic, Google
from openanchor.models import ModelIntelligence

# Initialization
optimizer = CostOptimizer(
    api_key="sk-...",
    model="claude-3-5-sonnet",
    providers=[Anthropic(), OpenAI(), Google()],  # Optional: provider discovery
    enable_model_intelligence=True,  # Daily pricing tracker
    enable_cost_meter=True
)

# Wrap any LLM call
response = optimizer.optimized_call(
    prompt="Analyze this PDF...",
    context={"file": "report.pdf", "task_type": "document_analysis"},
    model="auto"  # Auto-route to cheapest capable model
)

# Get full cost report
report = optimizer.cost_meter.report()
# {
#   "optimizations_applied": ["DocIngest", "LazyMCP", "ModelRouter"],
#   "cost_breakdown": {
#     "DocIngest": {"tokens_saved": 15000, "cost_saved": "$0.04"},
#     "LazyMCP": {"tokens_saved": 8500, "cost_saved": "$0.02"},
#     "ModelRouter": {"tokens_saved": 0, "cost_saved": "$0.00", "note": "Haiku elected (already cheapest)"}
#   },
#   "total_cost_before": "$0.45",
#   "total_cost_after": "$0.17",
#   "savings": "62%"
# }

# Model discovery
intelligence = ModelIntelligence(api_key="sk-...")
recommendations = intelligence.get_recommendations()
# [
#   {
#     "title": "Save $1,200/month by switching to Gemini Flash",
#     "current_model": "claude-3-5-opus",
#     "recommended_model": "gemini-2-flash",
#     "cost_delta": "$1,200/month",
#     "quality_match": "98% (tested on 100 of your tasks)",
#     "one_click_switch": True
#   }
# ]

# Switch models with one line
optimizer.switch_model("gemini-2-flash", run_regression_test=True)
# Runs A/B test on last 20 tasks, shows results, auto-rollback if quality <95%
```

**Integration examples:**

```python
# LangChain Integration
from langchain.chat_models import ChatOpenAI
from openanchor import CostOptimizer

optimizer = CostOptimizer(api_key="sk-...")

# Wrap the LLM
llm = ChatOpenAI(model="gpt-4")
llm_optimized = optimizer.wrap(llm)

# Use normally; OpenAnchor intercepts
chain = llm_optimized | StrOutputParser()
result = chain.invoke({"input": "..."})  # 60% cheaper, transparently
```

```python
# Deep Agents Integration
from langchain.agents import AgentExecutor, create_tool_calling_agent
from openanchor import CostOptimizer

optimizer = CostOptimizer(api_key="sk-...")

# Wrap agent's LLM
agent = create_tool_calling_agent(
    llm=optimizer.wrap(llm),
    tools=tools,
    prompt=prompt
)

executor = AgentExecutor(agent=agent, tools=tools)
result = executor.invoke({"input": "..."})  # 60% cheaper
```

**Structure:**
```
openanchor-py/
├─ openanchor/
│  ├─ __init__.py
│  ├─ optimizer.py          # Main CostOptimizer class
│  ├─ cost_meter.py         # Cost tracking & reporting
│  ├─ model_intelligence.py # Model discovery engine
│  ├─ providers/
│  │  ├─ anthropic.py
│  │  ├─ openai.py
│  │  ├─ google.py
│  │  ├─ mistral.py
│  │  └─ open_source.py     # Groq, DeepInfra, Together, etc
│  ├─ integrations/
│  │  ├─ langchain.py
│  │  ├─ deep_agents.py
│  │  ├─ llamaindex.py
│  │  └─ custom.py
│  └─ config.py
├─ tests/
├─ setup.py
└─ pyproject.toml
```

**Published to PyPI as `openanchor`**
- `pip install openanchor`

---

### Layer 3: Node.js SDK
**Location:** `openanchor-js/` (published to npm as `@openanchor/core`)

```javascript
const { CostOptimizer, ModelIntelligence } = require("@openanchor/core");

// Initialization
const optimizer = new CostOptimizer({
  apiKey: "sk-...",
  model: "claude-3-5-sonnet",
  enableModelIntelligence: true,
  enableCostMeter: true
});

// Wrap LLM calls
const response = await optimizer.optimizedCall({
  prompt: "Analyze this PDF...",
  context: { file: "report.pdf", taskType: "document_analysis" },
  model: "auto"
});

// Get cost report
const report = optimizer.costMeter.report();
console.log(`Saved ${report.savings}% on this call`);

// Model discovery
const intelligence = new ModelIntelligence({ apiKey: "sk-..." });
const recommendations = await intelligence.getRecommendations();
recommendations.forEach(rec => {
  console.log(`${rec.title}: ${rec.costDelta}`);
});

// One-click model switch
await optimizer.switchModel("gemini-2-flash", { runRegressionTest: true });
```

**Structure:**
```
openanchor-js/
├─ src/
│  ├─ index.ts
│  ├─ optimizer.ts
│  ├─ costMeter.ts
│  ├─ modelIntelligence.ts
│  ├─ providers/
│  │  └─ ...
│  └─ integrations/
│     ├─ langchain.ts
│     └─ vercel-ai.ts
├─ tests/
├─ package.json
└─ tsconfig.json
```

**Published to npm as `@openanchor/core`**
- `npm install @openanchor/core`

---

### Layer 4: HTTP API (Framework-Agnostic)

For frameworks without native SDK support, expose HTTP endpoint:

```bash
# Start OpenAnchor server
openanchor serve --port 8000
```

```python
# Any language can now call
import requests

response = requests.post("http://localhost:8000/optimize", json={
    "prompt": "Analyze this PDF...",
    "context": {"file": "report.pdf"},
    "model": "claude-3-5-sonnet"
})

print(response.json()["cost_saved"])  # "62%"
```

**Endpoints:**
- `POST /optimize` - Optimize single LLM call
- `GET /recommendations` - Get model/provider recommendations
- `POST /switch-model` - Switch to recommended model
- `GET /cost-meter` - Get real-time cost metrics
- `GET /health` - Health check

---

### Layer 5: Environment Variable Interception

For maximum friction-free adoption:

```bash
export OPENANCHOR_API_KEY="sk-..."
export OPENANCHOR_ENABLED=true
export OPENANCHOR_MODEL="claude-3-5-sonnet"

# Your agent runs normally; OpenAnchor intercepts all LLM calls
python my_agent.py
```

Mechanism:
1. Python SDK patches `openai.OpenAI()`, `anthropic.Anthropic()` on import
2. All LLM calls go through OpenAnchor transparently
3. Cost meter available via `$OPENANCHOR_COST_REPORT` environment variable

---

## Integration Patterns

### Pattern 1: Wrap the LLM (Recommended for Most Users)

```python
from openanchor import CostOptimizer

optimizer = CostOptimizer(api_key="sk-...")
llm = optimizer.wrap(your_llm)

# Use llm normally; OpenAnchor intercepts
response = llm.invoke(prompt)
```

### Pattern 2: Wrap the Agent

```python
from openanchor import CostOptimizer

optimizer = CostOptimizer(api_key="sk-...")
agent = optimizer.wrap(your_agent)

# Use agent normally
response = agent.run(input)
```

### Pattern 3: Manual Calls

```python
from openanchor import CostOptimizer

optimizer = CostOptimizer(api_key="sk-...")

# Explicit optimization
response = optimizer.optimized_call(
    prompt="...",
    context={"task_type": "document_analysis"}
)
```

### Pattern 4: Streaming

```python
from openanchor import CostOptimizer

optimizer = CostOptimizer(api_key="sk-...")

# Streaming works transparently
for chunk in optimizer.stream(prompt):
    print(chunk, end="")

# Cost meter still tracks all tokens
print(optimizer.cost_meter.report())
```

---

## Cursor Plugin (If Possible)

**Goal:** Detect when Cursor launches an agent, intercept LLM calls, apply optimizations transparently.

```typescript
// cursor-plugin/main.ts
import * as vscode from "vscode";
import { CostOptimizer } from "@openanchor/core";

export function activate(context: vscode.ExtensionContext) {
  const optimizer = new CostOptimizer({
    apiKey: process.env.OPENANCHOR_API_KEY
  });

  // Hook into Cursor's LLM call pipeline
  // Intercept when agent makes LLM call
  // Apply optimizations transparently
  // Show cost savings in Cursor's UI
}
```

If Cursor's plugin API doesn't allow this, fall back to environment variable interception.

---

## Configuration

**Default behavior:**
- All 9 optimizations enabled by default
- Quality threshold: 95% (disable optimization if <95% quality)
- Cost meter: enabled
- Model discovery: enabled

**Per-call overrides:**

```python
response = optimizer.optimized_call(
    prompt="...",
    optimizations={"DocIngest": True, "LazyMCP": True, "ModelRouter": False},
    quality_threshold=0.95,
    model="auto",  # Auto-route to cheapest capable model
    force_model="gpt-4"  # Override with specific model
)
```

**Team/Enterprise config:**

```python
optimizer = CostOptimizer(
    api_key="sk-...",
    team_id="team_123",
    cost_budget_monthly=5000,  # Hard cap
    audit_logging=True,
    sso_enabled=True
)
```

---

## Observability

**Built-in metrics (OpenTelemetry):**

```python
from openanchor import CostOptimizer

optimizer = CostOptimizer(
    api_key="sk-...",
    tracing_enabled=True,
    tracing_endpoint="http://localhost:4318"
)

# All operations traced:
# - Cost optimization breakdown
# - Model selections + reasoning
# - Quality test results
# - Cache hits/misses
# - Provider selections
```

**Dashboard:**

```
OpenAnchor Dashboard (localhost:3000)
├─ Real-time cost meter
├─ Model discovery recommendations
├─ Cost savings by optimization
├─ Team cost analytics (enterprise)
├─ Audit logs (enterprise)
└─ Model/provider comparison charts
```

---

## Summary: Minimal Friction

```python
# 3 lines of code to add OpenAnchor
from openanchor import CostOptimizer
optimizer = CostOptimizer(api_key="sk-...")
llm = optimizer.wrap(your_llm)

# Everything else is exactly the same
response = llm.invoke(prompt)  # 60% cheaper, transparently
```

**That's it. No new concepts. No new frameworks. Just cheaper.**
