resource "random_password" "db_password" {
  length  = 32
  special = false
}

resource "random_password" "django_secret_key" {
  length  = 50
  special = true
}

resource "aws_secretsmanager_secret" "database" {
  name        = "debtflow/${var.environment}/database"
  description = "DebtFlow database credentials (${var.environment})"

  tags = { Name = "debtflow-${var.environment}-db-secret" }
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

resource "aws_secretsmanager_secret" "django" {
  name        = "debtflow/${var.environment}/django"
  description = "DebtFlow Django secret key (${var.environment})"

  tags = { Name = "debtflow-${var.environment}-django-secret" }
}

resource "aws_secretsmanager_secret_version" "django" {
  secret_id = aws_secretsmanager_secret.django.id
  secret_string = jsonencode({
    secret_key = random_password.django_secret_key.result
  })
}

resource "aws_secretsmanager_secret" "stripe" {
  name        = "debtflow/${var.environment}/stripe"
  description = "DebtFlow Stripe credentials (${var.environment})"

  tags = { Name = "debtflow-${var.environment}-stripe-secret" }
}

resource "aws_secretsmanager_secret_version" "stripe" {
  secret_id = aws_secretsmanager_secret.stripe.id
  secret_string = jsonencode({
    api_key        = "sk_test_changeme"
    webhook_secret = "whsec_changeme"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "aws_secretsmanager_secret" "sftp" {
  name        = "debtflow/${var.environment}/sftp"
  description = "DebtFlow SFTP credentials (${var.environment})"

  tags = { Name = "debtflow-${var.environment}-sftp-secret" }
}

resource "aws_secretsmanager_secret_version" "sftp" {
  secret_id = aws_secretsmanager_secret.sftp.id
  secret_string = jsonencode({
    user     = "sftpuser"
    password = "changeme"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}
