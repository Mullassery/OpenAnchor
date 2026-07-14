# PyCostAudit Code Audit: What to Keep vs Delete for v0.5

**Context:** PyCostAudit codebase has accumulated features for forecasting, compliance, reporting, dashboards, and Claude-specific integrations. For v0.5 (multi-API cost core), we need to ruthlessly cut scope.

---

## Code Inventory

### Python Package (pycostaudit/)
**Total: 34 files, ~500KB, estimated 15,000+ lines of code**

---

## Files to KEEP (Core v0.5 - 6 files)

### 1. ✅ `__init__.py`
- **Purpose:** Package initialization, public API exports
- **Size:** ~573 bytes
- **Action:** KEEP - Update to expose only v0.5 APIs
- **Changes:** 
  - Export: `CostCalculator`, `CostTracker`, `ProviderComparison`
  - Remove: forecasting, compliance, reporting, alerting imports

### 2. ✅ `cost_calculator.py`
- **Purpose:** Calculate cost for any provider + model + tokens
- **Size:** ~14KB
- **Action:** KEEP - This is the core
- **Changes:** 
  - Remove Claude-specific logic
  - Add provider parameter
  - Support 20+ providers (already done?)
  - Test with OpenAnchor

### 3. ✅ `pricing_manager.py`
- **Purpose:** Manage provider pricing database
- **Size:** ~10KB
- **Action:** KEEP - Core dependency
- **Changes:**
  - Update to support 20+ cloud + 10+ open-source APIs
  - Add daily pricing crawler
  - Remove forecasting-related code

### 4. ✅ `database.py`
- **Purpose:** SQLite storage for operations + costs
- **Size:** ~20KB
- **Action:** KEEP - Storage layer
- **Changes:**
  - Remove compliance audit tables
  - Remove team/RBAC tables
  - Keep: provider, model, task_type, tokens, cost, timestamp
  - Simplify schema

### 5. ✅ `cost_model.py`
- **Purpose:** Cost calculation logic/models
- **Size:** ~12KB
- **Action:** KEEP but verify not Claude-specific
- **Changes:**
  - Ensure provider-agnostic
  - Support uniform token pricing (input/output rates per provider)

### 6. ✅ `persistence.py`
- **Purpose:** Load/save cost tracking state
- **Size:** ~10KB
- **Action:** KEEP - Storage abstraction
- **Changes:**
  - Simplify to just SQLite backend
  - Remove cloud storage backends (if any)

---

## Files to DELETE - Forecasting (3 files, ~50KB)

### ❌ `ml_forecasting_service.py` (15.7KB)
- **Purpose:** ML-based cost forecasting with confidence intervals
- **Why delete:** Forecasting is v0.2, not MVP
- **Dependencies to check:** Who imports this?
- **Action:** DELETE entirely

### ❌ `forecasting_service.py` (14.4KB)
- **Purpose:** Forecasting wrapper/interface
- **Why delete:** Not needed for v0.5
- **Action:** DELETE entirely

### ❌ `ml_token_estimator.py` (10.9KB)
- **Purpose:** ML-based token estimation
- **Why delete:** Not core functionality
- **Action:** DELETE entirely

### ❌ `anomaly_detection.py` (17KB)
- **Purpose:** Detect anomalies in cost trends
- **Why delete:** Forecasting-related, v0.2 feature
- **Action:** DELETE entirely

---

## Files to DELETE - Compliance & Audit (3 files, ~40KB)

### ❌ `compliance_audit.py` (15.8KB)
- **Purpose:** Compliance audit logging + SOC2/HIPAA/GDPR tracking
- **Why delete:** Enterprise feature, v0.2+
- **Action:** DELETE entirely

### ❌ `compliance_reporting.py` (13.5KB)
- **Purpose:** Generate compliance reports
- **Why delete:** Not MVP
- **Action:** DELETE entirely

### ❌ `observability_export.py` (17KB)
- **Purpose:** Export to OpenTelemetry/Datadog/BigQuery
- **Why delete:** Integrations are v0.2+
- **Action:** DELETE entirely

### ❌ `telemetry.py` (7KB)
- **Purpose:** Telemetry collection
- **Why delete:** Observability is v0.2
- **Action:** DELETE entirely

---

## Files to DELETE - Alerting & Reporting (6 files, ~85KB)

