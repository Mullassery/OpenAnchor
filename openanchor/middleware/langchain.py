"""LangChain integration for OpenAnchor."""

import logging
from typing import Any, Dict, List, Optional
import time
import uuid

from ..collector import TokenCollector
from ..attribution import AttributionModel
from ..analytics import Analytics
from ..storage import EventStore
from ..models import OperationType, RequestPhase

logger = logging.getLogger(__name__)


class OpenAnchorMiddleware:
    """LangChain middleware for capturing and analyzing token consumption."""

    def __init__(
        self,
        project_name: str = "langchain_app",
        store: Optional[EventStore] = None,
        session_id: Optional[str] = None,
    ):
        """
        Initialize OpenAnchor middleware.

        Args:
            project_name: Name of the project
            store: Event store (defaults to in-memory)
            session_id: Session ID (auto-generated if not provided)
        """
        self.project_name = project_name
        self.store = store or EventStore()
        self.session_id = session_id or str(uuid.uuid4())

        self.collector = TokenCollector(self.store)
        self.collector.set_session(self.session_id)

        self.attribution = AttributionModel(self.store)
        self.analytics = Analytics(self.collector, self.attribution)

        logger.info(f"OpenAnchor initialized for {project_name} (session: {self.session_id})")

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Make middleware callable for use as LangChain runnable."""
        if len(args) == 1 and hasattr(args[0], "invoke"):
            # Assume first arg is a runnable
            runnable = args[0]
            return self._wrap_runnable(runnable)
        raise ValueError("OpenAnchorMiddleware requires a LangChain runnable")

    def _wrap_runnable(self, runnable: Any) -> Any:
        """Wrap a LangChain runnable to capture token events."""

        class WrappedRunnable:
            def __init__(inner_self, middleware):
                inner_self.middleware = middleware
                inner_self.runnable = runnable

            def invoke(inner_self, input_data: Any, config: Optional[Any] = None) -> Any:
                """Invoke wrapped runnable and capture metrics."""
                call_id = str(uuid.uuid4())
                start_time = time.time()

                try:
                    result = inner_self.runnable.invoke(input_data, config)

                    latency_ms = (time.time() - start_time) * 1000

                    # Try to extract token counts from result metadata
                    input_tokens = 0
                    output_tokens = 0

                    if hasattr(result, "response_metadata"):
                        metadata = result.response_metadata
                        if isinstance(metadata, dict):
                            if "usage" in metadata:
                                usage = metadata["usage"]
                                input_tokens = usage.get("input_tokens", 0)
                                output_tokens = usage.get("output_tokens", 0)

                    # Capture event
                    inner_self.middleware.collector.capture_event(
                        call_id=call_id,
                        model=self._get_model_name(input_data),
                        provider="langchain",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        latency_ms=latency_ms,
                        operation_type=OperationType.MODEL_REASONING,
                        request_data={"input": str(input_data)[:500]},
                        response_data={"output": str(result)[:500]},
                    )

                    return result

                except Exception as e:
                    logger.error(f"Error in OpenAnchor middleware: {e}")
                    raise

            def batch(inner_self, inputs: List[Any], config: Optional[Any] = None) -> List[Any]:
                """Batch invoke wrapped runnable."""
                return [inner_self.invoke(input_data, config) for input_data in inputs]

            def stream(inner_self, input_data: Any, config: Optional[Any] = None) -> Any:
                """Stream from wrapped runnable."""
                if hasattr(inner_self.runnable, "stream"):
                    return inner_self.runnable.stream(input_data, config)
                else:
                    yield inner_self.invoke(input_data, config)

            @staticmethod
            def _get_model_name(input_data: Any) -> str:
                """Extract model name from input."""
                if isinstance(input_data, dict):
                    return input_data.get("model", "unknown")
                return "unknown"

        return WrappedRunnable(self)

    def capture_llm_call(
        self,
        *,
        call_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: Optional[float] = None,
        quality_score: Optional[float] = None,
        prompt_template: Optional[str] = None,
        operation_type: OperationType = OperationType.MODEL_REASONING,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Manually capture an LLM call.

        Args:
            call_id: Unique call identifier
            model: Model name
            input_tokens: Input token count
            output_tokens: Output token count
            latency_ms: Call latency in milliseconds
            quality_score: Quality score (0.0-1.0)
            prompt_template: Prompt template used
            operation_type: Type of operation
            request_data: Request metadata
            response_data: Response metadata
        """
        self.collector.capture_event(
            call_id=call_id,
            model=model,
            provider="langchain",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            quality_score=quality_score,
            prompt_template=prompt_template,
            operation_type=operation_type,
            request_data=request_data,
            response_data=response_data,
        )

    # Query APIs

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for current session."""
        return self.analytics.get_session_stats(self.session_id).to_dict()

    def get_tokens_by_operation(self) -> Dict[str, int]:
        """Get token breakdown by operation type."""
        return self.analytics.get_tokens_by_operation(self.session_id)

    def get_tokens_by_phase(self) -> Dict[str, int]:
        """Get token breakdown by phase."""
        return self.analytics.get_tokens_by_phase(self.session_id)

    def rank_prompts_by_efficiency(self, top_n: int = 10) -> List[tuple]:
        """Rank prompts by efficiency."""
        return self.analytics.rank_prompts_by_efficiency(self.session_id, top_n)

    def get_problematic_calls(self) -> List[Dict[str, Any]]:
        """Find calls with high token consumption and low quality."""
        return self.analytics.get_problematic_calls(self.session_id)

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary."""
        return self.analytics.get_summary(self.session_id)

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get optimization recommendations (v0.2+).

        For v0.1, returns basic recommendations based on data.
        """
        summary = self.get_summary()
        recommendations = []

        # Check for high token consumption
        if summary["total_tokens"] > 10000:
            recommendations.append(
                {
                    "action": "Review prompt efficiency",
                    "reason": f"High token consumption ({summary['total_tokens']} tokens)",
                    "confidence": 0.8,
                }
            )

        # Check for low quality calls
        problematic = self.get_problematic_calls()
        if problematic:
            recommendations.append(
                {
                    "action": "Review low-quality calls",
                    "reason": f"Found {len(problematic)} calls with low quality scores",
                    "confidence": 0.85,
                }
            )

        # Check for operation imbalance
        by_op = self.get_tokens_by_operation()
        if by_op:
            top_op = max(by_op.items(), key=lambda x: x[1])
            if top_op[1] > summary["total_tokens"] * 0.6:
                recommendations.append(
                    {
                        "action": f"Optimize {top_op[0]} operations",
                        "reason": f"{top_op[0]} consumes {100 * top_op[1] / summary['total_tokens']:.1f}% of tokens",
                        "confidence": 0.75,
                    }
                )

        return recommendations
