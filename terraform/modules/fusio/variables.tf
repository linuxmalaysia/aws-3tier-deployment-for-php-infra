variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "The ID of the VPC"
  type        = string
}

variable "private_app_subnet_ids" {
  description = "List of private subnets for application placement"
  type        = list(string)
}

variable "alb_sg_id" {
  description = "The ID of the ALB Security Group"
  type        = string
}

variable "db_sg_id" {
  description = "The ID of the Database Security Group"
  type        = string
}

variable "https_listener_arn" {
  description = "The ARN of the ALB HTTPS Listener"
  type        = string
}

variable "instance_type" {
  description = "Instance type for ASG instances"
  type        = string
  default     = "t4g.micro"
}

variable "min_size" {
  description = "Minimum size of the ASG"
  type        = number
  default     = 2
}

variable "max_size" {
  description = "Maximum size of the ASG"
  type        = number
  default     = 4
}

variable "desired_capacity" {
  description = "Desired size of the ASG"
  type        = number
  default     = 2
}

variable "enable_standalone" {
  description = "Whether to enable the standalone EC2 instance for development/staging"
  type        = bool
  default     = true
}

variable "standalone_instance_type" {
  description = "Instance type for the standalone instance"
  type        = string
  default     = "t4g.micro"
}

variable "db_port" {
  description = "Database connection port"
  type        = number
  default     = 3306
}

variable "ami_id" {
  description = "AMI ID to use for launch template (optional)"
  type        = string
  default     = ""
}

variable "ubuntu_ami_filter_name" {
  description = "AMI search filter for Ubuntu Noble Server"
  type        = string
  default     = "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-*-server-*"
}
