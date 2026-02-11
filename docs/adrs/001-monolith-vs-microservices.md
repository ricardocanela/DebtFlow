# ADR-001: Modular Monolith over Microservices

**Date:** 2025-01-15

**Status:** Accepted

## Context

DebtFlow is being built by a 9-person engineering team. We need to decide on the
high-level architecture for the system. The two primary options considered were:

- **Microservices:** Independent services per domain (accounts, payments, communications, ingestion).
- **Modular monolith:** A single deployable unit with well-defined internal module boundaries.

The team has experience with Django and Python. We expect moderate traffic volumes
typical of B2B debt collection workflows, not consumer-scale request rates. Early
velocity and operational simplicity are critical — the team must ship features
quickly while maintaining reliability for financial operations.

## Decision

We will adopt a **modular monolith** architecture using Django, with clearly
separated internal modules (Django apps) for each bounded context:

- `accounts` — debtor accounts and creditor relationships
- `payments` — payment processing and plan management
- `communications` — letters, emails, SMS dispatch
- `ingestion` — file intake and parsing
- `audit` — audit logging and compliance trails

Module boundaries will be enforced through explicit public interfaces (service
layers) rather than direct cross-module model imports.

## Consequences

**Positive:**

- Single deployment artifact simplifies CI/CD, monitoring, and debugging.
- In-process function calls eliminate network latency and serialization overhead
  between modules.
- Shared PostgreSQL transactions across modules maintain strong consistency for
  financial data operations.
- Lower operational overhead — no service mesh, no distributed tracing required
  on day one.
- A team of 9 can own and deploy the entire system without complex coordination.

**Negative:**

- Individual modules cannot be scaled independently. If the ingestion pipeline
  needs more compute, the entire application must scale horizontally.
- Risk of module boundaries eroding over time if code reviews do not enforce
  separation discipline.
- Future extraction to services (if needed) will require refactoring effort,
  though well-defined interfaces reduce this cost.

**Mitigations:**

- Lint rules and CI checks to prevent cross-module model imports.
- Quarterly architecture reviews to assess whether extraction is warranted.
- Celery workers already run as separate processes, providing natural scaling
  for background workloads.