### ❌ `alerts_service.py` (18KB)
- **Purpose:** Alert management (Slack, email, webhook)
- **Why delete:** Alerting is v0.2
- **Action:** DELETE entirely

### ❌ `alerts_cli.py` (7.2KB)
- **Purpose:** CLI for alert management
- **Why delete:** Related to alerts_service
- **Action:** DELETE entirely

### ❌ `alerting.py` (15.7KB)
- **Purpose:** Alert creation + dispatch
- **Why delete:** Not MVP
- **Action:** DELETE entirely

### ❌ `reports_service.py` (22.4KB)
- **Purpose:** Generate various cost reports
- **Why delete:** Reporting is v0.2 (basic CLI queries sufficient for v0.5)
- **Action:** DELETE entirely

### ❌ `reports_cli.py` (7.8KB)
- **Purpose:** CLI for report generation
- **Why delete:** Related to reports_service
- **Action:** DELETE entirely

### ❌ `custom_report_builder.py` (24.8KB)
- **Purpose:** Build custom reports with filters
- **Why delete:** Advanced reporting, v0.2
- **Action:** DELETE entirely

### ❌ `reporting.py` (9.3KB)
- **Purpose:** Reporting module
- **Why delete:** Not core
- **Action:** DELETE entirely

---

## Files to DELETE - Recommendations Engine (2 files, ~50KB)

### ❌ `recommendations_engine.py` (21.4KB)
- **Purpose:** Generate cost reduction recommendations
- **Why delete:** **This is OpenAnchor's job, not PyCostAudit's**. PyCostAudit-Multi should only calculate costs, not recommend models/providers.
- **Action:** DELETE entirely
- **Note:** Provider comparison stays (simple, factual), but NO intelligence/recommendations

### ❌ `detailed_recommendations.py` (29.5KB)
- **Purpose:** Detailed recommendation generation
- **Why delete:** Related to recommendations_engine
- **Action:** DELETE entirely

---

## Files to DELETE - Team Management & Advanced Features (4 files, ~50KB)

### ❌ `multi_org_manager.py` (14.8KB)
- **Purpose:** Multi-organization/team management with RBAC
- **Why delete:** Team management is v0.2
- **Action:** DELETE entirely

### ❌ `user_context.py` (12.4KB)
- **Purpose:** User context + permissions
- **Why delete:** Related to team management
- **Action:** DELETE entirely

### ❌ `advanced_filters.py` (14.7KB)
- **Purpose:** Advanced filtering for cost queries
- **Why delete:** Nice-to-have, not MVP
- **Action:** DELETE entirely

### ❌ `detailed_token_classifier.py` (23.8KB)
- **Purpose:** Classify tokens by type (Claude-specific)
- **Why delete:** Claude-specific, not multi-API
- **Action:** DELETE entirely

---

## Files to DELETE - Claude-Specific Integration (2 files, ~20KB)

### ❌ `anthropic_integration.py` (9.4KB)
- **Purpose:** Claude Code-specific integration
- **Why delete:** v0.4 was Claude-only, v0.5 is multi-API
- **Action:** DELETE entirely

### ❌ `token_classifier.py` (12.4KB)
- **Purpose:** Classify tokens for Claude operations
- **Why delete:** Claude-specific, not needed for v0.5
- **Action:** DELETE entirely

---

## Files to DELETE - CLI & Interactive Features (2 files, ~25KB)

### ❌ `cli_interactive.py` (18.3KB)
- **Purpose:** Interactive CLI guide
- **Why delete:** Nice-to-have, basic CLI sufficient
- **Action:** DELETE entirely

### ❌ `interactive_guide.py` (11.6KB)
- **Purpose:** Interactive onboarding guide
- **Why delete:** Not MVP
- **Action:** DELETE entirely

---

## Files to DELETE - Backend & Other (2 files, ~25KB)

### ❌ `backend_service.py` (10.6KB)
- **Purpose:** Backend API service
- **Why delete:** Need to verify if used; if for dashboard/reporting, delete
- **Action:** CHECK dependencies, likely DELETE

---

## Directory to DELETE: dashboard/ (Entire)

