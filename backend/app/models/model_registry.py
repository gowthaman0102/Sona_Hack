from pydantic import BaseModel


class RegisteredModelResponse(BaseModel):
    tier: str
    model_name: str
    display_name: str
    parameter_size: str
    compute_score: int
    expected_speed: str
    description: str
    installed: bool


class ModelRegistryResponse(BaseModel):
    count: int
    models: list[RegisteredModelResponse]
