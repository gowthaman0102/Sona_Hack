from app.services.query_analyzer import QueryAnalyzer


analyzer = QueryAnalyzer()


def test_extraction_task():
    result = analyzer.analyze(
        "Extract the email address from this text."
    )

    assert result.task_type == "extraction"
    assert result.recommended_tier == "low"


def test_transformation_task():
    result = analyzer.analyze(
        "Convert this sentence to uppercase."
    )

    assert result.task_type == "transformation"
    assert result.recommended_tier == "low"


def test_classification_task():
    result = analyzer.analyze(
        "Classify this review as positive or negative."
    )

    assert result.task_type == "classification"
    assert result.recommended_tier == "low"


def test_summarization_task():
    result = analyzer.analyze(
        "Summarize this paragraph in five sentences."
    )

    assert result.task_type == "summarization"
    assert result.recommended_tier == "medium"


def test_explanation_task():
    result = analyzer.analyze(
        "Explain database normalization with an example."
    )

    assert result.task_type == "explanation"
    assert result.recommended_tier == "medium"


def test_coding_task():
    result = analyzer.analyze(
        "Write Python code for binary search."
    )

    assert result.task_type == "coding"
    assert result.recommended_tier == "medium"
    assert result.features.has_code is True


def test_analysis_task():
    result = analyzer.analyze(
        (
            "Analyze this Python API and identify "
            "the root cause of high latency."
        )
    )

    assert result.task_type == "analysis"
    assert result.recommended_tier == "high"
    assert result.reasoning_required is True


def test_planning_task():
    result = analyzer.analyze(
        (
            "Design a scalable backend architecture "
            "for an e-commerce application."
        )
    )

    assert result.task_type == "planning"
    assert result.recommended_tier == "high"


def test_multiple_requirements():
    result = analyzer.analyze(
        (
            "Analyze this API, identify the root cause, "
            "compare two solutions, and recommend one."
        )
    )

    assert (
        result.features.has_multiple_requirements
        is True
    )


def test_single_requirement():
    result = analyzer.analyze(
        "Explain normalization."
    )

    assert (
        result.features.has_multiple_requirements
        is False
    )


def test_general_query():
    result = analyzer.analyze(
        "Hello, how are you?"
    )

    assert result.task_type == "general"
    assert result.recommended_tier == "low"


def test_score_is_bounded():
    result = analyzer.analyze(
        (
            "Analyze and debug this Python backend API, "
            "identify the root cause, compare solutions, "
            "recommend improvements, and justify the design."
        )
    )

    assert (
        1
        <= result.complexity_score
        <= 10
    )
