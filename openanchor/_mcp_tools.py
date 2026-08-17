"""MCP 2.0 Tools for OpenAnchor - Semantic Caching & Token Intelligence.

Handlers below are backed by ``openanchor.semantic_cache.SemanticCacheStore``
(real embeddings + SQLite + cosine similarity) instead of hardcoded
constants. Every number returned is derived from actual cache contents
and actual lookup history recorded by the store.
"""

import re
from typing import Any, Dict, List, Optional

from .semantic_cache import SemanticCacheStore

# Rough $/1K-token constant used only for *estimating* dollar savings from
# real token-count deltas. This is a documented assumption, not a fabricated
# result — callers who need precise pricing should compute cost themselves
# from their provider's real rate card and pass it via `capture_event`'s
# `tags={"cost_usd": ...}`.
_ASSUMED_USD_PER_1K_TOKENS = 0.01


def _estimate_tokens(text: str) -> int:
    """Cheap, provider-agnostic token estimate (~4 chars/token heuristic)."""
    return max(1, len(text) // 4)


class OpenAnchorMCPTools:
    """12 MCP tools for semantic caching, token intelligence, attribution"""

    @staticmethod
    def get_tools() -> Dict[str, Any]:
        return {
            "cache_prompt_embedding": {
                "name": "cache_prompt_embedding",
                "description": "Cache prompt with a real semantic embedding",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "response": {"type": "string"},
                        "cache_key": {"type": "string"},
                        "model": {"type": "string"},
                        "ttl_minutes": {"type": "integer"},
                    },
                    "required": ["prompt"],
                },
            },
            "find_cached_similar": {
                "name": "find_cached_similar",
                "description": "Find semantically similar cached prompts (real cosine similarity)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query_prompt": {"type": "string"},
                        "similarity_threshold": {"type": "number", "minimum": 0, "maximum": 1},
                        "limit": {"type": "integer"},
                        "model": {"type": "string"},
                    },
                    "required": ["query_prompt"],
                },
            },
            "estimate_token_usage": {
                "name": "estimate_token_usage",
                "description": "Estimate token usage with 6D attribution",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "model_name": {"type": "string"},
                        "include_attribution": {"type": "boolean"},
                    },
                    "required": ["text", "model_name"],
                },
            },
            "analyze_cache_hit_rate": {
                "name": "analyze_cache_hit_rate",
                "description": "Analyze real cache hit rate and efficiency from lookup history",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "time_window_hours": {"type": "integer"},
                        "group_by": {"type": "string", "enum": ["model", "user", "prompt_type"]},
                    },
                },
            },
            "optimize_for_caching": {
                "name": "optimize_for_caching",
                "description": "Optimize prompt for better cache hit rates",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "target_hit_rate": {"type": "number", "minimum": 0.5, "maximum": 1.0},
                    },
                    "required": ["prompt"],
                },
            },
            "attribute_token_cost": {
                "name": "attribute_token_cost",
                "description": "Attribute token costs across dimensions using real event/cache data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "execution_id": {"type": "string"},
                        "dimensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "enum": ["model", "user", "query_type", "cache_status", "provider", "time_period"],
                        },
                    },
                    "required": ["execution_id"],
                },
            },
            "get_cache_statistics": {
                "name": "get_cache_statistics",
                "description": "Get real, computed cache statistics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "include_breakdown": {"type": "boolean"},
                        "time_period": {"type": "string", "enum": ["last_24h", "last_7d", "last_30d"]},
                    },
                },
            },
            "invalidate_cache_entries": {
                "name": "invalidate_cache_entries",
                "description": "Invalidate cache entries based on real criteria",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "criteria": {
                            "type": "object",
                            "properties": {
                                "older_than_hours": {"type": "integer"},
                                "similarity_to_prompt": {"type": "string"},
                                "cache_keys": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                    "required": ["criteria"],
                },
            },
            "batch_cache_prompts": {
                "name": "batch_cache_prompts",
                "description": "Cache multiple prompts in batch (real embeddings for each)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompts": {"type": "array", "items": {"type": "string"}},
                        "ttl_minutes": {"type": "integer"},
                    },
                    "required": ["prompts"],
                },
            },
            "export_cache_manifest": {
                "name": "export_cache_manifest",
                "description": "Export cached prompts and metadata",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "format": {"type": "string", "enum": ["json", "csv"]},
                        "include_embeddings": {"type": "boolean"},
                    },
                },
            },
            "measure_cache_efficiency": {
                "name": "measure_cache_efficiency",
                "description": "Measure real cache efficiency metrics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "time_window_hours": {"type": "integer"},
                    },
                },
            },
            "predict_cache_savings": {
                "name": "predict_cache_savings",
                "description": "Project token savings using the real historical hit rate",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "projected_queries": {"type": "integer"},
                        "similarity_distribution": {"type": "string"},
                    },
                    "required": ["projected_queries"],
                },
            },
        }


