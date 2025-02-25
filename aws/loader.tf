resource "aws_iam_policy" "loader" {
  name = "manymetrics-loader-${var.name}"

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
          "s3:PutObject",
          "s3:DeleteObject"
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

resource "aws_iam_role" "loader" {
  name = "manymetrics-loader-${var.name}"

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

resource "aws_iam_role_policy_attachment" "loader" {
  role       = aws_iam_role.loader.name
  policy_arn = aws_iam_policy.loader.arn
}

resource "null_resource" "loader_docker_build" {
  triggers = {
    docker_file    = md5(file("${path.module}/../lambda/loader/Dockerfile"))
    lambda_handler = md5(file("${path.module}/../lambda/loader/lambda_handler.py"))
    process_events = md5(file("${path.module}/../lambda/loader/uv.lock"))
  }

  provisioner "local-exec" {
    command = <<EOF
      aws ecr get-login-password --region ${data.aws_region.current.name} | docker login --username AWS --password-stdin ${aws_ecr_repository.loader.repository_url}
      docker build -t ${aws_ecr_repository.loader.repository_url}:latest ${path.module}/../lambda/loader
      docker push ${aws_ecr_repository.loader.repository_url}:latest
    EOF
  }
}

data "aws_ecr_image" "loader" {
  repository_name = aws_ecr_repository.loader.name
  image_tag       = "latest"

  depends_on = [null_resource.loader_docker_build]
}

# data "external" "event_spark_image_digest" {
#   program = ["sh", "-c", "aws ecr describe-images --repository-name ${aws_ecr_repository.event_spark.name} --image-ids imageTag=latest --query 'imageDetails[0].imageDigest' --output text | jq -R -s '{digest: .}'"]

#   depends_on = [null_resource.event_spark_docker_build]
# }

# TODO: we need to use something else than latest for the image tag
resource "aws_lambda_function" "loader" {
  function_name = "manymetrics-loader-${var.name}"
  role          = aws_iam_role.loader.arn

  package_type = "Image"
  image_uri    = data.aws_ecr_image.loader.image_uri

  timeout     = 120
  memory_size = 1024

  environment {
    variables = {
      GLUE_DATABASE_NAME   = aws_glue_catalog_database.database.name
      WAREHOUSE_LOCATION   = "s3://${aws_s3_bucket.data.id}/data"
      DEPLOYMENT_TIMESTAMP = timestamp()
    }
  }

  depends_on = [null_resource.loader_docker_build]
}

resource "aws_lambda_event_source_mapping" "loader" {
  event_source_arn  = aws_kinesis_stream.stream.arn
  function_name     = aws_lambda_function.loader.arn
  starting_position = "TRIM_HORIZON"
  batch_size        = 9999
}
