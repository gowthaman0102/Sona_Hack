import re

from app.models.confidence import ConfidenceEvaluation
from app.models.query_analysis import QueryAnalysis


class ConfidenceEvaluator:
    """
    Deterministic baseline response-confidence evaluator.

    AURA uses this after generation to decide whether a
    cheaper model's answer is trustworthy enough to return
    or should be escalated to a stronger model.
    """

    UNCERTAINTY_MARKERS = {
        "i am not sure",
        "i'm not sure",
        "i cannot determine",
        "i can't determine",
        "uncertain",
        "probably",
        "might be",
        "may be",
        "possibly",
    }

    FAILURE_MARKERS = {
        "i cannot answer",
        "i can't answer",
        "unable to answer",
        "unable to determine",
        "i don't know",
        "i do not know",
        "error occurred",
        "failed to",
    }

    def evaluate(
        self,
        response: str,
        analysis: QueryAnalysis,
    ) -> ConfidenceEvaluation:

        text = (
            response
            or ""
        ).strip()

        lower = text.lower()

        words = re.findall(
            r"\b[\w'-]+\b",
            text,
        )

        word_count = len(words)

        score = 1.0
        reasons: list[str] = []

        if not text:
            score = 0.0
            reasons.append(
                "empty_response"
            )

        if (
            "<think>" in lower
            or "</think>" in lower
        ):
            score -= 0.50
            reasons.append(
                "reasoning_leak_detected"
            )

        if any(
            marker in lower
            for marker in self.FAILURE_MARKERS
        ):
            score -= 0.45
            reasons.append(
                "failure_language_detected"
            )

        if any(
            marker in lower
            for marker in self.UNCERTAINTY_MARKERS
        ):
            score -= 0.20
            reasons.append(
                "uncertainty_language_detected"
            )

        if (
            analysis.task_type
            in {
                "explanation",
                "summarization",
                "coding",
            }
            and word_count < 12
        ):
            score -= 0.25
            reasons.append(
                "response_too_short_for_task"
            )

        if (
            analysis.task_type
            in {
                "analysis",
                "planning",
            }
            and word_count < 30
        ):
            score -= 0.35
            reasons.append(
                "insufficient_detail_for_complex_task"
            )

        if (
            analysis.reasoning_required
            and word_count < 20
        ):
            score -= 0.20
            reasons.append(
                "limited_reasoning_evidence"
            )

        score = round(
            max(
                0.0,
                min(score, 1.0),
            ),
            2,
        )

        if score >= 0.80:
            level = "high"

        elif score >= 0.55:
            level = "medium"

        else:
            level = "low"

        should_escalate = (
            score < 0.65
        )

        if not reasons:
            reasons.append(
                "no_quality_risk_detected"
            )

        return ConfidenceEvaluation(
            score=score,
            level=level,
            should_escalate=should_escalate,
            reasons=reasons,
            response_word_count=word_count,
        )
