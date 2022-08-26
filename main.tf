## Create necessary Infrastructure for deploying Lambda

## DynamoDB Table
resource "aws_dynamodb_table" "aws_cost_optimization" {
  name         = "AWSCostOptimization"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "EnvironmentName"
  range_key    = "Creator"

  attribute {
    name = "Creator"
    type = "S"
  }

  attribute {
    name = "EnvironmentName"
    type = "S"
  }

  tags = var.tags
}


## S3 Bucket
resource "random_pet" "lambda_bucket_name" {
  prefix = "aws-cost-optimization"
  length = 4
}

resource "aws_s3_bucket" "lambda_bucket" {
  bucket = random_pet.lambda_bucket_name.id

  acl           = "private"
  force_destroy = true

  tags = var.tags
}


resource "aws_iam_policy" "policy_lambda_exec_01" {
  name = "aws-cost-optimization-lambda-exec-01"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "tag:GetResources",
          "tag:GetTagValues",  
          "cloudformation:ListStackResources",
          "cloudformation:DescribeStacks",        
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",                 
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = ["dynamodb:BatchGetItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchWriteItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DescribeTable",
          "dynamodb:CreateTable",
          "dynamodb:DeleteTable",
        ]
        Effect   = "Allow"
        Resource = "${aws_dynamodb_table.aws_cost_optimization.arn}"
      },
      {
        "Sid" : "ListObjectsInBucket",
        "Effect" : "Allow",
        "Action" : ["s3:ListBucket"],
        "Resource" : "${aws_s3_bucket.lambda_bucket.arn}"
      },
      {
        "Sid" : "AllObjectActions",
        "Effect" : "Allow",
        "Action" : ["s3:*Object"],
        "Resource" : "${aws_s3_bucket.lambda_bucket.arn}/*"
      },
    ]
  })

  tags = var.tags
}

resource "aws_iam_role" "lambda_exec" {
  name = "ms360_aws_cost_optimisation_lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Sid    = ""
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      }
    ]
  })

  managed_policy_arns = [aws_iam_policy.policy_lambda_exec_01.arn, ]

  tags = var.tags
}


# RGTA-Sync Lambda Fn and supporting inf
data "archive_file" "lambda_rgta_sync" {
  type = "zip"

  source_dir  = "${path.module}/lambda/rgta-sync"
  output_path = "${path.module}/lambda/rgta-sync.zip"
}

resource "aws_s3_bucket_object" "lambda_rgta_sync" {
  bucket = aws_s3_bucket.lambda_bucket.id

  key    = "rgta-sync.zip"
  source = data.archive_file.lambda_rgta_sync.output_path

  etag = filemd5(data.archive_file.lambda_rgta_sync.output_path)

  tags = var.tags
}

resource "aws_lambda_function" "rgta_sync" {
  function_name = "AWS-Cost-Optimization-ResourceGroupsTaggingAPI-Sync"

  s3_bucket = aws_s3_bucket.lambda_bucket.id
  s3_key    = aws_s3_bucket_object.lambda_rgta_sync.key

  runtime = "python3.7"
  handler = "lambda_function.lambda_handler"

  source_code_hash = data.archive_file.lambda_rgta_sync.output_base64sha256

  role = aws_iam_role.lambda_exec.arn

  timeout = 900 # set to max value

  environment {
    variables = {
      "COST_REPORT_S3_BUCKET_NAME" = aws_s3_bucket.lambda_bucket.id,
      "COST_REPORT_DDB_TABLE_NAME" = aws_dynamodb_table.aws_cost_optimization.name,
      "COST_REPORT_RESOURCE_REGIONS" = jsonencode(var.resource_regions)
    }
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "rgta_sync" {
  name = "/aws/lambda/${aws_lambda_function.rgta_sync.function_name}"

  retention_in_days = 30

  tags = var.tags
}

#####  Scheduled Tasks #####
## Add Scheduled Tasks for RGTA-Sync lambda functions
resource "aws_cloudwatch_event_rule" "rgta_sync_event" {
  name                = "rgta-sync-event"
  description         = "Cost Optimization RGTA Sync Lambda - Fires at a given time"
  schedule_expression = var.rgta_sync_event_schedule
}

resource "aws_cloudwatch_event_target" "run_rgta_sync" {
    rule = aws_cloudwatch_event_rule.rgta_sync_event.name
    target_id = "rgta_sync"
    arn = aws_lambda_function.rgta_sync.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_rg_sync" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rgta_sync.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.rgta_sync_event.arn
}
