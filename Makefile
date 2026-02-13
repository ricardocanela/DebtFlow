.PHONY: help dev test lint migrate seed clean docker-up docker-down format typecheck

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development
dev: ## Start development environment with Docker
	docker compose -f docker/docker-compose.yml up --build

dev-d: ## Start development environment in background
	docker compose -f docker/docker-compose.yml up --build -d

down: ## Stop development environment
	docker compose -f docker/docker-compose.yml down

# Database
migrate: ## Run database migrations
	python manage.py migrate

makemigrations: ## Create new migrations
	python manage.py makemigrations

seed: ## Load seed data
	python scripts/seed_data.py

# Testing
test: ## Run all tests
	pytest --cov=apps --cov-report=term-missing

test-unit: ## Run unit tests only
	pytest -m "not integration" --cov=apps --cov-report=term-missing

test-integration: ## Run integration tests only
	pytest -m integration

test-ci: ## Run tests in CI mode
	pytest --cov=apps --cov-report=xml --junitxml=junit.xml

# Code Quality
lint: ## Run linter
	ruff check .
	ruff format --check .

format: ## Auto-format code
	ruff check --fix .
	ruff format .

typecheck: ## Run type checker
	mypy apps/ --ignore-missing-imports

# Docker
docker-build: ## Build Docker images
	docker compose -f docker/docker-compose.yml build

docker-test: ## Run tests in Docker
	docker compose -f docker/docker-compose.test.yml run --rm api pytest --cov=apps

# Helm
helm-lint: ## Lint Helm chart
	helm lint infra/helm/debtflow

helm-template: ## Render Helm templates
	helm template debtflow infra/helm/debtflow

helm-install: ## Install on minikube
	helm upgrade --install debtflow infra/helm/debtflow -f infra/helm/debtflow/values.yaml

# Terraform
tf-init: ## Initialize Terraform
	cd infra/terraform && terraform init

tf-plan: ## Plan Terraform changes
	cd infra/terraform && terraform plan

tf-validate: ## Validate Terraform
	cd infra/terraform && terraform validate

# Cleanup
clean: ## Remove cached files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov .coverage coverage.xml junit.xml
