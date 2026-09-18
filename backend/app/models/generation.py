from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        description="Prompt to send to the selected local LLM.",
    )

    model: str = Field(
        default="qwen2.5:7b",
        description="Ollama model name.",
    )

    system_prompt: str | None = Field(
        default=None,
        description="Optional system instruction.",
    )

    think: bool = Field(
        default=False,
        description="Enable supported model reasoning/thinking mode.",
    )


class GenerateResponse(BaseModel):
    model: str
    response: str
    done: bool
    total_duration: int | None = None
    load_duration: int | None = None
    prompt_eval_count: int | None = None
    eval_count: int | None = None
    eval_duration: int | None = None
