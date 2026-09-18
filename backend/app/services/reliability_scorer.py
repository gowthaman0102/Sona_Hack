from app.models.learning import PerformanceStats


class ReliabilityScorer:
    """
    Deterministic Phase 10 reliability calculations.

    Reliability uses Laplace smoothing:

        (successes + 1) / (attempts + 2)

    This prevents very small samples from being
    treated as definitive historical evidence.
    """

    def calculate_reliability(
        self,
        *,
        attempts: int,
        successes: int,
    ) -> float:

        if attempts < 0:
            raise ValueError(
                "attempts cannot be negative"
            )

        if successes < 0:
            raise ValueError(
                "successes cannot be negative"
            )

        if successes > attempts:
            raise ValueError(
                "successes cannot exceed attempts"
            )

        return round(
            (successes + 1)
            / (attempts + 2),
            3,
        )

    def build_stats(
        self,
        *,
        task_type: str,
        tier: str,
        attempts: int,
        successes: int,
        total_confidence: float,
        total_latency_seconds: float,
        total_normalized_compute_cost: float,
    ) -> PerformanceStats:

        if attempts == 0:

            return PerformanceStats(
                task_type=task_type,
                tier=tier,
                attempts=0,
                successes=0,
                failures=0,
                average_confidence=0.0,
                average_latency_seconds=0.0,
                average_normalized_compute_cost=0.0,
                reliability_score=0.5,
            )

        failures = (
            attempts
            - successes
        )

        return PerformanceStats(
            task_type=task_type,
            tier=tier,
            attempts=attempts,
            successes=successes,
            failures=failures,
            average_confidence=round(
                total_confidence
                / attempts,
                3,
            ),
            average_latency_seconds=round(
                total_latency_seconds
                / attempts,
                3,
            ),
            average_normalized_compute_cost=round(
                total_normalized_compute_cost
                / attempts,
                3,
            ),
            reliability_score=(
                self.calculate_reliability(
                    attempts=attempts,
                    successes=successes,
                )
            ),
        )
