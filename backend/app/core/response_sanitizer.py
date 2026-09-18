import re


_THINK_BLOCK_PATTERN = re.compile(
    r"<think>.*?</think>",
    flags=re.IGNORECASE | re.DOTALL,
)

_ORPHAN_THINK_END_PATTERN = re.compile(
    r".*?</think>",
    flags=re.IGNORECASE | re.DOTALL,
)


def sanitize_model_response(text: str) -> str:
    """
    Removes model reasoning blocks that should never be exposed
    in AURA's final user-facing response.
    """

    if not text:
        return ""

    cleaned = _THINK_BLOCK_PATTERN.sub("", text)

    # Some model/template combinations may emit reasoning text
    # followed only by a closing </think> tag.
    if "</think>" in cleaned.lower():
        cleaned = _ORPHAN_THINK_END_PATTERN.sub("", cleaned)

    return cleaned.strip()
