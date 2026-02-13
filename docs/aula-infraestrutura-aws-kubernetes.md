# AWS Infrastructure + Kubernetes for Production Applications

## Complete Lesson -- From Zero to Deploy with Terraform, Helm, EKS, and CI/CD

**Reference project:** DebtFlow -- Debt Collection Management Platform
**Stack:** Django + Celery + React | PostgreSQL + Redis | AWS EKS
**Prerequisites:** Basic knowledge of Docker, Linux, and AWS

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Terraform -- Infrastructure as Code](#2-terraform--infrastructure-as-code)
3. [Networking Module -- VPC and Subnets](#3-networking-module--vpc-and-subnets)
4. [EKS Module -- Kubernetes Cluster](#4-eks-module--kubernetes-cluster)
5. [Database Module -- RDS PostgreSQL](#5-database-module--rds-postgresql)
6. [Cache Module -- ElastiCache Redis](#6-cache-module--elasticache-redis)
7. [Storage Module -- S3](#7-storage-module--s3)
8. [ECR Module -- Container Registry](#8-ecr-module--container-registry)
9. [IAM Module -- IRSA (Roles for Pods)](#9-iam-module--irsa-roles-for-pods)
10. [Secrets Module -- AWS Secrets Manager](#10-secrets-module--aws-secrets-manager)
11. [DNS Module -- Route53 + ACM](#11-dns-module--route53--acm)
12. [Module Orchestration](#12-module-orchestration)
13. [Helm -- Packaging for Kubernetes](#13-helm--packaging-for-kubernetes)
14. [Helm Templates -- Deployments](#14-helm-templates--deployments)
15. [Helm Templates -- Services and Ingress](#15-helm-templates--services-and-ingress)
16. [Helm Templates -- Service Accounts (IRSA)](#16-helm-templates--service-accounts-irsa)
17. [Helm Templates -- ConfigMap and Secrets](#17-helm-templates--configmap-and-secrets)
18. [Helm Templates -- Network Policies](#18-helm-templates--network-policies)
19. [Helm Templates -- Jobs and CronJobs](#19-helm-templates--jobs-and-cronjobs)
20. [Helm Templates -- HPA and PDB](#20-helm-templates--hpa-and-pdb)
21. [Values per Environment](#21-values-per-environment)
22. [CI/CD -- GitHub Actions](#22-cicd--github-actions)
23. [Docker -- Production Images](#23-docker--production-images)
24. [Local Validation](#24-local-validation)
25. [Complete Deploy Flow](#25-complete-deploy-flow)
26. [Production Checklist](#26-production-checklist)

---

## 1. Architecture Overview

Before writing any infrastructure code, it is essential to understand **what** we are deploying and **how** the components connect to each other.

### Application Components

Our application has **3 deployable components**:

| Component | Description | Technology | Port |
|-----------|-------------|------------|------|
| **Backend (API)** | REST API serving the frontend | Django + Gunicorn | 8000 |
| **Data Retriever (Workers)** | Asynchronous processing, SFTP imports, payments | Celery + Redis | -- |
| **Frontend** | SPA served by nginx | React + Vite + Nginx | 80 |

### Infrastructure Services

| Service | Purpose | AWS Managed |
|---------|---------|-------------|
| PostgreSQL 16 | Primary database | RDS |
| Redis 7 | Cache + Celery Broker | ElastiCache |
| S3 | File storage (imports) | S3 |
| Kubernetes | Container orchestration | EKS |
| Container Registry | Docker image storage | ECR |
| Load Balancer | HTTP/HTTPS traffic entry point | ALB (via Ingress) |
| DNS | Domain resolution | Route53 |
| SSL/TLS | HTTPS certificates | ACM |

### Architecture Diagram

```
                         Internet
                            │
                      ┌─────┴──────┐
                      │  Route53   │
                      │  DNS       │
                      └─────┬──────┘
                            │
                      ┌─────┴──────┐
                      │  ACM       │
                      │  SSL/TLS   │
                      └─────┬──────┘
                            │
                 ┌──────────┴──────────┐
                 │    AWS ALB          │
                 │    (Load Balancer)  │
                 └────┬───────────┬────┘
                      │           │
              /api/*  │           │  /*
                      ▼           ▼
              ┌──────────┐  ┌──────────┐
              │ API Pods │  │ Frontend │
              │ Gunicorn │  │  Nginx   │
              │ :8000    │  │  :80     │
              └────┬─────┘  └──────────┘
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
     ┌────────┐ ┌──────┐ ┌──────────┐
     │ Worker │ │ Beat │ │ Migrate  │
     │ Celery │ │      │ │ (Job)    │
     └───┬────┘ └──┬───┘ └──────────┘
         │         │
    ┌────┴─────────┴────┐
    │                    │
    ▼                    ▼
┌─────────┐       ┌──────────┐       ┌────┐
│ RDS     │       │ElastiCache│      │ S3 │
│ PG 16   │       │ Redis 7  │      │    │
└─────────┘       └──────────┘      └────┘
```

### Fundamental Principle: Separation of Concerns

- **Terraform** provisions the AWS infrastructure (VPC, EKS, RDS, ElastiCache, S3, ECR, IAM)
- **Helm** deploys the application inside Kubernetes (Deployments, Services, Ingress)
- **GitHub Actions** automates the build and deploy process (CI/CD)
- **Docker** packages the application into reproducible images

Each tool has a well-defined scope. Terraform knows nothing about your application. Helm knows nothing about your AWS infrastructure. CI/CD connects the two worlds.

---

## 2. Terraform -- Infrastructure as Code

### What is Terraform?

Terraform is a tool that allows you to **describe infrastructure in configuration files** (HCL -- HashiCorp Configuration Language). Instead of clicking through the AWS console, you write code that can be versioned, reviewed, and reproduced.

### Fundamental Concepts

**Provider** -- The plugin that connects Terraform to a cloud service (AWS, GCP, Azure).

**Resource** -- An infrastructure component (e.g., `aws_instance`, `aws_vpc`, `aws_s3_bucket`).

**Module** -- A reusable group of resources. Works like an infrastructure "function."

**State** -- The file Terraform uses to track what already exists in the cloud. A mapping between code and reality.

**Backend** -- Where the state is stored (local, S3, etc.).

### Our Terraform Project Structure

```
infra/terraform/
├── backend.tf              # Provider and state configuration
├── variables.tf            # Input variables
├── main.tf                 # Module orchestration
├── outputs.tf              # Exported values
├── staging.tfvars          # Values for staging
├── production.tfvars       # Values for production
│
└── modules/
    ├── networking/          # VPC, subnets, security groups
    ├── eks/                 # Kubernetes cluster
    ├── database/            # RDS PostgreSQL
    ├── cache/               # ElastiCache Redis
    ├── storage/             # S3 bucket
    ├── ecr/                 # Container registries
    ├── iam/                 # IRSA roles
    ├── secrets/             # Secrets Manager
    └── dns/                 # Route53 + ACM
```

### The Backend -- Where Terraform Stores Its State

```hcl
# backend.tf
terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "debtflow-terraform-state"
    key            = "state/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "debtflow-terraform-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "debtflow"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
```

**Why S3 + DynamoDB?**
- **S3** stores the state durably and with versioning
- **DynamoDB** implements locking -- prevents two `terraform apply` commands from running simultaneously
- **Encrypt** ensures that sensitive data in the state is encrypted

**`default_tags`** -- All created resources will automatically receive these tags. Essential for cost control and organization.

### Variables -- Parameterizing the Infrastructure

```hcl
# variables.tf
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (staging, production)"
  type        = string

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be 'staging' or 'production'."
  }
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "create_dns" {
  description = "Whether to create Route53 and ACM resources"
  type        = bool
  default     = false
}

variable "eks_namespace" {
  description = "Kubernetes namespace for DebtFlow workloads"
  type        = string
  default     = "debtflow"
}
```

**Best practices:**
- Use `validation` to prevent invalid values
- Provide a `default` for values that rarely change
- Mark sensitive variables with `sensitive = true`
- Always use `description` -- it serves as living documentation

---

## 3. Networking Module -- VPC and Subnets

The networking module creates the **network foundation** for the entire infrastructure. No other AWS resource exists outside of a VPC.

### Concepts

**VPC (Virtual Private Cloud)** -- Your private network on AWS. All traffic between your resources passes through here.

**Subnet** -- A subdivision of the VPC. Can be public (internet access) or private (isolated).

**Internet Gateway** -- Allows public subnets to access the internet.

**NAT Gateway** -- Allows private subnets to access the internet (for downloading packages, for example) without being accessible from outside.

**Security Group** -- A virtual firewall that controls inbound and outbound traffic.

### Implementation

```hcl
# modules/networking/main.tf

# The VPC is the container for the entire network
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr       # 10.0.0.0/16 = 65,536 IPs
  enable_dns_hostnames = true               # Pods and services need DNS
  enable_dns_support   = true

  tags = { Name = "debtflow-${var.environment}" }
}

# Internet Gateway -- gateway to the internet
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "debtflow-${var.environment}-igw" }
}

# Public subnets -- where the Load Balancer lives
# We use count to create one subnet per AZ
resource "aws_subnet" "public" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = { Name = "debtflow-${var.environment}-public-${count.index}" }
}

# Private subnets -- where pods, RDS, and Redis live
resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = var.availability_zones[count.index]

  tags = { Name = "debtflow-${var.environment}-private-${count.index}" }
}

# NAT Gateway -- private pods need internet access
# (downloading pip packages, calls to Stripe API, etc.)
resource "aws_eip" "nat" {
  domain = "vpc"
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id    # NAT lives in the public subnet
}
```

### Why Both Public AND Private Subnets?

```
Internet
    │
    ▼
┌─────────────────────────────────────────┐
│ VPC (10.0.0.0/16)                       │
│                                          │
│  ┌──────────────┐  ┌──────────────┐     │
│  │ Public       │  │ Public       │     │
│  │ 10.0.0.0/24  │  │ 10.0.1.0/24  │     │
│  │ (us-east-1a) │  │ (us-east-1b) │     │
│  │              │  │              │     │
│  │  ALB ←───────┤  │              │     │
│  │  NAT GW      │  │              │     │
│  └──────┬───────┘  └──────────────┘     │
│         │                                │
│  ┌──────┴───────┐  ┌──────────────┐     │
│  │ Private      │  │ Private      │     │
│  │ 10.0.10.0/24 │  │ 10.0.11.0/24 │     │
│  │ (us-east-1a) │  │ (us-east-1b) │     │
│  │              │  │              │     │
│  │  EKS Pods    │  │  EKS Pods    │     │
│  │  RDS         │  │  Redis       │     │
│  └──────────────┘  └──────────────┘     │
│                                          │
└─────────────────────────────────────────┘
```

- **Public:** ALB, NAT Gateway -- accessible from the internet
- **Private:** Pods, RDS, Redis -- isolated, only accessible via internal VPC

### Security Groups -- Per-Service Firewalls

```hcl
# Database -- only accepts connections on port 5432 from within the VPC
resource "aws_security_group" "db" {
  name_prefix = "debtflow-${var.environment}-db-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]    # Internal traffic only
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"              # Any outbound traffic
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Cache -- same logic, port 6379
resource "aws_security_group" "cache" {
  name_prefix = "debtflow-${var.environment}-cache-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }
}
```

**Golden rule:** never expose a database or cache to the internet. Always use the VPC CIDR.

---

## 4. EKS Module -- Kubernetes Cluster

EKS (Elastic Kubernetes Service) is AWS's managed Kubernetes. AWS takes care of the control plane (API server, etcd, scheduler). You take care of the worker nodes.

### Concepts

**Cluster** -- The Kubernetes control plane (managed by AWS).

**Node Group** -- A group of EC2 instances that run your pods.

**OIDC Provider** -- Allows pods to assume IAM roles (IRSA). Essential for security.

**EKS Addons** -- AWS-managed components inside the cluster (CoreDNS, VPC CNI, etc.).

### Implementation

```hcl
# modules/eks/main.tf

# IAM Role for the cluster -- EKS needs permissions to manage resources
resource "aws_iam_role" "cluster" {
  name = "${var.cluster_name}-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.cluster.name
}

# The EKS Cluster itself
resource "aws_eks_cluster" "main" {
  name     = var.cluster_name           # e.g., "debtflow-staging"
  role_arn = aws_iam_role.cluster.arn

  vpc_config {
    subnet_ids = var.private_subnet_ids  # Cluster runs in private subnets
  }

  depends_on = [aws_iam_role_policy_attachment.cluster_policy]
}
```

### Node Group -- Where Your Pods Actually Run

```hcl
# IAM Role for the nodes
resource "aws_iam_role" "node" {
  name = "${var.cluster_name}-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

# 3 mandatory policies for EKS nodes
resource "aws_iam_role_policy_attachment" "node_worker" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.node.name
}

resource "aws_iam_role_policy_attachment" "node_cni" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.node.name
}

resource "aws_iam_role_policy_attachment" "node_ecr" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.node.name
}

# The Node Group with auto-scaling
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-nodes"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.private_subnet_ids
  instance_types  = [var.node_instance_type]   # e.g., "t3.medium"

  scaling_config {
    min_size     = var.node_min_size            # minimum 2 nodes
    max_size     = var.node_max_size            # maximum 5 nodes
    desired_size = var.node_desired_size        # starts with 3 nodes
  }
}
```

### OIDC Provider -- The Bridge Between Kubernetes and AWS IAM

```hcl
# This allows K8s pods to assume IAM roles directly
# Without OIDC, all pods inherit the node's role (insecure!)
data "tls_certificate" "cluster" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "cluster" {
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.cluster.certificates[0].sha1_fingerprint]
}
```

### EKS Addons -- Essential Managed Components

```hcl
# CoreDNS -- DNS resolution inside the cluster
resource "aws_eks_addon" "coredns" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "coredns"
  depends_on   = [aws_eks_node_group.main]
}

# kube-proxy -- networking rules for Services
resource "aws_eks_addon" "kube_proxy" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "kube-proxy"
  depends_on   = [aws_eks_node_group.main]
}

# VPC CNI -- each pod gets a real VPC IP
resource "aws_eks_addon" "vpc_cni" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "vpc-cni"
  depends_on   = [aws_eks_node_group.main]
}

# EBS CSI Driver -- for PersistentVolumes with EBS
resource "aws_eks_addon" "ebs_csi" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "aws-ebs-csi-driver"
  depends_on   = [aws_eks_node_group.main]
}
```

**Why declare addons as resources?** By declaring addons in Terraform, we ensure they exist in all environments and are updated in a controlled manner.

---

## 5. Database Module -- RDS PostgreSQL

### Implementation

```hcl
# modules/database/main.tf

# Subnet group -- RDS needs to know which subnets it can run in
resource "aws_db_subnet_group" "main" {
  name       = "debtflow-${var.environment}"
  subnet_ids = var.private_subnet_ids          # Always in private subnets!
}

# Parameter group -- PostgreSQL configuration
resource "aws_db_parameter_group" "main" {
  name   = "debtflow-${var.environment}-pg16"
  family = "postgres16"

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"               # Query monitoring
  }

  parameter {
    name  = "pg_stat_statements.track"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"                              # Log queries > 1 second
  }
}

# The RDS instance
resource "aws_db_instance" "main" {
  identifier     = "debtflow-${var.environment}"
  engine         = "postgres"
  engine_version = "16"
  instance_class = var.instance_class           # db.t3.medium

  allocated_storage     = var.allocated_storage  # 20 GB
  max_allocated_storage = var.allocated_storage * 4  # Autoscaling up to 80 GB
  storage_encrypted     = true                   # Encryption at rest

  db_name  = var.db_name                         # "debtflow"
  username = "debtflow"
  password = var.db_password                     # Comes from Secrets Manager!

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = var.security_group_ids
  parameter_group_name   = aws_db_parameter_group.main.name

  # Multi-AZ only in production (automatic failover)
  multi_az            = var.environment == "production"
  publicly_accessible = false                    # NEVER public!

  # Automatic backups
  backup_retention_period = 7                    # 7 days of backups
  backup_window           = "03:00-04:00"        # Backup at 3 AM UTC
  maintenance_window      = "Mon:04:00-Mon:05:00"

  # Protection against accidental deletion in production
  skip_final_snapshot       = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "debtflow-final-${var.environment}" : null
  deletion_protection       = var.environment == "production"
}
```

**Key points:**
- `multi_az` -- In production, RDS maintains a replica in another AZ. If the primary fails, automatic failover in ~60 seconds
- `storage_encrypted` -- Data encrypted on disk
- `deletion_protection` -- Prevents accidental `terraform destroy` in production
- `password` comes from the `secrets` module, not hardcoded

---

## 6. Cache Module -- ElastiCache Redis

```hcl
# modules/cache/main.tf

resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "debtflow-${var.environment}"
  description          = "DebtFlow Redis cluster (${var.environment})"

  node_type          = var.node_type         # cache.t3.micro
  num_cache_clusters = var.environment == "production" ? 2 : 1
  engine             = "redis"
  engine_version     = "7.0"
  port               = 6379

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = var.security_group_ids

  at_rest_encryption_enabled = true           # Data encrypted on disk
  transit_encryption_enabled = true           # Data encrypted in transit

  # Automatic failover only in production (requires 2+ nodes)
  automatic_failover_enabled = var.environment == "production"
}
```

**Redis serves two purposes:**
- **DB 0:** Django cache (sessions, query cache)
- **DB 1:** Celery broker (task queue)

---

## 7. Storage Module -- S3

```hcl
# modules/storage/main.tf

resource "aws_s3_bucket" "main" {
  bucket = var.bucket_name    # "debtflow-files-staging"
}

# Versioning -- keeps a history of each file
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration { status = "Enabled" }
}

# Encryption -- all objects are encrypted
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lifecycle -- old files move to Glacier (cheap) and are deleted after 1 year
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    id     = "archive-old-files"
    status = "Enabled"
    filter {}

    transition {
      days          = 90
      storage_class = "GLACIER"       # 90 days -> Glacier ($0.004/GB vs $0.023/GB)
    }

    expiration {
      days = 365                       # 365 days -> deleted
    }
  }
}

# Block all public access
resource "aws_s3_bucket_public_access_block" "main" {
  bucket                  = aws_s3_bucket.main.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

---

## 8. ECR Module -- Container Registry

ECR (Elastic Container Registry) stores your Docker images. It is like a private Docker Hub on AWS.

```hcl
# modules/ecr/main.tf

resource "aws_ecr_repository" "api" {
  name                 = "debtflow-api-${var.environment}"
  image_tag_mutability = "MUTABLE"     # Allows overwriting the "latest" tag

  image_scanning_configuration {
    scan_on_push = true                 # Automatic vulnerability scanning
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_repository" "frontend" {
  name                 = "debtflow-frontend-${var.environment}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

# Lifecycle policy -- keep only the last 20 images
# Without this, storage costs grow indefinitely
resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 20 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 20
      }
      action = { type = "expire" }
    }]
  })
}
```

**Why two repositories?**
- `debtflow-api` -- Backend image (Django + Gunicorn). Used by the API deployment, worker, beat, and jobs
- `debtflow-frontend` -- Frontend image (React build + Nginx). Used by the frontend deployment

---

## 9. IAM Module -- IRSA (Roles for Pods)

### The problem: how to grant AWS permissions to specific pods?

Without IRSA, all pods inherit the EC2 node's permissions. If the worker needs S3, **all** pods get S3 access. This violates the principle of least privilege.

### The solution: IRSA (IAM Roles for Service Accounts)

IRSA associates an IAM Role with a Kubernetes ServiceAccount. Only pods that use that ServiceAccount receive the permissions.

```
Pod (worker) -> ServiceAccount (debtflow-worker) -> IAM Role (debtflow-worker-role) -> S3 Policy
```

### Implementation

```hcl
# modules/iam/main.tf

locals {
  # Extracts the OIDC provider hostname (without https://)
  oidc_provider = replace(var.oidc_provider_url, "https://", "")
}

# Role for Workers (Celery) -- S3 access
resource "aws_iam_role" "worker" {
  name = "debtflow-${var.environment}-worker"

  # Trust policy: only the "debtflow-worker" ServiceAccount can assume this role
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = var.oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${local.oidc_provider}:aud" = "sts.amazonaws.com"
          "${local.oidc_provider}:sub" = "system:serviceaccount:${var.namespace}:debtflow-worker"
        }
      }
    }]
  })
}

# Policy: worker can read/write to S3
resource "aws_iam_role_policy" "worker_s3" {
  name = "debtflow-${var.environment}-worker-s3"
  role = aws_iam_role.worker.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket",
      ]
      Resource = [
        var.s3_bucket_arn,              # The bucket
        "${var.s3_bucket_arn}/*",       # Objects inside the bucket
      ]
    }]
  })
}
```

**The same logic applies to API and ALB Controller, each with their specific permissions.**

The API role includes access to S3 (for exports) and Secrets Manager (for reading secrets). The ALB Controller role includes extensive permissions for managing load balancers, target groups, and security groups.

---

## 10. Secrets Module -- AWS Secrets Manager

### The problem: hardcoded passwords

The original Helm chart had:
```yaml
DJANGO_SECRET_KEY: {{ "change-me-in-production" | b64enc }}
DATABASE_PASSWORD: {{ "change-me" | b64enc }}
```

This is extremely insecure -- passwords in source code, in Git, visible to everyone.

### The solution: Secrets Manager + automatic generation

```hcl
# modules/secrets/main.tf

# Generates a random 32-character password for the database
resource "random_password" "db_password" {
  length  = 32
  special = false          # No special characters (avoids issues with URLs)
}

# Generates a 50-character secret key for Django
resource "random_password" "django_secret_key" {
  length  = 50
  special = true
}

# Stores in Secrets Manager
resource "aws_secretsmanager_secret" "database" {
  name        = "debtflow/${var.environment}/database"
  description = "DebtFlow database credentials (${var.environment})"
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id
  secret_string = jsonencode({
    username = "debtflow"
    password = random_password.db_password.result
    host     = var.db_endpoint
    port     = 5432
    dbname   = "debtflow"
  })
}
```

**For secrets that cannot be generated (Stripe API key, SFTP password):**

```hcl
resource "aws_secretsmanager_secret_version" "stripe" {
  secret_id = aws_secretsmanager_secret.stripe.id
  secret_string = jsonencode({
    api_key        = "sk_test_changeme"      # Placeholder
    webhook_secret = "whsec_changeme"
  })

  lifecycle {
    ignore_changes = [secret_string]          # Terraform won't overwrite after manual population
  }
}
```

The `lifecycle { ignore_changes }` block is essential -- it allows Terraform to create the secret with a placeholder, and then someone can fill it in manually via the AWS console without Terraform reverting the change.

---

## 11. DNS Module -- Route53 + ACM

```hcl
# modules/dns/main.tf

# References an existing hosted zone
data "aws_route53_zone" "main" {
  name         = var.domain_name     # "debtflow.example.com"
  private_zone = false
}

# Wildcard SSL certificate
resource "aws_acm_certificate" "main" {
  domain_name               = var.domain_name
  subject_alternative_names = ["*.${var.domain_name}"]   # *.debtflow.example.com
  validation_method         = "DNS"                       # Automatic validation

  lifecycle {
    create_before_destroy = true    # Creates new cert before deleting the old one (zero downtime)
  }
}

# DNS records for certificate validation
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.main.zone_id
}

# Waits for validation to complete
resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}
```

**This module is conditional** -- it is only created when `create_dns = true`. For initial environments without a domain, it can be disabled.

---

## 12. Module Orchestration

The `main.tf` file at the Terraform root connects all the modules:

```hcl
# main.tf -- Orchestrates 9 modules

module "networking" {
  source             = "./modules/networking"
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
}

module "eks" {
  source             = "./modules/eks"
  environment        = var.environment
  cluster_name       = "debtflow-${var.environment}"
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  # ... (node sizing)
}

module "database" {
  source             = "./modules/database"
  environment        = var.environment
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  db_password        = module.secrets.db_password    # <- Comes from Secrets Manager!
  security_group_ids = [module.networking.db_security_group_id]
  # ...
}

module "iam" {
  source            = "./modules/iam"
  environment       = var.environment
  oidc_provider_arn = module.eks.oidc_provider_arn   # <- Comes from EKS!
  oidc_provider_url = module.eks.oidc_provider_url
  s3_bucket_arn     = module.storage.bucket_arn      # <- Comes from Storage!
  namespace         = var.eks_namespace
  # ...
}

# DNS is conditional
module "dns" {
  source      = "./modules/dns"
  count       = var.create_dns ? 1 : 0              # <- Only created if enabled
  environment = var.environment
  domain_name = var.domain_name
}
```

**Dependency graph:**

```
networking --> eks --> iam
     |              /
     |---> database
     |
     └---> cache

storage --> iam

secrets --> database (db_password)

eks --> iam (oidc_provider)
```

Terraform automatically resolves the creation order based on references between modules.

### Outputs -- Exporting Values for Helm

```hcl
# outputs.tf

output "ecr_api_repository_url" {
  description = "ECR repository URL for API image"
  value       = module.ecr.api_repository_url
  # E.g., 123456789.dkr.ecr.us-east-1.amazonaws.com/debtflow-api-staging
}

output "worker_role_arn" {
  description = "IAM role ARN for Celery worker service account"
  value       = module.iam.worker_role_arn
  # E.g., arn:aws:iam::123456789:role/debtflow-staging-worker
}
```

These outputs feed the `--set` flags of the Helm deploy in CI/CD.

---

## 13. Helm -- Packaging for Kubernetes

### What is Helm?

Helm is the "package manager" for Kubernetes. It allows you to:
- **Template** YAML manifests with variables
- **Version** deploys (rollback with `helm rollback`)
- **Parameterize** by environment (staging vs production)

### Helm Chart Structure

```
infra/helm/debtflow/
├── Chart.yaml                    # Chart metadata
├── values.yaml                   # Default values
├── values-staging.yaml           # Override for staging
├── values-production.yaml        # Override for production
│
└── templates/
    ├── api-deployment.yaml       # Backend API (Gunicorn)
    ├── worker-deployment.yaml    # Celery Worker
    ├── beat-deployment.yaml      # Celery Beat
    ├── frontend-deployment.yaml  # Frontend (Nginx)
    ├── service.yaml              # ClusterIP for API
    ├── frontend-service.yaml     # ClusterIP for Frontend
    ├── ingress.yaml              # ALB Ingress (routing)
    ├── serviceaccount.yaml       # Service Accounts (IRSA)
    ├── configmap.yaml            # Environment variables
    ├── secret.yaml               # Secrets
    ├── network-policy.yaml       # Pod firewall
    ├── hpa.yaml                  # Horizontal Pod Autoscaler
    ├── pdb.yaml                  # Pod Disruption Budget
    ├── migrate-job.yaml          # Migration Job (Helm hook)
    └── cronjobs.yaml             # Vacuum + audit cleanup
```

### Chart.yaml

```yaml
apiVersion: v2
name: debtflow
description: DebtFlow — Debt Collection Management Platform
type: application
version: 0.1.0           # Chart version
appVersion: "1.0.0"      # Application version
```

---

## 14. Helm Templates -- Deployments

### API Deployment

```yaml
# templates/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-api
  labels:
    app: debtflow
    component: api
spec:
  replicas: {{ .Values.replicaCount.api }}           # 2 (default), 3 (prod)
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1            # Creates 1 new pod before killing the old one
      maxUnavailable: 0      # Never runs out of available pods (zero downtime)
  selector:
    matchLabels:
      app: debtflow
      component: api
  template:
    metadata:
      labels:
        app: debtflow
        component: api
    spec:
      serviceAccountName: {{ .Release.Name }}-api    # <- IRSA
      containers:
        - name: api
          image: "{{ .Values.image.api.repository }}:{{ .Values.image.api.tag }}"
          imagePullPolicy: {{ .Values.image.api.pullPolicy }}
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: {{ .Release.Name }}-config     # <- Env vars
            - secretRef:
                name: {{ .Release.Name }}-secret     # <- Secrets
          resources:
            {{- toYaml .Values.resources.api | nindent 12 }}
          readinessProbe:                             # <- K8s checks if the pod is ready
            httpGet:
              path: /health/
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:                              # <- K8s restarts if the pod hangs
            httpGet:
              path: /health/
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 30
```

**Key concepts:**

- **`readinessProbe`** -- If it fails, K8s stops sending traffic to this pod (but does not kill it)
- **`livenessProbe`** -- If it fails, K8s restarts the pod
- **`resources`** -- CPU/memory limits. Without this, a single pod can consume the entire node
- **`RollingUpdate` with `maxUnavailable: 0`** -- Zero downtime deploy

### Worker Deployment (Data Retriever)

```yaml
# templates/worker-deployment.yaml
spec:
  template:
    spec:
      serviceAccountName: {{ .Release.Name }}-worker   # <- IRSA with S3 access
      containers:
        - name: worker
          image: "{{ .Values.image.api.repository }}:{{ .Values.image.api.tag }}"
          # ^ Uses the SAME image as the API! Only the command changes.
          command: ["celery", "-A", "config.celery", "worker",
                    "--loglevel=info",
                    "--concurrency={{ .Values.celery.concurrency }}"]
```

**Note:** Worker and API use the same Docker image. The difference is the `command`. This simplifies the build and ensures that API and worker run exactly the same code.

### Frontend Deployment

```yaml
# templates/frontend-deployment.yaml
spec:
  template:
    spec:
      containers:
        - name: frontend
          image: "{{ .Values.image.frontend.repository }}:{{ .Values.image.frontend.tag }}"
          # ^ DIFFERENT image -- React build + Nginx
          ports:
            - containerPort: 80
          readinessProbe:
            httpGet:
              path: /
              port: 80
```

---

## 15. Helm Templates -- Services and Ingress

### Services -- Internal Address for Each Component

```yaml
# templates/service.yaml -- API
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}-api
spec:
  type: ClusterIP              # Only accessible within the cluster
  ports:
    - port: 8000
      targetPort: 8000
  selector:
    app: debtflow
    component: api             # Routes to pods with this label
```

```yaml
# templates/frontend-service.yaml -- Frontend
spec:
  type: ClusterIP
  ports:
    - port: 80
      targetPort: 80
  selector:
    app: debtflow
    component: frontend
```

### Ingress -- The External Traffic Router

The Ingress is the central piece that connects the external world to internal services. On AWS, it creates an ALB (Application Load Balancer).

```yaml
# templates/ingress.yaml
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ .Release.Name }}-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing    # Public
    alb.ingress.kubernetes.io/target-type: ip            # Routes directly to pod IP
spec:
  ingressClassName: alb
  {{- if .Values.ingress.tls.enabled }}
  tls:
    - hosts:
        - {{ .Values.ingress.host }}
  {{- end }}
  rules:
    - host: {{ .Values.ingress.host }}
      http:
        paths:
          # /api/* -> Backend (Django)
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: {{ .Release.Name }}-api
                port:
                  number: 8000

          # /health/* -> Backend (health check)
          - path: /health
            pathType: Prefix
            backend:
              service:
                name: {{ .Release.Name }}-api
                port:
                  number: 8000

          # /admin/* -> Backend (Django Admin)
          - path: /admin
            pathType: Prefix
            backend:
              service:
                name: {{ .Release.Name }}-api
                port:
                  number: 8000

          # /* -> Frontend (React SPA)
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ .Release.Name }}-frontend
                port:
                  number: 80
{{- end }}
```

**Path order matters!** More specific paths (`/api`) must come before generic paths (`/`). The ALB evaluates from top to bottom.

```
https://debtflow.example.com/api/v1/accounts  ->  API Pod :8000
https://debtflow.example.com/health/           ->  API Pod :8000
https://debtflow.example.com/admin/            ->  API Pod :8000
https://debtflow.example.com/                  ->  Frontend Pod :80
https://debtflow.example.com/worklist          ->  Frontend Pod :80
```

---

## 16. Helm Templates -- Service Accounts (IRSA)

```yaml
# templates/serviceaccount.yaml

# API Service Account -- with IAM role annotation
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ .Release.Name }}-api
  annotations:
    {{- toYaml .Values.serviceAccount.api.annotations | nindent 4 }}
    # In production, this will be:
    # eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/debtflow-production-api
---
# Worker Service Account -- with IAM role for S3
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ .Release.Name }}-worker
  annotations:
    {{- toYaml .Values.serviceAccount.worker.annotations | nindent 4 }}
