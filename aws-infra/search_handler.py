import json
import os

import requests

# Initialize clients
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

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
            input=text[:8000],
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return None


def _vector_search(query_embedding: list[float], user_id: str, limit: int = 10) -> list[dict]:
    """
    Perform cosine similarity search on user's approved documents via Supabase RPC.
    Requires a Postgres function for vector search with RLS.
    """
    url = f"{SUPABASE_URL}/rest/v1/rpc/search_user_documents"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "query_embedding": query_embedding,
        "match_count": limit,
        "filter_user_id": user_id,
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    print(f"Vector search failed: {response.status_code} - {response.text}")
    return []


def lambda_handler(event, context):
    """
    Search endpoint: embed query → vector search (RLS filtered) → return results.
    """
    print(f"Search event: {json.dumps(event)}")

    try:
        # Parse request body
        if event.get("body"):
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        else:
            body = event

        query = body.get("query", "").strip()
        user_id = body.get("user_id", "")
        limit = min(body.get("limit", 10), 50)

        if not query or not user_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: query, user_id"}),
            }

        # Generate query embedding
        query_embedding = _generate_embedding(query)
        if not query_embedding:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to generate query embedding"}),
            }

        # Execute vector search
        results = _vector_search(query_embedding, user_id, limit)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"query": query, "results": results, "count": len(results)}),
        }

    except Exception as e:
        print(f"Search error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }


# Local testing
if __name__ == "__main__":
    test_event = {
        "query": "project status update",
        "user_id": "tenant-usr-489x-wells",
        "limit": 5,
    }
    print(lambda_handler(test_event, None))
