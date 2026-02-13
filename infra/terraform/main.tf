module "networking" {
  source = "./modules/networking"

  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
}

module "eks" {
  source = "./modules/eks"

  environment        = var.environment
  cluster_name       = "debtflow-${var.environment}"
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  node_instance_type = var.eks_node_instance_type
  node_min_size      = var.eks_node_min_size
  node_max_size      = var.eks_node_max_size
  node_desired_size  = var.eks_node_desired_size
}

module "database" {
  source = "./modules/database"

  environment        = var.environment
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  instance_class     = var.db_instance_class
  allocated_storage  = var.db_allocated_storage
  db_name            = "debtflow"
  db_password        = module.secrets.db_password
  security_group_ids = [module.networking.db_security_group_id]
}

module "cache" {
  source = "./modules/cache"

  environment        = var.environment
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  node_type          = var.cache_node_type
  security_group_ids = [module.networking.cache_security_group_id]
}

module "storage" {
  source = "./modules/storage"

  environment = var.environment
  bucket_name = "debtflow-files-${var.environment}"
}

module "ecr" {
  source = "./modules/ecr"

  environment = var.environment
}

module "iam" {
  source = "./modules/iam"

  environment       = var.environment
  aws_region        = var.aws_region
  oidc_provider_arn = module.eks.oidc_provider_arn
  oidc_provider_url = module.eks.oidc_provider_url
  namespace         = var.eks_namespace
  s3_bucket_arn     = module.storage.bucket_arn
}

module "secrets" {
  source = "./modules/secrets"

  environment = var.environment
  db_endpoint = module.database.db_endpoint
}

module "dns" {
  source = "./modules/dns"
  count  = var.create_dns ? 1 : 0

  environment = var.environment
  domain_name = var.domain_name
}
