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

resource "aws_lambda_function" "event_lambda" {
  function_name = "manymetrics-event_lambda-${random_string.random.result}"
  role          = aws_iam_role.event_lambda.arn

  package_type = "Image"
  image_uri    = "483218637139.dkr.ecr.eu-west-1.amazonaws.com/manymetrics-lk1o4gzf:latest"

  timeout     = 90
  memory_size = 512

  environment {
    variables = {
      GLUE_DATABASE_NAME = aws_glue_catalog_database.database.name
      EVENTS_S3_URI      = "s3://${aws_s3_bucket.data.id}/data/events"
    }
  }
}
