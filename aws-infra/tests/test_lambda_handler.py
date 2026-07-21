import json
import os
import sys
from unittest.mock import Mock, patch

# Add aws-infra to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lambda_handler import lambda_handler, scan_for_pii, update_document_classification


class TestScanForPII:
    """Test PII detection patterns"""

    def test_ssn_detection(self):
        text = "My SSN is 123-45-6789"
        has_pii, types, matches = scan_for_pii(text)
        assert has_pii is True
        assert "ssn" in types
        assert "123-45-6789" in matches["ssn"]

    def test_aws_access_key_detection(self):
        text = "AKIAIOSFODNN7EXAMPLE is my key"
        has_pii, types, matches = scan_for_pii(text)
        assert has_pii is True
        assert "aws_access_key" in types

    def test_credit_card_detection(self):
        text = "Card: 4111 1111 1111 1111"
        has_pii, types, matches = scan_for_pii(text)
        assert has_pii is True
        assert "credit_card" in types

    def test_email_detection(self):
        text = "Contact john.doe@company.com"
        has_pii, types, matches = scan_for_pii(text)
        assert has_pii is True
        assert "email" in types

    def test_phone_us_detection(self):
        text = "Call 555-123-4567"
        has_pii, types, matches = scan_for_pii(text)
        assert has_pii is True
        assert "phone_us" in types

    def test_api_key_detection(self):
        text = "sk-abcdefghijklmnopqrstuvwxyz123456"
        has_pii, types, matches = scan_for_pii(text)
        assert has_pii is True
        assert "api_key_generic" in types

    def test_no_pii_clean_text(self):
        text = "This is a clean document about project management."
        has_pii, types, matches = scan_for_pii(text)
        assert has_pii is False
        assert len(types) == 0
        assert len(matches) == 0

    def test_multiple_pii_types(self):
        text = "Email: test@example.com, SSN: 123-45-6789, Key: AKIAIOSFODNN7EXAMPLE"
        has_pii, types, matches = scan_for_pii(text)
        assert has_pii is True
        assert len(types) == 3
        assert "email" in types
        assert "ssn" in types
        assert "aws_access_key" in types


class TestUpdateDocumentClassification:
    """Test Supabase update function"""

    @patch.dict(
        os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_SERVICE_KEY": "test-key"}
    )
    @patch("requests.patch")
    def test_update_approved(self, mock_patch):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_patch.return_value = mock_response

        result = update_document_classification("doc-123", "approved", [], {})
        assert result is True
        mock_patch.assert_called_once()

    @patch.dict(
        os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_SERVICE_KEY": "test-key"}
    )
    @patch("requests.patch")
    def test_update_quarantined(self, mock_patch):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_patch.return_value = mock_response

        result = update_document_classification(
            "doc-456", "quarantined", ["ssn"], {"ssn": ["123-45-6789"]}
        )
        assert result is True

    @patch.dict(
        os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_SERVICE_KEY": "test-key"}
    )
    @patch("requests.patch")
    def test_update_failure(self, mock_patch):
        mock_response = Mock()
        mock_response.status_code = 400
        mock_patch.return_value = mock_response

        result = update_document_classification("doc-789", "approved", [], {})
        assert result is False


class TestLambdaHandler:
    """Test Lambda entry point"""

    @patch.dict(
        os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_SERVICE_KEY": "test-key"}
    )
    @patch("lambda_handler.update_document_classification")
    def test_lambda_direct_invocation(self, mock_update):
        mock_update.return_value = True

        event = {"document_id": "test-doc-123", "content": "Contact john@example.com for details"}

        result = lambda_handler(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["processed"] == 1
        assert body["results"][0]["pii_detected"] is True

    @patch.dict(
        os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_SERVICE_KEY": "test-key"}
    )
    @patch("lambda_handler.update_document_classification")
    def test_lambda_s3_event(self, mock_update):
        mock_update.return_value = True

        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "documents/test-doc.txt"},
                    }
                }
            ]
        }

        result = lambda_handler(event, None)
        assert result["statusCode"] == 200

    @patch.dict(
        os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_SERVICE_KEY": "test-key"}
    )
    @patch("lambda_handler.update_document_classification")
    def test_lambda_no_content(self, mock_update):
        event = {"document_id": "empty-doc", "content": ""}
        result = lambda_handler(event, None)
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        # Should skip empty content
        assert len(body["results"]) == 0
