from app.services.task_decomposer import TaskDecomposer


decomposer = TaskDecomposer()


def test_single_task_is_not_decomposed():
    result = decomposer.decompose(
        "Explain database normalization."
    )

    assert result.is_multi_task is False
    assert result.task_count == 1
    assert result.tasks[0].text == (
        "Explain database normalization."
    )


def test_comma_separated_actions_are_decomposed():
    result = decomposer.decompose(
        (
            "Extract the email address, "
            "summarize the paragraph, "
            "and analyze the security risk."
        )
    )

    assert result.is_multi_task is True
    assert result.task_count == 3


def test_and_before_action_is_decomposed():
    result = decomposer.decompose(
        (
            "Explain normalization and "
            "compare it with denormalization."
        )
    )

    assert result.is_multi_task is True
    assert result.task_count == 2


def test_normal_and_phrase_is_not_split():
    result = decomposer.decompose(
        (
            "Explain the advantages and disadvantages "
            "of database normalization."
        )
    )

    assert result.is_multi_task is False
    assert result.task_count == 1


def test_numbered_tasks_are_decomposed():
    result = decomposer.decompose(
        (
            "1. Extract the email address\n"
            "2. Summarize the paragraph\n"
            "3. Analyze the security risk"
        )
    )

    assert result.is_multi_task is True
    assert result.task_count == 3


def test_semicolon_tasks_are_decomposed():
    result = decomposer.decompose(
        (
            "Extract the date; "
            "summarize the text; "
            "analyze the result"
        )
    )

    assert result.is_multi_task is True
    assert result.task_count == 3


def test_each_task_gets_independent_analysis():
    result = decomposer.decompose(
        (
            "Extract the email address, "
            "summarize the paragraph, "
            "and analyze the security risk."
        )
    )

    assert (
        result.tasks[0].analysis.task_type
        == "extraction"
    )

    assert (
        result.tasks[0].analysis.recommended_tier
        == "low"
    )

    assert (
        result.tasks[1].analysis.task_type
        == "summarization"
    )

    assert (
        result.tasks[1].analysis.recommended_tier
        == "medium"
    )

    assert (
        result.tasks[2].analysis.task_type
        == "analysis"
    )

    assert (
        result.tasks[2].analysis.recommended_tier
        == "high"
    )


def test_duplicate_tasks_removed():
    result = decomposer.decompose(
        (
            "Summarize the paragraph; "
            "Summarize the paragraph"
        )
    )

    assert result.is_multi_task is False
    assert result.task_count == 1


def test_empty_prompt_returns_no_tasks():
    result = decomposer.decompose(
        ""
    )

    assert result.is_multi_task is False
    assert result.task_count == 0
    assert result.tasks == []
