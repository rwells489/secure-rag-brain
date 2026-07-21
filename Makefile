# Secure RAG Brain - Development Makefile

.PHONY: help install lint test format clean deploy-local deploy-aws deploy-supabase start-local

# Default target
help:
	@echo "Secure RAG Brain - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install          Install all dependencies"
	@echo "  install-aws      Install SAM CLI and AWS tools"
	@echo "  install-supabase Install Supabase CLI"
	@echo ""
	@echo "Development:"
	@echo "  lint             Run ruff linting on Python code"
	@echo "  format           Format code with ruff"
	@echo "  test             Run all tests"
	@echo "  start-local      Start local development stack"
	@echo "  start-streamlit  Run Streamlit app locally"
	@echo ""
	@echo "Deploy:"
	@echo "  deploy-aws       Deploy SAM stack to AWS"
	@echo "  deploy-supabase  Push Supabase migrations"
	@echo "  deploy-frontend  Deploy Streamlit to cloud"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean            Remove build artifacts and caches"
# Setup
install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -r aws-infra/requirements.txt
	.venv/bin/pip install -r src/requirements.txt
	.venv/bin/pip install ruff pytest pytest-cov pytest-mock boto3 moto

install-aws:
	.venv/bin/pip install aws-sam-cli
	# Or: brew install aws/tap/aws-sam-cli

install-supabase:
	npm install -g supabase

# Linting
lint:
	.venv/bin/ruff check src/ aws-infra/ --output-format=github

format:
	.venv/bin/ruff format src/ aws-infra/
	.venv/bin/ruff check --fix src/ aws-infra/

# Testing
test:
	cd /home/ubuntu/secure-rag-brain/aws-infra && /home/ubuntu/secure-rag-brain/.venv/bin/python -m pytest tests/ -v
	cd /home/ubuntu/secure-rag-brain/src && /home/ubuntu/secure-rag-brain/.venv/bin/python -m pytest tests/ -v

test-lambda:
	pytest aws-infra/tests/ -v --tb=short

test-frontend:
	pytest src/tests/ -v --tb=short

# Local development
start-local:
	docker-compose up -d
	@echo "LocalStack running at http://localhost:4566"
	@echo "Redis running at localhost:6379"
	@echo ""
	@echo "Set env vars for local development:"
	@echo "  export AWS_ENDPOINT_URL=http://localhost:4566"
	@echo "  export AWS_REGION=us-east-1"
	@echo "  export AWS_ACCESS_KEY_ID=test"
	@echo "  export AWS_SECRET_ACCESS_KEY=test"

start-streamlit:
	cd src && streamlit run app.py --server.port 8501

start-supabase:
	supabase start

# Deployment
deploy-aws:
	cd aws-infra && sam deploy \
	  --stack-name secure-rag-brain-triage \
	  --region $(AWS_REGION) \
	  --capabilities CAPABILITY_IAM \
	  --parameter-overrides \
	    SupabaseUrl=$(SUPABASE_URL) \
	    SupabaseServiceKey=$(SUPABASE_SERVICE_KEY) \
	  --no-confirm-changeset

deploy-supabase:
	supabase db push --project-ref $(SUPABASE_PROJECT_REF)

deploy-frontend:
	@echo "Configure Streamlit Cloud / Railway / Fly.io deployment"
	@echo "See docs/deployment.md"

# Cleanup
clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	docker-compose down -v

# Validation
validate-sql:
	@for f in supabase/migrations/*.sql; do \
	  echo "Checking $$f..."; \
	  head -100 "$$f" | grep -E "(CREATE|ALTER|DROP|INSERT|UPDATE|DELETE|SELECT|INDEX|POLICY)" || true; \
	done

check-secrets:
	@echo "Checking for potential secrets in code..."
	@grep -r -i "api_key\|secret\|password\|token" --include="*.py" --include="*.ts" --include="*.sql" src/ aws-infra/ supabase/ | grep -v "example\|test\|mock\|placeholder\|os.environ\|os.getenv\|SUPABASE_SERVICE_KEY\|SUPABASE_URL" || echo "No hardcoded secrets found"