---
# Frontend Service Account -- no IAM role (does not need AWS access)
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ .Release.Name }}-frontend
```

During deploy, IRSA annotations are passed via `--set`:

```bash
helm upgrade --install debtflow ./debtflow \
  --set serviceAccount.worker.annotations."eks\.amazonaws\.com/role-arn"=arn:aws:iam::123:role/debtflow-worker
```

---

## 17. Helm Templates -- ConfigMap and Secrets

### ConfigMap -- Non-Sensitive Environment Variables

```yaml
# templates/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ .Release.Name }}-config
data:
  DJANGO_SETTINGS_MODULE: {{ .Values.env.DJANGO_SETTINGS_MODULE }}
  DJANGO_ALLOWED_HOSTS: {{ .Values.ingress.host | quote }}
  CORS_ALLOWED_ORIGINS: "https://{{ .Values.ingress.host }}"
  DATABASE_HOST: {{ .Values.database.host }}
  DATABASE_PORT: "{{ .Values.database.port }}"
  DATABASE_NAME: {{ .Values.database.name }}
  DATABASE_USER: "debtflow"
  REDIS_URL: "redis://{{ .Values.redis.host }}:{{ .Values.redis.port }}/0"
  CELERY_BROKER_URL: "redis://{{ .Values.redis.host }}:{{ .Values.redis.port }}/1"
  SFTP_HOST: {{ .Values.sftp.host | quote }}
  SFTP_PORT: "{{ .Values.sftp.port }}"
  SFTP_USER: {{ .Values.sftp.user | quote }}
  SFTP_REMOTE_DIR: {{ .Values.sftp.remoteDir | quote }}
  AWS_STORAGE_BUCKET_NAME: {{ .Values.aws.s3Bucket | quote }}
  AWS_S3_REGION_NAME: {{ .Values.aws.region | quote }}
  JWT_ACCESS_TOKEN_LIFETIME_MINUTES: "{{ .Values.jwt.accessLifetimeMinutes }}"
  JWT_REFRESH_TOKEN_LIFETIME_DAYS: "{{ .Values.jwt.refreshLifetimeDays }}"
  SENTRY_DSN: {{ .Values.sentry.dsn | default "" | quote }}
