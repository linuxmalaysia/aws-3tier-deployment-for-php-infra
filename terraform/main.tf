# VPC Module Setup
module "vpc" {
  source = "./modules/vpc"

  vpc_cidr                 = var.vpc_cidr
  environment              = var.environment
  public_subnet_cidrs      = var.public_subnet_cidrs
  private_app_subnet_cidrs = var.private_app_subnet_cidrs
  private_db_subnet_cidrs  = var.private_db_subnet_cidrs
  availability_zones       = var.availability_zones
}

# Security Groups Setup
module "security_groups" {
  source = "./modules/security_groups"

  vpc_id                        = module.vpc.vpc_id
  environment                   = var.environment
  http_port                     = var.http_port
  db_port                       = var.db_port
  http_ingress_cidr_blocks      = var.http_ingress_cidr_blocks
  http_ingress_ipv6_cidr_blocks = var.http_ingress_ipv6_cidr_blocks
}

# Application Load Balancer (ALB) Setup
module "alb" {
  source = "./modules/alb"

  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  alb_sg_id         = module.security_groups.alb_sg_id
  http_port         = var.http_port
  certificate_arn   = var.certificate_arn
}

# Web Application Firewall (WAF) Setup
module "waf" {
  source = "./modules/waf"

  environment = var.environment
  alb_arn     = module.alb.alb_arn
  rate_limit  = var.waf_rate_limit
}

# Auto Scaling Group (ASG) Setup
module "asg" {
  source = "./modules/asg"

  environment            = var.environment
  private_app_subnet_ids = module.vpc.private_app_subnet_ids
  asg_sg_id              = module.security_groups.asg_sg_id
  target_group_arn       = module.alb.target_group_arn
  min_size               = var.min_size
  max_size               = var.max_size
  desired_capacity       = var.desired_capacity
  instance_type          = var.instance_type
  ami_id                 = var.ami_id
}

# Relational Database Service (RDS) Setup
module "rds" {
  source = "./modules/rds"

  environment           = var.environment
  private_db_subnet_ids = module.vpc.private_db_subnet_ids
  db_sg_id              = module.security_groups.db_sg_id
  db_engine             = var.db_engine
  db_engine_version     = var.db_engine_version
  db_instance_class     = var.db_instance_class
  db_name               = var.db_name
  db_username           = var.db_username
  db_password           = var.db_password
  db_port               = var.db_port
}

# Standalone EC2 Instances Module Setup
module "standalone_ec2" {
  count  = var.enable_standalone_ec2 ? 1 : 0
  source = "./modules/standalone_ec2"

  environment            = var.environment
  vpc_id                 = module.vpc.vpc_id
  private_app_subnet_ids = module.vpc.private_app_subnet_ids
  alb_sg_id              = module.security_groups.alb_sg_id
  instance_type          = var.standalone_ec2_instance_type
  instance_count         = var.standalone_ec2_count
  ami_id                 = var.standalone_ec2_ami_id
  ubuntu_ami_filter_name = var.standalone_ubuntu_ami_filter_name
}

# Secure SSH Jumphost (Bastion) Setup (Conditional Setup)
module "jumphost" {
  count  = var.enable_jumphost ? 1 : 0
  source = "./modules/jumphost"

  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  instance_type     = var.jumphost_instance_type
  allowed_ssh_cidr  = var.jumphost_allowed_ssh_cidr
  jumphost_os       = var.jumphost_os
  ami_id            = var.jumphost_ami_id
  asg_sg_id         = module.security_groups.asg_sg_id
  standalone_sg_id  = try(module.standalone_ec2[0].security_group_id, "")
}

# ElastiCache Valkey Setup (Conditional Setup)
module "elasticache_valkey" {
  count  = var.enable_elasticache_valkey ? 1 : 0
  source = "./modules/elasticache"

  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  private_db_subnet_ids = module.vpc.private_db_subnet_ids
  asg_sg_id             = module.security_groups.asg_sg_id
  standalone_sg_id      = try(module.standalone_ec2[0].security_group_id, "")
  node_type             = var.valkey_node_type
  num_cache_clusters    = var.valkey_num_cache_clusters
  engine_version        = var.valkey_engine_version
  parameter_group_name  = var.valkey_parameter_group_name
}

# Route 53 Module Setup (Conditional Setup)
module "route53" {
  count  = var.enable_route53 ? 1 : 0
  source = "./modules/route53"

  environment  = var.environment
  domain_name  = var.domain_name
  subdomain    = var.subdomain
  alb_dns_name = module.alb.alb_dns_name
  alb_zone_id  = module.alb.alb_zone_id
}
