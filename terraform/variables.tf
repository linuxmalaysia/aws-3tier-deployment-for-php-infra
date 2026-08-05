variable "aws_region" {
  description = "AWS region where resources will be deployed"
  type        = string
  default     = "ap-southeast-5"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "List of CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_app_subnet_cidrs" {
  description = "List of CIDR blocks for private app subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "private_db_subnet_cidrs" {
  description = "List of CIDR blocks for private database subnets"
  type        = list(string)
  default     = ["10.0.20.0/24", "10.0.21.0/24"]
}

variable "availability_zones" {
  description = "Availability Zones to deploy subnets"
  type        = list(string)
  default     = ["ap-southeast-5a", "ap-southeast-5b"]
}

variable "http_port" {
  description = "Port to expose the application"
  type        = number
  default     = 80
}

variable "db_port" {
  description = "Port to connect to the database"
  type        = number
  default     = 5432
}

variable "db_engine" {
  description = "RDS engine (e.g., mysql, postgres)"
  type        = string
  default     = "postgres"
}

variable "db_engine_version" {
  description = "RDS engine version"
  type        = string
  default     = "16"
}

variable "db_instance_class" {
  description = "RDS instance size (e.g., 'db.t4g.micro' for testing, 'db.m6g.large' [2 vCPU, 8GB] for baseline production, or 'db.m6g.xlarge' [4 vCPU, 16GB] to match developer server specifications)"
  type        = string
  default     = "db.t4g.micro"
}

variable "db_name" {
  description = "The database name"
  type        = string
  default     = "appdb"
}

variable "db_username" {
  description = "The database administrator username"
  type        = string
  default     = "dbadmin"
}

variable "db_password" {
  description = "The database administrator password"
  type        = string
  sensitive   = true
}

variable "instance_type" {
  description = "Instance type for ASG instances (e.g., 't4g.medium' [2 vCPU, 4GB] for baseline, or 't4g.xlarge' [4 vCPU, 16GB] / 'm6g.xlarge' [4 vCPU, 16GB] to match developer server specifications)"
  type        = string
  default     = "t4g.micro"
}

variable "ami_id" {
  description = "AMI ID to use for the launch template in ap-southeast-5"
  type        = string
  default     = ""
}

variable "min_size" {
  description = "Minimum size of the ASG"
  type        = number
  default     = 2
}

variable "max_size" {
  description = "Maximum size of the ASG"
  type        = number
  default     = 6
}

variable "desired_capacity" {
  description = "Desired size of the ASG"
  type        = number
  default     = 2
}

variable "waf_rate_limit" {
  description = "WAF IP rate limit value (requests per 5 minutes)"
  type        = number
  default     = 2000
}

# --- Standalone EC2 Instance Variables ---
variable "enable_standalone_ec2" {
  description = "Whether to enable the standalone EC2 instances for development/application requirements"
  type        = bool
  default     = true
}

variable "standalone_ec2_instance_type" {
  description = "The instance type to use for standalone EC2 instances (typically Graviton e.g., t4g.micro)"
  type        = string
  default     = "t4g.micro"
}

variable "standalone_ec2_count" {
  description = "The number of standalone EC2 instances to provision"
  type        = number
  default     = 1
}

variable "standalone_ec2_ami_id" {
  description = "Optional AMI ID to override standard Ubuntu AMI lookup for standalone instances"
  type        = string
  default     = ""
}

variable "standalone_ubuntu_ami_filter_name" {
  description = "Search filter pattern for the Ubuntu AMI name (allows switching between 24.04 and 26.04)"
  type        = string
  default     = "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-*-server-*"
}

# --- Route 53 Variables ---
variable "enable_route53" {
  description = "Whether to enable Route 53 domain management and create an alias record for the ALB"
  type        = bool
  default     = true
}

variable "domain_name" {
  description = "The custom root domain name (e.g., linuxmalaysia.com)"
  type        = string
  default     = "linuxmalaysia.com"
}

variable "subdomain" {
  description = "The subdomain to point to the ALB (e.g., app). If empty, points to the root domain."
  type        = string
  default     = "app"
}

# --- ElastiCache Valkey Variables ---
variable "enable_elasticache_valkey" {
  description = "Whether to enable the secure, multi-AZ ElastiCache Valkey caching cluster"
  type        = bool
  default     = true
}

variable "valkey_node_type" {
  description = "The instance type of the ElastiCache Valkey cache nodes (typically Graviton e.g., cache.t4g.micro)"
  type        = string
  default     = "cache.t4g.micro"
}

variable "valkey_num_cache_clusters" {
  description = "Number of cache clusters (nodes) in the replication group"
  type        = number
  default     = 1
}

variable "valkey_engine_version" {
  description = "The engine version for ElastiCache Valkey"
  type        = string
  default     = "7.2"
}

variable "valkey_parameter_group_name" {
  description = "The name of the parameter group to associate with Valkey"
  type        = string
  default     = "default.valkey7"
}

# --- Jumphost Variables ---
variable "enable_jumphost" {
  description = "Whether to enable the secure, hardened SSH Jumphost (Bastion)"
  type        = bool
  default     = true
}

variable "jumphost_instance_type" {
  description = "The instance type to use for the Jumphost (typically Graviton e.g., t4g.micro)"
  type        = string
  default     = "t4g.micro"
}

variable "jumphost_os" {
  description = "The operating system of the Jumphost ('ubuntu' or 'amazon-linux-2023')"
  type        = string
  default     = "ubuntu" # Recommended for ASIMP OS hardening compatibility
}

variable "jumphost_allowed_ssh_cidr" {
  description = "IP CIDR allowed to connect to the Jumphost via SSH (e.g., Cyberjaya office public IP)"
  type        = string
  default     = "103.188.0.0/16" # Default dummy representing Cyberjaya ISP subnet
}

variable "jumphost_ami_id" {
  description = "Optional specific AMI ID override for the Jumphost"
  type        = string
  default     = ""
}
