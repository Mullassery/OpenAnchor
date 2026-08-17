"""Tests for openanchor/_mcp_tools.py: OpenAnchorMCPHandler now backed by a
real SemanticCacheStore rather than hardcoded constants
(e.g. previously `overall_hit_rate: 0.68` always, regardless of input).
Previously had zero test coverage.

Handlers are async (MCP tool convention), so tests drive them with
``asyncio.run`` directly rather than pulling in pytest-asyncio as a new
test dependency.
"""

import asyncio

import pytest

from openanchor._mcp_connector import SemanticCache
from openanchor._mcp_tools import OpenAnchorMCPHandler, OpenAnchorMCPTools
from openanchor.collector import TokenCollector
from openanchor.semantic_cache import HashingEmbeddingProvider
from openanchor.storage import EventStore


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def handler(tmp_path):
    cache = SemanticCache(
        cache_db_path=str(tmp_path / "cache.db"),
        embedder=HashingEmbeddingProvider(dim=32),
    )
    h = OpenAnchorMCPHandler(cache)
    yield h
    cache.cache.close()


@pytest.fixture
def handler_with_store(tmp_path):
    store = EventStore()
    cache = SemanticCache(
        store=store,
        cache_db_path=str(tmp_path / "cache_linked.db"),
        embedder=HashingEmbeddingProvider(dim=32),
    )
    h = OpenAnchorMCPHandler(cache)
    yield h, store
    cache.cache.close()


class TestToolSchema:
    def test_get_tools_returns_12_tools(self):
        tools = OpenAnchorMCPTools.get_tools()
        assert len(tools) == 12

    def test_every_tool_has_input_schema(self):
        tools = OpenAnchorMCPTools.get_tools()
        for name, spec in tools.items():
            assert "inputSchema" in spec
            assert spec["name"] == name


class TestCachePromptEmbeddingAndFind:
    def test_cache_and_find_similar_real_roundtrip(self, handler):
        cached = run(handler.cache_prompt_embedding(
            "What's the weather like today?", response="Sunny", model="gpt-4"
        ))
        assert cached["cached"] is True
        assert cached["embedding_dim"] == 32

        found = run(handler.find_cached_similar(
            "What's the weather today?", similarity_threshold=0.3
        ))
        assert found["total_matches"] >= 1
        assert found["matches"][0]["response"] == "Sunny"

    def test_find_similar_no_match_for_unrelated_prompt(self, handler):
        run(handler.cache_prompt_embedding("What's the weather like today?"))
        found = run(handler.find_cached_similar(
            "Explain quantum entanglement", similarity_threshold=0.9
        ))
        assert found["total_matches"] == 0
        assert found["matches"] == []


class TestEstimateTokenUsage:
    def test_returns_real_length_derived_estimate(self, handler):
        result = run(handler.estimate_token_usage("a" * 400, "gpt-4"))
        assert result["text_length"] == 400
        assert result["token_count"] == 100  # 400 // 4
        assert result["attribution_6d"] is None

    def test_attribution_reflects_real_cache_status(self, handler):
        # Miss before caching.
        miss = run(handler.estimate_token_usage(
            "unique uncached text", "gpt-4", include_attribution=True
        ))
        assert miss["attribution_6d"]["cache_status"] == "miss"

        run(handler.cache_prompt_embedding("unique uncached text"))

        hit = run(handler.estimate_token_usage(
            "unique uncached text", "gpt-4", include_attribution=True
        ))
        assert hit["attribution_6d"]["cache_status"] == "hit"


class TestAnalyzeCacheHitRate:
    def test_hit_rate_reflects_actual_lookups_not_hardcoded(self, handler):
        run(handler.cache_prompt_embedding("cats are great pets", response="agreed"))
        run(handler.find_cached_similar("cats are great pets", similarity_threshold=0.5))  # hit
        run(handler.find_cached_similar("unrelated tax law text", similarity_threshold=0.9))  # miss

        result = run(handler.analyze_cache_hit_rate())
        assert result["cache_hits"] == 1
        assert result["cache_misses"] == 1
        assert result["overall_hit_rate"] == pytest.approx(0.5)

    def test_empty_history_gives_zero_not_fabricated_hit_rate(self, handler):
        result = run(handler.analyze_cache_hit_rate())
        assert result["overall_hit_rate"] == 0.0
        assert result["cache_hits"] == 0
        assert result["cache_misses"] == 0