### ❌ `dashboard/` directory
- **Contents:** Frontend React app + backend API for web dashboard
- **Size:** Estimated 500KB+
- **Purpose:** Web-based cost visualization
- **Why delete:** Dashboard is v0.2 feature
- **Action:** DELETE entire directory
  - `/dashboard/app.py` (backend)
  - `/dashboard/frontend/` (React frontend)
  - All associated CSS, components, etc.

---

## Summary: What Gets Deleted

| Category | Files | Size | Reason |
|----------|-------|------|--------|
| Forecasting | 4 | ~50KB | v0.2 feature |
| Compliance | 4 | ~53KB | v0.2 feature |
| Alerting | 3 | ~40KB | v0.2 feature |
| Reporting | 4 | ~65KB | v0.2 feature |
| Recommendations | 2 | ~50KB | OpenAnchor's job |
| Team Management | 2 | ~27KB | v0.2 feature |
| Claude-Specific | 2 | ~21KB | Old v0.4 code |
| CLI/Interactive | 2 | ~25KB | Nice-to-have |
| Dashboard | 1 dir | ~500KB | v0.2 feature |
| Other | TBD | TBD | TBD |
| **TOTAL** | **~26 files** | **~800KB+** | **Keep only 6 core files** |

---

## What Remains: v0.5 Core

```
PyCostAudit/
├─ pycostaudit/
│  ├─ __init__.py               ✅ (KEEP, simplify exports)
│  ├─ cost_calculator.py        ✅ (KEEP, core)
│  ├─ cost_model.py             ✅ (KEEP, core)
│  ├─ pricing_manager.py        ✅ (KEEP, core)
│  ├─ database.py               ✅ (KEEP, simplified schema)
│  └─ persistence.py            ✅ (KEEP, simplified)
│
├─ tests/
│  ├─ test_cost_model.py        ✅ (KEEP)
│  ├─ test_integration.py       ✅ (KEEP, simplify)
│  └─ [DELETE ALL OTHER TESTS]
│
└─ examples/
   └─ quick_start.py            ✅ (KEEP, update for v0.5)
```

**Result: ~2000 lines of clean, focused code (down from 15,000+)**

---

## Implementation Plan

### Phase 1: Create Deletion List (This doc)
- ✅ Identify all files to delete
- ✅ Document reasoning
- ✅ Plan test updates

### Phase 2: Backup (Before Deletion)
```bash
# Create backup branch
git checkout -b v0.4-backup
git push origin v0.4-backup
# Now we can safely delete on main
```

### Phase 3: Delete Files
```bash
# Delete forecasting
rm pycostaudit/ml_forecasting_service.py
rm pycostaudit/forecasting_service.py
rm pycostaudit/ml_token_estimator.py
rm pycostaudit/anomaly_detection.py

# Delete compliance
rm pycostaudit/compliance_audit.py
rm pycostaudit/compliance_reporting.py
rm pycostaudit/observability_export.py
rm pycostaudit/telemetry.py

# Delete alerting & reporting
rm pycostaudit/alerts_service.py
rm pycostaudit/alerts_cli.py
rm pycostaudit/alerting.py
rm pycostaudit/reports_service.py
rm pycostaudit/reports_cli.py
rm pycostaudit/custom_report_builder.py
rm pycostaudit/reporting.py

# Delete recommendations
rm pycostaudit/recommendations_engine.py
rm pycostaudit/detailed_recommendations.py

# Delete team management
rm pycostaudit/multi_org_manager.py
rm pycostaudit/user_context.py
rm pycostaudit/advanced_filters.py
rm pycostaudit/detailed_token_classifier.py

# Delete Claude-specific
rm pycostaudit/anthropic_integration.py
rm pycostaudit/token_classifier.py

# Delete CLI/interactive
rm pycostaudit/cli_interactive.py
rm pycostaudit/interactive_guide.py

# Delete dashboard
rm -rf pycostaudit/dashboard/

# Delete tests for deleted features
rm tests/test_forecasting.py
rm tests/test_compliance_audit.py
rm tests/test_alerting.py
rm tests/test_alerts_service.py
rm tests/test_reports_service.py
rm tests/test_anomaly_detection.py
rm tests/test_multi_org.py
rm tests/test_observability.py
# Keep only:
# tests/test_cost_model.py
# tests/test_integration.py
# tests/test_database_schema.py
```

