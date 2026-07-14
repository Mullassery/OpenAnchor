# PyCostAudit-Multi v0.5: Focused Scope (No Scope Creep)

**Context:** PyCostAudit has 50+ documentation files from various phases. This doc clarifies EXACTLY what should ship in v0.5 to support OpenAnchor.

---

## What We NEED for v0.5 (OpenAnchor MVP)

### Core: Cost Calculation Library
- ✅ `CostCalculator` class (calculate cost for any provider/model)
- ✅ Support 20+ cloud + 10+ open-source APIs
- ✅ Accuracy: ±1% vs actual API bills
- ✅ Real-time pricing updates (daily crawler)
- ✅ Sub-5ms latency per calculation

### Tracking: Cost Attribution
- ✅ `CostTracker` class (log operations + aggregate)
- ✅ Track by provider, model, task type
- ✅ SQLite storage (local, no cloud)
- ✅ Basic reporting (today, week, month)

### Interface: Minimal but Useful
- ✅ Python SDK (pip install pycostaudit-multi)
- ✅ Simple CLI (query today's costs, compare providers)
- ✅ REST API (for dashboard access)
- ✅ Documentation (library usage + OpenAnchor integration)

**That's it. Everything else is v0.2+.**

---

## What We DON'T NEED for v0.5 (Cut These)

### ❌ Forecasting & ML
- ❌ ARIMA algorithms
- ❌ Exponential smoothing
- ❌ Confidence intervals
- ❌ Anomaly detection
- ❌ Seasonality detection
- **Reason:** Not needed for OpenAnchor MVP. Cost reduction is the priority, not prediction.
- **Defer to:** v0.2

### ❌ Compliance & Audit
- ❌ SOC2 certification
- ❌ HIPAA compliance
- ❌ GDPR compliance
- ❌ PCI DSS compliance
- ❌ ISO 27001 compliance
- ❌ Immutable audit trail
- **Reason:** Enterprise feature, not MVP. OpenAnchor doesn't need this yet.
- **Defer to:** v0.2 (after v0.1 is stable)

### ❌ Team Management & RBAC
- ❌ User roles (Admin, Analyst, Viewer)
- ❌ Cost budgets per team
- ❌ Chargeback calculations
- ❌ Team dashboards
- **Reason:** Not needed for individual/LangChain users.
- **Defer to:** v0.2

### ❌ Advanced Analytics
- ❌ Trend analysis (growth rates, week-over-week)
- ❌ Billing plan comparisons
- ❌ Custom reports
- ❌ CSV/JSON exports (nice to have, but not MVP)
- **Reason:** Basic aggregation is enough for v0.5.
- **Defer to:** v0.2

### ❌ Model Recommendation Engine
- ❌ Task-based model selector
- ❌ Quality/cost/speed tradeoff analysis
- ❌ Automatic benchmarking
- **Reason:** This is OpenAnchor's job, not PyCostAudit-Multi's. Keep separation clean.
- **Defer to:** v0.2 (if needed as standalone tool)

### ❌ Web Dashboard
- ❌ Interactive charts
- ❌ Real-time cost visualization
- ❌ Budget alerts
- ❌ Forecast projections
- **Reason:** Nice to have, but CLI + REST API are sufficient for v0.5.
- **Defer to:** v0.2

### ❌ Integrations
- ❌ Slack notifications
- ❌ Webhooks
- ❌ BigQuery export
- ❌ Datadog integration
- ❌ OpenTelemetry
- **Reason:** Can be added later when demand is proven.
- **Defer to:** v0.2+

### ❌ Claude Code Specific Features
- ❌ MCP cost tracking
- ❌ GitHub operations cost tracking
- ❌ File operation breakdown
- ❌ Claude Code skill
- **Reason:** PyCostAudit-Multi is provider-agnostic, not Claude-specific.
- **Deprecate:** Claude-only code is removed.

---

## What STAYS: The Core

### v0.5 Deliverables

```python
# 1. Cost calculation (the MVP)
from pycostaudit_multi import CostCalculator

calc = CostCalculator()
cost = calc.calculate("anthropic", "claude-3-5-sonnet", 1000, 250)
# Returns: 0.00825

# 2. Cost tracking (the storage)
from pycostaudit_multi import CostTracker

tracker = CostTracker()
tracker.track(
    provider="anthropic",
    model="claude-3-5-sonnet",
    input_tokens=1000,
    output_tokens=250,
    task_type="document_qa"
)

# 3. Basic reporting
report = tracker.report(period="day")
# Returns: {"by_provider": {...}, "by_model": {...}, "by_task_type": {...}, "total": 0.00825}

# 4. Provider comparison (nice to have, but simple)
from pycostaudit_multi import ProviderComparison

comp = ProviderComparison()
result = comp.same_model_different_providers("llama-70b")
# Returns: costs for Groq, DeepInfra, Together, etc.
```

### Files Structure (Clean)

```
PyCostAudit/
├─ Cargo.toml                # Rust workspace
├─ pyproject.toml            # Python package
├─ README.md                 # Main docs (START HERE)
├─ ROADMAP_MULTI.md         # v0.5+ roadmap
│
├─ src/                      # Rust core
│  ├─ cost_calculator.rs
│  ├─ pricing.rs
│  ├─ provider_registry.rs
│  ├─ comparison.rs
│  └─ storage.rs
│
├─ python/
│  ├─ pycostaudit_multi/
│  │  ├─ cost_calculator.py
│  │  ├─ cost_tracker.py
│  │  ├─ provider_comparison.py
│  │  ├─ cli.py
│  │  └─ __init__.py
│  └─ tests/
│
└─ docs/
   ├─ QUICK_START.md         # How to use
   ├─ LIBRARY_API.md          # For OpenAnchor
   ├─ OPENANCHOR_INTEGRATION.md
   └─ PROVIDER_LIST.md        # Which APIs supported
```

### What Gets Deleted

**Delete these 50+ files from the repo:**
- All "PHASE_*" files (phase documentation)
- All "DESIGN_*" files (over-engineered designs)
- "ROADMAP.md", "ROADMAP_2026.md", "ROADMAP_PRIORITIZED.md" (keep only ROADMAP_MULTI.md)
- All "MCP_*" files (Claude Code skill, not relevant)
- All "*_GUIDE.md" files (too specific)
- "FEATURES_ROADMAP.md" (too ambitious)
- "ML_FORECASTING*" files (cut that feature)
- "COMPLIANCE_*" files (v0.2 feature)
- "DASHBOARD_*" files (v0.2 feature)
- All cloud provider integration docs (not MVP)
- "RESEARCH_ROADMAP.md" (unfocused)

**Keep only:**
- README.md (main)
- ROADMAP_MULTI.md (future)
- CLAUDE.md (if still relevant)
- Quick start docs

---

## v0.5 Development Plan (2 Weeks)

### Week 1
- [ ] **Rust core**
  - [ ] CostCalculator (supports 20+ providers)
  - [ ] Pricing registry (daily updates)
  - [ ] ProviderComparison logic
  - [ ] Storage (SQLite)
  - [ ] Tests (cost accuracy ±1%)

- [ ] **Python SDK**
  - [ ] CostCalculator wrapper
  - [ ] CostTracker class
  - [ ] ProviderComparison wrapper
  - [ ] Tests

### Week 2
- [ ] **CLI**
  - [ ] `pycostaudit-multi today` (today's costs)
  - [ ] `pycostaudit-multi compare --model llama-70b` (provider comparison)
  - [ ] `pycostaudit-multi by-provider` (breakdown)

- [ ] **Documentation**
  - [ ] README (what it does, who should use it)
  - [ ] Quick start (basic usage)
  - [ ] Library API (how OpenAnchor uses it)
  - [ ] Provider list (which APIs supported)

- [ ] **Launch**
  - [ ] PyPI release
  - [ ] GitHub release
  - [ ] Announce to PyCostAudit users

---

## Success Metrics for v0.5

- ✅ CostCalculator accuracy: ±1% vs actual API bills
- ✅ Calculation latency: <5ms per operation
- ✅ Support 20+ cloud + 10+ open-source APIs
- ✅ OpenAnchor can call PyCostAudit-Multi cost calculation without modification
- ✅ Basic CLI works (query today's costs, compare providers)
- ✅ 200+ PyPI downloads in week 1
- ✅ Documentation clear enough that OpenAnchor can integrate

---

## What PyCostAudit-Multi IS vs ISN'T

### IS
✅ A cost calculation library for multi-API LLM environments
✅ A cost tracking tool for understanding where money goes
✅ A provider comparison engine
✅ The cost core for OpenAnchor
✅ Open-source, self-hosted, privacy-first

### ISN'T
❌ A forecasting tool (that's v0.2)
❌ A compliance platform (that's v0.2)
❌ A team management tool (that's v0.2)
❌ An advanced analytics platform (that's v0.2+)
❌ A model recommendation engine (that's OpenAnchor's job)
❌ A Claude Code specific tool (that was v0.4, this is v0.5+)

---

## Conclusion

**PyCostAudit-Multi v0.5 is laser-focused:**

One job: Track multi-API LLM costs accurately.

That's it. Shipping in 2 weeks. OpenAnchor can build on this solid foundation. Everything else (forecasting, compliance, dashboards, recommendations) waits for v0.2+.

No more wandering. No more 50+ doc files. Just focused, useful, accurate cost tracking.
