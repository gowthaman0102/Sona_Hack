from app.core.model_registry import (
    ModelTier,
    get_model_by_tier,
)
from app.models.routing import (
    RoutedResponse,
    RoutingDecision,
)
from app.services.multi_model_service import MultiModelService
from app.services.query_analyzer import QueryAnalyzer
from app.services.routing_explanation import RoutingExplanationService


class IntelligentRouter:
    """
    Core AURA routing engine.

    Supports:
    - automatic routing
    - manual model-tier override
    - reasoning-mode policy
    - manual thinking override
    - structured routing explanations
    """

    def __init__(self) -> None:
        self.analyzer = QueryAnalyzer()
        self.models = MultiModelService()
        self.explanations = RoutingExplanationService()

    def route(
        self,
        prompt: str,
        override_tier: str | None = None,
        override_thinking: bool | None = None,
    ) -> RoutedResponse:

        analysis = self.analyzer.analyze(
            prompt
        )

        recommended_tier = ModelTier(
            analysis.recommended_tier
        )

        override_applied = (
            override_tier is not None
        )

        if override_applied:
            selected_tier = ModelTier(
                override_tier
            )
        else:
            selected_tier = (
                recommended_tier
            )

        profile = get_model_by_tier(
            selected_tier
        )

        automatic_thinking = (
            self._should_enable_thinking(
                analysis=analysis,
                tier=selected_tier,
            )
        )

        thinking_override_applied = (
            override_thinking is not None
        )

        if thinking_override_applied:
            thinking_enabled = bool(
                override_thinking
            )
        else:
            thinking_enabled = (
                automatic_thinking
            )

        result = self.models.generate_for_tier(
            tier=selected_tier,
            prompt=prompt,
            system_prompt=(
                "You are an assistant inside AURA. "
                "Give only the final answer. "
                "Do not expose internal reasoning."
            ),
            think=thinking_enabled,
        )

        explanation = (
            self.explanations.explain(
                analysis=analysis,
                recommended_tier=(
                    recommended_tier
                ),
                selected_tier=(
                    selected_tier
                ),
                selected_profile=profile,
                override_applied=(
                    override_applied
                ),
                thinking_enabled=(
                    thinking_enabled
                ),
                thinking_override_applied=(
                    thinking_override_applied
                ),
            )
        )

        routing = RoutingDecision(
            recommended_tier=(
                recommended_tier.value
            ),
            selected_tier=(
                selected_tier.value
            ),
            selected_model=(
                profile.model_name
            ),
            compute_score=(
                profile.compute_score
            ),
            override_applied=(
                override_applied
            ),
            thinking_override_applied=(
                thinking_override_applied
            ),
            thinking_enabled=(
                thinking_enabled
            ),
            analysis=analysis,
            explanation=explanation,
        )

        return RoutedResponse(
            prompt=prompt,
            routing=routing,
            response=result["response"],
            prompt_tokens=(
                result["prompt_tokens"]
            ),
            output_tokens=(
                result["output_tokens"]
            ),
            latency_seconds=(
                result["latency_seconds"]
            ),
            tokens_per_second=(
                result["tokens_per_second"]
            ),
        )

    def _should_enable_thinking(
        self,
        analysis,
        tier: ModelTier,
    ) -> bool:

        return (
            tier == ModelTier.HIGH
            and analysis.reasoning_required
            and analysis.complexity_score >= 9
        )
