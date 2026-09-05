# OpenAnchor

**LLM token-attribution middleware: capture, attribute, and observe every LLM call — with real OpenTelemetry export and real semantic caching.**

OpenAnchor sits alongside your LLM calls (via a LangChain middleware today,
or by calling its collector API directly from any provider) and captures
token consumption events, breaks them down across 6 dimensions (phase,
operation type, prompt template, session, model, and pattern), and exposes
that data through a query API. It also ships real OTEL span export and a
real semantic-caching layer, both backed by actual embeddings and storage
— not mocked stand-ins.

[![PyPI](https://img.shields.io/pypi/v/openanchor)](https://pypi.org/project/openanchor)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org)
[![Tests: 248 Passing](https://img.shields.io/badge/tests-248%20passing-success)](./tests)
[![License: Proprietary (free w/ attribution)](https://img.shields.io/badge/License-Proprietary-blue.svg)](./LICENSE)

---

## 30-Second Start

```python
from openanchor import TokenCollector, Analytics, AttributionModel

collector = TokenCollector()
collector.set_session("session_1")

collector.capture_event(
    call_id="call_1",
    model="gpt-4",
    provider="openai",
    input_tokens=120,
    output_tokens=45,
)

attribution = AttributionModel(collector.store)
analytics = Analytics(collector, attribution)

summary = analytics.get_summary("session_1")
print(summary["total_tokens"], summary["by_operation"])
```

Or wrap a LangChain runnable directly:

```python
from openanchor.middleware.langchain import OpenAnchorMiddleware

middleware = OpenAnchorMiddleware(project_name="my_app")
wrapped_chain = middleware(my_langchain_runnable)

result = wrapped_chain.invoke({"model": "gpt-4", "prompt": "..."})
print(middleware.get_session_stats())
```

See `examples/basic_usage.py` and `examples/mcp_openanchor.py` for full
runnable examples.

---

## What's actually implemented

| Capability | Status |
|---|---|
| Token capture + 6D attribution (phase/operation/prompt/session/model) | Real, tested |
| In-memory + SQLite event storage (indexed, WAL, connection-reused) | Real, tested |
| LangChain middleware (`OpenAnchorMiddleware`, `WrappedRunnable`) | Real, tested |
| OpenTelemetry span export (`openanchor.otel`) | Real, tested — see below |
| Semantic caching (`openanchor.semantic_cache`, 12 MCP tools) | Real, tested — see below |
| Cost governance / token profiles / optimization tracking (`okf_*`) | Real, tested |
| Docker image with a working entry point | Real (`python -m openanchor`) |

---

## Observability (OpenTelemetry)

Every `TokenCollector.capture_event` call is wrapped in a real OTEL span
(token counts, model, provider, operation type, and cost-if-provided as
span attributes) — not a mocked stand-in. Tracing is **off by default**
(the collector's hot path shouldn't pay tracing overhead or make network
calls unless asked to):

```python
from openanchor import configure_tracing

configure_tracing(exporter="console")  # safe default, no network calls
# or: configure_tracing(exporter="otlp", otlp_endpoint="http://localhost:4318/v1/traces")
```

Full details, env-var-only configuration, and the span attribute reference:
[`OTEL_SETUP_GUIDE.md`](OTEL_SETUP_GUIDE.md). Tests use OTEL's in-memory
span exporter (`tests/test_otel.py`) to verify real spans are produced.

---

## Semantic caching

`openanchor.semantic_cache` implements real embedding-based caching:

- **Embeddings**: uses a local Ollama server (`nomic-embed-text` or similar)
  when reachable at `localhost:11434`, and automatically falls back to a
  deterministic, dependency-free feature-hashing embedder when it isn't —
  so the cache always works, online or offline.
- **Storage**: SQLite-backed (`SemanticCacheStore`), storing embeddings +
  responses + real lookup history (for real hit-rate stats, not hardcoded
  numbers).
- **Lookup**: real cosine-similarity search, not string matching.

```python
from openanchor import SemanticCache
from openanchor._mcp_tools import OpenAnchorMCPHandler

cache = SemanticCache(cache_db_path="cache.db")
handler = OpenAnchorMCPHandler(cache)

await handler.cache_prompt_embedding("Summarize this report", response="...")
matches = await handler.find_cached_similar("Summarize this report for me")
```

All 12 MCP tools (`cache_prompt_embedding`, `find_cached_similar`,
`analyze_cache_hit_rate`, `get_cache_statistics`, etc) compute real numbers
from actual cache contents and lookup history — see
`openanchor/_mcp_tools.py`. Tests: `tests/test_semantic_cache.py`,
`tests/test_mcp_tools.py`.

### MCP connector security

If you expose these tools over a network port via
`SemanticCache.start_mcp_connector()`, the defaults are deliberately
locked down: binds to `127.0.0.1` (not `0.0.0.0`), no CORS origins allowed
(not `*`), and least-privilege read-only permissions (not wildcard
actions/roles). Widening any of that requires explicit opt-in — see
`openanchor/_mcp_connector.py` and `PRODUCTION_DEPLOYMENT.md`.

---

## Privacy

OpenAnchor's job is intercepting and storing metadata about LLM calls, so
its privacy posture matters:

- **Raw prompt/response text capture is off by default.** The LangChain
  middleware's `WrappedRunnable.invoke()` records only a SHA-256 hash and
  length of the input/output by default — never the actual text — unless
  you construct `OpenAnchorMiddleware(capture_raw_content=True)`.
- **Opt-in captures are redacted by default.** When raw capture is
  enabled, excerpts are run through best-effort PII/secret redaction
  (emails, phone numbers, API keys, credit-card-like numbers, SSNs) before
  being stored, unless you explicitly disable that with
  `redact_captured_content=False`.
- **Retention/TTL.** `SqliteEventStore(retention_days=N)` automatically
  purges events older than the retention window (in addition to the
  existing manual `.clear()`), so persisted call data doesn't accumulate
  indefinitely once a retention policy is configured.

```python
from openanchor import SqliteEventStore
from openanchor.middleware.langchain import OpenAnchorMiddleware

store = SqliteEventStore("events.db", retention_days=30)
middleware = OpenAnchorMiddleware(
    store=store,
    capture_raw_content=False,       # default; only hash+length stored
    # capture_raw_content=True,      # opt in to store excerpts
    # redact_captured_content=True,  # default when opted in
)
```

See `openanchor/privacy.py` and `tests/test_privacy.py`.

---

## Installation

```bash
pip install openanchor
# with OTLP exporter support:
pip install "openanchor[otel]"
```

---

## Docker

```bash
docker build -t openanchor .
docker run -p 8080:8080 openanchor
curl http://localhost:8080/health
```

See `PRODUCTION_DEPLOYMENT.md` for details.

---

## Documentation

- [Production Deployment](PRODUCTION_DEPLOYMENT.md)
- [OTEL Setup Guide](OTEL_SETUP_GUIDE.md)
- [Quickstart](QUICKSTART.md)
- [Changelog](CHANGELOG.md)
- [Examples](examples/)

---

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
ruff check .
mypy openanchor/
bandit --ini .bandit -r openanchor/
```

248 tests across 14 test files, covering the collector/attribution/analytics
core, the LangChain middleware (including the token-capture hot path),
SQLite and in-memory storage, OTEL span export, semantic caching, the MCP
connector's security defaults, the OKF cost-governance/token-profile/
optimization-tracking modules, the `__main__` CLI entry point, the 6D
attribution analyzer, and the federated-learning / multi-agent-optimization
/ model-evolution modules.

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).
