import re

from app.models.query_analysis import (
    QueryAnalysis,
    QueryFeatures,
)


class QueryAnalyzer:
    """
    Transparent deterministic query analyzer for AURA.

    Detects task category, extracts query features,
    calculates complexity, and recommends a model tier.
    """

    EXTRACTION_MARKERS = {
        "extract",
        "find the email",
        "find the date",
        "identify the name",
        "get the value",
    }

    TRANSFORMATION_MARKERS = {
        "format",
        "uppercase",
        "lowercase",
        "rewrite",
        "translate",
        "convert",
        "correct grammar",
    }

    CLASSIFICATION_MARKERS = {
        "classify",
        "categorize",
        "categorise",
        "sentiment",
        "label",
    }

    SUMMARIZATION_MARKERS = {
        "summarize",
        "summarise",
        "summary",
        "shorten",
        "condense",
    }

    EXPLANATION_MARKERS = {
        "explain",
        "describe",
        "what is",
        "define",
        "teach",
    }

    CODING_ACTION_MARKERS = {
        "debug",
        "fix",
        "implement",
        "write code",
        "create function",
        "refactor",
        "program",
    }

    ANALYSIS_MARKERS = {
        "analyze",
        "analyse",
        "evaluate",
        "root cause",
        "compare and recommend",
        "investigate",
        "diagnose",
        "trade-off",
        "tradeoff",
    }

    PLANNING_MARKERS = {
        "design",
        "architect",
        "strategy",
        "plan",
        "roadmap",
        "recommend",
        "optimize",
        "optimise",
    }

    REASONING_MARKERS = {
        "why",
        "how",
        "step by step",
        "root cause",
        "trade-off",
        "tradeoff",
        "pros and cons",
        "advantages and disadvantages",
        "compare and recommend",
        "justify",
        "reason",
        "prove",
    }

    CODE_MARKERS = {
        "python",
        "java",
        "javascript",
        "typescript",
        "sql",
        "api",
        "backend",
        "frontend",
        "code",
        "function",
        "class",
        "bug",
        "error",
        "exception",
        "database",
        "fastapi",
        "react",
    }

    ACTION_MARKERS = {
        "extract",
        "format",
        "classify",
        "translate",
        "rewrite",
        "summarize",
        "summarise",
        "explain",
        "describe",
        "compare",
        "write",
        "generate",
        "analyze",
        "analyse",
        "debug",
        "design",
        "architect",
        "evaluate",
        "optimize",
        "optimise",
        "reason",
        "prove",
        "solve",
        "recommend",
        "identify",
        "implement",
        "refactor",
        "plan",
    }

    BASE_SCORES = {
        "extraction": 1,
        "transformation": 1,
        "classification": 2,
        "summarization": 4,
        "explanation": 4,
        "coding": 5,
        "analysis": 7,
        "planning": 7,
        "general": 2,
    }

    def analyze(self, prompt: str) -> QueryAnalysis:
        text = prompt.strip().lower()

        task_type = self._detect_task_type(text)

        word_count = len(text.split())

        has_reasoning_markers = any(
            marker in text
            for marker in self.REASONING_MARKERS
        )

        has_code = any(
            marker in text
            for marker in self.CODE_MARKERS
        )

        has_multiple_requirements = (
            self._has_multiple_requirements(text)
        )

        score = self.BASE_SCORES[task_type]

        reasons = [
            f"{task_type} task baseline"
        ]

        if word_count > 40:
            score += 1
            reasons.append(
                "longer prompt"
            )

        if word_count > 100:
            score += 1
            reasons.append(
                "very long prompt"
            )

        if has_reasoning_markers:
            score += 1
            reasons.append(
                "reasoning language detected"
            )

        if (
            has_code
            and task_type not in {"coding"}
        ):
            score += 1
            reasons.append(
                "technical or coding content"
            )

        if has_multiple_requirements:
            score += 1
            reasons.append(
                "multiple requirements detected"
            )

        score = max(
            1,
            min(score, 10),
        )

        reasoning_required = (
            score >= 7
            or task_type in {
                "analysis",
                "planning",
            }
        )

        if score <= 3:
            tier = "low"

        elif score <= 6:
            tier = "medium"

        else:
            tier = "high"

        features = QueryFeatures(
            word_count=word_count,
            has_code=has_code,
            has_reasoning_markers=has_reasoning_markers,
            has_multiple_requirements=has_multiple_requirements,
        )

        return QueryAnalysis(
            task_type=task_type,
            complexity_score=score,
            reasoning_required=reasoning_required,
            recommended_tier=tier,
            explanation=", ".join(reasons),
            features=features,
        )

    def _detect_task_type(
        self,
        text: str,
    ) -> str:

        if self._contains_any(
            text,
            self.ANALYSIS_MARKERS,
        ):
            return "analysis"

        if self._contains_any(
            text,
            self.PLANNING_MARKERS,
        ):
            return "planning"

        if (
            self._contains_any(
                text,
                self.CODING_ACTION_MARKERS,
            )
            or (
                self._contains_any(
                    text,
                    self.CODE_MARKERS,
                )
                and (
                    "write" in text
                    or "create" in text
                    or "build" in text
                )
            )
        ):
            return "coding"

        if self._contains_any(
            text,
            self.SUMMARIZATION_MARKERS,
        ):
            return "summarization"

        if self._contains_any(
            text,
            self.EXPLANATION_MARKERS,
        ):
            return "explanation"

        if self._contains_any(
            text,
            self.CLASSIFICATION_MARKERS,
        ):
            return "classification"

        if self._contains_any(
            text,
            self.EXTRACTION_MARKERS,
        ):
            return "extraction"

        if self._contains_any(
            text,
            self.TRANSFORMATION_MARKERS,
        ):
            return "transformation"

        return "general"

    def _contains_any(
        self,
        text: str,
        markers: set[str],
    ) -> bool:

        return any(
            marker in text
            for marker in markers
        )

    def _has_multiple_requirements(
        self,
        text: str,
    ) -> bool:

        detected_actions = {
            action
            for action in self.ACTION_MARKERS
            if re.search(
                rf"\b{re.escape(action)}\b",
                text,
            )
        }

        numbered_items = len(
            re.findall(
                r"\b\d+[\.\)]",
                text,
            )
        )

        clause_markers = (
            text.count(";")
            + text.count(" then ")
            + text.count(" also ")
        )

        return (
            len(detected_actions) >= 2
            or numbered_items >= 2
            or clause_markers >= 2
        )