```

### Secret -- Sensitive Variables

```yaml
# templates/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ .Release.Name }}-secret
type: Opaque
data:
  # Values passed via --set during deploy (never hardcoded in Git)
  DJANGO_SECRET_KEY: {{ .Values.secrets.djangoSecretKey | default "change-me" | b64enc }}
  DATABASE_PASSWORD: {{ .Values.secrets.databasePassword | default "change-me" | b64enc }}
  STRIPE_API_KEY: {{ .Values.secrets.stripeApiKey | default "sk_test_changeme" | b64enc }}
  STRIPE_WEBHOOK_SECRET: {{ .Values.secrets.stripeWebhookSecret | default "whsec_changeme" | b64enc }}
  SFTP_PASSWORD: {{ .Values.secrets.sftpPassword | default "changeme" | b64enc }}
```

**In a real deploy, secrets are passed via the CLI:**

```bash
helm upgrade --install debtflow ./debtflow \
  --set secrets.djangoSecretKey=$(aws secretsmanager get-secret-value ...) \
  --set secrets.databasePassword=$(aws secretsmanager get-secret-value ...)
```

---

## 18. Helm Templates -- Network Policies

Network Policies are **pod-level firewalls**. Without them, any pod can communicate with any other pod in the cluster.

```yaml
# templates/network-policy.yaml

