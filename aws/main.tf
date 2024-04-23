data "aws_region" "current" {}

resource "random_string" "random" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_kinesis_stream" "this" {
  name        = "manymetrics-stream-${random_string.random.result}"
  stream_mode_details {
    stream_mode = "ON_DEMAND"
  }
}

