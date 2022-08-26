variable "aws_region" {
  description = "Default AWS region for all resources."

  type    = string
  default = "eu-west-1"
}

variable "resource_regions" {
  description = "List of AWS regions to scan for finding target resources"

  type = list(any)
}

variable "tags" {
  description = "A map of tags to add to the resources"
  type        = map(string)
  default     = {}
}

variable "rg_sync_event_schedule" {
  description = "CRON or rate expression for scheduling RGTA-Sync Lambda function"

  type    = string
  default = "cron(0 1 ? * SUN *)"
}
