"""Optional automatic instrumentation for LLM SDKs.

OpenAnchor's collector accepts explicit events.  Most production apps use the
OpenTelemetry instrumentors from OpenLLMetry/OpenInference, so this module
bridges their span attributes into ``TokenCollector`` automatically.

Install an instrumentor extra, for example::

    pip install "openanchor[auto-instrument]"

Usage::

    from openanchor import TokenCollector, enable_auto_instrumentation
    collector = TokenCollector()
    enable_auto_instrumentation(collector)

Only spans that look like LLM/agent spans are processed; OpenAnchor's own
``openanchor.capture_event`` spans are skipped to avoid recursion or double
counting.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable, Optional

from .collector import TokenCollector
from .models import OperationType, RequestPhase

logger = logging.getLogger(__name__)


class InstrumentationUnavailable(RuntimeError):
    """Raised when auto-instrumentation is requested without OTEL/instrumentors."""


_TOKEN_KEYS = {
    "input": (
        "gen_ai.usage.input_tokens",
        "gen_ai.usage.prompt_tokens",
        "llm.token_count.prompt",
        "llm.token_count.input",
        "openinference.llm.token_count.prompt",
    ),
    "output": (
        "gen_ai.usage.output_tokens",
        "gen_ai.usage.completion_tokens",
        "llm.token_count.completion",
        "llm.token_count.output",
        "openinference.llm.token_count.completion",
    ),
}

_MODEL_KEYS = (
    "gen_ai.request.model",
    "gen_ai.response.model",
    "llm.model_name",
    "openinference.llm.model_name",
)
_PROVIDER_KEYS = (
    "gen_ai.system",
    "llm.system",
    "openinference.llm.system",
    "openinference.provider",
)
_SESSION_KEYS = (
    "session.id",
    "openinference.session.id",
    "gen_ai.conversation.id",
)
_CALL_KEYS = (
    "llm.request_id",
    "gen_ai.response.id",
    "openinference.llm.request_id",
)

_OPERATION_MAP = {
    "LLM": OperationType.MODEL_REASONING,
    "CHAT": OperationType.MODEL_REASONING,
    "COMPLETION": OperationType.MODEL_REASONING,
    "RETRIEVER": OperationType.RETRIEVAL,
    "RETRIEVAL": OperationType.RETRIEVAL,
    "EMBEDDING": OperationType.OTHER,
    "TOOL": OperationType.OTHER,
    "AGENT": OperationType.MODEL_REASONING,
}


def _first(attrs: dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        if key in attrs and attrs[key] not in (None, ""):
            return attrs[key]
    return default


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


class OpenAnchorSpanProcessor:
    """OTEL ``SpanProcessor`` that writes LLM spans into a TokenCollector.

    Implements the OpenTelemetry SpanProcessor protocol (``on_start``,
    ``on_end``, ``shutdown``, ``force_flush``). It can also be used directly
    with a duck-typed readable span in tests.
    """

    def __init__(self, collector: Optional[TokenCollector] = None):
        self.collector = collector or TokenCollector()
        self._seen: set[tuple[str, str]] = set()

    def on_start(self, span: Any, parent_context: Any = None) -> None:  # noqa: D401,ARG002
        return None

    def _is_llm_span(self, span: Any, attrs: dict[str, Any]) -> bool:
        name = str(getattr(span, "name", ""))
        if name == "openanchor.capture_event":
            return False
        if any(key in attrs for key in _TOKEN_KEYS["input"]) or any(
            key in attrs for key in _TOKEN_KEYS["output"]
        ):
            return True
        kind = str(attrs.get("openinference.span.kind") or "").upper()
        if kind in _OPERATION_MAP:
            return True
        scope = getattr(getattr(span, "instrumentation_scope", None), "name", "") or ""
        return scope.startswith("opentelemetry.instrumentation.")

    def on_end(self, span: Any) -> None:
        attrs = dict(getattr(span, "attributes", None) or {})
        if not self._is_llm_span(span, attrs):
            return

        input_tokens = _as_int(_first(attrs, _TOKEN_KEYS["input"], 0))
        output_tokens = _as_int(_first(attrs, _TOKEN_KEYS["output"], 0))
        if input_tokens == 0 and output_tokens == 0:
            return

        span_context = (
            getattr(span, "context", None) or getattr(span, "get_span_context", lambda: None)()
        )
        trace_id = format(getattr(span_context, "trace_id", 0) or 0, "032x")
        span_id = format(getattr(span_context, "span_id", 0) or 0, "016x")
        key = (trace_id, span_id)
        if key != ("0" * 32, "0" * 16) and key in self._seen:
            return
        self._seen.add(key)

        duration_ns = getattr(span, "end_time", 0) - getattr(span, "start_time", 0)
        latency_ms = duration_ns / 1_000_000 if duration_ns else None
        model = str(_first(attrs, _MODEL_KEYS, "unknown"))
        provider = str(_first(attrs, _PROVIDER_KEYS, "unknown"))
        session_id = _first(attrs, _SESSION_KEYS)
        call_id = str(_first(attrs, _CALL_KEYS, f"{trace_id}:{span_id}"))

        if session_id:
            self.collector.set_session(str(session_id))

        kind = str(attrs.get("openinference.span.kind") or "").upper()
        operation = _OPERATION_MAP.get(kind, OperationType.OTHER)

        self.collector.capture_event(
            call_id=call_id,
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            phase=RequestPhase.RESPONSE,
            operation_type=operation,
            latency_ms=latency_ms,
            request_data={
                "otel.trace_id": trace_id,
                "otel.span_id": span_id,
                "otel.span_name": getattr(span, "name", ""),
            },
            tags={
                "instrumentation": "auto",
                "openinference.span.kind": kind,
            },
        )

    def shutdown(self) -> None:
        return None

    def force_flush(self, timeout_millis: int = 30000) -> bool:  # noqa: ARG002
        return True


def _instrumentor_classes() -> dict[str, str]:
    """Map friendly names to OpenLLMetry instrumentor import paths."""
    return {
        "openai": "opentelemetry.instrumentation.openai.OpenAIInstrumentor",
        "anthropic": "opentelemetry.instrumentation.anthropic.AnthropicInstrumentor",
        "langchain": "opentelemetry.instrumentation.langchain.LangChainInstrumentor",
        "cohere": "opentelemetry.instrumentation.cohere.CohereInstrumentor",
        "mistralai": "opentelemetry.instrumentation.mistralai.MistralAIInstrumentor",
        "groq": "opentelemetry.instrumentation.groq.GroqInstrumentor",
    }


def enable_auto_instrumentation(
    collector: Optional[TokenCollector] = None,
    instrumentors: Optional[Iterable[str]] = None,
    tracer_provider: Optional[Any] = None,
) -> Any:
    """Enable OpenLLMetry/OpenInference instrumentors and feed OpenAnchor.

    Args:
        collector: Collector receiving normalized token events.
        instrumentors: Names from ``openai``, ``anthropic``, ``langchain``,
            ``cohere``, ``mistralai``, ``groq``. Defaults to all installed.
        tracer_provider: Optional pre-built OTEL TracerProvider. If omitted,
            a provider with ``OpenAnchorSpanProcessor`` is created.

    Returns:
        The ``TracerProvider`` in use.

    Raises:
        InstrumentationUnavailable: If OTEL SDK or no instrumentor is installed.
    """
    try:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
    except ImportError as exc:
        raise InstrumentationUnavailable(
            "OpenTelemetry SDK is required. Install with "
            '`pip install "openanchor[otel]"` or `pip install opentelemetry-sdk`.'
        ) from exc

    processor = OpenAnchorSpanProcessor(collector)
    if tracer_provider is None:
        tracer_provider = TracerProvider(resource=Resource.create({"service.name": "openanchor"}))
    # Most SDK TracerProvider implementations expose add_span_processor.
    tracer_provider.add_span_processor(processor)

    names = list(instrumentors or _instrumentor_classes().keys())
    enabled: list[str] = []
    missing: list[str] = []
    for name in names:
        path = _instrumentor_classes().get(name)
        if not path:
            missing.append(name)
            continue
        module_name, class_name = path.rsplit(".", 1)
        try:
            module = __import__(module_name, fromlist=[class_name])
            instrumentor_cls = getattr(module, class_name)
        except (ImportError, AttributeError):
            missing.append(name)
            continue
        try:
            instrumentor_cls().instrument(tracer_provider=tracer_provider)
            enabled.append(name)
        except TypeError:
            # Some instrumentors only support global instrumentation.
            instrumentor_cls().instrument()
            enabled.append(name)
        except Exception as exc:  # pragma: no cover - instrumentor-specific
            logger.warning("Failed to enable %s instrumentor: %s", name, exc)
            missing.append(name)

    if not enabled:
        raise InstrumentationUnavailable(
            "No OpenLLMetry/OpenInference instrumentor is installed. "
            'Install one, e.g. `pip install "openanchor[auto-instrument]"`. '
            f"Missing: {', '.join(missing)}"
        )

    logger.info("OpenAnchor auto-instrumentation enabled for: %s", ", ".join(enabled))
    return tracer_provider


__all__ = [
    "InstrumentationUnavailable",
    "OpenAnchorSpanProcessor",
    "enable_auto_instrumentation",
]
