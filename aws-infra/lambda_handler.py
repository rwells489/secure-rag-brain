import json
import os
import re

# Initialize Supabase client (using service role key for RLS bypass)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# PII detection patterns (regex-based, zero external dependencies)
PII_PATTERNS = {
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "aws_access_key": r"\b(AKIA|ASCA|ASIA)[A-Z0-9]{16}\b",
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone_us": r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "api_key_generic": r"\b(sk-|pk-|rk-)[A-Za-z0-9]{32,}\b",
}

# Classification thresholds
QUARANTINE_THRESHOLD = 1  # Any PII detection triggers quarantine

# OpenRouter client for embeddings (initialized lazily)
_openrouter_client = None


def _get_openrouter_client():
    """Lazy-initialize OpenRouter client for embeddings."""
    global _openrouter_client
    if _openrouter_client is None and OPENROUTER_API_KEY:
        from openai import OpenAI
        _openrouter_client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )
    return _openrouter_client


def _generate_embedding(text: str) -> list[float] | None:
    """Generate embedding via OpenRouter (free nomic-embed-text model)."""
    client = _get_openrouter_client()
    if not client:
        return None
    try:
        response = client.embeddings.create(
            model="nomic-ai/nomic-embed-text-v1.5",
            input=text[:8000],  # Truncate to model max
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return None


def scan_for_pii(text: str) -> tuple[bool, list[str], dict[str, list[str]]]:
    """
    Scan text for PII patterns.
    Returns: (has_pii, pii_types_list, matches_dict)
    """
    detected_types = []
    matches = {}

    for pii_type, pattern in PII_PATTERNS.items():
        found = re.findall(pattern, text)
        if found:
            detected_types.append(pii_type)
            matches[pii_type] = found[:5]  # Limit stored matches

    return len(detected_types) > 0, detected_types, matches


def update_document_classification(
    document_id: str, status: str, pii_types: list[str], matches: dict, embedding: list[float] | None = None
) -> bool:
    """
    Update document classification in Supabase using service role.
    """
    import requests

    url = f"{SUPABASE_URL}/rest/v1/user_documents?id=eq.{document_id}"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    payload = {
        "classification_status": status,
        "pii_detected": len(pii_types) > 0,
        "detected_pii_types": pii_types,
        "pii_matches": matches,
    }
    if embedding is not None:
        payload["embedding"] = embedding

    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code == 204


def lambda_handler(event, context):
    """
    AWS Lambda entry point for async document triage.
    Triggered by S3 ObjectCreated or API Gateway.
    """
    print(f"Received event: {json.dumps(event)}")

    # Parse S3 event or direct invocation
    records = event.get("Records", [])
    if not records and "document_id" in event:
        # Direct invocation format
        records = [{"s3": {"bucket": {"name": "direct"}, "object": {"key": event["document_id"]}}}]

    results = []

    for record in records:
        try:
            # Extract document ID from S3 key or event
            s3_key = record.get("s3", {}).get("object", {}).get("key", "")
            document_id = s3_key.split("/")[-1].replace(".txt", "")

            # In production: fetch document content from S3
            # For demo: content passed in event or fetched from DB
            content = record.get("content", "") or event.get("content", "")

            if not content:
                print(f"No content for document {document_id}")
                continue

            # Scan for PII
            has_pii, pii_types, matches = scan_for_pii(content)

            # Determine classification
            status = "quarantined" if has_pii else "approved"

            # Generate embedding for approved documents
            embedding = None
            if status == "approved":
                embedding = _generate_embedding(content)
                if embedding:
                    print(f"Generated embedding for document {document_id} ({len(embedding)} dims)")
                else:
                    print(f"Warning: Failed to generate embedding for {document_id}")

            # Update database
            success = update_document_classification(document_id, status, pii_types, matches, embedding)

            results.append(
                {
                    "document_id": document_id,
                    "status": status,
                    "pii_detected": has_pii,
                    "pii_types": pii_types,
                    "updated": success,
                }
            )

            print(f"Document {document_id}: {status} | PII: {pii_types}")

        except Exception as e:
            print(f"Error processing record: {e}")
            results.append({"error": str(e)})

    return {"statusCode": 200, "body": json.dumps({"processed": len(results), "results": results})}


# Local testing
if __name__ == "__main__":
    test_event = {
        "document_id": "test-doc-123",
        "content": "Contact John at john.doe@company.com or call 555-123-4567. SSN: 123-45-6789",
    }
    print(lambda_handler(test_event, None))
