output "asg_name" {
  description = "The name of the Fusio API Server Auto Scaling Group"
  value       = aws_autoscaling_group.fusio_asg.name
}

output "standalone_instance_id" {
  description = "The ID of the Fusio Standalone Dev EC2 instance"
  value       = try(aws_instance.fusio_standalone[0].id, "")
}
