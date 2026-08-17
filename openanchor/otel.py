"""OpenTelemetry integration for OpenAnchor.

Wraps token-capture events (see ``collector.py``) in real OTEL spans with
token counts, cost, model, and provider as span attributes, and exposes a
configurable exporter:

- ``console`` (default when tracing is enabled): safe, no network calls,
  prints spans to stdout. Good default for local dev and for not
  surprising anyone with an outbound network call they didn't ask for.
- ``otlp``: sends spans to an OTLP/HTTP collector (e.g. an OTEL Collector,
  Honeycomb, Jaeger, etc). Opt-in via ``exporter="otlp"`` or the
  ``OPENANCHOR_OTEL_EXPORTER=otlp`` environment variable.

Tracing itself is **opt-in** (disabled by default) via
``OPENANCHOR_OTEL_ENABLED=true`` or an explicit ``configure_tracing()``
call, because the collector's ``capture_event`` is a hot path and we don't
want to add tracing overhead or third-party network calls for users who
never asked for observability.

If the ``opentelemetry-api``/``opentelemetry-sdk`` packages aren't
installed, everything in this module degrades to safe no-ops.
"""

from __future__ import annotations

import logging
import os
import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

logger = logging.getLogger(__name__)

try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SimpleSpanProcessor,
        SpanExporter,
    )

    OTEL_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only without the extra installed
    OTEL_AVAILABLE = False

_lock = threading.Lock()
_tracer_provider: Optional[Any] = None
_configured_exporter_name: Optional[str] = None
_env_autoconfig_attempted = False


def is_otel_available() -> bool:
    """Whether the opentelemetry-api/sdk packages are importable."""
    return OTEL_AVAILABLE


def is_tracing_configured() -> bool:
    """Whether a tracer provider has been configured (enabled)."""
    return _tracer_provider is not None


def configured_exporter() -> Optional[str]:
    """Name of the currently configured exporter, or None if disabled."""
    return _configured_exporter_name


def configure_tracing(
    exporter: str = "console",
    service_name: str = "openanchor",
    otlp_endpoint: Optional[str] = None,
    span_processor: str = "simple",
    custom_exporter: Optional["SpanExporter"] = None,
) -> Optional["TracerProvider"]:
    """Configure the global OpenAnchor tracer provider.

    Args:
        exporter: "console" (default, safe, no network calls), "otlp"
            (sends spans to an OTLP/HTTP collector), or "none"/"disabled"
            to turn tracing off again.
        service_name: OTEL ``service.name`` resource attribute.
        otlp_endpoint: OTLP/HTTP traces endpoint, used only when
            ``exporter="otlp"``. Defaults to the ``OTEL_EXPORTER_OTLP_ENDPOINT``
            environment variable, or ``http://localhost:4318/v1/traces``.
        span_processor: "simple" (synchronous — spans are exported as soon
            as they end; good for tests/CLI/short-lived scripts) or
            "batch" (async batching — recommended for long-running
            production services).
        custom_exporter: Pass a pre-built ``SpanExporter`` directly
            (e.g. an in-memory exporter for tests). Overrides ``exporter``.

    Returns:
        The configured ``TracerProvider``, or ``None`` if OTEL isn't
        installed or tracing was disabled.
    """
    global _tracer_provider, _configured_exporter_name

    if not OTEL_AVAILABLE:
        logger.warning(
            "opentelemetry-api/opentelemetry-sdk are not installed; "
            "OpenAnchor tracing will be a no-op. Install with "
            "`pip install openanchor[otel]` or "
            "`pip install opentelemetry-api opentelemetry-sdk`."
        )
        return None

    with _lock:
        if exporter in ("none", "disabled") and custom_exporter is None:
            _tracer_provider = None
            _configured_exporter_name = "disabled"
            return None

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)

        if custom_exporter is not None:
            span_exporter: "SpanExporter" = custom_exporter
            exporter_name = "custom"
        elif exporter == "console":
            span_exporter = ConsoleSpanExporter()
            exporter_name = "console"
        elif exporter == "otlp":
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            endpoint = otlp_endpoint or os.environ.get(
                "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces"
            )
            span_exporter = OTLPSpanExporter(endpoint=endpoint)
            exporter_name = "otlp"
        else:
            raise ValueError(
                f"Unknown OTEL exporter {exporter!r}; expected 'console', 'otlp', "
                "'none', or pass custom_exporter=..."
            )

        processor_cls = (
            BatchSpanProcessor if span_processor == "batch" else SimpleSpanProcessor
        )
        provider.add_span_processor(processor_cls(span_exporter))

        trace.set_tracer_provider(provider)
        _tracer_provider = provider
        _configured_exporter_name = exporter_name

        logger.info(
            "OpenAnchor OTEL tracing configured (exporter=%s, service_name=%s)",
            exporter_name,
            service_name,
        )
        return provider


def disable_tracing() -> None:
    """Turn tracing back off (mainly for tests)."""
    global _tracer_provider, _configured_exporter_name
    with _lock:
        _tracer_provider = None
        _configured_exporter_name = "disabled"


def _maybe_autoconfigure_from_env() -> None:
    """Lazily enable tracing from environment variables on first use.

    This lets users turn on tracing with plain env vars (no code changes)
    while keeping the *default* fully off, per the audit's safety
    requirement that the collector hot path never silently starts making
    network calls.
    """
    global _env_autoconfig_attempted

    with _lock:
        if _env_autoconfig_attempted or _tracer_provider is not None:
            return
        _env_autoconfig_attempted = True

    enabled = os.environ.get("OPENANCHOR_OTEL_ENABLED", "false").strip().lower()
    if enabled not in ("1", "true", "yes", "on"):
        return

    exporter = os.environ.get("OPENANCHOR_OTEL_EXPORTER", "console").strip().lower()
    service_name = os.environ.get("OPENANCHOR_OTEL_SERVICE_NAME", "openanchor")
    span_processor = os.environ.get("OPENANCHOR_OTEL_SPAN_PROCESSOR", "batch")
    configure_tracing(
        exporter=exporter, service_name=service_name, span_processor=span_processor
    )


def get_tracer():
    """Return the OpenAnchor tracer, or None if tracing isn't available."""
    if not OTEL_AVAILABLE:
        return None
    _maybe_autoconfigure_from_env()
    if _tracer_provider is None:
        return None
    return trace.get_tracer("openanchor", tracer_provider=_tracer_provider)


@contextmanager
def start_span(name: str, attributes: Optional[Dict[str, Any]] = None) -> Iterator[Any]:
    """Context manager that starts a real OTEL span, or safely no-ops.

    Yields ``None`` (and does nothing else) when OTEL isn't installed or
    tracing hasn't been enabled, so call sites (e.g. the collector's hot
    path) never pay a real cost or risk an exception because of
    telemetry.
    """
    tracer = get_tracer()
    if tracer is None:
        yield None
        return

    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                if value is None:
                    continue
                try:
                    span.set_attribute(key, value)
                except Exception:  # pragma: no cover - defensive, never break capture
                    logger.debug("Failed to set span attribute %s", key, exc_info=True)
        yield span
