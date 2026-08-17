"""MCP Connector for OpenAnchor - Semantic Caching & Token Intelligence"""

import json
import logging
import subprocess  # nosec B404
import tempfile
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .semantic_cache import EmbeddingProvider, SemanticCacheStore

logger = logging.getLogger(__name__)

try:
    from statguardian._mcp_connector import BaseMCPConnector  # type: ignore[import-not-found]
except ImportError:
    class BaseMCPConnector(ABC):  # type: ignore[no-redef]
        def __init__(self, project_name: str, port: int = 8765, host: str = "127.0.0.1"):
            self.project_name = project_name
            self.port = port
            self.host = host
            self.dab_process: Optional[subprocess.Popen] = None
            self._ready = False

        @abstractmethod
        def get_mcp_tools(self) -> Dict[str, Any]:
            pass

        @abstractmethod
        def get_tool_handlers(self) -> Any:
            pass

        def start_mcp_connector(self) -> str:
            logger.info(f"Starting {self.project_name} MCP...")
            try:
                tools = self.get_mcp_tools()
                self.handler = self.get_tool_handlers()
                config = self._generate_dab_config(tools)
                config_path = self._write_temp_config(config)
                self._start_dab_subprocess(config_path)
                self._ready = True
                return f"http://{self.host}:{self.port}/mcp"
            except Exception as e:
                logger.error(f"Failed: {e}")
                raise

        def stop_mcp_connector(self):
            if self.dab_process:
                try:
                    self.dab_process.terminate()
                    self.dab_process.wait(timeout=5)
                except (subprocess.TimeoutExpired, OSError):
                    pass
                self._ready = False

        def _generate_dab_config(
            self,
            tools: Dict[str, Any],
            allowed_origins: Optional[List[str]] = None,
            allowed_roles: Optional[List[str]] = None,
        ) -> Dict:
            """Build the connector's runtime config with secure-by-default settings.

            Defaults are locked down deliberately:
              - host binds to loopback only (``self.host``, default
                "127.0.0.1"), not "0.0.0.0" — the previous default exposed
                the MCP/REST/GraphQL endpoints on every network interface
                the host had, including public ones, by default.
              - CORS origins default to none (no wildcard "*").
              - Tool permissions are least-privilege: only "read" actions
                for the "user" role by default, not wildcard actions for
                wildcard roles. Callers that genuinely need broader access
                (e.g. a trusted internal admin tool) must opt in explicitly
                via ``allowed_roles``/``allowed_origins`` — nothing here
                grants that by default.

            Wider exposure (binding to 0.0.0.0, wildcard CORS, or
            write/admin permissions) requires explicit opt-in by
            constructing the connector with different values — it is never
            the default.
            """
            origins = allowed_origins if allowed_origins is not None else []
            roles = allowed_roles if allowed_roles is not None else ["user"]

            return {
                "runtime": {
                    "host": self.host,
                    "port": self.port,
                    "cors": {"origins": origins},
                },
                "entities": {
                    k: {
                        "source": k,
                        "permissions": [{"actions": ["read"], "roles": roles}],
                    }
                    for k in tools.keys()
                },
                "rest": {"enabled": True, "path": "/api"},
                "graphql": {"enabled": True, "path": "/graphql"},
                "mcp": {"enabled": True, "path": "/mcp"},
            }

        def _write_temp_config(self, config: Dict) -> str:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(config, f)
                return f.name

        def _start_dab_subprocess(self, config_path: str):
            # Fixed command name + a config path we generated ourselves
            # (via _write_temp_config); no untrusted/user-controlled input
            # reaches argv, and shell=True is deliberately not used.
            self.dab_process = subprocess.Popen(  # nosec B603 B607
                ["dab", "start", "--config", config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        def is_ready(self) -> bool:
            return self._ready


class SemanticCache:
    """Semantic caching with real embeddings, real storage, real 6D token attribution.

    Args:
        store: Optional token-event store (``EventStore``/``SqliteEventStore``)
            to link for real per-execution 6D attribution via
            ``attribute_token_cost``. If omitted, that tool reports that no
            store is linked instead of fabricating numbers.
        cache_db_path: SQLite path for the semantic cache (embeddings +
            cached responses).
        embedder: Optional custom ``EmbeddingProvider``. Defaults to
            ``semantic_cache.default_embedder()``, which uses Ollama when
            reachable and a dependency-free hashing embedder otherwise.
    """

    def __init__(
        self,
        store: Optional[Any] = None,
        cache_db_path: str = "openanchor_cache.db",
        embedder: Optional[EmbeddingProvider] = None,
    ):
        self.store = store
        self.cache = SemanticCacheStore(db_path=cache_db_path, embedder=embedder)
        self.mcp_connector: Optional[Any] = None

    def start_mcp_connector(
        self,
        port: int = 8779,
        host: str = "127.0.0.1",
        allowed_origins: Optional[List[str]] = None,
        allowed_roles: Optional[List[str]] = None,
    ) -> str:
        """Start the MCP connector.

        ``host`` defaults to loopback-only ("127.0.0.1"). Pass
        ``host="0.0.0.0"`` explicitly (and set ``allowed_origins``/
        ``allowed_roles`` deliberately) to expose this beyond localhost —
        that is an explicit opt-in, never the default.
        """
        self.mcp_connector = _MCPAnchorConnector(
            anchor=self,
            port=port,
            host=host,
            allowed_origins=allowed_origins,
            allowed_roles=allowed_roles,
        )
        return str(self.mcp_connector.start_mcp_connector())

    def stop_mcp_connector(self):
        if self.mcp_connector:
            self.mcp_connector.stop_mcp_connector()


class _MCPAnchorConnector(BaseMCPConnector):
    def __init__(
        self,
        anchor: SemanticCache,
        port: int = 8779,
        host: str = "127.0.0.1",
        allowed_origins: Optional[List[str]] = None,
        allowed_roles: Optional[List[str]] = None,
    ):
        super().__init__("OpenAnchor", port=port, host=host)
        self.anchor = anchor
        self._allowed_origins = allowed_origins
        self._allowed_roles = allowed_roles

    def get_mcp_tools(self) -> Dict[str, Any]:
        from openanchor._mcp_tools import OpenAnchorMCPTools
        return OpenAnchorMCPTools.get_tools()

    def get_tool_handlers(self) -> Any:
        from openanchor._mcp_tools import OpenAnchorMCPHandler
        return OpenAnchorMCPHandler(self.anchor)

    def _generate_dab_config(self, tools: Dict[str, Any]) -> Dict:
        return dict(
            super()._generate_dab_config(
                tools,
                allowed_origins=self._allowed_origins,
                allowed_roles=self._allowed_roles,
            )
        )
