output "redis_endpoint" {
  value     = aws_elasticache_replication_group.main.primary_endpoint_address
  sensitive = true
}

output "redis_port" {
  value = aws_elasticache_replication_group.main.port
}
