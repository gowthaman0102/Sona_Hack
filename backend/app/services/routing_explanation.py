from app.core.model_registry import (
    ModelProfile,
    ModelTier,
)
from app.models.query_analysis import QueryAnalysis
from app.models.routing import RoutingExplanation


class RoutingExplanationService:
    """
    Produces deterministic, human-readable explanations
    for AURA routing decisions.
    """

    def explain(
        self,
        analysis: QueryAnalysis,
        recommended_tier: ModelTier,
        selected_tier: ModelTier,
        selected_profile: ModelProfile,
        override_applied: bool,
        thinking_enabled: bool,
        thinking_override_applied: bool,
        escalation_applied: bool = False,
    ) -> RoutingExplanation:

        signals = self._build_signals(
            analysis
        )

        summary = (
            f"AURA selected the "
            f"{selected_tier.value.upper()} tier "
            f"using {selected_profile.display_name}."
        )

        selection_reason = (
            self._selection_reason(
                analysis=analysis,
                recommended_tier=recommended_tier,
                selected_tier=selected_tier,
                override_applied=override_applied,
                escalation_applied=escalation_applied,
            )
        )

        article = self._article_for(
            analysis.task_type
        )

        complexity_reason = (
            f"The query received a complexity score of "
            f"{analysis.complexity_score}/10 and was "
            f"classified as {article} "
            f"{analysis.task_type} task."
        )

        reasoning_reason = (
            self._reasoning_reason(
                analysis=analysis,
                thinking_enabled=thinking_enabled,
                thinking_override_applied=(
                    thinking_override_applied
                ),
            )
        )

        compute_quality_tradeoff = (
            self._tradeoff_reason(
                recommended_tier=recommended_tier,
                selected_tier=selected_tier,
                override_applied=override_applied,
            )
        )

        override_reason = (
            self._override_reason(
                recommended_tier=recommended_tier,
                selected_tier=selected_tier,
                override_applied=override_applied,
            )
        )

        return RoutingExplanation(
            summary=summary,
            selection_reason=selection_reason,
            complexity_reason=complexity_reason,
            reasoning_reason=reasoning_reason,
            compute_quality_tradeoff=(
                compute_quality_tradeoff
            ),
            override_reason=override_reason,
            signals=signals,
        )

    def _build_signals(
        self,
        analysis: QueryAnalysis,
    ) -> list[str]:

        signals = [
            f"task_type={analysis.task_type}",
            (
                f"complexity="
                f"{analysis.complexity_score}/10"
            ),
        ]

        if analysis.features.has_code:
            signals.append(
                "technical_or_code_content"
            )

        if (
            analysis.features
            .has_reasoning_markers
        ):
            signals.append(
                "reasoning_markers_detected"
            )

        if (
            analysis.features
            .has_multiple_requirements
        ):
            signals.append(
                "multiple_requirements"
            )

        if analysis.features.word_count > 40:
            signals.append(
                "long_prompt"
            )

        return signals

    def _selection_reason(
        self,
        analysis: QueryAnalysis,
        recommended_tier: ModelTier,
        selected_tier: ModelTier,
        override_applied: bool,
        escalation_applied: bool,
    ) -> str:

        if override_applied:
            return (
                f"AURA recommended "
                f"{recommended_tier.value.upper()}, "
                f"but the user explicitly selected "
                f"{selected_tier.value.upper()}."
            )

        if escalation_applied:
            return (
                f"The {analysis.task_type} task with complexity "
                f"{analysis.complexity_score}/10 initially mapped "
                f"to the {recommended_tier.value.upper()} tier. "
                f"AURA then escalated to "
                f"{selected_tier.value.upper()} because the earlier "
                f"response did not meet the confidence threshold."
            )

        return (
            f"The {analysis.task_type} task with complexity "
            f"{analysis.complexity_score}/10 maps to the "
            f"{selected_tier.value.upper()} tier under "
            f"AURA's routing policy."
        )

    def _reasoning_reason(
        self,
        analysis: QueryAnalysis,
        thinking_enabled: bool,
        thinking_override_applied: bool,
    ) -> str:

        if thinking_override_applied:
            state = (
                "enabled"
                if thinking_enabled
                else "disabled"
            )

            return (
                f"Thinking mode was manually {state} "
                f"by the user."
            )

        if thinking_enabled:
            return (
                "Thinking mode was enabled because the query "
                "requires deeper reasoning and reached AURA's "
                "high-complexity reasoning threshold."
            )

        if analysis.reasoning_required:
            return (
                "The query requires reasoning, but thinking "
                "mode is disabled for the selected route."
            )

        return (
            "Thinking mode was not required for this query."
        )

    def _tradeoff_reason(
        self,
        recommended_tier: ModelTier,
        selected_tier: ModelTier,
        override_applied: bool,
    ) -> str:

        if override_applied:
            if selected_tier == recommended_tier:
                return (
                    "The override selected the same tier that "
                    "AURA recommended, so the compute-quality "
                    "trade-off is unchanged."
                )

            selected_score = self._tier_cost(
                selected_tier
            )

            recommended_score = self._tier_cost(
                recommended_tier
            )

            if selected_score > recommended_score:
                return (
                    f"The user selected "
                    f"{selected_tier.value.upper()} instead of "
                    f"AURA's recommended "
                    f"{recommended_tier.value.upper()} tier. "
                    f"This increases compute usage in exchange "
                    f"for access to a more capable model."
                )

            return (
                f"The user selected "
                f"{selected_tier.value.upper()} instead of "
                f"AURA's recommended "
                f"{recommended_tier.value.upper()} tier. "
                f"This reduces compute usage, but may reduce "
                f"response quality for this request."
            )

        if selected_tier == ModelTier.LOW:
            return (
                "LOW prioritizes speed and minimal compute "
                "for straightforward tasks where a larger "
                "model would add unnecessary cost."
            )

        if selected_tier == ModelTier.MEDIUM:
            return (
                "MEDIUM balances response quality and compute "
                "cost for moderately complex requests."
            )

        return (
            "HIGH prioritizes reasoning quality and capability "
            "for difficult tasks, accepting higher latency and "
            "compute usage."
        )

    def _override_reason(
        self,
        recommended_tier: ModelTier,
        selected_tier: ModelTier,
        override_applied: bool,
    ) -> str:

        if not override_applied:
            return (
                "No model-tier override was applied."
            )

        if selected_tier == recommended_tier:
            return (
                f"The user explicitly selected "
                f"{selected_tier.value.upper()}, which matches "
                f"AURA's recommendation."
            )

        return (
            f"User override changed the route from "
            f"{recommended_tier.value.upper()} to "
            f"{selected_tier.value.upper()}."
        )

    def _tier_cost(
        self,
        tier: ModelTier,
    ) -> int:

        scores = {
            ModelTier.LOW: 1,
            ModelTier.MEDIUM: 2,
            ModelTier.HIGH: 4,
        }

        return scores[tier]

    def _article_for(
        self,
        word: str,
    ) -> str:

        if (
            word
            and word[0].lower()
            in {"a", "e", "i", "o", "u"}
        ):
            return "an"

        return "a"
