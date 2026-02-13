variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "instance_class" {
  type    = string
  default = "db.t3.medium"
}

variable "allocated_storage" {
  type    = number
  default = 20
}

variable "db_name" {
  type    = string
  default = "debtflow"
}

variable "db_password" {
  type      = string
  sensitive = true
  default   = "changeme"
}

variable "security_group_ids" {
  type = list(string)
}
