#!/usr/bin/env python
"""Basic usage example for OpenAnchor."""

from openanchor import TokenCollector, AttributionModel, Analytics
from openanchor.models import OperationType, RequestPhase


def main():
    """Demonstrate basic OpenAnchor usage."""

    # 1. Create collector and start a session
    collector = TokenCollector()
    session_id = "example_session_q3_2026"
    collector.set_session(session_id)

    print("🚀 OpenAnchor Example: Token Intelligence\n")
    print(f"Session: {session_id}\n")

    # 2. Capture events from different operations
    print("📊 Capturing token events...")

    # System prompt event
    collector.capture_event(
        call_id="call_1",
        model="gpt-4",
        provider="openai",
        input_tokens=500,
        output_tokens=0,
        phase=RequestPhase.REQUEST,
        operation_type=OperationType.SYSTEM_PROMPT,
        prompt_template="rag_system_prompt",
    )

    # Retrieval event
    collector.capture_event(
        call_id="call_1",
        model="gpt-4",
        provider="openai",
        input_tokens=1500,
        output_tokens=0,
        phase=RequestPhase.REQUEST,
        operation_type=OperationType.RETRIEVAL,
        prompt_template="rag_system_prompt",
    )

    # Model reasoning event
    collector.capture_event(
        call_id="call_1",
        model="gpt-4",
        provider="openai",
        input_tokens=0,
        output_tokens=450,
        phase=RequestPhase.RESPONSE,
        operation_type=OperationType.MODEL_REASONING,
        prompt_template="rag_system_prompt",
        quality_score=0.92,
        latency_ms=2500.0,
    )

    # Second call with different prompt
    collector.capture_event(
        call_id="call_2",
        model="gpt-4",
        provider="openai",
        input_tokens=2000,
        output_tokens=200,
        operation_type=OperationType.RETRIEVAL,
        prompt_template="search_optimized_prompt",
        quality_score=0.88,
        latency_ms=1800.0,
    )

    # Third call with low quality
    collector.capture_event(
        call_id="call_3",
        model="gpt-4",
        provider="openai",
        input_tokens=3000,
        output_tokens=100,
        operation_type=OperationType.RETRIEVAL,
        prompt_template="complex_query_prompt",
        quality_score=0.65,
        latency_ms=3200.0,
    )

    print("✅ Captured 5 events across 3 calls\n")

    # 3. Analyze with attribution model
    print("📈 Attribution Analysis:")
    print("-" * 60)

    attribution = AttributionModel(collector.store)

    # Analyze first call
    attr_call1 = attribution.analyze_call("call_1")
    print(f"\nCall 1 Attribution (Total: {attr_call1.total_tokens} tokens):")
    print(f"  By Phase:")
    for phase, tokens in attr_call1.by_phase.items():
        pct = 100 * tokens / attr_call1.total_tokens
        print(f"    - {phase.value}: {tokens} ({pct:.1f}%)")

    print(f"  By Operation:")
    for op, tokens in attr_call1.by_operation.items():
        pct = 100 * tokens / attr_call1.total_tokens
        print(f"    - {op.value}: {tokens} ({pct:.1f}%)")

    # 4. Query with Analytics API
    print("\n\n📊 Session Analytics:")
    print("-" * 60)

    analytics = Analytics(collector, attribution)

    # Session stats
    stats = analytics.get_session_stats(session_id)
    print(f"\nSession Summary:")
    print(f"  Total tokens: {stats.total_tokens:,}")
    print(f"  Total calls: {stats.total_calls}")
    print(f"  Avg latency: {stats.avg_latency_ms:.1f}ms")
    print(f"  Avg quality: {stats.avg_quality_score:.2f}")

    # Token breakdown by operation
    print(f"\nTokens by Operation:")
    by_op = analytics.get_tokens_by_operation(session_id)
    for op, tokens in sorted(by_op.items(), key=lambda x: x[1], reverse=True):
        pct = 100 * tokens / stats.total_tokens
        print(f"  - {op}: {tokens:,} ({pct:.1f}%)")

    # Token breakdown by phase
    print(f"\nTokens by Phase:")
    by_phase = analytics.get_tokens_by_phase(session_id)
    for phase, tokens in sorted(by_phase.items(), key=lambda x: x[1], reverse=True):
        pct = 100 * tokens / stats.total_tokens
        print(f"  - {phase}: {tokens:,} ({pct:.1f}%)")

    # Prompt efficiency
    print(f"\nPrompt Efficiency Ranking:")
    prompts = analytics.get_prompt_stats(session_id)
    for prompt, data in sorted(
        prompts.items(), key=lambda x: x[1]["efficiency_score"], reverse=True
    ):
        print(f"  - {prompt}:")
        print(f"      Avg tokens: {data['avg_tokens']:.0f}")
        print(f"      Avg quality: {data['avg_quality']:.2f}")
        print(f"      Efficiency: {data['efficiency_score']:.4f}")

    # Problematic calls
    print(f"\nProblematic Calls (high tokens, low quality):")
    problematic = analytics.get_problematic_calls(session_id)
    if problematic:
        for call in problematic[:3]:
            print(f"  - {call['call_id']}: {call['total_tokens']} tokens, "
                  f"quality {call['avg_quality']:.2f}")
    else:
        print("  None found")

    # Summary
    print(f"\n\n📋 Complete Summary:")
    print("-" * 60)
    summary = analytics.get_summary(session_id)
    print(f"Session: {summary['session_id']}")
    print(f"Total tokens: {summary['total_tokens']:,}")
    print(f"Total calls: {summary['total_calls']}")
    print(f"Duration: {summary['duration_seconds']:.1f}s" if summary['duration_seconds'] else "Duration: N/A")
    print(f"Tokens per call: {summary['tokens_per_call']:.0f}")


if __name__ == "__main__":
    main()
