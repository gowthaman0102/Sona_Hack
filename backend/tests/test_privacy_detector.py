from app.services.privacy_detector import PrivacyDetector


detector = PrivacyDetector()


def test_normal_prompt_has_no_privacy_risk():

    result = detector.assess(
        "Explain database normalization."
    )

    assert (
        result.contains_sensitive_data
        is False
    )

    assert result.risk_level == "none"
    assert result.requires_local is False
    assert result.categories == []


def test_email_is_detected():

    result = detector.assess(
        "My email is alice@example.com."
    )

    assert (
        result.contains_sensitive_data
        is True
    )

    assert "email" in result.categories
    assert result.requires_local is True
    assert result.risk_level == "medium"


def test_indian_phone_is_detected():

    result = detector.assess(
        "Call me at +91 9876543210."
    )

    assert "phone" in result.categories
    assert result.requires_local is True


def test_aadhaar_is_high_risk():

    result = detector.assess(
        "Aadhaar number: 1234 5678 9012"
    )

    assert "aadhaar" in result.categories
    assert result.risk_level == "high"
    assert result.requires_local is True


def test_valid_payment_card_is_detected():

    result = detector.assess(
        "Card number: 4111 1111 1111 1111"
    )

    assert (
        "payment_card"
        in result.categories
    )

    assert result.risk_level == "high"


def test_random_long_number_is_not_payment_card():

    result = detector.assess(
        "Reference number: 1234567890123456"
    )

    assert (
        "payment_card"
        not in result.categories
    )


def test_password_is_high_risk():

    result = detector.assess(
        "password=MySecret123"
    )

    assert (
        "password_or_secret"
        in result.categories
    )

    assert result.risk_level == "high"


def test_api_key_is_high_risk():

    result = detector.assess(
        "api_key=abc123-super-secret"
    )

    assert (
        "api_key_or_token"
        in result.categories
    )

    assert result.risk_level == "high"


def test_medical_context_is_detected():

    result = detector.assess(
        (
            "Summarize this patient record "
            "and medication history."
        )
    )

    assert "medical" in result.categories
    assert result.risk_level == "medium"


def test_financial_context_is_detected():

    result = detector.assess(
        (
            "Review this bank account "
            "statement."
        )
    )

    assert "financial" in result.categories
    assert result.requires_local is True


def test_multiple_categories_are_preserved():

    result = detector.assess(
        (
            "Email alice@example.com, "
            "phone +91 9876543210, "
            "password=Secret123"
        )
    )

    assert "email" in result.categories
    assert "phone" in result.categories

    assert (
        "password_or_secret"
        in result.categories
    )

    assert result.risk_level == "high"
    assert result.requires_local is True


def test_payment_card_is_not_misclassified_as_aadhaar():

    result = detector.assess(
        "Use card 4111 1111 1111 1111."
    )

    assert (
        "payment_card"
        in result.categories
    )

    assert (
        "aadhaar"
        not in result.categories
    )


def test_unlabelled_twelve_digit_number_is_not_aadhaar():

    result = detector.assess(
        "Reference number: 1234 5678 9012"
    )

    assert (
        "aadhaar"
        not in result.categories
    )


def test_aadhar_alternate_spelling_is_detected():

    result = detector.assess(
        "Aadhar number: 1234-5678-9012"
    )

    assert (
        "aadhaar"
        in result.categories
    )

    assert result.requires_local is True
