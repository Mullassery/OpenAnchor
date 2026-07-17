"""Token collection and event capture."""

from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

from .models import (
    TokenEvent,
    TokenConsumption,
    Attribution,
    SessionStats,
    OperationType,
    RequestPhase,
)
from .storage import EventStore, SqliteEventStore

logger = logging.getLogger(__name__)


class TokenCollector:
    """Collects and manages token consumption events."""

    def __init__(self, store: Optional[EventStore] = None):
        """
        Initialize collector.

        Args:
            store: Event store (defaults to in-memory)
        """
        self.store = store or EventStore()
        self._current_session: Optional[str] = None

    def set_session(self, session_id: str) -> None:
        """Set the current session ID."""
        self._current_session = session_id

    def capture_event(
        self,
        *,
        call_id: str,
        model: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        phase: RequestPhase = RequestPhase.REQUEST,
        operation_type: OperationType = OperationType.OTHER,
        prompt_template: Optional[str] = None,
        latency_ms: Optional[float] = None,
        ttft_ms: Optional[float] = None,
        quality_score: Optional[float] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> TokenEvent:
        """
        Capture a token consumption event.

        Args:
            call_id: Unique identifier for this LLM call
            model: Model name (e.g., "gpt-4", "claude-3-opus")
            provider: Provider (e.g., "openai", "anthropic")
            input_tokens: Input tokens consumed
            output_tokens: Output tokens consumed
            phase: Request or response phase
            operation_type: Type of operation
            prompt_template: Prompt template used
            latency_ms: Call latency in milliseconds
            ttft_ms: Time-to-first-token in milliseconds
            quality_score: Quality score (0.0-1.0)
            request_data: Request metadata
            response_data: Response metadata
            tags: Custom tags

        Returns:
            The captured TokenEvent
        """
        event = TokenEvent(
            call_id=call_id,
            timestamp=datetime.utcnow(),
            phase=phase,
            operation_type=operation_type,
            prompt_template=prompt_template,
            session_id=self._current_session,
            tokens=TokenConsumption(
                input_tokens=input_tokens, output_tokens=output_tokens
            ),
            model=model,
            provider=provider,
            latency_ms=latency_ms,
            ttft_ms=ttft_ms,
            quality_score=quality_score,
            request_data=request_data or {},
            response_data=response_data or {},
            tags=tags or {},
        )

        self.store.add_event(event)
        logger.debug(
            f"Captured event {event.event_id}: {event.tokens.total_tokens} tokens "
            f"({event.operation_type.value})"
        )
        return event

    def get_events_for_call(self, call_id: str) -> List[TokenEvent]:
        """Get all events for a call."""
        return self.store.get_events_by_call(call_id)

    def get_events_for_session(self, session_id: str) -> List[TokenEvent]:
        """Get all events in a session."""
        return self.store.get_events_by_session(session_id)

    def get_all_events(self) -> List[TokenEvent]:
        """Get all captured events."""
        return self.store.all_events()

    def compute_call_stats(self, call_id: str) -> Dict[str, Any]:
        """Compute statistics for a single call."""
        events = self.get_events_for_call(call_id)
        if not events:
            return {}

        total_input = sum(e.tokens.input_tokens for e in events)
        total_output = sum(e.tokens.output_tokens for e in events)
        latencies = [e.latency_ms for e in events if e.latency_ms]
        qualities = [e.quality_score for e in events if e.quality_score]

        return {
            "call_id": call_id,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "event_count": len(events),
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else None,
            "avg_quality_score": sum(qualities) / len(qualities) if qualities else None,
        }

    def compute_session_stats(self, session_id: str) -> SessionStats:
        """Compute statistics for a session."""
        events = self.get_events_for_session(session_id)

        if not events:
            return SessionStats(session_id=session_id)

        total_input = sum(e.tokens.input_tokens for e in events)
        total_output = sum(e.tokens.output_tokens for e in events)
        latencies = [e.latency_ms for e in events if e.latency_ms]
        qualities = [e.quality_score for e in events if e.quality_score]

        # Group by operation type and model
        by_operation: Dict[str, int] = {}
        by_model: Dict[str, int] = {}
        for event in events:
            op_key = event.operation_type.value
            by_operation[op_key] = by_operation.get(op_key, 0) + event.tokens.total_tokens

            model_key = event.model
            by_model[model_key] = by_model.get(model_key, 0) + event.tokens.total_tokens

        return SessionStats(
            session_id=session_id,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_calls=len(set(e.call_id for e in events)),
            avg_latency_ms=sum(latencies) / len(latencies) if latencies else 0.0,
            avg_quality_score=sum(qualities) / len(qualities) if qualities else 0.0,
            start_time=min(e.timestamp for e in events),
            end_time=max(e.timestamp for e in events),
            by_operation=by_operation,
            by_model=by_model,
        )
