"""Tests for real semantic caching (openanchor/semantic_cache.py).

Uses HashingEmbeddingProvider (dependency-free, deterministic) rather than
OllamaEmbeddingProvider so these tests don't require a running Ollama
server, while still exercising the real embedding + cosine-similarity +
SQLite cache-store logic end to end (not hardcoded constants).
"""


import pytest

from openanchor.semantic_cache import (
    HashingEmbeddingProvider,
    SemanticCacheStore,
    cosine_similarity,
)


@pytest.fixture
def store(tmp_path):
    s = SemanticCacheStore(
        db_path=str(tmp_path / "cache.db"),
        embedder=HashingEmbeddingProvider(dim=128),
    )
    yield s
    s.close()


class TestHashingEmbeddingProvider:
    def test_embed_is_deterministic(self):
        embedder = HashingEmbeddingProvider(dim=64)
        v1 = embedder.embed("hello world")
        v2 = embedder.embed("hello world")
        assert v1 == v2

    def test_embed_dimension_matches_config(self):
        embedder = HashingEmbeddingProvider(dim=32)
        assert len(embedder.embed("some text")) == 32
        assert embedder.dimension == 32

    def test_similar_text_scores_higher_than_unrelated_text(self):
        embedder = HashingEmbeddingProvider(dim=128)
        base = embedder.embed("What is the capital of France?")
        similar = embedder.embed("What is the capital city of France?")
        unrelated = embedder.embed("How do I bake a chocolate cake?")

        sim_similar = cosine_similarity(base, similar)
        sim_unrelated = cosine_similarity(base, unrelated)
        assert sim_similar > sim_unrelated

    def test_empty_text_returns_zero_vector(self):
        embedder = HashingEmbeddingProvider(dim=16)
        vec = embedder.embed("")
        assert vec == [0.0] * 16


class TestCosineSimilarity:
    def test_identical_vectors(self):
        assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_mismatched_length_returns_zero(self):
        assert cosine_similarity([1.0, 0.0], [1.0, 0.0, 0.0]) == 0.0

    def test_empty_vectors_return_zero(self):
        assert cosine_similarity([], []) == 0.0


class TestSemanticCacheStorePutAndFind:
    def test_put_returns_real_embedding_dim(self, store):
        result = store.put("hello world")
        assert result["embedding_dim"] == 128
        assert result["cached"] is True
        assert result["cache_key"]

    def test_find_similar_finds_a_near_duplicate(self, store):
        store.put("What is the capital of France?", response="Paris")
        matches = store.find_similar(
            "What is the capital city of France?", similarity_threshold=0.3
        )
        assert len(matches) == 1
        assert matches[0].response == "Paris"
        assert matches[0].similarity > 0.3

    def test_find_similar_excludes_unrelated_prompts(self, store):
        store.put("What is the capital of France?", response="Paris")
        matches = store.find_similar(
            "How do I bake a chocolate cake?", similarity_threshold=0.5
        )
        assert matches == []

    def test_find_similar_respects_limit(self, store):
        for i in range(5):
            store.put(f"prompt number {i} about weather")
        matches = store.find_similar("prompt about weather", similarity_threshold=0.0, limit=2)
        assert len(matches) <= 2

    def test_custom_cache_key_is_respected(self, store):
        result = store.put("hello", cache_key="my_key")
        assert result["cache_key"] == "my_key"

    def test_model_filter_excludes_other_models(self, store):
        store.put("hello world", model="gpt-4")
        matches = store.find_similar("hello world", similarity_threshold=0.5, model="claude-3")
        assert matches == []
        matches = store.find_similar("hello world", similarity_threshold=0.5, model="gpt-4")
        assert len(matches) == 1


class TestSemanticCacheStoreTTL:
    def test_ttl_none_means_no_expiry(self, store):
        result = store.put("hello", ttl_minutes=None)
        assert result["expires_at"] is None

    def test_negative_ttl_makes_entry_immediately_expired(self, store):
        store.put("hello", ttl_minutes=-1)
        assert store.count_entries(only_live=True) == 0
        assert store.count_entries(only_live=False) == 1

    def test_purge_expired_removes_expired_entries(self, store):
        store.put("hello", ttl_minutes=-1)
        store.put("world", ttl_minutes=1440)
        removed = store.purge_expired()
        assert removed == 1
        assert store.count_entries(only_live=False) == 1


class TestSemanticCacheStoreStats:
    def test_lookup_stats_reflects_real_hits_and_misses(self, store):
        store.put("cats are great pets", response="agreed")
        store.find_similar("cats are wonderful pets", similarity_threshold=0.3)  # hit
        store.find_similar("quantum physics equations", similarity_threshold=0.9)  # miss

        stats = store.lookup_stats()
        assert stats["total_lookups"] == 2
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == pytest.approx(0.5)

    def test_empty_store_has_zero_hit_rate_not_fabricated(self, store):
        stats = store.lookup_stats()
        assert stats["total_lookups"] == 0
        assert stats["hit_rate"] == 0.0

    def test_hit_count_increments_on_repeated_hits(self, store):
        store.put("shared prompt text", cache_key="k1")
        store.find_similar("shared prompt text", similarity_threshold=0.5)
        store.find_similar("shared prompt text", similarity_threshold=0.5)

        entries = store.export_entries()
        assert entries[0]["hit_count"] == 2

    def test_estimated_size_bytes_is_nonzero_after_put(self, store):
        assert store.estimated_size_bytes() == 0
        store.put("some reasonably long prompt text here")
        assert store.estimated_size_bytes() > 0


class TestSemanticCacheStoreInvalidate:
    def test_invalidate_by_cache_keys(self, store):
        r = store.put("hello")
        result = store.invalidate(cache_keys=[r["cache_key"]])
        assert result["entries_invalidated"] == 1
        assert store.count_entries() == 0

    def test_invalidate_by_similarity(self, store):
        store.put("The weather today is sunny and warm")
        store.put("Completely unrelated text about tax law")
        result = store.invalidate(
            similarity_to_prompt="The weather is sunny and warm today",
            similarity_threshold=0.5,
        )
        assert result["entries_invalidated"] == 1
        assert store.count_entries() == 1

    def test_invalidate_older_than_hours(self, store):
        store.put("old entry")
        result = store.invalidate(older_than_hours=-1)  # "older than the future" == everything
        assert result["entries_invalidated"] == 1

    def test_invalidate_nothing_matching_is_a_noop(self, store):
        store.put("hello")
        result = store.invalidate(cache_keys=["nonexistent"])
        assert result["entries_invalidated"] == 0
        assert store.count_entries() == 1


class TestSemanticCacheStoreClearAndExport:
    def test_clear_removes_everything(self, store):
        store.put("a")
        store.put("b")
        store.clear()
        assert store.count_entries() == 0
        assert store.lookup_stats()["total_lookups"] == 0

    def test_export_entries_returns_stored_data(self, store):
        store.put("hello", response="world", model="gpt-4")
        entries = store.export_entries()
        assert len(entries) == 1
        assert entries[0]["prompt"] == "hello"
        assert entries[0]["response"] == "world"
        assert entries[0]["model"] == "gpt-4"
