import ast
import operator
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

    _ARITHMETIC_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    def evaluate(
        self,
        response: str,
        analysis: QueryAnalysis,
        prompt: str | None = None,
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

        arithmetic_check = (
            self._check_simple_arithmetic(
                prompt=prompt,
                response=text,
            )
        )

        if arithmetic_check is False:
            score = 0.0
            reasons.append(
                "deterministic_arithmetic_mismatch"
            )

        elif arithmetic_check is True:
            reasons.append(
                "deterministic_arithmetic_match"
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

    def _check_simple_arithmetic(
        self,
        prompt: str | None,
        response: str,
    ) -> bool | None:
        if not prompt:
            return None

        expression = self._extract_arithmetic_expression(
            prompt
        )

        if expression is None:
            return None

        expected = self._safe_eval_arithmetic(
            expression
        )

        if expected is None:
            return None

        actual = self._extract_numeric_response(
            response
        )

        if actual is None:
            return False

        return abs(
            actual - expected
        ) < 1e-9

    def _extract_arithmetic_expression(
        self,
        prompt: str,
    ) -> str | None:
        stripped = prompt.strip()

        direct = re.fullmatch(
            r"[0-9\s+\-*/().%]+",
            stripped,
        )

        if direct:
            return stripped

        match = re.search(
            r"(?:what\s+is|calculate)\s+"
            r"([0-9\s+\-*/().%]+)"
            r"\??",
            stripped,
            flags=re.IGNORECASE,
        )

        if match:
            expression = (
                match.group(1)
                .strip()
            )

            if expression:
                return expression

        return None

    def _extract_numeric_response(
        self,
        response: str,
    ) -> float | None:
        stripped = response.strip()

        match = re.fullmatch(
            r"[-+]?\d+(?:\.\d+)?",
            stripped,
        )

        if not match:
            return None

        return float(
            stripped
        )

    def _safe_eval_arithmetic(
        self,
        expression: str,
    ) -> float | None:
        try:
            tree = ast.parse(
                expression,
                mode="eval",
            )

            value = self._eval_node(
                tree.body
            )

            return float(
                value
            )

        except (
            SyntaxError,
            TypeError,
            ValueError,
            ZeroDivisionError,
            OverflowError,
        ):
            return None

    def _eval_node(
        self,
        node,
    ):
        if isinstance(
            node,
            ast.Constant,
        ):
            if (
                isinstance(
                    node.value,
                    (int, float),
                )
                and not isinstance(
                    node.value,
                    bool,
                )
            ):
                return node.value

            raise ValueError(
                "Unsupported constant."
            )

        if isinstance(
            node,
            ast.UnaryOp,
        ):
            operator_fn = (
                self._ARITHMETIC_OPERATORS.get(
                    type(node.op)
                )
            )

            if operator_fn is None:
                raise ValueError(
                    "Unsupported unary operator."
                )

            return operator_fn(
                self._eval_node(
                    node.operand
                )
            )

        if isinstance(
            node,
            ast.BinOp,
        ):
            operator_fn = (
                self._ARITHMETIC_OPERATORS.get(
                    type(node.op)
                )
            )

            if operator_fn is None:
                raise ValueError(
                    "Unsupported binary operator."
                )

            left = self._eval_node(
                node.left
            )

            right = self._eval_node(
                node.right
            )

            if (
                isinstance(
                    node.op,
                    ast.Pow,
                )
                and abs(right) > 10
            ):
                raise ValueError(
                    "Exponent too large."
                )

            result = operator_fn(
                left,
                right,
            )

            if (
                isinstance(
                    result,
                    (int, float),
                )
                and abs(result) > 1_000_000_000
            ):
                raise ValueError(
                    "Arithmetic result too large."
                )

            return result

        raise ValueError(
            "Unsupported arithmetic expression."
        )
