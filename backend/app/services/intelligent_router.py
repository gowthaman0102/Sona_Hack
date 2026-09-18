from app.core.model_registry import (
    ModelTier,
    get_model_by_tier,
)
from app.models.confidence import (
    EscalationAttempt,
    EscalationSummary,
)
from app.models.routing import (
    RoutedResponse,
    RoutingDecision,
)
from app.services.analytics_calculator import AnalyticsCalculator
from app.services.adaptive_routing_policy import AdaptiveRoutingPolicy
from app.services.learning_outcome_recorder import LearningOutcomeRecorder
from app.services.confidence_evaluator import ConfidenceEvaluator
from app.services.multi_model_service import MultiModelService
from app.services.query_analyzer import QueryAnalyzer
from app.services.privacy_detector import PrivacyDetector
from app.services.privacy_routing_policy import PrivacyRoutingPolicyService
from app.services.routing_explanation import RoutingExplanationService


class IntelligentRouter:
    """
    Core AURA adaptive routing engine.

    Supports:
    - automatic tier selection
    - manual tier override
    - thinking-mode policy
    - structured routing explanations
    - response confidence evaluation
    - confidence-based model escalation
    - escalation history and explanation
    """

    def __init__(
        self,
        learning_recorder: LearningOutcomeRecorder | None = None,
        adaptive_policy: AdaptiveRoutingPolicy | None = None,
    ) -> None:
        self.analyzer = QueryAnalyzer()
        self.models = MultiModelService()
        self.explanations = RoutingExplanationService()
        self.confidence = ConfidenceEvaluator()
        self.analytics = AnalyticsCalculator()
        self.privacy = PrivacyDetector()
        self.privacy_policy = PrivacyRoutingPolicyService()
        self.learning_recorder = learning_recorder
        self.adaptive_policy = adaptive_policy

    def route(
        self,
        prompt: str,
        override_tier: str | None = None,
        override_thinking: bool | None = None,
    ) -> RoutedResponse:

        analysis = self.analyzer.analyze(
            prompt
        )

        privacy = self.privacy.assess(
            prompt
        )

        recommended_tier = ModelTier(
            analysis.recommended_tier
        )

        override_applied = (
            override_tier is not None
        )

        adaptive_recommendation = None

        if (
            not override_applied
            and self.adaptive_policy is not None
        ):
            adaptive_recommendation = (
                self.adaptive_policy.recommend(
                    task_type=analysis.task_type,
                    baseline_tier=(
                        recommended_tier.value
                    ),
                )
            )

        adaptive_tier = (
            ModelTier(
                adaptive_recommendation.recommended_tier
            )
            if (
                adaptive_recommendation is not None
                and adaptive_recommendation.learning_applied
            )
            else recommended_tier
        )

        initial_tier = (
            ModelTier(override_tier)
            if override_applied
            else adaptive_tier
        )

        current_tier = initial_tier

        thinking_override_applied = (
            override_thinking is not None
        )

        attempts: list[EscalationAttempt] = []
        metric_attempts = []

        final_result = None
        final_confidence = None
        final_thinking = False

        while True:
            profile = get_model_by_tier(
                current_tier
            )

            if privacy.requires_local:
                self.privacy_policy.assert_local_model(
                    profile.model_name
                )

            automatic_thinking = (
                self._should_enable_thinking(
                    analysis=analysis,
                    tier=current_tier,
                )
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
                tier=current_tier,
                prompt=prompt,
                system_prompt=(
                    "You are an assistant inside AURA. "
                    "Give only the final answer. "
                    "Do not expose internal reasoning."
                ),
                think=thinking_enabled,
            )

            confidence = self.confidence.evaluate(
                response=result["response"],
                analysis=analysis,
            )

            attempts.append(
                EscalationAttempt(
                    tier=current_tier.value,
                    model_name=profile.model_name,
                    confidence_score=(
                        confidence.score
                    ),
                    confidence_level=(
                        confidence.level
                    ),
                    should_escalate=(
                        confidence.should_escalate
                    ),
                    reasons=confidence.reasons,
                )
            )

            metric_attempts.append(
                self.analytics.build_attempt(
                    tier=current_tier.value,
                    model_name=profile.model_name,
                    compute_score=(
                        profile.compute_score
                    ),
                    confidence_score=(
                        confidence.score
                    ),
                    confidence_level=(
                        confidence.level
                    ),
                    should_escalate=(
                        confidence.should_escalate
                    ),
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
            )

            final_result = result
            final_confidence = confidence
            final_thinking = thinking_enabled

            if override_applied:
                break

            if not confidence.should_escalate:
                break

            next_tier = self._next_tier(
                current_tier
            )

            if next_tier is None:
                break

            current_tier = next_tier

        final_profile = get_model_by_tier(
            current_tier
        )

        privacy_policy = (
            self.privacy_policy.evaluate(
                assessment=privacy,
                selected_model=(
                    final_profile.model_name
                ),
            )
        )

        explanation = (
            self.explanations.explain(
                analysis=analysis,
                recommended_tier=(
                    recommended_tier
                ),
                selected_tier=(
                    current_tier
                ),
                selected_profile=(
                    final_profile
                ),
                override_applied=(
                    override_applied
                ),
                thinking_enabled=(
                    final_thinking
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
                current_tier.value
            ),
            selected_model=(
                final_profile.model_name
            ),
            compute_score=(
                final_profile.compute_score
            ),
            override_applied=(
                override_applied
            ),
            thinking_override_applied=(
                thinking_override_applied
            ),
            thinking_enabled=(
                final_thinking
            ),
            analysis=analysis,
            explanation=explanation,
        )

        escalation = EscalationSummary(
            escalated=(
                current_tier != initial_tier
            ),
            initial_tier=(
                initial_tier.value
            ),
            final_tier=(
                current_tier.value
            ),
            reason=self._escalation_reason(
                attempts=attempts,
                override_applied=override_applied,
                initial_tier=initial_tier,
                final_tier=current_tier,
            ),
            attempts=attempts,
        )

        route_analytics = (
            self.analytics.summarize(
                metric_attempts
            )
        )

        if self.learning_recorder is not None:
            self.learning_recorder.record_route(
                task_type=analysis.task_type,
                analytics=route_analytics,
            )

        return RoutedResponse(
            prompt=prompt,
            routing=routing,
            response=final_result["response"],
            confidence=final_confidence,
            escalation=escalation,
            privacy=privacy,
            privacy_policy=privacy_policy,
            analytics=route_analytics,
            prompt_tokens=(
                final_result["prompt_tokens"]
            ),
            output_tokens=(
                final_result["output_tokens"]
            ),
            latency_seconds=(
                final_result["latency_seconds"]
            ),
            tokens_per_second=(
                final_result["tokens_per_second"]
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

    def _next_tier(
        self,
        tier: ModelTier,
    ) -> ModelTier | None:

        if tier == ModelTier.LOW:
            return ModelTier.MEDIUM

        if tier == ModelTier.MEDIUM:
            return ModelTier.HIGH

        return None

    def _escalation_reason(
        self,
        attempts: list[EscalationAttempt],
        override_applied: bool,
        initial_tier: ModelTier,
        final_tier: ModelTier,
    ) -> str:

        if override_applied:
            return (
                "Automatic escalation was disabled because "
                "the user explicitly overrode the model tier."
            )

        if final_tier != initial_tier:
            failed_attempts = [
                attempt
                for attempt in attempts[:-1]
                if attempt.should_escalate
            ]

            reasons = []

            for attempt in failed_attempts:
                reasons.extend(
                    attempt.reasons
                )

            unique_reasons = list(
                dict.fromkeys(
                    reasons
                )
            )

            reason_text = (
                ", ".join(unique_reasons)
                if unique_reasons
                else "low response confidence"
            )

            return (
                f"AURA escalated from "
                f"{initial_tier.value.upper()} to "
                f"{final_tier.value.upper()} because earlier "
                f"responses did not meet the confidence "
                f"threshold. Detected risks: {reason_text}."
            )

        last_attempt = attempts[-1]

        if (
            last_attempt.should_escalate
            and final_tier == ModelTier.HIGH
        ):
            return (
                "The HIGH tier is AURA's strongest configured "
                "model, so no further escalation is available "
                "even though confidence remained below the "
                "acceptance threshold."
            )

        return (
            "The initial response met AURA's confidence "
            "threshold, so no escalation was required."
        )
