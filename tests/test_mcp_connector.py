"""Tests for openanchor/_mcp_connector.py: secure-by-default config lockdown
and SemanticCache wiring. Previously had zero test coverage.
"""

import pytest

from openanchor._mcp_connector import SemanticCache, _MCPAnchorConnector
from openanchor.semantic_cache import HashingEmbeddingProvider


@pytest.fixture
def semantic_cache(tmp_path):
    cache = SemanticCache(
        cache_db_path=str(tmp_path / "cache.db"),
        embedder=HashingEmbeddingProvider(dim=32),
    )
    yield cache
    cache.cache.close()


class TestSemanticCacheConstruction:
    def test_creates_real_cache_store(self, semantic_cache):
        result = semantic_cache.cache.put("hello world")
        assert result["cached"] is True

    def test_store_is_none_by_default(self, semantic_cache):
        assert semantic_cache.store is None

    def test_store_can_be_linked(self, tmp_path):
        from openanchor.storage import EventStore

        store = EventStore()
        cache = SemanticCache(
            store=store,
            cache_db_path=str(tmp_path / "cache2.db"),
            embedder=HashingEmbeddingProvider(dim=32),
        )
        assert cache.store is store
        cache.cache.close()


class TestDabConfigSecureDefaults:
    """The audit's BLOCKER-adjacent finding: _generate_dab_config previously
    defaulted to host=0.0.0.0, cors origins=["*"], and wildcard permissions.
    """

    def test_default_host_is_loopback(self, semantic_cache):
        connector = _MCPAnchorConnector(anchor=semantic_cache, port=9999)
        config = connector._generate_dab_config({"tool_a": {}})
        assert config["runtime"]["host"] == "127.0.0.1"

    def test_default_cors_origins_is_empty_not_wildcard(self, semantic_cache):
        connector = _MCPAnchorConnector(anchor=semantic_cache, port=9999)
        config = connector._generate_dab_config({"tool_a": {}})
        assert config["runtime"]["cors"]["origins"] == []

    def test_default_permissions_are_read_only_user_role(self, semantic_cache):
        connector = _MCPAnchorConnector(anchor=semantic_cache, port=9999)
        config = connector._generate_dab_config({"tool_a": {}, "tool_b": {}})
        for entity in config["entities"].values():
            perm = entity["permissions"][0]
            assert perm["actions"] == ["read"]
            assert perm["roles"] == ["user"]
            assert "*" not in perm["actions"]
            assert "*" not in perm["roles"]

    def test_explicit_opt_in_widens_host(self, semantic_cache):
        connector = _MCPAnchorConnector(anchor=semantic_cache, port=9999, host="0.0.0.0")
        config = connector._generate_dab_config({"tool_a": {}})
        assert config["runtime"]["host"] == "0.0.0.0"

    def test_explicit_opt_in_widens_cors_and_roles(self, semantic_cache):
        connector = _MCPAnchorConnector(
            anchor=semantic_cache,
            port=9999,
            allowed_origins=["https://example.com"],
            allowed_roles=["admin"],
        )
        config = connector._generate_dab_config({"tool_a": {}})
        assert config["runtime"]["cors"]["origins"] == ["https://example.com"]
        assert config["entities"]["tool_a"]["permissions"][0]["roles"] == ["admin"]

    def test_start_mcp_connector_default_host_is_loopback(self, semantic_cache):
        assert semantic_cache.mcp_connector is None
        # We don't actually start the `dab` subprocess (not installed in
        # test envs) — just verify the connector object is configured with
        # the secure default before start_mcp_connector attempts to launch
        # a subprocess it can't find.
        connector = _MCPAnchorConnector(anchor=semantic_cache, port=9999)
        assert connector.host == "127.0.0.1"


class TestMcpToolWiring:
    def test_get_mcp_tools_returns_12_tools(self, semantic_cache):
        connector = _MCPAnchorConnector(anchor=semantic_cache, port=9999)
        tools = connector.get_mcp_tools()
        assert len(tools) == 12

    def test_get_tool_handlers_returns_handler_bound_to_cache(self, semantic_cache):
        connector = _MCPAnchorConnector(anchor=semantic_cache, port=9999)
        handler = connector.get_tool_handlers()
        assert handler.cache is semantic_cache.cache
