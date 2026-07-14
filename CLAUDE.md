# CLAUDE.md — OpenAnchor Developer Guidelines

**CRITICAL: Read VISION.md first. OpenAnchor is a token intelligence layer, not an optimization platform.**

---

## Project Overview

OpenAnchor is a Python library that consumes token accounting data from PyTokenCalc and provides observability, attribution, pattern detection, and optimization intelligence.

**Core dependency:** PyTokenCalc v0.8+ (token accounting foundation)

---

## Repository Structure

```
openanchor/
├── openanchor/
│   ├── __init__.py                 # Public API
│   ├── core/
│   │   ├── events.py               # Token event types
│   │   ├── collector.py            # Collect events from PyTokenCalc
│   │   └── types.py                # Core type definitions
│   ├── attribution/
│   │   ├── __init__.py
│   │   ├── base.py                 # Attribution framework
│   │   ├── system_prompt.py        # System prompt attribution
│   │   ├── user_input.py           # User input attribution
│   │   ├── context.py              # Context/history attribution
│   │   └── retrieval.py            # RAG/retrieval attribution
│   ├── patterns/
│   │   ├── __init__.py
│   │   ├── detector.py             # Anomaly/pattern detection
│   │   ├── trends.py               # Trend analysis
│   │   └── drift.py                # Input drift detection
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── otel.py                 # OpenTelemetry export
│   │   ├── langfuse.py             # Langfuse integration
│   │   └── prometheus.py           # Prometheus metrics
│   └── utils/
│       ├── __init__.py
│       └── formatting.py           # Report generation
├── tests/
│   ├── test_collector.py
│   ├── test_attribution.py
│   ├── test_patterns.py
│   └── test_integration.py
├── examples/
│   ├── basic_usage.py              # Quick start
│   ├── with_langchain.py           # LangChain integration
│   └── with_otel.py                # OpenTelemetry export
├── docs/
│   ├── VISION.md                   # Product vision + scope
│   ├── ROADMAP.md                  # Implementation roadmap
│   └── API.md                      # API reference
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

---

## Key Concepts

### Token Events
Events emitted by PyTokenCalc when tokens are consumed:
```python
{
    "timestamp": "2026-07-15T10:00:00Z",
    "provider": "anthropic",
    "model": "claude-3-5-sonnet",
    "input_tokens": 1500,
    "output_tokens": 300,
    "context": {
        "user_id": "user123",
        "session_id": "sess456",
        "task": "code_review"
    }
}
```

### Attribution
Breaking down consumption by component:
- System prompt tokens (fixed)
- User input tokens (variable)
- Context/history tokens (growing)
- Retrieval context tokens (RAG-specific)
- Model overhead tokens (context window overhead)

### Pattern Detection
Identifying trends and anomalies:
- Token growth over time (correlation with incidents)
- Input drift (users changing query patterns)
- Context inflation (memory growing beyond expected)
- Cost anomalies (unusual spikes)

### Integration
Exporting signals to observability platforms:
- OpenTelemetry (standard format)
- Langfuse (LLM-specific observability)
- Prometheus (metrics)
- CSV/JSON (raw data export)

---

## Development Workflow

### Add New Attribution Model

1. Create file: `openanchor/attribution/your_model.py`
2. Implement `AttributionModel` ABC:
   ```python
   from openanchor.attribution.base import AttributionModel
   
   class YourAttributionModel(AttributionModel):
       def attribute(self, event: TokenEvent) -> AttributionBreakdown:
           """Break down tokens by component."""
           return AttributionBreakdown(
               system_prompt=...,
               user_input=...,
               context=...,
               other=...
           )
   ```
3. Add tests in `tests/test_attribution.py`
4. Document in `docs/API.md`

### Add New Pattern Detector

1. Create file: `openanchor/patterns/your_detector.py`
2. Implement `PatternDetector` ABC:
   ```python
   from openanchor.patterns.detector import PatternDetector
   
   class YourDetector(PatternDetector):
       def detect(self, events: List[TokenEvent]) -> List[Pattern]:
           """Detect patterns in token consumption."""
           return [Pattern(...), ...]
   ```
3. Add tests in `tests/test_patterns.py`

### Add New Integration

1. Create file: `openanchor/integration/your_platform.py`
2. Implement `Integration` ABC:
   ```python
   from openanchor.integration.base import Integration
   
   class YourPlatformIntegration(Integration):
       def export(self, events: List[TokenEvent]) -> None:
           """Export events to your platform."""
           pass
   ```
3. Document in README

---

## Testing Requirements

### Unit Tests
- All new functions must have unit tests
- Minimum 80% coverage per module
- Run with: `pytest tests/ --cov=openanchor`

### Integration Tests
- Test PyTokenCalc integration
- Test with real observability platforms (optional)
- Test error handling (corrupt data, network failures)

### Example Scripts
- All major features should have runnable examples
- Examples should be self-contained
- Run with: `python examples/your_example.py`

---

## Scope Discipline

### ✅ DO
- Improve attribution accuracy
- Add pattern detectors for new anomalies
- Integrate with new observability platforms
- Enhance PyTokenCalc integration
- Improve documentation and examples

### ❌ DON'T
- Re-implement tokenization (PyTokenCalc does this)
- Build cost calculation (PyTokenCalc does this)
- Create visualization UIs (Grafana, Langfuse do this)
- Add optimization execution (separate project)
- Add model selection logic (frameworks handle this)
- Store historical data (use observability platforms)

---

## Commit Guidelines

**Format:**
```
<type>: <description>

<optional detailed explanation>

Closes: <issue number if applicable>
```

**Types:**
- `feat:` New attribution model, pattern detector, or integration
- `fix:` Bug fix in existing feature
- `docs:` Documentation or README updates
- `refactor:` Code reorganization without behavior change
- `test:` Add or update tests
- `perf:` Performance improvement

**Examples:**
```
feat: Add drift detection for user input changes

Detects when user input tokens increase >20% in 24h window,
indicating potential query pattern shift.

Closes: #42
```

```
fix: Handle missing context in attribution breakdown

Previously crashed if PyTokenCalc event missing context field.
Now gracefully handles missing optional fields.
```

---

## Before Making a PR

- [ ] Read VISION.md (understand scope)
- [ ] Run: `pytest tests/ --cov=openanchor` (must pass)
- [ ] Run: `black openanchor/` (code formatting)
- [ ] Run: `ruff check openanchor/` (linting)
- [ ] Add tests for new functionality
- [ ] Update docs if adding new feature
- [ ] Update ROADMAP.md if changing priorities
- [ ] Ensure commit message follows guidelines

---

## Common Questions

**Q: Should I add cost calculation to OpenAnchor?**  
A: No. PyTokenCalc does this. Use PyTokenCalc's output.

**Q: Can I optimize token usage automatically?**  
A: No. OpenAnchor detects opportunities; users/optimization services decide actions.

**Q: What if PyTokenCalc is missing a model?**  
A: Update PyTokenCalc in a separate PR, then use it here.

**Q: Should I add alerting/notifications?**  
A: No. Export to OpenTelemetry; alerting platforms handle notifications.

**Q: Can I store historical token data?**  
A: No. Use observability platforms (Grafana, ClickHouse) for storage.

---

## Resources

- **PyTokenCalc:** https://github.com/Mullassery/pytokencalc
- **OpenTelemetry:** https://opentelemetry.io/
- **Langfuse:** https://langfuse.com/
- **Grafana:** https://grafana.com/

---

**Last Updated:** 2026-07-15  
**Maintainer:** Georgi Mammen Mullassery
