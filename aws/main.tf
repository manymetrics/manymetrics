data "aws_region" "current" {}

resource "random_string" "random" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_kinesis_stream" "this" {
  name        = "manymetrics-stream-${random_string.random.result}"
  stream_mode_details {
    stream_mode = "ON_DEMAND"
  }
}

resource "aws_api_gateway_rest_api" "this" {
  name = "manymetrics-api-${random_string.random.result}"
}

resource "aws_iam_role" "this" {
  name = "manymetrics-role-${random_string.random.result}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
        Effect = "Allow"
      },
    ]
  })
}

resource "aws_iam_role_policy" "this" {
  name = "manymetrics-policy-${random_string.random.result}"
  role = aws_iam_role.this.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "kinesis:PutRecord",
          "kinesis:PutRecords",
        ]
        Resource = aws_kinesis_stream.this.arn
        Effect   = "Allow"
      },
    ]
  })
}

resource "aws_api_gateway_deployment" "this" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  stage_name  = "prod"
  depends_on  = [aws_api_gateway_integration.events]
}
