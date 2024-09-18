resource "aws_kinesis_stream" "stream" {
  name        = "manymetrics-stream-${var.name}"
  shard_count = var.kinesis_shards == -1 ? null : var.kinesis_shards

  stream_mode_details {
    stream_mode = var.kinesis_shards == -1 ? "ON_DEMAND" : "PROVISIONED"
  }
}
