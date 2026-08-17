"""Tests for real OTEL span export (openanchor/otel.py + collector.py wiring).

Uses OTEL's in-memory span exporter so these tests verify actual spans are
created/exported without needing a live collector, per the standard OTEL
testing approach.
"""

import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from openanchor import otel as otel_module
from openanchor.collector import TokenCollector
from openanchor.models import OperationType, RequestPhase
from openanchor.storage import EventStore


@pytest.fixture(autouse=True)
def _reset_tracing():
    """Ensure each test starts with tracing disabled and cleans up after."""
    otel_module.disable_tracing()
    yield
    otel_module.disable_tracing()


@pytest.fixture
def memory_exporter():
    exporter = InMemorySpanExporter()
    otel_module.configure_tracing(custom_exporter=exporter, span_processor="simple")
    yield exporter
    exporter.clear()


class TestOtelAvailability:
    def test_otel_is_available_in_this_environment(self):
        # opentelemetry-api/sdk are core dependencies now.
        assert otel_module.is_otel_available() is True


class TestTracingDisabledByDefault:
    def test_no_tracer_when_not_configured(self):
        assert otel_module.is_tracing_configured() is False
        tracer = otel_module.get_tracer()
        assert tracer is None

    def test_start_span_is_a_safe_noop_when_disabled(self):
        with otel_module.start_span("some.span", attributes={"a": 1}) as span:
            assert span is None
        # No exception, no spans recorded anywhere.


class TestConfigureTracing:
    def test_configure_with_console_exporter(self):
        provider = otel_module.configure_tracing(exporter="console")
        assert provider is not None
        assert otel_module.is_tracing_configured() is True
        assert otel_module.configured_exporter() == "console"

    def test_disable_after_configure(self):
        otel_module.configure_tracing(exporter="console")
        assert otel_module.is_tracing_configured() is True
        otel_module.disable_tracing()
        assert otel_module.is_tracing_configured() is False

    def test_unknown_exporter_raises(self):
        with pytest.raises(ValueError):
            otel_module.configure_tracing(exporter="not-a-real-exporter")


class TestSpanCreation:
    def test_start_span_creates_real_span(self, memory_exporter):
        with otel_module.start_span("test.span", attributes={"foo": "bar"}) as span:
            assert span is not None

        spans = memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "test.span"
        assert spans[0].attributes["foo"] == "bar"

    def test_none_attributes_are_skipped(self, memory_exporter):
        with otel_module.start_span("test.span", attributes={"a": 1, "b": None}):
            pass

        spans = memory_exporter.get_finished_spans()
        assert "a" in spans[0].attributes
        assert "b" not in spans[0].attributes


class TestCollectorSpanIntegration:
    """Verify capture_event wraps real spans with token/model/provider attributes."""

    def test_capture_event_creates_span_with_token_attributes(self, memory_exporter):
        collector = TokenCollector(EventStore())
        collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
            operation_type=OperationType.RETRIEVAL,
            phase=RequestPhase.REQUEST,
        )

        spans = memory_exporter.get_finished_spans()
        assert len(spans) == 1
        span = spans[0]
        assert span.name == "openanchor.capture_event"
        assert span.attributes["openanchor.call_id"] == "call_1"
        assert span.attributes["openanchor.model"] == "gpt-4"
        assert span.attributes["openanchor.provider"] == "openai"
        assert span.attributes["openanchor.operation_type"] == "retrieval"
        assert span.attributes["openanchor.phase"] == "request"
        assert span.attributes["llm.token_count.input"] == 100
        assert span.attributes["llm.token_count.output"] == 50
        assert span.attributes["llm.token_count.total"] == 150

    def test_capture_event_includes_cost_when_provided_via_tags(self, memory_exporter):
        collector = TokenCollector(EventStore())
        collector.capture_event(
            call_id="call_1",
            model="gpt-4",
            provider="openai",
            input_tokens=10,
            output_tokens=5,
            tags={"cost_usd": 0.0032},
        )

        spans = memory_exporter.get_finished_spans()
        assert spans[0].attributes["openanchor.cost_usd"] == 0.0032

    def test_capture_event_omits_cost_when_not_provided(self, memory_exporter):
        collector = TokenCollector(EventStore())
        collector.capture_event(
            call_id="call_1", model="gpt-4", provider="openai",
            input_tokens=10, output_tokens=5,
        )

        spans = memory_exporter.get_finished_spans()
        assert "openanchor.cost_usd" not in spans[0].attributes

    def test_multiple_events_produce_multiple_spans(self, memory_exporter):
        collector = TokenCollector(EventStore())
        for i in range(3):
            collector.capture_event(
                call_id=f"call_{i}", model="gpt-4", provider="openai",
                input_tokens=10, output_tokens=5,
            )

        spans = memory_exporter.get_finished_spans()
        assert len(spans) == 3

    def test_capture_event_still_works_when_tracing_disabled(self):
        """The hot path must never break because of telemetry."""
        otel_module.disable_tracing()
        collector = TokenCollector(EventStore())
        event = collector.capture_event(
            call_id="call_1", model="gpt-4", provider="openai",
            input_tokens=10, output_tokens=5,
        )
        assert event.tokens.total_tokens == 15


class TestEnvAutoConfigure:
    def test_env_enabled_configures_console_exporter(self, monkeypatch):
        monkeypatch.setenv("OPENANCHOR_OTEL_ENABLED", "true")
        monkeypatch.setenv("OPENANCHOR_OTEL_EXPORTER", "console")
        otel_module._env_autoconfig_attempted = False

        tracer = otel_module.get_tracer()
        assert tracer is not None
        assert otel_module.configured_exporter() == "console"

    def test_env_disabled_by_default_leaves_tracer_none(self, monkeypatch):
        monkeypatch.delenv("OPENANCHOR_OTEL_ENABLED", raising=False)
        otel_module._env_autoconfig_attempted = False

        tracer = otel_module.get_tracer()
        assert tracer is None
