variable "vpc_id" {
  description = "The ID of the VPC"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "http_port" {
  description = "HTTP Port"
  type        = number
  default     = 80
}

variable "db_port" {
  description = "Database connection port"
  type        = number
  default     = 3306 # Default for MySQL
}

variable "http_ingress_cidr_blocks" {
  description = "List of allowed IPv4 CIDR blocks for HTTP ingress on the ALB"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "http_ingress_ipv6_cidr_blocks" {
  description = "List of allowed IPv6 CIDR blocks for HTTP ingress on the ALB"
  type        = list(string)
  default     = []
}
