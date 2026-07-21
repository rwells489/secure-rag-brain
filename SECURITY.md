# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not open public issues for security vulnerabilities.**

Instead, report them privately via:

1. **GitHub Security Advisories** (preferred): Go to Security tab → "Report a vulnerability"
2. **Email:** security@wells.dev

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment:** Within 48 hours
- **Initial assessment:** Within 1 week
- **Fix timeline:** Depends on severity, typically 2-4 weeks

## Security Architecture

This project implements defense-in-depth for PII protection:

### Ingress Layer
- Async Lambda triage scans **before** vector ingestion
- Regex + NER detection (SSN, AWS keys, credit cards, emails, phones, API keys)
- Quarantine-by-default: any detection → `classification_status = 'quarantined'`

### Storage Layer
- **Row Level Security (RLS)** enforced at PostgreSQL level
- Users **cannot** query quarantined vectors (`classification_status = 'approved'` required)
- Service role bypass only for Lambda/Edge Function updates

### Query Layer
- HNSW vector index scoped to approved documents only
- Tenant isolation via `auth.uid() = user_id` RLS policies
- Admin audit access via separate RLS policy

## Threat Model

| Threat | Mitigation |
|--------|------------|
| PII in vector store | Pre-ingestion scan + quarantine |
| Tenant data leakage | PostgreSQL RLS (database-enforced) |
| Unauthorized admin access | Service role restricted to Lambda/Edge Fn |
| Embedding model poisoning | OpenRouter free models, local option |
| S3 data exposure | Private bucket, versioning, no public access |

## Compliance Notes

- **GDPR:** Right to erasure via document deletion + vector cleanup job
- **CCPA:** PII detection covers major categories
- **SOC 2:** Audit trail via `classification_status`, `detected_pii_types`, `pii_matches`

## Dependencies

- All dependencies pinned in `requirements.txt` / `pyproject.toml`
- `Dependabot` enabled for automated security updates
- `pip-audit` recommended for CI

## Disclosure Policy

We follow responsible disclosure. Public disclosure after fix is released and users have reasonable time to upgrade (typically 30 days).