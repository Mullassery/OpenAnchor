"""Token attribution analysis (6D breakdown)."""

from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import logging

from .models import Attribution, OperationType, RequestPhase, TokenEvent
from .storage import EventStore

logger = logging.getLogger(__name__)


class AttributionModel:
    """Performs 6-dimensional token attribution analysis."""

    def __init__(self, store: EventStore):
        """
        Initialize attribution model.

        Args:
            store: Event store to analyze
        """
        self.store = store

    def analyze_call(self, call_id: str) -> Attribution:
        """
        Analyze token attribution for a single call.

        Breaks down tokens across 6 dimensions:
        1. WHEN: Request vs response phase
        2. WHERE: Operation type (GitHub, PDF, reasoning, etc.)
        3. HOW: Sub-operation (GitHub read/write/search)
        4. WHICH: Prompt template used
        5. SESSION/PHASE: Temporal grouping
        6. WHY: Patterns and recommendations (v0.2+)

        Args:
            call_id: Call to analyze

        Returns:
            Attribution breakdown
        """
        events = self.store.get_events_by_call(call_id)

        if not events:
            return Attribution(call_id=call_id)

        # Check cache first
        cached = self.store.get_attribution(call_id)
        if cached:
            return cached

        # Breakdown by phase
        by_phase: Dict[RequestPhase, int] = defaultdict(int)
        # Breakdown by operation type
        by_operation: Dict[OperationType, int] = defaultdict(int)
        # Breakdown by prompt template
        by_prompt_template: Dict[str, int] = defaultdict(int)

        total_tokens = 0

        for event in events:
            tokens = event.tokens.total_tokens
            total_tokens += tokens

            # WHEN: Request vs response
            by_phase[event.phase] += tokens

            # WHERE & HOW: Operation type
            by_operation[event.operation_type] += tokens

            # WHICH: Prompt template
            if event.prompt_template:
                by_prompt_template[event.prompt_template] += tokens
            else:
                by_prompt_template["untagged"] += tokens

        attribution = Attribution(
            call_id=call_id,
            by_phase=dict(by_phase),
            by_operation=dict(by_operation),
            by_prompt_template=dict(by_prompt_template),
            total_tokens=total_tokens,
        )

        # Cache the result
        self.store.add_attribution(attribution)

        return attribution

    def get_operation_breakdown(self, session_id: str) -> Dict[str, int]:
        """
        Get token breakdown by operation type for a session.

        Returns:
            Dict mapping operation names to token counts
        """
        events = self.store.get_events_by_session(session_id)

        breakdown: Dict[str, int] = defaultdict(int)
        for event in events:
            op_name = event.operation_type.value
            breakdown[op_name] += event.tokens.total_tokens

        return dict(breakdown)

    def get_phase_breakdown(self, session_id: str) -> Dict[str, int]:
        """
        Get token breakdown by request/response phase.

        Returns:
            Dict with 'request' and 'response' token counts
        """
        events = self.store.get_events_by_session(session_id)

        breakdown: Dict[str, int] = {"request": 0, "response": 0}
        for event in events:
            phase_name = event.phase.value
            breakdown[phase_name] += event.tokens.total_tokens

        return breakdown

    def get_prompt_efficiency(self, session_id: str) -> Dict[str, Dict[str, float]]:
        """
        Rank prompts by efficiency (tokens per quality point).

        Returns:
            Dict mapping prompt templates to efficiency metrics
        """
        events = self.store.get_events_by_session(session_id)

        prompt_stats: Dict[str, Dict[str, List[float]]] = defaultdict(
            lambda: {"tokens": [], "quality": []}
        )

        for event in events:
            if event.prompt_template:
                prompt_stats[event.prompt_template]["tokens"].append(
                    event.tokens.total_tokens
                )
                if event.quality_score is not None:
                    prompt_stats[event.prompt_template]["quality"].append(
                        event.quality_score
                    )

        # Calculate efficiency
        efficiency: Dict[str, Dict[str, float]] = {}
        for prompt, stats in prompt_stats.items():
            if not stats["tokens"]:
                continue

            avg_tokens = sum(stats["tokens"]) / len(stats["tokens"])
            avg_quality = (
                sum(stats["quality"]) / len(stats["quality"])
                if stats["quality"]
                else 0.0
            )

            efficiency[prompt] = {
                "avg_tokens": avg_tokens,
                "avg_quality": avg_quality,
                "efficiency_score": (
                    avg_quality / avg_tokens if avg_tokens > 0 else 0.0
                ),
                "usage_count": len(stats["tokens"]),
            }

        return efficiency

    def get_model_distribution(self, session_id: str) -> Dict[str, int]:
        """
        Get token distribution across models.

        Returns:
            Dict mapping model names to token counts
        """
        events = self.store.get_events_by_session(session_id)

        distribution: Dict[str, int] = defaultdict(int)
        for event in events:
            distribution[event.model] += event.tokens.total_tokens

        return dict(distribution)

    def rank_prompts_by_efficiency(
        self, session_id: str, top_n: int = 10
    ) -> List[tuple]:
        """
        Rank prompts by efficiency (quality per token).

        Args:
            session_id: Session to analyze
            top_n: Number of top prompts to return

        Returns:
            List of (prompt_name, efficiency_score) tuples, sorted by efficiency
        """
        efficiency = self.get_prompt_efficiency(session_id)

        if not efficiency:
            return []

        # Sort by efficiency score (descending)
        sorted_prompts = sorted(
            efficiency.items(), key=lambda x: x[1]["efficiency_score"], reverse=True
        )

        return [(prompt, data["efficiency_score"]) for prompt, data in sorted_prompts][
            :top_n
        ]

    def get_attribution_summary(self, call_id: str) -> Dict[str, str]:
        """
        Get a human-readable summary of token attribution.

        Args:
            call_id: Call to summarize

        Returns:
            Dict with readable breakdown
        """
        attr = self.analyze_call(call_id)

        summary: Dict[str, str] = {
            "total_tokens": str(attr.total_tokens),
        }

        # Phase breakdown
        if attr.by_phase:
            phase_strs = [
                f"{phase.value}: {tokens} ({100 * tokens / attr.total_tokens:.1f}%)"
                for phase, tokens in sorted(
                    attr.by_phase.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
            ]
            summary["by_phase"] = " | ".join(phase_strs)

        # Operation breakdown
        if attr.by_operation:
            op_strs = [
                f"{op.value}: {tokens} ({100 * tokens / attr.total_tokens:.1f}%)"
                for op, tokens in sorted(
                    attr.by_operation.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
            ]
            summary["by_operation"] = " | ".join(op_strs)

        # Prompt breakdown
        if attr.by_prompt_template:
            prompt_strs = [
                f"{prompt}: {tokens} ({100 * tokens / attr.total_tokens:.1f}%)"
                for prompt, tokens in sorted(
                    attr.by_prompt_template.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
            ]
            summary["by_prompt"] = " | ".join(prompt_strs)

        return summary
