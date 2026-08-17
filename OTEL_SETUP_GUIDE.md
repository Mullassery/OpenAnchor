# OpenTelemetry Setup Guide

OpenAnchor wraps every captured token event (`TokenCollector.capture_event`,
see `openanchor/collector.py`) in a real OTEL span via `openanchor/otel.py`,
with token counts, model, provider, operation type, and (when available)
cost as span attributes.

Tracing is **off by default** — the collector's `capture_event` is a hot
path, and OpenAnchor won't add tracing overhead or make outbound network
calls unless you ask it to.

## Enabling tracing

### Option A: in code

```python
from openanchor import configure_tracing

# Safe default: prints spans to stdout, no network calls.
configure_tracing(exporter="console")

# Or send spans to an OTLP collector (Jaeger, an OTEL Collector,
# Honeycomb, etc):
configure_tracing(
    exporter="otlp",
    otlp_endpoint="http://localhost:4318/v1/traces",
    span_processor="batch",  # async batching, recommended for production
)
```

Call this once, early in your application, before any `TokenCollector`
usage. Every subsequent `capture_event` call will be wrapped in a span.

### Option B: environment variables (no code changes)

```bash
export OPENANCHOR_OTEL_ENABLED=true
export OPENANCHOR_OTEL_EXPORTER=console        # or "otlp"
export OPENANCHOR_OTEL_SERVICE_NAME=my-app
export OPENANCHOR_OTEL_SPAN_PROCESSOR=batch    # or "simple"
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces  # if exporter=otlp
```

Tracing configures itself lazily from these on first use.

## Installing the OTLP exporter

The `opentelemetry-api`/`opentelemetry-sdk` packages are core dependencies.
The OTLP/HTTP exporter (only needed for `exporter="otlp"`) is an optional
extra:

```bash
pip install "openanchor[otel]"
```

## Span shape

Each `capture_event` call produces a span named `openanchor.capture_event`
with attributes:

| Attribute | Meaning |
|---|---|
| `openanchor.call_id` | Call this event belongs to |
| `openanchor.model` / `openanchor.provider` | LLM model/provider |
| `openanchor.operation_type` / `openanchor.phase` | 6D attribution dimensions |
| `llm.token_count.input` / `.output` / `.total` | Token counts |
| `openanchor.latency_ms` / `openanchor.quality_score` | Performance metrics, if provided |
| `openanchor.cost_usd` | Only set if the caller passes `tags={"cost_usd": ...}` — OpenAnchor doesn't compute pricing itself |

## Testing

`tests/test_otel.py` verifies real spans are created and exported using
OTEL's in-memory span exporter (`opentelemetry.sdk.trace.export.in_memory_span_exporter.InMemorySpanExporter`)
— no live collector required.
