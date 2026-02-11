# ADR-005: Helm Charts over Kustomize

**Date:** 2025-02-01

**Status:** Accepted

## Context

DebtFlow runs on Kubernetes (EKS). We need a strategy for managing Kubernetes
manifests across multiple environments: `dev`, `staging`, and `production`.

The two primary approaches evaluated:

- **Kustomize:** Overlay-based patching of plain YAML manifests. Built into
  `kubectl`. No templating — uses strategic merge patches.
- **Helm:** Templated charts with per-environment values files. Package
  management, dependency resolution, and lifecycle hooks.

Key requirements:

- Per-environment configuration (replica counts, resource limits, feature flags).
- Pre-deploy database migration execution.
- Dependency management (e.g., Redis, ingress controller sub-charts).
- Rollback support.

## Decision

We will use **Helm 3** as the primary tool for packaging and deploying DebtFlow
to Kubernetes.

Structure:

```
charts/
  debtflow/
    Chart.yaml
    values.yaml              # defaults
    values-dev.yaml
    values-staging.yaml
    values-production.yaml
    templates/
      deployment.yaml
      service.yaml
      ingress.yaml
      migration-job.yaml     # pre-upgrade hook
    charts/                  # sub-chart dependencies
```

Key practices:

- `helm upgrade --install` with `--atomic` flag for automatic rollback on failure.
- Pre-upgrade hook (`helm.sh/hook: pre-upgrade`) runs Django migrations before
  new pods are deployed.
- ArgoCD syncs Helm charts from the Git repository for GitOps-driven deployments.

## Consequences

**Positive:**

- Go templates enable conditional logic and loops — useful for generating
  environment-specific resources (e.g., HPA only in production).
- Values files provide a clear, declarative diff between environments.
- Helm hooks solve the migration-before-deploy problem cleanly.
- Sub-chart dependencies (Redis, ingress-nginx) managed via `Chart.yaml`
  without maintaining separate manifests.
- `helm rollback` provides a built-in mechanism for reverting failed releases.

**Negative:**

- Go template syntax is verbose and error-prone. Complex templates are
  difficult to read and debug.
- Helm introduces a layer of abstraction over plain Kubernetes YAML —
  new team members must learn Helm-specific concepts.
- Template rendering bugs can produce invalid YAML that only surfaces
  at deploy time.

**Mitigations:**

- `helm template` and `helm lint` integrated into CI to catch rendering
  errors before deployment.
- `helm diff` plugin used in PR previews to show manifest changes.
- Templates kept intentionally simple — complex logic pushed into values
  files or external scripts.
