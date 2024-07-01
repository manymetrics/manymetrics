resource "aws_iam_policy" "event_spark" {
  name = "manymetrics-event_spark-${random_string.random.result}"

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

resource "aws_iam_role" "event_spark" {
  name = "manymetrics-event_spark-${random_string.random.result}"

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

resource "aws_iam_role_policy_attachment" "event_spark" {
  role       = aws_iam_role.event_spark.name
  policy_arn = aws_iam_policy.event_spark.arn
}

resource "null_resource" "event_spark_docker_build" {
  triggers = {
    docker_file = md5(file("${path.module}/../lambda/event_spark/Dockerfile"))
    lambda_handler = md5(file("${path.module}/../lambda/event_spark/lambda_handler.py"))
    process_events = md5(file("${path.module}/../lambda/event_spark/process_events.py"))
  }

  provisioner "local-exec" {
    command = <<EOF
      aws ecr get-login-password --region ${data.aws_region.current.name} | docker login --username AWS --password-stdin ${aws_ecr_repository.event_spark.repository_url}
      docker build -t ${aws_ecr_repository.event_spark.repository_url}:latest ${path.module}/../lambda/event_spark
      docker push ${aws_ecr_repository.event_spark.repository_url}:latest
    EOF
  }
}

data "aws_ecr_image" "event_spark" {
  repository_name = aws_ecr_repository.event_spark.name
  image_tag       = "latest"

  depends_on = [ null_resource.event_spark_docker_build ]
}

# data "external" "event_spark_image_digest" {
#   program = ["sh", "-c", "aws ecr describe-images --repository-name ${aws_ecr_repository.event_spark.name} --image-ids imageTag=latest --query 'imageDetails[0].imageDigest' --output text | jq -R -s '{digest: .}'"]

#   depends_on = [null_resource.event_spark_docker_build]
# }

# TODO: we need to use something else than latest for the image tag
resource "aws_lambda_function" "event_spark" {
  function_name = "manymetrics-event_spark-${random_string.random.result}"
  role          = aws_iam_role.event_spark.arn

  package_type = "Image"
  image_uri    = data.aws_ecr_image.event_spark.image_uri

  timeout     = 120
  memory_size = 1024

  environment {
    variables = {
      GLUE_DATABASE_NAME = aws_glue_catalog_database.database.name
      EVENTS_S3_URI      = "s3://${aws_s3_bucket.data.id}/data/events"
    }
  }

  depends_on = [null_resource.event_spark_docker_build]
}

resource "aws_lambda_event_source_mapping" "event_spark" {
  event_source_arn  = aws_kinesis_stream.stream.arn
  function_name     = aws_lambda_function.event_spark.arn
  starting_position = "TRIM_HORIZON"
}
