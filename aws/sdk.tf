resource "aws_s3_bucket" "sdk" {
  bucket = "manymetrics-sdk-${var.name}"
}

resource "aws_s3_bucket_public_access_block" "sdk" {
  bucket = aws_s3_bucket.sdk.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_acl" "sdk" {
  depends_on = [
    aws_s3_bucket_public_access_block.sdk,
    aws_s3_bucket_ownership_controls.sdk,
  ]

  bucket = aws_s3_bucket.sdk.id
  acl    = "public-read"
}

resource "aws_s3_object" "sdk" {
  bucket       = aws_s3_bucket.sdk.id
  key          = "analytics.js"
  content      = file("../browser-sdk/analytics.js")
  content_type = "application/javascript"
}

resource "aws_s3_bucket_ownership_controls" "sdk" {
  bucket = aws_s3_bucket.sdk.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_cors_configuration" "sdk" {
  bucket = aws_s3_bucket.sdk.id

  cors_rule {
    allowed_methods = ["GET"]
    allowed_origins = ["*"]
  }
}

resource "aws_s3_bucket_policy" "sdk" {
  bucket = aws_s3_bucket.sdk.id
  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "${aws_s3_bucket.sdk.arn}/*"
    }
  ]
}
POLICY
}
