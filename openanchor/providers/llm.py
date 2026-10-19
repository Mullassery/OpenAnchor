"""OpenAnchor LLM provider package.

OpenAnchor treats ``provider``/``model`` as string metadata on token events,
but now ships real LLM provider clients so you can actually *route* calls
through OpenRouter (an OpenAI-compatible meta-provider that aggregates OpenAI,
Anthropic, Google, Meta, Mistral, Cohere, AWS Bedrock, Microsoft Foundry,
Google Model Garden, Build.NVIDIA, and many more behind a single endpoint).

The module exposes:
    * ``LLMProvider`` — abstract base class (``complete`` / ``complete_async``)
    * ``OpenRouterProvider`` — concrete OpenAI-compatible client against
      ``https://openrouter.ai/api/v1/chat/completions``
    * ``LLMProviderRegistry`` — name → provider mapping with auto-discovery
    * ``default_provider`` / ``set_default_provider`` — global default switch

Example::

    from openanchor.providers import OpenRouterProvider, LLMProviderRegistry

    provider = OpenRouterProvider(
        api_key="sk-or-...",   # or rely on OPENROUTER_API_KEY env var
        model="openrouter/auto",
    )
    result = provider.complete("Explain quantum computing in one sentence.")
    # result = LLMResponse(text=..., input_tokens=..., output_tokens=...,
    #                      provider="openrouter", model="openrouter/auto")

    # Switch models on the same provider instance:
    provider.model = "anthropic/claude-3-haiku"
    result = provider.complete("Same prompt, different model.")

    # Or register and switch via the registry:
    registry = LLMProviderRegistry()
    registry.register("cheap", OpenRouterProvider(model="openrouter/auto"))
    registry.register("smart", OpenRouterProvider(model="anthropic/claude-3-opus"))
    active = registry.get("cheap")
"""

from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "OpenRouterProvider",
    "LLMProviderRegistry",
    "default_provider",
    "set_default_provider",
    "get_default_provider",
]

# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------


@dataclass
class LLMResponse:
    """Result of a single LLM completion call."""

    text: str
    input_tokens: int
    output_tokens: int
    provider: str
    model: str
    latency_ms: float
    finish_reason: str = "unknown"
    raw: Optional[Dict[str, Any]] = None

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class LLMProvider(ABC):
    """Interface for LLM completion providers.

    Substituting one provider for another (e.g. OpenRouter → a direct
    OpenAI key) is a one-line change at construction; switching *models*
    is a property assignment or a registry lookup.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Stable provider identifier (used as the `provider` label on events)."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Currently selected model."""

    @model.setter
    @abstractmethod
    def model(self, value: str) -> None:  # noqa: D401 - setter doc on ABC
        ...

    @abstractmethod
    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Synchronous chat completion."""

    @abstractmethod
    def complete_async(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Asynchronous chat completion (default implementation wraps sync)."""

    def capture_compatible_event(
        self,
        collector: Any,
        *,
        call_id: str,
        prompt: str,
        response: LLMResponse,
        phase: Any = None,
        operation_type: Any = None,
        **extra: Any,
    ) -> Any:
        """Convenience: capture a :class:`openanchor.collector.TokenEvent`
        from an :class:`LLMResponse` using the same ``capture_event``
        signature the rest of OpenAnchor expects."""
        from .collector import OperationType, RequestPhase

        return collector.capture_event(
            call_id=call_id,
            model=response.model,
            provider=self.provider_name,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            phase=phase or RequestPhase.REQUEST,
            operation_type=operation_type or OperationType.OTHER,
            latency_ms=response.latency_ms,
            request_data={"prompt": prompt, **kwargs_from_response(response)},
            response_data={"text": response.text, "finish_reason": response.finish_reason},
            **extra,
        )


def kwargs_from_response(response: LLMResponse) -> Dict[str, Any]:
    return {
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "finish_reason": response.finish_reason,
        "latency_ms": response.latency_ms,
    }


# ---------------------------------------------------------------------------
# OpenRouter provider (OpenAI-compatible)
# ---------------------------------------------------------------------------


