# OpenAnchor

LLM token-attribution middleware — capture, attribute, and observe every LLM call, with real OpenTelemetry export and real semantic caching.

[![Tests](https://github.com/Mullassery/openanchor/actions/workflows/ci.yml/badge.svg)](https://github.com/Mullassery/openanchor/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/openanchor)](https://pypi.org/project/openanchor/)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

## What it is

OpenAnchor is an in-process SDK that sits alongside your LLM calls — via a
LangChain middleware today, or by calling its collector API directly from any
provider — and captures token-consumption events. It breaks usage down across
six dimensions (phase, operation type, prompt template, session, model, and
pattern) and exposes that data through a query API.

It also ships real OpenTelemetry span export and a real semantic-caching layer,
both backed by actual embeddings and storage rather than mocked stand-ins.

## Features / Highlights

- **Token capture + 6D attribution** — phase, operation type, prompt template,
  session, model, and pattern, via `TokenCollector` / `AttributionModel` /
  `Analytics`.
- **Storage** — in-memory and SQLite event stores (indexed, WAL,
  connection-reused) with optional retention/TTL purging.
- **LangChain middleware** — `OpenAnchorMiddleware` wraps a runnable and captures
  usage transparently, reading real `usage_metadata`.
- **OpenTelemetry export** — every `capture_event` is wrapped in a real OTEL span;
  tracing is off by default and enabled via `configure_tracing(...)`.
- **Semantic caching** — embedding-based cache with real cosine-similarity
  search, SQLite storage, and hit-rate stats; 12 MCP tools
  (`cache_prompt_embedding`, `find_cached_similar`, `analyze_cache_hit_rate`, ...).
- **Cost governance** — `okf_*` token profiles, cost governance, and optimization
  tracking.
- **Privacy by default** — raw prompt/response capture is off by default (hash +
  length only), and opt-in captures are redacted for common PII/secrets.
- **Docker image** with a working entry point (`python -m openanchor`).

## Who it's for / Use cases

- **Attributing LLM cost/token spend** across sessions, models, and prompt
  templates in an existing app, without switching providers.
- **Wrapping a LangChain chain** to capture usage transparently via
  `OpenAnchorMiddleware`.
- **Reducing repeat-call cost** with real semantic caching.
- **Tracking optimization impact** over time with the cost-governance and
  token-profile modules.

## What it is not

- **Not a proxy or a hosted platform.** OpenAnchor is an in-process SDK with no
  network hop and no separate services to run — unlike proxy/async-logging
  platforms such as Helicone.
- **Not framework-agnostic yet.** The shipped integration is the LangChain
  middleware plus the direct collector API. The broader "drop-in across
  Cursor/Claude Code/Codex CLI/Deep Agents" pitch exists only in `planning/` as
  an earlier, aspirational design.
- **Not a content logger by default.** Raw prompt/response text is not captured
  unless you explicitly opt in.
- **Not production-certified.** The project is classified Alpha; audit the
  privacy and MCP-connector defaults before relying on it in regulated
  environments.

## Project status

**Alpha (v0.6.1).** The collector/attribution/analytics core, storage, LangChain
middleware, OTEL export, semantic caching, the MCP tools, and the cost-governance
modules are implemented and tested. See [CHANGELOG.md](CHANGELOG.md) for release
history and [docs/](docs/) for architecture and roadmap material.

## Auto-instrumentation

Bridge OpenLLMetry/OpenInference instrumentors into OpenAnchor without changing
your application code:

```bash
pip install "openanchor[auto-instrument]"
```

```python
from openanchor import TokenCollector, enable_auto_instrumentation

collector = TokenCollector()
enable_auto_instrumentation(collector)  # enables every installed instrumentor

# Any OpenAI/Anthropic/LangChain call now produces a TokenEvent automatically.
print(collector.get_all_events())
```

The adapter maps `gen_ai.usage.*` / `llm.token_count.*` attributes, model,
provider, session and latency into OpenAnchor's existing event model. It skips
OpenAnchor's own spans to prevent recursion and deduplicates by trace/span id.
If no instrumentor is installed it raises `InstrumentationUnavailable` rather
than silently doing nothing.

## Installation

```bash
pip install openanchor
# with OTLP exporter support:
pip install "openanchor[otel]"
```

Development install:

```bash
pip install -e ".[dev]"
```

## Quick start

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

Runnable examples live in `examples/basic_usage.py` and
`examples/mcp_openanchor.py`.

## Usage

Enable OpenTelemetry tracing:

```python
from openanchor import configure_tracing

configure_tracing(exporter="console")  # safe default, no network calls
# or: configure_tracing(exporter="otlp", otlp_endpoint="http://localhost:4318/v1/traces")
```

Semantic caching:

```python
from openanchor import SemanticCache
from openanchor._mcp_tools import OpenAnchorMCPHandler

cache = SemanticCache(cache_db_path="cache.db")
handler = OpenAnchorMCPHandler(cache)

await handler.cache_prompt_embedding("Summarize this report", response="...")
matches = await handler.find_cached_similar("Summarize this report for me")
```

Privacy controls:

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

Docker:

```bash
docker build -t openanchor .
docker run -p 8080:8080 openanchor
curl http://localhost:8080/health
```

## Documentation

- [QUICKSTART.md](QUICKSTART.md) — the fastest path to a working capture.
- [OTEL_SETUP_GUIDE.md](OTEL_SETUP_GUIDE.md) — tracing config, env-var-only
  setup, and the span attribute reference.
- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) — deployment and MCP
  connector security defaults.
- [CHANGELOG.md](CHANGELOG.md) — release history.
- [examples/](examples/) — runnable examples.

## Known issues and deferred work

**Blocked / failed:**
- OTel/OpenInference auto-instrumentation and more framework adapters.

**Rejected / deferred:**
- A dashboard; export to Langfuse/Phoenix/Helicone.

Full shipped/blocked/rejected detail: [`docs/internal/QUEUE_STATUS.md`](docs/internal/QUEUE_STATUS.md).

## Contributing

Contributions are welcome. Run the same checks CI runs:

```bash
pip install -e ".[dev]"
pytest tests/ -v
ruff check .
mypy openanchor/
bandit --ini .bandit -r openanchor/
```

## Related projects

- [PyAPICheck](https://github.com/Mullassery/PyAPICheck) — API security discovery with cited risk scores
- [PyBeamGuard](https://github.com/Mullassery/PyBeamGuard) — Apache Beam and Dataflow pipeline analysis
- [PyNetworkIntel](https://github.com/Mullassery/PyNetworkIntel) — network discovery and anomaly detection
- [OpenAnchor](https://github.com/Mullassery/OpenAnchor) — LLM token-usage intelligence middleware
- [PyAgentHound](https://github.com/Mullassery/PyAgentHound) — trace, detect, and explain AI agent failures
- [PyVectorHound](https://github.com/Mullassery/PyVectorHound) — diagnose RAG retrieval failures
- [Browse all projects](https://github.com/Mullassery?tab=repositories)

## License

This project is licensed under the [Apache License 2.0](LICENSE).
