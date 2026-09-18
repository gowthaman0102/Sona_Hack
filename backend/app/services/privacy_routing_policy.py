from app.core.model_registry import (
    ModelTier,
    get_model_by_tier,
)
from app.models.privacy import (
    PrivacyAssessment,
    PrivacyRoutingPolicy,
)


class PrivacyRoutingPolicyService:
    """
    Enforces privacy-aware execution constraints.

    Current AURA deployment uses Ollama-hosted local models.
    Sensitive prompts are explicitly restricted to the
    approved local model registry.
    """

    def __init__(self) -> None:

        self.local_models = {
            get_model_by_tier(
                ModelTier.LOW
            ).model_name,
            get_model_by_tier(
                ModelTier.MEDIUM
            ).model_name,
            get_model_by_tier(
                ModelTier.HIGH
            ).model_name,
        }

    def evaluate(
        self,
        assessment: PrivacyAssessment,
        selected_model: str,
    ) -> PrivacyRoutingPolicy:

        selected_model_is_local = (
            selected_model
            in self.local_models
        )

        if assessment.requires_local:

            if not selected_model_is_local:
                raise ValueError(
                    "Privacy policy blocked routing: "
                    "sensitive data requires an approved "
                    "local model."
                )

            categories = (
                ", ".join(
                    assessment.categories
                )
                if assessment.categories
                else "sensitive data"
            )

            return PrivacyRoutingPolicy(
                privacy_enforced=True,
                execution_scope="local_only",
                external_routing_allowed=False,
                selected_model_is_local=True,
                reason=(
                    "Sensitive data was detected "
                    f"({categories}). AURA therefore "
                    "restricted execution to an approved "
                    "local model."
                ),
            )

        return PrivacyRoutingPolicy(
            privacy_enforced=False,
            execution_scope="standard",
            external_routing_allowed=True,
            selected_model_is_local=(
                selected_model_is_local
            ),
            reason=(
                "No sensitive data requiring local-only "
                "execution was detected."
            ),
        )

    def assert_local_model(
        self,
        model_name: str,
    ) -> None:

        if (
            model_name
            not in self.local_models
        ):
            raise ValueError(
                f"Model '{model_name}' is not in "
                "AURA's approved local model registry."
            )
