# Introduction

TF Lambda Resource Sync module is a helper module for optimizing cost of AWS cloud resources. The Terraform code provisions the necessary infrastructure to run the below AWS Lambda functions written in Python `3.7.x`.


*   *`AWS-Cost-Optimization-ResourceGroupsTaggingAPI-Sync`* - This Lambda function provides the following capabilities:

    *   Pulls the information of the environments provisioned with specific tags from the AWS Resource Groups Tagging API and stores them in an AWS DynamoDB table. The primary key in the DynamoDB table is the name of the environment. The sort key in this table is the creator of the environment.
    *   Deletes the old table, re-creates a new table with the same name and populates it with the latest information fetched from the Resource Groups Tagging API. Each item of this table represents an environment with a complete list of the resources and their details.


## Running AWS Lambda Function

To run the AWS Lambda function in a different time, update the cron schedule for the following entries in the local `terraform.tfvars` file:

*   `rg_sync_event_schedule`


!!! important
    Make sure that the cron job schedule expression is compliant with [AWS guidelines](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html).
