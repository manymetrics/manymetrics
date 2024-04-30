resource "aws_kinesis_firehose_delivery_stream" "firehose" {
    name        = "manymetrics-firehose-${random_string.random.result}"
    destination = "extended_s3"

    extended_s3_configuration {
        bucket_arn = aws_s3_bucket.data.arn
        prefix    = "raw/"
        error_output_prefix = "raw_errors/"
        role_arn   = aws_iam_role.firehose.arn

        compression_format = "GZIP"
    }
}

resource "aws_iam_policy" "firehose" {
  name = "manymetrics-firehose-${random_string.random.result}"

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
          "${aws_s3_bucket.data.arn}/raw/*"
        ]
      },
    #   {
    #     "Effect" : "Allow",
    #     "Action" : [
    #       "lambda:InvokeFunction",
    #       "lambda:GetFunctionConfiguration"
    #     ],
    #     "Resource" : "${aws_lambda_function.prepare.arn}:*"
    #   },
    #   {
    #     "Effect" : "Allow",
    #     "Action" : [
    #       "glue:Get*",
    #       "glue:List*"
    #     ],
    #     "Resource" : "*"
    #   },
    ]
  })
}
resource "aws_iam_role" "firehose" {
  name = "manymetrics-firehose-${random_string.random.result}"

  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Action" : "sts:AssumeRole",
        "Principal" : {
          "Service" : "firehose.amazonaws.com"
        },
        "Effect" : "Allow",
        "Sid" : ""
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "firehose" {
  role       = aws_iam_role.firehose.id
  policy_arn = aws_iam_policy.firehose.arn
}
