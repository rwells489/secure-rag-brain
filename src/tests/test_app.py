import os
import re
import sys

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Test the PII detection patterns directly (copied from app.py for isolation)
PII_PATTERNS = {
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "AWS Access Key": r"\b(AKIA|ASCA|ASIA)[A-Z0-9]{16}\b",
    "Credit Card": r"\b(?:\d[ -]*?){13,16}\b",
    "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "Phone (US)": r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "API Key": r"\b(sk-|pk-|rk-)[A-Za-z0-9]{32,}\b",
}


def scan_for_pii(text: str):
    """Test version of PII scanner"""
    detected_types = []
    matches = {}
    for pii_type, pattern in PII_PATTERNS.items():
        found = re.findall(pattern, text)
        if found:
            detected_types.append(pii_type)
            matches[pii_type] = found[:3]
    has_pii = len(detected_types) > 0
    status = "quarantined" if has_pii else "approved"
    return has_pii, detected_types, matches, status


class TestPIIDetection:
    """Test PII detection patterns"""

    def test_ssn_detection(self):
        text = "My SSN is 123-45-6789"
        has_pii, types, matches, status = scan_for_pii(text)
        assert has_pii is True
        assert "SSN" in types
        assert status == "quarantined"

    def test_aws_key_detection(self):
        text = "AKIAIOSFODNN7EXAMPLE is my key"
        has_pii, types, matches, status = scan_for_pii(text)
        assert has_pii is True
        assert "AWS Access Key" in types
        assert status == "quarantined"

    def test_credit_card_detection(self):
        text = "Card: 4111 1111 1111 1111"
        has_pii, types, matches, status = scan_for_pii(text)
        assert has_pii is True
        assert "Credit Card" in types
        assert status == "quarantined"

    def test_email_detection(self):
        text = "Contact john.doe@company.com for info"
        has_pii, types, matches, status = scan_for_pii(text)
        assert has_pii is True
        assert "Email" in types
        assert status == "quarantined"

    def test_phone_detection(self):
        text = "Call 555-123-4567 or (555) 123-4567"
        has_pii, types, matches, status = scan_for_pii(text)
        assert has_pii is True
        assert "Phone (US)" in types
        assert status == "quarantined"

    def test_api_key_detection(self):
        text = "sk-1234567890abcdef1234567890abcdef"
        has_pii, types, matches, status = scan_for_pii(text)
        assert has_pii is True
        assert "API Key" in types
        assert status == "quarantined"

    def test_clean_text_approved(self):
        text = "This is a clean document about project management."
        has_pii, types, matches, status = scan_for_pii(text)
        assert has_pii is False
        assert types == []
        assert status == "approved"

    def test_multiple_pii_types(self):
        text = "John at john@test.com has SSN 111-22-3333"
        has_pii, types, matches, status = scan_for_pii(text)
        assert has_pii is True
        assert len(types) >= 2
        assert status == "quarantined"


class TestClassificationLogic:
    """Test document classification logic"""

    def test_quarantine_threshold(self):
        """Any PII triggers quarantine"""
        has_pii, types, matches, status = scan_for_pii("Email: test@test.com")
        assert status == "quarantined"
        assert len(types) == 1

    def test_no_pii_approved(self):
        """Clean text gets approved"""
        has_pii, types, matches, status = scan_for_pii("Project update: all systems nominal")
        assert status == "approved"
        assert types == []


class TestEdgeCases:
    """Test edge cases"""

    def test_empty_string(self):
        has_pii, types, matches, status = scan_for_pii("")
        assert status == "approved"

    def test_whitespace_only(self):
        has_pii, types, matches, status = scan_for_pii("   \n\t  ")
        assert status == "approved"

    def test_special_characters(self):
        text = "Symbols: !@#$%^&*()_+-=[]{}|;':\",./<>?"
        has_pii, types, matches, status = scan_for_pii(text)
        assert status == "approved"

    def test_case_insensitive_email(self):
        text = "EMAIL@EXAMPLE.COM and User@Domain.ORG"
        has_pii, types, matches, status = scan_for_pii(text)
        assert has_pii is True
        assert "Email" in types
        assert len(matches.get("Email", [])) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
