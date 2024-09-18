resource "aws_kinesis_stream" "stream" {
  name = "manymetrics-stream-${var.name}"
  stream_mode_details {
    # it's actually more expensive, TODO
    stream_mode = "ON_DEMAND"
  }
}
