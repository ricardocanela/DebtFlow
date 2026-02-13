variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "oidc_provider_arn" {
  description = "EKS OIDC provider ARN for IRSA"
  type        = string
}

variable "oidc_provider_url" {
  description = "EKS OIDC provider URL"
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace for DebtFlow workloads"
  type        = string
  default     = "debtflow"
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket for file storage"
  type        = string
}
