resource "aws_db_subnet_group" "main" {
  name       = "debtflow-${var.environment}"
  subnet_ids = var.private_subnet_ids

  tags = { Name = "debtflow-${var.environment}-db-subnet" }
}

resource "aws_db_parameter_group" "main" {
  name   = "debtflow-${var.environment}-pg16"
  family = "postgres16"

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  parameter {
    name  = "pg_stat_statements.track"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }
}

resource "aws_db_instance" "main" {
  identifier     = "debtflow-${var.environment}"
  engine         = "postgres"
  engine_version = "16"
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.allocated_storage * 4
  storage_encrypted     = true

  db_name  = var.db_name
  username = "debtflow"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = var.security_group_ids
  parameter_group_name   = aws_db_parameter_group.main.name

  multi_az            = var.environment == "production"
  publicly_accessible = false

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  skip_final_snapshot       = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "debtflow-final-${var.environment}" : null
  deletion_protection       = var.environment == "production"

  tags = { Name = "debtflow-${var.environment}-db" }
}
