output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "alb_dns_name" {
  description = "The public-facing DNS name of the Application Load Balancer protected by WAF"
  value       = module.alb.alb_dns_name
}

output "rds_endpoint" {
  description = "The connection endpoint for the private RDS database"
  value       = module.rds.db_instance_endpoint
}

output "asg_name" {
  description = "The name of the application Auto Scaling Group"
  value       = module.asg.asg_name
}

output "waf_web_acl_arn" {
  description = "The ARN of the protecting WAFv2 Web ACL"
  value       = module.waf.web_acl_arn
}

output "standalone_ec2_instance_ids" {
  description = "The IDs of the generated standalone EC2 instances"
  value       = try(module.standalone_ec2[0].instance_ids, [])
}

output "standalone_ec2_private_ips" {
  description = "The private IP addresses assigned to the standalone EC2 instances"
  value       = try(module.standalone_ec2[0].private_ips, [])
}

output "standalone_ec2_security_group_id" {
  description = "The security group ID assigned to the standalone instances"
  value       = try(module.standalone_ec2[0].security_group_id, "")
}

output "route53_hosted_zone_id" {
  description = "The Route 53 Hosted Zone ID"
  value       = try(module.route53[0].hosted_zone_id, "")
}

output "route53_name_servers" {
  description = "The list of Name Servers assigned to the Route 53 Hosted Zone"
  value       = try(module.route53[0].name_servers, [])
}

output "route53_fqdn" {
  description = "The FQDN created in Route 53 pointing to the ALB"
  value       = try(module.route53[0].fqdn, "")
}

output "valkey_primary_endpoint" {
  description = "The primary connection endpoint of the secure ElastiCache Valkey cluster"
  value       = try(module.elasticache_valkey[0].primary_endpoint_address, "")
}

output "valkey_security_group_id" {
  description = "The ID of the security group assigned to the Valkey cluster"
  value       = try(module.elasticache_valkey[0].security_group_id, "")
}

output "jumphost_public_ip" {
  description = "The static Elastic IP address assigned to the secure SSH Jumphost"
  value       = try(module.jumphost[0].jumphost_public_ip, "")
}

output "jumphost_private_ip" {
  description = "The private IP address of the secure SSH Jumphost within the VPC"
  value       = try(module.jumphost[0].jumphost_private_ip, "")
}

output "jumphost_security_group_id" {
  description = "The security group ID assigned to the secure SSH Jumphost"
  value       = try(module.jumphost[0].security_group_id, "")
}

output "fusio_asg_name" {
  description = "The name of the Fusio API Server Auto Scaling Group"
  value       = module.fusio.asg_name
}

output "fusio_standalone_instance_id" {
  description = "The ID of the Fusio Standalone Dev EC2 instance"
  value       = module.fusio.standalone_instance_id
}
