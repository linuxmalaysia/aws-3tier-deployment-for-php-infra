variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "The ID of the VPC"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of IDs of public subnets"
  type        = list(string)
}

variable "alb_sg_id" {
  description = "The ID of the ALB Security Group"
  type        = string
}

variable "http_port" {
  description = "HTTP Port"
  type        = number
  default     = 80
}

variable "certificate_arn" {
  description = "The ARN of the ACM SSL/TLS certificate for the HTTPS listener"
  type        = string
}
