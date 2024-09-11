output "kinesis_stream_arn" {
  value = aws_kinesis_stream.stream.arn
}

output "kinesis_stream_name" {
  value = aws_kinesis_stream.stream.name
}

output "data_bucket_name" {
  value = aws_s3_bucket.data.bucket
}

output "api_instance_url" {
  value = aws_apigatewayv2_api.api.api_endpoint
}

output "browser_sdk_url" {
  value = "https://${aws_s3_bucket.sdk.bucket}.s3.amazonaws.com${aws_s3_bucket_object.sdk.key}"
}

output "glue_database_name" {
  value = aws_glue_catalog_database.database.name
}
