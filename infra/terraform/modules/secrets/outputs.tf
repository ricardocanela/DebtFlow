output "db_password" {
  value     = random_password.db_password.result
  sensitive = true
}

output "django_secret_key" {
  value     = random_password.django_secret_key.result
  sensitive = true
}

output "database_secret_arn" {
  value = aws_secretsmanager_secret.database.arn
}

output "django_secret_arn" {
  value = aws_secretsmanager_secret.django.arn
}

output "stripe_secret_arn" {
  value = aws_secretsmanager_secret.stripe.arn
}

output "sftp_secret_arn" {
  value = aws_secretsmanager_secret.sftp.arn
}