# API -- accepts traffic on port 8000, can access DB, Redis, HTTPS, DNS
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ .Release.Name }}-api-netpol
spec:
  podSelector:
    matchLabels:
      app: debtflow
      component: api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector: {}        # Any namespace (the ALB is in kube-system)
      ports:
        - port: 8000
  egress:
    - to: []
      ports:
        - port: 5432                   # PostgreSQL
          protocol: TCP
        - port: 6379                   # Redis
          protocol: TCP
        - port: 443                    # HTTPS (Stripe API, S3, Sentry)
          protocol: TCP
        - port: 53                     # DNS
          protocol: UDP
---
# Worker -- same idea, but also needs SSH (SFTP on port 22)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ .Release.Name }}-worker-netpol
spec:
  podSelector:
    matchLabels:
      app: debtflow
      component: worker
  policyTypes:
    - Egress
  egress:
    - to: []
      ports:
        - port: 5432                   # PostgreSQL
        - port: 6379                   # Redis
        - port: 443                    # HTTPS
        - port: 22                     # SFTP (SSH)
        - port: 53                     # DNS
---
# Frontend -- accepts traffic on port 80, does not need egress (serves static files)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ .Release.Name }}-frontend-netpol
spec:
  podSelector:
    matchLabels:
      app: debtflow
      component: frontend
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector: {}
      ports:
        - port: 80
  egress: []                           # No egress -- frontend is 100% static
