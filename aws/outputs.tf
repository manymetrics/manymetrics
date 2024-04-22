output "kinesis_stream_arn" {
  value = aws_kinesis_stream.this.arn
}

output "kinesis_stream_name" {
  value = aws_kinesis_stream.this.name
}

output "role_arn" {
  value = aws_iam_role.this.arn
}

output "role_name" {
  value = aws_iam_role.this.name
}
