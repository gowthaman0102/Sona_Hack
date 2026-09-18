from app.core.response_sanitizer import sanitize_model_response


def test_clean_response_remains_unchanged():
    text = "This is the final answer."

    assert sanitize_model_response(text) == text


def test_complete_think_block_removed():
    text = (
        "<think>"
        "This is private reasoning."
        "</think>"
        "Final answer."
    )

    assert sanitize_model_response(text) == "Final answer."


def test_orphan_closing_think_block_removed():
    text = (
        "Private reasoning that leaked."
        "</think>"
        "Visible final answer."
    )

    assert (
        sanitize_model_response(text)
        == "Visible final answer."
    )


def test_empty_response():
    assert sanitize_model_response("") == ""