```

---

## 19. Helm Templates -- Jobs and CronJobs

### Migration Job -- Runs Before Each Deploy

```yaml
# templates/migrate-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ .Release.Name }}-migrate
  annotations:
    "helm.sh/hook": pre-upgrade,pre-install        # Runs BEFORE the deploy
    "helm.sh/hook-weight": "-1"                     # High priority
    "helm.sh/hook-delete-policy": before-hook-creation  # Cleans up previous job
spec:
  template:
    spec:
      serviceAccountName: {{ .Release.Name }}-api
      restartPolicy: Never
      containers:
        - name: migrate
          image: "{{ .Values.image.api.repository }}:{{ .Values.image.api.tag }}"
          command: ["python", "manage.py", "migrate", "--noinput"]
          envFrom:
            - configMapRef:
                name: {{ .Release.Name }}-config
            - secretRef:
                name: {{ .Release.Name }}-secret
  backoffLimit: 3                                    # Retries 3 times on failure
```

**Helm Hooks** execute Jobs at specific moments in the deploy lifecycle:
- `pre-install` -- Before the first installation
- `pre-upgrade` -- Before each upgrade
- `post-install` -- After installation
- `pre-delete` -- Before uninstalling

### CronJobs -- Scheduled Tasks

```yaml
# templates/cronjobs.yaml

