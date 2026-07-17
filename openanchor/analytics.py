"""Analytics and query APIs for token insights."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import logging

from .collector import TokenCollector
from .attribution import AttributionModel
from .models import TokenEvent, SessionStats
from .storage import EventStore

logger = logging.getLogger(__name__)


class Analytics:
    """High-level analytics and query API."""

    def __init__(self, collector: TokenCollector, attribution: AttributionModel):
        """
        Initialize analytics engine.

        Args:
            collector: Token collector
            attribution: Attribution model
        """
        self.collector = collector
        self.attribution = attribution
        self.store = collector.store

    # Session-level queries

    def get_session_stats(self, session_id: str) -> SessionStats:
        """Get overall statistics for a session."""
        return self.collector.compute_session_stats(session_id)

    def get_all_sessions(self) -> List[str]:
        """Get all session IDs."""
        events = self.store.all_events()
        sessions = set()
        for event in events:
            if event.session_id:
                sessions.add(event.session_id)
        return sorted(sessions)

    # Call-level queries

    def get_call_stats(self, call_id: str) -> Dict[str, Any]:
        """Get statistics for a single call."""
        return self.collector.compute_call_stats(call_id)

    # Token breakdown queries

    def get_tokens_by_operation(self, session_id: str) -> Dict[str, int]:
        """Get token consumption by operation type."""
        return self.attribution.get_operation_breakdown(session_id)

    def get_tokens_by_phase(self, session_id: str) -> Dict[str, int]:
        """Get token consumption by request/response phase."""
        return self.attribution.get_phase_breakdown(session_id)

    def get_tokens_by_model(self, session_id: str) -> Dict[str, int]:
        """Get token consumption by model."""
        return self.attribution.get_model_distribution(session_id)

    def get_tokens_by_prompt_template(self, session_id: str) -> Dict[str, int]:
        """Get token consumption by prompt template."""
        events = self.store.get_events_by_session(session_id)
        breakdown: Dict[str, int] = defaultdict(int)

        for event in events:
            template = event.prompt_template or "untagged"
            breakdown[template] += event.tokens.total_tokens

        return dict(breakdown)

    # Efficiency queries

    def rank_prompts_by_efficiency(
        self, session_id: str, top_n: int = 10
    ) -> List[tuple]:
        """Rank prompt templates by efficiency (quality per token)."""
        return self.attribution.rank_prompts_by_efficiency(session_id, top_n)

    def get_prompt_stats(self, session_id: str) -> Dict[str, Dict[str, float]]:
        """Get efficiency stats for all prompts in a session."""
        return self.attribution.get_prompt_efficiency(session_id)

    # Time-based queries

    def get_tokens_by_hour(self, session_id: str) -> Dict[str, int]:
        """Get token consumption by hour."""
        events = self.store.get_events_by_session(session_id)

        breakdown: Dict[str, int] = defaultdict(int)
        for event in events:
            hour_key = event.timestamp.strftime("%Y-%m-%d %H:00")
            breakdown[hour_key] += event.tokens.total_tokens

        return dict(sorted(breakdown.items()))

    def get_tokens_by_day(self, session_id: str) -> Dict[str, int]:
        """Get token consumption by day."""
        events = self.store.get_events_by_session(session_id)

        breakdown: Dict[str, int] = defaultdict(int)
        for event in events:
            day_key = event.timestamp.strftime("%Y-%m-%d")
            breakdown[day_key] += event.tokens.total_tokens

        return dict(sorted(breakdown.items()))

    # Performance queries

    def get_latency_stats(self, session_id: str) -> Dict[str, float]:
        """Get latency statistics for a session."""
        events = self.store.get_events_by_session(session_id)

        latencies = [e.latency_ms for e in events if e.latency_ms]
        if not latencies:
            return {"count": 0}

        latencies.sort()
        total = sum(latencies)

        return {
            "count": len(latencies),
            "avg_ms": total / len(latencies),
            "median_ms": latencies[len(latencies) // 2],
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "p95_ms": latencies[int(len(latencies) * 0.95)],
            "p99_ms": latencies[int(len(latencies) * 0.99)],
        }

    def get_quality_stats(self, session_id: str) -> Dict[str, float]:
        """Get quality score statistics for a session."""
        events = self.store.get_events_by_session(session_id)

        scores = [e.quality_score for e in events if e.quality_score is not None]
        if not scores:
            return {"count": 0}

        scores.sort()
        total = sum(scores)

        return {
            "count": len(scores),
            "avg": total / len(scores),
            "median": scores[len(scores) // 2],
            "min": min(scores),
            "max": max(scores),
        }

    # Comparison queries

    def compare_sessions(self, session_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Compare statistics across sessions."""
        comparison: Dict[str, Dict[str, Any]] = {}

        for session_id in session_ids:
            stats = self.get_session_stats(session_id)
            comparison[session_id] = {
                "total_tokens": stats.total_tokens,
                "total_calls": stats.total_calls,
                "avg_latency_ms": stats.avg_latency_ms,
                "avg_quality": stats.avg_quality_score,
                "tokens_per_call": (
                    stats.total_tokens / stats.total_calls if stats.total_calls > 0 else 0
                ),
            }

        return comparison

    # Diagnostic queries

    def get_problematic_calls(
        self, session_id: str, min_tokens: int = 5000, max_quality: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Find calls that consumed many tokens but had low quality.

        Args:
            session_id: Session to analyze
            min_tokens: Minimum tokens to consider problematic
            max_quality: Maximum quality score to flag

        Returns:
            List of problematic calls
        """
        events = self.store.get_events_by_session(session_id)

        problematic = []
        call_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"tokens": 0})

        for event in events:
            call_id = event.call_id
            call_stats[call_id]["tokens"] += event.tokens.total_tokens

            if event.quality_score is not None:
                if "quality_scores" not in call_stats[call_id]:
                    call_stats[call_id]["quality_scores"] = []
                call_stats[call_id]["quality_scores"].append(event.quality_score)

        for call_id, stats in call_stats.items():
            if stats["tokens"] < min_tokens:
                continue

            avg_quality = (
                sum(stats["quality_scores"]) / len(stats["quality_scores"])
                if "quality_scores" in stats and stats["quality_scores"]
                else 1.0
            )

            if avg_quality <= max_quality:
                problematic.append(
                    {
                        "call_id": call_id,
                        "total_tokens": stats["tokens"],
                        "avg_quality": avg_quality,
                        "quality_ratio": (
                            avg_quality / stats["tokens"] if stats["tokens"] > 0 else 0
                        ),
                    }
                )

        return sorted(
            problematic,
            key=lambda x: x["quality_ratio"],
        )

    def get_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a comprehensive summary of session activity."""
        stats = self.get_session_stats(session_id)
        op_breakdown = self.get_tokens_by_operation(session_id)
        phase_breakdown = self.get_tokens_by_phase(session_id)
        latency_stats = self.get_latency_stats(session_id)
        quality_stats = self.get_quality_stats(session_id)

        return {
            "session_id": session_id,
            "total_tokens": stats.total_tokens,
            "total_calls": stats.total_calls,
            "duration_seconds": stats.duration_seconds,
            "by_operation": op_breakdown,
            "by_phase": phase_breakdown,
            "latency_stats": latency_stats,
            "quality_stats": quality_stats,
            "tokens_per_call": (
                stats.total_tokens / stats.total_calls if stats.total_calls > 0 else 0
            ),
        }
