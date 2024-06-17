resource "aws_kinesis_stream" "stream" {
  name = "manymetrics-stream-${random_string.random.result}"
  stream_mode_details {
    stream_mode = "ON_DEMAND"
  }
}
