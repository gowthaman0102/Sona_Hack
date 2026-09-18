from app.models.analytics import (
    RouteAnalytics,
)
from app.models.learning import (
    LearningOutcome,
    PerformanceStats,
)
from app.services.performance_history_store import (
    PerformanceHistoryStore,
)


class LearningOutcomeRecorder:
    """
    Converts AURA generation-attempt analytics into
    persistent learning outcomes.

    Success means the attempt satisfied AURA's
    confidence threshold and did not request escalation.

    Prompts and model responses are never persisted.
    """

    def __init__(
        self,
        store: PerformanceHistoryStore,
    ) -> None:

        self.store = store

    def record_route(
        self,
        *,
        task_type: str,
        analytics: RouteAnalytics,
    ) -> list[PerformanceStats]:

        recorded = []

        for attempt in analytics.attempts:

            outcome = LearningOutcome(
                task_type=task_type,
                tier=attempt.tier,
                model_name=attempt.model_name,
                success=(
                    not attempt.should_escalate
                ),
                confidence_score=(
                    attempt.confidence_score
                ),
                latency_seconds=(
                    attempt.latency_seconds
                ),
                normalized_compute_cost=(
                    attempt.normalized_compute_cost
                ),
            )

            recorded.append(
                self.store.record(
                    outcome
                )
            )

        return recorded

    def record_tasks(
        self,
        tasks,
    ) -> list[PerformanceStats]:

        recorded = []

        for task in tasks:

            recorded.extend(
                self.record_route(
                    task_type=task.task_type,
                    analytics=task.analytics,
                )
            )

        return recorded
