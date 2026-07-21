# Security RAG Brain - Architecture Reference

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SECURE RAG BRAIN ARCHITECTURE                        │
│                                                                             │
│  Zero-Trust, Serverless PII Triage → Vector Search Isolation                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   Client    │────▶│  API Gateway     │────▶│  S3 (Raw Land)  │────▶│  Lambda Triage   │
│ (Streamlit) │     │  /ingest         │     │  Bucket         │     │  (PII Scanner)   │
└─────────────┘     └──────────────────┘     └─────────────────┘     └────────┬─────────┘
                                                                               │
                    ┌──────────────────────┐                                  │
                    ▼                      ▼                                  │
            ┌───────────────┐      ┌───────────────┐                          │
            │  QUARANTINED  │      │   APPROVED    │                          │
            │  (RLS Blocked)│      │   (Clean)     │                          │
            └───────┬───────┘      └───────┬───────┘                          │
                    │                      │                                  │
                    ▼                      ▼                                  ▼
            ┌───────────────┐      ┌───────────────┐                ┌──────────────────┐
            │ Admin Review  │      │ Vector Store  │◀───────────────│  Classification  │
            │ Dashboard     │      │ (pgvector +   │                │  Update (RLS     │
            │               │      │  HNSW)        │                │  Bypass)         │
            └───────────────┘      └───────┬───────┘                └──────────────────┘
                                           │
                                           ▼
                                  ┌──────────────────┐
                                  │  Semantic Query  │
                                  │  (RLS Filtered)  │
                                  └──────────────────┘
```

---

## Component Details

### 1. Ingress Layer (API Gateway + S3)
- **Purpose:** Receive raw documents, store durably before processing
- **Security:** Private S3 bucket, versioned, no public access
- **Trigger:** `s3:ObjectCreated:*` events → Lambda

### 2. Triage Layer (AWS Lambda)
- **Runtime:** Python 3.11
- **Memory:** 256 MB
- **Timeout:** 30 seconds
- **Function:** Async PII scan using regex + optional NER
- **Output:** Updates Supabase `classification_status`

### 3. Storage Layer (Supabase PostgreSQL + pgvector)
- **Table:** `user_documents`
- **Vector:** `embedding vector(1536)` for semantic search
- **Index:** HNSW on `embedding` with `vector_cosine_ops`
- **Classification:** `pending | approved | quarantined`
- **PII Tracking:** `pii_detected`, `detected_pii_types`, `pii_matches`

### 4. Isolation Layer (PostgreSQL RLS)
```sql
-- Users see ONLY their own APPROVED documents for vector search
CREATE POLICY "users_select_own_approved"
ON user_documents FOR SELECT
USING (auth.uid() = user_id AND classification_status = 'approved');

-- Quarantined docs visible for review but NOT in vector index
CREATE POLICY "users_select_own_quarantined"
ON user_documents FOR SELECT
USING (auth.uid() = user_id AND classification_status = 'quarantined');

-- Only service role (Lambda/Edge Fn) can update classification
CREATE POLICY "service_role_full_access"
ON user_documents FOR ALL
USING (auth.role() = 'service_role');
```

### 5. Search Layer (HNSW Vector Index)
- **Algorithm:** Hierarchical Navigable Small World (HNSW)
- **Distance:** Cosine similarity
- **Scope:** Partial index `WHERE classification_status = 'approved'`
- **Tenant isolation:** Per-user via RLS + user_id filter

### 6. Admin Layer (Edge Function + Dashboard)
- **Edge Function:** `document-triage` (Deno/TypeScript)
- **Dashboard:** Streamlit admin UI
- **Capabilities:** Review quarantined, approve/reject, audit trail

---

## Data Flow

```
1. USER UPLOAD
   └─ Streamlit → API Gateway → S3 (raw text)

2. ASYNC TRIAGE
   └─ S3 Event → Lambda (PII scan) → Supabase (update status)

