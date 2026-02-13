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
	docker compose -f docker/docker-compose.yml exec api python manage.py migrate

makemigrations: ## Create new migrations
	docker compose -f docker/docker-compose.yml exec api python manage.py makemigrations

seed: ## Seed demo data (agencies, collectors, accounts, payments)
	docker compose -f docker/docker-compose.yml exec api python manage.py seed_demo

seed-clear: ## Clear and re-seed demo data from scratch
	docker compose -f docker/docker-compose.yml exec api python manage.py seed_demo --clear

shell: ## Open Django shell inside container
	docker compose -f docker/docker-compose.yml exec api python manage.py shell

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

# Frontend
frontend-install: ## Install frontend dependencies
	cd frontend && npm install

frontend-dev: ## Start frontend dev server
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	cd frontend && npm run build

frontend-lint: ## Lint frontend code
	cd frontend && npm run lint

# SFTP
sftp-upload: ## Upload sample CSVs to SFTP server
	docker compose -f docker/docker-compose.yml cp docker/sftp-samples/new_placements_feb2026.csv sftp-test-server:/home/sftpuser/upload/
	docker compose -f docker/docker-compose.yml cp docker/sftp-samples/portfolio_transfer_march2026.csv sftp-test-server:/home/sftpuser/upload/
	docker compose -f docker/docker-compose.yml cp docker/sftp-samples/urgent_placements_feb13.csv sftp-test-server:/home/sftpuser/upload/
	@echo "3 CSV files uploaded. Click 'Trigger Import' on /imports."

sftp-clear: ## Clear all files from SFTP server
	docker compose -f docker/docker-compose.yml exec sftp-test-server sh -c "rm -rf /home/sftpuser/upload/* /home/sftpuser/upload/processed/* 2>/dev/null; mkdir -p /home/sftpuser/upload/processed"
	@echo "SFTP server cleared."

sftp-reload: ## Clear SFTP and upload fresh samples
	$(MAKE) sftp-clear
	$(MAKE) sftp-upload

sftp-status: ## Show files on the SFTP server
	@echo "=== Pending (upload/) ==="
	@docker compose -f docker/docker-compose.yml exec sftp-test-server ls -la /home/sftpuser/upload/ 2>/dev/null || true
	@echo ""
	@echo "=== Processed ==="
	@docker compose -f docker/docker-compose.yml exec sftp-test-server ls -la /home/sftpuser/upload/processed/ 2>/dev/null || true

# Reset
reset: ## Full reset: destroy volumes, rebuild, seed, upload SFTP samples
	docker compose -f docker/docker-compose.yml down -v
	docker compose -f docker/docker-compose.yml up --build -d
	@echo "Waiting for services to start..."
	@sleep 12
	$(MAKE) seed
	$(MAKE) sftp-upload
	@echo "Reset complete. Frontend: http://localhost:3000"

# Logs
worker-logs: ## Tail Celery worker logs
	docker compose -f docker/docker-compose.yml logs -f worker

beat-logs: ## Tail Celery Beat logs
	docker compose -f docker/docker-compose.yml logs -f beat

api-logs: ## Tail API logs
	docker compose -f docker/docker-compose.yml logs -f api

# Cleanup
clean: ## Remove cached files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov .coverage coverage.xml junit.xml
