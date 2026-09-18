from typing import Any

from app.core.model_registry import (
    ModelTier,
    get_model_by_tier,
)
from app.services.ollama_service import OllamaService


class MultiModelService:
    """
    Executes prompts against AURA's registered model tiers.
    """

    def __init__(self) -> None:
        self.ollama = OllamaService()

    def generate_for_tier(
        self,
        tier: ModelTier,
        prompt: str,
        system_prompt: str | None = None,
        think: bool = False,
    ) -> dict[str, Any]:

        profile = get_model_by_tier(tier)

        result = self.ollama.generate(
            model=profile.model_name,
            prompt=prompt,
            system_prompt=system_prompt,
            think=think,
        )

        total_duration_ns = result.get("total_duration")
        eval_duration_ns = result.get("eval_duration")
        output_tokens = result.get("eval_count")

        latency_seconds = (
            round(
                total_duration_ns / 1_000_000_000,
                3,
            )
            if total_duration_ns
            else None
        )

        tokens_per_second = None

        if (
            output_tokens
            and eval_duration_ns
            and eval_duration_ns > 0
        ):
            tokens_per_second = round(
                output_tokens /
                (eval_duration_ns / 1_000_000_000),
                2,
            )

        return {
            "tier": tier.value,
            "model_name": profile.model_name,
            "display_name": profile.display_name,
            "compute_score": profile.compute_score,
            "thinking_enabled": think,
            "response": result["response"],
            "prompt_tokens": result.get("prompt_eval_count"),
            "output_tokens": output_tokens,
            "latency_seconds": latency_seconds,
            "tokens_per_second": tokens_per_second,
        }