# PostgreSQL Vacuum -- every Sunday at 3 AM
apiVersion: batch/v1
kind: CronJob
metadata:
  name: {{ .Release.Name }}-vacuum
spec:
  schedule: "0 3 * * 0"                  # Cron syntax: min hour day month weekday
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: {{ .Release.Name }}-worker
          restartPolicy: OnFailure
          containers:
            - name: vacuum
              image: "{{ .Values.image.api.repository }}:{{ .Values.image.api.tag }}"
              command: ["python", "-c",
                "import django; django.setup(); from tasks.maintenance import vacuum_tables; vacuum_tables()"]
```

---

## 20. Helm Templates -- HPA and PDB

### HPA -- Horizontal Pod Autoscaler

Automatically scales the number of pods based on metrics (CPU, memory).

```yaml
# templates/hpa.yaml
{{- if .Values.hpa.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ .Release.Name }}-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ .Release.Name }}-api
  minReplicas: {{ .Values.hpa.minReplicas }}         # Minimum 3 (prod)
  maxReplicas: {{ .Values.hpa.maxReplicas }}         # Maximum 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.hpa.targetCPUUtilization }}  # 70%
{{- end }}
```

**How it works:**
- Average CPU > 70% -> creates more pods (up to maxReplicas)
- Average CPU < 70% -> removes pods (down to minReplicas)
- Decisions are made every 15 seconds

### PDB -- Pod Disruption Budget

Ensures that pods are always available during maintenance (node upgrades, scaling, etc.).

```yaml
# templates/pdb.yaml
{{- if .Values.pdb.enabled }}
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ .Release.Name }}-api-pdb
spec:
  minAvailable: {{ .Values.pdb.minAvailable }}       # Always at least 2 pods available
  selector:
    matchLabels:
      app: debtflow
      component: api
{{- end }}
```

**Without PDB:** K8s can kill all pods of a Deployment during a node drain. Your app goes down.

**With PDB:** K8s ensures that at least N pods are always running, even during maintenance.

---

## 21. Values per Environment

### Default (values.yaml)

```yaml
replicaCount:
  api: 2
  worker: 2
  beat: 1
  frontend: 2

