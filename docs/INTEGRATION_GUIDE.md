# Integration guide

OpenAnchor is a library plus a local MCP server. There is no hosted service and
no required network dependency beyond your chosen embedding backend.

## 1. Install

```bash
pip install openanchor
```

For OTEL export:

```bash
pip install "openanchor[otel]"
```

## 2. Choose a cache backend

Semantic caching uses SQLite and an embedding provider.

```python
from openanchor._mcp_connector import SemanticCache
from openanchor.semantic_cache import HashingEmbeddingProvider

cache = SemanticCache(
    cache_db_path="openanchor.db",
    embedder=HashingEmbeddingProvider(dim=256),  # deterministic/offline
)
```

- Use the default embedder when Ollama is available for higher-quality
  similarity.
- Use `HashingEmbeddingProvider` for tests, CI, and fully offline deployments.
- Use a custom embedder by implementing the provider interface expected by
  `SemanticCache`.

## 3. Link token events (optional)

`attribute_token_cost` needs an event store:

```python
from openanchor.storage import EventStore

cache = SemanticCache(store=EventStore(), cache_db_path="openanchor.db")
```

For durable storage use `SqliteEventStore` (see `openanchor/storage.py`). If no
store is linked, attribution returns zero with an explicit note instead of
inventing numbers.

## 4. Use the middleware

Instrument your LLM client with `openanchor.instrumentation`; events are
recorded into the store, and the cache can answer near-duplicate prompts before
calling the provider. See `examples/basic_usage.py` for the full flow.

## 5. Expose MCP tools

```python
url = cache.start_mcp_connector()  # binds 127.0.0.1 by default
print(url)
```

Register the connector URL with any MCP 2.0 client. The 12 tool schemas are
served from `OpenAnchorMCPTools.get_tools()`.

Only pass `host="0.0.0.0"` when you have deliberately put the service behind
authentication and network controls. The default loopback bind is intentional.

## 6. Integrate with sibling projects

| Project | Integration |
| --- | --- |
| PyTokenCalc | Exact provider token counts; pass counts into captured events |
| statguardian | Validate RAG/context data before caching or attributing |
| PyStreamMCP | Consume cache hit-rate/savings tools in cost-aware planning |
| OTEL backend | Export events/traces via `openanchor.otel` |

Keep OpenAnchor focused on token attribution and semantic caching; do not
duplicate provider tokenizers or data-quality logic here.

## 7. Verify

```bash
pytest -q
python examples/mcp_openanchor.py
python scripts/benchmark_mcp_tools.py
```

A successful integration has: real events in the store, non-zero lookup
history, and MCP tools returning values derived from that data (not defaults).

## Operational notes

- `cache_db_path` should be on persistent storage in production.
- Invalidate/retain cache entries deliberately;
  `invalidate_cache_entries` supports age, keys, and similarity criteria.
- Back up the SQLite database with the same care as any other stateful store.
- Do not log prompt text or responses unless your privacy policy allows it.
- `cost_savings_usd` from MCP tools is an estimate with documented
  assumptions; use your real rate card for billing.
