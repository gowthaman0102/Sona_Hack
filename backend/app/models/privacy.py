from pydantic import BaseModel


class PrivacyAssessment(BaseModel):
    contains_sensitive_data: bool
    risk_level: str
    requires_local: bool
    categories: list[str]
    signals: list[str]


class PrivacyRoutingPolicy(BaseModel):
    privacy_enforced: bool
    execution_scope: str
    external_routing_allowed: bool
    selected_model_is_local: bool
    reason: str