image:
  api:
    repository: debtflow-api
    tag: latest
    pullPolicy: IfNotPresent
  frontend:
    repository: debtflow-frontend
    tag: latest
    pullPolicy: IfNotPresent

resources:
  api:
    requests: { cpu: 250m, memory: 256Mi }
    limits: { cpu: 500m, memory: 512Mi }
  worker:
    requests: { cpu: 250m, memory: 256Mi }
    limits: { cpu: 500m, memory: 512Mi }
  beat:
    requests: { cpu: 50m, memory: 64Mi }
    limits: { cpu: 100m, memory: 128Mi }
  frontend:
    requests: { cpu: 50m, memory: 64Mi }
    limits: { cpu: 100m, memory: 128Mi }
```

### Staging (values-staging.yaml) -- Minimal Resources

```yaml
replicaCount:
  api: 1          # 1 replica (cost-effective)
  worker: 1
  beat: 1
  frontend: 1

hpa:
  enabled: false  # No autoscaling

pdb:
  enabled: false  # No disruption budget

celery:
  concurrency: 2  # Fewer Celery workers
```

### Production (values-production.yaml) -- High Availability

```yaml
replicaCount:
  api: 3          # 3 replicas (HA)
  worker: 2
  beat: 1
  frontend: 2

hpa:
  enabled: true
  minReplicas: 3
  maxReplicas: 10

pdb:
  enabled: true
  minAvailable: 2

ingress:
  tls:
    enabled: true  # HTTPS required

celery:
  concurrency: 8   # 8 workers per pod
```

---

## 22. CI/CD -- GitHub Actions

### Deploy Flow

```
Developer -> Push to main --> CD Staging --> Staging Environment
                                              |
Developer -> Git tag v1.0.0 --> CD Production --> Production Environment
```

### Staging Pipeline

```yaml
# .github/workflows/cd-staging.yml
name: CD — Deploy to Staging

on:
  push:
    branches: [main]        # Every push to main deploys to staging

env:
  ECR_API_REPOSITORY: debtflow-api-staging
  ECR_FRONTEND_REPOSITORY: debtflow-frontend-staging

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging     # GitHub Environment (requires approval if configured)
    steps:
      # 1. Checkout the code
      - uses: actions/checkout@v4

      # 2. Login to AWS via OIDC (no access keys!)
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}

      # 3. Login to ECR
      - uses: aws-actions/amazon-ecr-login@v2

      # 4. Build and push the API image
      - name: Build & Push API image
        run: |
          docker build -f docker/Dockerfile \
            -t $ECR_REGISTRY/$ECR_API_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_API_REPOSITORY:$IMAGE_TAG

      # 5. Build and push the Frontend image
      - name: Build & Push Frontend image
        run: |
          docker build -f frontend/Dockerfile \
            --build-arg VITE_API_BASE_URL=/api/v1 \
            -t $ECR_REGISTRY/$ECR_FRONTEND_REPOSITORY:$IMAGE_TAG \
            frontend/
          docker push $ECR_REGISTRY/$ECR_FRONTEND_REPOSITORY:$IMAGE_TAG

      # 6. Deploy with Helm
      - name: Deploy with Helm
        run: |
          helm upgrade --install debtflow infra/helm/debtflow \
            -f infra/helm/debtflow/values-staging.yaml \
            --set image.api.repository=$ECR_REGISTRY/$ECR_API_REPOSITORY \
            --set image.api.tag=$IMAGE_TAG \
            --set image.frontend.repository=$ECR_REGISTRY/$ECR_FRONTEND_REPOSITORY \
            --set image.frontend.tag=$IMAGE_TAG \
            --wait --timeout 5m

      # 7. Health check with automatic rollback
      - name: Health check
        run: |
          for i in $(seq 1 5); do
            if curl -sf https://staging.debtflow.example.com/health/; then
              echo "Health check passed"
              exit 0
            fi
            sleep 10
          done
          echo "Health check failed — rolling back"
          helm rollback debtflow
          exit 1