class OpenRouterProvider(LLMProvider):
    """OpenRouter chat-completions client.

    OpenRouter exposes a drop-in OpenAI-compatible API at
    ``https://openrouter.ai/api/v1/chat/completions``.  Because it is a
    meta-provider, changing the ``model`` string lets you route to any of
    the hundreds of models OpenRouter proxies (OpenAI GPT, Anthropic Claude,
    Google Gemini, Meta Llama, Mistral, Cohere, AWS Bedrock, Microsoft
    Foundry, Google Model Garden, Build.NVIDIA, …) without changing code.
    """

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "openrouter/auto"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        provider_name: str = "openrouter",
    ):
        self._api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self._model = model
        self._base_url = (
            base_url or os.environ.get("OPENROUTER_BASE_URL") or self.DEFAULT_BASE_URL
        ).rstrip("/")
        self._timeout = timeout
        self._provider_name = provider_name
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/Mullassery/OpenAnchor",
                "X-Title": "OpenAnchor",
            }
        )

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model(self) -> str:
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        self._model = value

    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        start = time.perf_counter()
        payload: Dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
        }
        # Forward common OpenAI-compatible sampling params if supplied.
        for key in ("max_tokens", "temperature", "top_p", "stream"):
            if key in kwargs:
                payload[key] = kwargs[key]

        try:
            resp = self._session.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                timeout=self._timeout,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:  # pragma: no cover - network
            raise RuntimeError(f"OpenRouter request failed: {exc}") from exc
        except ValueError as exc:  # pragma: no cover - bad JSON
            raise RuntimeError(f"OpenRouter returned invalid JSON: {exc}") from exc

        latency_ms = (time.perf_counter() - start) * 1000.0

        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        text = message.get("content", "")
        finish_reason = choice.get("finish_reason", "unknown")

        usage = data.get("usage", {}) or {}
        input_tokens = int(usage.get("prompt_tokens", 0))
        output_tokens = int(usage.get("completion_tokens", 0))

        return LLMResponse(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider=self._provider_name,
            model=self._model,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            raw=data,
        )

    def complete_async(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Default async wrapper — delegates to the synchronous client.

        Override in subclasses that have a native async HTTP client."""
        return self.complete(prompt, **kwargs)


# ---------------------------------------------------------------------------
# Registry for model/provider switching
# ---------------------------------------------------------------------------


class LLMProviderRegistry:
    """Name → ``LLMProvider`` mapping with a switchable default.

    Use this when you want to keep several provider/model combinations
    ready and flip between them by name (e.g. routing by task complexity,
    cost tier, or user preference).
    """

    def __init__(self) -> None:
        self._providers: Dict[str, LLMProvider] = {}
        self._default: Optional[str] = None

    def register(self, name: str, provider: LLMProvider) -> None:
        self._providers[name] = provider
        if self._default is None:
            self._default = name

    def get(self, name: str) -> LLMProvider:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise KeyError(
                f"No provider registered under {name!r}. Known: {sorted(self._providers)}"
            ) from exc

    def list(self) -> list[str]:
        return sorted(self._providers)

    @property
    def default(self) -> Optional[str]:
        return self._default

    @default.setter
    def default(self, name: str) -> None:
        if name not in self._providers:
            raise KeyError(
                f"No provider registered under {name!r}. Known: {sorted(self._providers)}"
            )
        self._default = name

    def switch(self, name: str) -> LLMProvider:
        """Set the default provider to ``name`` and return it."""
        self.default = name
        return self.get(name)

    def complete(self, prompt: str, name: Optional[str] = None, **kwargs: Any) -> LLMResponse:
        provider = self.get(name or self._default)
        if provider is None:
            raise RuntimeError("No default provider set — register one first.")
        return provider.complete(prompt, **kwargs)


# Module-level default registry for one-liner usage.
_default_registry = LLMProviderRegistry()


def default_provider() -> Optional[LLMProvider]:
    """Return the module-level default provider (or None if unset)."""
    name = _default_registry.default
    return _default_registry.get(name) if name else None


def set_default_provider(provider: LLMProvider, name: Optional[str] = None) -> None:
    """Register a provider as the module-level default.

    ``name`` defaults to ``provider.provider_name``.
    """
    _default_registry.register(name or provider.provider_name, provider)
    _default_registry.default = name or provider.provider_name


def get_default_provider() -> Optional[LLMProvider]:
    return default_provider()
