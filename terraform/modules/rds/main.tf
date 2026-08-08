# DB Subnet Group (associates RDS with our private database subnets)
resource "aws_db_subnet_group" "main" {
  name        = "${var.environment}-db-subnet-group"
  description = "Database subnet group for 3-tier architecture"
  subnet_ids  = var.private_db_subnet_ids

  tags = {
    Name        = "${var.environment}-db-subnet-group"
    Environment = var.environment
  }
}

# Parameter Group for custom configuration tuning if needed
resource "aws_db_parameter_group" "main" {
  name   = "${var.environment}-db-parameter-group"
  family = var.db_engine == "postgres" ? "postgres${split(".", var.db_engine_version)[0]}" : (
    var.db_engine == "mariadb" ? "mariadb${var.db_engine_version}" : "mysql8.0"
  )

  parameter {
    name  = var.db_engine == "postgres" ? "log_connections" : "max_connections"
    value = var.db_engine == "postgres" ? "1" : "100"
  }

  tags = {
    Name        = "${var.environment}-db-parameter-group"
    Environment = var.environment
  }
}

# RDS Multi-AZ Database Instance
resource "aws_db_instance" "main" {
  identifier                  = "${var.environment}-database"
  engine                      = var.db_engine
  engine_version              = var.db_engine_version
  instance_class              = var.db_instance_class
  allocated_storage           = var.db_allocated_storage
  max_allocated_storage       = var.db_max_allocated_storage
  storage_type                = "gp3"
  db_name                     = var.db_name
  username                    = var.db_username
  password                    = var.db_password
  port                        = var.db_port
  multi_az                    = var.multi_az
  db_subnet_group_name        = aws_db_subnet_group.main.name
  vpc_security_group_ids      = [var.db_sg_id]
  parameter_group_name        = aws_db_parameter_group.main.name
  allow_major_version_upgrade = false
  auto_minor_version_upgrade  = true
  publicly_accessible         = false
  storage_encrypted           = true
  skip_final_snapshot         = true # Change to false for production use cases with a final_snapshot_identifier

  tags = {
    Name        = "${var.environment}-database"
    Environment = var.environment
  }
}