```

**Important points:**
- **OIDC** instead of access keys -- more secure, no static secrets
- **`--wait`** -- Helm waits for pods to become `Ready` before returning
- **Health check with rollback** -- If the deploy fails, automatically rolls back to the previous version

---

## 23. Docker -- Production Images

### API (multi-stage build)

```dockerfile
# docker/Dockerfile

# Stage 1: Install dependencies
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/prod.txt

# Stage 2: Runtime (smaller final image)
FROM python:3.12-slim AS runtime
RUN adduser --disabled-password --no-create-home appuser   # Non-root user!
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin
WORKDIR /app
COPY . .
RUN python manage.py collectstatic --noinput 2>/dev/null || true
USER appuser                                                 # Never runs as root
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')"
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "gthread", \
     "--threads", "2", \
     "--timeout", "120"]
```

### Frontend (multi-stage build)

```dockerfile
# frontend/Dockerfile

# Stage 1: React build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci                           # Install dependencies (deterministic)
COPY . .
ARG VITE_API_BASE_URL=/api/v1       # Build arg injected by CI/CD
RUN npm run build                    # Generates /app/dist/

# Stage 2: Serve with Nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Why multi-stage?**
- The build stage has Node.js, npm, source code -- ~1 GB
- The production stage has only Nginx and static files -- ~30 MB
- Smaller = faster to pull, smaller attack surface

---

## 24. Local Validation

Before deploying, always validate locally:

### Terraform

```bash
cd infra/terraform

# Initialize without backend (S3 not required)
terraform init -backend=false

# Validate syntax and references
terraform validate
# Success! The configuration is valid.

# Check formatting
terraform fmt -check -recursive
# (no output = everything formatted)
```

### Helm

```bash
cd infra/helm

# Lint -- checks for syntax errors and best practices
helm lint debtflow/
# 1 chart(s) linted, 0 chart(s) failed

# Template -- renders manifests without installing
helm template debtflow debtflow/
helm template debtflow debtflow/ -f debtflow/values-staging.yaml
helm template debtflow debtflow/ -f debtflow/values-production.yaml
```

**Tip:** Redirect the `helm template` output to a file and review the generated YAML manifests before deploying.

---

## 25. Complete Deploy Flow

### Step 1: Provision the Infrastructure (one time)

```bash
# Create S3 bucket and DynamoDB for Terraform state (manual bootstrap)
aws s3 mb s3://debtflow-terraform-state
aws dynamodb create-table --table-name debtflow-terraform-lock ...

# Provision staging
cd infra/terraform
terraform init
terraform plan -var-file=staging.tfvars
terraform apply -var-file=staging.tfvars
```

### Step 2: Configure kubectl

```bash
aws eks update-kubeconfig --name debtflow-staging --region us-east-1
kubectl get nodes    # Verify that the nodes are Ready
```

### Step 3: Install AWS Load Balancer Controller

```bash
# Using the role ARN from Terraform output
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=debtflow-staging \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=$(terraform output -raw alb_controller_role_arn)
```

### Step 4: Deploy the Application

```bash
# Build and push images
ECR_URL=$(terraform output -raw ecr_api_repository_url)
docker build -f docker/Dockerfile -t $ECR_URL:v1.0.0 .
docker push $ECR_URL:v1.0.0

# Deploy with Helm
helm upgrade --install debtflow infra/helm/debtflow \
  -f infra/helm/debtflow/values-staging.yaml \
  --set image.api.repository=$ECR_URL \
  --set image.api.tag=v1.0.0 \
  --set database.host=$(terraform output -raw db_endpoint) \
  --set redis.host=$(terraform output -raw redis_endpoint) \
  --wait
```

### Step 5: Verify

```bash
kubectl get pods -l app=debtflow          # All Running?
kubectl get ingress                        # ALB created?
curl https://staging.debtflow.example.com/health/   # Responding?
```

---

## 26. Production Checklist

### Security
- [ ] All secrets are in AWS Secrets Manager (not in Git)
- [ ] RDS is not publicly accessible
- [ ] Security groups restrict traffic by port and CIDR
- [ ] Network policies limit communication between pods
- [ ] Containers run as non-root (USER appuser)
- [ ] IRSA configured (pods have only the necessary permissions)
- [ ] HTTPS required in production (TLS on Ingress)
- [ ] CORS configured for the correct domain

### High Availability
- [ ] RDS Multi-AZ enabled
- [ ] Redis with automatic failover (2 nodes)
- [ ] HPA configured (min 3, max 10 pods)
- [ ] PDB configured (min 2 available)
- [ ] Nodes in 2+ AZs
- [ ] RollingUpdate with maxUnavailable: 0

### Observability
- [ ] Health checks (readiness + liveness) on all deployments
- [ ] Prometheus collecting metrics
- [ ] Grafana with dashboards
- [ ] Sentry configured for error tracking
- [ ] Centralized logs (CloudWatch)

### Backup & Recovery
- [ ] RDS automatic backups (7 days)
- [ ] S3 with versioning
- [ ] Terraform state in S3 with encryption
- [ ] `deletion_protection` enabled in production
- [ ] Helm rollback tested

### CI/CD
- [ ] Automated build on push to main
- [ ] Post-deploy health check with automatic rollback
- [ ] Production deploy requires a version tag (v*.*.*)
- [ ] GitHub Environments with approval gates

---

## Glossary

| Term | Definition |
|------|------------|
| **ALB** | Application Load Balancer -- AWS layer 7 load balancer |
| **ACM** | AWS Certificate Manager -- free SSL/TLS certificates |
| **CIDR** | Classless Inter-Domain Routing -- IP range notation (e.g., 10.0.0.0/16) |
| **ECR** | Elastic Container Registry -- AWS private Docker registry |
| **EKS** | Elastic Kubernetes Service -- AWS managed Kubernetes |
| **HPA** | Horizontal Pod Autoscaler -- automatically scales pods |
| **IRSA** | IAM Roles for Service Accounts -- associates IAM roles with specific pods |
| **NAT** | Network Address Translation -- allows private subnets to access the internet |
| **OIDC** | OpenID Connect -- authentication protocol used by IRSA |
| **PDB** | Pod Disruption Budget -- ensures a minimum number of pods during maintenance |
| **RDS** | Relational Database Service -- AWS managed database |
| **VPC** | Virtual Private Cloud -- isolated private network on AWS |
| **Helm Hook** | A Job that executes at specific moments in the deploy lifecycle |
| **tfvars** | A file containing Terraform variable values for a specific environment |

---

*Document generated as teaching material for the DebtFlow project.*
*Based on a real AWS infrastructure implementation with Terraform + Kubernetes.*
