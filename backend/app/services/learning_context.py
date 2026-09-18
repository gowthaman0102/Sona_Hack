from app.services.adaptive_routing_policy import (
    AdaptiveRoutingPolicy,
)
from app.services.learning_outcome_recorder import (
    LearningOutcomeRecorder,
)
from app.services.performance_history_store import (
    PerformanceHistoryStore,
)


performance_history_store = (
    PerformanceHistoryStore()
)

learning_outcome_recorder = (
    LearningOutcomeRecorder(
        performance_history_store
    )
)

adaptive_routing_policy = (
    AdaptiveRoutingPolicy(
        performance_history_store
    )
)
