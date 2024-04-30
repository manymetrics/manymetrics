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

resource "aws_iam_role_policy_attachment" "api_logs" {
  role       = aws_iam_role.this.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

resource "aws_iam_role_policy" "this" {
  name = "manymetrics-policy-${random_string.random.result}"
  role = aws_iam_role.this.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "firehose:PutRecord",
          "firehose:PutRecordBatch",
        ]
        Resource = aws_kinesis_firehose_delivery_stream.firehose.arn
        Effect   = "Allow"
      }
    ]
  })
}

resource "aws_api_gateway_deployment" "this" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  stage_name  = "prod"
  depends_on  = [aws_api_gateway_integration.events]

  triggers = {
    redeployment = timestamp()
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_resource" "events" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  parent_id   = aws_api_gateway_rest_api.this.root_resource_id
  path_part   = "e"
}

resource "aws_api_gateway_method" "events" {
  rest_api_id   = aws_api_gateway_rest_api.this.id
  resource_id   = aws_api_gateway_resource.events.id
  http_method   = "POST"
  authorization = "NONE"
  # request_models = {
  #   "application/json" = aws_api_gateway_model.model.name
  # }
  # request_validator_id = aws_api_gateway_request_validator.validator.id
}

resource "aws_api_gateway_integration" "events" {
  rest_api_id             = aws_api_gateway_rest_api.this.id
  resource_id             = aws_api_gateway_resource.events.id
  http_method             = aws_api_gateway_method.events.http_method
  integration_http_method = "POST"
  type                    = "AWS"
  credentials             = aws_iam_role.this.arn
  uri                     = "arn:aws:apigateway:${data.aws_region.current.name}:firehose:action/PutRecord"

  passthrough_behavior = "NEVER"

  request_parameters = {
    "integration.request.header.Content-Type" = "'application/x-amz-json-1.1'"
  }

  request_templates = {
    "application/json" = <<EOT
       {
        "Record": {
          "Data": "$util.base64Encode($input.json('$'))"
        },
        "DeliveryStreamName": "${aws_kinesis_firehose_delivery_stream.firehose.name}"
       }
    EOT
  }
}

resource "aws_api_gateway_method_response" "events_200" {
  http_method = aws_api_gateway_method.events.http_method
  resource_id = aws_api_gateway_resource.events.id
  rest_api_id = aws_api_gateway_rest_api.this.id
  status_code = 200

  response_parameters = {
    "method.response.header.Content-Type"                = true
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}


resource "aws_api_gateway_method_response" "events_400" {
  http_method = aws_api_gateway_method.events.http_method
  resource_id = aws_api_gateway_resource.events.id
  rest_api_id = aws_api_gateway_rest_api.this.id
  status_code = 400

  response_parameters = {
    "method.response.header.Content-Type"                = true
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_integration_response" "events_200" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  resource_id = aws_api_gateway_resource.events.id
  http_method = aws_api_gateway_method.events.http_method
  status_code = aws_api_gateway_method_response.events_200.status_code

  response_parameters = {
    "method.response.header.Content-Type"                = "'application/json'"
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  response_templates = {
    "application/json" = <<EOT
      {
        "state": "ok"
      }
    EOT
  }

  depends_on = [aws_api_gateway_integration.events]
}

resource "aws_api_gateway_integration_response" "events_400" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  resource_id = aws_api_gateway_resource.events.id
  http_method = aws_api_gateway_method.events.http_method
  status_code = aws_api_gateway_method_response.events_400.status_code

  selection_pattern = "4\\d{2}"

  response_templates = {
    "application/json" = <<EOT
      {
        "state": "error",
        "message": "$util.escapeJavaScript($input.path('$.errorMessage'))"
      }
    EOT
  }

  response_parameters = {
    "method.response.header.Content-Type"                = "'application/json'"
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [aws_api_gateway_integration.events]
}

module "events_cors" {
  source = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.this.id
  api_resource_id = aws_api_gateway_resource.events.id
}
