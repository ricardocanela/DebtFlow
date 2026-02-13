resource "aws_elasticache_subnet_group" "main" {
  name       = "debtflow-${var.environment}"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "debtflow-${var.environment}"
  description          = "DebtFlow Redis cluster (${var.environment})"

  node_type            = var.node_type
  num_cache_clusters   = var.environment == "production" ? 2 : 1
  engine               = "redis"
  engine_version       = "7.0"
  port                 = 6379
  parameter_group_name = "default.redis7"

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = var.security_group_ids

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  automatic_failover_enabled = var.environment == "production"

  tags = { Name = "debtflow-${var.environment}-redis" }
}
