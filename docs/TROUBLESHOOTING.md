# Troubleshooting

## The MCP connector does not start

- `start_mcp_connector()` binds to loopback by default. Check that the port is
  free and that a local firewall is not blocking loopback.
- If you passed `host="0.0.0.0"`, ensure that is a deliberate choice and that
  access is controlled. The default is intentionally local-only.
- Stop a previous connector before starting another one:
  `cache.stop_mcp_connector()`.

## `attribute_token_cost` returns zero with a note

Expected when the cache has no event store. Link one:

```python
from openanchor.storage import EventStore
cache = SemanticCache(store=EventStore(), cache_db_path="openanchor.db")
```

Then record events through the instrumentation layer for the execution id you
query. Zero is honest output for "no data", not a failure to look up.

## `find_cached_similar` never matches

- Lower `similarity_threshold` (for example `0.5`) and retry.
- Confirm both prompts used the same embedder. Different embedders produce
  incomparable vectors.
- The default offline embedder is deterministic but shallow; semantic matches
  are weaker than a real embedding model. Use Ollama or a custom embedder for
  production quality.
- Check `model=` filters: a lookup scoped to one model will not match another.

## Cache hit rate stays at zero

- Hit rate is derived from **recorded lookups**. `find_cached_similar` records
  lookups by default; `estimate_token_usage` intentionally uses
  `record_lookup=False` for its internal probe.
- A cache with writes but no lookups has no hit-rate history yet.
- `predict_cache_savings` reports `no_history_yet_defaulted_to_zero` until
  lookups exist.

## `estimate_token_usage` numbers differ from my provider

The tool uses a documented ~4-characters-per-token heuristic. It is not a
provider tokenizer. Use PyTokenCalc for exact counts, and treat this tool as a
fast estimate only.

## `export_cache_manifest` returns an error field

Only `json` and `csv` are supported. The handler returns
`{"error": ...}` for other formats instead of raising, so check that field when
consuming exports.

## SQLite database errors / locked database

- Ensure only one process writes to the same `cache_db_path` at a time, or use
  a dedicated database per process.
- Use `":memory:"` for tests and short-lived processes.
- Do not place the database on a filesystem without SQLite locking support.

## Embedding backend is unreachable

If Ollama is not running, OpenAnchor falls back to the deterministic offline
embedder. This is intentional and lets tests/CI run without network access. If
you require a specific backend, pass it explicitly and handle its errors at
startup.

## Tests fail after changing cache behavior

Run the focused suite first:

```bash
pytest tests/test_mcp_tools.py tests/test_mcp_connector.py tests/test_semantic_cache.py -q
```

The MCP tests assert values derived from real cache contents. If a default or
assumption changes, update the test and the documented assumption together —
do not hardcode an expected value that the implementation no longer produces.

## I need to reproduce a result

Capture the prompt, model, embedder name, cache DB path, and the tool arguments
and response. Similarity results depend on both the embedder and the exact
cached contents; a response alone is not reproducible.
