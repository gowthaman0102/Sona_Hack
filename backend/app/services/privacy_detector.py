import re

from app.models.privacy import PrivacyAssessment


class PrivacyDetector:
    """
    Deterministic sensitive-data detector for AURA.

    The detector does not attempt to prove identity or
    correctness of values. It identifies patterns that
    should cause AURA to apply privacy-aware routing.
    """

    EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    PHONE_PATTERN = re.compile(
        r"(?<!\d)"
        r"(?:\+?91[-\s]?)?"
        r"[6-9]\d{9}"
        r"(?!\d)"
    )

    AADHAAR_PATTERN = re.compile(
        r"(?<!\d)"
        r"\d{4}[\s-]?\d{4}[\s-]?\d{4}"
        r"(?!\d)"
    )

    AADHAAR_CONTEXT_PATTERN = re.compile(
        r"\b(?:aadhaar|aadhar|uidai|uid)\b",
        re.IGNORECASE,
    )

    CARD_PATTERN = re.compile(
        r"(?<!\d)"
        r"(?:\d[ -]*?){13,19}"
        r"(?!\d)"
    )

    SECRET_PATTERNS = [
        re.compile(
            r"\bpassword\s*[:=]\s*\S+",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bpin\s*[:=]\s*\d{4,6}\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\botp\s*[:=]\s*\d{4,8}\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bsecret\s*[:=]\s*\S+",
            re.IGNORECASE,
        ),
    ]

    API_KEY_PATTERNS = [
        re.compile(
            r"\bapi[_ -]?key\s*[:=]\s*\S+",
            re.IGNORECASE,
        ),
        re.compile(
            r"\baccess[_ -]?token\s*[:=]\s*\S+",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bbearer\s+[A-Za-z0-9._\-]+",
            re.IGNORECASE,
        ),
    ]

    MEDICAL_TERMS = {
        "diagnosis",
        "medical record",
        "patient record",
        "blood report",
        "prescription",
        "medication",
        "disease",
        "hospital record",
        "health record",
    }

    FINANCIAL_TERMS = {
        "bank account",
        "account number",
        "ifsc",
        "credit card",
        "debit card",
        "cvv",
        "bank statement",
        "upi pin",
    }

    HIGH_RISK = {
        "aadhaar",
        "payment_card",
        "password_or_secret",
        "api_key_or_token",
    }

    def assess(
        self,
        text: str,
    ) -> PrivacyAssessment:

        content = (
            text
            or ""
        ).strip()

        lower = content.lower()

        categories: list[str] = []
        signals: list[str] = []

        if self.EMAIL_PATTERN.search(
            content
        ):
            categories.append(
                "email"
            )
            signals.append(
                "email_pattern_detected"
            )

        if self.PHONE_PATTERN.search(
            content
        ):
            categories.append(
                "phone"
            )
            signals.append(
                "phone_pattern_detected"
            )

        if self._contains_aadhaar(
            content
        ):
            categories.append(
                "aadhaar"
            )
            signals.append(
                "aadhaar_pattern_detected"
            )

        if self._contains_payment_card(
            content
        ):
            categories.append(
                "payment_card"
            )
            signals.append(
                "payment_card_pattern_detected"
            )

        if any(
            pattern.search(content)
            for pattern in self.SECRET_PATTERNS
        ):
            categories.append(
                "password_or_secret"
            )
            signals.append(
                "credential_pattern_detected"
            )

        if any(
            pattern.search(content)
            for pattern in self.API_KEY_PATTERNS
        ):
            categories.append(
                "api_key_or_token"
            )
            signals.append(
                "api_credential_pattern_detected"
            )

        if any(
            term in lower
            for term in self.MEDICAL_TERMS
        ):
            categories.append(
                "medical"
            )
            signals.append(
                "medical_context_detected"
            )

        if any(
            term in lower
            for term in self.FINANCIAL_TERMS
        ):
            categories.append(
                "financial"
            )
            signals.append(
                "financial_context_detected"
            )

        categories = list(
            dict.fromkeys(
                categories
            )
        )

        signals = list(
            dict.fromkeys(
                signals
            )
        )

        contains_sensitive_data = bool(
            categories
        )

        requires_local = (
            contains_sensitive_data
        )

        if any(
            category in self.HIGH_RISK
            for category in categories
        ):
            risk_level = "high"

        elif categories:
            risk_level = "medium"

        else:
            risk_level = "none"

        if not signals:
            signals.append(
                "no_sensitive_data_detected"
            )

        return PrivacyAssessment(
            contains_sensitive_data=(
                contains_sensitive_data
            ),
            risk_level=risk_level,
            requires_local=(
                requires_local
            ),
            categories=categories,
            signals=signals,
        )

    def _contains_aadhaar(
        self,
        content: str,
    ) -> bool:
        """
        Detect Aadhaar-like values only when the text also
        contains Aadhaar-specific context.

        This avoids classifying arbitrary 12-digit sequences
        or the first 12 digits of a payment card as Aadhaar.
        """

        if not self.AADHAAR_CONTEXT_PATTERN.search(
            content
        ):
            return False

        return bool(
            self.AADHAAR_PATTERN.search(
                content
            )
        )

    def _contains_payment_card(
        self,
        content: str,
    ) -> bool:

        for match in self.CARD_PATTERN.finditer(
            content
        ):

            candidate = re.sub(
                r"\D",
                "",
                match.group(),
            )

            if (
                13 <= len(candidate) <= 19
                and self._luhn_valid(
                    candidate
                )
            ):
                return True

        return False

    def _luhn_valid(
        self,
        number: str,
    ) -> bool:

        digits = [
            int(char)
            for char in number
        ]

        checksum = 0
        parity = len(digits) % 2

        for index, digit in enumerate(
            digits
        ):

            value = digit

            if index % 2 == parity:
                value *= 2

                if value > 9:
                    value -= 9

            checksum += value

        return (
            checksum % 10
            == 0
        )
