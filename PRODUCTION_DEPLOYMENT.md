# Production Deployment Guide

This guide describes deploying **OpenAnchor** itself — LLM token-attribution
middleware you embed in your application. It does not run as a standalone
service in most setups; you `pip install openanchor` and call it from your
own app. This document covers the parts that *do* run standalone: the
Docker image, the optional MCP semantic-cache server, and OTEL export.

## Pre-Production Checklist

- [ ] `pip install openanchor` (or `openanchor[otel]` if you want OTLP export)
- [ ] Storage backend chosen: in-memory `EventStore` (dev/tests) or
      `SqliteEventStore` (persistent, single-process)
- [ ] Privacy posture reviewed — see "Privacy" below; raw prompt/response
      capture is off by default and should stay off unless you have a
      documented reason and a retention policy
- [ ] `retention_days` set on `SqliteEventStore` if you're persisting
      captured events, so old events don't accumulate indefinitely
- [ ] OTEL tracing configured if you want span export (`configure_tracing`,
      see `OTEL_SETUP_GUIDE.md`) — off by default
- [ ] If exposing the MCP semantic-cache server: confirm you actually want
      it reachable beyond localhost before passing `host="0.0.0.0"`
- [ ] Tests pass: `pytest tests/ -v`
- [ ] `ruff check .`, `bandit -c .bandit -r openanchor/`, `mypy openanchor/`
      all clean (see CI config in `.github/workflows/ci.yml`)

## Library usage (the common case)

```python
from openanchor import TokenCollector, SqliteEventStore

store = SqliteEventStore("openanchor.db", retention_days=30)
collector = TokenCollector(store)
collector.set_session("session_123")

collector.capture_event(
    call_id="call_1",
    model="gpt-4",
    provider="openai",
    input_tokens=120,
    output_tokens=45,
)
```

No network exposure, no separate process — this runs inside your
application's process.

## Docker

The included `Dockerfile` builds an image whose default command runs a
minimal health server (`python -m openanchor serve --host 0.0.0.0 --port
8080`), exposing `GET /health` and `GET /version`. This is mainly useful
for smoke-testing the built image and for container orchestrators that
want something to health-check; it is **not** a general-purpose OpenAnchor
API server.

```bash
docker build -t openanchor .
docker run -p 8080:8080 openanchor
curl http://localhost:8080/health
```

`docker-compose.yml` wraps the same image with a named volume for
persisting a SQLite event store under `/app/data` if you mount your own
code that uses it.

## Semantic caching / MCP server

If you use `openanchor.SemanticCache` to expose the MCP tools
(`cache_prompt_embedding`, `find_cached_similar`, etc) over a network
port:

```python
from openanchor import SemanticCache

cache = SemanticCache(cache_db_path="/data/openanchor_cache.db")
# Defaults: host="127.0.0.1" (loopback only), no CORS origins allowed,
# read-only least-privilege permissions. Widening any of that is an
# explicit, deliberate opt-in — never silently exposed.
mcp_url = cache.start_mcp_connector()
```

To expose it beyond localhost (e.g. inside a private network only other
trusted services can reach), pass `host="0.0.0.0"` and explicit
`allowed_origins`/`allowed_roles` — do this only behind your own network
boundary/firewall/auth layer; OpenAnchor's connector itself does not
terminate TLS or authenticate requests.

Embeddings: real cosine-similarity search backed by Ollama
(`nomic-embed-text` or similar) when reachable at `localhost:11434`, with
an automatic, dependency-free fallback to a deterministic hashing
embedder when Ollama isn't available.

## Privacy

See the README's "Privacy" section for the full posture. Summary:

- Raw prompt/response excerpts are captured only if you explicitly opt in
  (`OpenAnchorMiddleware(capture_raw_content=True)`); the default records
  only a SHA-256 hash + length.
- Opt-in captures are run through best-effort PII/secret redaction by
  default.
- `SqliteEventStore(retention_days=N)` auto-purges events past the
  retention window.

## Observability

OTEL span export is real but opt-in (see `OTEL_SETUP_GUIDE.md`). Default
is off; enabling it does not send any prompt/response content over the
wire — only token counts, model/provider names, and performance metrics
become span attributes.
