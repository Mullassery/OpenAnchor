# MCP tool reference

OpenAnchor exposes 12 MCP tools backed by a real `SemanticCache` (SQLite +
embeddings) and, when linked, a real token-event store. Tool schemas come from
`OpenAnchorMCPTools.get_tools()`; handlers live in
`openanchor/_mcp_tools.py`.

## Setup

```python
from openanchor._mcp_connector import SemanticCache
from openanchor._mcp_tools import OpenAnchorMCPHandler
from openanchor.storage import EventStore

cache = SemanticCache(
    store=EventStore(),              # optional; enables attribute_token_cost
    cache_db_path="openanchor.db",
)
handler = OpenAnchorMCPHandler(cache)

url = cache.start_mcp_connector()    # loopback by default
print(url)
```

Bring your own embedder with `SemanticCache(embedder=...)`. The default is
Ollama when reachable, otherwise a deterministic offline embedding provider.
See [`examples/mcp_openanchor.py`](../examples/mcp_openanchor.py).

## Tools

### `cache_prompt_embedding`

Cache a prompt (and optional response) with a real embedding.

| Argument | Type | Required | Notes |
| --- | --- | --- | --- |
| `prompt` | string | yes | Text to embed and cache |
| `response` | string | no | Cached response text |
| `cache_key` | string | no | Override the derived key |
| `model` | string | no | Model scope for lookups |
| `ttl_minutes` | integer | no | Default `1440` |

Returns the cached key, embedding dimension, and embedder name.

### `find_cached_similar`

Find semantically similar cached prompts by real cosine similarity.

| Argument | Type | Required | Notes |
| --- | --- | --- | --- |
| `query_prompt` | string | yes | Prompt to match |
| `similarity_threshold` | number | no | Default `0.85`, range 0–1 |
| `limit` | integer | no | Default `10` |
| `model` | string | no | Restrict matches to a model |

Returns `matches[]` (each with key, prompt, response, similarity, model) and
`total_matches`. The lookup is recorded in hit-rate history.

### `estimate_token_usage`

Cheap, provider-agnostic token estimate with optional 6D attribution.

| Argument | Type | Required | Notes |
| --- | --- | --- | --- |
| `text` | string | yes | Text to estimate |
| `model_name` | string | yes | Model label |
| `include_attribution` | boolean | no | Adds `attribution_6d` |

The estimate uses a documented ~4-characters-per-token heuristic, not a
provider tokenizer. Use PyTokenCalc when exact counts are required.

### `analyze_cache_hit_rate`

Real hit rate from recorded lookup history.

| Argument | Type | Required | Notes |
| --- | --- | --- | --- |
| `time_window_hours` | integer | no | Default `24` |
| `group_by` | string | no | `model`, `user`, or `prompt_type` |

Returns overall hit rate, hits, misses, and token-savings percentage.

### `optimize_for_caching`

Normalize high-entropy prompt content (dates, UUIDs, long numeric runs) to
improve cache hit rates.

| Argument | Type | Required | Notes |
| --- | --- | --- | --- |
| `prompt` | string | yes | Prompt to normalize |
| `target_hit_rate` | number | no | Default `0.85` |

Returns the optimized prompt and a list of applied improvements.

### `attribute_token_cost`

Real 6D attribution for one execution id, when the cache was created with an
event store.

| Argument | Type | Required | Notes |
| --- | --- | --- | --- |
| `execution_id` | string | yes | Event/execution id |
| `dimensions` | array | no | Requested dimension labels |

If no store is linked, returns zero totals with a `note` explaining how to
link one — it does not fabricate attribution.

### `get_cache_statistics`

Real cache size, entry count, hit rate, average similarity, and savings.

| Argument | Type | Required | Notes |
| --- | --- | --- | --- |
| `include_breakdown` | boolean | no | Adds per-model stats |
| `time_period` | string | no | `last_24h`, `last_7d`, `last_30d` |

### `invalidate_cache_entries`

Remove entries by age, key, or similarity.

| Argument | Type | Required | Notes |
| --- | --- | --- | --- |
| `criteria` | object | yes | Any of `older_than_hours`, `cache_keys`, `similarity_to_prompt` |

### `batch_cache_prompts`

Cache many prompts with real embeddings in one call.

| Argument | Type | Required | Notes |
| --- | --- | --- | --- |
| `prompts` | array of strings | yes | Prompts to cache |
| `ttl_minutes` | integer | no | Default `1440` |

Returns the number cached, storage estimate, and generated keys.

### `export_cache_manifest`

Export cache entries as JSON or CSV.

| Argument | Type | Required | Notes |
| --- | --- | --- | --- |
| `format` | string | no | `json` (default) or `csv` |
| `include_embeddings` | boolean | no | Default `false` |

Unsupported formats return an `error` field rather than throwing.

### `measure_cache_efficiency`

Hit-rate and similarity-based efficiency score plus documented cost estimate.

| Argument | Type | Required | Notes |
| --- | --- | --- | --- |
| `time_window_hours` | integer | no | Default `24` |

`cost_savings_usd` uses a documented estimate (~500 tokens per hit at
$0.01/1K tokens), not a provider bill.

### `predict_cache_savings`

Project savings from observed history.

| Argument | Type | Required | Notes |
| --- | --- | --- | --- |
| `projected_queries` | integer | yes | Queries to project |
| `similarity_distribution` | string | no | Default `"normal"` |

With no history, the base hit rate is explicitly `0.0` with
`base_hit_rate_source: "no_history_yet_defaulted_to_zero"` — never a made-up
success rate.

## Calling tools directly

The handlers are plain async methods, so they can be used without an MCP
client:

```python
import asyncio
from openanchor._mcp_connector import SemanticCache
from openanchor._mcp_tools import OpenAnchorMCPHandler

async def main():
    cache = SemanticCache(cache_db_path=":memory:")
    handler = OpenAnchorMCPHandler(cache)
    await handler.cache_prompt_embedding("hello", response="hi")
    print(await handler.find_cached_similar("hello", similarity_threshold=0.5))

asyncio.run(main())
```

## Performance

Run the stdlib-only benchmark for latency and throughput on your machine:

```bash
python scripts/benchmark_mcp_tools.py
```

It reports cache-write and cache-lookup latency distribution plus lookups per
second against a temporary SQLite cache. Numbers depend on the embedder, so do
not treat them as universal.
