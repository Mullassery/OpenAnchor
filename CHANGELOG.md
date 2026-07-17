# OpenAnchor Changelog

## v0.1.0 — 2026-07-17

### 🎯 Initial Release: Token Intelligence Foundation

**Status:** ✅ Production Ready (Single-Tenant)

#### Core Features

- **6-Dimensional Token Attribution**
  - WHEN: Request vs response phase
  - WHERE: Operation type breakdown
  - HOW: Sub-operation detail
  - WHICH: Prompt template tracking
  - SESSION/PHASE: Temporal grouping
  - WHY: Patterns and recommendations (roadmap for v0.2)

- **Token Collection**
  - `TokenCollector` class for event capture
  - Support for manual and automatic capture
  - Multi-session tracking
  - Per-call and per-session aggregation

- **Attribution Analysis**
  - `AttributionModel` for 6D breakdown
  - Multi-dimensional analysis
  - Prompt efficiency ranking
  - Operation type distribution
  - Phase-based breakdown

- **Analytics APIs**
  - Query by operation, phase, model, prompt
  - Time-based breakdown (hourly, daily)
  - Performance metrics (latency, quality)
  - Problem detection (high tokens, low quality)
  - Comprehensive summaries

- **LangChain Middleware**
  - `OpenAnchorMiddleware` for integration
  - Manual capture API
  - Automatic recommendations
  - Query chaining

- **Storage Layers**
  - `EventStore` (in-memory)
  - `SqliteEventStore` (persistent)
  - PostgreSQL adapter (v1.0)

#### Test Coverage

- **25 tests, 100% passing**
  - 15 core component tests
  - 10 middleware integration tests
  - Complete coverage of APIs

#### Documentation

- Comprehensive README with examples
- QUICKSTART.md for 5-minute setup
- API reference in docstrings
- Example scripts in `examples/`

#### Breaking Changes

None — first release.

#### Known Limitations

- Single-tenant only (v0.2+ will add multi-tenant)
- In-memory or SQLite storage only (PostgreSQL in v1.0)
- Manual prompt tagging required (auto-detection in v0.2+)
- No pattern detection (v0.2+)
- No OTEL export (v0.2+)
- No external integrations (LangSmith, LlamaIndex coming v0.2+)

#### Dependencies

- pytokencalc >= 0.7.0
- pydantic >= 2.0.0
- requests >= 2.31.0

#### Files Added

```
openanchor/
├── __init__.py           (core exports)
├── models.py             (data models)
├── collector.py          (event collection)
├── storage.py            (storage abstraction)
├── attribution.py        (6D analysis)
├── analytics.py          (query APIs)
└── middleware/
    ├── __init__.py
    └── langchain.py      (LangChain integration)

tests/
├── __init__.py
├── test_core.py          (15 tests)
└── test_langchain_middleware.py (10 tests)

examples/
└── basic_usage.py        (complete walkthrough)

docs/
├── README.md
├── QUICKSTART.md
├── CHANGELOG.md (this file)
└── CONTRIBUTING.md
```

#### Migration from v0.0.X

No previous versions.

---

## v0.2.0 — Planned (July 2026)

### Features

- **Pattern Detection**
  - Anomaly detection
  - Trend analysis
  - Drift detection
  - Statistical insights

- **Advanced Recommendations**
  - Token savings estimates
  - Specific optimization suggestions
  - A/B testing comparison
  - Confidence scoring

- **New Integrations**
  - LlamaIndex callback
  - LangSmith bridge
  - OpenTelemetry export (Grafana, Datadog)

- **Multi-Model Optimization**
  - Model cost comparison
  - Routing recommendations
  - Latency vs quality trade-offs

### Improvements

- Auto-detect operation types
- Caching layer for performance
- Batch query optimization
- Enhanced error handling

---

## v0.3.0 — Planned (August 2026)

- A/B testing framework
- Advanced routing strategies
- Prompt optimization suggestions
- Cost-aware recommendations

---

## v1.0.0 — Planned (September 2026)

- PostgreSQL backend (multi-tenant)
- Production deployment guide
- Admin dashboard
- API gateway
- Rate limiting
- Authentication
- Comprehensive documentation
- 3+ example systems
- Enterprise support

---

## Development Notes

### Architecture Decisions

1. **6-Dimensional Attribution**: Inspired by data warehouse thinking — every token must be traced across multiple dimensions.

2. **Event-Based Storage**: Events are immutable append-only logs, enabling accurate replay and analysis.

3. **Query-as-Analysis**: Analytics API provides high-level queries that abstract storage layer, enabling future optimization.

4. **Plugin Architecture**: Middleware pattern allows easy integration with LangChain, LlamaIndex, etc.

### Performance Targets

- Event capture: < 1ms overhead
- Query response: < 100ms for 1M events
- Storage: < 1 byte per token (with compression)

### Testing Strategy

- Unit tests for each component
- Integration tests for workflows
- Example scripts as regression tests
- Benchmarks for performance targets

### Code Quality

- Type hints throughout
- Comprehensive docstrings
- Black formatting (100 char line)
- Mypy checking for type safety
- pytest for testing

---

## Contributors

- **Georgi Mammen Mullassery** (@Mullassery) — Initial architecture and implementation

---

## License

MIT License — see LICENSE file.
