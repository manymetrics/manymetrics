resource "aws_iam_policy" "event_lambda" {
  name = "manymetrics-event_lambda-${random_string.random.result}"

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : [
          "s3:AbortMultipartUpload",
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads",
          "s3:PutObject"
        ],
        "Resource" : [
          aws_s3_bucket.data.arn,
          "${aws_s3_bucket.data.arn}/*"
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource" : "arn:aws:logs:*:*:*"
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "kinesis:GetRecords",
          "kinesis:GetShardIterator",
          "kinesis:DescribeStream",
          "kinesis:DescribeStreamSummary",
          "kinesis:ListShards",
          "kinesis:ListStreams",
          "kinesis:SubscribeToShard",
        ],
        "Resource" : aws_kinesis_stream.stream.arn
      },
      {
        # TODO: narrow down the permissions
        "Effect" : "Allow",
        "Action" : [
          "glue:*"
        ],
        "Resource" : "*"
      }
    ]
  })
}

resource "aws_iam_role" "event_lambda" {
  name = "manymetrics-event_lambda-${random_string.random.result}"

  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Action" : "sts:AssumeRole",
        "Principal" : {
          "Service" : "lambda.amazonaws.com"
        },
        "Effect" : "Allow",
        "Sid" : ""
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "event_lambda" {
  role       = aws_iam_role.event_lambda.name
  policy_arn = aws_iam_policy.event_lambda.arn
}

# data "archive_file" "event_lambda" {
#   type        = "zip"
#   source_file = "${path.module}/lambdas/event_lambda/lambda.py"
#   output_path = "event_lambda.zip"
# }


resource "aws_lambda_function" "event_lambda" {
  function_name = "manymetrics-event_lambda-${random_string.random.result}"
  role          = aws_iam_role.event_lambda.arn

  package_type = "Image"
  image_uri    = "483218637139.dkr.ecr.eu-west-1.amazonaws.com/manymetrics-lk1o4gzf:latest"

  timeout     = 90
  memory_size = 512

  # image_config {
  #   command           = local.docker_api.command
  # }

  environment {
    variables = {
      GLUE_DATABASE_NAME = aws_glue_catalog_database.database.name
      EVENTS_S3_URI      = "s3://${aws_s3_bucket.data.id}/data/events"
    }
  }
}

# resource "null_resource" "event_lambda_layer" {
#   triggers = {
#     requirements = timestamp() # filesha1(local.requirements_path)
#   }
#   # the command to install python and dependencies to the machine and zips
#   provisioner "local-exec" {
#     command = <<EOT
#       cd ${local.layer_path}
#       rm -rf python
#       mkdir python
#       pip3.12 install -r ${local.requirements_name} -t python/
#       zip -r ${local.layer_zip_name} python/
#     EOT
#   }
# }

# resource "aws_s3_object" "event_lambda_layer" {
#   bucket     = aws_s3_bucket.data.id
#   key        = "lambda_layers/${local.layer_name}/${local.layer_zip_name}"
#   source     = "${local.layer_path}/${local.layer_zip_name}"
#   depends_on = [null_resource.event_lambda_layer]
# }

# resource "aws_lambda_layer_version" "event_lambda_layer" {
#   s3_bucket           = aws_s3_bucket.data.id
#   s3_key              = aws_s3_object.event_lambda_layer.key
#   layer_name          = local.layer_name
#   compatible_runtimes = ["python3.12"]
#   skip_destroy        = true
#   depends_on          = [aws_s3_object.event_lambda_layer]
# }

# resource "aws_lambda_event_source_mapping" "event_lambda" {
#   event_source_arn = "${aws_kinesis_stream.stream.arn}"
#   function_name = "${aws_lambda_function.event_lambda.arn}"
#   starting_position = "TRIM_HORIZON"
# }