3. CLASSIFICATION
   ├─ APPROVED → embedding generated → HNSW index → searchable
   └─ QUARANTINED → RLS blocks from vector index → admin review

4. SEMANTIC SEARCH
   └─ User query → embed → HNSW search (RLS filtered) → results

5. ADMIN REVIEW
   └─ Dashboard → list quarantined → view matches → approve/reject
```

---

## Security Properties

| Property | Implementation |
|----------|----------------|
| **PII never in vectors** | Scan before embedding; quarantined excluded from HNSW |
| **Tenant isolation** | PostgreSQL RLS (`user_id = auth.uid()`) |
| **Admin bypass** | Service role only for Lambda/Edge Function |
| **Audit trail** | `classification_status`, `detected_pii_types`, `pii_matches` |
| **Data residency** | AWS region + Supabase region configurable |
| **Encryption** | TLS in transit, AES-256 at rest (S3, Supabase) |

---

## Cost Model (Free Tier)

| Component | Free Tier Limit | Monthly Cost |
|-----------|-----------------|--------------|
| AWS Lambda | 1M requests, 400K GB-sec | $0 |
| S3 | 5 GB storage | $0 |
| API Gateway | 1M requests | $0 |
| Supabase | 500 MB DB, 1 GB files, 2GB bandwidth | $0 |
| OpenRouter | Free models (nomic-embed-text, etc.) | $0 |
| **Total** | | **$0/month** |

At scale (>1M docs): ~$15-30/month (Lambda + Supabase Pro + paid embeddings)

---

## Deployment Commands

```bash
# 1. Deploy AWS SAM stack
cd aws-infra
sam deploy --guided

# 2. Push Supabase migrations
supabase db push --project-ref <PROJECT_REF>

# 3. Deploy Edge Function
supabase functions deploy document-triage --project-ref <PROJECT_REF>

# 4. Run Streamlit locally
cd src && streamlit run app.py

# 5. Deploy Streamlit to cloud (Streamlit Cloud, Railway, Fly.io)
```

---

## Environment Variables

### Lambda / Edge Function
```
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SERVICE_KEY=<service_role_key>
SUPABASE_SERVICE_ROLE_KEY=<service_role_key>  # Edge Function uses this name
```

### Streamlit (local)
```
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=<anon_key>
```

---

## Extending the System

### Add New PII Patterns
1. Update `PII_PATTERNS` in `lambda_handler.py`
2. Update `PII_PATTERNS` in `supabase/functions/document-triage/index.ts`
3. Update client-side preview in `src/app.py`
4. Test with `make test`

### Add Embedding Generation
```python
# In lambda_handler.py after approval
from openai import OpenAI
client = OpenAI(api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1")
embedding = client.embeddings.create(
    model="nomic-ai/nomic-embed-text-v1.5",
    input=document_content
).data[0].embedding
# Update Supabase with embedding
```

### Add Multi-Tenant API
- Create API Gateway authorizer (JWT validation)
- Scope all queries by `auth.uid()`
- Add rate limiting per tenant

---

## Monitoring & Debugging

### Lambda Logs
```bash
aws logs tail /aws/lambda/secure-rag-brain-triage --follow
```

### Supabase Logs
- Dashboard → Logs → Edge Functions
- Dashboard → Logs → Database → RLS violations

### Streamlit Debug
```bash
cd src && streamlit run app.py --logger.level=debug
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Lambda timeout | Increase timeout (max 15 min) or batch process |
| RLS not working | Check `auth.role()` = 'service_role' for Lambda |
| HNSW index slow | Ensure `classification_status = 'approved'` partial index |
| Embedding dimension mismatch | Verify `vector(1536)` matches model output |
| CORS errors | Check `corsHeaders` in Edge Function |
| Streamlit session state lost | Use `st.session_state` properly, avoid rerun loops |

---

## License

MIT — Use freely for portfolio, interviews, or production.