class TestOptimizeForCaching:
    def test_generalizes_dates_and_numbers(self, handler):
        result = run(handler.optimize_for_caching(
            "On 2024-01-01T10:00:00 user 123456789 filed a request"
        ))
        assert "<DATE>" in result["optimized_prompt"]
        assert "<NUM>" in result["optimized_prompt"]
        assert len(result["improvements"]) >= 1

    def test_no_patterns_found_is_honest_about_it(self, handler):
        result = run(handler.optimize_for_caching("hello there"))
        assert result["optimized_prompt"] == "hello there"
        assert "No high-entropy patterns" in result["improvements"][0]


class TestAttributeTokenCost:
    def test_no_linked_store_returns_honest_zero(self, handler):
        result = run(handler.attribute_token_cost("exec_1"))
        assert result["total_tokens"] == 0
        assert "note" in result

    def test_linked_store_returns_real_attribution(self, handler_with_store):
        handler, store = handler_with_store
        collector = TokenCollector(store)
        collector.capture_event(
            call_id="exec_1", model="gpt-4", provider="openai",
            input_tokens=100, output_tokens=50,
        )

        result = run(handler.attribute_token_cost("exec_1"))
        assert result["total_tokens"] == 150


class TestGetCacheStatistics:
    def test_reflects_real_entry_count(self, handler):
        run(handler.cache_prompt_embedding("a"))
        run(handler.cache_prompt_embedding("b"))
        result = run(handler.get_cache_statistics())
        assert result["total_entries"] == 2
        assert result["cache_size_mb"] > 0


class TestInvalidateCacheEntries:
    def test_invalidate_by_cache_keys(self, handler):
        cached = run(handler.cache_prompt_embedding("a"))
        result = run(handler.invalidate_cache_entries({"cache_keys": [cached["cache_key"]]}))
        assert result["entries_invalidated"] == 1


class TestBatchCachePrompts:
    def test_caches_all_prompts_for_real(self, handler):
        result = run(handler.batch_cache_prompts(["a", "b", "c"]))
        assert result["cached_successfully"] == 3
        assert len(result["cache_keys"]) == 3
        assert len(set(result["cache_keys"])) == 3  # all unique


class TestExportCacheManifest:
    def test_json_export_contains_real_entries(self, handler):
        run(handler.cache_prompt_embedding("hello", response="world"))
        result = run(handler.export_cache_manifest(format="json"))
        assert result["entries"] == 1
        assert "hello" in result["manifest"]

    def test_csv_export(self, handler):
        run(handler.cache_prompt_embedding("hello"))
        result = run(handler.export_cache_manifest(format="csv"))
        assert "hello" in result["manifest"]

    def test_unsupported_format_is_honest_error(self, handler):
        result = run(handler.export_cache_manifest(format="parquet"))
        assert "error" in result


class TestMeasureCacheEfficiency:
    def test_zero_history_gives_zero_efficiency(self, handler):
        result = run(handler.measure_cache_efficiency())
        assert result["hit_rate"] == 0.0
        assert result["efficiency_score"] == 0.0


class TestPredictCacheSavings:
    def test_no_history_uses_documented_default_not_fabricated_hit_rate(self, handler):
        result = run(handler.predict_cache_savings(1000))
        assert result["base_hit_rate"] == 0.0
        assert result["base_hit_rate_source"] == "no_history_yet_defaulted_to_zero"
        assert result["predicted_hits"] == 0

    def test_uses_real_observed_hit_rate_when_available(self, handler):
        run(handler.cache_prompt_embedding("cats are great pets"))
        run(handler.find_cached_similar("cats are great pets", similarity_threshold=0.5))

        result = run(handler.predict_cache_savings(100))
        assert result["base_hit_rate_source"] == "observed_history"
        assert result["base_hit_rate"] == 1.0
        assert result["predicted_hits"] == 100
