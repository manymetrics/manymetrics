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

resource "aws_lambda_function" "event_spark" {
  function_name = "manymetrics-event_spark-${random_string.random.result}"
  role          = aws_iam_role.event_spark.arn

  package_type = "Image"
  image_uri    = "${aws_ecr_repository.event_spark.repository_url}:latest"

  timeout     = 120
  memory_size = 1024

  environment {
    variables = {
      GLUE_DATABASE_NAME = aws_glue_catalog_database.database.name
      EVENTS_S3_URI      = "s3://${aws_s3_bucket.data.id}/data/events"
    }
  }
}

resource "aws_lambda_event_source_mapping" "event_spark" {
  event_source_arn  = aws_kinesis_stream.stream.arn
  function_name     = aws_lambda_function.event_spark.arn
  starting_position = "TRIM_HORIZON"
}
