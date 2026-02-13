output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
  sensitive   = true
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "db_endpoint" {
  description = "RDS endpoint"
  value       = module.database.db_endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "ElastiCache endpoint"
  value       = module.cache.redis_endpoint
  sensitive   = true
}

output "s3_bucket_name" {
  description = "S3 bucket for SFTP files"
  value       = module.storage.bucket_name
}

output "ecr_api_repository_url" {
  description = "ECR repository URL for API image"
  value       = module.ecr.api_repository_url
}

output "ecr_frontend_repository_url" {
  description = "ECR repository URL for frontend image"
  value       = module.ecr.frontend_repository_url
}

output "worker_role_arn" {
  description = "IAM role ARN for Celery worker service account"
  value       = module.iam.worker_role_arn
}

output "api_role_arn" {
  description = "IAM role ARN for API service account"
  value       = module.iam.api_role_arn
}

output "alb_controller_role_arn" {
  description = "IAM role ARN for AWS Load Balancer Controller"
  value       = module.iam.alb_controller_role_arn
}

output "acm_certificate_arn" {
  description = "ACM certificate ARN (if DNS enabled)"
  value       = var.create_dns ? module.dns[0].certificate_arn : null
}
