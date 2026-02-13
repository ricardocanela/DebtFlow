module "networking" {
  source = "./modules/networking"

  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
}

module "eks" {
  source = "./modules/eks"

  environment         = var.environment
  cluster_name        = "debtflow-${var.environment}"
  vpc_id              = module.networking.vpc_id
  private_subnet_ids  = module.networking.private_subnet_ids
  node_instance_type  = var.eks_node_instance_type
  node_min_size       = var.eks_node_min_size
  node_max_size       = var.eks_node_max_size
  node_desired_size   = var.eks_node_desired_size
}

module "database" {
  source = "./modules/database"

  environment        = var.environment
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  instance_class     = var.db_instance_class
  allocated_storage  = var.db_allocated_storage
  db_name            = "debtflow"
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
