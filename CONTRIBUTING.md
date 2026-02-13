# Contributing to DebtFlow

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ricardocanela/debtflow.git
   cd debtflow
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements/local.txt
   pip install -r requirements/test.txt
   ```

4. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

5. **Start infrastructure (PostgreSQL, Redis):**
   ```bash
   docker compose -f docker/docker-compose.yml up postgres redis -d
   ```

6. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

7. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the server:**
   ```bash
   python manage.py runserver
   ```

## Code Style

- **Linting:** We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting
- **Type hints:** All public functions must have type annotations
- **Imports:** Sorted by Ruff (isort compatible)
- Run `make format` before committing

## Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add collector performance analytics endpoint
fix: correct balance calculation on partial refund
docs: add SFTP import runbook
infra: add EKS node group scaling policy
test: add circuit breaker recovery test
refactor: extract payment validation to service layer
```

## Pull Request Process

1. Create a feature branch from `main`
2. Write tests for new functionality
3. Ensure all tests pass: `make test`
4. Ensure linting passes: `make lint`
5. Update documentation if needed
6. Create PR with descriptive title and summary

## Testing

- **Unit tests:** Test models, services, serializers in isolation
- **Integration tests:** Test API endpoints with real database
- **Mark integration tests:** Use `@pytest.mark.integration`
- **Factories:** Use factory-boy for test data (see `tests/factories.py`)

```bash
make test          # All tests
make test-unit     # Unit tests only
make lint          # Linting
make typecheck     # Type checking
```

## Project Structure

```
apps/           # Django apps (accounts, payments, integrations, analytics, audit)
config/         # Django settings and configuration
tasks/          # Celery tasks
infra/          # Terraform + Helm
monitoring/     # Prometheus + Grafana
docker/         # Dockerfiles and compose
docs/           # Documentation, ADRs, runbooks
scripts/        # Utility scripts
```
