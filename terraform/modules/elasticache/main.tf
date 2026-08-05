# Data source to retrieve VPC details (including CIDR block)
data "aws_vpc" "current" {
  id = var.vpc_id
}

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "valkey" {
  name        = "${var.environment}-valkey-subnet-group"
  subnet_ids  = var.private_db_subnet_ids
  description = "Subnet group for ElastiCache Valkey cluster in secure private subnets"
}

# ElastiCache Valkey Security Group
resource "aws_security_group" "valkey_sg" {
  name        = "${var.environment}-valkey-sg"
  description = "Security group for ElastiCache Valkey cluster"
  vpc_id      = var.vpc_id

  # Inbound Valkey port (6379) from private ASG compute security group
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [var.asg_sg_id]
    description     = "Allow port 6379 ingress from the private application ASG security group"
  }

  # Inbound Valkey port (6379) from Standalone staging/developer security group (if enabled)
  dynamic "ingress" {
    for_each = var.standalone_sg_id != "" ? [var.standalone_sg_id] : []
    content {
      from_port       = 6379
      to_port         = 6379
      protocol        = "tcp"
      security_groups = [ingress.value]
      description     = "Allow port 6379 ingress from standalone developer/staging security group"
    }
  }

  # Egress restricted for database/cache security (allow only VPC-internal egress)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [data.aws_vpc.current.cidr_block]
    description = "Allow outbound traffic only within the VPC CIDR range"
  }

  tags = {
    Name        = "${var.environment}-valkey-sg"
    Environment = var.environment
  }
}

# ElastiCache Valkey Replication Group (Multi-AZ Ready)
resource "aws_elasticache_replication_group" "valkey" {
  replication_group_id       = "${var.environment}-valkey"
  description                = "Managed ElastiCache Valkey cache cluster"
  node_type                  = var.node_type
  num_cache_clusters         = var.num_cache_clusters
  port                       = 6379
  parameter_group_name       = var.parameter_group_name
  subnet_group_name          = aws_elasticache_subnet_group.valkey.name
  security_group_ids         = [aws_security_group.valkey_sg.id]
  engine                     = "valkey"
  engine_version             = var.engine_version
  automatic_failover_enabled = var.num_cache_clusters > 1 ? true : false
  multi_az_enabled           = var.num_cache_clusters > 1 ? true : false

  # Security Hardening
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  tags = {
    Name        = "${var.environment}-valkey-cluster"
    Environment = var.environment
    Engine      = "valkey"
  }
}
