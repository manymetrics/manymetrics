output "kinesis_stream_arn" {
  value = aws_kinesis_stream.stream.arn
}

output "kinesis_stream_name" {
  value = aws_kinesis_stream.stream.name
}

output "api_role_arn" {
  value = aws_iam_role.api.arn
}

output "api_role_name" {
  value = aws_iam_role.api.name
}

output "ecr_event_lambda_name" {
  value = aws_ecr_repository.ecr.name
}

output "data_bucket_name" {
  value = aws_s3_bucket.data.bucket
}