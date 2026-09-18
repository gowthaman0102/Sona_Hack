from unittest.mock import patch

import pytest

from app.services.intelligent_router import IntelligentRouter
from app.services.privacy_detector import PrivacyDetector
from app.services.privacy_routing_policy import (
    PrivacyRoutingPolicyService,
)


def generation(
    response: str = "alice@example.com",
):
    return {
        "tier": "test",
        "model_name": "mock",
        "display_name": "mock",
        "compute_score": 1,
        "thinking_enabled": False,
        "response": response,
        "prompt_tokens": 10,
        "output_tokens": 5,
        "latency_seconds": 1.0,
        "tokens_per_second": 5.0,
    }


def test_normal_prompt_uses_standard_privacy_policy():

    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=generation(
            "Database normalization reduces duplication."
        ),
    ):

        result = router.route(
            "Explain database normalization."
        )

    assert (
        result.privacy.contains_sensitive_data
        is False
    )

    assert (
        result.privacy_policy.privacy_enforced
        is False
    )

    assert (
        result.privacy_policy.execution_scope
        == "standard"
    )

    assert (
        result.privacy_policy.external_routing_allowed
        is True
    )


def test_sensitive_email_enforces_local_only():

    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=generation(
            "alice@example.com"
        ),
    ):

        result = router.route(
            (
                "Extract the email from "
                "alice@example.com"
            )
        )

    assert result.privacy.requires_local is True

    assert (
        "email"
        in result.privacy.categories
    )

    assert (
        result.privacy_policy.privacy_enforced
        is True
    )

    assert (
        result.privacy_policy.execution_scope
        == "local_only"
    )

    assert (
        result.privacy_policy.external_routing_allowed
        is False
    )

    assert (
        result.privacy_policy.selected_model_is_local
        is True
    )


def test_high_risk_secret_enforces_local_only():

    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=generation(
            "Credential received."
        ),
    ):

        result = router.route(
            "password=Secret123"
        )

    assert result.privacy.risk_level == "high"

    assert (
        result.privacy_policy.execution_scope
        == "local_only"
    )


def test_selected_local_models_are_approved():

    service = PrivacyRoutingPolicyService()

    assert "qwen3:1.7b" in service.local_models
    assert "qwen3:4b" in service.local_models
    assert "qwen3:8b" in service.local_models


def test_unknown_model_is_blocked_by_local_policy():

    service = PrivacyRoutingPolicyService()

    with pytest.raises(
        ValueError,
        match="not in AURA's approved local model registry",
    ):
        service.assert_local_model(
            "cloud-provider-model"
        )


def test_sensitive_assessment_blocks_external_model():

    detector = PrivacyDetector()

    assessment = detector.assess(
        "My Aadhaar number is 1234 5678 9012."
    )

    service = PrivacyRoutingPolicyService()

    with pytest.raises(
        ValueError,
        match="sensitive data requires an approved local model",
    ):

        service.evaluate(
            assessment=assessment,
            selected_model="external-model",
        )


def test_manual_high_override_remains_local_for_sensitive_prompt():

    router = IntelligentRouter()

    with patch.object(
        router.models,
        "generate_for_tier",
        return_value=generation(
            "alice@example.com"
        ),
    ):

        result = router.route(
            (
                "Extract the email from "
                "alice@example.com"
            ),
            override_tier="high",
        )

    assert (
        result.routing.selected_tier
        == "high"
    )

    assert (
        result.routing.selected_model
        == "qwen3:8b"
    )

    assert (
        result.privacy_policy.privacy_enforced
        is True
    )

    assert (
        result.privacy_policy.selected_model_is_local
        is True
    )
