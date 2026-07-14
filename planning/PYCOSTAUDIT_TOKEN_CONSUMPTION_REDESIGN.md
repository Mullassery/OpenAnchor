# PyCostAudit v0.6: Token Consumption Model Redesign

**Problem:** v0.5 assumes all tokens work like Claude (uniform input/output rates). Multi-LLM reality is far more complex.

**Timeline:** Post-v0.5, Phase 1 of v0.6 development

---

## What Changed from v0.4 → v0.5 → v0.6

| Version | Scope | Token Model | Assumption | Reality |
|---------|-------|------------|-----------|---------|
| **v0.4** | Claude Code only | Simple (input/output) | All tokens equal | ✅ Works (Claude) |
| **v0.5** | Multi-LLM/agent | Simple (input/output) | All tokens equal | ❌ BREAKS for multi-LLM |
| **v0.6** | Multi-LLM/agent | **Provider-specific** | Tokens vary by provider | ✅ Handles all LLMs |

---

## Different Token Consumption Models

### 1. Claude (Token-based)
```
Cost = (input_tokens × $3.00/1M + output_tokens × $15.00/1M) / 1M
Assumption: All tokens cost the same
```

### 2. GPT-4o (Token + Mini Token Model)
```
Cost = (input_full × $2.50 + input_mini × $0.625)/1M 
        + (output_full × $10.00 + output_mini × $2.50)/1M

Note: GPT-4o returns BOTH full and mini token counts
      Need to track which model variant was used
```

### 3. Gemini (Character-based Billing)
```
Cost = input_characters × $0.000000375 + output_characters × $0.000001500

Note: NOT token-based
      Need UTF-8 character counting
      Completely different billing model
```

### 4. Groq (Speed-tiered Pricing)
```
Cost = tokens × $0.05/1M (standard speed)
      = tokens × $0.10/1M (fast speed)
      = tokens × $0.20/1M (fastest speed)

Note: Same model, different prices based on latency SLA
      Need to track speed tier per call
```

### 5. DeepSeek (Usage-based Batching)
```
Cost = batch_size_factor × base_tokens_cost

Note: Costs vary based on whether called in batch or single
      Need to track batch context
```

### 6. Open-source APIs (Quantization-dependent)
```
Cost = tokens × rate

BUT token count changes based on:
  - Quantization level (int8 vs int4 vs fp8)
  - Model version (Llama 2 vs 3 vs 3.1)
  - Provider's tokenizer (different tokenizers count differently)

Note: Same model, different token counts on different providers
```

---

## Required Design Changes

### 1. Provider-Specific Cost Models

```python
# v0.5 (CURRENT - WRONG for multi-LLM)
cost = (input_tokens * input_rate + output_tokens * output_rate) / 1M

# v0.6 (CORRECT for multi-LLM)
class CostModel(ABC):
    @abstractmethod
    def calculate(self, usage: UsageData) -> float:
        """Calculate cost based on provider-specific model"""
        pass

class ClaudeTokenModel(CostModel):
    def calculate(self, usage: UsageData) -> float:
        # Input/output token rates
        pass

class GPT4oTokenModel(CostModel):
    def calculate(self, usage: UsageData) -> float:
        # Full token + mini token rates
        pass

class GeminiCharacterModel(CostModel):
    def calculate(self, usage: UsageData) -> float:
        # Character-based billing
        pass

class GroqSpeedTieredModel(CostModel):
    def calculate(self, usage: UsageData) -> float:
        # Speed tier affects pricing
        pass
```

### 2. Provider Usage Data Structure

```python
# v0.5 (TOO SIMPLE)
@dataclass
class UsageData:
    input_tokens: int
    output_tokens: int
    # That's it - assumes all tokens are equal

# v0.6 (PROVIDER-SPECIFIC)
@dataclass
class UsageData:
    provider: str
    model: str
    # Standard tokens
    input_tokens: int
    output_tokens: int
    # Provider-specific variants
    input_mini_tokens: Optional[int] = None  # GPT-4o
    input_characters: Optional[int] = None   # Gemini
    output_characters: Optional[int] = None  # Gemini
    # Context
    speed_tier: Optional[str] = None  # Groq
    batch_size: Optional[int] = None  # DeepSeek
    quantization_level: Optional[str] = None  # Open-source
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    model_variant: Optional[str] = None  # Llama 2 vs 3 vs 3.1
```

### 3. Provider Registry with Models

