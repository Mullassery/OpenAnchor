"""Core data models for token events and attribution."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid


class OperationType(str, Enum):
    """Types of operations that consume tokens."""
    SYSTEM_PROMPT = "system_prompt"
    USER_INPUT = "user_input"
    RETRIEVAL = "retrieval"
    MODEL_REASONING = "reasoning"
    GITHUB_READ = "github_read"
    GITHUB_WRITE = "github_write"
    GITHUB_SEARCH = "github_search"
    PDF_EXTRACTION = "pdf_extraction"
    PDF_CHUNKING = "pdf_chunking"
    PDF_RETRIEVAL = "pdf_retrieval"
    OTHER = "other"


class RequestPhase(str, Enum):
    """Token consumption phase."""
    REQUEST = "request"
    RESPONSE = "response"


@dataclass
class TokenConsumption:
    """Token counts for a single call."""
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        """Total tokens (input + output)."""
        return self.input_tokens + self.output_tokens


@dataclass
class TokenEvent:
    """Single token consumption event."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Dimensional attributes (6D)
    phase: RequestPhase = RequestPhase.REQUEST
    operation_type: OperationType = OperationType.OTHER
    prompt_template: Optional[str] = None
    session_id: Optional[str] = None

    # Token data
    tokens: TokenConsumption = field(default_factory=lambda: TokenConsumption(0, 0))

    # Call metadata
    model: str = "unknown"
    provider: str = "unknown"
    call_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Performance metrics
    latency_ms: Optional[float] = None
    ttft_ms: Optional[float] = None
    quality_score: Optional[float] = None

    # Request/response data
    request_data: Dict[str, Any] = field(default_factory=dict)
    response_data: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (JSON-serializable)."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "phase": self.phase.value,
            "operation_type": self.operation_type.value,
            "prompt_template": self.prompt_template,
            "session_id": self.session_id,
            "tokens": {
                "input_tokens": self.tokens.input_tokens,
                "output_tokens": self.tokens.output_tokens,
                "total_tokens": self.tokens.total_tokens,
            },
            "model": self.model,
            "provider": self.provider,
            "call_id": self.call_id,
            "latency_ms": self.latency_ms,
            "ttft_ms": self.ttft_ms,
            "quality_score": self.quality_score,
            "tags": self.tags,
        }


@dataclass
class Attribution:
    """Token attribution breakdown for a call."""
    call_id: str

    # Dimensional breakdown
    by_phase: Dict[RequestPhase, int] = field(default_factory=dict)
    by_operation: Dict[OperationType, int] = field(default_factory=dict)
    by_prompt_template: Dict[str, int] = field(default_factory=dict)

    # Total
    total_tokens: int = 0

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "call_id": self.call_id,
            "by_phase": {k.value: v for k, v in self.by_phase.items()},
            "by_operation": {k.value: v for k, v in self.by_operation.items()},
            "by_prompt_template": self.by_prompt_template,
            "total_tokens": self.total_tokens,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class SessionStats:
    """Statistics for a session."""
    session_id: str

    # Token totals
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    # Call counts
    total_calls: int = 0

    # Performance
    avg_latency_ms: float = 0.0
    avg_quality_score: float = 0.0

    # Time range
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Breakdown
    by_operation: Dict[str, int] = field(default_factory=dict)
    by_model: Dict[str, int] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        """Total tokens in session."""
        return self.total_input_tokens + self.total_output_tokens

    @property
    def duration_seconds(self) -> Optional[float]:
        """Duration of session in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "total_tokens": self.total_tokens,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_calls": self.total_calls,
            "avg_latency_ms": self.avg_latency_ms,
            "avg_quality_score": self.avg_quality_score,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "by_operation": self.by_operation,
            "by_model": self.by_model,
        }
