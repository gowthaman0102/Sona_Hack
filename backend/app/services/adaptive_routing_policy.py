from app.models.learning import (
    LearningRecommendation,
    TierReliability,
)
from app.services.performance_history_store import (
    PerformanceHistoryStore,
)


class AdaptiveRoutingPolicy:
    """
    Conservative history-aware tier recommendation.

    The query analyzer's baseline tier is treated as the
    minimum capability floor.

    Learning may proactively upgrade to a stronger tier
    when:

    1. the baseline has enough historical observations,
    2. baseline reliability is poor, and
    3. a stronger tier has enough observations and
       strong reliability.

    Learning never downgrades below the analyzer baseline.
    """

    TIER_ORDER = (
        "low",
        "medium",
        "high",
    )

    MIN_ATTEMPTS = 5

    POOR_RELIABILITY_THRESHOLD = 0.60
    STRONG_RELIABILITY_THRESHOLD = 0.75

    def __init__(
        self,
        store: PerformanceHistoryStore,
    ) -> None:

        self.store = store

    def recommend(
        self,
        *,
        task_type: str,
        baseline_tier: str,
    ) -> LearningRecommendation:

        baseline = baseline_tier.strip().lower()

        if baseline not in self.TIER_ORDER:
            raise ValueError(
                f"Unsupported baseline tier: {baseline_tier}"
            )

        candidates = self._candidates(
            task_type=task_type,
        )

        baseline_stats = self.store.get_stats(
            task_type=task_type,
            tier=baseline,
        )

        if (
            baseline_stats.attempts
            < self.MIN_ATTEMPTS
        ):
            return LearningRecommendation(
                task_type=task_type,
                baseline_tier=baseline,
                recommended_tier=baseline,
                learning_applied=False,
                reason=(
                    "Insufficient historical evidence for "
                    "the baseline tier, so AURA preserved "
                    "the analyzer recommendation."
                ),
                candidates=candidates,
            )

        if (
            baseline_stats.reliability_score
            >= self.POOR_RELIABILITY_THRESHOLD
        ):
            return LearningRecommendation(
                task_type=task_type,
                baseline_tier=baseline,
                recommended_tier=baseline,
                learning_applied=False,
                reason=(
                    "The baseline tier has acceptable "
                    "historical reliability, so no adaptive "
                    "upgrade was required."
                ),
                candidates=candidates,
            )

        baseline_index = self.TIER_ORDER.index(
            baseline
        )

        stronger_tiers = (
            self.TIER_ORDER[
                baseline_index + 1:
            ]
        )

        for tier in stronger_tiers:

            stats = self.store.get_stats(
                task_type=task_type,
                tier=tier,
            )

            if (
                stats.attempts
                >= self.MIN_ATTEMPTS
                and stats.reliability_score
                >= self.STRONG_RELIABILITY_THRESHOLD
            ):
                return LearningRecommendation(
                    task_type=task_type,
                    baseline_tier=baseline,
                    recommended_tier=tier,
                    learning_applied=True,
                    reason=(
                        f"Historical evidence shows the "
                        f"{baseline.upper()} tier has poor "
                        f"reliability for {task_type}, while "
                        f"{tier.upper()} has sufficient strong "
                        f"evidence. AURA proactively upgraded "
                        f"the starting tier."
                    ),
                    candidates=candidates,
                )

        return LearningRecommendation(
            task_type=task_type,
            baseline_tier=baseline,
            recommended_tier=baseline,
            learning_applied=False,
            reason=(
                "The baseline tier has poor historical "
                "reliability, but no stronger tier currently "
                "has enough reliable evidence to justify a "
                "proactive adaptive upgrade."
            ),
            candidates=candidates,
        )

    def _candidates(
        self,
        *,
        task_type: str,
    ) -> list[TierReliability]:

        result = []

        for tier in self.TIER_ORDER:

            stats = self.store.get_stats(
                task_type=task_type,
                tier=tier,
            )

            result.append(
                TierReliability(
                    tier=tier,
                    attempts=stats.attempts,
                    reliability_score=(
                        stats.reliability_score
                    ),
                )
            )

        return result
