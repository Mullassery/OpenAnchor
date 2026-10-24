# Competitive intelligence in roadmap and upgrade work

**Policy date:** 2026-10-19

Competitive findings are an input to product decisions, not a one-off report.
Every pending roadmap item, new feature, and routine dependency upgrade should
check the repository's [`AUDIT_FINDINGS.md`](AUDIT_FINDINGS.md) before work
starts, and record the decision in the PR or changelog.

## Required check before building

1. **Read `AUDIT_FINDINGS.md`.** Find the relevant competitor row and the
   ranked next actions. If the finding is stale, update it with a dated source.
2. **Name the competitor and the user problem.** A feature is not justified by
   "competitor has it". State the workflow it unlocks, who needs it, and how
   often. Mark unverified demand as a hypothesis.
3. **Prefer reuse over new code.** Check whether an existing Mullassery repo
   already provides the capability (see `BUNDLES.md` in the profile repo and
   the bundle role file in this repo, when present). Typical reuse:
   - crawling/fetching/robots/SSRF → **MudFish**
   - architecture maps / PR diffs → **CodeAtlas**
   - data-quality contracts / validation → **StatGuardian**
   - token counting / cost tables → **PyTokenCalc**
   - dependency graph / advisories / SBOM → **PyDeepMesh**
   - segmentation / CLV / churn → **ClusterAudienceKit**
   - activation / lineage / PII → **PyReverseETL**
   - fleet state sync → **SyncFleet** (only after conflict resolution)
4. **Choose one disposition:** build, integrate, defer, or reject. Write it
   down. A rejection with a reason is a successful outcome.
5. **For routine upgrades**, check whether the upgrade closes a known
   competitor gap or breaks a differentiated capability. Run the tests that
   cover the affected path; do not merge a green build that silently changes a
   user-visible contract.

## PR / changelog checklist

- [ ] Competitor and source URL/date recorded (or "no direct competitor").
- [ ] User impact and frequency stated; unverified demand labelled.
- [ ] Reuse check done against sibling repos/bundles.
- [ ] Failure mode and rollback considered (especially auth, PII, cost).
- [ ] Docs/roadmap status updated honestly.
- [ ] Tests or a manual verification command included.

## Review cadence

- Refresh the competitor row when a release changes the capability.
- Re-check the full `AUDIT_FINDINGS.md` at least quarterly and before a major
  release.
- If a finding is wrong or stale, correct it in the same PR that relies on it.

## Non-goals

- Copying features for parity.
- Adding a dependency just because a competitor uses it.
- Treating star counts or download counts as proof of user need.

## OSS gap analysis — 2026-10-24

**Scope.** Covers OpenAnchor v0.6.3 as implemented here: capture, six-dimension
attribution, SQLite/in-memory stores, LangChain middleware, opt-in OTEL spans,
semantic cache, `okf_*` governance, and MCP tools. Hosted SaaS is excluded unless
its core is OSS. Claims come from this repository and the sources below.

### Comparable OSS projects

| Project | License | Activity | Why comparable |
|---|---|---|---|
| OpenLLMetry | Apache-2.0 | 0.62.4, 2026-09-29 | LLM instrumentation that emits OpenTelemetry spans |
| Langfuse | MIT (core) | SDK 5.0.4, 2026-10-21 | OSS LLM observability, cost tracking, evals, prompts |
| Arize Phoenix | ELv2 | 20.x; 20.23.0, 2026-10-16 | OSS tracing, evaluation, and prompt workbench |
| LiteLLM | MIT (core) | 1.106.3, 2026-10-24 | Multi-provider gateway with spend tracking and budgets |

### Capability comparison

