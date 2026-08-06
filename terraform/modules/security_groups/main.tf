# ALB Security Group (Internet facing - receives traffic from external users, potentially protected by WAF)
resource "aws_security_group" "alb_sg" {
  name        = "${var.environment}-alb-sg"
  description = "Security group for application load balancer"
  vpc_id      = var.vpc_id

  # Inbound HTTP (port 80) restricted to internal networks / CloudFront only
  ingress {
    from_port        = var.http_port
    to_port          = var.http_port
    protocol         = "tcp"
    cidr_blocks      = var.http_ingress_cidr_blocks
    ipv6_cidr_blocks = var.http_ingress_ipv6_cidr_blocks
  }

  # Inbound HTTPS (port 443) from anywhere
  ingress {
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  # Outbound rule to application servers only
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.environment}-alb-sg"
    Environment = var.environment
  }
}

# ASG/EC2 Security Group (Only accepts traffic from the ALB SG)
resource "aws_security_group" "asg_sg" {
  name        = "${var.environment}-asg-sg"
  description = "Security group for Auto Scaling Group instances"
  vpc_id      = var.vpc_id

  # Inbound TCP from the ALB SG only
  ingress {
    from_port       = var.http_port
    to_port         = var.http_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  # Allow egress to internet for package updates/downloads
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.environment}-asg-sg"
    Environment = var.environment
  }
}

# Database Security Group (Only accepts traffic from the ASG SG)
resource "aws_security_group" "db_sg" {
  name        = "${var.environment}-db-sg"
  description = "Security group for database layer"
  vpc_id      = var.vpc_id

  # Inbound database connections only from private ASG security group
  ingress {
    from_port       = var.db_port
    to_port         = var.db_port
    protocol        = "tcp"
    security_groups = [aws_security_group.asg_sg.id]
  }

  # Egress restricted for database security
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.environment}-db-sg"
    Environment = var.environment
  }
}
