# Audit Report: openanchor
Date: 2026-10-26 | Type: Read-only systems design audit  
Repo: ../openanchor (local: /Users/georgimullassery/Desktop/Projects/openanchor) | Branch: main | Status: clean

## Overview
LLM token-attribution middleware with 6D attribution, LangChain integration, real OpenTelemetry export, semantic caching, cost governance. Python package `openanchor` (pyproject). Apache 2.0.

## Architecture / Entry points
- Core: `openanchor/collector.py`, `attribution.py`, `attribution_6d.py`, `analytics.py`, `storage.py` (SQLite + in-memory). 
- Middleware: `openanchor/middleware/langchain.py`. 
- OTEL: `openanchor/otel.py`. 
- Semantic cache: `openanchor/semantic_cache.py`, `_mcp_tools.py`, `_mcp_connector.py`. 
- CLI/entry: `openanchor/__main__.py`, `openanchor/scripts/post_install.py`. 
- Providers: `openanchor/providers/llm.py`.

## Dependencies
Runtime: `pytokencalc>=0.7.0` (cross-repo dependency on Mullassery/PyTokenCalc), `requests>=2.31.0`, `pydantic>=2.0.0`, `opentelemetry-api/sdk<2.0`. Optional: auto-instrumentation, otel exporter, dev/docs. Lock file present (`requirements-lock.txt`).

## Data / State
- Events stored via `TokenCollector`/stores; SQLite with indexing/WAL mentioned in README. Retention/TTL purging supported.
- Semantic cache uses embeddings + SQLite storage.
- Privacy: raw prompt/response capture off by default; hash+length; opt-in redacted for PII/secrets (`openanchor/privacy.py`).

## APIs / Contracts
- Collector API, Analytics API, LangChain middleware. MCP tools for cache (12 tools per README). Docker entry point `python -m openanchor`.

## Security observations
- Network: `semantic_cache.py:87` uses `requests.post(...)`, `:109` uses `requests.get(f"{self.host}/api/tags", ...)` to Ollama/local endpoints. Host/URL construction needs review for SSRF/localhost abuse.
- Secrets/PII: privacy module exists; redaction mentioned. README states "PII/secret redaction pass (see openanchor.privacy) before being stored/sent".
- Cross-repo dependency: relies on `pytokencalc>=0.7.0` from PyPI/GitHub — supply chain risk if upstream deleted (user instruction says dependencies must be forked).
- OTEL exporters optional; tracing off by default.
- No obvious hardcoded secrets in scanned code.

## Tests / CI
- CI: ci.yml, commit-conventions.yml. Tests: 15 test files found (grep). Dev deps include pytest, bandit, mypy, ruff, black.

## Findings
| ID | Severity | Category | Evidence | Impact | Root cause | Recommendation | Confidence |
|---|---|---|---|---|---|---|---|
| OAN-001 | High | Supply Chain / Dependency | pyproject.toml:29 `pytokencalc>=0.7.0`; requirements-lock.txt:15 same. Cross-repo dep on Mullassery/PyTokenCalc | If PyTokenCalc repo deleted/unpublished, openanchor cannot install/build. | External dependency on sibling repo without vendoring/fork. | Fork PyTokenCalc into repo or vendor it (per user instruction); pin to fork URL or include as git dependency; add SBOM and fallback. | High |
| OAN-002 | Medium | Network Security (SSRF) | semantic_cache.py:87,109 — requests to `self.host` (Ollama). Host not validated against allowlist/private ranges. | Malicious config could probe internal services. | Unvalidated user-configurable host. | Enforce allowlist (localhost/loopback/private only if explicitly enabled), scheme allowlist (http/https), block cloud metadata IPs, timeouts already present; validate in config. | High |
| OAN-003 | Medium | Error Handling / Resilience | semantic_cache.py makes HTTP calls with timeouts (1.5s) but unclear retry/circuit breaking. | Transient failures could cascade. | Basic requests usage. | Add retry with backoff, circuit breaker, handle connection errors explicitly; don't fail open unsafely. | Medium |
| OAN-004 | Low | Observability / Privacy | Privacy redaction exists but enforcement depends on opt-in paths. Default "raw capture off" is good. | Misconfiguration could leak PII. | Documentation/code split. | Add tests for redaction, default-deny audit logs, ensure OTEL spans don't include raw prompts/responses. | Medium |

## Strengths
- Privacy-by-default stance, real OTEL integration, semantic cache backed by real embeddings/storage, comprehensive feature set, good CI/tooling.
- LangChain middleware integration is concrete.

## Prioritized remediation
1. Address OAN-001 (fork/vendor pytokencalc).
2. Harden semantic cache host validation (OAN-002).
3. Resilience improvements (OAN-003), privacy tests (OAN-004).

## Limitations
Read-only audit; did not run tests or trace full request flows.