```python
# v0.5 (STATIC)
PROVIDERS = {
    "anthropic": {
        "claude-3-5-sonnet": {"input": 3.00, "output": 15.00}
    }
}

# v0.6 (DYNAMIC WITH MODELS)
PROVIDERS = {
    "anthropic": {
        "claude-3-5-sonnet": {
            "model_class": ClaudeTokenModel,
            "input_rate": 3.00,
            "output_rate": 15.00
        }
    },
    "openai": {
        "gpt-4o": {
            "model_class": GPT4oTokenModel,
            "input_full_rate": 2.50,
            "input_mini_rate": 0.625,
            "output_full_rate": 10.00,
            "output_mini_rate": 2.50
        }
    },
    "google": {
        "gemini-2-flash": {
            "model_class": GeminiCharacterModel,
            "input_rate": 0.000000375,
            "output_rate": 0.000001500,
            "char_encoding": "utf-8"
        }
    },
    "groq": {
        "llama-70b": {
            "model_class": GroqSpeedTieredModel,
            "base_rate": 0.05,
            "speed_tiers": {
                "standard": 0.05,
                "fast": 0.10,
                "fastest": 0.20
            }
        }
    }
}
```

### 4. Cost Calculator Refactoring

```python
# v0.5 (SIMPLE BUT BROKEN)
class CostCalculator:
    def calculate(self, provider: str, model: str, 
                  input_tokens: int, output_tokens: int) -> float:
        rate = self.pricing_manager.get_rates(provider, model)
        return (input_tokens * rate["input"] + 
                output_tokens * rate["output"]) / 1M

# v0.6 (PROVIDER-AWARE)
class CostCalculator:
    def calculate(self, usage: UsageData) -> float:
        """Calculate cost using provider-specific model"""
        provider_config = self.registry.get_provider(usage.provider)
        model_config = provider_config.get(usage.model)
        cost_model = model_config["model_class"]()
        return cost_model.calculate(usage)
    
    def calculate_with_variants(self, provider: str, model: str,
                                input_tokens: int, output_tokens: int,
                                **provider_specific_kwargs) -> float:
        """Handle provider-specific parameters"""
        usage = UsageData(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            **provider_specific_kwargs  # speed_tier, mini_tokens, etc.
        )
        return self.calculate(usage)
```

---

## Implementation Phases for v0.6

### Phase 1: Abstraction Layer (Week 1)
- [ ] Create CostModel abstract base class
- [ ] Implement provider-specific models (Claude, GPT-4o, Gemini, Groq)
- [ ] Create UsageData dataclass with provider-specific fields
- [ ] Refactor PricingManager to use provider models

### Phase 2: Integration (Week 2)
- [ ] Update CostCalculator to use provider models
- [ ] Update CostDatabase to store provider-specific usage data
- [ ] Add queries for provider-specific metrics
- [ ] Backward compatibility layer (wrap v0.5 calls)

### Phase 3: Documentation (Week 3)
- [ ] Update README with provider-specific examples
- [ ] API documentation for each cost model
- [ ] Migration guide from v0.5 to v0.6
- [ ] Per-provider integration examples

### Phase 4: Testing (Week 4)
- [ ] Unit tests for each cost model
- [ ] Integration tests with real provider data
- [ ] Accuracy validation (±1% vs actual billing)
- [ ] Benchmarks across providers

---

## Backward Compatibility (v0.5 → v0.6)

```python
# v0.5 code (still works in v0.6)
from pycostaudit import CostCalculator
calc = CostCalculator()
cost = calc.calculate("anthropic", "claude-3-5-sonnet", 1000, 250)

# New v0.6 code (explicit provider-specific data)
from pycostaudit import CostCalculator, UsageData, GroqSpeedTieredModel
usage = UsageData(
    provider="groq",
    model="llama-70b",
    input_tokens=1000,
    output_tokens=250,
    speed_tier="fast"  # NEW: Groq-specific
)
cost = calc.calculate(usage)

# NEW: Gemini (character-based)
usage = UsageData(
    provider="google",
    model="gemini-2-flash",
    input_characters=5000,  # NEW
    output_characters=2000  # NEW
)
cost = calc.calculate(usage)
```

---

## Impact on OpenAnchor

OpenAnchor will benefit from this redesign:

```python
# v0.5 (assumes all tokens equal)
if model == "gpt-4o-mini":
    # Can't optimize correctly because token counting is wrong
    pass

# v0.6 (understands provider-specific models)
if model == "gpt-4o-mini":
    usage = UsageData(
        provider="openai",
        model="gpt-4o-mini",
        input_tokens=input_tokens,
        input_mini_tokens=mini_token_count,  # ACCURATE
        output_tokens=output_tokens,
        output_mini_tokens=mini_output_count  # ACCURATE
    )
    cost = calculator.calculate(usage)  # CORRECT cost
```

---

## Risk & Mitigation

**Risk:** Breaking change from v0.5 → v0.6
**Mitigation:** Backward compatibility layer + migration guide

**Risk:** Missing provider-specific behaviors
**Mitigation:** Implement iteratively; start with 3 major providers

**Risk:** Cost calculation accuracy
**Mitigation:** Validate ±1% against real usage from each provider

---

## Summary

**v0.5:** Simple token model that works for Claude
**v0.6:** Provider-specific cost models that work for all LLMs

**Why it matters:** 
- OpenAnchor can't optimize costs if cost calculation is wrong
- Different LLMs consume and bill tokens differently
- Accurate cost calculation is the foundation for accurate optimization

**Next step:** After v0.5 launch, start v0.6 design & implementation
