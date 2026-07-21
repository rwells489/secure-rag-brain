# Contributing to Secure RAG Brain

Thank you for your interest in contributing! This project demonstrates a secure, serverless RAG architecture with PII triage.

## Development Setup

1. **Fork and clone** the repository
2. **Install dependencies:**
   ```bash
   make install-dev
   ```
3. **Configure environment:**
   ```bash
   cp .env.example .env  # Create from template
   # Edit .env with your keys
   ```

## Code Standards

- **Python:** 3.11+, formatted with `ruff`, type-checked with `mypy`
- **SQL:** Postgres dialect, migrations in `supabase/migrations/`
- **TypeScript:** Deno for Supabase Edge Functions
- **Linting:** `ruff check` and `ruff format` before committing

## Testing

```bash
# Run all tests
make test

# Run specific test suites
cd aws-infra && python -m pytest tests/ -v
cd src && python -m pytest tests/ -v
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with tests
3. Run `make lint format typecheck test` locally
4. Submit PR with clear description
5. CI must pass (lint, test, typecheck)
6. At least one approval required

## Commit Convention

Use conventional commits:
```
feat: add new PII pattern for medical record numbers
fix: handle empty content in Lambda handler
docs: update architecture diagram
refactor: extract PII scanner to separate module
test: add unit tests for quarantine flow
```

## Security Issues

Report security vulnerabilities privately via GitHub Security Advisories or email security@wells.dev. Do not open public issues for security concerns.

## Architecture Decisions

Significant changes should be documented in `docs/adr/` as Architecture Decision Records (ADRs).

## Questions?

Open a discussion or issue — happy to help!