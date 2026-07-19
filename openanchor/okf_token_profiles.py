"""OKF Token Profile Management for OpenAnchor.

Token attribution profiles by model and domain, enabling efficient
cost-aware query planning and model selection based on historical patterns.
"""

from pathlib import Path
from typing import Dict, List, Optional
import json
from dataclasses import dataclass, asdict


@dataclass
class TokenProfile:
    """Token distribution profile for a model-domain combination."""

    model_id: str
    domain: str
    system_prompt_pct: float  # 0-100
    retrieval_pct: float
    user_input_pct: float
    overhead_pct: float
    avg_total_tokens: int
    percentile_95: int
    samples: int
    last_updated: str


class OKFTokenProfileCatalog:
    """Manage token profiles as OKF documents."""

    def __init__(self, catalog_dir: Path = None):
        self.catalog_dir = catalog_dir or Path.cwd() / "token_profiles"
        self.catalog_dir.mkdir(exist_ok=True)

    def save_profile(self, profile: TokenProfile) -> None:
        """Save token profile as OKF document."""
        filename = f"{profile.model_id}_{profile.domain}.json"
        filepath = self.catalog_dir / filename

        with open(filepath, 'w') as f:
            json.dump(asdict(profile), f, indent=2)

    def get_profile(self, model_id: str, domain: str) -> Optional[TokenProfile]:
        """Retrieve token profile."""
        filename = f"{model_id}_{domain}.json"
        filepath = self.catalog_dir / filename

        if not filepath.exists():
            return None

        with open(filepath) as f:
            data = json.load(f)
            return TokenProfile(**data)

    def get_model_efficiency(self, model_ids: List[str]) -> Dict[str, float]:
        """Compare token efficiency across models (lower is better)."""
        efficiency = {}

        for model_id in model_ids:
            profiles = []
            for f in self.catalog_dir.glob(f"{model_id}_*.json"):
                with open(f) as fp:
                    data = json.load(fp)
                    profiles.append(data)

            if profiles:
                avg_tokens = sum(p["avg_total_tokens"] for p in profiles) / len(profiles)
                efficiency[model_id] = avg_tokens

        return efficiency


class TokenProfileAnalyzer:
    """Analyze token usage patterns for cost optimization."""

    @staticmethod
    def estimate_cost(model_id: str, domain: str,
                     input_tokens: int, catalog: OKFTokenProfileCatalog) -> Optional[float]:
        """Estimate total tokens needed based on profile."""
        profile = catalog.get_profile(model_id, domain)
        if not profile:
            return None

        # Scale by domain-specific ratios
        system_tokens = int(input_tokens * (profile.system_prompt_pct / 100))
        retrieval_tokens = int(input_tokens * (profile.retrieval_pct / 100))
        overhead_tokens = int(input_tokens * (profile.overhead_pct / 100))

        return system_tokens + input_tokens + retrieval_tokens + overhead_tokens

    @staticmethod
    def recommend_model(domain: str, budget: int,
                       catalog: OKFTokenProfileCatalog) -> Optional[str]:
        """Recommend most efficient model for domain within budget."""
        profiles = []
        for f in catalog.catalog_dir.glob(f"*_{domain}.json"):
            with open(f) as fp:
                data = json.load(fp)
                if data["avg_total_tokens"] <= budget:
                    profiles.append(data)

        if not profiles:
            return None

        # Return model with lowest average tokens (most efficient)
        best = min(profiles, key=lambda p: p["avg_total_tokens"])
        return best["model_id"]
