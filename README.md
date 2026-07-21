# Secure RAG Brain — Hybrid Edge-Cloud Data Triage Architecture

**Enterprise-grade PII filtering, vector search, and secure RAG — built on free-tier serverless infrastructure.**

---

## 🎯 Project Overview

This repository demonstrates a **zero-trust, cost-optimized architecture** for ingesting, classifying, and querying documents with guaranteed PII isolation. It replaces expensive managed compliance services (AWS Macie, Azure Purview) with a **hybrid edge-cloud triage layer** running open-source detection (Microsoft Presidio / regex) on serverless compute — keeping raw data out of vector stores until validated.

**Key outcomes:**
- ✅ **$0/month** operational cost (AWS Lambda Free Tier + Supabase Free Tier + OpenRouter free models)
- ✅ **Sub-second PII detection** at ingestion gateway
- ✅ **Row-Level Security (RLS)** enforces tenant isolation at database layer
- ✅ **HNSW vector index** for production-grade semantic search
- ✅ **Audit-ready quarantine flow** with admin review dashboard

---

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  User Upload │────▶│  Gateway Triage Layer │────▶│  Classification │
│  (Frontend)  │     │  (Lambda / Edge Fn)   │     │  Decision       │
└─────────────┘     └──────────┬─────────────┘     └────────┬────────┘
                               │                          │
                    ┌──────────┴──────────┐                │
                    ▼                     ▼                ▼
            ┌───────────────┐      ┌───────────────┐  ┌───────────┐
            │  QUARANTINED  │      │   APPROVED    │  │  EMBED &  │
            │  (RLS Blocked)│      │   (Clean)     │  │  INDEX    │
            └───────────────┘      └───────────────┘  └───────────┘
                    │                     │                    │
                    ▼                     ▼                    ▼
            ┌───────────────┐      ┌───────────────┐  ┌───────────────┐
            │ Admin Review  │      │ Vector Store  │  │  Semantic     │
            │ Dashboard     │      │ (pgvector +   │  │  Query (RLS   │
            │               │      │  HNSW)        │  │  Filtered)    │
            └───────────────┘      └───────────────┘  └───────────────┘
```

---

## 📂 Repository Structure

```
secure-rag-brain/
├── .github/workflows/
│   └── deploy-infra.yml          # CI/CD for infra + functions
├── aws-infra/
│   ├── lambda_handler.py         # PII triage Lambda (Python 3.11)
│   └── template.yaml             # AWS SAM template
├── supabase/
│   ├── migrations/
│   │   ├── 20260718000000_init_schema.sql
│   │   └── 20260718000001_rls_policies.sql
│   └── functions/
│       └── document-triage/      # Supabase Edge Function (Deno)
├── src/
│   ├── components/               # React/Streamlit UI components
│   └── lib/                      # Supabase client, auth helpers
├── architecture-diagram.png      # Excalidraw / Mermaid source
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured (`aws configure`)
- Supabase CLI (`brew install supabase/tap/supabase`)
- Python 3.11+, Node 18+
- OpenRouter API key (free tier) for embeddings

### 1. Deploy Supabase Schema
```bash
cd supabase
supabase db push
```

### 2. Deploy AWS Lambda (SAM)
```bash
cd aws-infra
sam build
sam deploy --guided
# Stack name: secure-rag-triage
# Region: us-east-1 (or your Supabase region)
```

### 3. Configure Environment Variables
| Variable | Where | Value |
|----------|-------|-------|
| `SUPABASE_URL` | Lambda / Edge Fn | `https://<project>.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Lambda / Edge Fn | Service role key (settings → API) |
| `OPENROUTER_API_KEY` | Lambda / Edge Fn | Free key from openrouter.ai |

### 4. Run Frontend (Streamlit Example)
```bash
cd src
pip install -r requirements.txt
streamlit run app.py
```

---

## 🛡️ Security Model

| Layer | Mechanism | Guarantee |
|-------|-----------|-----------|
| **Ingress** | Regex + Presidio NER in Lambda | No raw PII reaches vector store |
| **Storage** | `classification_status` enum + `pii_detected` flag | Explicit state machine |
| **Query** | RLS policy: `classification_status = 'approved'` | Tenants **cannot** query quarantined vectors |
| **Admin** | Separate RLS policy for `quarantined` metadata | Review without vector exposure |
| **Embeddings** | OpenRouter free models (local optional) | No proprietary model lock-in |

---

## 💰 Cost Breakdown (Monthly)

| Component | Free Tier Limit | Estimated Cost |
|-----------|-----------------|----------------|
| AWS Lambda | 1M requests / 400k GB-sec | **$0** |
| Supabase | 500MB DB, 1GB file storage | **$0** |
| OpenRouter | Free models (nomic-embed-text, etc.) | **$0** |
| **Total** | | **$0/month** |

> At scale (>1M docs): ~$15-30/month (Lambda + Supabase Pro + paid embeddings)

---

## 🧪 Testing the PII Pipeline

```bash
# Invoke Lambda directly with test payload
aws lambda invoke \
  --function-name secure-rag-triage-DocumentTriageFunction \
  --payload '{"document_id":"test-uuid","text":"My SSN is 123-45-6789"}' \
  response.json

cat response.json
# {"statusCode":200,"body":"Document flagged and safely isolated."}
```

Check Supabase dashboard → `user_documents` table → `classification_status = 'quarantined'`

---

## 📈 Interview Talking Points

> **Q: "Why not just use AWS Macie?"**
> **A:** Macie charges ~$1/GB scanned + $30/month for S3 monitoring. For a RAG pipeline ingesting 10GB/month, that's $400+/yr before you store a single vector. This architecture moves detection to **compute you already pay for** (Lambda free tier) and keeps raw text out of object storage entirely.

> **Q: "How do you handle false positives/negatives?"**
> **A:** The `detected_pii_types` JSONB array preserves *what* triggered quarantine. Admins review metadata (not raw content) via the quarantine dashboard. For false negatives, the async embedding job re-scans with Presidio's full NER model before indexing pass.

> **Q: "What about multi-tenancy at scale?"**
> **A:** RLS policies enforce `auth.uid() = user_id` at the PostgreSQL level — no application bypass. HNSW index is partitioned per-tenant via partial indexes (`WHERE user_id = ...`) for query isolation and performance.

---

## 📜 License

MIT — Use freely for portfolio, interviews, or production.

---

## 🙋 Author

**Raina Wells** — Data Governance & Architecture  
[LinkedIn](https://linkedin.com/in/rainawells) • [GitHub](https://github.com/rainawells)

*Built to prove that enterprise data security doesn't require enterprise budgets.*