| Capability | OpenAnchor | OpenLLMetry | Langfuse | Phoenix | LiteLLM |
|---|---|---|---|---|---|
| Automatic LLM instrumentation | Yes | Yes | Partial | Partial | Partial |
| OpenTelemetry span export | Yes | Yes | Partial | Yes | Partial |
| Token and cost tracking | Yes | Partial | Yes | Partial | Yes |
| Multi-dimensional attribution | Yes | No | Partial | Partial | Partial |
| Local-only persistence | Yes | No | No | Partial | Partial |
| Response caching | Yes | No | No | No | Yes |
| Budget enforcement | Yes | No | No | No | Yes |
| Trace explorer or evaluation UI | No | No | Yes | Yes | No |
| Prompt management | No | No | Yes | Yes | No |

"Partial" means narrower than the comparison: Langfuse/Phoenix need external
instrumentors; their attribution uses tags, users, sessions, or metadata rather
than OpenAnchor's six fixed dimensions; LiteLLM attributes by key/team/tag and
its budget store is proxy-backed. Phoenix can use SQLite for one node.

### Gaps that matter (ranked)

1. **Framework and provider instrumentation breadth.** OpenAnchor ships a
   LangChain middleware and a generic OTEL span processor, not native
   instrumentors for LlamaIndex, CrewAI, DSPy, or raw OpenAI/Anthropic SDKs.
   OpenLLMetry's product is that breadth. Build adapters only for demonstrated
   stacks and make the generic OTEL path the first-class fallback.

2. **No trace exploration, evaluation, or prompt workflow.** There is no trace
   list, per-run waterfall, dataset evaluation, or prompt management surface.
   Langfuse and Phoenix provide those around the same telemetry. This is a
   separate product surface: integrate by exporting to an OSS backend.

3. **Budget governance is local and single-tenant.** `OKFCostGovernance` writes
   an organisation-wide policy to `budget_policy.json` in the working directory
   and keeps spend in memory; the cache is local SQLite. There is no
   key/team/project hierarchy or multi-instance coordination comparable to
   LiteLLM's proxy budgets. Build a pluggable quota backend only when demanded.

4. **Pricing coverage is narrow and manual.** Cost estimates depend on
   PyTokenCalc's static table of 24 models with `PRICING_LAST_UPDATED = "2026-09"`.
   LiteLLM maintains a broader model cost map and tokencost advertises hundreds
   of models. Integrate a maintained source rather than duplicating a table.

5. **Semantic-cache quality depends on an optional local embedder.** The default
   tries Ollama then falls back to a dependency-free hashing embedder: useful
   offline, but not semantic and collision-prone at the default threshold.
   Production hits should require a real provider and reported match quality.

### Where we are differentiated

- Six-dimension attribution is persisted per event, so cost is sliceable by
  phase, operation, template, session, model, and pattern without a pipeline.
- Local-first is real: in-memory/SQLite storage, in-process semantic cache with
  TTL and invalidation, and file-backed governance, with no required server.
- Privacy defaults: raw content is off, excerpts are redacted, hashes retained.
- MCP exposes governance, cache, and attribution operations to agent clients.

### Disposition

- **Build:** a documented generic OTEL ingestion path correlated to
  `TokenEvent`; cache guardrails requiring a real embedder; a multi-process
  quota interface only after a concrete deployment need is recorded.
- **Integrate/reuse:** Langfuse or Phoenix for UI, evals, and prompts; a
  maintained pricing source with provenance; existing OTEL instrumentors.
- **Defer/reject:** hosted UI, prompt management, a provider gateway, and a
  multi-tenant budget service; these are separate products with OSS options.

### Sources

- OpenLLMetry: https://github.com/traceloop/openllmetry (0.62.4, 2026-09-29; Apache-2.0).
- Langfuse: https://github.com/langfuse/langfuse (MIT core; PyPI 5.0.4, 2026-10-21).
- Phoenix: https://github.com/Arize-ai/phoenix (20.23.0, 2026-10-16; ELv2).
- LiteLLM: https://github.com/BerriAI/litellm (1.106.3, 2026-10-24; MIT core).
- Local: `openanchor/semantic_cache.py`, `openanchor/okf_cost_governance.py`,
  `openanchor/instrumentation.py`; PyTokenCalc `pytokencalc/pricing.py`.