### Phase 4: Update __init__.py
```python
# OLD (v0.4): Exports everything
from .ml_forecasting_service import TimeSeriesForecaster
from .compliance_reporting import ComplianceManager
from .alerts_service import AlertsManager
from .recommendations_engine import RecommendationsEngine
# ... 20+ more imports

# NEW (v0.5): Exports only core
from .cost_calculator import CostCalculator
from .cost_model import CostModel
from .pricing_manager import PricingManager
from .database import CostDatabase
from .persistence import PersistenceManager
```

### Phase 5: Update Dependencies
- Review `pyproject.toml` and `Cargo.toml`
- Remove dependencies for deleted features:
  - Remove: sklearn, statsmodels (forecasting)
  - Remove: plotly, pandas (dashboard/reporting)
  - Keep: only essentials (sqlite, httpx, pydantic)

### Phase 6: Update Tests
- Delete test files for deleted features
- Keep: test_cost_model.py, test_integration.py, test_database_schema.py
- Update remaining tests to use only core APIs

### Phase 7: Commit
```bash
git add -A
git commit -m "PyCostAudit v0.5: Cut scope - remove forecasting, compliance, reporting, dashboards

DELETIONS (26 files, ~800KB):
- Forecasting: ml_forecasting_service, forecasting_service, anomaly_detection, ml_token_estimator
- Compliance: compliance_audit, compliance_reporting
- Alerting: alerts_service, alerts_cli, alerting
- Reporting: reports_service, reports_cli, custom_report_builder, reporting
- Recommendations: recommendations_engine, detailed_recommendations
- Team Management: multi_org_manager, user_context, advanced_filters, detailed_token_classifier
- Claude-Specific: anthropic_integration, token_classifier
- CLI/Interactive: cli_interactive, interactive_guide
- Dashboard: entire dashboard/ directory
- Tests: all related test files

KEPT (6 files, ~60KB):
- __init__.py (simplified exports)
- cost_calculator.py (core)
- cost_model.py (core)
- pricing_manager.py (core)
- database.py (simplified schema)
- persistence.py (simplified)

RESULT:
- Down from 15,000+ to ~2,000 lines of code
- Laser-focused on v0.5 scope: multi-API cost calculation
- Ready to support OpenAnchor as cost core
- 80% code reduction

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Verification Checklist

After deletion, verify:

- [ ] `python -c "from pycostaudit import CostCalculator; print('✅ Import works')"` succeeds
- [ ] Core tests pass: `pytest tests/test_cost_model.py tests/test_database_schema.py -v`
- [ ] No broken imports in __init__.py
- [ ] No leftover references to deleted modules
- [ ] pyproject.toml has no orphaned dependencies
- [ ] README updated to reflect v0.5 scope
- [ ] CHANGELOG documents the deletions

---

## Files Requiring Special Attention

### `database.py` - Schema Simplification Needed
Check for these tables and potentially remove:
- `compliance_audit_log` table → DELETE
- `user_roles` table → DELETE (team management)
- `organizations` table → DELETE (multi-org)
- `alerts` table → DELETE (alerting)
- `reports` table → DELETE (reporting)
- `forecast_cache` table → DELETE (forecasting)

Keep only:
- `cost_operations` table (provider, model, tokens, cost, timestamp)
- `pricing_cache` table (provider pricing history)

### `cost_calculator.py` - Provider Support Verification
Verify it already supports:
- 20+ cloud providers (OpenAI, Anthropic, Google, Mistral, DeepSeek, etc.)
- 10+ open-source APIs (Groq, DeepInfra, Together, Fireworks, etc.)
- Generic token pricing (input_rate, output_rate per provider/model)

If it's Claude-specific, needs major rewrite.

### `__init__.py` - Simplify Exports
Current exports likely include 20+ classes/functions. Reduce to:
```python
from .cost_calculator import CostCalculator
from .pricing_manager import PricingManager
from .database import CostDatabase

__all__ = ['CostCalculator', 'PricingManager', 'CostDatabase']
```

---

## Timeline

- **Now:** Complete this audit
- **Tomorrow:** Backup + delete files
- **Day 3:** Update core files, simplify schemas
- **Day 4:** Update tests, verify imports
- **Day 5:** Push to GitHub, announce v0.5 focus

Total: 5 days to production-ready v0.5 codebase.

---

**PyCostAudit v0.5: From 15,000 lines of wandering code to 2,000 lines of focused cost tracking.**
