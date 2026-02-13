variable "environment" {
  type = string
}

variable "db_endpoint" {
  description = "RDS endpoint for database secret"
  type        = string
  default     = ""
}
