# OpenAnchor

**See every LLM request. Track costs, latency, and quality in real-time.**

Sit between your app and LLM providers. Observe token usage, latency, cost, and execution metrics for every request. Identify optimization opportunities before they become expensive problems.

[![PyPI](https://img.shields.io/pypi/v/openanchor)](https://pypi.org/project/openanchor)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org)
[![Tests: 25 Passing](https://img.shields.io/badge/tests-25%20passing-success)](./tests)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-blue.svg)](./LICENSE)

---

## 30-Second Start

```python
from openanchor import Observer

# Wrap your LLM client (any provider)
with Observer() as observer:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )

# Instant metrics
print(f"Cost: ${observer.cost:.4f}")
print(f"Tokens: {observer.tokens}")
print(f"Latency: {observer.latency_ms}ms")
```

---

## Why OpenAnchor?

**The Problem:**
- You don't know how much you're spending on LLMs
- Latency spikes go unnoticed until users complain
- No visibility into which prompts are expensive
- Cost optimization is guesswork

**The Solution:**
- Transparent observation of every LLM request
- Real-time cost tracking across all providers
- Latency analysis and bottleneck detection
- Automatic optimization recommendations

---

## Key Features

- **Real-Time Metrics:** Cost, tokens, latency, model, provider
- **Multi-Provider:** Claude, GPT-4, Gemini, Llama, custom APIs
- **Cost Attribution:** See exactly which features cost the most
- **Telemetry Export:** Send to Datadog, Prometheus, cloud observability platforms
- **Alerts:** Notify when costs exceed thresholds
- **Quality Metrics:** Track accuracy, token efficiency, response quality
- **Historical Analysis:** Trends over time

---

## Real-World Use Cases

**Monitor Costs:**
```python
with Observer() as observer:
    for i in range(100):
        response = client.chat(prompt)

daily_cost = observer.total_cost
print(f"Daily LLM spending: ${daily_cost:.2f}")
if daily_cost > 100:
    alert("LLM costs spiking!")
```

**Optimize Prompts:**
```python
# Test different approaches
results = []
for prompt_version in [v1, v2, v3]:
    with Observer() as obs:
        response = client.chat(prompt_version)
    results.append({
        "version": prompt_version,
        "cost": obs.cost,
        "tokens": obs.tokens,
        "quality": evaluate(response)
    })

# v2 is cheapest and best
best = min(results, key=lambda x: x['cost'])
```

**Detect Problems:**
```python
with Observer() as observer:
    for req in requests:
        observer.track(req)

# Latency spiked?
if observer.p99_latency > 2000:
    print("Provider degradation detected")
```

---

## Metrics Collected

| Metric | Type | Example |
|--------|------|---------|
| Cost | USD | $0.012 |
| Tokens | Count | 245 input, 43 output |
| Latency | ms | 245ms |
| Model | String | gpt-4-turbo |
| Provider | String | openai |
| Quality | Score | 0.95 |

---

## Installation

```bash
pip install openanchor
# or with uv
uv pip install openanchor
```

---

## Documentation

- [Quick Start](docs/QUICKSTART.md) — Add observation to your app
- [Providers](docs/PROVIDERS.md) — Supported LLM APIs
- [Metrics](docs/METRICS.md) — What's tracked and how
- [Telemetry](docs/TELEMETRY.md) — Export to monitoring platforms
- [Examples](examples/) — Real-world setups

---

## License

Proprietary License - Free to use with explicit attribution. See [LICENSE](LICENSE).

---

**OpenAnchor v2.0.0** | LLM observability | Python 3.10+ | 25 tests passing

## License

MIT

---

**MCP 2.0 Mega-Platform | v2.0.0 | Wheels-Only Distribution**
