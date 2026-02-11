# ADR-006: Terraform Workspaces per Environment

**Date:** 2025-02-01

**Status:** Accepted

## Context

DebtFlow infrastructure (VPC, EKS, RDS, ElastiCache, S3, SQS) is provisioned
with Terraform. We need a strategy to manage the same infrastructure definition
across three environments: `dev`, `staging`, and `production`.

Approaches considered:

- **Directory-based separation:** Duplicate Terraform roots per environment
  (`infra/dev/`, `infra/staging/`, `infra/prod/`). Clear isolation but high
  duplication and drift risk.
- **Terraform workspaces:** Single set of modules with `terraform.workspace`
  used to select variable files. Shared code, per-workspace state.
- **Terragrunt:** Wrapper tool that manages remote state and module composition.
  Powerful but adds tooling complexity.

## Decision

We will use **Terraform workspaces** to manage per-environment infrastructure
from a single module codebase.

Structure:

```
infra/
  main.tf
  variables.tf
  outputs.tf
  envs/
    dev.tfvars
    staging.tfvars
    production.tfvars
  modules/
    vpc/
    eks/
    rds/
    elasticache/
    s3/
    sqs/
```

State management:

- Remote state stored in **S3** with a per-workspace key prefix.
- **DynamoDB table** for state locking to prevent concurrent applies.
- State bucket versioning enabled for rollback capability.

Usage:

```bash
terraform workspace select staging
terraform plan -var-file=envs/staging.tfvars
terraform apply -var-file=envs/staging.tfvars
```

## Consequences

**Positive:**

- Single module codebase eliminates duplication — a fix in one place applies
  to all environments.
- Per-workspace state provides full isolation between environments. A failed
  apply in `dev` cannot affect `production` state.
- S3 + DynamoDB locking is a well-established pattern with strong durability
  guarantees.
- Variable files per environment make differences between environments
  explicit and auditable.

**Negative:**

- Workspace name is implicit context — operators must verify the active
  workspace before running `terraform apply`. Applying to the wrong workspace
  is a high-severity mistake.
- All environments share the same module versions. A module change intended
  for `dev` is immediately available in the `production` workspace if applied.
- Terraform workspaces are considered by some in the community as better
  suited for ephemeral environments rather than long-lived ones.

**Mitigations:**

- CI/CD pipeline (GitHub Actions) is the only path to `staging` and
  `production` applies — no manual `terraform apply` in those environments.
- `terraform plan` output is posted as a PR comment for review before merge.
- Workspace name printed prominently in all CI logs and plan outputs.
- Branch protection rules require plan approval before apply runs.
