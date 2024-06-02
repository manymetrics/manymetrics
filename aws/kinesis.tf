resource "aws_kinesis_stream" "stream" {
  name = "manymetrics-stream-${random_string.random.result}"
  stream_mode_details {
    stream_mode = "ON_DEMAND"
  }
}


# resource "aws_kinesis_firehose_delivery_stream" "firehose" {
#     name        = "manymetrics-firehose-${random_string.random.result}"
#     destination = "extended_s3"

#     extended_s3_configuration {
#         bucket_arn = aws_s3_bucket.data.arn
#         prefix    = "raw/"
#         error_output_prefix = "raw_errors/"
#         role_arn   = aws_iam_role.firehose.arn

#         compression_format = "GZIP"
#     }
# }

