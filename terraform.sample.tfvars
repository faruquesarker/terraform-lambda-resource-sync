# Sample configuration file
# Copy this file contents to terraform.tfvars and change as appropriate

# Region and Profile Information
aws_region = "eu-west-1"

# Common tags
tags = {
  Owner          = "owner-01"
  EnvironmentName    = "aws-cost-report"
}

# EventBridge event schedules automatic Lambda fn invocation
rgta_sync_event_schedule = "cron(0 1 * * ? *)"

# AWS Regions to scan for finding resources
resource_regions = [ "eu-west-1", "eu-west-2" ]