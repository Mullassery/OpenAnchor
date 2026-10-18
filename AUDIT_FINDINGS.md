# Audit findings — 2026-10-19

This file records the repository-specific findings from the portfolio audit
conducted on 2026-10-19. It is documentation only; no code or release artifacts
were changed in this pass unless explicitly noted under "Implementation status".

Sources: the repository's own README/source/workflows, GitHub metadata and
Actions runs, PyPI metadata, and official competitor documentation. Claims are
marked as verified, inferred, or open questions. "Absent" means not found in the
inspected repository/docs, not proof that it cannot exist.

## What it is

In-process LLM token-attribution middleware: 6D attribution, cost governance, semantic caching, OTel export, and MCP tools.

## Verified strengths

- Real 6D attribution, SQLite/in-memory stores, LangChain middleware, OTEL spans, semantic cache, 12 MCP tools, privacy-by-default hashing/redaction, Docker entry point, 15 tests.
- In-process design avoids a network hop; Apache-2.0.

## Verified gaps and user-facing risks

- Only LangChain integration; no auto-instrumentation for OpenAI/Anthropic SDKs or LlamaIndex.
- No dashboard; no production overhead/latency benchmark; 'framework-agnostic' remains aspirational.
- No GitHub release despite PyPI 0.6.2; alpha.

## Direct competitors

- Helicone (gateway + observability, 100+ models, prompts), Langfuse (tracing/evals/prompts), OpenLLMetry (OTel instrumentation), Phoenix.

## Ranked next actions

- P1: adopt OTel/OpenInference semantic conventions + auto-instrumentation (M).
- P1: add OpenAI/Anthropic SDK and LlamaIndex integrations (M).
- P2: publish a reproducible overhead benchmark (S).

## Do not build

- A dashboard; export to Langfuse/Phoenix/Helicone instead.

## Evidence gaps / validation needed

- No user data; no latency overhead numbers; no regulated-environment validation.

## Recommended disposition

Invest as an interoperability layer, not as a platform.

## Implementation status

No code changes in this pass.
