locals {
  is_arm64 = length(regexall("^[a-z]+[0-9]g[a-z]*\\.", var.instance_type)) > 0
  selected_ami_id = var.ami_id != "" ? var.ami_id : (
    var.jumphost_os == "ubuntu" ? one(data.aws_ami.ubuntu[*].id) : one(data.aws_ami.amazon_linux[*].id)
  )
}

# Fetch Canonical Ubuntu Server AMI based on architecture
data "aws_ami" "ubuntu" {
  count       = var.jumphost_os == "ubuntu" && var.ami_id == "" ? 1 : 0
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = [var.ubuntu_ami_filter_name]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = [local.is_arm64 ? "arm64" : "x86_64"]
  }
}

# Fetch Amazon Linux 2023 AMI based on architecture
data "aws_ami" "amazon_linux" {
  count       = var.jumphost_os == "amazon-linux-2023" && var.ami_id == "" ? 1 : 0
  most_recent = true
  owners      = ["137112412989"] # Amazon

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-${local.is_arm64 ? "arm64" : "x86_64"}"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Jumphost Security Group
resource "aws_security_group" "jumphost_sg" {
  name        = "${var.environment}-jumphost-sg"
  description = "Security group for secure SSH Jumphost / Bastion"
  vpc_id      = var.vpc_id

  # Inbound SSH restricted strictly to allowed office IP CIDR
  ingress {
    description = "SSH ingress restricted to Cyberjaya office"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  # Outbound access for packages updates and SSH proxying
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "${var.environment}-jumphost-sg"
    Environment = var.environment
  }
}

# Ingress SSH Rules attached to the Private SGs (ASG and Standalone EC2)
# These allow SSH connections originating ONLY from the Jumphost SG.

resource "aws_security_group_rule" "ssh_to_asg" {
  type                     = "ingress"
  description              = "Allow SSH from Jumphost"
  from_port                = 22
  to_port                  = 22
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.jumphost_sg.id
  security_group_id        = var.asg_sg_id
}

resource "aws_security_group_rule" "ssh_to_standalone" {
  count                    = var.standalone_sg_id != "" ? 1 : 0
  type                     = "ingress"
  description              = "Allow SSH from Jumphost"
  from_port                = 22
  to_port                  = 22
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.jumphost_sg.id
  security_group_id        = var.standalone_sg_id
}

# IAM Role for Jumphost (Supports SSM Session Manager as a secure backup)
resource "aws_iam_role" "jumphost_role" {
  name = "${var.environment}-jumphost-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.jumphost_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "jumphost_profile" {
  name = "${var.environment}-jumphost-profile"
  role = aws_iam_role.jumphost_role.name
}

# Secure Jumphost EC2 Instance in the first public subnet
resource "aws_instance" "jumphost" {
  ami           = local.selected_ami_id
  instance_type = var.instance_type

  subnet_id = var.public_subnet_ids[0]

  vpc_security_group_ids = [aws_security_group.jumphost_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.jumphost_profile.name

  # Enable detailed monitoring for staging audit compatibility
  monitoring = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 15
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name        = "${var.environment}-jumphost"
    Environment = var.environment
    OS          = var.jumphost_os == "ubuntu" ? "Ubuntu-24.04-LTS" : "Amazon-Linux-2023"
    Hardened    = "ASIMP-Compliant"
  }

  lifecycle {
    ignore_changes = [ami]
  }
}

# Static Elastic IP for the SSH Jumphost
resource "aws_eip" "jumphost_eip" {
  domain = "vpc"

  tags = {
    Name        = "${var.environment}-jumphost-eip"
    Environment = var.environment
  }
}

resource "aws_eip_association" "jumphost_assoc" {
  instance_id   = aws_instance.jumphost.id
  allocation_id = aws_eip.jumphost_eip.id
}