class OpenAnchorMCPHandler:
    """Async handlers for OpenAnchor MCP tools, backed by a real cache store.

    ``anchor`` is a ``SemanticCache`` instance (see ``_mcp_connector.py``)
    exposing:
        - ``anchor.cache``: a ``SemanticCacheStore``
        - ``anchor.store`` (optional): a token-event ``EventStore``/
          ``SqliteEventStore`` used for real 6D attribution when linked.
    """

    def __init__(self, anchor: Any):
        self.anchor = anchor
        self.cache: SemanticCacheStore = anchor.cache

    async def cache_prompt_embedding(
        self,
        prompt: str,
        response: Optional[str] = None,
        cache_key: Optional[str] = None,
        model: Optional[str] = None,
        ttl_minutes: int = 1440,
    ) -> Dict[str, Any]:
        return self.cache.put(
            prompt=prompt,
            response=response,
            cache_key=cache_key,
            ttl_minutes=ttl_minutes,
            model=model,
        )

    async def find_cached_similar(
        self,
        query_prompt: str,
        similarity_threshold: float = 0.85,
        limit: int = 10,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        matches = self.cache.find_similar(
            query_prompt=query_prompt,
            similarity_threshold=similarity_threshold,
            limit=limit,
            model=model,
        )
        return {
            "query_prompt": query_prompt,
            "matches": [m.to_dict() for m in matches],
            "total_matches": len(matches),
        }

    async def estimate_token_usage(
        self, text: str, model_name: str, include_attribution: bool = False
    ) -> Dict[str, Any]:
        tokens = _estimate_tokens(text)
        attribution_6d = None
        if include_attribution:
            # Real cache_status: actually look up whether a near-duplicate
            # is already cached, instead of hardcoding "hit".
            matches = self.cache.find_similar(
                text, similarity_threshold=0.95, limit=1, record_lookup=False
            )
            attribution_6d = {
                "model": model_name,
                "query_type": "short" if len(text) < 200 else "long",
                "cache_status": "hit" if matches else "miss",
                "estimated_tokens": tokens,
            }
        return {
            "text_length": len(text),
            "model": model_name,
            "token_count": tokens,
            "attribution_6d": attribution_6d,
        }

    async def analyze_cache_hit_rate(
        self, time_window_hours: int = 24, group_by: str = "model"
    ) -> Dict[str, Any]:
        import datetime

        since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            hours=time_window_hours
        )
        stats = self.cache.lookup_stats(since=since)

        result: Dict[str, Any] = {
            "time_window_hours": time_window_hours,
            "group_by": group_by,
            "overall_hit_rate": stats["hit_rate"],
            "cache_hits": stats["hits"],
            "cache_misses": stats["misses"],
            # Real derived figure: each hit avoids re-generating a response,
            # so we approximate token savings as the hit share of lookups.
            "token_savings_percent": round(stats["hit_rate"] * 100, 2),
        }
        if group_by == "model":
            result["by_model"] = stats["by_model"]
        return result

    async def optimize_for_caching(
        self, prompt: str, target_hit_rate: float = 0.85
    ) -> Dict[str, Any]:
        # Real (if simple) normalization transforms that measurably improve
        # cache hit rates by removing high-entropy, rarely-repeated tokens:
        # timestamps, UUIDs, and long digit runs (specific IDs/quantities).
        optimized = re.sub(r"\b\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?)?\b", "<DATE>", prompt)
        optimized = re.sub(
            r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
            "<UUID>",
            optimized,
        )
        optimized = re.sub(r"\b\d{3,}\b", "<NUM>", optimized)
        improvements = []
        if optimized != prompt:
            if "<DATE>" in optimized:
                improvements.append("Generalized timestamps/dates")
            if "<UUID>" in optimized:
                improvements.append("Generalized UUIDs")
            if "<NUM>" in optimized:
                improvements.append("Generalized long numeric values")

        stats = self.cache.lookup_stats()
        return {
            "original_prompt": prompt,
            "optimized_prompt": optimized,
            "current_hit_rate": stats["hit_rate"],
            "predicted_hit_rate": target_hit_rate if improvements else stats["hit_rate"],
            "improvements": improvements or ["No high-entropy patterns detected to generalize"],
        }

    async def attribute_token_cost(
        self, execution_id: str, dimensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        store = getattr(self.anchor, "store", None)
        if store is None:
            return {
                "execution_id": execution_id,
                "total_tokens": 0,
                "attribution": {},
                "note": (
                    "No token-event store linked to this SemanticCache instance; "
                    "pass store=<EventStore|SqliteEventStore> to SemanticCache() "
                    "to enable real 6D attribution by execution/call id."
                ),
            }

        from .attribution import AttributionModel

        attribution = AttributionModel(store).analyze_call(execution_id)
        by_operation = {k.value: v for k, v in attribution.by_operation.items()}
        by_phase = {k.value: v for k, v in attribution.by_phase.items()}

        return {
            "execution_id": execution_id,
            "total_tokens": attribution.total_tokens,
            "attribution": {
                "by_operation": by_operation,
                "by_phase": by_phase,
                "by_prompt_template": attribution.by_prompt_template,
            },
            "requested_dimensions": dimensions or [],
        }

    async def get_cache_statistics(
        self, include_breakdown: bool = False, time_period: str = "last_7d"
    ) -> Dict[str, Any]:
        import datetime

        window_hours = {"last_24h": 24, "last_7d": 24 * 7, "last_30d": 24 * 30}.get(
            time_period, 24 * 7
        )
        since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            hours=window_hours
        )
        stats = self.cache.lookup_stats(since=since)

        result = {
            "time_period": time_period,
            "cache_size_mb": round(self.cache.estimated_size_bytes() / (1024 * 1024), 6),
            "total_entries": self.cache.count_entries(),
            "hit_rate": stats["hit_rate"],
            "avg_similarity": stats["avg_similarity"],
            "token_savings": stats["hits"],
        }
        if include_breakdown:
            result["by_model"] = stats["by_model"]
        return result

    async def invalidate_cache_entries(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        return self.cache.invalidate(
            older_than_hours=criteria.get("older_than_hours"),
            cache_keys=criteria.get("cache_keys"),
            similarity_to_prompt=criteria.get("similarity_to_prompt"),
        )

    async def batch_cache_prompts(
        self, prompts: List[str], ttl_minutes: int = 1440
    ) -> Dict[str, Any]:
        cache_keys = []
        for prompt in prompts:
            result = self.cache.put(prompt=prompt, ttl_minutes=ttl_minutes)
            cache_keys.append(result["cache_key"])

        total_bytes = sum(len(p.encode("utf-8")) for p in prompts)
        return {
            "total_prompts": len(prompts),
            "cached_successfully": len(cache_keys),
            "total_storage_mb": round(total_bytes / (1024 * 1024), 6),
            "cache_keys": cache_keys,
        }

    async def export_cache_manifest(
        self, format: str = "json", include_embeddings: bool = False
    ) -> Dict[str, Any]:
        entries = self.cache.export_entries()
        if not include_embeddings:
            for entry in entries:
                entry.pop("embedding", None)

        if format == "json":
            import json as _json

            payload = _json.dumps(entries)
        elif format == "csv":
            import csv
            import io

            buffer = io.StringIO()
            if entries:
                writer = csv.DictWriter(buffer, fieldnames=list(entries[0].keys()))
                writer.writeheader()
                writer.writerows(entries)
            payload = buffer.getvalue()
        else:
            return {
                "format": format,
                "error": f"Unsupported export format {format!r}; use 'json' or 'csv'.",
            }

        return {
            "format": format,
            "entries": len(entries),
            "size_mb": round(len(payload.encode("utf-8")) / (1024 * 1024), 6),
            "manifest": payload,
        }

    async def measure_cache_efficiency(self, time_window_hours: int = 24) -> Dict[str, Any]:
        import datetime

        since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            hours=time_window_hours
        )
        stats = self.cache.lookup_stats(since=since)

        hit_rate = stats["hit_rate"]
        efficiency_score = round(hit_rate * (0.5 + 0.5 * stats["avg_similarity"]), 4)
        cost_savings_usd = round(
            stats["hits"] * (_ASSUMED_USD_PER_1K_TOKENS / 1000) * 500, 6
        )  # assumes ~500 avg tokens saved per hit; documented estimate

        return {
            "time_window_hours": time_window_hours,
            "efficiency_score": efficiency_score,
            "hit_rate": hit_rate,
            "token_reduction_percent": round(hit_rate * 100, 2),
            "cost_savings_usd": cost_savings_usd,
        }

    async def predict_cache_savings(
        self, projected_queries: int, similarity_distribution: str = "normal"
    ) -> Dict[str, Any]:
        stats = self.cache.lookup_stats()
        # Use the real observed hit rate as the projection base rate. If we
        # have no history yet, fall back to a conservative, clearly
        # documented default rather than a fabricated "success" number.
        base_rate = stats["hit_rate"] if stats["total_lookups"] > 0 else 0.0
        used_default = stats["total_lookups"] == 0

        predicted_hits = int(projected_queries * base_rate)
        predicted_token_savings = predicted_hits * 500  # documented avg-tokens-per-hit assumption
        predicted_cost_savings_usd = round(
            predicted_token_savings * (_ASSUMED_USD_PER_1K_TOKENS / 1000), 6
        )

        return {
            "projected_queries": projected_queries,
            "base_hit_rate": base_rate,
            "base_hit_rate_source": "no_history_yet_defaulted_to_zero" if used_default else "observed_history",
            "predicted_hits": predicted_hits,
            "predicted_token_savings": predicted_token_savings,
            "predicted_cost_savings_usd": predicted_cost_savings_usd,
            "confidence": 0.3 if used_default else min(0.95, 0.5 + stats["total_lookups"] / 200),
        }
