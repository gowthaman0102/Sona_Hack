from app.models.analytics import (
    AttemptMetrics,
    MultiTaskAnalytics,
    RouteAnalytics,
)


class AnalyticsCalculator:
    """
    Deterministic resource accounting for AURA.

    normalized_compute_cost =
        model compute score × latency seconds

    This is a relative local-compute metric, not monetary spend.
    """

    def build_attempt(
        self,
        *,
        tier: str,
        model_name: str,
        compute_score: int,
        confidence_score: float,
        confidence_level: str,
        should_escalate: bool,
        prompt_tokens: int | None,
        output_tokens: int | None,
        latency_seconds: float | None,
        tokens_per_second: float | None,
    ) -> AttemptMetrics:

        prompt = prompt_tokens or 0
        output = output_tokens or 0
        latency = latency_seconds or 0.0

        normalized_compute_cost = round(
            compute_score * latency,
            3,
        )

        return AttemptMetrics(
            tier=tier,
            model_name=model_name,
            compute_score=compute_score,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            should_escalate=should_escalate,
            prompt_tokens=prompt,
            output_tokens=output,
            total_tokens=prompt + output,
            latency_seconds=round(
                latency,
                3,
            ),
            tokens_per_second=tokens_per_second,
            normalized_compute_cost=(
                normalized_compute_cost
            ),
        )

    def summarize(
        self,
        attempts: list[AttemptMetrics],
    ) -> RouteAnalytics:

        if not attempts:
            return RouteAnalytics(
                attempt_count=0,
                total_prompt_tokens=0,
                total_output_tokens=0,
                total_tokens=0,
                total_latency_seconds=0.0,
                normalized_compute_cost=0.0,
                final_attempt_compute_cost=0.0,
                escalation_overhead_compute=0.0,
                attempts=[],
            )

        total_prompt_tokens = sum(
            attempt.prompt_tokens
            for attempt in attempts
        )

        total_output_tokens = sum(
            attempt.output_tokens
            for attempt in attempts
        )

        total_latency_seconds = round(
            sum(
                attempt.latency_seconds
                for attempt in attempts
            ),
            3,
        )

        normalized_compute_cost = round(
            sum(
                attempt.normalized_compute_cost
                for attempt in attempts
            ),
            3,
        )

        final_attempt_compute_cost = (
            attempts[-1].normalized_compute_cost
        )

        escalation_overhead_compute = round(
            normalized_compute_cost
            - final_attempt_compute_cost,
            3,
        )

        return RouteAnalytics(
            attempt_count=len(attempts),
            total_prompt_tokens=(
                total_prompt_tokens
            ),
            total_output_tokens=(
                total_output_tokens
            ),
            total_tokens=(
                total_prompt_tokens
                + total_output_tokens
            ),
            total_latency_seconds=(
                total_latency_seconds
            ),
            normalized_compute_cost=(
                normalized_compute_cost
            ),
            final_attempt_compute_cost=(
                final_attempt_compute_cost
            ),
            escalation_overhead_compute=(
                escalation_overhead_compute
            ),
            attempts=attempts,
        )


    def summarize_tasks(
        self,
        task_analytics: list[RouteAnalytics],
    ) -> MultiTaskAnalytics:

        if not task_analytics:
            return MultiTaskAnalytics(
                task_count=0,
                total_attempt_count=0,
                total_prompt_tokens=0,
                total_output_tokens=0,
                total_tokens=0,
                total_latency_seconds=0.0,
                normalized_compute_cost=0.0,
                final_attempt_compute_cost=0.0,
                escalation_overhead_compute=0.0,
            )

        total_prompt_tokens = sum(
            item.total_prompt_tokens
            for item in task_analytics
        )

        total_output_tokens = sum(
            item.total_output_tokens
            for item in task_analytics
        )

        total_latency_seconds = round(
            sum(
                item.total_latency_seconds
                for item in task_analytics
            ),
            3,
        )

        normalized_compute_cost = round(
            sum(
                item.normalized_compute_cost
                for item in task_analytics
            ),
            3,
        )

        final_attempt_compute_cost = round(
            sum(
                item.final_attempt_compute_cost
                for item in task_analytics
            ),
            3,
        )

        escalation_overhead_compute = round(
            sum(
                item.escalation_overhead_compute
                for item in task_analytics
            ),
            3,
        )

        return MultiTaskAnalytics(
            task_count=len(task_analytics),
            total_attempt_count=sum(
                item.attempt_count
                for item in task_analytics
            ),
            total_prompt_tokens=(
                total_prompt_tokens
            ),
            total_output_tokens=(
                total_output_tokens
            ),
            total_tokens=(
                total_prompt_tokens
                + total_output_tokens
            ),
            total_latency_seconds=(
                total_latency_seconds
            ),
            normalized_compute_cost=(
                normalized_compute_cost
            ),
            final_attempt_compute_cost=(
                final_attempt_compute_cost
            ),
            escalation_overhead_compute=(
                escalation_overhead_compute
            ),
        )
